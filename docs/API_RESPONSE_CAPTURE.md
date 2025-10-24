# API Response Capture Guide

This guide explains how to capture and view MARRVEL API responses during test execution.

## Overview

The API response capture system automatically logs all API calls made during integration tests, including:
- Test name
- Tool name
- API endpoint
- Input parameters
- JSON output
- Success/failure status
- Timestamp

## How It Works

### 1. Automatic Capture in Tests

Use the `api_capture` fixture in your integration tests:

```python
import pytest
from src.utils.api_client import fetch_marrvel_data


@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_gene_api_with_capture(api_capture):
    """Test gene API endpoint and capture the response."""
    entrez_id = "7157"
    endpoint = f"/gene/entrezId/{entrez_id}"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # Log the successful API response
        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=result,
            status="success",
            return_code=return_code,
        )

        assert result is not None

    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        # Log errors too
        api_capture.log_response(
            tool_name="get_gene_by_entrez_id",
            endpoint=endpoint,
            input_data={"entrez_id": entrez_id},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise
```

### 2. Running Tests Locally

Run integration tests to capture API responses:

```bash
# Run all integration tests
pytest tests/ -m integration_api -v

# Run specific test file
pytest tests/integration/api/test_api_capture_example.py -v

# Check the output
ls -la test-output/
```

After running tests, you'll find:
- `test-output/api_responses.json` - Structured JSON data
- `test-output/api_responses.md` - Human-readable markdown table

### 3. Viewing Results Locally

#### JSON Output
```bash
# View the JSON file
cat test-output/api_responses.json | python -m json.tool

# Or use jq for better formatting
cat test-output/api_responses.json | jq '.'
```

#### Markdown Output
```bash
# View the markdown file
cat test-output/api_responses.md

# Or use a markdown viewer
open test-output/api_responses.md
```

## GitHub Integration

### In Pull Requests

When you create a PR, the CI workflow automatically:

1. **Runs Integration Tests** - Executes all `@pytest.mark.integration_api` tests
2. **Captures API Responses** - Logs all API calls and responses
3. **Generates Reports** - Creates both JSON and Markdown formats
4. **Uploads Artifacts** - Saves to GitHub for download
5. **Posts PR Comment** - Adds a table of responses to the PR
6. **Updates Summary** - Displays in the Actions summary page

### Viewing in GitHub

#### Option 1: PR Comment (Automatic)

The CI will automatically post a comment on your PR with a table like:

```markdown
# MARRVEL API Test Responses

**Total API Calls:** 5
**Generated:** 2025-10-22 10:30:45 UTC

## Summary Table

| Test Name | Tool | Endpoint | Input | Output Preview | # Output Keys | Return Code | Status |
|-----------|------|----------|-------|----------------|---------------|-------------|--------|
| test_gene_api_with_capture | get_gene_by_entrez_id | /gene/entrezId/7157 | `{"entrez_id": "7157"}` | {symbol, entrezId, name, chromosome, +11 more} | 15 | 200 | ✅ |
| test_variant_api_with_capture | get_variant_dbnsfp | /variant/dbnsfp/17-7577121-C-T | `{"variant": "17-7577121-C-T"}` | {chromosome, position, ref, alt, +16 more} | 20 | 200 | ✅ |
| test_error_example | get_gene_by_entrez_id | /gene/entrezId/invalid |`{"entrez_id": "invalid"}` |  | 0 | 404 | ❌ |
...
```

**Note:** Error cases show empty output preview (no error messages in table). The Return Code column shows HTTP status codes or "N/A" for network errors.

**Output:**
```json
{
  "symbol": "TP53",
  "entrezId": "7157",
  "name": "tumor protein p53",
  ...
}
```

#### Option 2: GitHub Actions Summary

1. Go to your PR
2. Click on "Checks" tab
3. Select the "CI" workflow
4. Click on the "Run Tests (Python 3.13)" job
5. Scroll to the bottom to see the summary

#### Option 3: Download Artifacts

1. Go to the Actions tab in GitHub
2. Click on the workflow run
3. Scroll to "Artifacts" section at the bottom
4. Download `test-reports-py3.13`
5. Extract and open `test-output/api_responses.md`

### Example Artifact Contents

The artifact will contain:
```
test-reports-py3.13/
├── test-report-unit-3.13.html       # HTML test report
├── test-report-unit-3.13.json       # JSON test report
├── test-report-integration-3.13.html
├── test-report-integration-3.13.json
├── junit-unit-3.13.xml              # JUnit format
├── junit-integration-3.13.xml
├── coverage-3.13.xml                # Coverage report
├── htmlcov-3.13/                    # Coverage HTML
│   └── index.html
└── test-output/
    ├── api_responses.json           # ← API responses (JSON)
    └── api_responses.md             # ← API responses (Markdown)
```

