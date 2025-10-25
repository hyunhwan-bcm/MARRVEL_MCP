"""
Disease-related tools for MARRVEL-MCP.

This module provides tools for querying disease information from OMIM
(Online Mendelian Inheritance in Man) database.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP


async def get_omim_by_mim_number(mim_number: str) -> str:
    """
    Retrieve OMIM (Online Mendelian Inheritance in Man) entry by MIM number.

    OMIM is a comprehensive database of human genes and genetic disorders.

    Args:
        mim_number: OMIM MIM number (e.g., "191170" for Treacher Collins syndrome)

    Returns:
        JSON string with OMIM entry:
        - Disease/phenotype description
        - Clinical features
        - Inheritance pattern
        - Molecular genetics
        - Allelic variants

    Example:
        get_omim_by_mim_number("191170")  #
        get_omim_by_mim_number("114480")  # Breast cancer (BRCA1)
    """
    try:
        data = await fetch_marrvel_data(f"/omim/mimNumber/{mim_number}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def get_omim_by_gene_symbol(gene_symbol: str) -> str:
    """
    Find all OMIM diseases associated with a gene symbol.

    This tool retrieves all OMIM entries (diseases, phenotypes) that are
    associated with a particular gene.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1", "CFTR")

    Returns:
        JSON string with list of OMIM diseases including:
        - MIM numbers
        - Disease names
        - Inheritance patterns
        - Gene-disease relationships

    Example:
        get_omim_by_gene_symbol("TP53")  # Li-Fraumeni syndrome
        get_omim_by_gene_symbol("BRCA1")  # Breast/ovarian cancer
        get_omim_by_gene_symbol("CFTR")  # Cystic fibrosis
    """
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def get_omim_variant(gene_symbol: str, variant: str) -> str:
    """
    Query OMIM for specific variant information.

    Get OMIM data for a specific variant in a gene, including disease
    associations and clinical significance.

    Args:
        gene_symbol: Gene symbol (e.g., "TP53")
        variant: Variant description (e.g., "p.R248Q", "c.743G>A")

    Returns:
        JSON string with variant-specific OMIM information

    Example:
        get_omim_variant("TP53", "p.R248Q")
        get_omim_variant("BRCA1", "p.C61G")
    """
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def search_omim_by_disease_name(disease_name: str) -> str:
    """
    Search OMIM (Online Mendelian Inheritance in Man) by disease name or keyword.

    This tool allows searching for OMIM entries using disease names, symptoms,
    or related keywords. Useful for researchers who don't know the specific
    OMIM ID but want to find relevant genetic disorders.

    Args:
        disease_name: Disease name, symptom, or keyword to search for
                     (e.g., "breast cancer", "cystic fibrosis", "diabetes")

    Returns:
        JSON string with matching OMIM entries including:
        - MIM numbers and disease names
        - Alternative names and synonyms
        - Brief descriptions and clinical features
        - Inheritance patterns
        - Associated genes (when available)

    Example:
        search_omim_by_disease_name("breast cancer")
        search_omim_by_disease_name("cystic fibrosis")
        search_omim_by_disease_name("diabetes")
    """
    try:
        # URL encode the disease name for the API call
        import urllib.parse

        encoded_disease = urllib.parse.quote(disease_name)
        data = await fetch_marrvel_data(f"/omim/phenotypes/title/{encoded_disease}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


def register_tools(mcp_instance: FastMCP):
    """
    Register all disease tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    # Register the tools
    mcp_instance.tool()(get_omim_by_mim_number)
    mcp_instance.tool()(get_omim_by_gene_symbol)
    mcp_instance.tool()(get_omim_variant)
    mcp_instance.tool()(search_omim_by_disease_name)
