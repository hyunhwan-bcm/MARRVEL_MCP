"""
Unit tests for gene tools module.

Tests the three gene query functions: get_gene_by_entrez_id,
get_gene_by_symbol, and get_gene_by_position.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.gene_tools import get_gene_by_entrez_id, get_gene_by_symbol, get_gene_by_position


class TestGetGeneByEntrezId:
    """Test the get_gene_by_entrez_id function."""

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """Test successful gene query with valid Entrez ID."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {
                "entrezId": "7157",
                "symbol": "TP53",
                "name": "tumor protein p53",
                "chromosome": "17",
            }
            result = await get_gene_by_entrez_id("7157")
            assert "TP53" in result
            assert "7157" in result
            mock_fetch.assert_called_once_with("/gene/entrezId/7157")

    @pytest.mark.asyncio
    async def test_api_error_404(self):
        """Test error handling when gene not found (404)."""
        import httpx

        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=AsyncMock()
            )
            result = await get_gene_by_entrez_id("99999999")
            assert "Error fetching gene data" in result

    @pytest.mark.asyncio
    async def test_api_error_500(self):
        """Test error handling when server error occurs (500)."""
        import httpx

        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "500 Internal Server Error", request=AsyncMock(), response=AsyncMock()
            )
            result = await get_gene_by_entrez_id("7157")
            assert "Error fetching gene data" in result

    @pytest.mark.asyncio
    async def test_correct_url_construction(self):
        """Test that the function builds the correct API endpoint."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"entrezId": "672", "symbol": "BRCA1"}
            await get_gene_by_entrez_id("672")
            mock_fetch.assert_called_once_with("/gene/entrezId/672")

    @pytest.mark.asyncio
    async def test_response_parsing_and_string_conversion(self):
        """Test that response is properly converted to string."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            complex_response = {
                "entrezId": "7157",
                "symbol": "TP53",
                "transcripts": [{"id": "NM_000546", "version": 5}],
                "summary": "This gene encodes a tumor suppressor protein",
            }
            mock_fetch.return_value = complex_response
            result = await get_gene_by_entrez_id("7157")
            assert isinstance(result, str)
            assert "TP53" in result
            assert "NM_000546" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_tp53(self):
        """Integration test with real API for TP53 gene."""
        result = await get_gene_by_entrez_id("7157")
        assert isinstance(result, str)
        assert "TP53" in result or "7157" in result


class TestGetGeneBySymbol:
    """Test the get_gene_by_symbol function."""

    @pytest.mark.asyncio
    async def test_successful_query_default_taxon(self):
        """Test successful gene query with default human taxon ID."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {
                "symbol": "BRCA1",
                "entrezId": "672",
                "name": "BRCA1 DNA repair associated",
                "taxonId": "9606",
            }
            result = await get_gene_by_symbol("BRCA1", "9606")
            assert "BRCA1" in result
            assert "672" in result
            mock_fetch.assert_called_once_with("/gene/taxonId/9606/symbol/BRCA1")

    @pytest.mark.asyncio
    async def test_query_with_custom_taxon_mouse(self):
        """Test gene query with mouse taxon ID."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {
                "symbol": "Trp53",
                "entrezId": "22059",
                "name": "transformation related protein 53",
                "taxonId": "10090",
            }
            result = await get_gene_by_symbol("Trp53", "10090")
            assert "Trp53" in result
            assert "22059" in result
            mock_fetch.assert_called_once_with("/gene/taxonId/10090/symbol/Trp53")

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test error handling when gene symbol not found."""
        import httpx

        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=AsyncMock()
            )
            result = await get_gene_by_symbol("NONEXISTENT", "9606")
            assert "Error fetching gene data" in result

    @pytest.mark.asyncio
    async def test_correct_url_construction_with_parameters(self):
        """Test that URL is correctly constructed with taxon and symbol."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"symbol": "TP53", "taxonId": "9606"}
            await get_gene_by_symbol("TP53", "9606")
            mock_fetch.assert_called_once_with("/gene/taxonId/9606/symbol/TP53")

    @pytest.mark.asyncio
    async def test_response_string_conversion(self):
        """Test that complex response is converted to string."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            complex_response = {
                "symbol": "CFTR",
                "entrezId": "1080",
                "aliases": ["ABC35", "ABCC7", "CF"],
                "taxonId": "9606",
            }
            mock_fetch.return_value = complex_response
            result = await get_gene_by_symbol("CFTR", "9606")
            assert isinstance(result, str)
            assert "CFTR" in result
            assert "1080" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_brca1(self):
        """Integration test with real API for BRCA1 gene."""
        result = await get_gene_by_symbol("BRCA1", "9606")
        assert isinstance(result, str)
        assert "BRCA1" in result or "672" in result


class TestGetGeneByPosition:
    """Test the get_gene_by_position function."""

    @pytest.mark.asyncio
    async def test_successful_query(self):
        """Test successful gene query by genomic position."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {
                "genes": [
                    {
                        "symbol": "TP53",
                        "entrezId": "7157",
                        "chromosome": "chr17",
                        "start": 7571720,
                        "end": 7590868,
                    }
                ],
                "position": 7577121,
            }
            result = await get_gene_by_position("chr17", 7577121)
            assert "TP53" in result
            assert "chr17" in result
            mock_fetch.assert_called_once_with("/gene/chr/chr17/pos/7577121")

    @pytest.mark.asyncio
    async def test_api_error_handling(self):
        """Test error handling when position is invalid."""
        import httpx

        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.side_effect = httpx.HTTPStatusError(
                "404 Not Found", request=AsyncMock(), response=AsyncMock()
            )
            result = await get_gene_by_position("chr99", 99999999)
            assert "Error fetching gene data" in result

    @pytest.mark.asyncio
    async def test_correct_url_construction_with_chr_and_position(self):
        """Test URL construction with chromosome and position parameters."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"genes": [], "position": 32900000}
            await get_gene_by_position("chr13", 32900000)
            mock_fetch.assert_called_once_with("/gene/chr/chr13/pos/32900000")

    @pytest.mark.asyncio
    async def test_response_parsing_with_empty_result(self):
        """Test response parsing when no genes found at position."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"genes": [], "position": 1000000, "chromosome": "chr1"}
            result = await get_gene_by_position("chr1", 1000000)
            assert isinstance(result, str)
            assert "genes" in result.lower() or "[]" in result

    @pytest.mark.asyncio
    async def test_response_with_multiple_genes(self):
        """Test response when multiple genes overlap at position."""
        with patch("src.tools.gene_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {
                "genes": [
                    {"symbol": "GENE1", "entrezId": "1001"},
                    {"symbol": "GENE2", "entrezId": "1002"},
                ],
                "position": 5000000,
            }
            result = await get_gene_by_position("chrX", 5000000)
            assert isinstance(result, str)
            assert "GENE1" in result
            assert "GENE2" in result

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_tp53_region(self):
        """Integration test with real API for TP53 chromosomal region.

        Note: The MARRVEL API gene position endpoint currently returns empty results.
        This test verifies the endpoint is accessible and returns valid JSON.
        """
        result = await get_gene_by_position("chr17", 7577121)
        assert isinstance(result, str)
        # API currently returns [] for position queries, so we just verify it's valid JSON
        assert result == "[]"
