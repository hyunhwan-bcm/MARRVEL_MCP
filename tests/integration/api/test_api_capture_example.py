"""
Example integration test with API response capture.

This demonstrates how to use the api_capture fixture to log
API responses during test execution.
"""

import pytest
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

        # Log the API response
        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None
        assert "symbol" in result or "entrezId" in result

    except Exception as e:
        # Log errors too
        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_variant_api_with_capture(api_capture):
    """Test variant API endpoint and capture the response."""
    # Test variant
    variant = "17-7577121-C-T"
    endpoint = f"/variant/dbnsfp/{variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Log the API response
        api_capture.log_response(
            tool_name="get_variant_dbnsfp",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_variant_dbnsfp",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=None,
            status="error",
            error=str(e),
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

        # Log the API response
        api_capture.log_response(
            tool_name="get_omim_for_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_omim_for_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_diopt_api_with_capture(api_capture):
    """Test DIOPT ortholog API endpoint and capture the response."""
    # Test ortholog search
    gene_symbol = "TP53"
    taxon_id = "9606"  # human
    endpoint = f"/diopt/entrezId/7157/ortholog"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Log the API response
        api_capture.log_response(
            tool_name="get_diopt_orthologs_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": "7157", "gene_symbol": gene_symbol},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_diopt_orthologs_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": "7157"},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_expression_api_with_capture(api_capture):
    """Test GTEx expression API endpoint and capture the response."""
    # Test expression data
    gene_symbol = "TP53"
    endpoint = f"/gtex/{gene_symbol}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Log the API response
        api_capture.log_response(
            tool_name="get_gtex_expression",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gtex_expression",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise
