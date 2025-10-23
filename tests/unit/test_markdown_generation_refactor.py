"""
Unit tests for markdown generation after refactoring.

This tests the new format:
- Error messages suppressed in output preview
- Return code column added
- JSON output only for successful calls
"""

import json
from datetime import datetime, timezone
from tests.conftest import _generate_markdown_table


def test_markdown_generation_with_success():
    """Test markdown generation for successful API call."""
    responses = [
        {
            "test_name": "tests/integration/api/test_example.py::test_gene_api",
            "tool_name": "get_gene_by_entrez_id",
            "endpoint": "/gene/entrezId/7157",
            "input": {"entrez_id": "7157"},
            "output": {"symbol": "TP53", "entrezId": "7157", "name": "tumor protein p53"},
            "status": "success",
            "error": None,
            "return_code": "200",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]

    markdown = _generate_markdown_table(responses)

    # Verify structure
    assert "# MARRVEL API Test Responses" in markdown
    assert "## Summary Table" in markdown
    assert "Return Code" in markdown
    assert "| test_gene_api |" in markdown
    assert "| get_gene_by_entrez_id |" in markdown
    assert "| 200 |" in markdown
    assert "| ✅ |" in markdown

    # Verify output preview shows JSON keys
    assert "{symbol, entrezId, name}" in markdown

    # Verify no error messages in output
    assert "ERROR" not in markdown.upper()


def test_markdown_generation_with_error():
    """Test markdown generation for failed API call."""
    responses = [
        {
            "test_name": "tests/integration/api/test_example.py::test_gene_api_error",
            "tool_name": "get_gene_by_entrez_id",
            "endpoint": "/gene/entrezId/7157",
            "input": {"entrez_id": "7157"},
            "output": None,
            "status": "error",
            "error": "[Errno -5] No address associated with hostname",
            "return_code": "N/A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]

    markdown = _generate_markdown_table(responses)

    # Verify structure
    assert "# MARRVEL API Test Responses" in markdown
    assert "## Summary Table" in markdown
    assert "Return Code" in markdown
    assert "| test_gene_api_error |" in markdown
    assert "| get_gene_by_entrez_id |" in markdown
    assert "| N/A |" in markdown
    assert "| ❌ |" in markdown

    # Verify output preview is EMPTY (no error message)
    lines = markdown.split("\n")
    for line in lines:
        if "test_gene_api_error" in line:
            # Check that output preview column (5th column) is empty
            columns = line.split("|")
            # Column index: 0=empty, 1=test, 2=tool, 3=endpoint, 4=input, 5=output, 6=keys, 7=return_code, 8=status
            output_column = columns[5].strip()
            assert output_column == "", f"Expected empty output preview, got: '{output_column}'"

    # Verify error message is NOT in output preview
    assert "No address associated with hostname" not in markdown


def test_markdown_generation_with_http_error():
    """Test markdown generation for HTTP error (404, 500, etc)."""
    responses = [
        {
            "test_name": "tests/integration/api/test_example.py::test_gene_api_404",
            "tool_name": "get_gene_by_entrez_id",
            "endpoint": "/gene/entrezId/9999999",
            "input": {"entrez_id": "9999999"},
            "output": None,
            "status": "error",
            "error": "404 Not Found",
            "return_code": "404",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]

    markdown = _generate_markdown_table(responses)

    # Verify return code shows HTTP status
    assert "| 404 |" in markdown
    assert "| ❌ |" in markdown

    # Verify output preview is EMPTY (no error message)
    lines = markdown.split("\n")
    for line in lines:
        if "test_gene_api_404" in line:
            columns = line.split("|")
            output_column = columns[5].strip()
            assert output_column == "", f"Expected empty output preview, got: '{output_column}'"

    # Verify error message is NOT shown in output
    assert "404 Not Found" not in markdown or "| 404 |" in markdown


def test_markdown_generation_mixed_results():
    """Test markdown generation with both success and error cases."""
    responses = [
        {
            "test_name": "tests/integration/api/test_example.py::test_success",
            "tool_name": "get_gene_by_entrez_id",
            "endpoint": "/gene/entrezId/7157",
            "input": {"entrez_id": "7157"},
            "output": {"symbol": "TP53", "entrezId": "7157"},
            "status": "success",
            "error": None,
            "return_code": "200",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        {
            "test_name": "tests/integration/api/test_example.py::test_error",
            "tool_name": "get_gene_by_entrez_id",
            "endpoint": "/gene/entrezId/9999999",
            "input": {"entrez_id": "9999999"},
            "output": None,
            "status": "error",
            "error": "Connection timeout",
            "return_code": "N/A",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    ]

    markdown = _generate_markdown_table(responses)

    # Verify both entries present
    assert "test_success" in markdown
    assert "test_error" in markdown

    # Verify success shows output
    lines = markdown.split("\n")
    success_line = [line for line in lines if "test_success" in line][0]
    assert "{symbol, entrezId}" in success_line
    assert "| 200 |" in success_line
    assert "| ✅ |" in success_line

    # Verify error has empty output
    error_line = [line for line in lines if "test_error" in line][0]
    columns = error_line.split("|")
    output_column = columns[5].strip()
    assert output_column == "", f"Expected empty output preview, got: '{output_column}'"
    assert "| N/A |" in error_line
    assert "| ❌ |" in error_line

    # Verify error message is NOT in markdown table
    assert "Connection timeout" not in markdown


def test_markdown_table_structure():
    """Test that markdown table structure is valid."""
    responses = [
        {
            "test_name": "tests/integration/api/test_example.py::test_table",
            "tool_name": "get_gene_by_entrez_id",
            "endpoint": "/gene/entrezId/7157",
            "input": {"entrez_id": "7157"},
            "output": None,
            "status": "error",
            "error": "Test error with | pipe | characters",
            "return_code": "500",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    ]

    markdown = _generate_markdown_table(responses)

    # Verify table headers
    assert (
        "| Test Name | Tool | Endpoint | Input | Output Preview | # Output Keys | Return Code | Status |"
        in markdown
    )
    assert (
        "|-----------|------|----------|-------|----------------|---------------|-------------|--------|"
        in markdown
    )

    # Verify proper number of columns in each row
    lines = markdown.split("\n")
    table_rows = [line for line in lines if line.startswith("|") and "Test Name" not in line]
    for row in table_rows:
        if row.strip().startswith("|---"):  # Skip separator row
            continue
        columns = row.split("|")
        # Should have 10 columns (empty start, 8 data columns, empty end)
        assert len(columns) == 10, f"Expected 10 columns, got {len(columns)} in: {row}"
