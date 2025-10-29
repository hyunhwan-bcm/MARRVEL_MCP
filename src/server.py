"""
Core MCP server configuration for MARRVEL.

This module lives inside the package so that it can be imported both by the
GitHub Actions test suite and by external clients via ``import server`` after
the project is installed in editable mode.
"""

import logging, sys, os

# If env flipped you to DEBUG, ignore it for stdio runs
os.environ.pop("PYTHONLOGLEVEL", None)
os.environ.pop("LOG_LEVEL", None)

# Nuke existing handlers some lib may have added
root = logging.getLogger()
for h in list(root.handlers):
    root.removeHandler(h)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.WARNING)
root.addHandler(handler)
root.setLevel(logging.WARNING)


from mcp.server.fastmcp import FastMCP
import sys

from src.tools import (
    gene_tools,
    variant_tools,
    disease_tools,
    ortholog_tools,
    expression_tools,
    utility_tools,
    pubmed_tools,
    liftover_tools,
    decipher_tools,
)


def create_server() -> FastMCP:
    """
    Create and configure the MARRVEL MCP server.

    Returns:
        FastMCP: Configured MCP server instance with all tools registered.
    """

    mcp = FastMCP(
        name="MARRVEL-MCP",
        instructions=(
            "MARRVEL-MCP enables rare disease research through 32+ genetics tools. "
            "Query genes (symbol/ID/position), analyze variants (dbNSFP, ClinVar, gnomAD), "
            "find disease associations (OMIM, DECIPHER), discover orthologs (DIOPT), "
            "search tissue expression (GTEx), identify drug targets (Pharos), and search "
            "literature (PubMed). Supports liftover between genome builds. "
            "Default coordinates: hg19/GRCh37. State clearly when data is unavailable."
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
    decipher_tools.register_tools(mcp)

    return mcp


# Instantiate a shared server instance for convenience.
mcp = create_server()
