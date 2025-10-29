"""
Gene-related tools for MARRVEL-MCP.

This module provides tools for querying gene information from the MARRVEL database.
Supports queries by Entrez ID, gene symbol, and chromosomal position.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP


def register_tools(mcp_instance: FastMCP):
    """
    Register all gene tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    # Register the tools
    mcp_instance.tool()(get_gene_by_entrez_id)
    mcp_instance.tool()(get_gene_by_symbol)
    mcp_instance.tool()(get_gene_by_position)


async def get_gene_by_entrez_id(entrez_id: str) -> str:
    """
    Retrieve comprehensive gene information by NCBI Entrez Gene ID.

    Returns gene symbol, chromosomal location, summary, RefSeq transcripts, and
    external database links. Use when you have an Entrez ID and need detailed gene data.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53, "672" for BRCA1)

    Returns:
        JSON with gene symbol, name, location, summary, transcripts, and database IDs

    Example:
        get_gene_by_entrez_id("7157")  # TP53
        get_gene_by_entrez_id("672")   # BRCA1
    """
    try:
        data = await fetch_marrvel_data(f"/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


async def get_gene_by_symbol(gene_symbol: str, taxon_id: str = "9606") -> str:
    """
    Find gene information by gene symbol across multiple species.

    Returns comprehensive gene data for any model organism. Defaults to human.
    Use for cross-species gene queries or when you have a gene symbol but not an Entrez ID.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1", "CFTR")
        taxon_id: NCBI taxonomy ID. Common values:
            - "9606": Human (default)
            - "10090": Mouse
            - "10116": Rat
            - "7955": Zebrafish
            - "7227": Drosophila
            - "6239": C. elegans

    Returns:
        JSON with gene details, Entrez ID, location, type, and description

    Example:
        get_gene_by_symbol("TP53")  # Human TP53 (default)
        get_gene_by_symbol("Trp53", "10090")  # Mouse Trp53
    """
    try:
        data = await fetch_marrvel_data(f"/gene/taxonId/{taxon_id}/symbol/{gene_symbol}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


async def get_gene_by_position(chromosome: str, position: int) -> str:
    """
    Identify genes at a specific chromosomal position (hg19/GRCh37).

    Find which gene(s) overlap a genomic coordinate. Useful for variant-to-gene
    mapping or exploring genomic regions.

    Args:
        chromosome: Chromosome with 'chr' prefix (e.g., "chr17", "chrX")
        position: Position in base pairs (hg19/GRCh37 coordinates)

    Returns:
        JSON with gene symbol, name, position details, and overlapping transcripts

    Example:
        get_gene_by_position("chr17", 7577121)  # TP53 region
        get_gene_by_position("chr13", 32900000)  # BRCA2 region
    """
    try:
        data = await fetch_marrvel_data(f"/gene/chr/{chromosome}/pos/{position}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"
