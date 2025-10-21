"""
Disease-related tools for querying OMIM database.
"""

import httpx
from mcp.server.fastmcp import FastMCP

from ..client import fetch_marrvel_data


def register_disease_tools(mcp: FastMCP) -> None:
    """Register all disease-related tools with the MCP server."""
    
    @mcp.tool()
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
            get_omim_by_mim_number("191170")  # Treacher Collins syndrome
            get_omim_by_mim_number("114480")  # Breast cancer (BRCA1)
        """
        try:
            data = await fetch_marrvel_data(f"/omim/mimNumber/{mim_number}")
            return str(data)
        except httpx.HTTPError as e:
            return f"Error fetching OMIM data: {str(e)}"

    @mcp.tool()
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

    @mcp.tool()
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
