# MARRVEL-MCP API Documentation

Comprehensive documentation for all MCP tools provided by the MARRVEL server.

## Table of Contents

1. [Gene Tools](#gene-tools)
2. [Variant Analysis Tools](#variant-analysis-tools)
3. [Disease Tools (OMIM)](#disease-tools-omim)
4. [Ortholog Tools (DIOPT)](#ortholog-tools-diopt)
5. [Expression Tools](#expression-tools)
6. [Utility Tools](#utility-tools)
7. [PubMed Literature Search Tools](#pubmed-literature-search-tools)
8. [Data Format Reference](#data-format-reference)

---

## Gene Tools

### `get_gene_by_entrez_id`

Retrieve comprehensive gene information using NCBI Entrez Gene ID.

**Parameters:**
- `entrez_id` (string, required): NCBI Entrez Gene ID (e.g., "7157" for TP53)

**Returns:**
- Gene symbol and name
- Chromosomal location
- Gene summary
- RefSeq transcripts
- Associated pathways
- External database links

**Example Usage:**
```
"Get information for gene with Entrez ID 7157"
"Look up Entrez ID 672 in MARRVEL"
```

**API Endpoint:** `GET /gene/entrezId/:entrezId`

---

### `get_gene_by_symbol`

Find gene information using gene symbol and species taxonomy ID.

**Parameters:**
- `gene_symbol` (string, required): Official gene symbol (e.g., "TP53", "BRCA1")
- `taxon_id` (string, required): NCBI taxonomy ID
  - Human: "9606"
  - Mouse: "10090"
  - Drosophila: "7227"
  - Zebrafish: "7955"
  - C. elegans: "6239"

**Returns:**
- Gene details for the specified species
- Entrez ID for further queries
- Chromosomal location
- Gene type and description

**Example Usage:**
```
"Find human TP53 gene"
"Get information about mouse Brca1"
"Look up zebrafish tp53"
```

**API Endpoint:** `GET /gene/taxonId/:taxonId/symbol/:symbol`

---

### `get_gene_by_position`

Identify genes at specific chromosomal positions (hg19 coordinates).

**Parameters:**
- `chromosome` (string, required): Chromosome name (e.g., "chr17", "chrX")
- `position` (integer, required): Chromosomal position in hg19 coordinates

**Returns:**
- Gene(s) at the specified location
- Overlapping transcripts
- Positional information

**Example Usage:**
```
"What gene is at chromosome 17 position 7577121?"
"Find genes at chr13:32900000"
```

**API Endpoint:** `GET /gene/gene/chr/:hg19Chr/pos/:hg19Pos`

**Note:** Uses hg19/GRCh37 reference genome.

---

## Variant Analysis Tools

### `get_variant_dbnsfp`

Retrieve comprehensive variant annotations from dbNSFP database.

**Parameters:**
- `variant` (string, required): Variant in format "chr-pos-ref-alt" (e.g., "17-7577121-C-T")

**Returns:**
- Functional predictions (SIFT, PolyPhen2, etc.)
- Conservation scores
- Population frequencies
- Pathogenicity predictions
- CADD scores
- Multiple in-silico prediction tools

**Example Usage:**
```
"Get dbNSFP annotations for variant 17-7577121-C-T"
"What are the functional predictions for chr13-32900000-G-A?"
```

**API Endpoint:** `GET /dbnsfp/variant/:variant`

**Variant Format:** `chromosome-position-reference-alternate` (all using hg19)

---

### `get_variant_clinvar`

Query ClinVar for clinical significance and interpretation.

**Parameters:**
- `variant` (string, required): Variant identifier

**Multiple Query Methods:**
1. **By variant position:** `get_variant_clinvar(variant="17-7577121-C-T")`
2. **By gene symbol:** Use `get_clinvar_by_gene_symbol(gene_symbol="TP53")`
3. **By Entrez ID:** Use `get_clinvar_by_entrez_id(entrez_id="7157")`

**Returns:**
- Clinical significance (Pathogenic, Benign, VUS, etc.)
- Review status
- Condition/disease associations
- Submission details
- Molecular consequence
- HGVS nomenclature

**Example Usage:**
```
"Is variant 17-7577121-C-T pathogenic according to ClinVar?"
"Get all ClinVar variants for TP53"
"What's the clinical significance of this variant?"
```

**API Endpoints:**
- `GET /clinvar/gene/variant/:variant`
- `GET /clinvar/gene/symbol/:geneSymbol`
- `GET /clinvar/gene/entrezId/:entrezId`

---

### `get_variant_gnomad`

Access population allele frequencies from gnomAD (Genome Aggregation Database).

**Parameters:**
- `variant` (string, required): Variant in format "chr-pos-ref-alt"

**Alternative Methods:**
- By gene symbol: `get_gnomad_by_gene_symbol(gene_symbol="TP53")`
- By Entrez ID: `get_gnomad_by_entrez_id(entrez_id="7157")`

**Returns:**
- Allele frequencies across populations
- Allele counts and number
- Homozygote counts
- Quality metrics
- Coverage information
- Population-specific frequencies (AFR, AMR, EAS, FIN, NFE, etc.)

**Example Usage:**
```
"What's the gnomAD frequency for variant 17-7577121-C-T?"
"Get population frequencies for this variant"
"Is this variant common in gnomAD?"
```

**API Endpoints:**
- `GET /gnomad/variant/:variant`
- `GET /gnomad/gene/symbol/:geneSymbol`
- `GET /gnomad/gene/entrezId/:entrezId`

---

### `get_variant_dgv`

Query Database of Genomic Variants for structural variants and CNVs.

**Parameters:**
- `variant` (string, required): Variant identifier

**Alternative Method:**
- By gene: `get_dgv_by_entrez_id(entrez_id="7157")`

**Returns:**
- Structural variant information
- Copy number variations
- Breakpoint coordinates
- Variant type
- Supporting studies

**Example Usage:**
```
"Are there structural variants in the TP53 region?"
"Get DGV data for this genomic position"
```

**API Endpoints:**
- `GET /dgv/variant/:variant`
- `GET /dgv/gene/entrezId/:entrezId`

---

### `get_variant_decipher`

Access DECIPHER database for developmental disorders and rare variants.

**Parameters:**
- `variant` (string, required): Variant identifier

**Alternative Method:**
- By genomic location: `get_decipher_by_location(chromosome="chr17", start=7570000, stop=7590000)`

**Returns:**
- Patient phenotype data
- CNV information
- Pathogenicity evidence
- Syndrome associations

**Example Usage:**
```
"Check DECIPHER for pathogenic variants in this region"
"Get DECIPHER data for chr17:7570000-7590000"
```

**API Endpoints:**
- `GET /decipher/variant/:variant`
- `GET /decipher/genomloc/:hg19Chr/:hg19Start/:hg19Stop`

---

### `get_variant_geno2mp`

Query Geno2MP for genotype-to-phenotype associations.

**Parameters:**
- `variant` (string, required): Variant identifier

**Alternative Method:**
- By gene: `get_geno2mp_by_entrez_id(entrez_id="7157")`

**Returns:**
- Phenotype associations
- HPO (Human Phenotype Ontology) terms
- Clinical features
- Patient data

**Example Usage:**
```
"What phenotypes are associated with variants in TP53?"
"Get Geno2MP data for this variant"
```

**API Endpoints:**
- `GET /geno2mp/variant/:variant`
- `GET /geno2mp/gene/entrezId/:entrezId`

---

## Disease Tools (OMIM)

### `get_omim_by_mim_number`

Retrieve OMIM entry by MIM number.

**Parameters:**
- `mim_number` (string, required): OMIM MIM number (e.g., "191170")

**Returns:**
- Disease/phenotype description
- Clinical features
- Inheritance pattern
- Molecular genetics
- Gene-phenotype relationships
- Allelic variants

**Example Usage:**
```
"Get OMIM entry 191170"
"What is OMIM 600060?"
```

**API Endpoint:** `GET /omim/mimNumber/:mimNumber`

---

### `get_omim_by_gene_symbol`

Find all OMIM diseases associated with a gene symbol.

**Parameters:**
- `gene_symbol` (string, required): Gene symbol (e.g., "TP53", "BRCA1")

**Returns:**
- List of associated diseases
- MIM numbers
- Inheritance patterns
- Phenotype descriptions
- Gene-disease relationships

**Example Usage:**
```
"What diseases are associated with TP53?"
"Show me OMIM entries for BRCA1"
"List all disorders linked to CFTR gene"
```

**API Endpoint:** `GET /omim/gene/symbol/:geneSymbol`

---

### `get_omim_variant`

Query OMIM for specific variant information.

**Parameters:**
- `gene_symbol` (string, required): Gene symbol
- `variant` (string, required): Variant description (e.g., "p.R248Q")

**Returns:**
- Variant-specific disease associations
- Clinical significance
- Reported cases
- Molecular consequences

**Example Usage:**
```
"Get OMIM information for TP53 variant p.R248Q"
"What diseases are caused by BRCA1 variant p.C61G?"
```

**API Endpoint:** `GET /omim/gene/symbol/:geneSymbol/variant/:variant`

---

## Ortholog Tools (DIOPT)

### `get_diopt_orthologs`

Find orthologs across model organisms using DIOPT.

**Parameters:**
- `entrez_id` (string, required): Human gene Entrez ID

**Returns:**
- Ortholog predictions across species
- DIOPT scores
- Supporting evidence
- Ortholog confidence levels
- Species: Human, Mouse, Rat, Zebrafish, Drosophila, C. elegans, Yeast

**Example Usage:**
```
"Find orthologs for human TP53"
"What's the Drosophila ortholog of BRCA1?"
"Get DIOPT predictions for gene 7157"
```

**API Endpoint:** `GET /diopt/ortholog/gene/entrezId/:entrezId`

**Scoring:** DIOPT integrates multiple ortholog prediction tools and provides confidence scores.

---

### `get_diopt_alignment`

Get protein sequence alignments for orthologs.

**Parameters:**
- `entrez_id` (string, required): Human gene Entrez ID

**Returns:**
- Multiple sequence alignments
- Conservation patterns
- Protein domain information
- Aligned sequences across species

**Example Usage:**
```
"Show alignment for TP53 orthologs"
"Get protein alignment for gene 7157 across species"
```

**API Endpoint:** `GET /diopt/alignment/gene/entrezId/:entrezId`

---

## Expression Tools

### `get_gtex_expression`

Access GTEx (Genotype-Tissue Expression) data.

**Parameters:**
- `entrez_id` (string, required): Gene Entrez ID

**Returns:**
- Expression levels across human tissues
- Tissue-specific expression patterns
- Median TPM values
- Sample sizes
- Expression variability

**Example Usage:**
```
"Show GTEx expression for TP53"
"Where is BRCA1 most highly expressed?"
"Get tissue expression for gene 7157"
```

**API Endpoint:** `GET /gtex/gene/entrezId/:entrezId`

**Tissues Include:** Brain, heart, liver, kidney, lung, muscle, and 40+ other tissues.

---

### `get_ortholog_expression`

Get expression data for orthologs across model organisms.

**Parameters:**
- `entrez_id` (string, required): Human gene Entrez ID

**Returns:**
- Expression patterns in model organisms
- Developmental stage expression
- Tissue-specific expression in models
- Comparative expression data

**Example Usage:**
```
"Show expression of TP53 orthologs across species"
"Where is the mouse ortholog of BRCA1 expressed?"
```

**API Endpoint:** `GET /expression/orthologs/gene/entrezId/:entrezId`

---

### `get_pharos_targets`

Query Pharos for drug target information.

**Parameters:**
- `entrez_id` (string, required): Gene Entrez ID

**Returns:**
- Target development level (Tclin, Tchem, Tbio, Tdark)
- Known drugs/compounds
- Druggability assessment
- Clinical trial information
- Target class

**Example Usage:**
```
"Is TP53 a drug target?"
"Get druggability information for BRCA1"
"Show Pharos data for gene 7157"
```

**API Endpoint:** `GET /pharos/targets/gene/entrezId/:entrezId`

**Target Classes:**
- **Tclin**: Clinical target with approved drugs
- **Tchem**: Target with known chemical probes
- **Tbio**: Biological target with evidence
- **Tdark**: Understudied protein

---

## Utility Tools

### `validate_hgvs_variant`

Validate and parse HGVS variant nomenclature using Mutalyzer.

**Parameters:**
- `hgvs_variant` (string, required): Variant in HGVS format (e.g., "NM_000546.5:c.215C>G")

**Returns:**
- Validation status
- Parsed variant components
- Genomic coordinates
- Protein change
- Alternative descriptions

**Example Usage:**
```
"Validate variant NM_000546.5:c.215C>G"
"Is this HGVS nomenclature correct: NM_000059.3:c.68_69del?"
"Parse HGVS string for me"
```

**API Endpoint:** `GET /mutalyzer/hgvs/:variantHGVS`

**Supported Formats:**
- Genomic: `NC_000017.10:g.7577121C>T`
- Coding: `NM_000546.5:c.215C>G`
- Protein: `NP_000537.3:p.Arg72Pro`

---

### `convert_protein_variant`

Convert protein-level variants to genomic coordinates using Transvar.

**Parameters:**
- `protein_variant` (string, required): Protein variant (e.g., "ENSP00000269305:p.R248Q")

**Returns:**
- Genomic coordinates
- cDNA changes
- Multiple transcript mappings
- Alternative annotations

**Example Usage:**
```
"Convert protein variant p.R248Q to genomic coordinates"
"What's the genomic position of ENSP00000269305:p.R248Q?"
```

**API Endpoint:** `GET /transvar/protein/:proteinVariant`

---

## PubMed Literature Search Tools

### `search_pubmed`

Search PubMed for biomedical literature and retrieve article details.

This tool performs comprehensive PubMed searches for any biomedical query including gene names, variants, diseases, symptoms, drug names, or research topics. It returns PubMed IDs along with article metadata including titles, abstracts, authors, and publication information.

**Parameters:**
- `query` (string, required): Search query using any biomedical terms
  - Gene names: "TP53 cancer", "BRCA1 breast cancer"
  - Variants: "rs1042522", "R175H TP53"
  - Diseases: "Alzheimer's disease genetics"
  - Symptoms: "fever malaria treatment"
  - Drug names: "aspirin cardiovascular disease"
  - General: "CRISPR gene editing"
- `max_results` (integer, optional): Maximum number of results to return (default: 50, max: 100)
- `email` (string, optional): Email address for PubMed API identification (default: marrvel@example.com)

**Returns:**
- `query`: The search query used
- `total_results`: Total number of matches found in PubMed
- `returned_results`: Number of results in this response
- `max_results`: Maximum results requested
- `articles`: List of article objects, each containing:
  - `pubmed_id`: PubMed ID (PMID)
  - `title`: Article title
  - `abstract`: Article abstract (if available)
  - `authors`: List of author names
  - `journal`: Journal name
  - `publication_date`: Publication date
  - `doi`: Digital Object Identifier (if available)
  - `keywords`: Article keywords (if available)
  - `methods`: Methods section (if available)
  - `results`: Results section (if available)
  - `conclusions`: Conclusions section (if available)

**Example Usage:**
```
"Search PubMed for TP53 cancer therapy"
"Find recent publications about BRCA1 mutations"
"Look up Alzheimer's disease APOE literature"
"Search for COVID-19 vaccine studies"
```

**Example Response:**
```json
{
  "query": "TP53 cancer",
  "total_results": 45678,
  "returned_results": 10,
  "max_results": 10,
  "articles": [
    {
      "pubmed_id": "12345678",
      "title": "TP53 mutations in human cancers",
      "abstract": "The tumor suppressor gene TP53 is frequently mutated...",
      "authors": ["Smith J", "Doe A", "Johnson M"],
      "journal": "Nature",
      "publication_date": "2023-01-15",
      "doi": "10.1038/example",
      "keywords": ["TP53", "cancer", "tumor suppressor"],
      "methods": null,
      "results": null,
      "conclusions": null
    }
  ]
}
```

**Notes:**
- Results are limited to max_results for performance
- Not all articles have full abstracts available
- Some articles may have limited metadata
- Full text sections (methods, results, conclusions) availability depends on publisher

---

### `get_pubmed_article`

Retrieve detailed information for a specific PubMed article by PMID.

This tool fetches comprehensive details for a single PubMed article including title, abstract, authors, journal information, keywords, and publication metadata.

**Parameters:**
- `pubmed_id` (string, required): PubMed ID (PMID) as a string (e.g., "12345678")
- `email` (string, optional): Email address for PubMed API identification (default: marrvel@example.com)

**Returns:**
- `pubmed_id`: PubMed ID
- `title`: Article title
- `abstract`: Full abstract
- `authors`: List of authors
- `journal`: Journal name
- `publication_date`: Date of publication
- `doi`: Digital Object Identifier
- `keywords`: Article keywords
- `methods`: Methods section (if available)
- `results`: Results section (if available)
- `conclusions`: Conclusions section (if available)
- `copyrights`: Copyright information (if available)

**Example Usage:**
```
"Get details for PubMed article 32601318"
"Retrieve article information for PMID 28887537"
"Show me the abstract for PubMed ID 12345678"
```

**Example Response:**
```json
{
  "pubmed_id": "32601318",
  "title": "COVID-19 vaccine development",
  "abstract": "The rapid development of COVID-19 vaccines...",
  "authors": ["Johnson A", "Smith B", "Doe C"],
  "journal": "The Lancet",
  "publication_date": "2020-06-28",
  "doi": "10.1016/S0140-6736(20)31252-6",
  "keywords": ["COVID-19", "vaccine", "SARS-CoV-2"],
  "methods": "Study methodology details...",
  "results": "Results of the study...",
  "conclusions": "Conclusions drawn from the study...",
  "copyrights": "Copyright 2020 Elsevier Ltd."
}
```

**Notes:**
- Not all articles have all fields available
- Full text sections (methods, results, conclusions) may not be available for all articles depending on publisher restrictions
- If article is not found, returns an error message

**API Endpoint:** PubMed E-utilities API via pymed_paperscraper library

---

## Data Format Reference

### Variant Formats

**Standard Format:** `chromosome-position-reference-alternate`
- Example: `17-7577121-C-T`
- Coordinates: hg19/GRCh37

**HGVS Format:**
- Genomic: `NC_000017.10:g.7577121C>T`
- Coding: `NM_000546.5:c.215C>G`
- Protein: `NP_000537.3:p.Arg72Pro`

### Taxonomy IDs

| Species | Taxon ID |
|---------|----------|
| Human | 9606 |
| Mouse | 10090 |
| Rat | 10116 |
| Zebrafish | 7955 |
| Drosophila melanogaster | 7227 |
| C. elegans | 6239 |
| S. cerevisiae | 4932 |

### Chromosome Formats

- Include "chr" prefix: `chr17`, `chrX`, `chrM`
- Valid chromosomes: chr1-chr22, chrX, chrY, chrM

### Response Formats

All tools return JSON data structures. Common fields include:
- `status`: Response status
- `data`: Main response data
- `error`: Error message (if applicable)
- `metadata`: Additional information

---

## Error Handling

All tools handle errors gracefully and return descriptive messages:

- **404 Not Found**: Gene/variant not in database
- **400 Bad Request**: Invalid parameter format
- **500 Server Error**: MARRVEL API issues

Example error response:
```json
{
  "status": "error",
  "message": "Gene with Entrez ID 999999 not found",
  "error_code": "NOT_FOUND"
}
```

---

## Rate Limiting

Be mindful of API usage:
- Recommended: < 10 requests per second
- For bulk queries, add delays between requests
- Cache results when possible

---

## Additional Resources

- **MARRVEL Website:** https://marrvel.org
- **API Documentation:** https://marrvel.org/doc
- **Python Examples:** https://colab.research.google.com/drive/1Iierhoprr6JfUoX99FKu6xyb2Pr87aAf
- **Publication:** Wang J, et al. (2017) Am J Hum Genet 100(6):843-853

---

## Version History

- **v1.0.0** (2025-01-21): Initial release with all MARRVEL v2 API endpoints

---

For questions or issues, please refer to the main README.md or submit an issue on GitHub.
