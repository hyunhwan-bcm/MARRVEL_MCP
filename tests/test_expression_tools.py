"""
Unit and integration tests for expression tools module.

Tests the gene expression data functions including GTEx, ortholog expression,
and Pharos drug target information.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.expression_tools import (
    get_gtex_expression,
    get_ortholog_expression,
    get_pharos_targets,
)


# ============================================================================
# UNIT TESTS - GTEx Expression
# ============================================================================


@pytest.mark.unit
class TestGetGtexExpression:
    """Test the get_gtex_expression function with mocked API calls."""

    @pytest.mark.asyncio
    async def test_successful_gtex_fetch(self):
        """Test successful GTEx expression data retrieval."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response with GTEx data
            mock_data = {
                "entrezId": "7157",
                "symbol": "TP53",
                "tissues": [
                    {"name": "Brain", "median_tpm": 45.2, "samples": 150},
                    {"name": "Heart", "median_tpm": 32.1, "samples": 120},
                ],
            }
            mock_fetch.return_value = mock_data

            # Execute test
            result = await get_gtex_expression("7157")

            # Verify results
            assert "7157" in result
            assert "TP53" in result
            assert "Brain" in result
            mock_fetch.assert_called_once_with("/gtex/gene/entrezId/7157")

    @pytest.mark.asyncio
    async def test_gtex_with_http_error(self):
        """Test GTEx function handles HTTP errors gracefully."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")

            # Execute test
            result = await get_gtex_expression("99999")

            # Verify error message returned
            assert "Error fetching GTEx data" in result
            assert "404" in result

    @pytest.mark.asyncio
    async def test_gtex_with_empty_data(self):
        """Test GTEx function with empty response data."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock with empty data
            mock_fetch.return_value = {}

            # Execute test
            result = await get_gtex_expression("7157")

            # Verify result is string representation
            assert isinstance(result, str)
            assert result == "{}"

    @pytest.mark.asyncio
    async def test_gtex_with_complex_tissue_data(self):
        """Test GTEx function with complex nested tissue expression data."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock with complex nested data
            complex_data = {
                "entrezId": "672",
                "symbol": "BRCA1",
                "tissues": [
                    {
                        "name": "Breast",
                        "median_tpm": 78.5,
                        "samples": 200,
                        "quartiles": {"q1": 65.2, "q3": 92.1},
                    }
                ],
                "metadata": {"version": "v8", "release_date": "2023"},
            }
            mock_fetch.return_value = complex_data

            # Execute test
            result = await get_gtex_expression("672")

            # Verify complex structure preserved in string
            assert "672" in result
            assert "BRCA1" in result
            assert "Breast" in result
            assert "quartiles" in result


# ============================================================================
# UNIT TESTS - Ortholog Expression
# ============================================================================


@pytest.mark.unit
class TestGetOrthologExpression:
    """Test the get_ortholog_expression function with mocked API calls."""

    @pytest.mark.asyncio
    async def test_successful_ortholog_expression_fetch(self):
        """Test successful ortholog expression data retrieval."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response with ortholog expression data
            mock_data = {
                "entrezId": "7157",
                "symbol": "TP53",
                "orthologs": [
                    {
                        "organism": "mouse",
                        "gene": "Trp53",
                        "expression": {"brain": "high", "liver": "medium"},
                    },
                    {
                        "organism": "fly",
                        "gene": "p53",
                        "expression": {"embryo": "high", "adult": "low"},
                    },
                ],
            }
            mock_fetch.return_value = mock_data

            # Execute test
            result = await get_ortholog_expression("7157")

            # Verify results
            assert "7157" in result
            assert "TP53" in result
            assert "mouse" in result
            assert "fly" in result
            mock_fetch.assert_called_once_with("/expression/orthologs/gene/entrezId/7157")

    @pytest.mark.asyncio
    async def test_ortholog_expression_with_http_error(self):
        """Test ortholog expression function handles HTTP errors gracefully."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("500 Server Error")

            # Execute test
            result = await get_ortholog_expression("12345")

            # Verify error message returned
            assert "Error fetching ortholog expression data" in result
            assert "500" in result

    @pytest.mark.asyncio
    async def test_ortholog_expression_with_no_orthologs(self):
        """Test ortholog expression function with gene having no orthologs."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock with no orthologs
            mock_fetch.return_value = {"entrezId": "7157", "orthologs": []}

            # Execute test
            result = await get_ortholog_expression("7157")

            # Verify result is string representation
            assert isinstance(result, str)
            assert "7157" in result
            assert "orthologs" in result

    @pytest.mark.asyncio
    async def test_ortholog_expression_with_developmental_stages(self):
        """Test ortholog expression with developmental stage data."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock with developmental stage data
            complex_data = {
                "entrezId": "672",
                "symbol": "BRCA1",
                "orthologs": [
                    {
                        "organism": "zebrafish",
                        "gene": "brca1",
                        "developmental_stages": [
                            {"stage": "embryo_1dpf", "expression": "high"},
                            {"stage": "embryo_2dpf", "expression": "medium"},
                            {"stage": "adult", "expression": "low"},
                        ],
                    }
                ],
            }
            mock_fetch.return_value = complex_data

            # Execute test
            result = await get_ortholog_expression("672")

            # Verify complex structure preserved
            assert "672" in result
            assert "zebrafish" in result
            assert "developmental_stages" in result
            assert "embryo_1dpf" in result


# ============================================================================
# UNIT TESTS - Pharos Targets
# ============================================================================


@pytest.mark.unit
class TestGetPharosTargets:
    """Test the get_pharos_targets function with mocked API calls."""

    @pytest.mark.asyncio
    async def test_successful_pharos_fetch(self):
        """Test successful Pharos drug target data retrieval."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response with Pharos data
            mock_data = {
                "entrezId": "7157",
                "symbol": "TP53",
                "targetLevel": "Tclin",
                "drugs": [
                    {"name": "Compound A", "phase": "Phase II"},
                    {"name": "Compound B", "phase": "Phase III"},
                ],
                "druggability": "high",
            }
            mock_fetch.return_value = mock_data

            # Execute test
            result = await get_pharos_targets("7157")

            # Verify results
            assert "7157" in result
            assert "TP53" in result
            assert "Tclin" in result
            assert "Compound A" in result
            mock_fetch.assert_called_once_with("/pharos/targets/gene/entrezId/7157")

    @pytest.mark.asyncio
    async def test_pharos_with_http_error(self):
        """Test Pharos function handles HTTP errors gracefully."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            import httpx

            mock_fetch.side_effect = httpx.HTTPError("403 Forbidden")

            # Execute test
            result = await get_pharos_targets("88888")

            # Verify error message returned
            assert "Error fetching Pharos data" in result
            assert "403" in result

    @pytest.mark.asyncio
    async def test_pharos_with_tdark_target(self):
        """Test Pharos function with understudied (Tdark) target."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock with Tdark target
            mock_fetch.return_value = {
                "entrezId": "54321",
                "symbol": "UNKNOWN_GENE",
                "targetLevel": "Tdark",
                "drugs": [],
                "druggability": "unknown",
            }

            # Execute test
            result = await get_pharos_targets("54321")

            # Verify Tdark classification
            assert "54321" in result
            assert "Tdark" in result
            assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_pharos_with_clinical_trials(self):
        """Test Pharos function with detailed clinical trial information."""
        with patch("src.tools.expression_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock with clinical trial data
            complex_data = {
                "entrezId": "672",
                "symbol": "BRCA1",
                "targetLevel": "Tclin",
                "targetClass": "DNA repair",
                "targetFamily": "Tumor suppressor",
                "drugs": [
                    {"name": "Olaparib", "phase": "FDA Approved", "mechanism": "PARP inhibitor"}
                ],
                "clinical_trials": [
                    {"nct_id": "NCT12345", "status": "Active", "phase": "Phase III"}
                ],
            }
            mock_fetch.return_value = complex_data

            # Execute test
            result = await get_pharos_targets("672")

            # Verify complex clinical data preserved
            assert "672" in result
            assert "BRCA1" in result
            assert "Olaparib" in result
            assert "PARP inhibitor" in result
            assert "clinical_trials" in result


# ============================================================================
# INTEGRATION TESTS (Real API calls)
# ============================================================================


class TestExpressionToolsIntegration:
    """Integration tests that make real API calls (marked for optional execution)."""

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_gtex_expression_tp53(self):
        """Test real GTEx API call for TP53 gene (requires network access)."""
        result = await get_gtex_expression("7157")
        # Should return data or error message, not crash
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_ortholog_expression_tp53(self):
        """Test real ortholog expression API call for TP53 (requires network access)."""
        result = await get_ortholog_expression("7157")
        # Should return data or error message, not crash
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_pharos_targets_tp53(self):
        """Test real Pharos API call for TP53 gene (requires network access)."""
        result = await get_pharos_targets("7157")
        # Should return data or error message, not crash
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_invalid_entrez_id(self):
        """Test real API calls with invalid Entrez ID (requires network access)."""
        # All functions should handle invalid IDs gracefully
        result1 = await get_gtex_expression("invalid_id_999999")
        result2 = await get_ortholog_expression("invalid_id_999999")
        result3 = await get_pharos_targets("invalid_id_999999")

        # Should all return error messages or empty data, not crash
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert isinstance(result3, str)
