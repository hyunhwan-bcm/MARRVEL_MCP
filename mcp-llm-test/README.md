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

## Quick Start

```bash
cd mcp-llm-test

# Run all test cases (uses cache for faster execution)
python evaluate_mcp.py

# Run with fresh evaluation (ignore cache)
python evaluate_mcp.py --force

# Run specific test cases only
python evaluate_mcp.py --subset "Gene for NM_001045477.4:c.187C>T" "CADD phred score"
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

#### `--force`

Force re-evaluation of all test cases, ignoring any cached results.

**When to use:**
- Testing changes to the MCP server or tools
- Verifying consistency of results
- Updating cache with fresh evaluations without deleting old cache first
- Running evaluations after API or model updates

**Example:**
```bash
python evaluate_mcp.py --force
```

**Difference from `--clear`:**
- `--clear`: Deletes cache, then runs evaluations
- `--force`: Ignores cache but overwrites it with new results

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

# Combine with --force for fresh evaluation
python evaluate_mcp.py --force --subset "Gene for NM_001045477.4:c.187C>T"
```

**Notes:**
- Test names must match exactly as they appear in `test_cases.yaml`
- Warnings are shown for non-existent test names
- Cached results are still used for subset runs unless `--force` is specified

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
   - By default, cached results are used if available
   - Cache is automatically created on first run
   - Each test case is cached independently
   - Failed evaluations and errors are NOT cached

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

| Scenario | Cache Used? | Notes |
|----------|-------------|-------|
| Default run | ✅ Yes | Fastest execution |
| `--force` flag | ❌ No | Ignores cache, overwrites with new results |
| `--clear` flag | ❌ No | Deletes cache first, then runs fresh |
| `--subset` flag | ✅ Yes | Only for selected tests (unless `--force` is used) |
| First run | ❌ No | No cache exists yet |
| Test case modified | ⚠️ Yes | Cache doesn't detect changes - use `--force` |

### Cache Invalidation

The cache **does not** automatically detect changes to:
- Test case inputs or expected results
- MCP server code or tools
- API endpoints or responses
- LLM model behavior

**Best practice:** Use `--clear` or `--force` after making changes to ensure accurate results.

## Usage Examples

### Routine Testing

```bash
# Daily check - fast, uses cache
python evaluate_mcp.py

# After making changes to MCP tools
python evaluate_mcp.py --force

# Test a specific feature you're working on
python evaluate_mcp.py --subset "Gene for NM_001045477.4:c.187C>T" "Protein change for NM_001045477.4:c.187C>T"
```

### Development Workflow

```bash
# 1. Clear cache and establish baseline
python evaluate_mcp.py --clear

# 2. Make changes to MCP server/tools
# ... edit server.py or tool files ...

# 3. Test specific affected functionality
python evaluate_mcp.py --force --subset "DGV entries" "DECIPHER control variants"

# 4. Run full suite with fresh evaluation
python evaluate_mcp.py --force
```

### Debugging Failures

```bash
# 1. Identify failing test from report
# ... open HTML report and find failing test ...

# 2. Re-run failing test with fresh evaluation
python evaluate_mcp.py --force --subset "NUTM2G OMIM entries"

# 3. Check the detailed conversation history in the HTML report
```

### Performance Optimization

```bash
# First run - takes ~5-10 minutes for all tests
python evaluate_mcp.py --clear

# Subsequent runs - takes seconds with cache
python evaluate_mcp.py

# Quick validation of critical tests
python evaluate_mcp.py --subset "Gene for NM_001045477.4:c.187C>T" "CADD phred score" "REVEL prediction"
```

### CI/CD Integration

```bash
# Run in CI with fresh evaluation (no cache)
python evaluate_mcp.py --force

# Or clear cache explicitly
python evaluate_mcp.py --clear
```

## Best Practices

### For Routine Testing

1. **Use cache by default**: Let the tool use cached results for fast feedback
   ```bash
   python evaluate_mcp.py
   ```

2. **Clear cache periodically**: Start fresh weekly or after major changes
   ```bash
   python evaluate_mcp.py --clear
   ```

3. **Review HTML reports**: Check conversation history for unexpected tool calls or responses

### For Development

1. **Use `--subset` for iteration**: Focus on specific tests during development
   ```bash
   python evaluate_mcp.py --subset "Gene for NM_001045477.4:c.187C>T"
   ```

2. **Use `--force` after changes**: Ensure fresh evaluation after modifying code
   ```bash
   python evaluate_mcp.py --force --subset "affected_test"
   ```

3. **Validate with full suite**: Run complete evaluation before committing
   ```bash
   python evaluate_mcp.py --force
   ```

### For Debugging

1. **Start with cached run**: Quickly identify which tests are failing
2. **Re-run failed tests**: Use `--subset` with `--force` for detailed debugging
3. **Check conversation logs**: Review full conversation JSON in HTML report
4. **Isolate issues**: Run related tests together to find patterns

### For Production/CI

1. **Always use `--force` or `--clear`**: Ensure fresh evaluation in CI
2. **Save artifacts**: Keep HTML reports and cache for debugging
3. **Set timeouts**: Consider evaluation time in CI pipeline (5-10 min without cache)
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

### Issue: Cache not being used

**Causes:**
- Using `--force` flag
- First run (no cache exists)
- Cache files were deleted

**Solution:** Remove `--force` flag to enable cache usage

### Issue: Stale cached results

**Solution:**
```bash
python evaluate_mcp.py --force
```

### Issue: Test takes too long

**Solutions:**
1. Use cache: `python evaluate_mcp.py` (fast)
2. Run subset: `python evaluate_mcp.py --subset "specific_test"`
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
        run: |
          cd mcp-llm-test
          python evaluate_mcp.py --force

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
