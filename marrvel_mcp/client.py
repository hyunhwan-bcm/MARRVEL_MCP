"""
HTTP client for making requests to MARRVEL API.
"""

import httpx
import inspect
from typing import Any

from .config import BASE_URL, TIMEOUT


async def fetch_marrvel_data(endpoint: str) -> dict[str, Any]:
    """
    Fetch data from MARRVEL API.
    
    Args:
        endpoint: API endpoint path (e.g., "/gene/entrezId/7157")
        
    Returns:
        JSON response from the API
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    url = f"{BASE_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        response = await client.get(url)
        # Some tests may mock raise_for_status/json as async coroutines; handle both sync/async.
        rfs = response.raise_for_status()
        if inspect.iscoroutine(rfs):
            await rfs
        data = response.json()
        if inspect.iscoroutine(data):
            data = await data
        return data
