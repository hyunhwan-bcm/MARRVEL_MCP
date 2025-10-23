"""
API Client for MARRVEL REST API.

This module provides the core HTTP communication layer for all MARRVEL-MCP tools.
It handles requests to the MARRVEL API with proper error handling and timeout management.
"""

import httpx
import inspect
import json
import ssl
import certifi
from typing import Any
from config import API_BASE_URL, API_TIMEOUT, VERIFY_SSL


async def fetch_marrvel_data(endpoint: str) -> dict[str, Any]:
    """
    Fetch data from MARRVEL API.

    This is the central HTTP client function used by all tool modules.
    It handles:
    - Building the complete URL
    - Making the async HTTP request with proper SSL certificate verification
    - Error handling and status code validation
    - JSON response parsing
    - Compatibility with both sync and async mocked responses (for testing)

    Args:
        endpoint: API endpoint path (e.g., "/gene/entrezId/7157")
                 Should start with "/" and not include the base URL

    Returns:
        JSON response from the API as a dictionary

    Raises:
        httpx.HTTPError: If the HTTP request fails (4xx, 5xx status codes)
        httpx.TimeoutException: If the request exceeds API_TIMEOUT
        httpx.ConnectError: If unable to connect to the API server

    Example:
        >>> data = await fetch_marrvel_data("/gene/entrezId/7157")
        >>> print(data['symbol'])  # 'TP53'

    Note:
        The function includes compatibility code to handle both synchronous
        and asynchronous mocked responses during testing. This allows tests
        to mock raise_for_status() and json() as either regular functions
        or coroutines.

        SSL certificate verification:
        - When VERIFY_SSL=True: uses certifi's CA bundle (production)
        - When VERIFY_SSL=False: bypasses SSL verification (development/testing only)
        WARNING: Never disable SSL verification in production!
    """
    url = f"{API_BASE_URL}{endpoint}"

    # Configure SSL verification based on config
    # For production: use certifi's CA bundle for robust certificate verification
    # For development/testing: can bypass SSL verification if VERIFY_SSL=False
    if VERIFY_SSL:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        verify = ssl_context
    else:
        # Bypass SSL verification (for development/testing only)
        verify = False

    async with httpx.AsyncClient(verify=verify, timeout=API_TIMEOUT) as client:
        response = await client.get(url)

        # Some tests may mock raise_for_status/json as async coroutines
        # Handle both sync and async for compatibility
        rfs = response.raise_for_status()
        if inspect.isawaitable(rfs):
            await rfs

        # Helper to coerce possibly-awaitable/callable values to string.
        async def _to_str(obj):
            try:
                if inspect.isawaitable(obj):
                    val = await obj
                elif callable(obj) and not isinstance(obj, str):
                    maybe = obj()
                    if inspect.isawaitable(maybe):
                        val = await maybe
                    else:
                        val = maybe
                else:
                    val = obj
            except Exception:
                val = obj
            if val is None:
                return ""
            try:
                return str(val)
            except Exception:
                return ""

        # Normalize content (bytes or str) existence
        content_raw = getattr(response, "content", None)
        try:
            if inspect.isawaitable(content_raw):
                content_val = await content_raw
            else:
                content_val = content_raw
        except Exception:
            content_val = content_raw

        # Consider both bytes and non-bytes content
        has_content = False
        if isinstance(content_val, (bytes, bytearray)):
            has_content = len(content_val) > 0
        else:
            has_content = bool(content_val)

        if not has_content:
            return {"error": "Empty response from API", "status_code": response.status_code}

        # Resolve content-type and text_preview to strings safely
        hdrs = getattr(response, "headers", {})
        if isinstance(hdrs, dict):
            content_type = await _to_str(hdrs.get("content-type", ""))
        else:
            # hdrs may be a mock object with a get method
            get_fn = getattr(hdrs, "get", None)
            if get_fn:
                content_type = await _to_str(get_fn("content-type", ""))
            else:
                content_type = await _to_str(hdrs)

        text_preview = await _to_str(getattr(response, "text", ""))

        content_type = (content_type or "").lower()
        if (
            "text/html" in content_type
            or text_preview.lstrip().lower().startswith("<!doctype")
            or text_preview.lstrip().lower().startswith("<html")
        ):
            # Normalize to a client error so callers always receive JSON-like error dicts
            return {
                "error": "Unexpected HTML response from API",
                "status_code": 400,
                "original_status": response.status_code,
                "content_preview": text_preview[:200],
            }

        try:
            data = response.json()
            if inspect.isawaitable(data):
                data = await data
            return data
        except json.JSONDecodeError:
            return {
                "error": "Invalid JSON response",
                "status_code": response.status_code,
                "content": response.text[:200],  # First 200 chars
            }


# Future enhancements that can be added to this module:
# - Response caching with TTL
# - Request retry logic with exponential backoff
# - Rate limiting
# - Request logging and metrics
# - Response validation
# - Error categorization and custom exceptions
