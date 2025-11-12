# Pull Request: Generalize LLM Testing Framework to Support Multiple Providers

## Summary

This PR generalizes the LLM-based testing framework to support multiple providers (**Bedrock**, **OpenAI**, **OpenRouter**, and **Ollama**) while maintaining full backward compatibility with the existing OpenRouter-only implementation.

### Key Changes

#### 1. **New Provider Abstraction Layer** (`llm_providers.py`)
- Unified `create_llm_instance()` factory function for creating LLM instances
- Support for 4 providers: Bedrock, OpenAI, OpenRouter, Ollama
- **All providers except Bedrock use OpenAI API** for consistency
- Automatic provider inference from model ID format
- Provider-specific credential validation

#### 2. **Enhanced Configuration** (`llm_config.py`)
- New `get_default_model_config()` function for provider-aware configuration
- Preserved `get_openrouter_model()` for backward compatibility
- Support for new environment variables: `LLM_PROVIDER` and `LLM_MODEL`
- Backward compatible with existing `OPENROUTER_MODEL` env var

#### 3. **Refactored Evaluation Script** (`evaluate_mcp.py`)
- Replaced direct `ChatOpenAI` instantiation with `create_llm_instance()`
- Updated single-model and multi-model test flows
- Added provider-specific credential validation
- Maintains complete backward compatibility

#### 4. **Updated Model Configuration** (`models_config.yaml`)
- Added `provider` field to each model definition
- Included commented examples for Bedrock, OpenAI, and Ollama
- Documented provider-specific model ID formats

#### 5. **Comprehensive Documentation** (`LLM_PROVIDERS_GUIDE.md`)
- Provider comparison and feature matrix
- Configuration examples for all providers
- Migration guide from OpenRouter-only setup
- Troubleshooting and best practices

---

## Supported Providers

### 1. **OpenRouter** (Default)
- **API:** OpenAI-compatible
- **Features:** Access to 100+ models, web search support (`:online` suffix)
- **Models:** Claude, Gemini, Llama, and more
- **Env Vars:** `OPENROUTER_API_KEY`

### 2. **OpenAI**
- **API:** Native OpenAI API
- **Features:** Latest GPT models, function calling
- **Models:** GPT-4, GPT-3.5 Turbo, etc.
- **Env Vars:** `OPENAI_API_KEY`

### 3. **AWS Bedrock**
- **API:** AWS Bedrock (via boto3)
- **Features:** Enterprise security, AWS integration
- **Models:** Claude, other foundation models
- **Env Vars:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`

### 4. **Ollama**
- **API:** OpenAI-compatible
- **Features:** Local execution, privacy, no API costs
- **Models:** Llama2, Mistral, CodeLlama, etc.
- **Env Vars:** Optional (doesn't require auth by default)

---

## Usage Examples

### Single Provider (Environment Variables)

```bash
# OpenRouter (default, backward compatible)
export OPENROUTER_MODEL=google/gemini-2.5-flash
export OPENROUTER_API_KEY=your_key
python evaluate_mcp.py

# OpenAI
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export OPENAI_API_KEY=your_key
python evaluate_mcp.py

# Bedrock
export LLM_PROVIDER=bedrock
export LLM_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
python evaluate_mcp.py

# Ollama
export LLM_PROVIDER=ollama
export LLM_MODEL=llama2
python evaluate_mcp.py
```

### Multi-Provider Testing

```bash
# Test multiple providers simultaneously
python evaluate_mcp.py --multi-model
```

---

## Architecture Benefits

✅ **Modularity:** Refactored invocation logic into separate, reusable functions
✅ **Flexibility:** Easy to switch between providers via configuration
✅ **Consistency:** All providers (except Bedrock) use OpenAI API
✅ **Backward Compatibility:** Existing scripts continue to work unchanged
✅ **Enterprise Ready:** Native AWS Bedrock integration for enterprise deployments
✅ **Cost Optimization:** Support for local Ollama models (no API costs)

---

## Migration Guide

### Existing Code (No Changes Needed)

Your existing code will continue to work without any modifications:

```bash
# This still works exactly as before
export OPENROUTER_MODEL=google/gemini-2.5-flash
export OPENROUTER_API_KEY=your_key
python evaluate_mcp.py
```

### Adopting New Provider System (Optional)

If you want to use other providers:

```bash
# New way: Explicit provider configuration
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export OPENAI_API_KEY=your_key
python evaluate_mcp.py
```

---

## Testing

- ✅ Syntax validation for all modified files
- ✅ Module imports verified
- ✅ Provider inference tested
- ✅ Configuration loading tested
- ✅ Backward compatibility confirmed

---

## Documentation

Complete documentation is available in `LLM_PROVIDERS_GUIDE.md`, including:
- Provider-specific setup instructions
- Configuration examples
- Troubleshooting guide
- Best practices

---

## Files Changed

- `llm_providers.py` (new): Provider abstraction layer
- `llm_config.py` (modified): Enhanced configuration with provider support
- `mcp-llm-test/evaluate_mcp.py` (modified): Refactored to use provider abstraction
- `mcp-llm-test/models_config.yaml` (modified): Added provider field to models
- `LLM_PROVIDERS_GUIDE.md` (new): Comprehensive documentation

---

## Checklist

- [x] Provider abstraction layer implemented
- [x] All providers use OpenAI API (except Bedrock)
- [x] Backward compatibility maintained
- [x] Configuration updated with provider field
- [x] Documentation created
- [x] Code tested and validated

---

## Branch Information

**Branch:** `claude/generalize-llm-testing-framework-011CV4YtazN7dNtBzSbTAciR`
**Base:** `main`

---

## Related Issues

This PR addresses the need for a generalized LLM testing framework that supports multiple providers while maintaining backward compatibility.
