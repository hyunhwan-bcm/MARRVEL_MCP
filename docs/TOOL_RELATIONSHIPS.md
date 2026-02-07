# MARRVEL MCP Tools - Relationship Graph

This diagram shows the natural flow and chaining relationships between MARRVEL MCP tools based on their inputs and outputs.

```mermaid
---
config:
  layout: elk
---
flowchart LR
    User@{ label: "<b><font size=\"6\">LLM</font></b>" } --> Input1@{ label: "<b><font size=\"5\">Gene Symbol</font></b>" } & Input2@{ label: "<b><font size=\"5\">Genomic Position</font></b>" } & Input3@{ label: "<b><font size=\"5\">Variant Notation</font></b><br>(HGVS/rsID/Protein)" } & Input4@{ label: "<b><font size=\"5\">Disease/Phenotype</font></b>" } & Input5@{ label: "<b><font size=\"5\">Literature ID</font></b><br>(PMID/PMCID)" }
    Input1 --> GeneTools@{ label: "<b><font size=\"4\">Gene Information</font></b><br>get_gene_by_symbol, get_gene_by_entrez_id, get_gene_by_position" } & LiteratureTools@{ label: "<b><font size=\"4\">Literature Search</font></b><br>search_pubmed, get_pubmed_article, pmid_to_pmcid, get_pmc_fulltext_by_pmcid, get_pmc_tables_by_pmcid" }
    Input2 --> GeneTools & VariantAnnotation@{ label: "<b><font size=\"4\">Variant Annotation</font></b><br>get_variant_dbnsfp, get_clinvar_by_variant, get_gnomad_variant, get_variant_annotation_by_genomic_position" }
    Input4 --> GeneTools & DiseaseTools@{ label: "<b><font size=\"4\">Disease Association</font></b><br>get_omim_by_gene_symbol, get_omim_by_mim_number, search_omim_by_disease_name, search_hpo_terms, get_hpo_associated_genes" } & LiteratureTools
    Input3 --> VariantConversion@{ label: "<b><font size=\"4\">Variant Conversion</font></b><br>convert_hgvs_to_genomic, convert_protein_variant, convert_rsid_to_variant" } & LiteratureTools
    VariantConversion --> VariantAnnotation
    GeneTools --> GeneVariants@{ label: "<b><font size=\"4\">Gene-Level Variants</font></b><br>get_clinvar_counts_by_entrez_id, get_gnomad_by_entrez_id, get_dgv_by_entrez_id, get_decipher_by_location, get_geno2mp_by_entrez_id" } & DiseaseTools & OrthologTools@{ label: "<b><font size=\"4\">Ortholog Analysis</font></b><br>get_diopt_orthologs_by_entrez_id, get_ontology_across_diopt_orthologs, get_diopt_alignment, get_ortholog_expression" } & ExpressionTools@{ label: "<b><font size=\"4\">Expression &amp; Function</font></b><br>get_gtex_expression, get_pharos_targets, get_string_interactions_by_entrez_id" } & LiteratureTools
    Input5 --> LiteratureTools
    VariantAnnotation --> Results1@{ label: "<b><font size=\"4\">Variant Pathogenicity<br>&amp; Frequencies</font></b>" }
    GeneVariants --> Results2@{ label: "<b><font size=\"4\">Gene-Level<br>Variant Burden</font></b>" }
    DiseaseTools --> Results3@{ label: "<b><font size=\"4\">Disease Associations<br>&amp; Phenotypes</font></b>" }
    OrthologTools --> Results4@{ label: "<b><font size=\"4\">Comparative Genomics<br>Across Species</font></b>" }
    ExpressionTools --> Results5@{ label: "<b><font size=\"4\">Expression Patterns<br>&amp; Drug Targets</font></b>" }
    LiteratureTools --> Results6@{ label: "<b><font size=\"4\">Literature Evidence<br>&amp; Supporting Data</font></b>" }
    Results1 --> FinalReport@{ label: "<b><font size=\"5\">Comprehensive<br>Rare Disease<br>Analysis</font></b>" }
    Results2 --> FinalReport
    Results3 --> FinalReport
    Results4 --> FinalReport
    Results5 --> FinalReport
    Results6 --> FinalReport
    User@{ shape: terminal}
    Input1@{ shape: lean-r}
    Input2@{ shape: lean-r}
    Input3@{ shape: lean-r}
    Input4@{ shape: lean-r}
    Input5@{ shape: lean-r}
    GeneTools@{ shape: rect}
    LiteratureTools@{ shape: rect}
    VariantAnnotation@{ shape: rect}
    DiseaseTools@{ shape: rect}
    VariantConversion@{ shape: rect}
    GeneVariants@{ shape: rect}
    OrthologTools@{ shape: rect}
    ExpressionTools@{ shape: rect}
    Results1@{ shape: hexagon}
    Results2@{ shape: hexagon}
    Results3@{ shape: hexagon}
    Results4@{ shape: hexagon}
    Results5@{ shape: hexagon}
    Results6@{ shape: hexagon}
    FinalReport@{ shape: rect}
     User:::userNode
     Input1:::inputNode
     Input2:::inputNode
     Input3:::inputNode
     Input4:::inputNode
     Input5:::inputNode
     GeneTools:::toolCategory
     LiteratureTools:::toolCategory
     VariantAnnotation:::toolCategory
     DiseaseTools:::toolCategory
     VariantConversion:::toolCategory
     GeneVariants:::toolCategory
     OrthologTools:::toolCategory
     ExpressionTools:::toolCategory
     Results1:::resultNode
     Results2:::resultNode
     Results3:::resultNode
     Results4:::resultNode
     Results5:::resultNode
     Results6:::resultNode
     FinalReport:::finalNode
    classDef inputNode fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef toolCategory fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef resultNode fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef finalNode fill:#e8f5e9,stroke:#388e3c,stroke-width:3px
    classDef userNode fill:#fffde7,stroke:#fbc02d,stroke-width:3px

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
```

### Chain 2: Variant Analysis Pipeline

```text
HGVS variant → convert_hgvs_to_genomic → (chr, pos, ref, alt)
  → get_variant_dbnsfp (CADD, conservation scores)
  → get_clinvar_by_variant (clinical significance)
  → get_gnomad_variant (population frequency)
  → get_variant_annotation_by_genomic_position (VEP annotations)
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
  → pmid_to_pmcid → pmcid
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

## Key Decision Points

### After getting Gene Info

- **Clinical Focus**: → ClinVar, OMIM, HPO
- **Population Genetics**: → gnomAD, DGV
- **Functional**: → GTEx, DIOPT, STRING
- **Therapeutic**: → Pharos (drug targets)

### After getting Variant Position

- **Pathogenicity**: → dbNSFP (computational predictions)
- **Clinical Evidence**: → ClinVar (expert curation)
- **Frequency**: → gnomAD (population data)
- **Context**: → OMIM (disease association)

### After getting PMID/PMCID

- **Quick Summary**: → get_pmc_abstract
- **Deep Analysis**: → get_pmc_fulltext
- **Data Mining**: → get_pmc_tables + get_pmc_figure_captions
