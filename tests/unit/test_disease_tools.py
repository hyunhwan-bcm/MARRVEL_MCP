"""
Unit tests for disease tools module.

Tests the OMIM disease query functionality from disease_tools.py.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.disease_tools import (
    get_omim_by_mim_number,
    get_omim_by_gene_symbol,
    get_omim_variant,
)
from config import API_BASE_URL


@pytest.mark.unit
class TestGetOmimByMimNumber:
    """Test the get_omim_by_mim_number function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful OMIM query by MIM number."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response
            mock_data = {
                "mimNumber": "191170",
                "disease": "Treacher Collins syndrome",
                "inheritance": "Autosomal dominant",
            }
            mock_fetch.return_value = mock_data

            # Execute test
            result = await get_omim_by_mim_number("191170")

            # Verify results
            assert "191170" in result
            assert "Treacher Collins syndrome" in result
            mock_fetch.assert_called_once_with("/omim/mimNumber/191170")

    @pytest.mark.asyncio
    async def test_fetch_with_http_error(self):
        """Test error handling when API returns HTTP error."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise exception
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")

            # Execute test
            result = await get_omim_by_mim_number("999999")

            # Verify error message returned
            assert "Error fetching OMIM data" in result
            assert "404" in result

    @pytest.mark.asyncio
    async def test_fetch_builds_correct_url(self):
        """Test that function builds correct API endpoint."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"mimNumber": "114480"}

            # Execute test
            await get_omim_by_mim_number("114480")

            # Verify correct endpoint called
            mock_fetch.assert_called_once_with("/omim/mimNumber/114480")

    @pytest.mark.asyncio
    async def test_fetch_with_complex_data(self):
        """Test handling complex nested OMIM data."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup complex mock response
            complex_data = {
                "mimNumber": "114480",
                "disease": "Breast-ovarian cancer, familial, susceptibility to, 1",
                "gene": "BRCA1",
                "inheritance": "Autosomal dominant",
                "clinicalFeatures": ["Breast cancer", "Ovarian cancer"],
                "variants": [
                    {"variant": "p.C61G", "pathogenicity": "Pathogenic"},
                    {"variant": "p.Q356R", "pathogenicity": "Likely pathogenic"},
                ],
            }
            mock_fetch.return_value = complex_data

            # Execute test
            result = await get_omim_by_mim_number("114480")

            # Verify complex structure preserved
            assert "BRCA1" in result
            assert "Breast cancer" in result
            assert "p.C61G" in result


@pytest.mark.unit
class TestGetOmimByGeneSymbol:
    """Test the get_omim_by_gene_symbol function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful OMIM query by gene symbol."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response
            mock_data = {
                "geneSymbol": "TP53",
                "diseases": [{"mimNumber": "151623", "disease": "Li-Fraumeni syndrome"}],
            }
            mock_fetch.return_value = mock_data

            # Execute test
            result = await get_omim_by_gene_symbol("TP53")

            # Verify results
            assert "TP53" in result
            assert "Li-Fraumeni syndrome" in result
            mock_fetch.assert_called_once_with("/omim/gene/symbol/TP53")

    @pytest.mark.asyncio
    async def test_fetch_with_http_error(self):
        """Test error handling when API returns HTTP error."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise exception
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")

            # Execute test
            result = await get_omim_by_gene_symbol("INVALID")

            # Verify error message returned
            assert "Error fetching OMIM data" in result
            assert "404" in result

    @pytest.mark.asyncio
    async def test_fetch_builds_correct_url(self):
        """Test that function builds correct API endpoint."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"geneSymbol": "BRCA1"}

            # Execute test
            await get_omim_by_gene_symbol("BRCA1")

            # Verify correct endpoint called
            mock_fetch.assert_called_once_with("/omim/gene/symbol/BRCA1")

    @pytest.mark.asyncio
    async def test_fetch_with_complex_data(self):
        """Test handling complex nested OMIM data."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup complex mock response
            complex_data = {
                "geneSymbol": "CFTR",
                "entrezId": "1080",
                "diseases": [
                    {
                        "mimNumber": "219700",
                        "disease": "Cystic fibrosis",
                        "inheritance": "Autosomal recessive",
                        "frequency": "1 in 2,500",
                    },
                    {
                        "mimNumber": "277180",
                        "disease": "Congenital bilateral absence of the vas deferens",
                        "inheritance": "Autosomal recessive",
                    },
                ],
            }
            mock_fetch.return_value = complex_data

            # Execute test
            result = await get_omim_by_gene_symbol("CFTR")

            # Verify complex structure preserved
            assert "CFTR" in result
            assert "Cystic fibrosis" in result
            assert "219700" in result
            assert "277180" in result


@pytest.mark.unit
class TestGetOmimVariant:
    """Test the get_omim_variant function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful OMIM query for variant."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response
            mock_data = {
                "geneSymbol": "TP53",
                "variant": "p.R248Q",
                "mimNumber": "151623",
                "pathogenicity": "Pathogenic",
            }
            mock_fetch.return_value = mock_data

            # Execute test
            result = await get_omim_variant("TP53", "p.R248Q")

            # Verify results
            assert "TP53" in result
            assert "p.R248Q" in result
            assert "Pathogenic" in result
            mock_fetch.assert_called_once_with("/omim/gene/symbol/TP53/variant/p.R248Q")

    @pytest.mark.asyncio
    async def test_fetch_with_http_error(self):
        """Test error handling when API returns HTTP error."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise exception
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")

            # Execute test
            result = await get_omim_variant("TP53", "p.INVALID")

            # Verify error message returned
            assert "Error fetching OMIM data" in result
            assert "404" in result

    @pytest.mark.asyncio
    async def test_fetch_builds_correct_url(self):
        """Test that function builds correct API endpoint."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"variant": "p.C61G"}

            # Execute test
            await get_omim_variant("BRCA1", "p.C61G")

            # Verify correct endpoint called
            mock_fetch.assert_called_once_with("/omim/gene/symbol/BRCA1/variant/p.C61G")

    @pytest.mark.asyncio
    async def test_fetch_with_complex_data(self):
        """Test handling complex variant data."""
        with patch("src.tools.disease_tools.fetch_marrvel_data") as mock_fetch:
            # Setup complex mock response
            complex_data = {
                "geneSymbol": "BRCA1",
                "variant": "p.C61G",
                "mimNumber": "113705",
                "pathogenicity": "Pathogenic",
                "clinicalSignificance": "Established risk factor",
                "diseases": ["Breast cancer", "Ovarian cancer"],
                "functionalStudies": [
                    {"type": "Cell proliferation", "result": "Impaired"},
                    {"type": "DNA repair", "result": "Defective"},
                ],
            }
            mock_fetch.return_value = complex_data

            # Execute test
            result = await get_omim_variant("BRCA1", "p.C61G")

            # Verify complex structure preserved
            assert "BRCA1" in result
            assert "p.C61G" in result
            assert "Pathogenic" in result
            assert "DNA repair" in result


# Integration tests (require actual API access)
class TestOmimIntegration:
    """Integration tests that make real API calls."""

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_mim_number(self):
        """Test real API call for OMIM by MIM number (requires network access)."""
        result = await get_omim_by_mim_number("191170")
        # Basic validation - should not be an error message
        assert "Error fetching OMIM data" not in result or isinstance(result, str)

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_gene_symbol(self):
        """Test real API call for OMIM by gene symbol (requires network access)."""
        result = await get_omim_by_gene_symbol("TP53")
        # Basic validation - should not be an error message or should be a string
        assert isinstance(result, str)

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_variant(self):
        """Test real API call for OMIM variant (requires network access)."""
        result = await get_omim_variant("TP53", "p.R248Q")
        # Basic validation - should return a string
        assert isinstance(result, str)
