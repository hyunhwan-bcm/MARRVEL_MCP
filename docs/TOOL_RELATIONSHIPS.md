# MARRVEL MCP Tools - Relationship Graph

This diagram shows the natural flow and chaining relationships between MARRVEL MCP tools based on their inputs and outputs.

```mermaid
---
config:
  layout: elk
---
flowchart LR
    User@{ label: "<b><font size=\"6\">LLM</font></b>" } --> Input1@{ label: "<b><font size=\"5\">Gene Symbol</font></b>" } & Input2@{ label: "<b><font size=\"5\">Genomic Position</font></b>" } & Input3@{ label: "<b><font size=\"5\">Variant Notation</font></b><br>(HGVS/rsID/Protein)" } & Input4@{ label: "<b><font size=\"5\">Disease/Phenotype</font></b>" } & Input5@{ label: "<b><font size=\"5\">Literature ID</font></b><br>(PMID/PMCID)" } & Input6@{ label: "<b><font size=\"5\">Ensembl ID</font></b>" }
    Input1 --> GeneTools@{ label: "<b><font size=\"4\">Gene Information</font></b><br>get_gene_by_symbol, get_gene_by_entrez_id,<br>get_gene_by_position, get_gene_by_ensembl_id" } & LiteratureTools@{ label: "<b><font size=\"4\">Literature Search</font></b><br>search_pubmed, get_pubmed_article,<br>pmid_to_pmcid, get_pmc_abstract_by_pmcid,<br>get_pmc_fulltext_by_pmcid,<br>get_pmc_tables_by_pmcid,<br>get_pmc_figure_captions_by_pmcid" }
    Input2 --> GeneTools & VariantAnnotation@{ label: "<b><font size=\"4\">Variant Annotation</font></b><br>get_variant_dbnsfp, get_clinvar_by_variant,<br>get_gnomad_variant,<br>get_protein_change_by_genomic_position,<br>get_geno2mp_by_variant" }
    Input4 --> GeneTools & DiseaseTools@{ label: "<b><font size=\"4\">Disease Association</font></b><br>get_omim_by_gene_symbol,<br>get_omim_by_mim_number,<br>get_omim_variant,<br>search_omim_by_disease_name,<br>search_hpo_terms,<br>get_hpo_associated_genes" } & LiteratureTools
    Input3 --> VariantConversion@{ label: "<b><font size=\"4\">Variant Conversion</font></b><br>convert_hgvs_to_genomic,<br>convert_protein_variant,<br>convert_rsid_to_variant" } & LiteratureTools
    Input6 --> GeneTools
    VariantConversion --> VariantAnnotation
    GeneTools --> GeneVariants@{ label: "<b><font size=\"4\">Gene-Level Variants</font></b><br>get_clinvar_counts_by_entrez_id,<br>get_gnomad_by_entrez_id,<br>get_dgv_by_entrez_id,<br>get_decipher_by_location,<br>get_geno2mp_by_entrez_id" } & DiseaseTools & OrthologTools@{ label: "<b><font size=\"4\">Ortholog Analysis</font></b><br>get_diopt_orthologs_by_entrez_id,<br>get_ontology_across_diopt_orthologs,<br>get_diopt_alignment,<br>get_ortholog_expression" } & ExpressionTools@{ label: "<b><font size=\"4\">Expression &amp; Function</font></b><br>get_gtex_expression, get_pharos_targets,<br>get_string_interactions_by_entrez_id,<br>get_string_interactions_between_entrez_ids" } & GOTools@{ label: "<b><font size=\"4\">Gene Ontology</font></b><br>get_go_by_entrez_id" } & LiteratureTools
    Input5 --> LiteratureTools
    VariantAnnotation --> Results1@{ label: "<b><font size=\"4\">Variant Pathogenicity<br>&amp; Frequencies</font></b>" }
    GeneVariants --> Results2@{ label: "<b><font size=\"4\">Gene-Level<br>Variant Burden</font></b>" }
    DiseaseTools --> Results3@{ label: "<b><font size=\"4\">Disease Associations<br>&amp; Phenotypes</font></b>" }
    OrthologTools --> Results4@{ label: "<b><font size=\"4\">Comparative Genomics<br>Across Species</font></b>" }
    ExpressionTools --> Results5@{ label: "<b><font size=\"4\">Expression Patterns<br>&amp; Drug Targets</font></b>" }
    LiteratureTools --> Results6@{ label: "<b><font size=\"4\">Literature Evidence<br>&amp; Supporting Data</font></b>" }
    GOTools --> Results7@{ label: "<b><font size=\"4\">Functional<br>Annotations</font></b>" }
    Results1 --> FinalReport@{ label: "<b><font size=\"5\">Comprehensive<br>Rare Disease<br>Analysis</font></b>" }
    Results2 --> FinalReport
    Results3 --> FinalReport
    Results4 --> FinalReport
    Results5 --> FinalReport
    Results6 --> FinalReport
    Results7 --> FinalReport
    LiftoverTools@{ label: "<b><font size=\"4\">Coordinate Liftover</font></b><br>liftover_hg19_to_hg38,<br>liftover_hg38_to_hg19" }
    VariantConversion -.->|"internally uses"| LiftoverTools
    VariantAnnotation -.->|"internally uses"| LiftoverTools
    DiseaseTools -.->|"internally uses"| LiftoverTools
    GeneTools -.->|"internally uses"| LiftoverTools
    DocTools@{ label: "<b><font size=\"4\">Documentation</font></b><br>get_dataset_docs,<br>get_dbnsfp_docs,<br>get_gnomad_docs" }
    User -.->|"reference"| DocTools
    User@{ shape: terminal}
    Input1@{ shape: lean-r}
    Input2@{ shape: lean-r}
    Input3@{ shape: lean-r}
    Input4@{ shape: lean-r}
    Input5@{ shape: lean-r}
    Input6@{ shape: lean-r}
    GeneTools@{ shape: rect}
    LiteratureTools@{ shape: rect}
    VariantAnnotation@{ shape: rect}
    DiseaseTools@{ shape: rect}
    VariantConversion@{ shape: rect}
    GeneVariants@{ shape: rect}
    OrthologTools@{ shape: rect}
    ExpressionTools@{ shape: rect}
    GOTools@{ shape: rect}
    LiftoverTools@{ shape: rect}
    DocTools@{ shape: rect}
    Results1@{ shape: hexagon}
    Results2@{ shape: hexagon}
    Results3@{ shape: hexagon}
    Results4@{ shape: hexagon}
    Results5@{ shape: hexagon}
    Results6@{ shape: hexagon}
    Results7@{ shape: hexagon}
    FinalReport@{ shape: rect}
     User:::userNode
     Input1:::inputNode
     Input2:::inputNode
     Input3:::inputNode
     Input4:::inputNode
     Input5:::inputNode
     Input6:::inputNode
     GeneTools:::toolCategory
     LiteratureTools:::toolCategory
     VariantAnnotation:::toolCategory
     DiseaseTools:::toolCategory
     VariantConversion:::toolCategory
     GeneVariants:::toolCategory
     OrthologTools:::toolCategory
     ExpressionTools:::toolCategory
     GOTools:::toolCategory
     LiftoverTools:::utilityNode
     DocTools:::docNode
     Results1:::resultNode
     Results2:::resultNode
     Results3:::resultNode
     Results4:::resultNode
     Results5:::resultNode
     Results6:::resultNode
     Results7:::resultNode
     FinalReport:::finalNode
    classDef inputNode fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef toolCategory fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef resultNode fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef finalNode fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    classDef userNode fill:#fffde7,stroke:#fbc02d,stroke-width:3px
    classDef utilityNode fill:#e0f2f1,stroke:#00897b,stroke-width:2px,stroke-dasharray: 5 5
    classDef docNode fill:#fce4ec,stroke:#c62828,stroke-width:2px,stroke-dasharray: 5 5

```

