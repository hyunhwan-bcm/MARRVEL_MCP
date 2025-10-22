"""
MARRVEL MCP Server - Utility Tools

This module provides utility tools for variant nomenclature validation
and coordinate conversion.

Includes:
- Mutalyzer - HGVS variant validation and parsing
- Transvar - Protein to genomic coordinate conversion
"""

import httpx
from src.utils.api_client import fetch_marrvel_data


def register_tools(mcp_instance):
    """Register all utility tools with the MCP server."""
    # Register tools
    mcp_instance.tool()(validate_hgvs_variant)
    mcp_instance.tool()(convert_protein_variant)


# ============================================================================
# VARIANT NOMENCLATURE & CONVERSION TOOLS
# ============================================================================

async def validate_hgvs_variant(hgvs_variant: str) -> str:
    """
    Validate and parse HGVS variant nomenclature using Mutalyzer.
    
    Mutalyzer checks if variant descriptions are correct according to HGVS
    nomenclature standards and provides parsed components.
    
    Args:
        hgvs_variant: Variant in HGVS format
            Examples:
            - Genomic: "NC_000017.10:g.7577121C>T"
            - Coding: "NM_000546.5:c.215C>G"
            - Protein: "NP_000537.3:p.Arg72Pro"
        
    Returns:
        JSON string with validation results:
        - Validation status (valid/invalid)
        - Parsed components
        - Genomic coordinates
        - Protein changes
        - Alternative descriptions
        
    Example:
        validate_hgvs_variant("NM_000546.5:c.215C>G")
        validate_hgvs_variant("NC_000017.10:g.7577121C>T")
    """
    try:
        data = await fetch_marrvel_data(f"/mutalyzer/hgvs/{hgvs_variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error validating HGVS variant: {str(e)}"


async def convert_protein_variant(protein_variant: str) -> str:
    """
    Convert protein-level variants to genomic coordinates using Transvar.
    
    Transvar is a tool for converting between different variant annotation
    formats and coordinate systems.
    
    Args:
        protein_variant: Protein variant description
            Examples:
            - "ENSP00000269305:p.R248Q"
            - "NP_000537.3:p.Arg72Pro"
        
    Returns:
        JSON string with converted coordinates:
        - Genomic coordinates (hg19, hg38)
        - cDNA changes
        - Multiple transcript mappings
        - Alternative annotations
        
    Example:
        convert_protein_variant("ENSP00000269305:p.R248Q")
        convert_protein_variant("NP_000537.3:p.Arg72Pro")
    """
    try:
        data = await fetch_marrvel_data(f"/transvar/protein/{protein_variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error converting protein variant: {str(e)}"
