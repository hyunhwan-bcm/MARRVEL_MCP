"""
Integration tests that make real API calls for server utilities.

Run with: pytest -m integration_api tests/integration/api/test_server_api_integration.py
"""

import pytest
import sys
from pathlib import Path

# Ensure repository root is on sys.path for importing src.*
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.api_client import fetch_marrvel_data


class TestIntegration:
    """
    Integration tests that make real API calls.
    Skip these in CI/CD by using pytest markers.
    """

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_gene_query(self, api_capture):
        """Test real API call for TP53."""
        endpoint = "/gene/entrezId/7157"
        entrez_id = "7157"

        try:
            result = await fetch_marrvel_data(endpoint)

            # Log the API response (endpoint omitted - optional)
            api_capture.log_response(
                tool_name="get_gene_by_entrez_id",
                input_data={"entrez_id": entrez_id},
                output_data=result,
                status="success",
            )

            assert result is not None

        except Exception as e:
            # Log errors
            api_capture.log_response(
                tool_name="get_gene_by_entrez_id",
                input_data={"entrez_id": entrez_id},
                output_data=None,
                status="error",
                error=str(e),
            )
            raise

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_variant_query(self, api_capture):
        """Test real API call for a variant."""
        endpoint = "/variant/dbnsfp/17-7577121-C-T"
        variant = "17-7577121-C-T"

        try:
            result = await fetch_marrvel_data(endpoint)

            # Log the API response (endpoint omitted - optional)
            api_capture.log_response(
                tool_name="get_variant_dbnsfp",
                input_data={"variant": variant},
                output_data=result,
                status="success",
            )

            assert result is not None

        except Exception as e:
            # Log errors
            api_capture.log_response(
                tool_name="get_variant_dbnsfp",
                input_data={"variant": variant},
                output_data=None,
                status="error",
                error=str(e),
            )
            raise
