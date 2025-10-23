# API Response Capture Refactoring Summary

## Issue Reference
- **Issue:** #64
- **Title:** Refactor API test output: print JSON only, suppress error messages, and add return code section
- **Branch:** `copilot/refactor-api-test-output`

## Problem Statement

The previous API test output format had several critical issues:

1. **Broken Table Formatting:** Error messages containing special characters (pipes, HTML tags, quotes) broke markdown table rendering
2. **Mixed Content Types:** "Output Preview" column showed both JSON keys (success) and error messages (failure)
3. **No Return Code Visibility:** HTTP status codes were not displayed, making it hard to identify error types
4. **Poor UX in PR Comments:** Broken tables made PR review difficult

### Example of Broken Table (Before)

```markdown
| test_error | tool | endpoint | input | ❌ Error: <html>500 Internal Server Error</html> with | special chars | ❌ |
```
*Note: HTML tags and special characters could break markdown rendering*

## Solution Implemented

### Key Changes

1. **Suppress Error Messages in Output Preview**
   - Error messages are no longer displayed in the "Output Preview" column
   - Errors show empty output preview instead
   - Prevents table formatting issues

2. **Add Return Code Column**
   - New column shows HTTP status codes: 200, 404, 500, etc.
   - Shows "N/A" for network errors (no HTTP response)
   - Provides quick error type identification

3. **Consistent Output Format**
   - Success cases: Show JSON keys in "Output Preview"
   - Error cases: Show empty "Output Preview"
   - Return code column shows status for both cases

### Files Modified

1. **tests/conftest.py**
   - Updated `APIResponseCapture.log_response()` to accept `return_code` parameter
   - Refactored `_generate_markdown_table()` to suppress error messages
   - Added "Return Code" column to table header

2. **.github/scripts/capture_api_responses.py**
   - Updated `APIResponseCollector.add_response()` to accept `return_code` parameter
   - Refactored `generate_markdown_table()` with same logic as conftest.py
   - Ensures consistency between local and CI outputs

3. **tests/integration/api/test_api_capture_example.py**
   - Updated all test cases to extract and pass return codes
   - Added logic to extract status codes from exceptions
   - Handles both success and error cases

4. **tests/integration/api/test_api_direct.py**
   - Updated test cases to pass return codes
   - Consistent with example file changes

5. **tests/unit/test_markdown_generation.py**
   - Updated existing tests to match new behavior
   - Tests now verify empty output preview for errors
   - Tests verify return code display

6. **tests/unit/test_markdown_generation_refactor.py** (NEW)
   - Comprehensive new tests for refactored behavior
   - Tests success cases, error cases, and mixed scenarios
   - Validates table structure and column counts

7. **Documentation**
   - `docs/API_RESPONSE_CAPTURE.md` - Updated with new format
   - `docs/API_RESPONSE_FORMAT_COMPARISON.md` - Before/after comparison
   - `docs/API_RESPONSE_FORMAT_EXAMPLE.txt` - Real example output

## Code Examples

### Before (Old Implementation)

```python
# Old log_response - no return_code
api_capture.log_response(
    tool_name="get_gene_by_entrez_id",
    endpoint="/gene/entrezId/7157",
    input_data={"entrez_id": "7157"},
    output_data=None,
    status="error",
    error="404 Not Found",
)

# Old output - error message in table
| test | tool | endpoint | input | ❌ Error: 404 Not Found | N/A | ❌ |
```

### After (New Implementation)

```python
# New log_response - with return_code
return_code = "404"  # Extracted from exception
api_capture.log_response(
    tool_name="get_gene_by_entrez_id",
    endpoint="/gene/entrezId/7157",
    input_data={"entrez_id": "7157"},
    output_data=None,
    status="error",
    error="404 Not Found",
    return_code=return_code,  # ← Added
)

# New output - clean table with return code
| test | tool | endpoint | input |  | 0 | 404 | ❌ |
```

### How to Extract Return Codes

```python
try:
    result = await fetch_marrvel_data(endpoint)

    # Success case - extract from result or default to 200
    return_code = None
    if isinstance(result, dict) and "status_code" in result:
        return_code = str(result["status_code"])
    else:
        return_code = "200"

    api_capture.log_response(
        tool_name="my_tool",
        endpoint=endpoint,
        input_data={"param": "value"},
        output_data=result,
        status="success",
        return_code=return_code,
    )

except Exception as e:
    # Error case - extract from exception or default to N/A
    return_code = "N/A"
    if hasattr(e, "response") and hasattr(e.response, "status_code"):
        return_code = str(e.response.status_code)

    api_capture.log_response(
        tool_name="my_tool",
        endpoint=endpoint,
        input_data={"param": "value"},
        output_data=None,
        status="error",
        error=str(e),
        return_code=return_code,
    )
    raise
```

## Visual Comparison

