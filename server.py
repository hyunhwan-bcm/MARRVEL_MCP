"""
MARRVEL-MCP Server
A Model Context Protocol server for MARRVEL genetics research platform.

This server provides AI agents access to comprehensive genetics databases including:
- Gene information (NCBI, RefSeq)
- Variant annotations (dbNSFP, ClinVar, gnomAD)
- Disease associations (OMIM)
- Ortholog predictions (DIOPT)
- Expression data (GTEx)
- And more...
"""

import httpx
from mcp.server.fastmcp import FastMCP
from src.utils.api_client import fetch_marrvel_data

# Import tool modules
from src.tools import gene_tools, variant_tools, disease_tools, ortholog_tools, expression_tools

# Initialize FastMCP server
mcp = FastMCP("MARRVEL")

# Register tools
gene_tools.register_tools(mcp)
variant_tools.register_tools(mcp)
disease_tools.register_tools(mcp)
ortholog_tools.register_tools(mcp)
expression_tools.register_tools(mcp)


# ============================================================================
# GENE TOOLS - Now imported from src.tools.gene_tools
# ============================================================================
# The following gene tools are now registered from the gene_tools module:
# - get_gene_by_entrez_id
# - get_gene_by_symbol
# - get_gene_by_position


# ============================================================================
# VARIANT ANALYSIS TOOLS - Now imported from src.tools.variant_tools
# ============================================================================
# The following variant tools are now registered from the variant_tools module:
# - get_variant_dbnsfp (dbNSFP)
# - get_clinvar_by_variant, get_clinvar_by_gene_symbol, get_clinvar_by_entrez_id (ClinVar)
# - get_gnomad_variant, get_gnomad_by_gene_symbol, get_gnomad_by_entrez_id (gnomAD)
# - get_dgv_variant, get_dgv_by_entrez_id (DGV)
# - get_decipher_variant, get_decipher_by_location (DECIPHER)
# - get_geno2mp_variant, get_geno2mp_by_entrez_id (Geno2MP)


# ============================================================================
# DISEASE TOOLS (OMIM) - Now imported from src.tools.disease_tools
# ============================================================================
# The following disease tools are now registered from the disease_tools module:
# - get_omim_by_mim_number
# - get_omim_by_gene_symbol
# - get_omim_variant


# ============================================================================
# ORTHOLOG TOOLS (DIOPT) - Now imported from src.tools.ortholog_tools
# ============================================================================
# The following ortholog tools are now registered from the ortholog_tools module:
# - get_diopt_orthologs
# - get_diopt_alignment


# ============================================================================
# EXPRESSION TOOLS - Now imported from src.tools.expression_tools
# ============================================================================
# The following expression tools are now registered from the expression_tools module:
# - get_gtex_expression (GTEx tissue expression)
# - get_ortholog_expression (Model organism expression)
# - get_pharos_targets (Drug target information)


# ============================================================================
# UTILITY TOOLS
# ============================================================================

@mcp.tool()
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


@mcp.tool()
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


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
