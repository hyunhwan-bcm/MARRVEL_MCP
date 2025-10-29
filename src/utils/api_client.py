"""
API Client for MARRVEL REST API.

This module provides the core HTTP communication layer for all MARRVEL-MCP tools.
It handles requests to the MARRVEL API with proper error handling and timeout management.
"""

import httpx
import json
import ssl
import certifi
import inspect
import ast
from typing import Any
from config import API_BASE_URL, API_TIMEOUT, VERIFY_SSL


async def fetch_marrvel_data(endpoint: str) -> str:
    """
    Fetch data from MARRVEL API.

    Args:
        endpoint: API endpoint path (e.g., "/gene/entrezId/7157")
                 Should start with "/" and not include the base URL

    Returns:
        JSON response from the API as a dictionary

    Raises:
        httpx.HTTPError: If the HTTP request fails (4xx, 5xx status codes)
        httpx.TimeoutException: If the request exceeds API_TIMEOUT
        httpx.ConnectError: If unable to connect to the API server
    """
    url = f"{API_BASE_URL}{endpoint}"

    # Configure SSL verification
    verify = ssl.create_default_context(cafile=certifi.where()) if VERIFY_SSL else False

    async def _maybe_await(obj):
        """Await obj if awaitable; call it if callable and await results if needed."""
        try:
            if inspect.isawaitable(obj):
                return await obj
            if callable(obj):
                val = obj()
                if inspect.isawaitable(val):
                    return await val
                return val
            return obj
        except Exception:
            return obj

    async with httpx.AsyncClient(verify=verify, timeout=API_TIMEOUT) as client:
        response = await client.get(url)

        # Some test mocks make raise_for_status() a coroutine
        rfs = response.raise_for_status()
        if inspect.isawaitable(rfs):
            await rfs

        # Parse JSON (handle mocks that return coroutines)
        try:
            data = response.json()
            if inspect.isawaitable(data):
                data = await data
        except json.JSONDecodeError:
            # Try a safe fallback for Python-style literals (e.g. "[{'a':1}]") using ast.literal_eval
            text = await _maybe_await(getattr(response, "text", ""))
            try:
                parsed = ast.literal_eval(text)
                # normalize and return like above
                if isinstance(parsed, list):
                    result = {"status": "success", "data": parsed, "count": len(parsed)}
                    return json.dumps(result, indent=2)
                if isinstance(parsed, dict):
                    return json.dumps(parsed, indent=2)
                return json.dumps({"status": "success", "data": parsed}, indent=2)
            except Exception:
                err = {
                    "error": "Invalid JSON response",
                    "status_code": getattr(response, "status_code", None),
                    "content": str(text)[:200],
                }
                return json.dumps(err, indent=2)

        # Normalize arrays to a consistent dict shape so callers don't need to special-case lists
        if isinstance(data, list):
            result = {"status": "success", "data": data, "count": len(data)}
            return json.dumps(result, indent=2)
        if isinstance(data, dict):
            return json.dumps(data, indent=2)

        # For primitives (str, int, etc.), wrap into data key
        result = {"status": "success", "data": data}
        return json.dumps(result, indent=2)


# Future enhancements that can be added to this module:
# - Response caching with TTL
# - Request retry logic with exponential backoff
# - Rate limiting
# - Request logging and metrics
# - Response validation
# - Error categorization and custom exceptions
