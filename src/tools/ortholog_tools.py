"""
MARRVEL MCP Server - Ortholog Tools (DIOPT)

This module provides tools for ortholog prediction using DIOPT
(DRSC Integrative Ortholog Prediction Tool).

DIOPT integrates multiple ortholog prediction algorithms to identify
orthologs with high confidence across model organisms.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data


def register_tools(mcp_instance):
    """Register all ortholog tools with the MCP server."""
    # Register tools
    # Provide an explicit alias matching other parts of the codebase/tests
    # which reference `get_diopt_orthologs_by_entrez_id`.
    mcp_instance.tool()(get_diopt_orthologs_by_entrez_id)
    mcp_instance.tool()(get_diopt_alignment)


# ============================================================================
# DIOPT ORTHOLOG TOOLS
# ============================================================================


async def get_diopt_orthologs_by_entrez_id(entrez_id: str) -> str:
    """
    Find high-confidence orthologs across model organisms using DIOPT.

    Returns orthologs in mouse, rat, zebrafish, fly, worm, and yeast with confidence
    scores. Essential for translating human genetics to model organism research.

    Args:
        entrez_id: Human gene Entrez ID (e.g., "7157" for TP53)

    Returns:
        JSON with orthologs per species, DIOPT scores, supporting algorithms, and gene symbols

    Example:
        get_diopt_orthologs_by_entrez_id("7157")  # TP53 orthologs
        get_diopt_orthologs_by_entrez_id("672")   # BRCA1 orthologs
    """
    try:
        data = await fetch_marrvel_data(f"/diopt/ortholog/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT data: {str(e)}"


async def get_diopt_alignment(entrez_id: str) -> str:
    """
    Get protein sequence alignment across orthologous species.

    Returns multiple sequence alignment showing conservation patterns and protein
    domains. Useful for identifying functionally important residues.

    Args:
        entrez_id: Human gene Entrez ID (e.g., "7157" for TP53)

    Returns:
        JSON with aligned sequences, conservation patterns, and domain annotations

    Example:
        get_diopt_alignment("7157")  # TP53 alignment
        get_diopt_alignment("672")   # BRCA1 alignment
    """
    try:
        data = await fetch_marrvel_data(f"/diopt/alignment/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT alignment data: {str(e)}"
