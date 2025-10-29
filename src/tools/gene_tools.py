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
    Retrieve comprehensive gene information using NCBI Entrez Gene ID.

    This tool provides detailed information about a gene including its symbol,
    name, chromosomal location, summary, transcripts, and links to various databases.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53, "672" for BRCA1)

    Returns:
        JSON string with gene information including:
        - Gene symbol and full name
        - Chromosomal location
        - Gene summary/description
        - RefSeq transcripts
        - External database identifiers

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
    Find gene information using gene symbol and species taxonomy ID.

    This tool allows you to search for genes by their symbol in different species.
    Default is human (taxon_id: 9606).

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1", "CFTR")
        taxon_id: NCBI taxonomy ID for the species. Common values:
            - "9606": Human (Homo sapiens) - DEFAULT
            - "10090": Mouse (Mus musculus)
            - "10116": Rat (Rattus norvegicus)
            - "7955": Zebrafish (Danio rerio)
            - "7227": Fruit fly (Drosophila melanogaster)
            - "6239": C. elegans (Caenorhabditis elegans)

    Returns:
        JSON string with gene information for the specified species

    Example:
        get_gene_by_symbol("TP53", "9606")  # Human TP53
        get_gene_by_symbol("Trp53", "10090")  # Mouse Trp53
        get_gene_by_symbol("tp53", "7955")  # Zebrafish tp53
    """
    try:
        data = await fetch_marrvel_data(f"/gene/taxonId/{taxon_id}/symbol/{gene_symbol}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


async def get_gene_by_position(chromosome: str, position: int) -> str:
    """
    Identify genes at specific chromosomal positions using hg19 coordinates.

    This tool helps find which gene(s) are located at a particular genomic position.
    Uses hg19/GRCh37 reference genome coordinates.

    Args:
        chromosome: Chromosome name with 'chr' prefix (e.g., "chr17", "chrX", "chr22")
        position: Chromosomal position in base pairs (hg19 coordinates)

    Returns:
        JSON string with gene(s) at the specified location including:
        - Gene symbol and name
        - Exact position information
        - Overlapping transcripts

    Example:
        get_gene_by_position("chr17", 7577121)  # TP53 region
        get_gene_by_position("chr13", 32900000)  # BRCA2 region
        get_gene_by_position("chrX", 153760000)  # F8 region
    """
    try:
        data = await fetch_marrvel_data(f"/gene/chr/{chromosome}/pos/{position}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"
