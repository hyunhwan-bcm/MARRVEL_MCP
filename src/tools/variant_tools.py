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
    Get comprehensive pathogenicity predictions and functional annotations from dbNSFP.

    Returns SIFT, PolyPhen2, CADD scores, conservation scores, and multiple in-silico
    predictions. Essential for variant pathogenicity assessment.

    Args:
        chr: Chromosome (e.g., "17", "X")
        pos: Genomic position (string)
        ref: Reference allele (e.g., "C")
        alt: Alternate allele (e.g., "T")

    Returns:
        JSON with functional predictions, conservation, frequencies, and pathogenicity scores

    Example:
        get_variant_dbnsfp("17", "7577121", "C", "T")
        get_variant_dbnsfp("X", "154247", "A", "G")
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
    Get ClinVar clinical significance and interpretation for a specific variant.

    Returns pathogenic/benign classification, review status, disease associations,
    and submission details. Critical for clinical variant interpretation.

    Args:
        chr: Chromosome (e.g., "17", "X")
        pos: Genomic position (string)
        ref: Reference allele (e.g., "C")
        alt: Alternate allele (e.g., "T")

    Returns:
        JSON with clinical significance, condition, review status, and HGVS nomenclature

    Example:
        get_clinvar_by_variant("17", "7577121", "C", "T")
        get_clinvar_by_variant("13", "32900000", "G", "A")
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
    Get all ClinVar variants for a gene.

    Returns all clinically significant variants within a gene. Useful for
    comprehensive gene-level variant review and pathogenic variant discovery.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1")

    Returns:
        JSON with all ClinVar variants, their significance, and disease associations

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
    Get all ClinVar variants for a gene by Entrez ID.

    Returns all clinically significant variants. Use when you have Entrez ID
    instead of gene symbol.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53)

    Returns:
        JSON with all ClinVar variants and their clinical interpretations

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
    Get population allele frequencies from gnomAD for a specific variant.

    Returns global and population-specific frequencies (AF, AFR, AMR, EAS, NFE, SAS).
    Essential for determining if a variant is common or rare in populations.

    Args:
        chr: Chromosome (e.g., "17", "X")
        pos: Genomic position (string)
        ref: Reference allele (e.g., "C")
        alt: Alternate allele (e.g., "T")

    Returns:
        JSON with allele frequencies across populations and homozygote counts

    Example:
        get_gnomad_variant("17", "7577121", "C", "T")
        get_gnomad_variant("X", "154247", "A", "G")
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
    Get gnomAD population frequencies for all variants in a gene.

    Returns frequency data for every variant in the gene. Useful for identifying
    common vs. rare variants within a gene.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53")

    Returns:
        JSON with gnomAD allele frequencies for all gene variants

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
    Get gnomAD population frequencies for a gene by Entrez ID.

    Returns frequency data for all variants. Use when you have Entrez ID instead
    of gene symbol.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53)

    Returns:
        JSON with gnomAD allele frequencies for all gene variants

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
    Get DGV structural variants and copy number variations (CNVs) for a gene.

    Returns benign structural variants from DGV database. Useful for identifying
    common CNVs that may confound pathogenic variant interpretation.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53)

    Returns:
        JSON with structural variants, CNVs, and deletion/duplication events

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
    Get Geno2MP phenotypes matched to a gene.

    Returns clinical phenotypes associated with the gene from Geno2MP database.
    Essential for phenotype-driven gene prioritization in rare disease diagnosis.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53)

    Returns:
        JSON with matched phenotypes, HPO terms, and clinical features

    Example:
        get_geno2mp_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/geno2mp/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})
