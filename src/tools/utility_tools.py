"""
MARRVEL MCP Server - Utility Tools

This module provides utility tools for variant nomenclature validation
and coordinate conversion.

Includes:
- Mutalyzer - HGVS variant validation and parsing
- Transvar - Protein to genomic coordinate conversion
- rsID Converter - Convert rsIDs to MARRVEL variant format
"""

import httpx
import json
from urllib.parse import quote
from src.utils.api_client import fetch_marrvel_data


def register_tools(mcp_instance):
    """Register all utility tools with the MCP server."""
    # Register tools
    mcp_instance.tool()(convert_hgvs_to_genomic)
    mcp_instance.tool()(convert_protein_variant)
    mcp_instance.tool()(convert_rsid_to_variant)


# ============================================================================
# VARIANT NOMENCLATURE & CONVERSION TOOLS
# ============================================================================


async def convert_hgvs_to_genomic(hgvs_variant: str) -> str:
    """
    Convert and validate HGVS variant nomenclature to genomic coordinates using Mutalyzer.

    Accepts genomic, coding, or protein HGVS formats and returns parsed genomic
    coordinates. Essential for standardizing variant notation.

    Args:
        hgvs_variant: HGVS format variant (e.g., "NM_000546.5:c.215C>G",
            "NC_000017.10:g.7577121C>T", "NP_000537.3:p.Arg72Pro")

    Returns:
        JSON with validation status, genomic coordinates (chr, pos, ref, alt), gene,
        transcript, protein changes, and alternative descriptions

    Example:
        convert_hgvs_to_genomic("NM_000546.5:c.215C>G")
        convert_hgvs_to_genomic("NC_000017.10:g.7577121C>T")
    """
    try:
        encoded_variant = quote(hgvs_variant)
        data = await fetch_marrvel_data(f"/mutalyzer/hgvs/{encoded_variant}")
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error converting HGVS variant: {str(e)}"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)


async def convert_protein_variant(protein_variant: str) -> str:
    """
    Convert protein-level variant to genomic coordinates using Transvar.

    Maps protein changes to genomic positions across multiple transcripts.
    Use when you have protein notation and need genomic coordinates.

    Args:
        protein_variant: Protein variant in HGVS format (e.g., "ENSP00000269305:p.R248Q",
            "NP_000537.3:p.Arg72Pro")

    Returns:
        JSON with genomic coordinates (hg19/hg38), cDNA changes, transcript mappings,
        and alternative annotations

    Example:
        convert_protein_variant("ENSP00000269305:p.R248Q")
        convert_protein_variant("NP_000537.3:p.Arg72Pro")
    """
    try:
        encoded_variant = quote(protein_variant)
        data = await fetch_marrvel_data(f"/transvar/protein/{encoded_variant}")
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error converting protein variant: {str(e)}"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)


async def convert_rsid_to_variant(rsid: str) -> str:
    """
    Convert dbSNP rsID to MARRVEL variant format (chr-pos-ref-alt).

    Queries NLM Clinical Tables API and returns GRCh37/hg19 coordinates compatible
    with MARRVEL tools. Essential for converting rsIDs from literature or databases.

    Args:
        rsid: dbSNP rsID with or without "rs" prefix (e.g., "rs12345", "429358")

    Returns:
        JSON with rsid, variant (chr-pos-ref-alt format), chr, pos, ref, alt, alleles,
        gene, and assembly (GRCh37)

    Example:
        convert_rsid_to_variant("rs12345")
        convert_rsid_to_variant("429358")  # APOE variant

    Note: Returns first alternate allele for multi-allelic sites. Uses hg19 coordinates.
    """
    try:
        # Normalize rsID - ensure it starts with "rs"
        if not rsid.startswith("rs"):
            rsid = f"rs{rsid}"

        # Query NLM Clinical Tables SNP API for GRCh37 data
        # ef parameter specifies extra fields to return: chr, pos, alleles, gene
        url = f"https://clinicaltables.nlm.nih.gov/api/snps/v3/search"
        params = {"terms": rsid, "ef": "37.chr,37.pos,37.alleles,37.gene"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        # Parse API response
        # Format: [total_count, [rsid_list], {field_data}, [[display_strings]]]
        if not data or len(data) < 3:
            return json.dumps({"error": "Invalid API response format"}, indent=2)

        total_count = data[0]
        if total_count == 0:
            return json.dumps({"error": f"rsID '{rsid}' not found in dbSNP"}, indent=2)

        rsid_list = data[1]
        field_data = data[2]

        # Get data for the first (exact) match
        if rsid not in rsid_list:
            return json.dumps(
                {"error": f"Exact match for '{rsid}' not found", "suggestions": rsid_list[:5]},
                indent=2,
            )

        idx = rsid_list.index(rsid)

        # Extract GRCh37 coordinates and alleles
        chr_data = field_data.get("37.chr", [])
        pos_data = field_data.get("37.pos", [])
        alleles_data = field_data.get("37.alleles", [])
        gene_data = field_data.get("37.gene", [])

        if idx >= len(chr_data) or idx >= len(pos_data) or idx >= len(alleles_data):
            return json.dumps({"error": "Incomplete GRCh37 data for this rsID"}, indent=2)

        chromosome = chr_data[idx]
        position = pos_data[idx]
        alleles = alleles_data[idx]
        gene = gene_data[idx] if idx < len(gene_data) and gene_data[idx] is not None else ""

        if not chromosome or not position or not alleles:
            return json.dumps({"error": "Missing required GRCh37 coordinate data"}, indent=2)

        # Parse alleles - format can be "G/A", "G/A, G/C", etc.
        # For simplicity, take the first pair
        allele_pairs = alleles.split(",")[0].strip().split("/")
        if len(allele_pairs) < 2:
            return json.dumps({"error": f"Invalid allele format: {alleles}"}, indent=2)

        reference = allele_pairs[0].strip()
        alternate = allele_pairs[1].strip()

        # Build MARRVEL variant format: chromosome-position-reference-alternate
        variant = f"{chromosome}-{position}-{reference}-{alternate}"

        result = {
            "rsid": rsid,
            "variant": variant,
            "chr": chromosome,
            "pos": position,
            "ref": reference,
            "alt": alternate,
            "alleles": alleles,
            "gene": gene,
            "assembly": "GRCh37",
        }

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return json.dumps(
            {"error": f"API error: {e.response.status_code}", "message": str(e)}, indent=2
        )
    except httpx.TimeoutException:
        return json.dumps({"error": "Request timeout - API took too long to respond"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to convert rsID: {str(e)}"}, indent=2)
