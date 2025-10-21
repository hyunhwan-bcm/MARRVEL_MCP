"""
Example queries and usage patterns for MARRVEL-MCP server.

This file demonstrates how to interact with the MARRVEL-MCP server
through an AI assistant or directly through the MCP protocol.
"""

# ============================================================================
# GENE QUERIES
# ============================================================================

"""
Example 1: Get basic gene information
--------------------------------------
User: "Tell me about the TP53 gene"
Agent uses: get_gene_by_entrez_id("7157")
         or get_gene_by_symbol("TP53", "9606")

User: "What gene is at chromosome 17 position 7577121?"
Agent uses: get_gene_by_position("chr17", 7577121)
"""

"""
Example 2: Cross-species gene queries
--------------------------------------
User: "Find the mouse ortholog of TP53"
Agent uses: 
  1. get_gene_by_symbol("TP53", "9606") to get human gene info
  2. get_diopt_orthologs("7157") to find mouse ortholog
  3. get_gene_by_symbol("Trp53", "10090") for mouse gene details

User: "Show me tp53 in zebrafish"
Agent uses: get_gene_by_symbol("tp53", "7955")
"""

# ============================================================================
# VARIANT ANALYSIS QUERIES
# ============================================================================

"""
Example 3: Comprehensive variant analysis
------------------------------------------
User: "Analyze variant chr17:7577121C>T"
Agent uses multiple tools:
  1. get_variant_dbnsfp("17-7577121-C-T")        # Functional predictions
  2. get_clinvar_by_variant("17-7577121-C-T")    # Clinical significance
  3. get_gnomad_variant("17-7577121-C-T")        # Population frequency
  4. get_geno2mp_variant("17-7577121-C-T")       # Phenotype associations
"""

"""
Example 4: Clinical significance queries
-----------------------------------------
User: "Is variant 17-7577121-C-T pathogenic?"
Agent uses: get_clinvar_by_variant("17-7577121-C-T")

User: "What's the population frequency of this variant?"
Agent uses: get_gnomad_variant("17-7577121-C-T")

User: "Show me all pathogenic variants in BRCA1"
Agent uses: get_clinvar_by_gene_symbol("BRCA1")
"""

"""
Example 5: Variant interpretation workflow
-------------------------------------------
User: "Interpret variant NM_000546.5:c.215C>G"
Agent workflow:
  1. validate_hgvs_variant("NM_000546.5:c.215C>G")  # Validate format
  2. Extract genomic coordinates from result
  3. get_variant_dbnsfp("17-7577121-C-G")           # Predictions
  4. get_clinvar_by_variant("17-7577121-C-G")       # Clinical data
  5. get_gnomad_variant("17-7577121-C-G")           # Frequency
  6. Provide comprehensive interpretation
"""

# ============================================================================
# DISEASE AND PHENOTYPE QUERIES
# ============================================================================

"""
Example 6: Gene-disease associations
-------------------------------------
User: "What diseases are associated with TP53?"
Agent uses: get_omim_by_gene_symbol("TP53")

User: "Tell me about Li-Fraumeni syndrome"
Agent uses: get_omim_by_mim_number("151623")

User: "What are the symptoms of mutations in BRCA1?"
Agent uses:
  1. get_omim_by_gene_symbol("BRCA1")
  2. get_geno2mp_by_entrez_id("672")  # For phenotype data
"""

"""
Example 7: Variant-specific disease queries
--------------------------------------------
User: "What disease is caused by TP53 p.R248Q variant?"
Agent uses: get_omim_variant("TP53", "p.R248Q")
"""

# ============================================================================
# ORTHOLOG AND MODEL ORGANISM QUERIES
# ============================================================================

"""
Example 8: Finding and analyzing orthologs
-------------------------------------------
User: "Find orthologs of human TP53 across model organisms"
Agent uses: get_diopt_orthologs("7157")

User: "Show me the protein alignment of TP53 orthologs"
Agent uses: get_diopt_alignment("7157")

User: "What's the DIOPT score for TP53 orthologs?"
Agent uses: get_diopt_orthologs("7157") and explains scoring
"""

