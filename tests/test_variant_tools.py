"""
Comprehensive tests for variant analysis tools.

Tests all 13 variant annotation functions in src/tools/variant_tools.py:
- dbNSFP (1 function)
- ClinVar (3 functions) 
- gnomAD (3 functions)
- DGV (2 functions)
- DECIPHER (2 functions)
- Geno2MP (2 functions)

Each function has:
- Unit tests with mocked API responses (success, error, URL validation, data structure)
- Integration tests with real API (marked with @pytest.mark.integration)
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.variant_tools import (
    get_variant_dbnsfp,
    get_clinvar_by_variant,
    get_clinvar_by_gene_symbol,
    get_clinvar_by_entrez_id,
    get_gnomad_variant,
    get_gnomad_by_gene_symbol,
    get_gnomad_by_entrez_id,
    get_dgv_variant,
    get_dgv_by_entrez_id,
    get_decipher_variant,
    get_decipher_by_location,
    get_geno2mp_variant,
    get_geno2mp_by_entrez_id,
)
from config import API_BASE_URL


# ============================================================================
# dbNSFP Tests (1 function)
# ============================================================================

class TestGetVariantDbNSFP:
    """Test get_variant_dbnsfp function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful dbNSFP variant query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            # Setup mock response with typical dbNSFP data
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "gene": "TP53",
                "sift_score": 0.01,
                "polyphen2_score": 0.99,
                "cadd_score": 25.3,
                "gerp_score": 4.5
            }
            
            result = await get_variant_dbnsfp("17-7577121-C-T")
            
            # Verify fetch was called with correct endpoint
            mock_fetch.assert_called_once_with("/dbnsfp/variant/17-7577121-C-T")
            # Verify result contains expected data
            assert "17-7577121-C-T" in result
            assert "TP53" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling when API returns HTTP error."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_variant_dbnsfp("invalid-variant")
            
            # Verify error message is returned
            assert "Error fetching dbNSFP data" in result
            assert "404" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test that correct API endpoint is constructed."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_variant_dbnsfp("13-32900000-G-A")
            
            mock_fetch.assert_called_once_with("/dbnsfp/variant/13-32900000-G-A")
    
    @pytest.mark.asyncio
    async def test_with_complex_data_structure(self):
        """Test handling of complex nested response data."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            complex_data = {
                "variant": "17-7577121-C-T",
                "predictions": {
                    "sift": {"score": 0.01, "prediction": "deleterious"},
                    "polyphen2": {"score": 0.99, "prediction": "probably_damaging"}
                },
                "conservation": [
                    {"method": "GERP++", "score": 4.5},
                    {"method": "PhyloP", "score": 2.1}
                ]
            }
            mock_fetch.return_value = complex_data
            
            result = await get_variant_dbnsfp("17-7577121-C-T")
            
            # Verify complex structure is preserved in result string
            assert "predictions" in result
            assert "conservation" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_tp53_variant(self):
        """Integration test with real API for TP53 variant."""
        result = await get_variant_dbnsfp("17-7577121-C-T")
        
        # Result should be a non-empty string
        assert isinstance(result, str)
        assert len(result) > 0
        # Should not be an error message (real API may return empty data, but not error)
        assert not result.startswith("Error fetching")


# ============================================================================
# ClinVar Tests (3 functions)
# ============================================================================

class TestGetClinVarByVariant:
    """Test get_clinvar_by_variant function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful ClinVar variant query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "clinical_significance": "Pathogenic",
                "review_status": "criteria provided, multiple submitters",
                "conditions": ["Li-Fraumeni syndrome"]
            }
            
            result = await get_clinvar_by_variant("17-7577121-C-T")
            
            mock_fetch.assert_called_once_with("/clinvar/variant/17-7577121-C-T")
            assert "Pathogenic" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("500 Server Error")
            
            result = await get_clinvar_by_variant("17-7577121-C-T")
            
            assert "Error fetching ClinVar data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_clinvar_by_variant("chr1-12345-A-G")
            
            mock_fetch.assert_called_once_with("/clinvar/variant/chr1-12345-A-G")
    
    @pytest.mark.asyncio
    async def test_vus_significance(self):
        """Test variant of uncertain significance response."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "clinical_significance": "Uncertain significance",
                "review_status": "no assertion criteria provided"
            }
            
            result = await get_clinvar_by_variant("17-7577121-C-T")
            
            assert "Uncertain significance" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_tp53_variant(self):
        """Integration test with real API."""
        result = await get_clinvar_by_variant("17-7577121-C-T")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetClinVarByGeneSymbol:
    """Test get_clinvar_by_gene_symbol function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful ClinVar gene query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "gene": "TP53",
                "variants": [
                    {"variant": "17-7577121-C-T", "significance": "Pathogenic"},
                    {"variant": "17-7578406-C-T", "significance": "Pathogenic"}
                ]
            }
            
            result = await get_clinvar_by_gene_symbol("TP53")
            
            mock_fetch.assert_called_once_with("/clinvar/gene/symbol/TP53")
            assert "TP53" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_clinvar_by_gene_symbol("INVALID")
            
            assert "Error fetching ClinVar data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_clinvar_by_gene_symbol("BRCA1")
            
            mock_fetch.assert_called_once_with("/clinvar/gene/symbol/BRCA1")
    
    @pytest.mark.asyncio
    async def test_with_multiple_variants(self):
        """Test response with multiple variants."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "gene": "BRCA1",
                "total_variants": 1500,
                "variants": [{"variant": f"17-{41200000+i}-A-G"} for i in range(10)]
            }
            
            result = await get_clinvar_by_gene_symbol("BRCA1")
            
            assert "BRCA1" in result
            assert "1500" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_tp53_gene(self):
        """Integration test with real API."""
        result = await get_clinvar_by_gene_symbol("TP53")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetClinVarByEntrezId:
    """Test get_clinvar_by_entrez_id function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful ClinVar query by Entrez ID."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "variants": [{"variant": "17-7577121-C-T"}]
            }
            
            result = await get_clinvar_by_entrez_id("7157")
            
            mock_fetch.assert_called_once_with("/clinvar/gene/entrezId/7157")
            assert "7157" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_clinvar_by_entrez_id("99999999")
            
            assert "Error fetching ClinVar data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_clinvar_by_entrez_id("672")
            
            mock_fetch.assert_called_once_with("/clinvar/gene/entrezId/672")
    
    @pytest.mark.asyncio
    async def test_with_numeric_string(self):
        """Test with numeric string input."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {"entrez_id": "7157"}
            
            result = await get_clinvar_by_entrez_id("7157")
            
            assert "7157" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_tp53_entrez(self):
        """Integration test with real API for TP53 Entrez ID."""
        result = await get_clinvar_by_entrez_id("7157")
        
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# gnomAD Tests (3 functions)
# ============================================================================

class TestGetGnomadVariant:
    """Test get_gnomad_variant function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful gnomAD variant query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "allele_frequency": 0.0001,
                "allele_count": 10,
                "allele_number": 100000,
                "populations": {
                    "AFR": {"af": 0.0002},
                    "EUR": {"af": 0.0001}
                }
            }
            
            result = await get_gnomad_variant("17-7577121-C-T")
            
            mock_fetch.assert_called_once_with("/gnomad/variant/17-7577121-C-T")
            assert "0.0001" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_gnomad_variant("invalid")
            
            assert "Error fetching gnomAD data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_gnomad_variant("1-12345-A-T")
            
            mock_fetch.assert_called_once_with("/gnomad/variant/1-12345-A-T")
    
    @pytest.mark.asyncio
    async def test_population_frequencies(self):
        """Test response with population-specific frequencies."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "populations": {
                    "AFR": {"af": 0.0005, "ac": 5, "an": 10000},
                    "AMR": {"af": 0.0003, "ac": 3, "an": 10000},
                    "EAS": {"af": 0.0001, "ac": 1, "an": 10000}
                }
            }
            
            result = await get_gnomad_variant("17-7577121-C-T")
            
            assert "AFR" in result
            assert "AMR" in result
            assert "EAS" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_variant(self):
        """Integration test with real API."""
        result = await get_gnomad_variant("17-7577121-C-T")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetGnomadByGeneSymbol:
    """Test get_gnomad_by_gene_symbol function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful gnomAD gene query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "gene": "TP53",
                "variants": [
                    {"variant": "17-7577121-C-T", "af": 0.0001},
                    {"variant": "17-7578406-C-T", "af": 0.0002}
                ]
            }
            
            result = await get_gnomad_by_gene_symbol("TP53")
            
            mock_fetch.assert_called_once_with("/gnomad/gene/symbol/TP53")
            assert "TP53" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("500 Server Error")
            
            result = await get_gnomad_by_gene_symbol("INVALID")
            
            assert "Error fetching gnomAD data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_gnomad_by_gene_symbol("BRCA2")
            
            mock_fetch.assert_called_once_with("/gnomad/gene/symbol/BRCA2")
    
    @pytest.mark.asyncio
    async def test_with_many_variants(self):
        """Test gene with many variants."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "gene": "CFTR",
                "total": 5000,
                "variants": [{"variant": f"7-{117000000+i}-A-G"} for i in range(100)]
            }
            
            result = await get_gnomad_by_gene_symbol("CFTR")
            
            assert "CFTR" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_gene(self):
        """Integration test with real API."""
        result = await get_gnomad_by_gene_symbol("TP53")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetGnomadByEntrezId:
    """Test get_gnomad_by_entrez_id function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful gnomAD query by Entrez ID."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "variants": [{"variant": "17-7577121-C-T"}]
            }
            
            result = await get_gnomad_by_entrez_id("7157")
            
            mock_fetch.assert_called_once_with("/gnomad/gene/entrezId/7157")
            assert "7157" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_gnomad_by_entrez_id("99999999")
            
            assert "Error fetching gnomAD data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_gnomad_by_entrez_id("675")
            
            mock_fetch.assert_called_once_with("/gnomad/gene/entrezId/675")
    
    @pytest.mark.asyncio
    async def test_with_constraint_metrics(self):
        """Test response with gene constraint metrics."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "constraint": {
                    "pLI": 0.95,
                    "LOEUF": 0.05
                }
            }
            
            result = await get_gnomad_by_entrez_id("7157")
            
            assert "constraint" in result
            assert "pLI" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_entrez(self):
        """Integration test with real API."""
        result = await get_gnomad_by_entrez_id("7157")
        
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# DGV Tests (2 functions)
# ============================================================================

class TestGetDgvVariant:
    """Test get_dgv_variant function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful DGV variant query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "structural_variants": [
                    {"type": "CNV", "size": 50000}
                ]
            }
            
            result = await get_dgv_variant("17-7577121-C-T")
            
            mock_fetch.assert_called_once_with("/dgv/variant/17-7577121-C-T")
            assert "CNV" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_dgv_variant("invalid")
            
            assert "Error fetching DGV data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_dgv_variant("1-12345-A-T")
            
            mock_fetch.assert_called_once_with("/dgv/variant/1-12345-A-T")
    
    @pytest.mark.asyncio
    async def test_structural_variant_types(self):
        """Test different structural variant types."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "structural_variants": [
                    {"type": "deletion", "size": 10000},
                    {"type": "duplication", "size": 25000},
                    {"type": "inversion", "size": 50000}
                ]
            }
            
            result = await get_dgv_variant("17-7577121-C-T")
            
            assert "deletion" in result
            assert "duplication" in result
            assert "inversion" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_variant(self):
        """Integration test with real API."""
        result = await get_dgv_variant("17-7577121-C-T")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetDgvByEntrezId:
    """Test get_dgv_by_entrez_id function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful DGV query by Entrez ID."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "structural_variants": [{"type": "CNV"}]
            }
            
            result = await get_dgv_by_entrez_id("7157")
            
            mock_fetch.assert_called_once_with("/dgv/gene/entrezId/7157")
            assert "7157" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("500 Server Error")
            
            result = await get_dgv_by_entrez_id("99999999")
            
            assert "Error fetching DGV data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_dgv_by_entrez_id("672")
            
            mock_fetch.assert_called_once_with("/dgv/gene/entrezId/672")
    
    @pytest.mark.asyncio
    async def test_multiple_sv_regions(self):
        """Test gene region with multiple structural variants."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "structural_variants": [
                    {"id": "dgv1", "type": "deletion"},
                    {"id": "dgv2", "type": "duplication"},
                    {"id": "dgv3", "type": "CNV"}
                ]
            }
            
            result = await get_dgv_by_entrez_id("7157")
            
            assert "dgv1" in result
            assert "dgv2" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_entrez(self):
        """Integration test with real API."""
        result = await get_dgv_by_entrez_id("7157")
        
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# DECIPHER Tests (2 functions)
# ============================================================================

class TestGetDecipherVariant:
    """Test get_decipher_variant function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful DECIPHER variant query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "patients": [
                    {"id": "12345", "phenotypes": ["developmental delay"]}
                ]
            }
            
            result = await get_decipher_variant("17-7577121-C-T")
            
            mock_fetch.assert_called_once_with("/decipher/variant/17-7577121-C-T")
            assert "developmental delay" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_decipher_variant("invalid")
            
            assert "Error fetching DECIPHER data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_decipher_variant("1-12345-A-T")
            
            mock_fetch.assert_called_once_with("/decipher/variant/1-12345-A-T")
    
    @pytest.mark.asyncio
    async def test_developmental_disorder_data(self):
        """Test response with developmental disorder information."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "patients": [
                    {
                        "id": "12345",
                        "phenotypes": ["intellectual disability", "seizures"],
                        "inheritance": "de novo"
                    }
                ]
            }
            
            result = await get_decipher_variant("17-7577121-C-T")
            
            assert "intellectual disability" in result
            assert "de novo" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_variant(self):
        """Integration test with real API."""
        result = await get_decipher_variant("17-7577121-C-T")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetDecipherByLocation:
    """Test get_decipher_by_location function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful DECIPHER location query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "chromosome": "chr17",
                "start": 7570000,
                "stop": 7590000,
                "variants": [{"position": 7577121}]
            }
            
            result = await get_decipher_by_location("chr17", 7570000, 7590000)
            
            mock_fetch.assert_called_once_with("/decipher/genomloc/chr17/7570000/7590000")
            assert "chr17" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("400 Bad Request")
            
            result = await get_decipher_by_location("chrInvalid", 100, 200)
            
            assert "Error fetching DECIPHER data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction with different parameters."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_decipher_by_location("chr1", 1000000, 2000000)
            
            mock_fetch.assert_called_once_with("/decipher/genomloc/chr1/1000000/2000000")
    
    @pytest.mark.asyncio
    async def test_large_region(self):
        """Test query for large genomic region."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "chromosome": "chr17",
                "start": 7000000,
                "stop": 8000000,
                "variants": [{"position": 7500000 + i * 1000} for i in range(100)]
            }
            
            result = await get_decipher_by_location("chr17", 7000000, 8000000)
            
            assert "chr17" in result
            assert "7000000" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_location(self):
        """Integration test with real API for TP53 region."""
        result = await get_decipher_by_location("chr17", 7570000, 7590000)
        
        assert isinstance(result, str)
        assert len(result) > 0


# ============================================================================
# Geno2MP Tests (2 functions)
# ============================================================================

class TestGetGeno2mpVariant:
    """Test get_geno2mp_variant function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful Geno2MP variant query."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "phenotypes": [
                    {"hpo_id": "HP:0002664", "term": "Neoplasm"}
                ]
            }
            
            result = await get_geno2mp_variant("17-7577121-C-T")
            
            mock_fetch.assert_called_once_with("/geno2mp/variant/17-7577121-C-T")
            assert "Neoplasm" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")
            
            result = await get_geno2mp_variant("invalid")
            
            assert "Error fetching Geno2MP data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_geno2mp_variant("1-12345-A-T")
            
            mock_fetch.assert_called_once_with("/geno2mp/variant/1-12345-A-T")
    
    @pytest.mark.asyncio
    async def test_multiple_hpo_terms(self):
        """Test variant with multiple HPO phenotype terms."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "variant": "17-7577121-C-T",
                "phenotypes": [
                    {"hpo_id": "HP:0002664", "term": "Neoplasm"},
                    {"hpo_id": "HP:0001249", "term": "Intellectual disability"},
                    {"hpo_id": "HP:0001263", "term": "Global developmental delay"}
                ]
            }
            
            result = await get_geno2mp_variant("17-7577121-C-T")
            
            assert "HP:0002664" in result
            assert "HP:0001249" in result
            assert "HP:0001263" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_variant(self):
        """Integration test with real API."""
        result = await get_geno2mp_variant("17-7577121-C-T")
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestGetGeno2mpByEntrezId:
    """Test get_geno2mp_by_entrez_id function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful Geno2MP query by Entrez ID."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "phenotypes": [{"hpo_id": "HP:0002664", "term": "Neoplasm"}]
            }
            
            result = await get_geno2mp_by_entrez_id("7157")
            
            mock_fetch.assert_called_once_with("/geno2mp/gene/entrezId/7157")
            assert "7157" in result
    
    @pytest.mark.asyncio
    async def test_with_http_error(self):
        """Test error handling."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            import httpx
            mock_fetch.side_effect = httpx.HTTPError("500 Server Error")
            
            result = await get_geno2mp_by_entrez_id("99999999")
            
            assert "Error fetching Geno2MP data" in result
    
    @pytest.mark.asyncio
    async def test_builds_correct_endpoint(self):
        """Test endpoint construction."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {}
            
            await get_geno2mp_by_entrez_id("672")
            
            mock_fetch.assert_called_once_with("/geno2mp/gene/entrezId/672")
    
    @pytest.mark.asyncio
    async def test_gene_phenotype_associations(self):
        """Test gene with multiple phenotype associations."""
        with patch('src.tools.variant_tools.fetch_marrvel_data') as mock_fetch:
            mock_fetch.return_value = {
                "entrez_id": "7157",
                "gene": "TP53",
                "phenotypes": [
                    {"hpo_id": "HP:0002664", "term": "Neoplasm", "frequency": "Very frequent"},
                    {"hpo_id": "HP:0000006", "term": "Autosomal dominant", "frequency": "Obligate"}
                ]
            }
            
            result = await get_geno2mp_by_entrez_id("7157")
            
            assert "Very frequent" in result
            assert "Autosomal dominant" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_entrez(self):
        """Integration test with real API for TP53."""
        result = await get_geno2mp_by_entrez_id("7157")
        
        assert isinstance(result, str)
        assert len(result) > 0
