# MARRVEL-MCP

[![CI](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/ci.yml)
[![Pre-commit](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/pre-commit.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Model Context Protocol (MCP) server for [MARRVEL](https://marrvel.org) - enabling AI agents to access genetics databases and variant analysis tools for rare disease research.

## Quick Start

### Installation

1. Clone and install:
```bash
git clone https://github.com/hyunhwan-bcm/MARRVEL_MCP.git
cd MARRVEL_MCP
pip install -r requirements.txt
```

2. Configure your MCP client (e.g., Claude Desktop):

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

### Usage

Ask your AI assistant natural language questions:

```
"Get information about the gene TP53"
"Look up variant chr17:g.7577121C>T in ClinVar"
"Find OMIM diseases associated with BRCA1"
"Find orthologs for human TP53"
"Search PubMed for TP53 cancer therapy literature"
"Get PubMed article 32601318"
```

## Features

- **28 MCP Tools** for genetics research
- Gene queries (by symbol, ID, or position)
- Variant analysis (dbNSFP, ClinVar, gnomAD)
- Disease associations (OMIM)
- Ortholog information (DIOPT)
- Expression data (GTEx)
- Drug targets (Pharos)
- PubMed literature search

## Documentation

- **[API Reference](./API_DOCUMENTATION.md)** - Complete tool documentation
- **[Architecture](docs/ARCHITECTURE.md)** - Technical details
- **[Contributing Guide](CONTRIBUTING.md)** - Development guidelines
- **[OpenAI Integration](examples/openai/README.md)** - Using with OpenAI

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Format code
black .
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed development instructions.

## Citation

Wang J, et al. (2017) MARRVEL: Integration of Human and Model Organism Genetic Resources to Facilitate Functional Annotation of the Human Genome. *Am J Hum Genet* 100(6):843-853.

## Support

- Website: https://marrvel.org
- API Docs: https://marrvel.org/doc
