"""
Essential retry logic tests.

Reduced test suite covering only critical retry behavior.
"""

import asyncio
import pytest
import httpx
from unittest.mock import AsyncMock, Mock

import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from marrvel_mcp.server import retry_with_backoff


@pytest.mark.asyncio
async def test_retry_success_on_first_attempt():
    """Test that successful call on first attempt returns immediately."""
    mock_func = AsyncMock(return_value="success")

    result = await retry_with_backoff(mock_func)

    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_with_500_error():
    """Test that 500 errors trigger exponential backoff retries."""
    mock_response = Mock()
    mock_response.status_code = 500

    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.HTTPStatusError(
                "Server error", request=Mock(), response=mock_response
            )
        return "success after retries"

    result = await retry_with_backoff(mock_func, max_retries=5, initial_delay=0.01)

    assert result == "success after retries"
    assert call_count == 3  # Failed twice, succeeded on 3rd attempt
