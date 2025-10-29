"""
MARRVEL MCP Server - Expression Tools

This module provides tools for accessing gene expression data across
human tissues and model organisms.

Includes:
- GTEx (Genotype-Tissue Expression) - Human tissue expression
- Ortholog expression patterns across model organisms
- Pharos drug target information
"""

import httpx
from src.utils.api_client import fetch_marrvel_data


def register_tools(mcp_instance):
    """Register all expression tools with the MCP server."""
    # Register tools
    mcp_instance.tool()(get_gtex_expression)
    mcp_instance.tool()(get_ortholog_expression)
    mcp_instance.tool()(get_pharos_targets)


# ============================================================================
# EXPRESSION DATA TOOLS
# ============================================================================


async def get_gtex_expression(entrez_id: str) -> str:
    """
    Access GTEx (Genotype-Tissue Expression) data.

    GTEx provides gene expression levels across 54 human tissues from
    healthy donors.

    Args:
        entrez_id: Gene Entrez ID

    Returns:
        JSON string with expression data:
        - Median TPM (Transcripts Per Million) per tissue
        - Expression variability
        - Sample sizes
        - Tissue-specific expression patterns

    Example:
        get_gtex_expression("7157")  # TP53 expression
        get_gtex_expression("672")   # BRCA1 expression
    """
    try:
        data = await fetch_marrvel_data(f"/gtex/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching GTEx data: {str(e)}"


async def get_ortholog_expression(entrez_id: str) -> str:
    """
    Get expression data for orthologs across model organisms.

    Provides comparative expression patterns for gene orthologs in
    model organisms including developmental stages and tissue types.

    Args:
        entrez_id: Human gene Entrez ID

    Returns:
        JSON string with ortholog expression data:
        - Expression in mouse, fly, zebrafish, etc.
        - Developmental stage expression
        - Tissue-specific patterns in models

    Example:
        get_ortholog_expression("7157")  # TP53 orthologs
        get_ortholog_expression("672")   # BRCA1 orthologs
    """
    try:
        data = await fetch_marrvel_data(f"/expression/orthologs/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching ortholog expression data: {str(e)}"


async def get_pharos_targets(entrez_id: str) -> str:
    """
    Query Pharos for drug target information.

    Pharos is the user interface to the Knowledge Management Center (KMC)
    for the Illuminating the Druggable Genome (IDG) program.

    Args:
        entrez_id: Gene Entrez ID

    Returns:
        JSON string with drug target information:
        - Target Development Level (Tclin, Tchem, Tbio, Tdark)
        - Known drugs and compounds
        - Clinical trial information
        - Target class and family
        - Druggability assessment

    Target Levels:
        - Tclin: Clinical target with approved drugs
        - Tchem: Target with known chemical probes
        - Tbio: Biological target with evidence
        - Tdark: Understudied protein

    Example:
        get_pharos_targets("7157")  # TP53 druggability
        get_pharos_targets("672")   # BRCA1 as drug target
    """
    try:
        data = await fetch_marrvel_data(f"/pharos/targets/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching Pharos data: {str(e)}"