## Common Tool Chains

### Chain 1: Gene Symbol → Full Gene Analysis

```text
gene_symbol → get_gene_by_symbol → entrez_id
  → get_diopt_orthologs_by_entrez_id (comparative genomics)
  → get_gtex_expression (tissue expression)
  → get_clinvar_counts_by_entrez_id (variant burden)
  → get_string_interactions_by_entrez_id (protein network)
  → get_pharos_targets (drug targets)
  → get_go_by_entrez_id (gene ontology)
```

### Chain 2: Variant Analysis Pipeline

```text
HGVS variant → convert_hgvs_to_genomic → (chr, pos, ref, alt)
  → get_variant_dbnsfp (CADD, conservation scores)
  → get_clinvar_by_variant (clinical significance)
  → get_gnomad_variant (population frequency)
  → get_protein_change_by_genomic_position (protein change / VEP annotations)
  → get_geno2mp_by_variant (genotype-phenotype associations)
```

### Chain 3: Disease → Gene → Variant Discovery

```text
disease_name → search_omim_by_disease_name → gene_symbol
  → get_gene_by_symbol → entrez_id
  → get_clinvar_counts_by_entrez_id → variant list
  → get_clinvar_by_variant (for each variant)
```

### Chain 4: Phenotype → Gene Discovery

