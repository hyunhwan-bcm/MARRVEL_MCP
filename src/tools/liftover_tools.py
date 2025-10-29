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
    Convert hg38 coordinates to hg19 using MARRVEL liftover API.

    Args:
        chr: Chromosome (e.g., "3")
        pos: Position (integer, e.g., 12345)

    Returns:
        JSON string with hg19 coordinates (e.g., {"hg19Chr": "3", "hg19Pos": 75271215})

    Example:
        liftover_hg38_to_hg19("3", 12345)

    Note:
        By default, assume input coordinates are hg38 unless user or database specifies hg19.
    """
    try:
        endpoint = f"/liftover/hg38/chr/{chr}/pos/{pos}/hg19"
        data = await fetch_marrvel_data(endpoint)
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error fetching liftover data: {str(e)}"})


async def liftover_hg19_to_hg38(chr: str, pos: int) -> str:
    """
    Convert hg19 coordinates to hg38 using MARRVEL liftover API.

    Args:
        chr: Chromosome (e.g., "3")
        pos: Position (integer, e.g., 75271215)

    Returns:
        JSON string with hg38 coordinates (e.g., {"hg38Chr": "3", "hg38Pos": 12345})

    Example:
        liftover_hg19to_hg38("3", 75271215)

    Note:
        Use this only if the database or user specifically provides hg19 coordinates; otherwise, default to hg38.
    """
    try:
        endpoint = f"/liftover/hg19/chr/{chr}/pos/{pos}/hg38"
        data = await fetch_marrvel_data(endpoint)
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error fetching liftover data: {str(e)}"})
