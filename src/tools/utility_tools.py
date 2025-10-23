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
from src.utils.api_client import fetch_marrvel_data


def register_tools(mcp_instance):
    """Register all utility tools with the MCP server."""
    # Register tools
    mcp_instance.tool()(validate_hgvs_variant)
    mcp_instance.tool()(convert_protein_variant)
    mcp_instance.tool()(convert_rsid_to_variant)


# ============================================================================
# VARIANT NOMENCLATURE & CONVERSION TOOLS
# ============================================================================


async def validate_hgvs_variant(hgvs_variant: str) -> str:
    """
    Validate and parse HGVS variant nomenclature using Mutalyzer.

    Mutalyzer checks if variant descriptions are correct according to HGVS
    nomenclature standards and provides parsed components.

    Args:
        hgvs_variant: Variant in HGVS format
            Examples:
            - Genomic: "NC_000017.10:g.7577121C>T"
            - Coding: "NM_000546.5:c.215C>G"
            - Protein: "NP_000537.3:p.Arg72Pro"

    Returns:
        JSON string with validation results:
        - Validation status (valid/invalid)
        - Parsed components
        - Genomic coordinates
        - Protein changes
        - Alternative descriptions

    Example:
        validate_hgvs_variant("NM_000546.5:c.215C>G")
        validate_hgvs_variant("NC_000017.10:g.7577121C>T")
    """
    try:
        data = await fetch_marrvel_data(f"/mutalyzer/hgvs/{hgvs_variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error validating HGVS variant: {str(e)}"


async def convert_protein_variant(protein_variant: str) -> str:
    """
    Convert protein-level variants to genomic coordinates using Transvar.

    Transvar is a tool for converting between different variant annotation
    formats and coordinate systems.

    Args:
        protein_variant: Protein variant description
            Examples:
            - "ENSP00000269305:p.R248Q"
            - "NP_000537.3:p.Arg72Pro"

    Returns:
        JSON string with converted coordinates:
        - Genomic coordinates (hg19, hg38)
        - cDNA changes
        - Multiple transcript mappings
        - Alternative annotations

    Example:
        convert_protein_variant("ENSP00000269305:p.R248Q")
        convert_protein_variant("NP_000537.3:p.Arg72Pro")
    """
    try:
        data = await fetch_marrvel_data(f"/transvar/protein/{protein_variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error converting protein variant: {str(e)}"


async def convert_rsid_to_variant(rsid: str) -> str:
    """
    Convert rsID to MARRVEL variant format using NLM Clinical Tables SNP API.

    Queries the NLM Clinical Tables API to retrieve SNP information and converts
    it to the MARRVEL variant format (chromosome-position-reference-alternate).
    Uses GRCh37/hg19 coordinates to match MARRVEL's coordinate system.

    Args:
        rsid: dbSNP reference SNP ID, with or without "rs" prefix
              Examples: "rs12345", "12345", "rs429358"

    Returns:
        JSON string with variant conversion results:
        - rsid: The original rsID
        - variant: MARRVEL format (chromosome-position-ref-alt)
        - chr: Chromosome number
        - pos: Position on chromosome (GRCh37/hg19)
        - alleles: Reference and alternate alleles
        - gene: Associated gene symbols (if available)
        - assembly: Genome assembly (GRCh37)

        If multiple alleles exist, returns information for the first variant.
        In case of errors, returns error message with details.

    Example:
        convert_rsid_to_variant("rs12345")
        # Returns: {"rsid": "rs12345", "variant": "22-25459491-G-A", ...}

        convert_rsid_to_variant("429358")  # APOE variant
        # Returns: {"rsid": "rs429358", "variant": "19-45411941-T-C", ...}

    API Endpoint: GET https://clinicaltables.nlm.nih.gov/api/snps/v3/search

    Note:
        - Uses GRCh37 (hg19) coordinates to match MARRVEL API requirements
        - Handles SNPs on autosomes, X, Y, and MT chromosomes
        - For multi-allelic sites, returns the first alternate allele
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
