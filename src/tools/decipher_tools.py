"""
DECIPHER tools for MARRVEL-MCP.

This module provides tools for querying DECIPHER database for developmental disorders and rare variants.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP
import json


def register_tools(mcp_instance: FastMCP):
    """
    Register all DECIPHER tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    mcp_instance.tool()(get_decipher_by_location)


async def get_decipher_by_location(chr: str, start: int, stop: int) -> str:
    """
    Query DECIPHER for control variant statistics in a genomic region.

    Args:
        chr: Chromosome without 'chr' prefix (e.g., "17")
        start: Start position in hg19 (integer)
        stop: End position in hg19 (integer)

    Returns:
        JSON with DECIPHER reported control variants

    Example:
        get_decipher_by_location("17", 7570000, 7590000)
    """
    try:
        data = await fetch_marrvel_data(f"/DECIPHER/genomloc/{chr}/{start}/{stop}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})
