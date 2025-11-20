# Refactoring Summary: Multi-Model Testing Workflow

## Changes Made

### 1. Removed Complex Multi-Model Logic
- **File**: `mcp_llm_test/evaluate_mcp.py`
- **Action**: Removed ~570 lines of complex multi-model testing code (lines 362-925)
- **Replaced with**: Simple deprecation message directing users to new workflow
- **Benefits**:
  - Simpler codebase (easier to maintain)
  - Better error isolation (each model tested independently)
  - Incremental result saving (no data loss on crashes)
  - Easy to resume interrupted runs

### 2. Added Output Directory Support
- **Files**: `mcp_llm_test/evaluate_mcp.py`, `mcp_llm_test/evaluation_modules/cli.py`
- **New argument**: `--output-dir PATH`
- **Purpose**: Allow specifying where to save results (CSV, cache, HTML)
- **Default**: `test-output/<timestamp>` (backward compatible)

### 3. Created Helper Scripts

#### `mcp_llm_test/get_model_configs.py`
- Parses `models_config.yaml` and outputs enabled models
- Supports JSON and bash-friendly formats
- Used by bash orchestration script

#### `run_benchmark.sh`
- Main orchestration script
- Iterates through enabled models
- Sets environment variables per model
- Runs `evaluate_mcp.py` for each model
- Saves results to `test_results/<model_id>/`
- Supports resume mode (`RESUME=true`)

#### `mcp_llm_test/analyze_results.py`
- Aggregates results from all model directories
- Generates summary tables (CSV, Markdown)
- Creates comparison plots (requires matplotlib)
- Automatically run by benchmark script

### 4. Updated Configuration
- **File**: `.gitignore`
- **Added**: `test_results/` directory to ignore list

- **File**: `config/llm_config.py`
- **Fixed**: Bug in `get_default_model_config()` where provider and model variables were swapped

### 5. Documentation
- **File**: `docs/BENCHMARK_WORKFLOW.md`
- Comprehensive guide for new workflow
- Migration instructions from old `--multi-model` mode

- **File**: `README.md`
- Added link to benchmark workflow documentation

## Usage Comparison

### Old Workflow
```bash
# Test multiple models (all in one process)
python mcp_llm_test/evaluate_mcp.py --multi-model

# Results embedded in single HTML report
# Hard to resume on failure
# All results lost if process crashes
```

### New Workflow
```bash
# Configure models in models_config.yaml
# Then run benchmark script
./run_benchmark.sh

# Resume interrupted run
RESUME=true ./run_benchmark.sh

# Results saved per model in test_results/
# - test_results/<model_id>/cache.json
# - test_results/<model_id>/evaluation.log
# - test_results/summary.csv
# - test_results/summary.md
# - test_results/comparison.png
```

## Benefits

### Reliability
- ✅ Each model tested independently (better isolation)
- ✅ Results saved incrementally (no data loss)
- ✅ Easy to resume (skip completed models)
- ✅ Better error handling (one model failure doesn't affect others)

### Maintainability
- ✅ Removed ~570 lines of complex async code
- ✅ Clear separation of concerns (config, test, orchestrate, analyze)
- ✅ Easier to debug (separate logs per model)
- ✅ Simpler to extend (add new models without code changes)

### Usability
- ✅ Multiple output formats (CSV, Markdown, plots)
- ✅ Resume support for long-running benchmarks
- ✅ Clear progress tracking
- ✅ Easier to run subsets or re-test specific models

## Testing

All existing tests pass:
```bash
pytest tests/test_llm_provider_config.py -v
# 4 passed in 2.23s
```

Helper scripts tested:
```bash
python mcp_llm_test/get_model_configs.py --format json
# Returns valid JSON with enabled models

python mcp_llm_test/get_model_configs.py --format bash
# Returns pipe-separated values for bash
```

Deprecation message tested:
```bash
python mcp_llm_test/evaluate_mcp.py --multi-model
# Shows helpful migration message
```

## Migration Path

For users currently using `--multi-model`:

1. Update models in `mcp_llm_test/models_config.yaml`
2. Run `./run_benchmark.sh` instead of `python evaluate_mcp.py --multi-model`
3. View results in `test_results/` directory
4. Use `analyze_results.py` for custom analysis if needed

## Files Changed

### Modified
- `.gitignore` - Added test_results/
- `README.md` - Added benchmark workflow link
- `config/llm_config.py` - Fixed config variable swap bug
- `mcp_llm_test/evaluate_mcp.py` - Removed multi-model code, added --output-dir
- `mcp_llm_test/evaluation_modules/cli.py` - Added --output-dir argument

### Created
- `run_benchmark.sh` - Main orchestration script
- `mcp_llm_test/get_model_configs.py` - Model config parser
- `mcp_llm_test/analyze_results.py` - Results aggregation
- `docs/BENCHMARK_WORKFLOW.md` - Comprehensive workflow documentation

## Future Enhancements

Possible improvements for future PRs:
- Parallel model testing (run multiple models concurrently)
- More visualization options (accuracy over time, per-test analysis)
- Integration with CI/CD for automated benchmarks
- Model performance regression detection
- Cost tracking per model (based on token usage)
