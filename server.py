"""
MARRVEL-MCP Server
==================
A Model Context Protocol server for the MARRVEL genetics research platform.

This server provides AI agents with access to comprehensive genetics databases:
- Gene information (NCBI, RefSeq)
- Variant annotations (dbNSFP, ClinVar, gnomAD, DGV, DECIPHER, Geno2MP)
- Disease associations (OMIM)
- Ortholog predictions (DIOPT)
- Expression data (GTEx, model organisms)
- Drug target information (Pharos)
- Variant nomenclature tools (Mutalyzer, Transvar)

For more information about available tools, see TOOL_REFERENCE.md
For API documentation, see API_DOCUMENTATION.md
"""

from mcp.server.fastmcp import FastMCP

# Import tool modules
from src.tools import (
    gene_tools,
    variant_tools,
    disease_tools,
    ortholog_tools,
    expression_tools,
    utility_tools,
)


def create_server() -> FastMCP:
    """
    Create and configure the MARRVEL MCP server.
    
    Returns:
        FastMCP: Configured MCP server instance with all tools registered
    """
    # Initialize FastMCP server
    mcp = FastMCP("MARRVEL")
    
    # Register all tool modules
    gene_tools.register_tools(mcp)
    variant_tools.register_tools(mcp)
    disease_tools.register_tools(mcp)
    ortholog_tools.register_tools(mcp)
    expression_tools.register_tools(mcp)
    utility_tools.register_tools(mcp)
    
    return mcp


# Create server instance
mcp = create_server()


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
