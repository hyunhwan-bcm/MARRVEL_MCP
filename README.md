# MARRVEL-MCP

[![CI](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/ci.yml)
[![Pre-commit](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/pre-commit.yml/badge.svg)](https://github.com/hyunhwan-bcm/MARRVEL_MCP/actions/workflows/pre-commit.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A Model Context Protocol (MCP) server for [MARRVEL](https://marrvel.org) - enabling AI agents to access genetics databases and variant analysis tools for rare disease research.

## Demo

Try out MARRVEL-MCP in action:
- <a href="https://chat.marrvel.org">MARRVEL-MCP Chatbot Demo</a>

## Quick Start

### Installation

```bash
git clone https://github.com/hyunhwan-bcm/MARRVEL_MCP.git
cd MARRVEL_MCP

# Using uv (recommended)
uv sync                  # core MCP server only
uv sync --extra eval     # include evaluation framework dependencies

# Or using pip
pip install .                  # core MCP server only
pip install ".[eval]"          # include evaluation framework dependencies
```

### MCP Server Setup

To use MARRVEL-MCP with Claude Desktop, LM Studio, or other MCP-compatible clients, add the following to your client's MCP configuration:

```json
{
  "mcpServers": {
    "marrvel-mcp": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["/path/to/MARRVEL_MCP/server.py"]
    }
  }
}
```

Replace the paths with the actual locations of your Python virtual environment and the cloned repository.

### Usage

Ask your AI assistant natural language questions about genes, variants, diseases, orthologs, and literature. For example test cases, see [`mcp_llm_test/test_cases.yaml`](mcp_llm_test/test_cases.yaml).

## Features

MARRVEL-MCP provides **35+ MCP tools** for genetics research:

- **Gene queries** - by symbol, Entrez ID, or genomic position
- **Variant analysis** - dbNSFP, ClinVar, gnomAD, DGV, Geno2MP
- **Disease associations** - OMIM, HPO, DECIPHER
- **Ortholog information** - DIOPT across model organisms
- **Expression data** - GTEx, Pharos drug targets, STRING interactions
- **Literature search** - PubMed, PMC full text/tables/figures
- **Coordinate conversion** - hg19/hg38 liftover

See [`docs/TOOL_RELATIONSHIPS.md`](docs/TOOL_RELATIONSHIPS.md) for a visual diagram of tool chains and workflows.

## Documentation

| Document | Description |
|----------|-------------|
| [`mcp_llm_test/README.md`](mcp_llm_test/README.md) | Evaluation framework for benchmarking LLMs with MARRVEL-MCP |
| [`docs/TOOL_RELATIONSHIPS.md`](docs/TOOL_RELATIONSHIPS.md) | Tool relationship graph and common analysis chains |
| [`marrvel_mcp/README.md`](marrvel_mcp/README.md) | Package API reference for the `marrvel_mcp` module |
| [`tests/README.md`](tests/README.md) | Test suite overview and instructions |

## Development

```bash
# Install with dev dependencies
uv sync --group dev --extra eval

# Run tests
pytest tests/

# Format code
black .
```

## Citation

Wang J, et al. (2017) MARRVEL: Integration of Human and Model Organism Genetic Resources to Facilitate Functional Annotation of the Human Genome. *Am J Hum Genet* 100(6):843-853.

## Support

- Website: https://marrvel.org
- API Docs: https://marrvel.org/doc
