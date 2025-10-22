"""
Unit tests for utility tools module.

Tests the variant nomenclature validation and conversion functions.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.utility_tools import validate_hgvs_variant, convert_protein_variant


@pytest.mark.unit
class TestValidateHgvsVariant:
    """Test the validate_hgvs_variant function."""

    @pytest.mark.asyncio
    async def test_validate_genomic_variant(self):
        """Test validation of genomic HGVS variant."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for valid genomic variant
            mock_fetch.return_value = {
                "valid": True,
                "variant": "NC_000017.10:g.7577121C>T",
                "type": "genomic",
                "chromosome": "17",
                "position": 7577121,
                "reference": "C",
                "alternative": "T",
            }

            # Execute test
            result = await validate_hgvs_variant("NC_000017.10:g.7577121C>T")

            # Verify results
            assert "valid" in str(result)
            assert "NC_000017.10:g.7577121C>T" in str(result)
            mock_fetch.assert_called_once_with("/mutalyzer/hgvs/NC_000017.10:g.7577121C>T")

    @pytest.mark.asyncio
    async def test_validate_coding_variant(self):
        """Test validation of coding (c.) HGVS variant."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for valid coding variant
            mock_fetch.return_value = {
                "valid": True,
                "variant": "NM_000546.5:c.215C>G",
                "type": "coding",
                "gene": "TP53",
                "transcript": "NM_000546.5",
                "position": 215,
                "reference": "C",
                "alternative": "G",
                "protein_change": "p.Arg72Pro",
            }

            # Execute test
            result = await validate_hgvs_variant("NM_000546.5:c.215C>G")

            # Verify results
            assert "valid" in str(result)
            assert "NM_000546.5:c.215C>G" in str(result)
            mock_fetch.assert_called_once_with("/mutalyzer/hgvs/NM_000546.5:c.215C>G")

    @pytest.mark.asyncio
    async def test_validate_protein_variant(self):
        """Test validation of protein (p.) HGVS variant."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for valid protein variant
            mock_fetch.return_value = {
                "valid": True,
                "variant": "NP_000537.3:p.Arg72Pro",
                "type": "protein",
                "protein": "NP_000537.3",
                "position": 72,
                "reference_aa": "Arg",
                "alternative_aa": "Pro",
            }

            # Execute test
            result = await validate_hgvs_variant("NP_000537.3:p.Arg72Pro")

            # Verify results
            assert "valid" in str(result)
            assert "NP_000537.3:p.Arg72Pro" in str(result)
            mock_fetch.assert_called_once_with("/mutalyzer/hgvs/NP_000537.3:p.Arg72Pro")

    @pytest.mark.asyncio
    async def test_validate_invalid_variant(self):
        """Test validation of invalid HGVS variant nomenclature."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for invalid variant
            mock_fetch.return_value = {
                "valid": False,
                "variant": "INVALID:VARIANT",
                "error": "Invalid HGVS nomenclature",
                "message": "Variant description does not conform to HGVS standards",
            }

            # Execute test
            result = await validate_hgvs_variant("INVALID:VARIANT")

            # Verify results
            assert "valid" in str(result) or "False" in str(result) or "error" in str(result)
            mock_fetch.assert_called_once_with("/mutalyzer/hgvs/INVALID:VARIANT")

    @pytest.mark.asyncio
    async def test_validate_http_error(self):
        """Test error handling when API returns HTTP error."""
        import httpx

        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            mock_fetch.side_effect = httpx.HTTPError("404 Not Found")

            # Execute test
            result = await validate_hgvs_variant("NC_000017.10:g.7577121C>T")

            # Verify error is handled gracefully
            assert "Error validating HGVS variant" in result
            assert "404" in result

    @pytest.mark.asyncio
    async def test_validate_network_error(self):
        """Test error handling when network request fails."""
        import httpx

        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise network error
            mock_fetch.side_effect = httpx.ConnectError("Connection failed")

            # Execute test
            result = await validate_hgvs_variant("NM_000546.5:c.215C>G")

            # Verify error is handled gracefully
            assert "Error validating HGVS variant" in result


@pytest.mark.unit
class TestConvertProteinVariant:
    """Test the convert_protein_variant function."""

    @pytest.mark.asyncio
    async def test_convert_ensembl_protein_variant(self):
        """Test conversion of Ensembl protein variant to genomic coordinates."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for Ensembl protein variant
            mock_fetch.return_value = {
                "protein_variant": "ENSP00000269305:p.R248Q",
                "gene": "TP53",
                "genomic_coordinates": {"hg19": "chr17:7577538C>T", "hg38": "chr17:7579472C>T"},
                "cdna_change": "c.743G>A",
                "transcripts": [
                    {
                        "id": "ENST00000269305",
                        "chromosome": "chr17",
                        "position": 7577538,
                        "reference": "C",
                        "alternative": "T",
                    }
                ],
            }

            # Execute test
            result = await convert_protein_variant("ENSP00000269305:p.R248Q")

            # Verify results
            assert "ENSP00000269305:p.R248Q" in str(result)
            assert "genomic_coordinates" in str(result) or "chr17" in str(result)
            mock_fetch.assert_called_once_with("/transvar/protein/ENSP00000269305:p.R248Q")

    @pytest.mark.asyncio
    async def test_convert_refseq_protein_variant(self):
        """Test conversion of RefSeq protein variant to genomic coordinates."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for RefSeq protein variant
            mock_fetch.return_value = {
                "protein_variant": "NP_000537.3:p.Arg72Pro",
                "gene": "TP53",
                "genomic_coordinates": {"hg19": "chr17:7579472G>C", "hg38": "chr17:7579406G>C"},
                "cdna_change": "c.215G>C",
                "transcripts": [
                    {
                        "id": "NM_000546.5",
                        "chromosome": "chr17",
                        "position": 7579472,
                        "reference": "G",
                        "alternative": "C",
                    }
                ],
            }

            # Execute test
            result = await convert_protein_variant("NP_000537.3:p.Arg72Pro")

            # Verify results
            assert "NP_000537.3:p.Arg72Pro" in str(result)
            assert "genomic_coordinates" in str(result) or "chr17" in str(result)
            mock_fetch.assert_called_once_with("/transvar/protein/NP_000537.3:p.Arg72Pro")

    @pytest.mark.asyncio
    async def test_convert_with_multiple_transcripts(self):
        """Test conversion that returns multiple transcript mappings."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response with multiple transcripts
            mock_fetch.return_value = {
                "protein_variant": "ENSP00000269305:p.R248Q",
                "gene": "TP53",
                "transcripts": [
                    {
                        "id": "ENST00000269305",
                        "chromosome": "chr17",
                        "position": 7577538,
                        "cdna_change": "c.743G>A",
                    },
                    {
                        "id": "ENST00000420246",
                        "chromosome": "chr17",
                        "position": 7577540,
                        "cdna_change": "c.743G>A",
                    },
                ],
            }

            # Execute test
            result = await convert_protein_variant("ENSP00000269305:p.R248Q")

            # Verify results contain transcript information
            assert "transcript" in str(result).lower()
            mock_fetch.assert_called_once_with("/transvar/protein/ENSP00000269305:p.R248Q")

    @pytest.mark.asyncio
    async def test_convert_invalid_protein_variant(self):
        """Test conversion of invalid protein variant format."""
        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock response for invalid protein variant
            mock_fetch.return_value = {
                "error": "Invalid protein variant format",
                "message": "Variant does not match expected format",
            }

            # Execute test
            result = await convert_protein_variant("INVALID_FORMAT")

            # Verify results
            assert "error" in str(result).lower() or "invalid" in str(result).lower()
            mock_fetch.assert_called_once_with("/transvar/protein/INVALID_FORMAT")

    @pytest.mark.asyncio
    async def test_convert_http_error(self):
        """Test error handling when API returns HTTP error."""
        import httpx

        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise HTTP error
            mock_fetch.side_effect = httpx.HTTPError("500 Internal Server Error")

            # Execute test
            result = await convert_protein_variant("ENSP00000269305:p.R248Q")

            # Verify error is handled gracefully
            assert "Error converting protein variant" in result
            assert "500" in result

    @pytest.mark.asyncio
    async def test_convert_timeout_error(self):
        """Test error handling when API request times out."""
        import httpx

        with patch("src.tools.utility_tools.fetch_marrvel_data") as mock_fetch:
            # Setup mock to raise timeout error
            mock_fetch.side_effect = httpx.TimeoutException("Request timed out")

            # Execute test
            result = await convert_protein_variant("NP_000537.3:p.Arg72Pro")

            # Verify error is handled gracefully
            assert "Error converting protein variant" in result


# Integration tests (require actual API access)
class TestValidateHgvsVariantIntegration:
    """Integration tests for validate_hgvs_variant with real API."""

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_validate_genomic_variant(self):
        """Test real API call for genomic variant validation."""
        result = await validate_hgvs_variant("NC_000017.10:g.7577121C>T")
        assert result is not None
        assert len(result) > 0

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_validate_coding_variant(self):
        """Test real API call for coding variant validation."""
        result = await validate_hgvs_variant("NM_000546.5:c.215C>G")
        assert result is not None
        assert len(result) > 0


class TestConvertProteinVariantIntegration:
    """Integration tests for convert_protein_variant with real API."""

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_convert_protein_variant(self):
        """Test real API call for protein variant conversion."""
        result = await convert_protein_variant("ENSP00000269305:p.R248Q")
        assert result is not None
        assert len(result) > 0

    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_convert_refseq_variant(self):
        """Test real API call for RefSeq protein variant conversion."""
        result = await convert_protein_variant("NP_000537.3:p.Arg72Pro")
        assert result is not None
        assert len(result) > 0
