# Changelog

All notable changes to MARRVEL-MCP will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-21

### Added
- Initial release of MARRVEL-MCP server
- 30+ MCP tools covering all MARRVEL v2 API endpoints
- Comprehensive API documentation
- Example queries and usage patterns
- Unit test framework
- Quick start guide

### Features

#### Gene Tools
- `get_gene_by_entrez_id`: Query genes by Entrez ID
- `get_gene_by_symbol`: Query genes by symbol and species
- `get_gene_by_position`: Find genes by chromosomal position

#### Variant Analysis Tools
- `get_variant_dbnsfp`: dbNSFP functional predictions
- `get_clinvar_by_variant`: ClinVar clinical significance
- `get_clinvar_by_gene_symbol`: All ClinVar variants for a gene
- `get_clinvar_by_entrez_id`: ClinVar variants by Entrez ID
- `get_gnomad_variant`: gnomAD population frequencies
- `get_gnomad_by_gene_symbol`: gnomAD data by gene symbol
- `get_gnomad_by_entrez_id`: gnomAD data by Entrez ID
- `get_dgv_variant`: DGV structural variants
- `get_dgv_by_entrez_id`: DGV data by gene
- `get_decipher_variant`: DECIPHER developmental disorder data
- `get_decipher_by_location`: DECIPHER data by genomic region
- `get_geno2mp_variant`: Geno2MP genotype-phenotype associations
- `get_geno2mp_by_entrez_id`: Geno2MP data by gene

#### Disease Tools (OMIM)
- `get_omim_by_mim_number`: OMIM entries by MIM number
- `get_omim_by_gene_symbol`: Disease associations for a gene
- `get_omim_variant`: Variant-specific OMIM information

#### Ortholog Tools (DIOPT)
- `get_diopt_orthologs`: Find orthologs across species
- `get_diopt_alignment`: Protein sequence alignments

#### Expression Tools
- `get_gtex_expression`: GTEx tissue expression data
- `get_ortholog_expression`: Expression in model organisms
- `get_pharos_targets`: Drug target information

#### Utility Tools
- `validate_hgvs_variant`: Validate HGVS nomenclature
- `convert_protein_variant`: Convert protein to genomic coordinates

### Documentation
- Comprehensive README.md with installation and usage
- API_DOCUMENTATION.md with detailed tool documentation
- QUICKSTART.md for quick setup
- examples/example_queries.py with 20+ usage examples

### Testing
- Basic test framework in tests/test_server.py
- Integration test markers for API testing

### Dependencies
- FastMCP >= 0.3.0
- httpx >= 0.27.0

## [Unreleased]

### Planned Features
- Response caching for improved performance
- Batch query support
- Additional error handling and validation
- Support for hg38 coordinates
- Enhanced variant annotation combining multiple sources
- GraphQL support for complex queries

### Known Issues
- None at this time

### Future Enhancements
- Add support for VCF file parsing
- Include variant effect prediction aggregation
- Add support for gene set enrichment analysis
- Integration with additional databases
- Web interface for server management
- Performance optimization for bulk queries

---

## Version History

- **1.0.0** (2025-01-21): Initial public release

---

For upgrade instructions and breaking changes, see [README.md](README.md).