"""
Example 9: Comparative genomics workflow
-----------------------------------------
User: "Compare TP53 across human, mouse, and fly"
Agent workflow:
  1. get_gene_by_symbol("TP53", "9606")      # Human
  2. get_diopt_orthologs("7157")              # Find orthologs
  3. get_gene_by_symbol("Trp53", "10090")    # Mouse details
  4. get_gene_by_symbol("p53", "7227")       # Fly details
  5. get_diopt_alignment("7157")              # Alignment
  6. get_ortholog_expression("7157")          # Expression comparison
"""

# ============================================================================
# EXPRESSION QUERIES
# ============================================================================

"""
Example 10: Gene expression analysis
-------------------------------------
User: "Where is TP53 expressed in the human body?"
Agent uses: get_gtex_expression("7157")

User: "Show me expression of BRCA1 orthologs across species"
Agent uses: get_ortholog_expression("672")

User: "Which tissue has the highest TP53 expression?"
Agent uses: get_gtex_expression("7157") and analyzes TPM values
"""

# ============================================================================
# DRUG TARGET QUERIES
# ============================================================================

"""
Example 11: Druggability assessment
------------------------------------
User: "Is TP53 a drug target?"
Agent uses: get_pharos_targets("7157")

User: "Are there drugs targeting BRCA1?"
Agent uses: get_pharos_targets("672")

User: "What's the druggability classification of gene 7157?"
Agent uses: get_pharos_targets("7157") and explains Tclin/Tchem/Tbio/Tdark
"""

# ============================================================================
# STRUCTURAL VARIANT QUERIES
# ============================================================================

"""
Example 12: Structural variant analysis
----------------------------------------
User: "Are there CNVs in the TP53 region?"
Agent uses:
  1. get_dgv_by_entrez_id("7157")                    # DGV data
  2. get_decipher_by_location("chr17", 7570000, 7590000)  # DECIPHER data

User: "Show me structural variants affecting BRCA1"
Agent uses:
  1. get_dgv_by_entrez_id("672")
  2. get_decipher_variant(...)  # If specific variant known
"""

# ============================================================================
# COMPLEX RESEARCH WORKFLOWS
# ============================================================================

"""
Example 13: Complete gene analysis
-----------------------------------
User: "Give me a comprehensive analysis of the TP53 gene"
Agent performs:
  1. get_gene_by_entrez_id("7157")           # Basic info
  2. get_omim_by_gene_symbol("TP53")         # Disease associations
  3. get_clinvar_by_gene_symbol("TP53")      # Clinical variants
  4. get_gnomad_by_entrez_id("7157")         # Population variants
  5. get_gtex_expression("7157")             # Expression profile
  6. get_diopt_orthologs("7157")             # Model organisms
  7. get_pharos_targets("7157")              # Druggability
  8. Synthesizes all information into comprehensive report
"""

"""
Example 14: Variant prioritization workflow
--------------------------------------------
User: "Help me prioritize variants in TP53 for functional studies"
Agent workflow:
  1. get_clinvar_by_gene_symbol("TP53")      # Known pathogenic variants
  2. get_gnomad_by_entrez_id("7157")         # Filter rare variants
  3. get_variant_dbnsfp(...) for each        # Functional predictions
  4. get_geno2mp_by_entrez_id("7157")        # Phenotype data
  5. Ranks variants by:
     - Clinical significance
     - Rarity (allele frequency)
     - Functional predictions
     - Phenotypic impact
"""

"""
Example 15: Cross-species functional validation
------------------------------------------------
User: "Can I use Drosophila to study a TP53 variant?"
Agent workflow:
  1. get_diopt_orthologs("7157")             # Find fly ortholog
  2. get_diopt_alignment("7157")             # Check conservation at position
  3. get_ortholog_expression("7157")         # Expression patterns
  4. Provides recommendation based on:
     - DIOPT score
     - Conservation of affected residue
     - Expression similarity
"""

