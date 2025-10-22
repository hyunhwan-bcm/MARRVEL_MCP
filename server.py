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
from src.tools import gene_tools, variant_tools, disease_tools

# Initialize FastMCP server
mcp = FastMCP("MARRVEL")

# Register tools
gene_tools.register_tools(mcp)
variant_tools.register_tools(mcp)
disease_tools.register_tools(mcp)


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
# ============================================================================
# DISEASE TOOLS (OMIM) - Now imported from src.tools.disease_tools
# ============================================================================
# The following disease tools are now registered from the disease_tools module:
# - get_omim_by_mim_number
# - get_omim_by_gene_symbol
# - get_omim_variant


# ============================================================================
# ORTHOLOG TOOLS (DIOPT)
# ============================================================================

@mcp.tool()
async def get_diopt_orthologs(entrez_id: str) -> str:
    """
    Find orthologs across model organisms using DIOPT.
    
    DIOPT (DRSC Integrative Ortholog Prediction Tool) integrates multiple
    ortholog prediction algorithms to identify orthologs with high confidence.
    
    Args:
        entrez_id: Human gene Entrez ID
        
    Returns:
        JSON string with ortholog predictions:
        - Orthologs in multiple species (Mouse, Rat, Zebrafish, Fly, Worm, Yeast)
        - DIOPT confidence scores
        - Number of supporting algorithms
        - Gene symbols in each species
        
    Example:
        get_diopt_orthologs("7157")  # TP53 orthologs
        get_diopt_orthologs("672")   # BRCA1 orthologs
    """
    try:
        data = await fetch_marrvel_data(f"/diopt/ortholog/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT data: {str(e)}"


@mcp.tool()
async def get_diopt_alignment(entrez_id: str) -> str:
    """
    Get protein sequence alignments for orthologs.
    
    Provides multiple sequence alignment of protein sequences across species
    to visualize conservation patterns.
    
    Args:
        entrez_id: Human gene Entrez ID
        
    Returns:
        JSON string with sequence alignment data:
        - Aligned protein sequences
        - Conservation patterns
        - Protein domain information
        
    Example:
        get_diopt_alignment("7157")  # TP53 alignment
        get_diopt_alignment("672")   # BRCA1 alignment
    """
    try:
        data = await fetch_marrvel_data(f"/diopt/alignment/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT alignment data: {str(e)}"


# ============================================================================
# EXPRESSION TOOLS
# ============================================================================

@mcp.tool()
async def get_gtex_expression(entrez_id: str) -> str:
    """
    Access GTEx (Genotype-Tissue Expression) data.
    
    GTEx provides gene expression levels across 54 human tissues from
    healthy donors.
    
    Args:
        entrez_id: Gene Entrez ID
        
    Returns:
        JSON string with expression data:
        - Median TPM (Transcripts Per Million) per tissue
        - Expression variability
        - Sample sizes
        - Tissue-specific expression patterns
        
    Example:
        get_gtex_expression("7157")  # TP53 expression
        get_gtex_expression("672")   # BRCA1 expression
    """
    try:
        data = await fetch_marrvel_data(f"/gtex/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching GTEx data: {str(e)}"


@mcp.tool()
async def get_ortholog_expression(entrez_id: str) -> str:
    """
    Get expression data for orthologs across model organisms.
    
    Provides comparative expression patterns for gene orthologs in
    model organisms including developmental stages and tissue types.
    
    Args:
        entrez_id: Human gene Entrez ID
        
    Returns:
        JSON string with ortholog expression data:
        - Expression in mouse, fly, zebrafish, etc.
        - Developmental stage expression
        - Tissue-specific patterns in models
        
    Example:
        get_ortholog_expression("7157")  # TP53 orthologs
        get_ortholog_expression("672")   # BRCA1 orthologs
    """
    try:
        data = await fetch_marrvel_data(f"/expression/orthologs/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching ortholog expression data: {str(e)}"


@mcp.tool()
async def get_pharos_targets(entrez_id: str) -> str:
    """
    Query Pharos for drug target information.
    
    Pharos is the user interface to the Knowledge Management Center (KMC)
    for the Illuminating the Druggable Genome (IDG) program.
    
    Args:
        entrez_id: Gene Entrez ID
        
    Returns:
        JSON string with drug target information:
        - Target Development Level (Tclin, Tchem, Tbio, Tdark)
        - Known drugs and compounds
        - Clinical trial information
        - Target class and family
        - Druggability assessment
        
    Target Levels:
        - Tclin: Clinical target with approved drugs
        - Tchem: Target with known chemical probes
        - Tbio: Biological target with evidence
        - Tdark: Understudied protein
        
    Example:
        get_pharos_targets("7157")  # TP53 druggability
        get_pharos_targets("672")   # BRCA1 as drug target
    """
    try:
        data = await fetch_marrvel_data(f"/pharos/targets/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching Pharos data: {str(e)}"


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
