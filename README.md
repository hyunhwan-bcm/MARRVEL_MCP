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

### MCP Server Setup (mcp.json)

To use MARRVEL-MCP with LM Studio, Claude Desktop, or other MCP-compatible clients, create an `mcp.json` file or add the following block to your client configuration:

```json
{
  "mcpServers": {
    "marrvel-mcp": {
      "command": "/Users/hyunhwan/CodeWorkspace/MARRVEL_MCP/.venv/bin/python",
      "args": [
        "/Users/hyunhwan/CodeWorkspace/MARRVEL_MCP/server.py"
      ]
    }
  }
}
```

- **Recommended:** Use a Python virtual environment (`venv`) and specify the full path to your venv's python executable as shown above.
- If you do not use a venv, you can use the system python (e.g., `"command": "python"` or `"python3"`).
- Make sure all dependencies are installed in the environment you specify.

This configuration allows your MCP client to launch the MARRVEL server and access all tools.

### Usage

Ask your AI assistant natural language questions about genes, variants, diseases, orthologs, and literature.

For comprehensive examples and test cases, see: [test_cases.yaml](mcp-llm-test/test_cases.yaml)

## Features

- **42 MCP Tools** for genetics research
- Gene queries (by symbol, ID, or position)
- Variant analysis (dbNSFP, ClinVar, gnomAD)
- Disease associations (OMIM, HPO)
- Ortholog information (DIOPT)
- Expression data (GTEx)
- Drug targets (Pharos)
- Literature search (PubMed, PMC):
  - Search PubMed by keyword
  - Get abstracts from PMC articles
  - Extract full text from open-access PMC articles
  - Extract tables with captions (markdown format)
  - Extract figure captions
  - Support for both PMID and PMCID

## Documentation

- **[API Reference](./API_DOCUMENTATION.md)** - Complete tool documentation
- **[MCP LLM Evaluation](mcp-llm-test/README.md)** - CLI tool for testing MCP with LangChain
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
