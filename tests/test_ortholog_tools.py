"""
Unit tests for ortholog tools module.

Tests the DIOPT ortholog prediction functions for finding orthologs
across model organisms and protein sequence alignments.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.ortholog_tools import get_diopt_orthologs, get_diopt_alignment
from config import API_BASE_URL


@pytest.mark.unit
class TestGetDioptOrthologs:
    """Test the get_diopt_orthologs function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful API request with valid ortholog response."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response with ortholog data
            mock_response = {
                "entrezId": "7157",
                "symbol": "TP53",
                "orthologs": {
                    "mouse": {"symbol": "Trp53", "entrezId": "22059"},
                    "fly": {"symbol": "p53", "entrezId": "42967"},
                },
                "diopt_score": 15,
            }
            mock_fetch.return_value = mock_response

            # Execute test
            result = await get_diopt_orthologs("7157")

            # Verify results
            assert "7157" in result
            assert "TP53" in result
            assert "orthologs" in result
            mock_fetch.assert_called_once_with("/diopt/ortholog/gene/entrezId/7157")

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test error handling when API returns HTTP error."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")

            # Execute test
            result = await get_diopt_orthologs("999999")

            # Verify error message returned
            assert "Error fetching DIOPT data" in result
            assert "404" in result

    @pytest.mark.asyncio
    async def test_correct_endpoint(self):
        """Test that the function builds the correct API endpoint."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"result": "success"}

            # Execute test with specific Entrez ID
            await get_diopt_orthologs("672")

            # Verify correct endpoint was called
            mock_fetch.assert_called_once_with("/diopt/ortholog/gene/entrezId/672")

    @pytest.mark.asyncio
    async def test_response_conversion_to_string(self):
        """Test that the response is converted to string."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            mock_response = {"gene": "BRCA1", "orthologs": ["data"]}
            mock_fetch.return_value = mock_response

            # Execute test
            result = await get_diopt_orthologs("672")

            # Verify result is a string
            assert isinstance(result, str)
            assert "BRCA1" in result


@pytest.mark.unit
class TestGetDioptAlignment:
    """Test the get_diopt_alignment function."""

    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful API request with valid alignment response."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response with alignment data
            mock_response = {
                "entrezId": "7157",
                "symbol": "TP53",
                "alignment": {"human": "MEEPQSDPSVEPPLSQETF", "mouse": "MTAMEESQSDISLELPLSQ"},
                "conservation": "high",
            }
            mock_fetch.return_value = mock_response

            # Execute test
            result = await get_diopt_alignment("7157")

            # Verify results
            assert "7157" in result
            assert "TP53" in result
            assert "alignment" in result
            mock_fetch.assert_called_once_with("/diopt/alignment/gene/entrezId/7157")

    @pytest.mark.asyncio
    async def test_http_error_handling(self):
        """Test error handling when API returns HTTP error."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("500 Server Error")

            # Execute test
            result = await get_diopt_alignment("999999")

            # Verify error message returned
            assert "Error fetching DIOPT alignment data" in result
            assert "500" in result

    @pytest.mark.asyncio
    async def test_correct_endpoint(self):
        """Test that the function builds the correct API endpoint."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"result": "success"}

            # Execute test with specific Entrez ID
            await get_diopt_alignment("672")

            # Verify correct endpoint was called
            mock_fetch.assert_called_once_with("/diopt/alignment/gene/entrezId/672")

    @pytest.mark.asyncio
    async def test_response_conversion_to_string(self):
        """Test that the response is converted to string."""
        with patch("src.tools.ortholog_tools.fetch_marrvel_data") as mock_fetch:
            mock_response = {"gene": "BRCA1", "alignment": {"data": "sequence"}}
            mock_fetch.return_value = mock_response

            # Execute test
            result = await get_diopt_alignment("672")

            # Verify result is a string
            assert isinstance(result, str)
            assert "BRCA1" in result


# Integration tests (require actual API access)
class TestOrthologToolsIntegration:
    """Integration tests that make real API calls (marked for optional execution)."""

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_get_diopt_orthologs_tp53(self):
        """Test real API call for TP53 orthologs (requires network access)."""
        result = await get_diopt_orthologs("7157")
        # Result should be a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error message
        if "Error" not in result:
            assert "7157" in result or "TP53" in result.upper()

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_get_diopt_orthologs_brca1(self):
        """Test real API call for BRCA1 orthologs (requires network access)."""
        result = await get_diopt_orthologs("672")
        # Result should be a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error message
        if "Error" not in result:
            assert "672" in result or "BRCA1" in result.upper()

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_get_diopt_alignment_tp53(self):
        """Test real API call for TP53 alignment (requires network access)."""
        result = await get_diopt_alignment("7157")
        # Result should be a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error message
        if "Error" not in result:
            assert "7157" in result or "TP53" in result.upper()

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_get_diopt_alignment_brca1(self):
        """Test real API call for BRCA1 alignment (requires network access)."""
        result = await get_diopt_alignment("672")
        # Result should be a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error message
        if "Error" not in result:
            assert "672" in result or "BRCA1" in result.upper()
