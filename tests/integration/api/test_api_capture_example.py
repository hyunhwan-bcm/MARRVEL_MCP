"""
Example integration test with API response capture.

This demonstrates how to use the api_capture fixture to log
API responses during test execution.
"""

import sys
import os
import pytest
from urllib.parse import quote

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.utils.api_client import fetch_marrvel_data


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gene_api_with_capture(api_capture):
    """Test gene API endpoint and capture the response."""
    # Test TP53 gene
    entrez_id = "7157"
    endpoint = f"/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # Log the API response
        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
            return_code=return_code,
        )

        assert result is not None
        assert "symbol" in result or "entrezId" in result

    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        # Log errors too
        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_variant_api_with_capture(api_capture):
    """Test variant API endpoint and capture the response."""
    # Test variant (use canonical format and endpoint)
    variant = "6:99365567 T>C"
    # Preserve ':' but encode spaces and special chars (like '>') to avoid breaking markdown tables
    encoded_variant = quote(variant, safe=":")
    endpoint = f"/dbnsfp/variant/{encoded_variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # Log the API response
        api_capture.log_response(
            tool_name="get_variant_dbnsfp",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=result,
            status="success",
            return_code=return_code,
        )

        assert result is not None

    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        api_capture.log_response(
            tool_name="get_variant_dbnsfp",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_omim_api_with_capture(api_capture):
    """Test OMIM API endpoint and capture the response."""
    # Test OMIM for TP53
    gene_symbol = "TP53"
    endpoint = f"/omim/gene/symbol/{gene_symbol}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # Log the API response
        api_capture.log_response(
            tool_name="get_omim_for_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=result,
            status="success",
            return_code=return_code,
        )

        assert result is not None

    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        api_capture.log_response(
            tool_name="get_omim_for_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_diopt_api_with_capture(api_capture):
    """Test DIOPT ortholog API endpoint and capture the response."""
    # Test ortholog search
    gene_symbol = "TP53"
    taxon_id = "9606"  # human
    # Use canonical DIOPT endpoint order: /diopt/ortholog/gene/entrezId/{id}
    endpoint = f"/diopt/ortholog/gene/entrezId/7157"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # Log the API response
        api_capture.log_response(
            tool_name="get_diopt_orthologs_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": "7157", "gene_symbol": gene_symbol},
            output_data=result,
            status="success",
            return_code=return_code,
        )

        assert result is not None

    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        api_capture.log_response(
            tool_name="get_diopt_orthologs_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": "7157"},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_expression_api_with_capture(api_capture):
    """Test GTEx expression API endpoint and capture the response."""
    # Test expression data (use canonical entrezId endpoint)
    entrez_id = "7157"
    endpoint = f"/gtex/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # Log the API response
        api_capture.log_response(
            tool_name="get_gtex_expression",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
            return_code=return_code,
        )

        assert result is not None

    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        api_capture.log_response(
            tool_name="get_gtex_expression",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise
