# MCP LLM Test Suite

This directory contains the LLM-based evaluation suite for testing MARRVEL MCP tools.

## Overview

The `evaluate_mcp.py` script evaluates MCP tools using LangChain and LLM agents to answer genetics-related questions and compares the responses against expected answers.

## Requirements

- Python 3.8+
- OpenRouter API key (set as `OPENROUTER_API_KEY` environment variable)
- All dependencies from `requirements.txt`

## Usage

### Run All Test Cases

```bash
cd mcp-llm-test
python evaluate_mcp.py
```

### Run a Subset of Test Cases

You can run specific test cases using the `--subset` parameter:

```bash
# Run test cases 1 through 5
python evaluate_mcp.py --subset 1-5

# Run specific test cases (1, 2, and 4)
python evaluate_mcp.py --subset 1,2,4

# Run a combination of ranges and individual indices
python evaluate_mcp.py --subset 1-3,5,7-9

# Run a single test case
python evaluate_mcp.py --subset 1
```

### View Help

```bash
python evaluate_mcp.py --help
```

## Test Cases

Test cases are defined in `test_cases.yaml`. Each test case includes:
- **name**: A descriptive name for the test
- **input**: The question to ask the LLM agent
- **expected**: The expected answer or key information

## Output

The script generates an HTML report with:
- Success rate summary
- Individual test results with pass/fail status
- Full conversation history with tool calls
- Token usage statistics

The report is automatically opened in your default browser when evaluation completes.

## Subset Parameter

The `--subset` parameter accepts:
- **Ranges**: `1-5` (test cases 1 through 5, inclusive)
- **Individual indices**: `1,2,4` (specific test cases)
- **Combinations**: `1-3,5,7-9` (mix of ranges and individual indices)

Notes:
- Indices are 1-based (first test case is 1, not 0)
- Indices must be within the valid range (1 to total number of test cases)
- Invalid indices or formats will result in an error message

## Examples

```bash
# Run only the first test case
python evaluate_mcp.py --subset 1

# Run the first 10 test cases
python evaluate_mcp.py --subset 1-10

# Run test cases 1-5, 10, and 15-20
python evaluate_mcp.py --subset 1-5,10,15-20
```