```text
phenotype_query → search_hpo_terms → hpo_id
  → get_hpo_associated_genes → gene list
  → get_gene_by_entrez_id (for each gene)
```

### Chain 5: Literature Deep Dive

```text
gene_symbol → search_pubmed → pmid list
  → get_pubmed_article (metadata + abstract)
  → pmid_to_pmcid → pmcid
  → get_pmc_abstract_by_pmcid (quick summary)
  → get_pmc_fulltext_by_pmcid (full text)
  → get_pmc_tables_by_pmcid (supplementary data)
  → get_pmc_figure_captions_by_pmcid (figures)
```

### Chain 6: Comparative Genomics Workflow

```text
entrez_id → get_diopt_orthologs_by_entrez_id → ortholog list
  → get_ontology_across_diopt_orthologs (for model organism)
  → get_diopt_alignment (sequence alignment)
  → get_ortholog_expression (cross-species expression)
```

### Chain 7: rsID → Clinical Interpretation

```text
rsid → convert_rsid_to_variant → (chr, pos, ref, alt)
  → get_variant_dbnsfp (pathogenicity scores)
  → get_clinvar_by_variant (clinical classification)
  → get_gnomad_variant (allele frequency)
  → get_omim_variant (disease association)
```

### Chain 8: Ensembl ID → Gene Analysis

```text
ensembl_id → get_gene_by_ensembl_id → entrez_id
  → (continues as Chain 1 from entrez_id)
```

### Chain 9: Protein-Level Variant → Genomic Annotation

```text
gene_symbol + protein_variant → convert_protein_variant → (chr, pos, ref, alt)
  → get_variant_dbnsfp (pathogenicity scores)
  → get_clinvar_by_variant (clinical significance)
  → get_protein_change_by_genomic_position (transcript-level annotation)
```

### Chain 10: Pairwise Protein Interaction Analysis

```text
gene_symbol_1 → get_gene_by_symbol → entrez_id_1
gene_symbol_2 → get_gene_by_symbol → entrez_id_2
  → get_string_interactions_between_entrez_ids (pairwise interactions)
```

## Utility Tools

### Coordinate Liftover

Several tools internally convert between genome builds. The liftover tools are also available directly:

```text
hg38 coordinates → liftover_hg38_to_hg19 → hg19 coordinates
hg19 coordinates → liftover_hg19_to_hg38 → hg38 coordinates
```

Tools that internally use liftover:
- `convert_hgvs_to_genomic` (hg19 → hg38)
- `convert_protein_variant` (hg19 → hg38)
- `get_protein_change_by_genomic_position` (hg38 → hg19)
- `get_omim_variant` (hg38 → hg19)
- `get_geno2mp_by_variant` (hg38 → hg19)
- `get_decipher_by_location` (hg38 → hg19)
- `fix_missing_hg38_vals` in gene tools (hg19 → hg38)

### Documentation Tools

Reference tools for understanding available datasets and score definitions:

```text
get_dataset_docs → descriptions of all MARRVEL datasets
get_dbnsfp_docs → descriptions of all dbNSFP prediction methods and scores
get_gnomad_docs → descriptions of gnomAD gene constraint metrics
```

## Key Decision Points

### After getting Gene Info

- **Clinical Focus**: → ClinVar, OMIM, HPO
- **Population Genetics**: → gnomAD, DGV
- **Functional**: → GTEx, DIOPT, STRING, GO
- **Therapeutic**: → Pharos (drug targets)

### After getting Variant Position

- **Pathogenicity**: → dbNSFP (computational predictions)
- **Clinical Evidence**: → ClinVar (expert curation)
- **Frequency**: → gnomAD (population data)
- **Disease Context**: → OMIM variant (disease association)
- **Phenotype Correlation**: → Geno2MP (genotype-phenotype)
- **Protein Impact**: → get_protein_change_by_genomic_position (protein change)

