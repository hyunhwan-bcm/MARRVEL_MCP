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
from src.tools import (
    gene_tools,
    variant_tools,
    disease_tools,
    ortholog_tools,
    expression_tools,
    utility_tools
)

# Initialize FastMCP server
mcp = FastMCP("MARRVEL")

# Register tools
gene_tools.register_tools(mcp)
variant_tools.register_tools(mcp)
disease_tools.register_tools(mcp)
ortholog_tools.register_tools(mcp)
expression_tools.register_tools(mcp)
utility_tools.register_tools(mcp)


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
# UTILITY TOOLS - Now imported from src.tools.utility_tools
# ============================================================================
# The following utility tools are now registered from the utility_tools module:
# - validate_hgvs_variant (Mutalyzer HGVS validation)
# - convert_protein_variant (Transvar coordinate conversion)


# ============================================================================
# SERVER STARTUP
# ============================================================================

if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
