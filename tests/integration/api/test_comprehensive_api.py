"""
Comprehensive integration tests for all MARRVEL API endpoints.

This test suite covers all endpoints exposed by the MARRVEL-MCP tools,
ensuring complete API integration coverage. Tests use the api_capture
fixture for logging and response validation.

Coverage includes:
- Gene endpoints (3)
- Variant endpoints (11)
- Disease endpoints (2)
- Ortholog endpoints (2)
- Expression endpoints (3)
- Utility endpoints (2)

Total: 24 tests (removed 2 non-existent variant endpoints)

Reference: https://marrvel.org/doc
"""

import sys
import os
import pytest
import httpx

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

from src.utils.api_client import fetch_marrvel_data


# =============================================================================
# GENE ENDPOINTS (3 tests)
# =============================================================================


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gene_by_entrez_id(api_capture):
    """Test gene lookup by Entrez ID."""
    entrez_id = "7157"
    endpoint = f"/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
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
async def test_gene_by_symbol(api_capture):
    """Test gene lookup by symbol and taxon ID."""
    gene_symbol = "BRCA1"
    taxon_id = "9606"
    endpoint = f"/gene/taxonId/{taxon_id}/symbol/{gene_symbol}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gene_by_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol, "taxon_id": taxon_id},
            output_data=result,
            status="success",
        )

        assert result is not None
        assert isinstance(result, dict)

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gene_by_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol, "taxon_id": taxon_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gene_by_position(api_capture):
    """Test gene lookup by chromosomal position."""
    chromosome = "chr17"
    position = 7577121
    endpoint = f"/gene/chr/{chromosome}/pos/{position}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gene_by_position",
            endpoint=endpoint,
            input_data={"chromosome": chromosome, "position": position},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gene_by_position",
            endpoint=endpoint,
            input_data={"chromosome": chromosome, "position": position},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


# =============================================================================
# VARIANT ENDPOINTS (11 tests)
# =============================================================================


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_variant_dbnsfp(api_capture):
    """Test dbNSFP variant annotations."""
    variant = "6:99365567T>C"
    endpoint = f"/dbnsfp/variant/{variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

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
async def test_clinvar_by_variant(api_capture):
    """Test ClinVar lookup by variant."""
    variant = "17-7577121-C-T"
    endpoint = f"/clinvar/variant/{variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_clinvar_by_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_clinvar_by_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_clinvar_by_gene_symbol(api_capture):
    """Test ClinVar variants by gene symbol."""
    gene_symbol = "TP53"
    endpoint = f"/clinvar/gene/symbol/{gene_symbol}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_clinvar_by_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_clinvar_by_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_clinvar_by_entrez_id(api_capture):
    """Test ClinVar variants by Entrez ID."""
    entrez_id = "7157"
    endpoint = f"/clinvar/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_clinvar_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_clinvar_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gnomad_variant(api_capture):
    """Test gnomAD population frequencies by variant."""
    variant = "6:99365567T>C"
    endpoint = f"/gnomad/variant/{variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gnomad_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gnomad_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gnomad_by_gene_symbol(api_capture):
    """Test gnomAD variants by gene symbol."""
    gene_symbol = "TP53"
    endpoint = f"/gnomad/gene/symbol/{gene_symbol}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gnomad_by_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gnomad_by_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gnomad_by_entrez_id(api_capture):
    """Test gnomAD variants by Entrez ID."""
    entrez_id = "7157"
    endpoint = f"/gnomad/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gnomad_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gnomad_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_dgv_variant(api_capture):
    """Test DGV structural variants by variant."""
    variant = "17-7577121-C-T"
    endpoint = f"/dgv/variant/{variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_dgv_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_dgv_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_dgv_by_entrez_id(api_capture):
    """Test DGV structural variants by gene Entrez ID."""
    entrez_id = "7157"
    endpoint = f"/dgv/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_dgv_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_dgv_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_decipher_variant(api_capture):
    """Test DECIPHER developmental disorder variants by variant."""
    variant = "17-7577121-C-T"
    endpoint = f"/decipher/variant/{variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_decipher_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_decipher_variant",
            endpoint=endpoint,
            input_data={"variant": variant},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_decipher_by_location(api_capture):
    """Test DECIPHER variants by genomic location."""
    chromosome = "chr17"
    start = 7570000
    stop = 7590000
    endpoint = f"/decipher/genomloc/{chromosome}/{start}/{stop}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_decipher_by_location",
            endpoint=endpoint,
            input_data={"chromosome": chromosome, "start": start, "stop": stop},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_decipher_by_location",
            endpoint=endpoint,
            input_data={"chromosome": chromosome, "start": start, "stop": stop},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_geno2mp_by_entrez_id(api_capture):
    """Test Geno2MP phenotype associations by gene Entrez ID."""
    entrez_id = "7157"
    endpoint = f"/geno2mp/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_geno2mp_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_geno2mp_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


