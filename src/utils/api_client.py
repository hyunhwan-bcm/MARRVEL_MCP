"""
API Client for MARRVEL REST API.

This module provides the core HTTP communication layer for all MARRVEL-MCP tools.
It handles requests to the MARRVEL API with proper error handling and timeout management.
"""

import httpx
import inspect
from typing import Any
from config import API_BASE_URL, API_TIMEOUT


async def fetch_marrvel_data(endpoint: str) -> dict[str, Any]:
    """
    Fetch data from MARRVEL API.
    
    This is the central HTTP client function used by all tool modules.
    It handles:
    - Building the complete URL
    - Making the async HTTP request
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
    """
    url = f"{API_BASE_URL}{endpoint}"
    
    async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
        response = await client.get(url)
        
        # Some tests may mock raise_for_status/json as async coroutines
        # Handle both sync and async for compatibility
        rfs = response.raise_for_status()
        if inspect.iscoroutine(rfs):
            await rfs
            
        data = response.json()
        if inspect.iscoroutine(data):
            data = await data
            
        return data


# Future enhancements that can be added to this module:
# - Response caching with TTL
# - Request retry logic with exponential backoff
# - Rate limiting
# - Request logging and metrics
# - Response validation
# - Error categorization and custom exceptions
