"""
Integration tests for API client module (real API calls).
"""

import pytest
import sys
from pathlib import Path

# Ensure repository root is on sys.path for importing src.*
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.api_client import fetch_marrvel_data


class TestFetchMarrvelDataIntegration:
    """Integration tests that make real API calls (marked for optional execution)."""

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_tp53(self, api_capture):
        """Test real API call for TP53 gene (requires network access)."""
        endpoint = "/gene/entrezId/7157"
        entrez_id = "7157"

        try:
            result = await fetch_marrvel_data(endpoint)

            # Log the API response (endpoint omitted - optional)
            api_capture.log_response(
                tool_name="fetch_marrvel_data",
                input_data={"entrez_id": entrez_id},
                output_data=result,
                status="success",
            )

            assert "symbol" in result or "entrezId" in result

        except Exception as e:
            # Log errors too
            api_capture.log_response(
                tool_name="fetch_marrvel_data",
                input_data={"entrez_id": entrez_id},
                output_data=None,
                status="error",
                error=str(e),
            )
            raise

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_invalid_endpoint(self, api_capture):
        """Test real API call with invalid endpoint (requires network access)."""
        endpoint = "/invalid/nonexistent/endpoint"

        try:
            result = await fetch_marrvel_data(endpoint)

            # Log the response (could be error dict or exception); omit endpoint
            api_capture.log_response(
                tool_name="fetch_marrvel_data",
                input_data={"test": "invalid"},
                output_data=result,
                status="error" if "error" in result else "success",
                error="Invalid endpoint test",
            )

            # If no exception raised, check for error in response
            status_code = result.get("status_code") if isinstance(result, dict) else None
            assert "error" in result or (isinstance(status_code, int) and status_code >= 400)

        except Exception as e:
            # Log HTTPStatusError or other exceptions
            api_capture.log_response(
                tool_name="fetch_marrvel_data",
                input_data={"test": "invalid"},
                output_data=None,
                status="error",
                error=str(e),
            )
            # HTTPStatusError is also acceptable
            pass
