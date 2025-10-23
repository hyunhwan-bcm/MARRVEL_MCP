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

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_validate_genomic_variant(self):
        """Test real API call for genomic variant validation."""
        result = await validate_hgvs_variant("NC_000017.10:g.7577121C>T")
        assert result is not None
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_validate_coding_variant(self):
        """Test real API call for coding variant validation."""
        result = await validate_hgvs_variant("NM_000546.5:c.215C>G")
        assert result is not None
        assert len(result) > 0


class TestConvertProteinVariantIntegration:
    """Integration tests for convert_protein_variant with real API."""

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_convert_protein_variant(self):
        """Test real API call for protein variant conversion."""
        result = await convert_protein_variant("ENSP00000269305:p.R248Q")
        assert result is not None
        assert len(result) > 0

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_convert_refseq_variant(self):
        """Test real API call for RefSeq protein variant conversion."""
        result = await convert_protein_variant("NP_000537.3:p.Arg72Pro")
        assert result is not None
        assert len(result) > 0


# ============================================================================
# rsID Converter Tests
# ============================================================================


@pytest.mark.unit
class TestConvertRsidToVariant:
    """Test the convert_rsid_to_variant function."""

    @pytest.mark.asyncio
    async def test_convert_rsid_with_prefix(self):
        """Test conversion of rsID with 'rs' prefix."""
        # Import at test level to avoid circular imports
        from src.tools.utility_tools import convert_rsid_to_variant
        from unittest.mock import MagicMock

        with patch("httpx.AsyncClient") as mock_client_class:
            # Setup mock response for rs12345
            mock_response = MagicMock()
            mock_response.json = MagicMock(
                return_value=[
                    1,  # total count
                    ["rs12345"],  # rsid list
                    {  # field data
                        "37.chr": ["22"],
                        "37.pos": ["25459491"],
                        "37.alleles": ["G/A"],
                        "37.gene": ["CRYBB2P1"],
                    },
                    [["rs12345", "22", "25459491", "G/A", "CRYBB2P1"]],  # display strings
                ]
            )
            mock_response.raise_for_status = MagicMock()

            # Setup mock client
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Execute test
            result = await convert_rsid_to_variant("rs12345")

            # Verify results
            import json

            result_data = json.loads(result)
            assert result_data["rsid"] == "rs12345"
            assert result_data["variant"] == "22-25459491-G-A"
            assert result_data["chr"] == "22"
            assert result_data["pos"] == "25459491"
            assert result_data["ref"] == "G"
            assert result_data["alt"] == "A"
            assert result_data["assembly"] == "GRCh37"

    @pytest.mark.asyncio
    async def test_convert_rsid_without_prefix(self):
        """Test conversion of rsID without 'rs' prefix."""
        from src.tools.utility_tools import convert_rsid_to_variant
        from unittest.mock import MagicMock

        with patch("httpx.AsyncClient") as mock_client_class:
            # Setup mock response for rs429358
            mock_response = MagicMock()
            mock_response.json = MagicMock(
                return_value=[
                    1,
                    ["rs429358"],
                    {
                        "37.chr": ["19"],
                        "37.pos": ["45411941"],
                        "37.alleles": ["T/C"],
                        "37.gene": ["APOE"],
                    },
                    [["rs429358", "19", "45411941", "T/C", "APOE"]],
                ]
            )
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Execute test with numeric rsID
            result = await convert_rsid_to_variant("429358")

            # Verify results
            import json

            result_data = json.loads(result)
            assert result_data["rsid"] == "rs429358"
            assert result_data["variant"] == "19-45411941-T-C"

    @pytest.mark.asyncio
    async def test_convert_rsid_multiallelic(self):
        """Test conversion of rsID with multiple alleles (takes first)."""
        from src.tools.utility_tools import convert_rsid_to_variant
        from unittest.mock import MagicMock

        with patch("httpx.AsyncClient") as mock_client_class:
            # Setup mock response with multiple alleles
            mock_response = MagicMock()
            mock_response.json = MagicMock(
                return_value=[
                    1,
                    ["rs12345"],
                    {
                        "37.chr": ["22"],
                        "37.pos": ["25459491"],
                        "37.alleles": ["G/A, G/C"],  # Multiple alleles
                        "37.gene": ["CRYBB2P1"],
                    },
                    [["rs12345", "22", "25459491", "G/A, G/C", "CRYBB2P1"]],
                ]
            )
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Execute test
            result = await convert_rsid_to_variant("rs12345")

            # Verify results - should use first allele pair (G/A)
            import json

            result_data = json.loads(result)
            assert result_data["variant"] == "22-25459491-G-A"
            assert result_data["alleles"] == "G/A, G/C"  # Original preserved

    @pytest.mark.asyncio
    async def test_convert_rsid_not_found(self):
        """Test handling of non-existent rsID."""
        from src.tools.utility_tools import convert_rsid_to_variant
        from unittest.mock import MagicMock

        with patch("httpx.AsyncClient") as mock_client_class:
            # Setup mock response with no results
            mock_response = MagicMock()
            mock_response.json = MagicMock(return_value=[0, [], {}, []])
            mock_response.raise_for_status = MagicMock()

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Execute test
            result = await convert_rsid_to_variant("rs99999999999")

            # Verify error handling
            import json

            result_data = json.loads(result)
            assert "error" in result_data
            assert "not found" in result_data["error"].lower()

    @pytest.mark.asyncio
    async def test_convert_rsid_api_error(self):
        """Test handling of API errors."""
        from src.tools.utility_tools import convert_rsid_to_variant
        from unittest.mock import MagicMock
        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            # Setup mock to raise HTTP error
            mock_response = MagicMock()
            mock_response.status_code = 500

            def raise_status():
                raise httpx.HTTPStatusError(
                    "Server Error", request=MagicMock(), response=mock_response
                )

            mock_response.raise_for_status = raise_status

            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Execute test
            result = await convert_rsid_to_variant("rs12345")

            # Verify error handling
            import json

            result_data = json.loads(result)
            assert "error" in result_data
            assert "API error" in result_data["error"]

    @pytest.mark.asyncio
    async def test_convert_rsid_timeout(self):
        """Test handling of timeout errors."""
        from src.tools.utility_tools import convert_rsid_to_variant
        import httpx

        with patch("httpx.AsyncClient") as mock_client_class:
            # Setup mock to raise timeout
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Request timeout"))
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            # Execute test
            result = await convert_rsid_to_variant("rs12345")

            # Verify error handling
            import json

            result_data = json.loads(result)
            assert "error" in result_data
            assert "timeout" in result_data["error"].lower()


# ============================================================================
# rsID Converter Integration Tests
# ============================================================================


@pytest.mark.integration
class TestConvertRsidToVariantIntegration:
    """Integration tests for convert_rsid_to_variant with real NLM API."""

    @pytest.mark.asyncio
    async def test_real_convert_rs12345(self):
        """Test real API call for rs12345."""
        from src.tools.utility_tools import convert_rsid_to_variant
        import json

        result = await convert_rsid_to_variant("rs12345")
        assert result is not None

        result_data = json.loads(result)
        assert "rsid" in result_data
        assert result_data["rsid"] == "rs12345"
        assert "variant" in result_data
        assert "chr" in result_data
        assert "pos" in result_data
        assert result_data["assembly"] == "GRCh37"

    @pytest.mark.asyncio
    async def test_real_convert_apoe_variant(self):
        """Test real API call for APOE rs429358."""
        from src.tools.utility_tools import convert_rsid_to_variant
        import json

        result = await convert_rsid_to_variant("429358")
        assert result is not None

        result_data = json.loads(result)
        assert result_data["rsid"] == "rs429358"
        assert "19" in result_data["variant"]  # APOE is on chr19
        # Note: Gene field may be null/empty in the API response
