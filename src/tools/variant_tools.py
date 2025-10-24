"""
Variant analysis tools for MARRVEL-MCP.

This module provides tools for querying variant annotations from multiple databases:
- dbNSFP: Functional predictions and conservation scores
- ClinVar: Clinical significance and disease associations
- gnomAD: Population allele frequencies
- DGV: Structural variants and CNVs
- DECIPHER: Developmental disorder variants
- Geno2MP: Genotype-phenotype associations
"""

import httpx
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP


def register_tools(mcp_instance: FastMCP):
    """
    Register all variant analysis tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    # Register all 13 variant tools
    mcp_instance.tool()(get_variant_dbnsfp)
    mcp_instance.tool()(get_clinvar_by_variant)
    mcp_instance.tool()(get_clinvar_by_gene_symbol)
    mcp_instance.tool()(get_clinvar_by_entrez_id)
    mcp_instance.tool()(get_gnomad_variant)
    mcp_instance.tool()(get_gnomad_by_gene_symbol)
    mcp_instance.tool()(get_gnomad_by_entrez_id)
    mcp_instance.tool()(get_dgv_variant)
    mcp_instance.tool()(get_dgv_by_entrez_id)
    mcp_instance.tool()(get_decipher_variant)
    mcp_instance.tool()(get_decipher_by_location)
    mcp_instance.tool()(get_geno2mp_variant)
    mcp_instance.tool()(get_geno2mp_by_entrez_id)


# ============================================================================
# dbNSFP - Functional Predictions
# ============================================================================


async def get_variant_dbnsfp(variant: str) -> str:
    """
    Retrieve comprehensive variant annotations from dbNSFP database.

    dbNSFP provides functional predictions and annotations for variants including
    SIFT, PolyPhen2, CADD scores, conservation scores, and population frequencies.

    Args:
        variant: Variant in canonical format "chromosome:position reference>alternate"
                 Uses hg19/GRCh37 coordinates
                 Example: "17:7577121 C>T"

    Returns:
        JSON string with extensive variant annotations:
        - Functional predictions (SIFT, PolyPhen2, FATHMM, etc.)
        - Conservation scores (GERP++, PhyloP, PhastCons)
        - CADD scores (pathogenicity prediction)
        - Population frequencies from various databases
        - Gene and protein information

    Example:
        get_variant_dbnsfp("17:7577121 C>T")  # TP53 variant
        get_variant_dbnsfp("13:32900000 G>A")  # BRCA2 region
    """
    try:
        data = await fetch_marrvel_data(f"/dbnsfp/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching dbNSFP data: {str(e)}"


# ============================================================================
# ClinVar - Clinical Significance
# ============================================================================


async def get_clinvar_by_variant(variant: str) -> str:
    """
    Query ClinVar for clinical significance of a specific variant.

    ClinVar aggregates information about relationships between variants and
    human health conditions.

    Args:
        variant: Variant identifier in format "chromosome-position-ref-alt"

    Returns:
        JSON string with ClinVar data:
        - Clinical significance (Pathogenic, Benign, VUS, etc.)
        - Review status (0-4 stars)
        - Condition/disease associations
        - Submission information
        - HGVS nomenclature

    Example:
        get_clinvar_by_variant("17-7577121-C-T")
    """
    try:
        data = await fetch_marrvel_data(f"/clinvar/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching ClinVar data: {str(e)}"


async def get_clinvar_by_gene_symbol(gene_symbol: str) -> str:
    """
    Get all ClinVar variants associated with a gene symbol.

    Retrieves all variants in ClinVar that are located within or associated
    with the specified gene.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1")

    Returns:
        JSON string with all ClinVar variants for the gene

    Example:
        get_clinvar_by_gene_symbol("TP53")
        get_clinvar_by_gene_symbol("BRCA1")
    """
    try:
        data = await fetch_marrvel_data(f"/clinvar/gene/symbol/{gene_symbol}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching ClinVar data: {str(e)}"


async def get_clinvar_by_entrez_id(entrez_id: str) -> str:
    """
    Get all ClinVar variants for a gene using Entrez ID.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with all ClinVar variants for the gene

    Example:
        get_clinvar_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/clinvar/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching ClinVar data: {str(e)}"


# ============================================================================
# gnomAD - Population Frequencies
# ============================================================================