## Output Format Changes (v2)

**What's New:**
- **Return Code Column**: Shows HTTP status codes (200, 404, 500) or "N/A" for network errors
- **Suppressed Error Messages**: Error messages are no longer shown in the "Output Preview" column to prevent markdown table formatting issues
- **Clean Tables**: Tables now render properly regardless of error message content

**Benefits:**
- Markdown tables never break due to special characters in error messages
- Clearer separation between successful JSON output and error status
- Return codes provide quick insight into failure types (404, 500, network, etc.)

### JSON Format (`api_responses.json`)

```json
{
  "total_api_calls": 5,
  "generated_at": "2025-10-22T10:30:45.123Z",
  "test_session": {
    "exit_status": 0
  },
  "api_calls": [
    {
      "test_name": "tests/integration/api/test_api_capture_example.py::test_gene_api_with_capture",
      "tool_name": "get_gene_by_entrez_id",
      "endpoint": "/gene/entrezId/7157",
      "input": {
        "entrez_id": "7157"
      },
      "output": {
        "symbol": "TP53",
        "entrezId": "7157",
        "name": "tumor protein p53",
        ...
      },
      "status": "success",
      "error": null,
      "return_code": "200",
      "timestamp": "2025-10-22T10:30:45.123Z"
    },
    ...
  ]
}
```

### Markdown Format (`api_responses.md`)

See example above in "Option 1: PR Comment".

## Best Practices

### 1. Always Capture Responses in Integration Tests

```python
@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_my_api(api_capture):  # ← Include api_capture fixture
    try:
        result = await fetch_marrvel_data("/some/endpoint")

        # Extract return code if available
        return_code = None
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])
        else:
            return_code = "200"

        # ✅ Always log successful calls
        api_capture.log_response(
            tool_name="my_tool",
            endpoint="/some/endpoint",
            input_data={"param": "value"},
            output_data=result,
            status="success",
            return_code=return_code,
        )
    except Exception as e:
        # Extract return code from HTTPStatusError if available
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        # ✅ Always log errors too
        api_capture.log_response(
            tool_name="my_tool",
            endpoint="/some/endpoint",
            input_data={"param": "value"},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise
```

### 2. Use Descriptive Tool Names

```python
# ✅ Good - matches actual tool function name
api_capture.log_response(tool_name="get_gene_by_entrez_id", ...)

# ❌ Bad - vague
api_capture.log_response(tool_name="gene_test", ...)
```

### 3. Include All Input Parameters

```python
# ✅ Good - all parameters documented
api_capture.log_response(
    tool_name="get_diopt_orthologs",
    endpoint=f"/diopt/ortholog/gene/entrezId/{entrez_id}",
    input_data={
        "entrez_id": entrez_id,
        "gene_symbol": gene_symbol,
        "taxon_id": taxon_id,
    },
    ...
)
```

### 4. Handle Large Responses

The system automatically handles large JSON responses. No need to truncate manually.

## Troubleshooting

### No API responses captured?

Check:
1. Are you using the `api_capture` fixture?
2. Are you running integration tests (`-m integration_api`)?
3. Did the tests actually execute (not skipped)?

### File not found?

```bash
# Create the directory if needed
mkdir -p test-output

# Run tests again
pytest tests/ -m integration_api -v
```

### PR comment too large?

The system automatically truncates comments > 65KB. Full output is always in artifacts.

## Advanced Usage

### Custom Response Processing

```python
@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_with_custom_processing(api_capture):
    result = await fetch_marrvel_data("/gene/entrezId/7157")

    # Extract specific fields
    simplified_output = {
        "symbol": result.get("symbol"),
        "entrezId": result.get("entrezId"),
        "summary": result.get("summary", "")[:200],  # First 200 chars
    }

    api_capture.log_response(
        tool_name="get_gene_by_entrez_id",
        endpoint="/gene/entrezId/7157",
        input_data={"entrez_id": "7157"},
        output_data=simplified_output,  # ← Simplified version
        status="success",
    )
```

### Programmatic Access

```python
import json

# Load captured responses
with open("test-output/api_responses.json") as f:
    data = json.load(f)

# Analyze responses
for call in data["api_calls"]:
    print(f"Tool: {call['tool_name']}")
    print(f"Status: {call['status']}")
    print(f"Response keys: {list(call['output'].keys())}")
```

## Summary

- ✅ Use `api_capture` fixture in integration tests
- ✅ Log both successes and failures
- ✅ Check PR comments for automatic summaries
- ✅ Download artifacts for full JSON/Markdown output
- ✅ View in GitHub Actions summary

For questions or issues, see [CONTRIBUTING.md](../CONTRIBUTING.md).
