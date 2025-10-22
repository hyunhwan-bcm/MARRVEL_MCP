"""
Unit tests for MARRVEL-MCP server.

Run with: pytest tests/test_server.py
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import server
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.api_client import fetch_marrvel_data
from config import API_BASE_URL as BASE_URL


@pytest.mark.unit
class TestFetchMarrvelData:
    """Test the fetch_marrvel_data helper function."""

    @pytest.mark.asyncio
    async def test_fetch_gene_by_entrez_id(self):
        """Test fetching gene data by Entrez ID."""
        # Mock the httpx client
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"gene": "TP53", "entrezId": "7157"}
            mock_response.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await fetch_marrvel_data("/gene/entrezId/7157")
            assert result["gene"] == "TP53"
            assert result["entrezId"] == "7157"

    @pytest.mark.asyncio
    async def test_fetch_with_error(self):
        """Test error handling when API returns error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            with pytest.raises(Exception):
                await fetch_marrvel_data("/invalid/endpoint")


@pytest.mark.unit
class TestGeneTools:
    """Test gene-related tools."""

    @pytest.mark.asyncio
    async def test_get_gene_by_entrez_id(self):
        """Test getting gene by Entrez ID."""
        # This would test the actual tool function
        # Implementation depends on how you want to structure tests
        pass

    @pytest.mark.asyncio
    async def test_get_gene_by_symbol(self):
        """Test getting gene by symbol."""
        pass


@pytest.mark.unit
class TestVariantTools:
    """Test variant analysis tools."""

    @pytest.mark.asyncio
    async def test_get_variant_dbnsfp(self):
        """Test getting dbNSFP data for a variant."""
        pass

    @pytest.mark.asyncio
    async def test_get_clinvar_variant(self):
        """Test getting ClinVar data for a variant."""
        pass


@pytest.mark.unit
class TestOMIMTools:
    """Test OMIM disease tools."""

    @pytest.mark.asyncio
    async def test_get_omim_by_mim_number(self):
        """Test getting OMIM entry by MIM number."""
        pass


@pytest.mark.unit
class TestDIOPTTools:
    """Test DIOPT ortholog tools."""

    @pytest.mark.asyncio
    async def test_get_diopt_orthologs(self):
        """Test getting orthologs via DIOPT."""
        pass


@pytest.mark.unit
class TestExpressionTools:
    """Test expression data tools."""

    @pytest.mark.asyncio
    async def test_get_gtex_expression(self):
        """Test getting GTEx expression data."""
        pass


@pytest.mark.unit
class TestUtilityTools:
    """Test utility tools."""

    @pytest.mark.asyncio
    async def test_validate_hgvs_variant(self):
        """Test HGVS variant validation."""
        pass


# Integration tests (require actual API access)
class TestIntegration:
    """
    Integration tests that make real API calls.
    Skip these in CI/CD by using pytest markers.
    """

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_gene_query(self):
        """Test real API call for TP53."""
        result = await fetch_marrvel_data("/gene/entrezId/7157")
        assert result is not None
        # Add more specific assertions based on expected response

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_variant_query(self):
        """Test real API call for a variant."""
        # Example with a real variant
        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
