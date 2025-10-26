"""
Core MCP server configuration for MARRVEL.

This module lives inside the package so that it can be imported both by the
GitHub Actions test suite and by external clients via ``import server`` after
the project is installed in editable mode.
"""

from mcp.server.fastmcp import FastMCP

from src.tools import (
    gene_tools,
    variant_tools,
    disease_tools,
    ortholog_tools,
    expression_tools,
    utility_tools,
    pubmed_tools,
    liftover_tools,
)


def create_server() -> FastMCP:
    """
    Create and configure the MARRVEL MCP server.

    Returns:
        FastMCP: Configured MCP server instance with all tools registered.
    """

    mcp = FastMCP(
        "MARRVEL-MCP",
        instructions=(
            "MARRVEL-MCP provides curated data and analysis tools for variant and gene "
            "prioritization using public resources (OMIM, ExAC, ClinVar, Geno2MP, DGV, "
            "DECIPHER) and model-organism annotations via DIOPT and model organism "
            "databases. Assume genomic coordinates are hg38 unless otherwise noted. "
            "When data is unavailable, state that clearly."
        ),
    )

    gene_tools.register_tools(mcp)
    variant_tools.register_tools(mcp)
    disease_tools.register_tools(mcp)
    ortholog_tools.register_tools(mcp)
    expression_tools.register_tools(mcp)
    liftover_tools.register_tools(mcp)
    utility_tools.register_tools(mcp)
    pubmed_tools.register_tools(mcp)

    return mcp


# Instantiate a shared server instance for convenience.
mcp = create_server()
