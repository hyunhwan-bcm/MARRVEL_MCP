"""
MARRVEL MCP Server - Ortholog Tools (DIOPT)

This module provides tools for ortholog prediction using DIOPT
(DRSC Integrative Ortholog Prediction Tool).

DIOPT integrates multiple ortholog prediction algorithms to identify
orthologs with high confidence across model organisms.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data

# MCP instance will be set by server.py
mcp = None


def register_tools(mcp_instance):
    """Register all ortholog tools with the MCP server."""
    global mcp
    mcp = mcp_instance
    
    # Register tools
    mcp.tool()(get_diopt_orthologs)
    mcp.tool()(get_diopt_alignment)


# ============================================================================
# DIOPT ORTHOLOG TOOLS
# ============================================================================

async def get_diopt_orthologs(entrez_id: str) -> str:
    """
    Find orthologs across model organisms using DIOPT.
    
    DIOPT (DRSC Integrative Ortholog Prediction Tool) integrates multiple
    ortholog prediction algorithms to identify orthologs with high confidence.
    
    Args:
        entrez_id: Human gene Entrez ID
        
    Returns:
        JSON string with ortholog predictions:
        - Orthologs in multiple species (Mouse, Rat, Zebrafish, Fly, Worm, Yeast)
        - DIOPT confidence scores
        - Number of supporting algorithms
        - Gene symbols in each species
        
    Example:
        get_diopt_orthologs("7157")  # TP53 orthologs
        get_diopt_orthologs("672")   # BRCA1 orthologs
    """
    try:
        data = await fetch_marrvel_data(f"/diopt/ortholog/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT data: {str(e)}"


async def get_diopt_alignment(entrez_id: str) -> str:
    """
    Get protein sequence alignments for orthologs.
    
    Provides multiple sequence alignment of protein sequences across species
    to visualize conservation patterns.
    
    Args:
        entrez_id: Human gene Entrez ID
        
    Returns:
        JSON string with sequence alignment data:
        - Aligned protein sequences
        - Conservation patterns
        - Protein domain information
        
    Example:
        get_diopt_alignment("7157")  # TP53 alignment
        get_diopt_alignment("672")   # BRCA1 alignment
    """
    try:
        data = await fetch_marrvel_data(f"/diopt/alignment/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT alignment data: {str(e)}"
