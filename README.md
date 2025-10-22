# MARRVEL-MCP

[![CI](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/ci.yml)
[![Pre-commit](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/pre-commit.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Model Context Protocol (MCP) server for [MARRVEL](https://marrvel.org) (Model organism Aggregated Resources for Rare Variant ExpLoration) genetics research platform.

## Overview

MARRVEL-MCP provides AI agents with seamless access to comprehensive genetics databases and variant analysis tools through the MCP protocol. This server enables researchers and AI assistants to query gene information, variant data, disease associations, and ortholog information programmatically.

## Features

- **Gene Information**: Query genes by Entrez ID, symbol, or chromosomal position
- **Variant Analysis**: Access variant annotations from dbNSFP, ClinVar, gnomAD
- **Disease Data**: Retrieve OMIM disease associations
- **Ortholog Information**: Find orthologs across species using DIOPT
- **Expression Data**: Access GTEx and model organism expression data
- **Clinical Variants**: Query ClinVar for clinical significance
- **Structural Variants**: Access DGV and DECIPHER data
- **Drug Targets**: Query Pharos for druggability information
- **Variant Nomenclature**: Validate and convert variant formats

## Installation

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone https://github.com/hyunhwan-bcm/MARRVEL_MCP.git
cd MARRVEL_MCP
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure the MCP server in your Claude Desktop or other MCP client configuration file.

For Claude Desktop, add to your configuration file:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "marrvel": {
      "command": "python",
      "args": ["/path/to/MARRVEL_MCP/server.py"]
    }
  }
}
```

## Usage

Once configured, you can interact with MARRVEL through your AI assistant. Here are some example queries:

### Gene Queries

```
"Get information about the gene TP53"
"Find the gene at chromosome 17 position 7577121"
"What is the function of BRCA1?"
```

### Variant Queries

```
"Look up variant chr17:g.7577121C>T in ClinVar"
"Get gnomAD frequency for variant 17-7577121-C-T"
"What is the clinical significance of NM_000546.5:c.215C>G?"
```

### Disease and Phenotype

```
"Find OMIM diseases associated with TP53"
"Get phenotype data for Entrez ID 7157"
```

### Ortholog Information

```
"Find orthologs for human TP53 across model organisms"
"Show me the DIOPT alignment for gene 7157"
```

### Expression Data

```
"Get GTEx expression data for BRCA1"
"Show expression patterns for orthologs of gene 7157"
```

## Available Tools

See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md) for comprehensive details on all available tools.

### Core Categories

1. **Gene Tools** (3 tools)
   - `get_gene_by_entrez_id`
   - `get_gene_by_symbol`
   - `get_gene_by_position`

2. **Variant Tools** (6 tools)
   - `get_variant_dbnsfp`
   - `get_variant_clinvar`
   - `get_variant_gnomad`
   - `get_variant_dgv`
   - `get_variant_decipher`
   - `get_variant_geno2mp`

3. **Disease Tools** (3 tools)
   - `get_omim_by_mim_number`
   - `get_omim_by_gene_symbol`
   - `get_omim_variant`

4. **Ortholog Tools** (2 tools)
   - `get_diopt_orthologs`
   - `get_diopt_alignment`

5. **Expression Tools** (3 tools)
   - `get_gtex_expression`
   - `get_ortholog_expression`
   - `get_pharos_targets`

6. **Utility Tools** (2 tools)
   - `validate_hgvs_variant`
   - `convert_protein_variant`

## Development

### Project Structure

```
MARRVEL_MCP/
├── server.py                          # Main FastMCP server
├── config.py                          # Configuration
├── requirements.txt                   # Dependencies
├── pyproject.toml                    # Black & pytest configuration
├── .pre-commit-config.yaml           # Pre-commit hooks configuration
├── pytest.ini                        # Test configuration
├── src/
│   ├── tools/                       # MCP tool modules
│   │   ├── gene_tools.py           # Gene query functions
│   │   ├── variant_tools.py        # Variant analysis functions
│   │   ├── disease_tools.py        # OMIM disease functions
│   │   ├── ortholog_tools.py       # DIOPT ortholog functions
│   │   ├── expression_tools.py     # Expression & drug target functions
│   │   └── utility_tools.py        # Variant nomenclature utilities
│   └── utils/
│       └── api_client.py           # HTTP client for MARRVEL API
├── examples/
│   ├── example_queries.py           # MCP usage examples
│   └── openai/
│       ├── README.md                # OpenAI integration guide
│       ├── openai_marrvel_simple.py # Production-ready OpenAI example
│       └── openai_marrvel_example.py # Advanced OpenAI example
└── tests/
    ├── README.md                    # Test documentation
    ├── test_server.py              # Core server tests
    ├── test_api_client.py          # API client tests
    ├── test_gene_tools.py          # Gene tools tests
    ├── test_variant_tools.py       # Variant tools tests
    ├── test_disease_tools.py       # Disease tools tests
    ├── test_ortholog_tools.py      # Ortholog tools tests
    ├── test_expression_tools.py    # Expression tools tests
    ├── test_utility_tools.py       # Utility tools tests
    ├── test_api_direct.py          # Direct API tests
    └── test_mcp_client.py          # MCP client tests
```

### Setup Development Environment

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install pre-commit hooks:
```bash
pre-commit install
```

This will automatically run code formatting and linting before each commit.

### Code Quality

We use **Black** for code formatting and **pre-commit** hooks to maintain code quality.

#### Running Black manually:
```bash
# Format all Python files
black .

# Check formatting without making changes
black --check .
```

#### Pre-commit hooks:
Pre-commit hooks run automatically on `git commit`. To run manually:
```bash
# Run on all files
pre-commit run --all-files

# Run on staged files only
pre-commit run
```

#### Bypass pre-commit (emergency use only):
```bash
git commit --no-verify -m "Emergency commit"
```

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
pytest tests/test_server.py

# Skip integration tests (for CI)
pytest tests/ -m "not integration"

# Run direct API tests
python3 tests/test_api_direct.py
```

### OpenAI Integration

MARRVEL-MCP can be used with OpenAI's function calling:

```bash
# Set your API key
export OPENAI_API_KEY='your-key-here'

# Run the example
python3 examples/openai/openai_marrvel_simple.py
```

See `examples/openai/README.md` and `OPENAI_INTEGRATION.md` for complete details.

## API Base URL

All requests are made to: `http://api.marrvel.org/data`

## Contributing

Contributions are welcome! Please feel free to submit issues or pull requests.

## License

[Add your license here]

## Citation

If you use MARRVEL in your research, please cite:

Wang J, et al. (2017) MARRVEL: Integration of Human and Model Organism Genetic Resources to Facilitate Functional Annotation of the Human Genome. *Am J Hum Genet* 100(6):843-853.

## Support

- MARRVEL Website: https://marrvel.org
- API Documentation: https://marrvel.org/doc
- Issues: [GitHub Issues URL]

## Version

Current version: 1.0.0
MARRVEL API version: v2