"""
Example 16: Disease mechanism investigation
--------------------------------------------
User: "How do BRCA1 mutations cause cancer?"
Agent workflow:
  1. get_gene_by_entrez_id("672")            # Gene function
  2. get_omim_by_gene_symbol("BRCA1")        # Disease mechanism
  3. get_clinvar_by_gene_symbol("BRCA1")     # Pathogenic variants
  4. get_pharos_targets("672")               # Pathway information
  5. Synthesizes information about:
     - DNA repair function
     - Specific mutations
     - Cancer predisposition
     - Therapeutic approaches
"""

"""
Example 17: Population genetics analysis
-----------------------------------------
User: "What's the carrier frequency of pathogenic CFTR variants?"
Agent workflow:
  1. get_gene_by_symbol("CFTR", "9606")      # Gene info
  2. get_clinvar_by_gene_symbol("CFTR")      # Pathogenic variants
  3. For each pathogenic variant:
     - get_gnomad_variant(...)                # Get frequency
  4. Calculates carrier frequency
  5. get_omim_by_gene_symbol("CFTR")         # Disease info
"""

# ============================================================================
# VARIANT NOMENCLATURE AND CONVERSION
# ============================================================================

"""
Example 18: Variant format conversion
--------------------------------------
User: "Convert protein variant p.R248Q to genomic coordinates"
Agent uses: convert_protein_variant("ENSP00000269305:p.R248Q")

User: "Is this HGVS notation correct: NM_000546.5:c.215C>G?"
Agent uses: validate_hgvs_variant("NM_000546.5:c.215C>G")

User: "Convert NM_000546.5:c.215C>G to genomic notation"
Agent workflow:
  1. validate_hgvs_variant("NM_000546.5:c.215C>G")
  2. Extracts genomic coordinates from result
"""

# ============================================================================
# TIPS FOR EFFECTIVE USAGE
# ============================================================================

"""
Best Practices:
---------------

1. Start with gene lookup:
   - Use Entrez ID when known (more reliable)
   - Use gene symbol + taxon ID for species-specific queries

2. For variants:
   - Always use chromosome-position-ref-alt format for MARRVEL
   - Validate HGVS nomenclature before using
   - Check multiple databases for comprehensive analysis

3. For disease research:
   - Start with OMIM for gene-disease relationships
   - Use ClinVar for variant-level clinical significance
   - Check gnomAD to assess variant rarity

4. For model organism studies:
   - Use DIOPT for ortholog prediction
   - Check alignment for conservation
   - Verify expression patterns match

5. Comprehensive analysis:
   - Combine multiple tools for complete picture
   - Cross-reference findings across databases
   - Consider population frequencies in interpretation
"""

# ============================================================================
# ERROR HANDLING EXAMPLES
# ============================================================================

"""
Example 19: Handling non-existent genes/variants
-------------------------------------------------
User: "Get information for gene XYZ123"
Agent:
  1. Attempts get_gene_by_symbol("XYZ123")
  2. Receives error
  3. Suggests: "Gene symbol not found. Please check spelling or provide Entrez ID"

User: "Analyze variant 99-1234567-A-T"
Agent:
  1. Attempts get_variant_dbnsfp("99-1234567-A-T")
  2. Receives error (chromosome 99 doesn't exist)
  3. Suggests: "Invalid chromosome. Please use chr1-22, chrX, chrY, or chrM"
"""

"""
Example 20: Coordinate system handling
---------------------------------------
User: "Find variant at position 7,577,121 on chromosome 17"
Agent:
  1. Recognizes this is likely hg19 coordinates
  2. Uses get_variant_dbnsfp("17-7577121-C-T") if ref/alt known
  3. Or uses get_gene_by_position("chr17", 7577121) to find gene
  4. Notes: "Using hg19 coordinates. For hg38, please convert first."
"""
