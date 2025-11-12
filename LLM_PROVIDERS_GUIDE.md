# LLM Provider System Guide

This guide explains the generalized LLM testing framework that supports multiple providers: **Bedrock**, **OpenAI**, **OpenRouter**, and **Ollama**.

## Table of Contents

- [Overview](#overview)
- [Supported Providers](#supported-providers)
- [Architecture](#architecture)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Migration Guide](#migration-guide)
- [Provider-Specific Notes](#provider-specific-notes)

## Overview

The LLM testing framework has been generalized to support multiple LLM providers through a unified abstraction layer. This allows you to:

- Test models across different providers (Bedrock, OpenAI, OpenRouter, Ollama)
- Switch providers easily through configuration
- Maintain backward compatibility with existing OpenRouter-only code
- Use provider-specific features (e.g., web search for OpenRouter)

### Key Design Principles

1. **All providers except Bedrock use the OpenAI API** for consistency
   - OpenRouter: Uses OpenAI-compatible API
   - Ollama: Uses OpenAI-compatible API
   - OpenAI: Direct OpenAI API

2. **Bedrock uses AWS SDK** (boto3 and langchain_aws)

3. **Unified interface** through `create_llm_instance()` factory function

## Supported Providers

### 1. OpenRouter

**Description:** Access to 100+ models from various providers through a single API

**API Compatibility:** OpenAI-compatible

**Features:**
- Web search support (`:online` suffix)
- Access to Claude, Gemini, Llama, and many other models
- Unified pricing across providers

**Environment Variables:**
```bash
OPENROUTER_API_KEY=your_api_key_here
```

**Example Model IDs:**
- `google/gemini-2.5-flash`
- `anthropic/claude-3.5-sonnet`
- `meta-llama/llama-3.3-70b-instruct`

### 2. OpenAI

**Description:** Direct access to OpenAI's models (GPT-4, GPT-3.5, etc.)

**API Compatibility:** Native OpenAI API

**Features:**
- Latest GPT models
- Function calling support
- Native OpenAI features

**Environment Variables:**
```bash
OPENAI_API_KEY=your_api_key_here
```

**Example Model IDs:**
- `gpt-4`
- `gpt-4-turbo-preview`
- `gpt-3.5-turbo`

### 3. AWS Bedrock

**Description:** AWS-managed service for foundation models

**API Compatibility:** AWS Bedrock API (via boto3)

**Features:**
- Enterprise-grade security
- AWS integration
- Claude and other foundation models

**Environment Variables:**
```bash
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_DEFAULT_REGION=us-east-1  # Optional, defaults to us-east-1
```

**Example Model IDs:**
- `anthropic.claude-3-5-sonnet-20241022-v2:0`
- `anthropic.claude-3-5-haiku-20241022-v1:0`

**Note:** Bedrock model IDs use a different format (dot notation with version suffix)

### 4. Ollama

**Description:** Run LLMs locally or on your own infrastructure

**API Compatibility:** OpenAI-compatible

**Features:**
- Local model execution
- Privacy and control
- No API costs

**Environment Variables:**
```bash
# Optional - Ollama doesn't require authentication by default
OLLAMA_API_KEY=optional_key  # Only if your Ollama instance requires auth
```

**Example Model IDs:**
- `llama2`
- `mistral`
- `codellama`

**Default Endpoint:** `http://localhost:11434/v1`

## Architecture

### Core Modules

```
llm_providers.py       # Provider abstraction and LLM instance creation
llm_config.py          # Configuration and environment variable handling
evaluate_mcp.py        # Main evaluation script (updated to use providers)
models_config.yaml     # Multi-model configuration with provider info
```

### Key Functions

#### `create_llm_instance(provider, model_id, temperature=0, web_search=False, **kwargs)`

Factory function to create LLM instances for any provider.

**Parameters:**
- `provider`: Provider type (`"bedrock"`, `"openai"`, `"openrouter"`, `"ollama"`)
- `model_id`: Model identifier (provider-specific format)
- `temperature`: Sampling temperature (0-1)
- `web_search`: Enable web search if supported by provider
- `**kwargs`: Additional provider-specific arguments

**Returns:** LangChain LLM instance (ChatOpenAI or ChatBedrock)

**Example:**
```python
from llm_providers import create_llm_instance

# Create OpenRouter instance
llm = create_llm_instance(
    provider="openrouter",
    model_id="google/gemini-2.5-flash",
    temperature=0,
)

# Create Bedrock instance
llm = create_llm_instance(
    provider="bedrock",
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    temperature=0,
    region_name="us-west-2",
)
```

#### `get_provider_config(provider)`

Get configuration for a specific provider.

**Returns:** `ProviderConfig` object with provider-specific settings

#### `infer_provider_from_model_id(model_id)`

Automatically infer the provider from model ID format.

**Examples:**
- `google/gemini-2.5-flash` → `openrouter`
- `gpt-4` → `openai`
- `anthropic.claude-3-5-sonnet-20241022-v2:0` → `bedrock`
- `llama2` → `ollama`

## Configuration

### Environment-Based Configuration

#### Option 1: Explicit Provider Configuration (Recommended)

```bash
# Set provider and model explicitly
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
```

#### Option 2: Legacy OpenRouter Configuration (Backward Compatible)

```bash
# Uses OpenRouter by default
export OPENROUTER_MODEL=google/gemini-2.5-flash
export OPENROUTER_API_KEY=your_key
```

#### Option 3: Model-Only Configuration (Auto-Infer Provider)

```bash
# Provider is inferred from model ID format
export LLM_MODEL=gpt-4  # Infers "openai"
```

### Multi-Model Configuration (`models_config.yaml`)

Define multiple models with their providers for comparison testing:

```yaml
models:
  # OpenRouter models
  - name: "Gemini 2.5 Flash"
    id: "google/gemini-2.5-flash"
    provider: "openrouter"
    enabled: true
    description: "Google Gemini via OpenRouter"

  # OpenAI models
  - name: "GPT-4"
    id: "gpt-4"
    provider: "openai"
    enabled: true
    description: "OpenAI GPT-4 direct API"

  # Bedrock models
  - name: "Claude 3.5 Sonnet (Bedrock)"
    id: "anthropic.claude-3-5-sonnet-20241022-v2:0"
    provider: "bedrock"
    enabled: true
    description: "Claude via AWS Bedrock"

  # Ollama models
  - name: "Llama 2"
    id: "llama2"
    provider: "ollama"
    enabled: true
    description: "Llama 2 via Ollama local"

config:
  only_enabled: true
  timeout: 300
  use_cache: true
```

## Usage Examples

### Single-Model Testing (Default)

```bash
# Use default model (Gemini 2.5 Flash via OpenRouter)
python evaluate_mcp.py

# Override with OpenAI GPT-4
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export OPENAI_API_KEY=your_key
python evaluate_mcp.py

# Use Bedrock Claude
export LLM_PROVIDER=bedrock
export LLM_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
python evaluate_mcp.py

# Use Ollama local model
export LLM_PROVIDER=ollama
export LLM_MODEL=llama2
python evaluate_mcp.py
```

### Multi-Model Testing

```bash
# Test all enabled models across providers
python evaluate_mcp.py --multi-model

# Use custom models configuration
python evaluate_mcp.py --multi-model --models-config my_models.yaml
```

### Web Search Testing (OpenRouter Only)

```bash
# OpenRouter supports web search with :online suffix
export OPENROUTER_MODEL=google/gemini-2.5-flash
python evaluate_mcp.py --with-web
```

### Ad-Hoc Questions

```bash
# Ask a single question
python evaluate_mcp.py --prompt "What is MECP2?"
```

## Migration Guide

### Migrating from OpenRouter-Only to Multi-Provider

The framework maintains **100% backward compatibility**. Existing code will continue to work without changes.

#### Before (OpenRouter-only)

```python
from llm_config import get_openrouter_model
from langchain_openai import ChatOpenAI
import os

model = get_openrouter_model()
llm = ChatOpenAI(
    model=model,
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.getenv("OPENROUTER_API_KEY"),
    temperature=0,
)
```

#### After (Multi-provider)

```python
from llm_config import get_default_model_config
from llm_providers import create_llm_instance

model_id, provider = get_default_model_config()
llm = create_llm_instance(
    provider=provider,
    model_id=model_id,
    temperature=0,
)
```

#### Or Keep Using Legacy API (Still Works!)

```python
from llm_config import get_openrouter_model
from llm_providers import create_llm_instance

model = get_openrouter_model()
llm = create_llm_instance(
    provider="openrouter",
    model_id=model,
    temperature=0,
)
```

## Provider-Specific Notes

### OpenRouter

- **Web Search:** Add `:online` suffix to model ID or use `web_search=True` parameter
- **Rate Limits:** Varies by model provider
- **Pricing:** Pay-per-use, see OpenRouter dashboard
- **Docs:** https://openrouter.ai/docs

### OpenAI

- **Rate Limits:** Based on tier (https://platform.openai.com/docs/guides/rate-limits)
- **Pricing:** See https://openai.com/pricing
- **Models:** GPT-4, GPT-3.5 Turbo, etc.

### Bedrock

- **Authentication:** Requires AWS credentials
- **Region:** Set via `AWS_DEFAULT_REGION` env var or `region_name` parameter
- **Pricing:** Pay-per-use, see AWS pricing
- **Model Access:** Must request access to models in AWS Console
- **Docs:** https://docs.aws.amazon.com/bedrock/

### Ollama

- **Local Setup:** Install Ollama and pull models: `ollama pull llama2`
- **API Endpoint:** Default `http://localhost:11434/v1`
- **Authentication:** Not required by default
- **Models:** See available models at https://ollama.ai/library

## Troubleshooting

### Missing Credentials

```
ValueError: OPENROUTER_API_KEY not found in environment variables
```

**Solution:** Set the required API key for your provider:
```bash
export OPENROUTER_API_KEY=your_key
# or
export OPENAI_API_KEY=your_key
# or
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
```

### Missing Dependencies

```
ImportError: No module named 'langchain_aws'
```

**Solution:** Install provider-specific dependencies:
```bash
# For Bedrock
pip install langchain-aws boto3

# For OpenAI/OpenRouter/Ollama
pip install langchain-openai
```

### Model Not Found

```
Error: Model X not found
```

**Solution:**
- For OpenRouter: Check model ID at https://openrouter.ai/models
- For OpenAI: Verify you have access to the model
- For Bedrock: Request model access in AWS Console
- For Ollama: Pull the model: `ollama pull model_name`

## Examples

### Example 1: Compare OpenRouter and OpenAI

Create `my_models.yaml`:
```yaml
models:
  - name: "Gemini (OpenRouter)"
    id: "google/gemini-2.5-flash"
    provider: "openrouter"
    enabled: true

  - name: "GPT-4 (OpenAI)"
    id: "gpt-4"
    provider: "openai"
    enabled: true
```

Run comparison:
```bash
export OPENROUTER_API_KEY=your_openrouter_key
export OPENAI_API_KEY=your_openai_key
python evaluate_mcp.py --multi-model --models-config my_models.yaml
```

### Example 2: Local Testing with Ollama

```bash
# Start Ollama and pull a model
ollama pull llama2

# Run tests
export LLM_PROVIDER=ollama
export LLM_MODEL=llama2
python evaluate_mcp.py
```

### Example 3: Enterprise Bedrock Setup

```bash
# Configure AWS credentials
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-west-2

# Run tests
export LLM_PROVIDER=bedrock
export LLM_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
python evaluate_mcp.py
```

## Best Practices

1. **Use Environment Variables:** Store credentials in `.env` file, never commit them
2. **Provider Selection:** Choose based on your needs:
   - **OpenRouter:** Quick access to many models
   - **OpenAI:** Best for GPT-4/3.5 performance
   - **Bedrock:** Enterprise security and AWS integration
   - **Ollama:** Privacy, control, and no API costs

3. **Cost Management:** Monitor usage and set up billing alerts
4. **Testing:** Use caching (`--cache`) to reduce API calls during development
5. **Multi-Model:** Compare providers to find the best model for your use case

## Contributing

When adding new providers:

1. Add provider config to `PROVIDER_CONFIGS` in `llm_providers.py`
2. Implement credential validation in `validate_provider_credentials()`
3. Add provider-specific LLM instantiation logic in `create_llm_instance()`
4. Update `models_config.yaml` with example models
5. Add documentation and examples to this guide

## Support

For issues or questions:
- Check existing test cases in `tests/` directory
- Review example configurations in `models_config.yaml`
- See LangChain documentation for provider-specific details
