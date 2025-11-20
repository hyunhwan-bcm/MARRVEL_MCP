"""
Tests for enhanced 500 error logging and debugging.

Validates that detailed error information is captured when 500 errors occur.
"""

import asyncio
import logging
import pytest
import httpx
from unittest.mock import AsyncMock, Mock, patch
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(repo_root))

from marrvel_mcp.server import retry_with_backoff


@pytest.mark.asyncio
async def test_500_error_logs_detailed_information(caplog):
    """Test that 500 errors log detailed diagnostic information."""
    # Create a mock response with detailed error information
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error: Database connection failed"
    mock_response.headers = {
        "Content-Type": "application/json",
        "X-Request-Id": "abc123",
        "Date": "Wed, 20 Nov 2024 20:00:00 GMT",
    }

    mock_request = Mock()
    mock_request.url = "https://marrvel.org/graphql"
    mock_request.method = "POST"

    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            error = httpx.HTTPStatusError(
                "Server error", request=mock_request, response=mock_response
            )
            raise error
        return "success after retries"

    # Capture logs at WARNING level
    with caplog.at_level(logging.WARNING):
        result = await retry_with_backoff(mock_func, max_retries=5, initial_delay=0.01)

    assert result == "success after retries"
    assert call_count == 3

    # Verify detailed logging occurred
    log_messages = [record.message for record in caplog.records if record.levelname == "WARNING"]

    # Should have 2 warning messages (one for each failed attempt)
    assert len(log_messages) >= 2

    # Check that error details are logged
    for log_msg in log_messages:
        assert "Server error (500)" in log_msg
        assert "Details:" in log_msg
        # Check for URL and method
        assert "https://marrvel.org/graphql" in log_msg
        assert "POST" in log_msg


@pytest.mark.asyncio
async def test_500_error_logs_response_body_and_headers(caplog):
    """Test that 500 errors capture response body and headers."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = (
        '{"error": "Database timeout", "details": "Connection to database timed out after 30s"}'
    )
    mock_response.headers = {
        "Content-Type": "application/json",
        "X-Error-Code": "DB_TIMEOUT",
        "X-Request-Id": "req-xyz789",
    }

    mock_request = Mock()
    mock_request.url = "https://marrvel.org/data/gnomAD/gene/entrezId/12345"
    mock_request.method = "GET"

    async def mock_func():
        error = httpx.HTTPStatusError("Server error", request=mock_request, response=mock_response)
        raise error

    with caplog.at_level(logging.WARNING):
        with pytest.raises(httpx.HTTPStatusError):
            await retry_with_backoff(mock_func, max_retries=2, initial_delay=0.01)

    # Check that response body and headers were logged
    log_text = "\n".join([record.message for record in caplog.records])

    # Should contain response body information
    assert "Database timeout" in log_text or "response_body" in log_text

    # Should contain response headers
    assert "X-Error-Code" in log_text or "response_headers" in log_text


@pytest.mark.asyncio
async def test_500_error_final_failure_logs_at_error_level(caplog):
    """Test that final failure after all retries logs at ERROR level."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Persistent server error"
    mock_response.headers = {"Content-Type": "text/plain"}

    mock_request = Mock()
    mock_request.url = "https://marrvel.org/graphql"
    mock_request.method = "POST"

    async def mock_func():
        raise httpx.HTTPStatusError("Server error", request=mock_request, response=mock_response)

    with caplog.at_level(logging.WARNING):
        with pytest.raises(httpx.HTTPStatusError):
            await retry_with_backoff(mock_func, max_retries=2, initial_delay=0.01)

    # Check for ERROR level log on final failure
    error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
    assert len(error_logs) >= 1

    # Verify the error log contains detailed information
    error_message = error_logs[0].message
    assert "Exhausted all retries" in error_message
    assert "Server error (500)" in error_message
    assert "Details:" in error_message


@pytest.mark.asyncio
async def test_429_error_does_not_log_response_body(caplog):
    """Test that 429 rate limit errors don't log response body (only 500 errors should)."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.text = "Rate limit exceeded"
    mock_response.headers = {"Retry-After": "60"}

    mock_request = Mock()
    mock_request.url = "https://marrvel.org/graphql"
    mock_request.method = "POST"

    call_count = 0

    async def mock_func():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.HTTPStatusError(
                "Rate limited", request=mock_request, response=mock_response
            )
        return "success"

    with caplog.at_level(logging.WARNING):
        result = await retry_with_backoff(mock_func, max_retries=3, initial_delay=0.01)

    assert result == "success"

    # Check that rate limit warnings don't include response_body
    log_text = "\n".join([record.message for record in caplog.records])
    assert "Rate limited (429)" in log_text
    # Should not log response body for 429 errors
    assert "response_body" not in log_text
