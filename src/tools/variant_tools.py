"""
Variant analysis tools for MARRVEL-MCP.

This module provides tools for querying variant annotations from multiple databases:
- dbNSFP: Functional predictions and conservation scores
- ClinVar: Clinical significance and disease associations
- gnomAD: Population allele frequencies
- DGV: Structural variants and CNVs
- DECIPHER: Developmental disorder variants
- Geno2MP: Genotype-phenotype associations
"""

import httpx
import json
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP


def register_tools(mcp_instance: FastMCP):
    """
    Register all variant analysis tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    # Register all 13 variant tools
    mcp_instance.tool()(get_variant_dbnsfp)
    mcp_instance.tool()(get_clinvar_by_variant)
    mcp_instance.tool()(get_clinvar_by_gene_symbol)
    mcp_instance.tool()(get_clinvar_by_entrez_id)
    mcp_instance.tool()(get_gnomad_variant)
    mcp_instance.tool()(get_gnomad_by_gene_symbol)
    mcp_instance.tool()(get_gnomad_by_entrez_id)
    mcp_instance.tool()(get_dgv_by_entrez_id)
    mcp_instance.tool()(get_geno2mp_by_entrez_id)


# ============================================================================
# dbNSFP - Functional Predictions
# ============================================================================


async def get_variant_dbnsfp(chr: str, pos: str, ref: str, alt: str) -> str:
    """
    Retrieve comprehensive variant annotations from dbNSFP database.

    Args:
        chr: Chromosome (e.g., "17", "X")
        pos: Genomic position (string)
        ref: Reference allele (e.g., "C")
        alt: Alternate allele (e.g., "T")

    Returns:
        JSON string with extensive variant annotations.

    Example:
        get_variant_dbnsfp("17", "7577121", "C", "T") # from "17:7577121 C>T" in prompt
        get_variant_dbnsfp("6", "99365567", "T", "C") # from "6-99365567-T-C" in prompt
        get_variant_dbnsfp("11", "5227002", "G", "A") # from "11-5227002G>A" in prompt
        get_variant_dbnsfp("X", "154247", "A", "G") # from "X-154247A>G" in prompt
        get_variant_dbnsfp("2", "47630779", "C", "T") # from "chromosome 2, position at 47630779, variant of C>T" in prompt
    """
    try:
        # Build canonical variant string for URI
        variant = f"{chr}:{pos} {ref}>{alt}"
        from urllib.parse import quote

        variant_uri = quote(variant, safe="")
        data = await fetch_marrvel_data(f"/dbnsfp/variant/{variant_uri}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# ClinVar - Clinical Significance
# ============================================================================


async def get_clinvar_by_variant(chr: str, pos: str, ref: str, alt: str) -> str:
    """
    Query ClinVar for clinical significance of a specific variant.

    Args:
        chr: Chromosome (e.g., "17", "X")
        pos: Genomic position (string)
        ref: Reference allele (e.g., "C")
        alt: Alternate allele (e.g., "T")

    Returns:
        JSON string with ClinVar data.

    Example:
        get_clinvar_by_variant("17", "7577121", "C", "T") # from "17:7577121 C>T" in prompt
        get_clinvar_by_variant("6", "99365567", "T", "C") # from "6-99365567-T-C" in prompt
        get_clinvar_by_variant("11", "5227002", "G", "A") # from "11-5227002G>A" in prompt
        get_clinvar_by_variant("X", "154247", "A", "G") # from "X-154247A>G" in prompt
        get_clinvar_by_variant("2", "47630779", "C", "T") # from "chromosome 2, position at 47630779, variant of C>T" in prompt
    """
    try:
        # Build canonical variant string for URI
        variant = f"{chr}:{pos} {ref}>{alt}"
        from urllib.parse import quote

        variant_uri = quote(variant, safe="")
        data = await fetch_marrvel_data(f"/clinvar/variant/{variant_uri}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


async def get_clinvar_by_gene_symbol(gene_symbol: str) -> str:
    """
    Get all ClinVar variants associated with a gene symbol.

    Retrieves all variants in ClinVar that are located within or associated
    with the specified gene.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1")

    Returns:
        JSON string with all ClinVar variants for the gene

    Example:
        get_clinvar_by_gene_symbol("TP53")
        get_clinvar_by_gene_symbol("BRCA1")
    """
    try:
        data = await fetch_marrvel_data(f"/clinvar/gene/symbol/{gene_symbol}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


async def get_clinvar_by_entrez_id(entrez_id: str) -> str:
    """
    Get all ClinVar variants for a gene using Entrez ID.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with all ClinVar variants for the gene

    Example:
        get_clinvar_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/clinvar/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# gnomAD - Population Frequencies
# ============================================================================


async def get_gnomad_variant(chr: str, pos: str, ref: str, alt: str) -> str:
    """
    Access population allele frequencies from gnomAD database.


    Args:
        chr: Chromosome (e.g., "17", "X")
        pos: Genomic position (string)
        ref: Reference allele (e.g., "C")
        alt: Alternate allele (e.g., "T")

    Returns:
        JSON string with population frequency data.

    Example:
        get_gnomad_variant("17", "7577121", "C", "T") # from "17:7577121 C>T" in prompt
        get_gnomad_variant("6", "99365567", "T", "C") # from "6-99365567-T-C" in prompt
        get_gnomad_variant("11", "5227002", "G", "A") # from "11-5227002G>A" in prompt
        get_gnomad_variant("X", "154247", "A", "G") # from "X-154247A>G" in prompt
        get_gnomad_variant("2", "47630779", "C", "T") # from "chromosome 2, position at 47630779, variant of C>T" in prompt
    """
    try:
        variant = f"{chr}:{pos} {ref}>{alt}"
        from urllib.parse import quote

        variant_uri = quote(variant, safe="")
        data = await fetch_marrvel_data(f"/gnomAD/variant/{variant_uri}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


async def get_gnomad_by_gene_symbol(gene_symbol: str) -> str:
    """
    Get gnomAD variant data for all variants in a gene.

    Args:
        gene_symbol: Official gene symbol

    Returns:
        JSON string with gnomAD data for all variants in the gene

    Example:
        get_gnomad_by_gene_symbol("TP53")
    """
    try:
        data = await fetch_marrvel_data(f"/gnomAD/gene/symbol/{gene_symbol}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


async def get_gnomad_by_entrez_id(entrez_id: str) -> str:
    """
    Get gnomAD variant data for a gene using Entrez ID.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with gnomAD data for all variants in the gene

    Example:
        get_gnomad_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/gnomad/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


async def get_dgv_by_entrez_id(entrez_id: str) -> str:
    """
    Get DGV structural variants for a gene.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with DGV data for the gene region

    Example:
        get_dgv_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/DGV/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


async def get_geno2mp_by_entrez_id(entrez_id: str) -> str:
    """
    Get Geno2MP phenotype associations for a gene.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with phenotype data for the gene

    Example:
        get_geno2mp_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/geno2mp/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})