async def get_gnomad_variant(variant: str) -> str:
    """
    Access population allele frequencies from gnomAD database.

    gnomAD (Genome Aggregation Database) provides allele frequencies from
    large-scale sequencing projects across diverse populations.

    Args:
        variant: Variant in format "chromosome-position-reference-alternate"

    Returns:
        JSON string with population frequency data:
        - Overall allele frequency
        - Population-specific frequencies (AFR, AMR, EAS, FIN, NFE, SAS, etc.)
        - Allele counts and number
        - Homozygote counts
        - Quality metrics

    Example:
        get_gnomad_variant("17-7577121-C-T")
    """
    try:
        data = await fetch_marrvel_data(f"/gnomad/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching gnomAD data: {str(e)}"


async def get_gnomad_by_gene_symbol(gene_symbol: str) -> str:
    """
    Get gnomAD variant data for all variants in a gene.

    Args:
        gene_symbol: Official gene symbol

    Returns:
        JSON string with gnomAD data for all variants in the gene

    Example:
        get_gnomad_by_gene_symbol("TP53")
    """
    try:
        data = await fetch_marrvel_data(f"/gnomad/gene/symbol/{gene_symbol}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching gnomAD data: {str(e)}"


async def get_gnomad_by_entrez_id(entrez_id: str) -> str:
    """
    Get gnomAD variant data for a gene using Entrez ID.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with gnomAD data for all variants in the gene

    Example:
        get_gnomad_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/gnomad/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching gnomAD data: {str(e)}"


# ============================================================================
# DGV - Structural Variants
# ============================================================================


async def get_dgv_variant(variant: str) -> str:
    """
    Query Database of Genomic Variants for structural variants and CNVs.

    DGV catalogs structural variations found in healthy individuals.

    Args:
        variant: Variant identifier

    Returns:
        JSON string with structural variant information

    Example:
        get_dgv_variant("17-7577121-C-T")
    """
    try:
        data = await fetch_marrvel_data(f"/dgv/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DGV data: {str(e)}"


async def get_dgv_by_entrez_id(entrez_id: str) -> str:
    """
    Get DGV structural variants for a gene.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with DGV data for the gene region

    Example:
        get_dgv_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/dgv/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DGV data: {str(e)}"


# ============================================================================
# DECIPHER - Developmental Disorders
# ============================================================================


async def get_decipher_variant(variant: str) -> str:
    """
    Access DECIPHER database for developmental disorders and rare variants.

    DECIPHER contains data on chromosomal abnormalities and pathogenic variants
    associated with developmental disorders.

    Args:
        variant: Variant identifier

    Returns:
        JSON string with DECIPHER data including patient phenotypes and CNVs

    Example:
        get_decipher_variant("17-7577121-C-T")
    """
    try:
        data = await fetch_marrvel_data(f"/decipher/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DECIPHER data: {str(e)}"


async def get_decipher_by_location(chromosome: str, start: int, stop: int) -> str:
    """
    Query DECIPHER by genomic location (hg19 coordinates).

    Args:
        chromosome: Chromosome (e.g., "chr17")
        start: Start position (hg19)
        stop: End position (hg19)

    Returns:
        JSON string with DECIPHER data for the genomic region

    Example:
        get_decipher_by_location("chr17", 7570000, 7590000)
    """
    try:
        data = await fetch_marrvel_data(f"/decipher/genomloc/{chromosome}/{start}/{stop}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching DECIPHER data: {str(e)}"


# ============================================================================
# Geno2MP - Genotype-Phenotype Associations
# ============================================================================


async def get_geno2mp_variant(variant: str) -> str:
    """
    Query Geno2MP for genotype-to-phenotype associations.

    Geno2MP links genetic variants to Human Phenotype Ontology (HPO) terms.

    Args:
        variant: Variant identifier

    Returns:
        JSON string with genotype-phenotype associations

    Example:
        get_geno2mp_variant("17-7577121-C-T")
    """
    try:
        data = await fetch_marrvel_data(f"/geno2mp/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching Geno2MP data: {str(e)}"


async def get_geno2mp_by_entrez_id(entrez_id: str) -> str:
    """
    Get Geno2MP phenotype associations for a gene.

    Args:
        entrez_id: NCBI Entrez Gene ID

    Returns:
        JSON string with phenotype data for the gene

    Example:
        get_geno2mp_by_entrez_id("7157")  # TP53
    """
    try:
        data = await fetch_marrvel_data(f"/geno2mp/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching Geno2MP data: {str(e)}"
