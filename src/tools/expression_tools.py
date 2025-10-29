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
    Get GTEx tissue-specific gene expression across 54 human tissues.

    Returns median TPM (Transcripts Per Million) for each tissue from healthy donors.
    Essential for understanding tissue specificity and normal expression patterns.

    Args:
        entrez_id: Gene Entrez ID (e.g., "7157" for TP53)

    Returns:
        JSON with median TPM per tissue, expression variability, and sample sizes

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
    Get expression patterns for orthologs across model organisms.

    Returns developmental stage and tissue expression in mouse, fly, zebrafish, etc.
    Useful for understanding conserved expression and planning model organism experiments.

    Args:
        entrez_id: Human gene Entrez ID (e.g., "7157" for TP53)

    Returns:
        JSON with expression in model organisms, developmental stages, and tissue patterns

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
    Get drug target information and druggability assessment from Pharos.

    Returns target development level (Tclin/Tchem/Tbio/Tdark), approved drugs,
    clinical trials, and druggability. Essential for therapeutic target evaluation.

    Args:
        entrez_id: Gene Entrez ID (e.g., "7157" for TP53)

    Returns:
        JSON with target level, drugs, trials, target class, and druggability assessment

    Target Levels: Tclin (approved drugs), Tchem (chemical probes), Tbio (biological),
    Tdark (understudied)

    Example:
        get_pharos_targets("7157")  # TP53 druggability
        get_pharos_targets("672")   # BRCA1 as drug target
    """
    try:
        data = await fetch_marrvel_data(f"/pharos/targets/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching Pharos data: {str(e)}"
