# MARRVEL-MCP Tool Reference

Quick reference guide for all 30+ MCP tools in MARRVEL-MCP.

## Quick Lookup by Use Case

### "I want to..."

| Goal | Tool to Use | Example |
|------|-------------|---------|
| Get gene info by name | `get_gene_by_symbol` | `get_gene_by_symbol("TP53", "9606")` |
| Get gene info by ID | `get_gene_by_entrez_id` | `get_gene_by_entrez_id("7157")` |
| Find gene at position | `get_gene_by_position` | `get_gene_by_position("chr17", 7577121)` |
| Check variant pathogenicity | `get_clinvar_by_variant` | `get_clinvar_by_variant("17-7577121-C-T")` |
| Get variant frequency | `get_gnomad_variant` | `get_gnomad_variant("17-7577121-C-T")` |
| Predict variant impact | `get_variant_dbnsfp` | `get_variant_dbnsfp("17-7577121-C-T")` |
| Find disease associations | `get_omim_by_gene_symbol` | `get_omim_by_gene_symbol("TP53")` |
| Find orthologs | `get_diopt_orthologs` | `get_diopt_orthologs("7157")` |
| Check gene expression | `get_gtex_expression` | `get_gtex_expression("7157")` |
| Assess druggability | `get_pharos_targets` | `get_pharos_targets("7157")` |

## Tool Categories

### 🧬 Gene Tools

| Tool | Input | Returns | Use When |
|------|-------|---------|----------|
| `get_gene_by_entrez_id` | Entrez ID | Gene details | You have NCBI gene ID |
| `get_gene_by_symbol` | Symbol + Taxon | Gene details | You have gene name |
| `get_gene_by_position` | Chr + Position | Gene at location | You have coordinates |

### 🔬 Variant Analysis Tools

#### Core Variant Tools
| Tool | Input | Database | Primary Info |
|------|-------|----------|--------------|
| `get_variant_dbnsfp` | Variant | dbNSFP | Functional predictions |
| `get_clinvar_by_variant` | Variant | ClinVar | Clinical significance |
| `get_gnomad_variant` | Variant | gnomAD | Population frequency |

#### Gene-Level Variant Tools
| Tool | Input | Database | Returns |
|------|-------|----------|---------|
| `get_clinvar_by_gene_symbol` | Symbol | ClinVar | All variants in gene |
| `get_clinvar_by_entrez_id` | Entrez ID | ClinVar | All variants in gene |
| `get_gnomad_by_gene_symbol` | Symbol | gnomAD | All variants in gene |
| `get_gnomad_by_entrez_id` | Entrez ID | gnomAD | All variants in gene |

#### Structural Variant Tools
| Tool | Input | Database | Focus |
|------|-------|----------|-------|
| `get_dgv_variant` | Variant | DGV | Common SVs |
| `get_dgv_by_entrez_id` | Entrez ID | DGV | Gene region SVs |
| `get_decipher_variant` | Variant | DECIPHER | Rare disease SVs |
| `get_decipher_by_location` | Chr + Range | DECIPHER | Region SVs |

#### Phenotype Tools
| Tool | Input | Database | Focus |
|------|-------|----------|-------|
| `get_geno2mp_variant` | Variant | Geno2MP | HPO phenotypes |
| `get_geno2mp_by_entrez_id` | Entrez ID | Geno2MP | Gene phenotypes |

### 🏥 Disease Tools (OMIM)

| Tool | Input | Returns | Best For |
|------|-------|---------|----------|
| `get_omim_by_mim_number` | MIM number | Disease entry | Known MIM ID |
| `get_omim_by_gene_symbol` | Gene symbol | All diseases | Gene-disease links |
| `get_omim_variant` | Gene + Variant | Variant diseases | Specific variant |

### 🐭 Ortholog Tools (DIOPT)

| Tool | Input | Returns | Use Case |
|------|-------|---------|----------|
| `get_diopt_orthologs` | Entrez ID | Ortholog list | Find model organisms |
| `get_diopt_alignment` | Entrez ID | Protein alignment | Check conservation |

### 📊 Expression Tools

| Tool | Input | Database | Data Type |
|------|-------|----------|-----------|
| `get_gtex_expression` | Entrez ID | GTEx | Human tissue TPM |
| `get_ortholog_expression` | Entrez ID | Multiple | Model organism expr. |
| `get_pharos_targets` | Entrez ID | Pharos | Drug target level |

