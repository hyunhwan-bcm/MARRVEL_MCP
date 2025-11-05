# MCP LLM Evaluation

This directory contains the LLM-based evaluation framework for testing MARRVEL MCP tools using LangChain and OpenRouter.

## Overview

The `evaluate_mcp.py` script evaluates MCP tools by:
- Running test cases defined in `test_cases.yaml`
- Using LangChain with OpenRouter API to interact with the MCP tools
- Evaluating responses against expected outputs
- Generating an HTML report with detailed results

## Prerequisites

1. Set your OpenRouter API key:
```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

Or create a `.env` file in the project root:
```
OPENROUTER_API_KEY=your-api-key-here
```

2. Install dependencies:
```bash
pip install -r ../requirements.txt
```

## Usage

### Basic Usage (with caching)

Run all test cases, using cached results for previously successful tests:

```bash
cd mcp-llm-test
python evaluate_mcp.py
```

The script will:
- Load test cases from `test_cases.yaml`
- Check the `.cache` directory for successful results
- Only re-run tests that failed previously or haven't been cached
- Generate an HTML report and open it in your browser

### Force Rerun All Tests

Ignore the cache and run all tests:

```bash
python evaluate_mcp.py --force
```

### Clear Cache

Clear the cache before running tests:

```bash
python evaluate_mcp.py --clear
```

### Run Specific Tests

Run only a subset of test cases:

```bash
# Run test 1 only
python evaluate_mcp.py --subset 1

# Run tests 1, 2, and 4
python evaluate_mcp.py --subset 1,2,4

# Run tests 1 through 5
python evaluate_mcp.py --subset 1-5

# Mixed format
python evaluate_mcp.py --subset 1,3-5,8
```

### Combine Options

You can combine multiple flags:

```bash
# Clear cache and run only tests 1-5
python evaluate_mcp.py --clear --subset 1-5

# Force rerun of tests 1-3
python evaluate_mcp.py --force --subset 1-3
```

## Caching

### How Caching Works

- **Cache Location**: `.cache/test_results.json`
- **What's Cached**: Only successful test results (where the LLM evaluation returns "yes")
- **When Cache is Used**: By default, cached results are used for successful tests
- **When Cache is Ignored**: 
  - When using `--force` flag
  - When a test previously failed (it will be re-run)

### Benefits

- **Faster iterations**: Skip successful tests when debugging failures
- **Cost savings**: Reduce API calls to OpenRouter
- **Consistent results**: Previously successful tests don't need re-evaluation

### Cache Management

The cache is automatically updated after each run:
- New successful results are added
- Failed results are not cached (will be re-run next time)

To manually manage the cache:
```bash
# View cache contents
cat .cache/test_results.json

# Remove cache
rm -rf .cache

# Or use the --clear flag
python evaluate_mcp.py --clear
```

## Test Cases

Test cases are defined in `test_cases.yaml`. Each test case has:
- `name`: A descriptive name for the test
- `input`: The question/query to send to the LLM
- `expected`: The expected response or answer

Example:
```yaml
- case:
    name: "Gene for NM_001045477.4:c.187C>T"
    input: "What gene is associated with the variant NM_001045477.4:c.187C>T?"
    expected: "The gene associated is NUTM2G."
```

## HTML Report

After running, an HTML report is automatically generated and opened in your browser. The report includes:
- Success rate and summary statistics
- Pass/Fail status for each test
- Question, expected answer, and actual response
- Tool calls made during evaluation
- Full conversation JSON for debugging
- Token usage statistics

## Architecture

The evaluation script uses:
- **LangChain v1**: For LLM integration and tool calling
- **OpenRouter**: API gateway for accessing various LLMs (default: Google Gemini 2.5 Flash)
- **FastMCP**: For MCP server and client communication
- **Async execution**: Tests run concurrently (4 at a time by default)

## Troubleshooting

### API Key Issues

If you see `OPENROUTER_API_KEY not found`:
1. Make sure you've set the environment variable or created a `.env` file
2. Verify the key is valid
3. Try running `echo $OPENROUTER_API_KEY` to check if it's set

### Test Failures

If tests are failing:
1. Use `--subset` to run specific tests for debugging
2. Check the HTML report for detailed error messages
3. Review the conversation JSON to see tool calls and responses
4. Verify the MCP server is working: `python ../server.py`

### Cache Issues

If cached results seem incorrect:
1. Clear the cache: `python evaluate_mcp.py --clear`
2. Force rerun: `python evaluate_mcp.py --force`
3. Manually inspect: `cat .cache/test_results.json`

## Development

To add new test cases:
1. Edit `test_cases.yaml`
2. Add your test case following the existing format
3. Run the evaluation

To modify the evaluation logic:
1. Edit `evaluate_mcp.py`
2. Run tests: `pytest ../tests/test_caching_functionality.py`
3. Format code: `black evaluate_mcp.py`
