# Multi-Model Benchmark Testing

This document describes the new modular benchmark testing workflow that replaces the previous `--multi-model` mode.

## Overview

The new workflow separates concerns:

1. **Model configuration** - Define models in `models_config.yaml`
2. **Single model testing** - `evaluate_mcp.py` tests one model at a time
3. **Orchestration** - `run_benchmark.sh` iterates through models
4. **Analysis** - `analyze_results.py` aggregates results

## Quick Start

### 1. Configure Models

Edit `mcp_llm_test/models_config.yaml` to enable the models you want to test:

```yaml
models:
  - name: "Claude 3.5 Haiku"
    id: "us.anthropic.claude-3-5-haiku-20241022-v1:0"
    provider: "bedrock"
    enabled: true
    skip_web_search: true
```

### 2. Run Benchmark

```bash
# Fresh run (tests all enabled models)
./run_benchmark.sh

# Resume previous run (skip completed models)
RESUME=true ./run_benchmark.sh

# Custom configuration (override concurrency)
CONCURRENCY=2 ./run_benchmark.sh
```

### 3. View Results

Results are saved to `test_results/<model_id>/`:

- `cache.json` - Test results cache
- `test_cases.yaml` - Test case snapshot
- `evaluation.log` - Execution log
- HTML report (opened automatically)

Aggregated results:

- `test_results/summary.csv` - Detailed CSV
- `test_results/summary.md` - Markdown summary table
- `test_results/comparison.png` - Performance comparison chart

## Environment Variables

### Benchmark Configuration

- `RESUME=true` - Skip models with completed results
- `MODELS_CONFIG=path` - Custom models config file (default: `mcp_llm_test/models_config.yaml`)
- `OUTPUT_DIR=path` - Base results directory (default: `test_results`)
- `CONCURRENCY=N` - Concurrent tests per model (default: 1)
- `ANALYZE=false` - Skip automatic analysis (default: true)

### LLM Configuration

The benchmark script sets these automatically per model:

- `LLM_PROVIDER` - Provider name (openrouter, bedrock, openai, ollama)
- `LLM_MODEL` - Model identifier
- `OPENAI_API_KEY` - API key (if specified in config)
- `OPENAI_API_BASE` - API base URL (if specified in config)

## Directory Structure

```text
test_results/
├── meta-llama_llama-3.1-8b-instruct/     # Model results
│   ├── cache.json                         # Test results cache
│   ├── test_cases.yaml                    # Test case snapshot
│   ├── evaluation.log                     # Execution log
│   ├── evaluation_report_*.html           # HTML report
│   └── .completed                         # Completion marker
├── qwen_qwen3-14b/                        # Another model
│   └── ...
├── summary.csv                            # Aggregated results (CSV)
├── summary.md                             # Aggregated results (Markdown)
└── comparison.png                         # Performance chart
```

## Manual Analysis

If you need to re-run analysis without re-testing:

```bash
python mcp_llm_test/analyze_results.py test_results
```

## Individual Model Testing

You can still test a single model directly:

```bash
# Set up environment
export LLM_PROVIDER=bedrock
export LLM_MODEL=us.anthropic.claude-3-5-haiku-20241022-v1:0

# Run evaluation
python mcp_llm_test/evaluate_mcp.py \
  --output-dir test_results/my-test \
  --concurrency 1 \
  --cache
```

## Comparison with Old Workflow

### Old Workflow (--multi-model)

- ❌ All models tested in one Python process
- ❌ Complex nested async code
- ❌ Hard to resume on failure
- ❌ All results lost if process crashes
- ❌ Results embedded in single HTML

### New Workflow (run_benchmark.sh)

- ✅ Each model tested independently
- ✅ Simple sequential/parallel bash orchestration
- ✅ Resume by skipping completed models
- ✅ Results saved per model incrementally
- ✅ Multiple output formats (CSV, Markdown, plots)
- ✅ Easy to add/remove models mid-run
- ✅ Better error isolation

## Advanced Usage

### Testing Specific Models

Edit `models_config.yaml` to set `enabled: true` only for desired models.

### Custom Model Configuration

Add per-model API overrides:

```yaml
models:
  - name: "Custom Ollama"
    id: "llama2"
    provider: "ollama"
    enabled: true
    api_base: "http://remote-server:11434/v1"
```

### Parallel Model Testing

The bash script runs models sequentially by default. To run multiple models in parallel, you can launch multiple instances with different `MODELS_CONFIG` files.

### Filtering Test Cases

Use the `--subset` argument when testing individual models:

```bash
python mcp_llm_test/evaluate_mcp.py \
  --output-dir test_results/quick-test \
  --subset "1-5"  # Only run first 5 tests
```

## Troubleshooting

### Model Results Not Appearing in Analysis

Check for `.completed` marker file in the model directory. If missing, the model didn't complete successfully. Check `evaluation.log` for errors.

### Resume Not Working

Make sure `RESUME=true` is set and that `.completed` marker files exist for completed models.

### Plot Generation Fails

Install matplotlib: `pip install matplotlib`

### Cache Issues

To clear cache for a specific model:

```bash
rm -rf test_results/<model_id>/cache.json
```

## Migration from Old Code

If you have existing code using `--multi-model`:

1. Remove the `--multi-model` flag
2. Use `./run_benchmark.sh` instead
3. Configure models in `models_config.yaml`
4. Results are now in `test_results/` instead of embedded in HTML

The old `--multi-model` mode has been removed to simplify the codebase and improve reliability.
