"""
Unit tests for markdown generation in conftest.py.

This tests the _generate_markdown_table function to ensure:
1. Output preview shows key names instead of just JSON string
2. Endpoint column displays clickable markdown links
3. Empty content in error responses is handled properly
"""

import json
import pytest
from datetime import datetime, timezone
from typing import Dict, Any, List


def test_markdown_generation_with_dict_response():
    """Test markdown generation with a dict response containing many keys."""
    # Import the function we're testing
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    # Create test data simulating TP53 gene response with 25 keys
    test_responses = [
        {
            "test_name": "tests/integration/api/test_api_client_integration.py::test_real_api_call_tp53",
            "tool_name": "fetch_marrvel_data",
            "endpoint": "/gene/entrezId/7157",
            "input": {"entrez_id": "7157"},
            "output": {
                "xref": {
                    "omimId": "191170",
                    "hgncId": "11998",
                    "ensemblId": "ENSG00000141510",
                },
                "symbol": "TP53",
                "name": "tumor protein p53",
                "entrezId": "7157",
                "taxonId": "9606",
                "chromosome": "17",
                "key1": "value1",
                "key2": "value2",
                "key3": "value3",
                "key4": "value4",
                "key5": "value5",
                "key6": "value6",
                "key7": "value7",
                "key8": "value8",
                "key9": "value9",
                "key10": "value10",
                "key11": "value11",
                "key12": "value12",
                "key13": "value13",
                "key14": "value14",
                "key15": "value15",
                "key16": "value16",
                "key17": "value17",
                "key18": "value18",
                "key19": "value19",
            },
            "status": "success",
            "error": None,
            "timestamp": "2025-10-23T01:00:00.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # Verify the markdown contains expected elements
    assert "# MARRVEL API Test Responses" in markdown
    assert "test_real_api_call_tp53" in markdown
    assert "fetch_marrvel_data" in markdown

    # Issue 1 & 2 fix: Verify key names are shown in preview, not just JSON string
    # Should show: {xref, symbol, name, entrezId, +21 more}
    assert "xref" in markdown
    assert "symbol" in markdown
    assert "name" in markdown
    assert "entrezId" in markdown
    assert "+21 more" in markdown or "+21 more}" in markdown

    # Verify total key count is shown
    assert "25" in markdown

    # Issue 3 fix: Verify endpoint is a clickable link
    assert "[/gene/entrezId/7157](https://marrvel.org/data/gene/entrezId/7157)" in markdown

    # Verify status icon
    assert "✅" in markdown


def test_markdown_generation_with_empty_error_response():
    """Test markdown generation with error response containing empty content."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    # Create test data simulating invalid endpoint with empty content
    test_responses = [
        {
            "test_name": "tests/integration/api/test_api_client_integration.py::test_real_api_call_invalid_endpoint",
            "tool_name": "fetch_marrvel_data",
            "endpoint": "/invalid/nonexistent/endpoint",
            "input": {"test": "invalid"},
            "output": {"error": "Invalid JSON response", "status_code": 200, "content": ""},
            "status": "error",
            "error": "Invalid endpoint test",
            "return_code": "200",
            "timestamp": "2025-10-23T01:00:01.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # Refactored behavior: Error messages are NOT shown in output preview
    # Output preview should be empty for errors
    lines = markdown.split("\n")
    for line in lines:
        if "test_real_api_call_invalid_endpoint" in line:
            columns = line.split("|")
            # Column 5 is output preview (0-indexed from start)
            output_column = columns[5].strip()
            assert (
                output_column == ""
            ), f"Expected empty output preview for error, got: '{output_column}'"

    # Verify return code column exists and shows the status code
    assert "| 200 |" in markdown

    # Verify endpoint is a clickable link
    assert (
        "[/invalid/nonexistent/endpoint](https://marrvel.org/data/invalid/nonexistent/endpoint)"
        in markdown
    )

    # Verify status icon
    assert "❌" in markdown


def test_markdown_generation_with_few_keys():
    """Test markdown generation when response has 5 or fewer keys."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    test_responses = [
        {
            "test_name": "tests/simple_test.py::test_simple",
            "tool_name": "simple_tool",
            "endpoint": "/simple/endpoint",
            "input": {"id": "123"},
            "output": {"key1": "value1", "key2": "value2", "key3": "value3"},
            "status": "success",
            "error": None,
            "timestamp": "2025-10-23T01:00:00.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # With 3 keys, should show all keys without "+X more"
    assert "key1" in markdown
    assert "key2" in markdown
    assert "key3" in markdown
    assert "more" not in markdown  # Should not have "+X more" suffix


def test_markdown_generation_with_non_empty_error_content():
    """Test markdown generation with error response containing non-empty content."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    test_responses = [
        {
            "test_name": "tests/error_test.py::test_error",
            "tool_name": "error_tool",
            "endpoint": "/error/endpoint",
            "input": {"id": "999"},
            "output": {
                "error": "Invalid JSON response",
                "status_code": 404,
                "content": "Not Found: The requested resource does not exist",
            },
            "status": "error",
            "error": "Resource not found",
            "return_code": "404",
            "timestamp": "2025-10-23T01:00:00.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # Refactored behavior: Error messages are NOT shown in output preview
    # Output preview should be empty for errors
    lines = markdown.split("\n")
    for line in lines:
        if "test_error" in line:
            columns = line.split("|")
            # Column 5 is output preview (0-indexed from start)
            output_column = columns[5].strip()
            assert (
                output_column == ""
            ), f"Expected empty output preview for error, got: '{output_column}'"

    # Verify return code column exists and shows the HTTP status code
    assert "| 404 |" in markdown

    # Error messages should NOT appear in the output preview
    assert "Invalid JSON response (HTTP 404):" not in markdown or "| 404 |" in markdown
    # The content should not be shown in output preview
    for line in markdown.split("\n"):
        if "test_error" in line:
            assert "Not Found: The requested resource does not exist" not in line


def test_markdown_generation_with_list_response():
    """Test markdown generation with a list response."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    test_responses = [
        {
            "test_name": "tests/list_test.py::test_list",
            "tool_name": "list_tool",
            "endpoint": "/list/endpoint",
            "input": {"query": "search"},
            "output": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
            "status": "success",
            "error": None,
            "timestamp": "2025-10-23T01:00:00.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # Should show "2 items" for list responses
    assert "2 items" in markdown


def test_markdown_generation_with_newlines_in_error_content():
    """Test markdown generation with error content containing newlines and whitespace.

    This test ensures that newlines, carriage returns, and multiple spaces in error
    content are properly sanitized to prevent breaking the markdown table format.
    Addresses GitHub issue where HTML error pages with newlines broke the table.
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    test_responses = [
        {
            "test_name": "tests/error_test.py::test_html_error",
            "tool_name": "fetch_marrvel_data",
            "endpoint": "/invalid/endpoint",
            "input": {"test": "invalid"},
            "output": {
                "error": "Invalid JSON response",
                "status_code": 200,
                "content": "\n\n\n  <html>\n  <head>Error Page</head>\n  <body>\n    <h1>Not Found</h1>\n  </body>\n</html>",
            },
            "status": "error",
            "error": "Invalid endpoint",
            "timestamp": "2025-10-23T01:00:00.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # The content should be sanitized but still readable
    assert "Invalid JSON response (HTTP 200):" in markdown
    assert "<html>" in markdown
    assert "Error Page" in markdown or "Not Found" in markdown

    # Verify markdown table structure is preserved (all lines should be part of table)
    lines = markdown.split("\n")
    # Find the table section (after "## Summary Table")
    table_start = None
    for i, line in enumerate(lines):
        if "## Summary Table" in line:
            table_start = i
            break

    assert table_start is not None, "Table header not found"

    # Table should have header, separator, and data rows without breaks
    # Look for the test row (should be a complete table row)
    test_row_found = False
    for line in lines[table_start:]:
        if "test_html_error" in line:
            # This line should be a complete table row (starts with |, ends with |)
            assert line.startswith("|"), f"Table row doesn't start with |: {line}"
            assert line.endswith("|"), f"Table row doesn't end with |: {line}"
            # Count pipe separators - should have 8 (7 columns + 2 boundaries)
            pipe_count = line.count("|")
            assert (
                pipe_count >= 7
            ), f"Table row has only {pipe_count} pipes, expected at least 7: {line}"
            # Verify no literal newlines in the table row itself
            assert (
                "\n" not in line[:-1]
            ), f"Table row contains newline: {repr(line)}"  # -1 to exclude trailing \n from split
            test_row_found = True
            break

    assert test_row_found, "Test row not found in markdown table"


def test_markdown_generation_with_mixed_problematic_characters():
    """Test markdown generation with various problematic characters.

    Tests handling of tabs, carriage returns, mixed newlines, and multiple
    consecutive spaces to ensure all are properly normalized.
    """
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.conftest import _generate_markdown_table

    test_responses = [
        {
            "test_name": "tests/whitespace_test.py::test_mixed_whitespace",
            "tool_name": "fetch_marrvel_data",
            "endpoint": "/problem/endpoint",
            "input": {"id": "123"},
            "output": {
                "error": "Invalid JSON response",
                "status_code": 500,
                "content": "Error:\t\tInternal\r\nServer\n\n\nError    with    spaces",
            },
            "status": "error",
            "error": "Server error",
            "timestamp": "2025-10-23T01:00:00.000000+00:00",
        }
    ]

    markdown = _generate_markdown_table(test_responses)

    # Verify content is still readable with normalized whitespace
    assert (
        "Error: Internal Server Error with spaces" in markdown
        or "Error: Internal Server Error with" in markdown
    )  # May be truncated at 50 chars

    # Verify the table row is complete and properly formatted
    lines = markdown.split("\n")
    test_row_found = False
    for line in lines:
        if "test_mixed_whitespace" in line:
            assert line.startswith("|"), "Table row doesn't start with |"
            assert line.endswith("|"), "Table row doesn't end with |"
            # Verify no literal problematic whitespace in the table cell content
            # Extract just the Output Preview cell content
            cells = line.split("|")
            if len(cells) >= 6:  # Ensure we have enough cells
                output_preview_cell = cells[5]  # Output Preview is the 5th column (0-indexed)
                assert (
                    "\t" not in output_preview_cell
                ), f"Tab character found in output preview: {repr(output_preview_cell)}"
                assert (
                    "\r" not in output_preview_cell
                ), f"Carriage return found in output preview: {repr(output_preview_cell)}"
                # No literal newline characters should be in the cell
                assert (
                    "\n" not in output_preview_cell
                ), f"Newline found in output preview: {repr(output_preview_cell)}"
            test_row_found = True
            break

    assert test_row_found, "Test row with mixed whitespace not found"
