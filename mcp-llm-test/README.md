# MCP LLM Test Evaluation

This directory contains the LLM-based evaluation framework for testing MARRVEL MCP tools.

## Overview

The `evaluate_mcp.py` script runs automated tests against the MARRVEL MCP server using LangChain and OpenRouter API. It evaluates whether tool calls return correct information compared to expected results.

## Features

- **Automated Testing**: Runs test cases defined in `test_cases.yaml`
- **Intelligent Caching**: Caches successful test results to speed up subsequent runs
- **HTML Reports**: Generates interactive HTML reports with conversation history
- **Concurrent Execution**: Runs multiple tests in parallel for efficiency
- **Token Counting**: Validates responses don't exceed token limits

## Requirements

- Python 3.13+
- OpenRouter API key (set as `OPENROUTER_API_KEY` environment variable)
- Dependencies from `requirements.txt`

## Usage

### Basic Usage

```bash
# Run tests normally (uses cache for successful results)
python evaluate_mcp.py
```

### Cache Management Flags

#### `--clear`: Fresh Test Run

Removes the existing cache before starting tests, guaranteeing a completely fresh run and cache population.

```bash
# Clear cache and run all tests
python evaluate_mcp.py --clear
```

**Use case**: When you want to reset all cached results and start fresh, useful after:
- Updating test expectations
- Modifying the MCP server implementation
- Testing after significant changes

#### `--force`: Ignore Cached Results

Ignores success entries in the cache and reruns all jobs regardless of earlier results. Still saves new results to cache.

```bash
# Rerun all tests, ignoring cached successes
python evaluate_mcp.py --force
```

**Use case**: When you want to:
- Verify that cached "successes" still pass
- Re-evaluate all tests without clearing cache history
- Check for consistency issues

### Combined Flags

```bash
# Clear cache AND force rerun of all tests
python evaluate_mcp.py --clear --force
```

This combination is useful when you want a completely fresh evaluation with no cached data influencing the results.

## Cache Behavior

### What Gets Cached?

- Test question and expected answer (as cache key)
- Actual response from the LLM
- Tool calls made during the test
- Full conversation history
- Token usage
- Classification result (yes/no)

### Cache Strategy

1. **Successful results are cached**: Tests that receive a "yes" classification are cached
2. **Failed results are NOT cached**: Tests that fail (receive a "no" classification) will be rerun on the next execution
3. **Errors are NOT cached**: Tests that error out will be retried on the next run
4. **Token limit exceeded results ARE cached**: Tests that exceed token limits are cached to avoid wasting API calls

### Cache Location

Cache files are stored in `.cache/test_results_cache.json` relative to this directory. This directory is ignored by git (see `.gitignore`).

## Test Cases

Test cases are defined in `test_cases.yaml`. Each test case includes:
- `name`: Descriptive name for the test
- `input`: The question/prompt to ask
- `expected`: Expected response or information

## Output

The script generates:
1. Console output showing test progress
2. An HTML report with:
   - Success rate summary
   - Detailed results table
   - Tool calls made
   - Full conversation JSON (in modals)
   - Token usage

The HTML report opens automatically in your default browser.

## Examples

### Example 1: First Time Running Tests
```bash
# No cache exists, all tests run
python evaluate_mcp.py
```

### Example 2: Second Run (Reusing Cache)
```bash
# Successful tests from previous run are skipped
# Only failed tests are rerun
python evaluate_mcp.py
```

### Example 3: After Changing Server Code
```bash
# Clear cache to test everything fresh
python evaluate_mcp.py --clear
```

### Example 4: Verifying Consistency
```bash
# Force rerun without clearing history
python evaluate_mcp.py --force
```

## Troubleshooting

### Cache Issues

If you encounter cache-related issues:

1. **Clear the cache**: `python evaluate_mcp.py --clear`
2. **Manually delete cache**: `rm -rf .cache/`
3. **Check cache file**: `cat .cache/test_results_cache.json`

### Missing API Key

If you see "OPENROUTER_API_KEY not found":

1. Create a `.env` file in the project root
2. Add: `OPENROUTER_API_KEY=your_key_here`
3. Or export the environment variable: `export OPENROUTER_API_KEY=your_key_here`

### Token Limit Exceeded

If tests fail due to token limits:

1. Check the `MAX_TOKENS` constant in `evaluate_mcp.py`
2. Consider reducing the size of tool responses
3. Review which tools return large amounts of data

## Development

To add new test cases:

1. Edit `test_cases.yaml`
2. Add a new entry with `name`, `input`, and `expected` fields
3. Run tests with `--clear` to populate fresh cache

## Related Files

- `evaluate_mcp.py`: Main evaluation script
- `test_cases.yaml`: Test case definitions
- `../assets/evaluation_report_template.html`: HTML report template
- `../tests/test_evaluate_cache.py`: Unit tests for cache functionality
- `../tests/test_evaluate_cli.py`: Integration tests for CLI flags
