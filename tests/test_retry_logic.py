"""
Unit tests for retry_with_backoff function with exponential backoff.

Tests the retry logic for handling 500 Internal Server Errors and 429 Rate Limit errors
from the MARRVEL API, particularly the Mutalyzer endpoint.
"""

import asyncio
import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch
import logging

# Import the functions we want to test
import sys
from pathlib import Path

# Add the marrvel_mcp directory to the path
repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from marrvel_mcp.server import retry_with_backoff, fetch_marrvel_data


@pytest.mark.asyncio
async def test_retry_with_backoff_success_on_first_attempt():
    """Test that successful call on first attempt returns immediately."""
    mock_func = AsyncMock(return_value="success")

    result = await retry_with_backoff(mock_func)

    assert result == "success"
    assert mock_func.call_count == 1


@pytest.mark.asyncio
async def test_retry_with_backoff_500_error_with_retry():
    """Test that 500 errors trigger exponential backoff retries."""
    # Create a mock response with 500 status code
    mock_response = Mock()
    mock_response.status_code = 500

    # Mock function that fails twice with 500, then succeeds
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)
        return "success"

    # Patch asyncio.sleep to avoid waiting during tests
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await retry_with_backoff(mock_func, max_retries=5, initial_delay=1.0)

    assert result == "success"
    assert call_count == 3
    # Should have called sleep twice (for the two failures)
    assert mock_sleep.call_count == 2


@pytest.mark.asyncio
async def test_retry_with_backoff_429_error_with_retry():
    """Test that 429 errors trigger exponential backoff retries."""
    # Create a mock response with 429 status code
    mock_response = Mock()
    mock_response.status_code = 429

    # Mock function that fails once with 429, then succeeds
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.HTTPStatusError("Rate limited", request=Mock(), response=mock_response)
        return "success"

    # Patch asyncio.sleep to avoid waiting during tests
    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        result = await retry_with_backoff(mock_func, max_retries=5, initial_delay=1.0)

    assert result == "success"
    assert call_count == 2
    assert mock_sleep.call_count == 1


@pytest.mark.asyncio
async def test_retry_with_backoff_exponential_delay():
    """Test that delays follow exponential backoff pattern."""
    mock_response = Mock()
    mock_response.status_code = 500

    # Mock function that always fails
    async def mock_func():
        raise httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

    sleep_times = []

    async def track_sleep(delay):
        sleep_times.append(delay)

    # Patch asyncio.sleep to track delay times
    with patch("asyncio.sleep", new_callable=AsyncMock, side_effect=track_sleep):
        with pytest.raises(httpx.HTTPStatusError):
            await retry_with_backoff(mock_func, max_retries=3, initial_delay=2.0)

    # Should have 3 sleep calls (for 3 retries after initial attempt)
    assert len(sleep_times) == 3
    # Verify exponential growth (with jitter, times should be around 2, 4, 8)
    # Allow for jitter by checking that each is greater than previous base value
    assert sleep_times[0] >= 2.0  # First delay around 2s
    assert sleep_times[1] >= 4.0  # Second delay around 4s
    assert sleep_times[2] >= 8.0  # Third delay around 8s


@pytest.mark.asyncio
async def test_retry_with_backoff_max_retries_exhausted():
    """Test that exception is raised after max retries are exhausted."""
    mock_response = Mock()
    mock_response.status_code = 500

    # Mock function that always fails
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        raise httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)

    # Patch asyncio.sleep to avoid waiting during tests
    with patch("asyncio.sleep", new_callable=AsyncMock):
        with pytest.raises(httpx.HTTPStatusError):
            await retry_with_backoff(mock_func, max_retries=3, initial_delay=1.0)

    # Should have tried 4 times total (initial + 3 retries)
    assert call_count == 4


@pytest.mark.asyncio
async def test_retry_with_backoff_non_retryable_error():
    """Test that non-retryable errors (e.g., 404) are not retried."""
    mock_response = Mock()
    mock_response.status_code = 404

    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        raise httpx.HTTPStatusError("Not found", request=Mock(), response=mock_response)

    # Should not retry on 404
    with pytest.raises(httpx.HTTPStatusError):
        await retry_with_backoff(mock_func, max_retries=5, initial_delay=1.0)

    # Should only be called once
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_with_backoff_logging(caplog):
    """Test that retry attempts are logged with appropriate messages."""
    mock_response = Mock()
    mock_response.status_code = 500

    # Mock function that fails twice, then succeeds
    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response)
        return "success"

    # Capture logs
    with caplog.at_level(logging.WARNING):
        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await retry_with_backoff(mock_func, max_retries=5, initial_delay=1.0)

    assert result == "success"
    # Check that log messages contain expected content
    assert any("Server error (500)" in record.message for record in caplog.records)
    assert any("retrying in" in record.message for record in caplog.records)


@pytest.mark.asyncio
async def test_fetch_marrvel_data_with_500_retry():
    """Test that fetch_marrvel_data properly retries on 500 errors."""
    mock_response_500 = Mock()
    mock_response_500.status_code = 500
    mock_response_500.json.return_value = {"error": "Server error"}
    mock_response_500.headers = {"Content-Type": "application/json"}

    mock_response_success = Mock()
    mock_response_success.status_code = 200
    mock_response_success.json.return_value = {"data": "success"}
    mock_response_success.raise_for_status = Mock()

    call_count = 0

    async def mock_get(url):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response_500)
        return mock_response_success

    # Patch the httpx.AsyncClient
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = Mock()
        mock_client_instance.get = mock_get
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await fetch_marrvel_data("/test/endpoint", is_graphql=False)

    # Should have retried and succeeded
    assert call_count == 2
    assert "success" in result


@pytest.mark.asyncio
async def test_fetch_marrvel_data_500_multiple_retries():
    """Test that fetch_marrvel_data retries multiple times on consecutive 500 errors."""
    mock_response_500 = Mock()
    mock_response_500.status_code = 500

    call_count = 0

    async def mock_get(url):
        nonlocal call_count
        call_count += 1
        raise httpx.HTTPStatusError("Server error", request=Mock(), response=mock_response_500)

    # Patch the httpx.AsyncClient
    with patch("httpx.AsyncClient") as mock_client:
        mock_client_instance = Mock()
        mock_client_instance.get = mock_get
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_client.return_value = mock_client_instance

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(httpx.HTTPStatusError):
                await fetch_marrvel_data("/test/endpoint", is_graphql=False)

    # Should have tried max_retries + 1 times (default is 5 retries + initial attempt = 6)
    assert call_count == 6