# =============================================================================
# DISEASE ENDPOINTS (2 tests)
# =============================================================================


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_omim_by_mim_number(api_capture):
    """Test OMIM lookup by MIM number."""
    mim_number = "191170"
    endpoint = f"/omim/mimNumber/{mim_number}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_omim_by_mim_number",
            endpoint=endpoint,
            input_data={"mim_number": mim_number},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_omim_by_mim_number",
            endpoint=endpoint,
            input_data={"mim_number": mim_number},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_omim_by_gene_symbol(api_capture):
    """Test OMIM diseases by gene symbol."""
    gene_symbol = "TP53"
    endpoint = f"/omim/gene/symbol/{gene_symbol}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_omim_by_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_omim_by_gene_symbol",
            endpoint=endpoint,
            input_data={"gene_symbol": gene_symbol},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


# =============================================================================
# ORTHOLOG ENDPOINTS (2 tests)
# =============================================================================


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_diopt_orthologs(api_capture):
    """Test DIOPT ortholog predictions."""
    entrez_id = "7157"
    endpoint = f"/diopt/ortholog/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_diopt_orthologs",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_diopt_orthologs",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_diopt_alignment(api_capture):
    """Test DIOPT protein sequence alignments."""
    entrez_id = "7157"
    endpoint = f"/diopt/alignment/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_diopt_alignment",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_diopt_alignment",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


# =============================================================================
# EXPRESSION ENDPOINTS (3 tests)
# =============================================================================


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gtex_expression(api_capture):
    """Test GTEx tissue expression data."""
    entrez_id = "7157"
    endpoint = f"/gtex/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_gtex_expression",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_gtex_expression",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_ortholog_expression(api_capture):
    """Test ortholog expression patterns across model organisms."""
    entrez_id = "7157"
    endpoint = f"/expression/orthologs/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_ortholog_expression",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_ortholog_expression",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_pharos_targets(api_capture):
    """Test Pharos drug target information."""
    entrez_id = "7157"
    endpoint = f"/pharos/targets/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="get_pharos_targets",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
        )

        assert result is not None

    except Exception as e:
        api_capture.log_response(
            tool_name="get_pharos_targets",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


# =============================================================================
# UTILITY ENDPOINTS (2 tests)
# =============================================================================


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_mutalyzer_hgvs_validation(api_capture):
    """Test Mutalyzer HGVS variant validation."""
    hgvs_variant = "NM_000546.5:c.215C>G"
    endpoint = f"/mutalyzer/hgvs/{hgvs_variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="validate_hgvs_variant",
            endpoint=endpoint,
            input_data={"hgvs_variant": hgvs_variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except httpx.ReadTimeout:
        # Mutalyzer service may be slow or unavailable
        api_capture.log_response(
            tool_name="validate_hgvs_variant",
            endpoint=endpoint,
            input_data={"hgvs_variant": hgvs_variant},
            output_data=None,
            status="timeout",
            error="Mutalyzer API timeout - service may be slow or unavailable",
        )
        pytest.skip("Mutalyzer API timeout - service unavailable")
    except Exception as e:
        api_capture.log_response(
            tool_name="validate_hgvs_variant",
            endpoint=endpoint,
            input_data={"hgvs_variant": hgvs_variant},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_transvar_protein_variant(api_capture):
    """Test Transvar protein variant conversion."""
    protein_variant = "ENSP00000269305:p.R248Q"
    endpoint = f"/transvar/protein/{protein_variant}"

    try:
        result = await fetch_marrvel_data(endpoint)

        api_capture.log_response(
            tool_name="convert_protein_variant",
            endpoint=endpoint,
            input_data={"protein_variant": protein_variant},
            output_data=result,
            status="success",
        )

        assert result is not None

    except httpx.ReadTimeout:
        # Transvar service may be slow or unavailable
        api_capture.log_response(
            tool_name="convert_protein_variant",
            endpoint=endpoint,
            input_data={"protein_variant": protein_variant},
            output_data=None,
            status="timeout",
            error="Transvar API timeout - service may be slow or unavailable",
        )
        pytest.skip("Transvar API timeout - service unavailable")
    except Exception as e:
        api_capture.log_response(
            tool_name="convert_protein_variant",
            endpoint=endpoint,
            input_data={"protein_variant": protein_variant},
            output_data=None,
            status="error",
            error=str(e),
        )
        raise