### After getting PMID/PMCID

- **Quick Summary**: → get_pmc_abstract_by_pmcid
- **Deep Analysis**: → get_pmc_fulltext_by_pmcid
- **Data Mining**: → get_pmc_tables_by_pmcid + get_pmc_figure_captions_by_pmcid

## Complete Tool Inventory

| Category | Tool | Description |
|---|---|---|
| **Meta** | `get_dataset_docs` | Descriptions of all MARRVEL datasets |
| **Meta** | `get_dbnsfp_docs` | Descriptions of dbNSFP prediction methods |
| **Meta** | `get_gnomad_docs` | Descriptions of gnomAD constraint metrics |
| **Gene** | `get_gene_by_symbol` | Gene info by symbol |
| **Gene** | `get_gene_by_entrez_id` | Gene info by Entrez ID |
| **Gene** | `get_gene_by_ensembl_id` | Gene info by Ensembl ID |
| **Gene** | `get_gene_by_position` | Gene info by genomic position (hg38) |
| **Variant** | `get_variant_dbnsfp` | Pathogenicity predictions (dbNSFP) |
| **Variant** | `get_clinvar_by_variant` | ClinVar clinical significance |
| **Variant** | `get_clinvar_counts_by_entrez_id` | ClinVar variant counts by gene |
| **Variant** | `get_gnomad_variant` | gnomAD population frequencies |
| **Variant** | `get_gnomad_by_entrez_id` | gnomAD gene-level data |
| **Variant** | `get_dgv_by_entrez_id` | DGV structural variants |
| **Variant** | `get_geno2mp_by_entrez_id` | Geno2MP gene-level HPO counts |
| **Variant** | `get_geno2mp_by_variant` | Geno2MP variant-level HPO terms |
| **Variant** | `get_decipher_by_location` | DECIPHER control variant stats |
| **Disease** | `get_omim_by_mim_number` | OMIM entry by MIM number |
| **Disease** | `get_omim_by_gene_symbol` | OMIM diseases by gene |
| **Disease** | `get_omim_variant` | OMIM variant disease association |
| **Disease** | `search_omim_by_disease_name` | OMIM search by disease name |
| **Disease** | `search_hpo_terms` | HPO term search |
| **Disease** | `get_hpo_associated_genes` | Genes for an HPO term |
| **Disease** | `get_go_by_entrez_id` | Gene Ontology terms |
| **Ortholog** | `get_diopt_orthologs_by_entrez_id` | Ortholog predictions |
| **Ortholog** | `get_ontology_across_diopt_orthologs` | GO terms across orthologs |
| **Ortholog** | `get_diopt_alignment` | Protein domain alignment |
| **Expression** | `get_gtex_expression` | GTEx tissue expression |
| **Expression** | `get_ortholog_expression` | Cross-species expression |
| **Expression** | `get_pharos_targets` | Drug target info |
| **Expression** | `get_string_interactions_by_entrez_id` | STRING protein interactions |
| **Expression** | `get_string_interactions_between_entrez_ids` | STRING pairwise interactions |
| **Utility** | `convert_hgvs_to_genomic` | HGVS → genomic coordinates |
| **Utility** | `convert_protein_variant` | Protein variant → genomic coordinates |
| **Utility** | `get_protein_change_by_genomic_position` | Genomic position → protein change |
| **Utility** | `convert_rsid_to_variant` | rsID → variant coordinates |
| **Utility** | `liftover_hg19_to_hg38` | hg19 → hg38 coordinate conversion |
| **Utility** | `liftover_hg38_to_hg19` | hg38 → hg19 coordinate conversion |
| **Literature** | `search_pubmed` | PubMed literature search |
| **Literature** | `get_pubmed_article` | PubMed article details |
| **Literature** | `pmid_to_pmcid` | PMID → PMCID conversion |
| **Literature** | `get_pmc_abstract_by_pmcid` | PMC abstract retrieval |
| **Literature** | `get_pmc_fulltext_by_pmcid` | PMC full text retrieval |
| **Literature** | `get_pmc_tables_by_pmcid` | PMC table extraction |
| **Literature** | `get_pmc_figure_captions_by_pmcid` | PMC figure captions |
