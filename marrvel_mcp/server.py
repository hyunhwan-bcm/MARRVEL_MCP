"""
Main server module for MARRVEL-MCP.

This module initializes the FastMCP server and registers all tools.
"""

from mcp.server.fastmcp import FastMCP

from .config import SERVER_NAME
from .tools import (
    register_gene_tools,
    register_variant_tools,
    register_disease_tools,
    register_ortholog_tools,
    register_expression_tools,
    register_utility_tools,
)


def create_server() -> FastMCP:
    """
    Create and configure the MARRVEL MCP server with all tools.
    
    Returns:
        Configured FastMCP server instance
    """
    # Initialize FastMCP server
    mcp = FastMCP(SERVER_NAME)
    
    # Register all tool modules
    register_gene_tools(mcp)
    register_variant_tools(mcp)
    register_disease_tools(mcp)
    register_ortholog_tools(mcp)
    register_expression_tools(mcp)
    register_utility_tools(mcp)
    
    return mcp


def run_server() -> None:
    """
    Create and run the MARRVEL MCP server.
    
    This is the main entry point for running the server.
    """
    mcp = create_server()
    mcp.run()
