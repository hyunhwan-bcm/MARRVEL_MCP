# MCP LLM Testing with Caching

This directory contains the MCP LLM evaluation script that tests MCP tools using LangChain with OpenRouter.

## Features

- **Automated Testing**: Runs test cases defined in `test_cases.yaml`
- **LLM Evaluation**: Uses LangChain with OpenRouter to evaluate responses
- **Caching**: Saves successful test results to avoid re-running passing tests
- **HTML Reports**: Generates interactive HTML reports with test results

## Usage

### Basic Usage (No Caching)

```bash
python evaluate_mcp.py
```

This runs all test cases without caching. Each test will be executed even if it passed previously.

### Using Cache

```bash
python evaluate_mcp.py --use-cache
```

This enables caching:
- On first run, all tests execute normally and successful results are cached
- On subsequent runs, tests that previously passed are skipped and results are loaded from cache
- Only new tests or previously failed tests will be executed
- Saves API costs and time by not re-running successful tests

### Clearing Cache

```bash
python evaluate_mcp.py --clear-cache
```

This clears all cached test results. Use this when:
- Test cases have been modified
- Expected outputs have changed
- You want to re-run all tests from scratch

## How Caching Works

### Cache Key Generation
Each test case is identified by a SHA256 hash of:
- Test input question
- Expected output

This ensures that if either the input or expected output changes, the cache is invalidated for that test.

### Cache Storage
- Cached results are stored in `../.cache/mcp-llm-test/`
- Each successful test result is saved as a JSON file named `{cache_key}.json`
- The cache directory is excluded from git via `.gitignore`

### Cache Validation
Only successful test results are cached:
- Results with classification containing "yes" are cached
- Failed results are never cached and must be re-run
- When loading from cache, the classification is validated to ensure it indicates success

### What Gets Cached
Each cached result includes:
- Original question and expected output
- LLM response
- Classification result
- Tool calls made during execution
- Full conversation history
- Token usage statistics

## Environment Setup

Required environment variables:
- `OPENROUTER_API_KEY`: API key for OpenRouter

Set in `.env` file or export as environment variable:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

## Test Cases

Test cases are defined in `test_cases.yaml`. Each test case includes:
- `name`: Descriptive name for the test
- `input`: Question/prompt for the LLM
- `expected`: Expected response or information

## Examples

### First Run (No Cache)
```bash
$ python evaluate_mcp.py --use-cache
--- Cache enabled: /path/to/.cache/mcp-llm-test ---
--- Running: Gene for NM_001045477.4:c.187C>T ---
--- Running: Protein change for NM_001045477.4:c.187C>T ---
...
--- HTML report saved to: /tmp/evaluation_results_xxx.html ---
```

### Second Run (Using Cache)
```bash
$ python evaluate_mcp.py --use-cache
--- Cache enabled: /path/to/.cache/mcp-llm-test ---
--- Using cached result for: Gene for NM_001045477.4:c.187C>T ---
--- Using cached result for: Protein change for NM_001045477.4:c.187C>T ---
...
--- HTML report saved to: /tmp/evaluation_results_xxx.html ---
```

## Benefits of Caching

1. **Cost Savings**: Avoid re-running expensive LLM API calls for tests that already pass
2. **Time Savings**: Significantly faster test runs when many tests already pass
3. **Focused Testing**: Spend time only on new or failing tests
4. **Reproducibility**: Cached successful results ensure consistent test reports

## Cache Management

### When to Clear Cache
- After modifying test cases
- After updating expected outputs
- After significant changes to the MCP tools
- When you want to re-validate all tests

### Cache Location
The cache is stored in:
```
MARRVEL_MCP/
├── .cache/
│   └── mcp-llm-test/
│       ├── {hash1}.json
│       ├── {hash2}.json
│       └── ...
```

### Cache Size
Each cached result is typically 1-10 KB, so even with many test cases, cache size remains small.
