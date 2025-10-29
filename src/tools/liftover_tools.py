"""
Liftover tools for MARRVEL-MCP.

This module provides tools for converting genome coordinates between hg38 and hg19 using the MARRVEL liftover API.
Default behavior: Assume input coordinates are hg38 unless explicitly specified as hg19. Most database queries use hg38; use hg19 only if required by the data source or user request.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP
import json


def register_tools(mcp_instance: FastMCP):
    """
    Register liftover tools with the MCP server instance.
    """
    mcp_instance.tool()(liftover_hg38_to_hg19)
    mcp_instance.tool()(liftover_hg19_to_hg38)


async def liftover_hg38_to_hg19(chr: str, pos: int) -> str:
    """
    Convert genome coordinates from hg38/GRCh38 to hg19/GRCh37.

    Returns hg19 coordinates for MARRVEL tool compatibility. Essential when source
    data uses hg38 but MARRVEL tools require hg19.

    Args:
        chr: Chromosome without 'chr' prefix (e.g., "3", "X")
        pos: Position in hg38 coordinates (integer)

    Returns:
        JSON with hg19Chr and hg19Pos

    Example:
        liftover_hg38_to_hg19("3", 12345)
    """
    try:
        endpoint = f"/liftover/hg38/chr/{chr}/pos/{pos}/hg19"
        data = await fetch_marrvel_data(endpoint)
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error fetching liftover data: {str(e)}"})


async def liftover_hg19_to_hg38(chr: str, pos: int) -> str:
    """
    Convert genome coordinates from hg19/GRCh37 to hg38/GRCh38.

    Returns hg38 coordinates. Use when MARRVEL returns hg19 data but you need
    hg38 for other tools or databases.

    Args:
        chr: Chromosome without 'chr' prefix (e.g., "3", "X")
        pos: Position in hg19 coordinates (integer)

    Returns:
        JSON with hg38Chr and hg38Pos

    Example:
        liftover_hg19_to_hg38("3", 75271215)
    """
    try:
        endpoint = f"/liftover/hg19/chr/{chr}/pos/{pos}/hg38"
        data = await fetch_marrvel_data(endpoint)
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error fetching liftover data: {str(e)}"})
