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
import inspect
from typing import Any
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("MARRVEL")

# Base API URL for MARRVEL
BASE_URL = "http://api.marrvel.org/data"


# Helper function to make API requests
async def fetch_marrvel_data(endpoint: str) -> dict[str, Any]:
    """
    Fetch data from MARRVEL API.
    
    Args:
        endpoint: API endpoint path (e.g., "/gene/entrezId/7157")
        
    Returns:
        JSON response from the API
        
    Raises:
        httpx.HTTPError: If the request fails
    """
    url = f"{BASE_URL}{endpoint}"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        # Some tests may mock raise_for_status/json as async coroutines; handle both sync/async.
        rfs = response.raise_for_status()
        if inspect.iscoroutine(rfs):
            await rfs
        data = response.json()
        if inspect.iscoroutine(data):
            data = await data
        return data


# ============================================================================
# GENE TOOLS
# ============================================================================

@mcp.tool()
async def get_gene_by_entrez_id(entrez_id: str) -> str:
    """
    Retrieve comprehensive gene information using NCBI Entrez Gene ID.
    
    This tool provides detailed information about a gene including its symbol,
    name, chromosomal location, summary, transcripts, and links to various databases.
    
    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53, "672" for BRCA1)
        
    Returns:
        JSON string with gene information including:
        - Gene symbol and full name
        - Chromosomal location
        - Gene summary/description
        - RefSeq transcripts
        - External database identifiers
        
    Example:
        get_gene_by_entrez_id("7157")  # TP53
        get_gene_by_entrez_id("672")   # BRCA1
    """
    try:
        data = await fetch_marrvel_data(f"/gene/entrezId/{entrez_id}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


@mcp.tool()
async def get_gene_by_symbol(gene_symbol: str, taxon_id: str = "9606") -> str:
    """
    Find gene information using gene symbol and species taxonomy ID.
    
    This tool allows you to search for genes by their symbol in different species.
    Default is human (taxon_id: 9606).
    
    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1", "CFTR")
        taxon_id: NCBI taxonomy ID for the species. Common values:
            - "9606": Human (Homo sapiens) - DEFAULT
            - "10090": Mouse (Mus musculus)
            - "10116": Rat (Rattus norvegicus)
            - "7955": Zebrafish (Danio rerio)
            - "7227": Fruit fly (Drosophila melanogaster)
            - "6239": C. elegans (Caenorhabditis elegans)
            
    Returns:
        JSON string with gene information for the specified species
        
    Example:
        get_gene_by_symbol("TP53", "9606")  # Human TP53
        get_gene_by_symbol("Trp53", "10090")  # Mouse Trp53
        get_gene_by_symbol("tp53", "7955")  # Zebrafish tp53
    """
    try:
        data = await fetch_marrvel_data(f"/gene/taxonId/{taxon_id}/symbol/{gene_symbol}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


@mcp.tool()
async def get_gene_by_position(chromosome: str, position: int) -> str:
    """
    Identify genes at specific chromosomal positions using hg19 coordinates.
    
    This tool helps find which gene(s) are located at a particular genomic position.
    Uses hg19/GRCh37 reference genome coordinates.
    
    Args:
        chromosome: Chromosome name with 'chr' prefix (e.g., "chr17", "chrX", "chr22")
        position: Chromosomal position in base pairs (hg19 coordinates)
        
    Returns:
        JSON string with gene(s) at the specified location including:
        - Gene symbol and name
        - Exact position information
        - Overlapping transcripts
        
    Example:
        get_gene_by_position("chr17", 7577121)  # TP53 region
        get_gene_by_position("chr13", 32900000)  # BRCA2 region
        get_gene_by_position("chrX", 153760000)  # F8 region
    """
    try:
        data = await fetch_marrvel_data(f"/gene/chr/{chromosome}/pos/{position}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


# ============================================================================
# VARIANT ANALYSIS TOOLS
# ============================================================================

@mcp.tool()
async def get_variant_dbnsfp(variant: str) -> str:
    """
    Retrieve comprehensive variant annotations from dbNSFP database.
    
    dbNSFP provides functional predictions and annotations for variants including
    SIFT, PolyPhen2, CADD scores, conservation scores, and population frequencies.
    
    Args:
        variant: Variant in format "chromosome-position-reference-alternate"
                 Uses hg19/GRCh37 coordinates
                 Example: "17-7577121-C-T"
        
    Returns:
        JSON string with extensive variant annotations:
        - Functional predictions (SIFT, PolyPhen2, FATHMM, etc.)
        - Conservation scores (GERP++, PhyloP, PhastCons)
        - CADD scores (pathogenicity prediction)
        - Population frequencies from various databases
        - Gene and protein information
        
    Example:
        get_variant_dbnsfp("17-7577121-C-T")  # TP53 variant
        get_variant_dbnsfp("13-32900000-G-A")  # BRCA2 region
    """
    try:
        data = await fetch_marrvel_data(f"/dbnsfp/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching dbNSFP data: {str(e)}"


@mcp.tool()
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
        data = await fetch_marrvel_data(f"/clinvar/gene/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching ClinVar data: {str(e)}"


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


@mcp.tool()
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


# ============================================================================
# DISEASE TOOLS (OMIM)
# ============================================================================

@mcp.tool()
async def get_omim_by_mim_number(mim_number: str) -> str:
    """
    Retrieve OMIM (Online Mendelian Inheritance in Man) entry by MIM number.
    
    OMIM is a comprehensive database of human genes and genetic disorders.
    
    Args:
        mim_number: OMIM MIM number (e.g., "191170" for Treacher Collins syndrome)
        
    Returns:
        JSON string with OMIM entry:
        - Disease/phenotype description
        - Clinical features
        - Inheritance pattern
        - Molecular genetics
        - Allelic variants
        
    Example:
        get_omim_by_mim_number("191170")  # Treacher Collins syndrome
        get_omim_by_mim_number("114480")  # Breast cancer (BRCA1)
    """
    try:
        data = await fetch_marrvel_data(f"/omim/mimNumber/{mim_number}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


@mcp.tool()
async def get_omim_by_gene_symbol(gene_symbol: str) -> str:
    """
    Find all OMIM diseases associated with a gene symbol.
    
    This tool retrieves all OMIM entries (diseases, phenotypes) that are
    associated with a particular gene.
    
    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1", "CFTR")
        
    Returns:
        JSON string with list of OMIM diseases including:
        - MIM numbers
        - Disease names
        - Inheritance patterns
        - Gene-disease relationships
        
    Example:
        get_omim_by_gene_symbol("TP53")  # Li-Fraumeni syndrome
        get_omim_by_gene_symbol("BRCA1")  # Breast/ovarian cancer
        get_omim_by_gene_symbol("CFTR")  # Cystic fibrosis
    """
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


@mcp.tool()
async def get_omim_variant(gene_symbol: str, variant: str) -> str:
    """
    Query OMIM for specific variant information.
    
    Get OMIM data for a specific variant in a gene, including disease
    associations and clinical significance.
    
    Args:
        gene_symbol: Gene symbol (e.g., "TP53")
        variant: Variant description (e.g., "p.R248Q", "c.743G>A")
        
    Returns:
        JSON string with variant-specific OMIM information
        
    Example:
        get_omim_variant("TP53", "p.R248Q")
        get_omim_variant("BRCA1", "p.C61G")
    """
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


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
