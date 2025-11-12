# MCP LLM Evaluation Tool

A comprehensive evaluation framework for testing MARRVEL-MCP tools using LangChain and OpenRouter. This tool evaluates the accuracy and reliability of MCP tools by running test cases and comparing actual responses against expected outcomes.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Command-Line Interface](#command-line-interface)
- [Caching System](#caching-system)
- [Usage Examples](#usage-examples)
- [Best Practices](#best-practices)
- [Test Cases](#test-cases)
- [Output and Reports](#output-and-reports)

## Overview

The `evaluate_mcp.py` script provides:
- **Automated Testing**: Run test cases defined in `test_cases.yaml`
- **LLM-based Evaluation**: Uses LangChain with OpenRouter for intelligent tool calling
- **Caching**: Smart caching system to avoid redundant API calls
- **HTML Reports**: Beautiful HTML reports with conversation history
- **Flexible Execution**: Run all tests, specific subsets, or force fresh evaluations

## Installation

1. Install dependencies:
```bash
cd MARRVEL_MCP
pip install -r requirements.txt
```

2. Set up your OpenRouter API key:
```bash
# Create a .env file in the project root
echo "OPENROUTER_API_KEY=your_key_here" > .env

# Or export as environment variable
export OPENROUTER_API_KEY="your_key_here"
```

Get your API key from [OpenRouter](https://openrouter.ai/).

### (Optional) Choose specific OpenRouter models

The evaluation system uses two separate models:

1. **Tested Model** - The model being evaluated for tool calling and response quality
   - Default: `google/gemini-2.5-flash`
   - Configure via: `OPENROUTER_MODEL` environment variable

2. **Evaluator Model** - The model used to judge and classify responses for consistency
   - Default: `google/gemini-2.5-pro`
   - Configure via: `EVALUATOR_MODEL` environment variable

This separation ensures consistent evaluation across different tested models.

```bash
# Test Claude with Gemini Pro as evaluator (default evaluator)
export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
python evaluate_mcp.py

# Test GPT-4o with Claude as evaluator
export OPENROUTER_MODEL="openai/gpt-4o"
export EVALUATOR_MODEL="anthropic/claude-3.5-sonnet"
python evaluate_mcp.py

# Use defaults (Gemini Flash tested, Gemini Pro evaluates)
python evaluate_mcp.py
```

If these environment variables are not set, the tool uses the defaults listed above.

## Quick Start

```bash
cd mcp-llm-test

# Run all test cases (fresh evaluation, results cached automatically)
python evaluate_mcp.py

# Use cached results (re-run only failed tests)
python evaluate_mcp.py --cache

# Run specific test cases by index
python evaluate_mcp.py --subset "1-5"
```

## Command-Line Interface

### Synopsis

```bash
python evaluate_mcp.py [OPTIONS]
```

### Options

#### `--clear`

Clear the evaluation cache before running tests.

**When to use:**
- Starting a fresh evaluation session
- After updating test cases or expected results
- When you suspect cache corruption
- Before generating baseline results for documentation

**Example:**
```bash
python evaluate_mcp.py --clear
```

**Impact:**
- Removes all cached results from `~/.cache/marrvel-mcp/evaluations/`
- Next run will re-evaluate all test cases from scratch
- Cache will be repopulated with new results

---

#### `--cache`

Use cached results from previous runs and re-run only failed test cases.

**When to use:**
- Quick validation runs to save time and API costs
- Re-running after fixing issues (only failed tests will be re-evaluated)
- Continuous development workflow where most tests pass
- Checking if previous failures have been resolved

**Example:**
```bash
python evaluate_mcp.py --cache
```

**Behavior:**
- Successful cached results are reused
- Failed tests (classification starts with "no" or contains "Error") are automatically re-run
- Results are always saved to cache after evaluation
- Without `--cache`, all tests are re-evaluated from scratch

**Difference from default:**
- Default (no flag): Re-runs all tests, updates cache
- `--cache`: Uses successful cached results, re-runs only failures

---

#### `--subset TEST_NAME [TEST_NAME ...]`

Run only specific test cases by name.

**When to use:**
- Debugging specific failing test cases
- Quick validation of recently modified functionality
- Running expensive test cases selectively
- Iterative development and testing

**Example:**
```bash
# Run a single test
python evaluate_mcp.py --subset "Gene for NM_001045477.4:c.187C>T"

# Run multiple tests
python evaluate_mcp.py --subset "CADD phred score" "REVEL prediction" "PolyPhen-2 prediction"

# Combine with --cache to use cached results for these tests
python evaluate_mcp.py --cache --subset "Gene for NM_001045477.4:c.187C>T"
```

**Notes:**
- Test names must match exactly as they appear in `test_cases.yaml`
- Warnings are shown for non-existent test names
- Use `--cache` with subset to reuse successful cached results

---

### Getting Help

```bash
# Show help message with all options
python evaluate_mcp.py --help

# View available test case names
cat test_cases.yaml | grep "name:"
```

## Caching System

### How Caching Works

The evaluation tool implements a **file-based caching system** to improve performance and reduce API costs:

1. **Cache Location**: `~/.cache/marrvel-mcp/evaluations/`
   - On macOS/Linux: `~/.cache/marrvel-mcp/evaluations/`
   - On Windows: `%USERPROFILE%\.cache\marrvel-mcp\evaluations\`

2. **Cache Files**: Each test case result is stored in a separate pickle file
   - Filename format: `<sanitized_test_name>.pkl`
   - Example: `Gene_for_NM_001045477.4_c.187C_T.pkl`

3. **What's Cached**:
   - LLM responses
   - Tool call history
   - Full conversation history
   - Evaluation classifications
   - Token usage statistics

4. **Cache Behavior**:
   - Results are **always saved** to cache after every run (automatic)
   - Use `--cache` flag to **read** from cache (opt-in)
   - When `--cache` is enabled, failed tests are automatically re-run
   - Each test case is cached independently
   - Without `--cache`, all tests run fresh but results are still cached

### Cache Management

**View cache location:**
```bash
# On macOS/Linux
ls -lh ~/.cache/marrvel-mcp/evaluations/

# On Windows (PowerShell)
dir $env:USERPROFILE\.cache\marrvel-mcp\evaluations\
```

**Manually clear cache:**
```bash
# On macOS/Linux
rm -rf ~/.cache/marrvel-mcp/evaluations/*

# On Windows (PowerShell)
Remove-Item -Recurse $env:USERPROFILE\.cache\marrvel-mcp\evaluations\*
```

**Check cache size:**
```bash
# On macOS/Linux
du -sh ~/.cache/marrvel-mcp/evaluations/

# On Windows (PowerShell)
(Get-ChildItem -Recurse $env:USERPROFILE\.cache\marrvel-mcp\evaluations\ | Measure-Object -Property Length -Sum).Sum / 1MB
```

### When Cache is Used

| Scenario | Cache Read? | Cache Written? | Notes |
|----------|-------------|----------------|-------|
| Default run | ❌ No | ✅ Yes | All tests run fresh, results saved |
| `--cache` flag | ✅ Yes | ✅ Yes | Reuses successful results, re-runs failures |
| `--clear` flag | ❌ No | ✅ Yes | Deletes cache first, then runs fresh |
| `--subset` flag | ❌ No | ✅ Yes | Selected tests only (add `--cache` to read cache) |
| First run | ❌ No | ✅ Yes | No cache exists yet, creates cache |
| Failed test | ♻️ Re-run | ✅ Yes | Failed tests are re-run even with `--cache` |

### Cache Invalidation

The cache **does not** automatically detect changes to:
- Test case inputs or expected results
- MCP server code or tools
- API endpoints or responses
- LLM model behavior

**Best practice:** Run without `--cache` flag (default behavior) after making changes to ensure accurate results. The `--cache` flag is best used for quick validation when you know the code hasn't changed.

## Usage Examples

### Routine Testing

```bash
# Quick check using cached results (fast, re-runs only failures)
python evaluate_mcp.py --cache

# After making changes to MCP tools (fresh evaluation)
python evaluate_mcp.py

# Test a specific feature you're working on
python evaluate_mcp.py --subset "1-5"
```

### Development Workflow

```bash
# 1. Establish baseline (fresh run, results cached)
python evaluate_mcp.py

# 2. Make changes to MCP server/tools
# ... edit server.py or tool files ...

# 3. Quick check to see if anything broke
python evaluate_mcp.py --cache

# 4. Test specific affected functionality with fresh evaluation
python evaluate_mcp.py --subset "1-5"

# 5. Run full suite with fresh evaluation before committing
python evaluate_mcp.py
```

### Debugging Failures

```bash
# 1. Run with cache to quickly identify which tests are failing
python evaluate_mcp.py --cache

# 2. Re-run specific failing test with fresh evaluation
python evaluate_mcp.py --subset "5"

# 3. Check the detailed conversation history in the HTML report
```

### Performance Optimization

```bash
# First run - establishes cache baseline (~5-10 minutes)
python evaluate_mcp.py

# Quick validation using cache - takes seconds (re-runs only failures)
python evaluate_mcp.py --cache

# Quick validation of specific tests
python evaluate_mcp.py --subset "1-3"
```

### CI/CD Integration

```bash
# Run in CI with fresh evaluation (default behavior)
python evaluate_mcp.py

# Or clear cache explicitly first
python evaluate_mcp.py --clear
```

## Best Practices

### For Routine Testing

1. **Use cache for quick checks**: Use `--cache` flag for fast feedback
   ```bash
   python evaluate_mcp.py --cache
   ```

2. **Run fresh after changes**: Default behavior re-runs all tests
   ```bash
   python evaluate_mcp.py
   ```

3. **Review HTML reports**: Check conversation history for unexpected tool calls or responses

### For Development

1. **Use `--subset` for iteration**: Focus on specific tests during development
   ```bash
   python evaluate_mcp.py --subset "1-5"
   ```

2. **Quick validation with cache**: Check if changes broke anything
   ```bash
   python evaluate_mcp.py --cache
   ```

3. **Validate with full suite**: Run complete fresh evaluation before committing
   ```bash
   python evaluate_mcp.py
   ```

### For Debugging

1. **Start with cached run**: Quickly identify which tests are failing
2. **Re-run failed tests**: Use `--subset` for fresh evaluation and detailed debugging
3. **Check conversation logs**: Review full conversation JSON in HTML report
4. **Isolate issues**: Run related tests together to find patterns

### For Production/CI

1. **Use default behavior**: Fresh evaluation is the default (no flag needed)
2. **Save artifacts**: Keep HTML reports for debugging
3. **Set timeouts**: Consider evaluation time in CI pipeline (5-10 min for full suite)
4. **Monitor API costs**: Track token usage in HTML reports

## Test Cases

Test cases are defined in `test_cases.yaml`. Each test case includes:

```yaml
- case:
    name: "Descriptive test name"
    input: "Question or prompt for the LLM"
    expected: "Expected response or outcome"
```

### Adding New Test Cases

1. Edit `test_cases.yaml`
2. Add a new case with unique name
3. Provide clear input and expected output
4. Run with `--subset` to test the new case
5. Review and iterate until the test passes

### Test Case Best Practices

- **Specific names**: Use descriptive names that clearly identify what's being tested
- **Clear expectations**: Expected outputs should be unambiguous
- **Realistic inputs**: Use actual queries that users might ask
- **Independent tests**: Each test should be self-contained

## Output and Reports

### HTML Report

After each run, an HTML report is automatically generated and opened in your browser:

**Features:**
- ✅/❌ Pass/fail indicators for each test
- 📊 Success rate summary
- 💬 Full conversation history (click to expand)
- 🔧 Tool call details
- 📈 Token usage statistics

**Report location:** Temporary file in system temp directory (auto-opens in browser)

### Console Output

During execution, the console shows:
```
📋 Running subset: 3/21 test cases
--- Running: Gene for NM_001045477.4:c.187C>T ---
  Available tools: 32
--- Finished: Gene for NM_001045477.4:c.187C>T ---
--- Using cached result: CADD phred score ---
```

### Cache Messages

- `✅ Cache cleared:` - Cache was successfully cleared
- `--- Using cached result:` - Test used cached result
- `⚠️ Warning: The following test names were not found:` - Subset names don't match

## Troubleshooting

### Issue: "OPENROUTER_API_KEY not found"

**Solution:**
```bash
echo "OPENROUTER_API_KEY=your_key_here" > .env
```

### Issue: Want to use cached results

**Solution:** Add the `--cache` flag
```bash
python evaluate_mcp.py --cache
```

**Note:** Cache usage is opt-in. Without `--cache`, all tests run fresh.

### Issue: Stale cached results

**Solution:** Run without `--cache` flag (default behavior)
```bash
python evaluate_mcp.py
```

### Issue: Test takes too long

**Solutions:**
1. Use cache: `python evaluate_mcp.py --cache` (fast)
2. Run subset: `python evaluate_mcp.py --subset "1-5"`
3. Check network connectivity and API rate limits

### Issue: All tests failing

**Causes:**
- MCP server not running properly
- API connectivity issues
- Invalid API key

**Solution:**
1. Verify API key in `.env`
2. Check network connectivity
3. Test MCP server independently

## Advanced Usage

### Custom Cache Location

The cache location is defined in `evaluate_mcp.py`:
```python
CACHE_DIR = Path.home() / ".cache" / "marrvel-mcp" / "evaluations"
```

To use a custom location, modify this line before running.

### Integrating with CI/CD

Example GitHub Actions workflow:

```yaml
name: MCP Evaluation

on: [push, pull_request]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run MCP evaluation
        env:
          OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}
               # Optional: pin a specific model for CI
               # OPENROUTER_MODEL: "google/gemini-2.5-flash"
        run: |
          cd mcp-llm-test
          python evaluate_mcp.py

      - name: Upload report
        uses: actions/upload-artifact@v3
        with:
          name: evaluation-report
          path: /tmp/evaluation_results_*.html
```

## Related Documentation

- [Main README](../README.md) - Project overview and setup
- [API Documentation](../API_DOCUMENTATION.md) - MCP tool reference
- [Test Suite Documentation](../tests/README.md) - Unit and integration tests

## Support

For issues or questions:
- Open an issue on GitHub
- Check existing test cases in `test_cases.yaml` for examples
- Review HTML reports for detailed conversation logs