### Old Format Table

```markdown
| Test Name | Tool | Endpoint | Input | Output Preview | # Keys | Status |
|-----------|------|----------|-------|----------------|--------|--------|
| test_success | get_gene | /gene/7157 | {...} | {symbol, entrezId, name} | 3 | ✅ |
| test_404 | get_gene | /gene/999 | {...} | ❌ 404 Client Error: Not Found for url: https://... | N/A | ❌ |
| test_network | get_gene | /gene/7157 | {...} | ❌ [Errno -5] No address associated with hostname | N/A | ❌ |
```

**Problems:**
- Long error messages make table hard to read
- Special characters can break markdown rendering
- No quick way to see HTTP status codes

### New Format Table

```markdown
| Test Name | Tool | Endpoint | Input | Output Preview | # Keys | Return Code | Status |
|-----------|------|----------|-------|----------------|--------|-------------|--------|
| test_success | get_gene | /gene/7157 | {...} | {symbol, entrezId, name} | 3 | 200 | ✅ |
| test_404 | get_gene | /gene/999 | {...} |  | 0 | 404 | ❌ |
| test_network | get_gene | /gene/7157 | {...} |  | 0 | N/A | ❌ |
```

**Improvements:**
- ✅ Clean, consistent table structure
- ✅ No special characters to break rendering
- ✅ Quick error identification via return codes
- ✅ Better readability in PR comments

## Benefits

### 1. Robust Table Rendering
- Tables never break due to special characters in error messages
- Consistent markdown rendering across all scenarios
- PR comments always display correctly

### 2. Better Error Visibility
- Return codes provide immediate error type identification
- HTTP status codes help debug issues quickly
- Network errors clearly marked as "N/A"

### 3. Consistent Output Format
- "Output Preview" column has consistent meaning
- Success = JSON keys, Error = empty
- No mixed content types in same column

### 4. Improved Developer Experience
- Easier to scan test results
- Faster error diagnosis
- Better PR review experience

### 5. Maintainability
- Logic is centralized in conftest.py
- Tests are simple and focused
- Documentation is comprehensive

## Testing

### Test Coverage

- **143 unit tests** - All passing
- **10 markdown generation tests** - All passing
  - 5 existing tests (updated)
  - 5 new tests (comprehensive coverage)

### Test Scenarios Covered

1. ✅ Success cases with various JSON structures
2. ✅ HTTP error cases (404, 500)
3. ✅ Network error cases (connection timeout, DNS)
4. ✅ Mixed success and error results
5. ✅ Special characters in error messages
6. ✅ Empty responses
7. ✅ Large JSON objects
8. ✅ List responses
9. ✅ Table structure validation
10. ✅ Return code extraction

## Migration Guide

For developers adding new integration tests:

### Step 1: Import Required Modules

```python
from src.utils.api_client import fetch_marrvel_data
import pytest
```

### Step 2: Use api_capture Fixture

```python
@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_my_api(api_capture):
    endpoint = "/my/endpoint"

    try:
        result = await fetch_marrvel_data(endpoint)

        # Extract return code
        return_code = "200"
        if isinstance(result, dict) and "status_code" in result:
            return_code = str(result["status_code"])

        # Log success
        api_capture.log_response(
            tool_name="my_tool",
            endpoint=endpoint,
            input_data={"param": "value"},
            output_data=result,
            status="success",
            return_code=return_code,
        )

    except Exception as e:
        # Extract return code from exception
        return_code = "N/A"
        if hasattr(e, "response") and hasattr(e.response, "status_code"):
            return_code = str(e.response.status_code)

        # Log error
        api_capture.log_response(
            tool_name="my_tool",
            endpoint=endpoint,
            input_data={"param": "value"},
            output_data=None,
            status="error",
            error=str(e),
            return_code=return_code,
        )
        raise
```

## Future Enhancements

Potential future improvements:

1. **Response Time Tracking:** Add column for API response time
2. **Error Categories:** Classify errors by type (client, server, network)
3. **Retry Information:** Track number of retries for failed requests
4. **Historical Comparison:** Compare against previous test runs
5. **Performance Metrics:** Track API performance trends over time

## Conclusion

This refactoring successfully addresses all issues from #64:

✅ Error messages suppressed in output preview
✅ Return code column added
✅ Markdown table formatting fixed
✅ All tests passing
✅ Documentation updated
✅ Code formatted with Black

The new format provides:
- Better readability
- Robust table rendering
- Improved error visibility
- Enhanced developer experience

## Related Documentation

- [API Response Capture Guide](./API_RESPONSE_CAPTURE.md)
- [Format Comparison](./API_RESPONSE_FORMAT_COMPARISON.md)
- [Example Output](./API_RESPONSE_FORMAT_EXAMPLE.txt)
- [Contributing Guide](../CONTRIBUTING.md)