### 🔧 Utility Tools

| Tool | Input | Output | Purpose |
|------|-------|--------|---------|
| `validate_hgvs_variant` | HGVS string | Validation + coords | Check nomenclature |
| `convert_protein_variant` | Protein var. | Genomic coords | Convert formats |

## Common Workflows

### Comprehensive Gene Analysis
```
1. get_gene_by_entrez_id("7157")
2. get_omim_by_gene_symbol("TP53")
3. get_clinvar_by_entrez_id("7157")
4. get_gtex_expression("7157")
5. get_diopt_orthologs("7157")
6. get_pharos_targets("7157")
```

### Complete Variant Assessment
```
1. get_variant_dbnsfp("17-7577121-C-T")
2. get_clinvar_by_variant("17-7577121-C-T")
3. get_gnomad_variant("17-7577121-C-T")
4. get_geno2mp_variant("17-7577121-C-T")
```

### Cross-Species Research
```
1. get_gene_by_symbol("TP53", "9606")  # Human
2. get_diopt_orthologs("7157")         # Find orthologs
3. get_diopt_alignment("7157")         # Check conservation
4. get_ortholog_expression("7157")     # Compare expression
```

### Disease Investigation
```
1. get_omim_by_gene_symbol("BRCA1")
2. get_clinvar_by_gene_symbol("BRCA1")
3. get_geno2mp_by_entrez_id("672")
4. get_gtex_expression("672")
```

## Format Reference

### Variant Formats
- **Standard**: `"17-7577121-C-T"` (chr-pos-ref-alt)
- **Chromosome**: Include "chr" prefix (`"chr17"`)
- **Coordinates**: hg19/GRCh37

### Species Taxonomy IDs
- Human: `"9606"`
- Mouse: `"10090"`
- Rat: `"10116"`
- Zebrafish: `"7955"`
- Drosophila: `"7227"`
- C. elegans: `"6239"`
- Yeast: `"4932"`

### HGVS Formats
- Genomic: `"NC_000017.10:g.7577121C>T"`
- Coding: `"NM_000546.5:c.215C>G"`
- Protein: `"NP_000537.3:p.Arg72Pro"`

## Return Data Summary

| Tool Category | Returns | Format |
|---------------|---------|--------|
| Gene | Symbol, name, location, summary | JSON string |
| Variant | Predictions, frequency, significance | JSON string |
| Disease | Phenotypes, inheritance, clinical | JSON string |
| Ortholog | Species, genes, scores | JSON string |
| Expression | TPM values, tissues | JSON string |
| Utility | Validation, coordinates | JSON string |

## Error Messages

| Error | Meaning | Solution |
|-------|---------|----------|
| "Gene not found" | Invalid ID/symbol | Check spelling, try Entrez ID |
| "Variant not found" | No data for variant | Verify format, try different DB |
| "Invalid chromosome" | Bad chr format | Use chr1-22, chrX, chrY, chrM |
| "API timeout" | Request too slow | Retry, check connection |
| "Invalid format" | Wrong input format | Check documentation examples |

## Tips for Effective Use

1. **Start with Gene Lookup**: Get Entrez ID first for most reliable queries
2. **Use Multiple Sources**: Cross-reference ClinVar, gnomAD, dbNSFP for variants
3. **Check Coordinates**: MARRVEL uses hg19 (convert hg38 if needed)
4. **Verify Symbols**: Gene symbols are case-sensitive
5. **Use Taxonomy IDs**: Always specify species for cross-species work

## API Endpoint Summary

All endpoints use base URL: `http://api.marrvel.org/data`

| Category | Endpoints | Count |
|----------|-----------|-------|
| Gene | `/gene/*` | 3 |
| Variant | `/dbnsfp/*, /clinvar/*, /gnomad/*, /dgv/*, /decipher/*, /geno2mp/*` | 13 |
| Disease | `/omim/*` | 3 |
| Ortholog | `/diopt/*` | 2 |
| Expression | `/gtex/*, /expression/*, /pharos/*` | 3 |
| Utility | `/mutalyzer/*, /transvar/*` | 2 |

**Total: 26 unique endpoints, 30+ tools**

---

For detailed documentation, see [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
