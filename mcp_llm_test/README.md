# MCP LLM Evaluation Tool

Evaluation framework for testing MARRVEL-MCP tools using LangChain with multiple LLM providers. Runs test cases from `test_cases.yaml` and compares responses against expected outcomes.

## Quick Start

```bash
# Install evaluation dependencies
cd MARRVEL_MCP
uv sync --extra eval

# Configure your LLM provider (pick one)
export LLM_PROVIDER=openrouter   # or: openai, bedrock
export LLM_MODEL=google/gemini-2.5-flash
export OPENAI_API_KEY=your_api_key

# Run all test cases
python mcp_llm_test/evaluate_mcp.py
```

## Provider Configuration

### OpenRouter

```bash
export LLM_PROVIDER=openrouter
export LLM_MODEL=google/gemini-2.5-flash
export OPENAI_API_KEY=your_openrouter_api_key
# OPENAI_API_BASE is automatically set to https://openrouter.ai/api/v1
```

### OpenAI

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=gpt-4
export OPENAI_API_KEY=your_openai_api_key
```

### AWS Bedrock

Bedrock uses AWS credentials, not the OpenAI-compatible config:

```bash
export LLM_PROVIDER=bedrock
export LLM_MODEL=anthropic.claude-3-5-sonnet-20241022-v2:0
export AWS_REGION=us-east-1
# AWS credentials from ~/.aws/credentials or environment variables
```

### Other OpenAI-Compatible Services

Any service with an OpenAI-compatible API (Groq, Mistral, DeepSeek, vLLM, llama.cpp, etc.):

```bash
export LLM_PROVIDER=openai
export LLM_MODEL=your-model-name
export OPENAI_API_KEY=your-api-key
export OPENAI_API_BASE=https://your-service.com/v1
```

You can also override `api_key` and `api_base` per-model in `models_config.yaml` or via CLI flags.

## Command-Line Interface

```
python mcp_llm_test/evaluate_mcp.py [OPTIONS]
```

### Common Options

| Flag | Description |
|------|-------------|
| `--cache` | Reuse successful cached results; re-run only failures |
| `--clear` | Clear the evaluation cache and exit |
| `--resume RUN_ID` | Resume a previous run by Run ID |
| `--retry-failed` | Re-run failed tests when resuming |
| `--subset INDICES` | Run specific tests by index (e.g. `1-5`, `1,3,7-9`) |
| `--prompt QUESTION` | Ask a one-off question, get JSON response (no HTML report) |
| `--concurrency N` | Parallel test executions (default: 4, 1 for Bedrock) |
| `--provider NAME` | Override provider (`openrouter`, `openai`, `bedrock`) |
| `--model MODEL_ID` | Override model ID |
| `--api-key KEY` | Override API key for this run |
| `--api-base URL` | Override API base URL for this run |
| `--with-vanilla` | Also run tests without tool calling for comparison |
| `--with-web` | Three-way comparison: vanilla / web search / MCP tools |
| `--output-dir PATH` | Save results to a specific directory |
| `--verbose` | Show detailed error messages |
| `--quiet` | Suppress all non-error output |

Run `python mcp_llm_test/evaluate_mcp.py --help` for full details.

## Caching

Results are cached to `~/.cache/marrvel-mcp/evaluations/` after every run. By default, all tests run fresh. Use `--cache` to reuse successful results and only re-run failures.

| Scenario | Reads cache? | Writes cache? |
|----------|:---:|:---:|
| Default (no flag) | No | Yes |
| `--cache` | Yes (successes only) | Yes |
| `--clear` | No | No (deletes cache) |

The cache does **not** detect changes to test cases, server code, or model behavior. Run without `--cache` after making changes.

Run metadata is stored in a canonical file at:

`~/.cache/marrvel-mcp/evaluations/<run_id>/run_config.yaml`

When `--output-dir` points elsewhere, `run_config.yaml` and `test_cases.yaml` are mirrored there for convenience.

## Multi-Model Benchmarks

To benchmark multiple models, use `run_benchmark.sh` with `models_config.yaml`:

```bash
# Run all enabled models
./run_benchmark.sh

# Resume a previous benchmark
RESUME=true ./run_benchmark.sh
```

Results are saved to `test_results/<model_id>/`.

## Test Cases

Test cases are defined in `test_cases.yaml`:

```yaml
- case:
    name: "Descriptive test name"
    input: "Question or prompt for the LLM"
    expected: "Expected response or outcome"
```

## Output

After each run, an HTML report is generated with:
- Pass/fail status per test
- Overall success rate
- Expandable conversation history and tool call details
- Token usage statistics
