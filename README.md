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

MARRVEL-MCP supports **various MCP Tools** for genetics research including:

- Gene queries (by symbol, ID, or position)
- Variant analysis (dbNSFP, ClinVar, gnomAD)
- Disease associations (OMIM, HPO)
- Ortholog information (DIOPT)
- Expression data (GTEx)
- Literature search (PubMed, PMC)

## LLM Provider Configuration

MARRVEL-MCP supports multiple LLM providers through a **unified OpenAI-compatible configuration**, with the exception of Amazon Bedrock which uses separate AWS credentials.

### Unified Configuration Model

All OpenAI-compatible providers (OpenRouter, OpenAI, Groq, Mistral, DeepSeek, Ollama, LM Studio, vLLM, llama.cpp, etc.) share the same global configuration:

**Global Defaults:**
- `OPENAI_API_KEY`: API key for OpenAI-compatible providers
- `OPENAI_API_BASE`: Server address for OpenAI-compatible providers
- `OPENAI_MODEL`: Default model name

**Per-Model Overrides** (in YAML config or function parameters):
- `api_key`: Override OPENAI_API_KEY for specific model
- `api_base`: Override OPENAI_API_BASE for specific model

### Supported Providers

#### 1. OpenRouter

Access 100+ models through OpenRouter:

```bash
export LLM_PROVIDER=openrouter
export LLM_MODEL=google/gemini-2.5-flash
export OPENAI_API_KEY=your_openrouter_api_key
# OPENAI_API_BASE is automatically set to https://openrouter.ai/api/v1 for openrouter provider
```

#### 2. OpenAI

Use OpenAI's official API:

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export OPENAI_API_KEY=your_openai_api_key
# OPENAI_API_BASE uses OpenAI's default endpoint if not specified
```
#### 3. AWS Bedrock (Separate Configuration)

Bedrock uses AWS credentials, not OpenAI-compatible config:

```bash
export LLM_PROVIDER=bedrock
export LLM_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
export AWS_ACCESS_KEY_ID=your_aws_access_key
export AWS_SECRET_ACCESS_KEY=your_aws_secret_key
export AWS_REGION=us-east-1
```

#### 4. Other OpenAI-Compatible Services

Any service compatible with the OpenAI API (Groq, Mistral, DeepSeek, vLLM, etc.):

```bash
export LLM_PROVIDER=openai  # Or create a custom provider type
export LLM_MODEL=your-model-name
export OPENAI_API_KEY=your-api-key
export OPENAI_API_BASE=https://your-service.com/v1
```

## Documentation

<!--- **[API Reference](./API_DOCUMENTATION.md)** - Complete tool documentation-->
- **[MCP LLM Evaluation](mcp_llm_test/README.md)** - CLI tool for testing MCP with LangChain
- **[Contributing Guide](CONTRIBUTING.md)** - Development guidelines

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
