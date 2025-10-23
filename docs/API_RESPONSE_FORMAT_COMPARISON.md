# API Response Capture Format - Before vs After

This document shows the changes made to the API response capture format to address issue #64.

## Problem Statement

The previous format had several issues:
1. Error messages were displayed in the "Output Preview" column
2. Error messages could contain special characters (pipes, HTML tags, etc.) that broke markdown table formatting
3. No visibility into HTTP status codes or error types
4. Tables could become unreadable when errors occurred

## Solution

The refactored format addresses these issues by:
1. Suppressing error messages in the "Output Preview" column (leaving it empty)
2. Adding a "Return Code" column to show HTTP status codes
3. Ensuring tables render correctly regardless of error content

## Format Comparison

### Old Format (Before)

```markdown
| Test Name | Tool | Endpoint | Input | Output Preview | # Output Keys | Status |
|-----------|------|----------|-------|----------------|---------------|--------|
| test_gene_success | get_gene_by_entrez_id | /gene/entrezId/7157 | `{"entrez_id": "7157"}` | {symbol, entrezId, name, ...} | 15 | ✅ |
| test_gene_404 | get_gene_by_entrez_id | /gene/entrezId/999 | `{"entrez_id": "999"}` | ❌ Error: 404 Client Error: Not Found | N/A | ❌ |
| test_network_error | get_gene_by_symbol | /gene/symbol/TEST | `{"symbol": "TEST"}` | ❌ [Errno -5] No address associated with hostname | N/A | ❌ |
```

**Issues:**
- Error messages appear in "Output Preview" column
- Special characters in error messages can break table rendering
- No HTTP status code visibility
- Mixed content types in "Output Preview" (JSON keys vs error text)

### New Format (After)

```markdown
| Test Name | Tool | Endpoint | Input | Output Preview | # Output Keys | Return Code | Status |
|-----------|------|----------|-------|----------------|---------------|-------------|--------|
| test_gene_success | get_gene_by_entrez_id | /gene/entrezId/7157 | `{"entrez_id": "7157"}` | {symbol, entrezId, name, ...} | 15 | 200 | ✅ |
| test_gene_404 | get_gene_by_entrez_id | /gene/entrezId/999 | `{"entrez_id": "999"}` |  | 0 | 404 | ❌ |
| test_network_error | get_gene_by_symbol | /gene/symbol/TEST | `{"symbol": "TEST"}` |  | 0 | N/A | ❌ |
```

**Improvements:**
- ✅ Error messages are NOT displayed in table (prevents table breaking)
- ✅ New "Return Code" column shows HTTP status codes
- ✅ "Output Preview" is consistent: JSON keys for success, empty for errors
- ✅ Tables render correctly regardless of error message content
- ✅ Quick visibility into error types (404, 500, N/A for network)

## Detailed Examples

### Example 1: Successful API Call

**Response Data:**
```json
{
  "symbol": "TP53",
  "entrezId": "7157",
  "name": "tumor protein p53",
  "taxonId": "9606",
  "chromosome": "17"
}
```

**Table Row:**
```markdown
| test_tp53_gene | get_gene_by_entrez_id | /gene/entrezId/7157 | `{"entrez_id": "7157"}` | {symbol, entrezId, name, taxonId, chromosome} | 5 | 200 | ✅ |
```

### Example 2: HTTP 404 Error

**Error:**
```
404 Client Error: Not Found for url: https://marrvel.org/data/gene/entrezId/999999999
```

**Table Row (Old Format):**
```markdown
| test_invalid_id | get_gene_by_entrez_id | /gene/entrezId/999999999 | `{"entrez_id": "999999999"}` | ❌ Error: 404 Client Error: Not Found for url: https://marrvel.org/data/gene/entrezId/999999999 | N/A | ❌ |
```
*Problem: Long error message causes table to be very wide and potentially break*

**Table Row (New Format):**
```markdown
| test_invalid_id | get_gene_by_entrez_id | /gene/entrezId/999999999 | `{"entrez_id": "999999999"}` |  | 0 | 404 | ❌ |
```
*Clean: Empty output preview, return code shows 404*

### Example 3: Network Error

**Error:**
```
[Errno -5] No address associated with hostname
```

**Table Row (Old Format):**
```markdown
| test_network | get_gene_by_symbol | /gene/symbol/BRCA1 | `{"symbol": "BRCA1"}` | ❌ [Errno -5] No address associated with hostname | N/A | ❌ |
```

**Table Row (New Format):**
```markdown
| test_network | get_gene_by_symbol | /gene/symbol/BRCA1 | `{"symbol": "BRCA1"}` |  | 0 | N/A | ❌ |
```
*Clean: Empty output preview, return code shows N/A for network errors*

### Example 4: Invalid JSON Response with Special Characters

**Error:**
```
Invalid JSON response (HTTP 500): <html><body><h1>Internal Server Error</h1></body></html>
```

**Table Row (Old Format):**
```markdown
| test_bad_json | get_omim | /omim/invalid | `{"id": "test"}` | ❌ Invalid JSON response (HTTP 500): <html><body><h1>Internal Server Error</h1></body></html> | N/A | ❌ |
```
*Problem: HTML tags could potentially break markdown rendering*

**Table Row (New Format):**
```markdown
| test_bad_json | get_omim | /omim/invalid | `{"id": "test"}` |  | 0 | 500 | ❌ |
```
*Clean: No HTML in table, return code shows 500*

## Code Changes

### 1. Updated `log_response()` Signature

```python
# Old
def log_response(
    self,
    tool_name: str,
    endpoint: str,
    input_data: Dict[str, Any],
    output_data: Any,
    status: str = "success",
    error: str = None,
):

# New
def log_response(
    self,
    tool_name: str,
    endpoint: str,
    input_data: Dict[str, Any],
    output_data: Any,
    status: str = "success",
    error: str = None,
    return_code: str = None,  # ← Added
):
```

### 2. Updated Markdown Generation Logic

```python
# Old - Error messages shown in output preview
if output_data is None:
    if resp.get("error"):
        output_preview = f"❌ {resp['error']}"  # ← Error message in table
        num_keys = "0"

# New - Error messages suppressed
if resp["status"] == "error" or output_data is None:
    output_preview = ""  # ← Empty for errors
    num_keys = "0"
```

### 3. Test Updates

```python
# Old
except Exception as e:
    api_capture.log_response(
        tool_name="my_tool",
        endpoint="/endpoint",
        input_data={"param": "value"},
        output_data=None,
        status="error",
        error=str(e),
    )

# New
except Exception as e:
    # Extract return code if available
    return_code = "N/A"
    if hasattr(e, "response") and hasattr(e.response, "status_code"):
        return_code = str(e.response.status_code)

    api_capture.log_response(
        tool_name="my_tool",
        endpoint="/endpoint",
        input_data={"param": "value"},
        output_data=None,
        status="error",
        error=str(e),
        return_code=return_code,  # ← Added
    )
```

## Benefits Summary

1. **Robust Table Formatting**: Tables never break due to special characters in error messages
2. **Better Error Visibility**: Return codes provide quick insight into error types
3. **Consistent Output**: "Output Preview" column is consistent (JSON for success, empty for errors)
4. **Cleaner PRs**: Markdown tables in PR comments render correctly
5. **Easier Debugging**: HTTP status codes help identify issues quickly

## Migration Guide

For developers adding new integration tests:

1. **Extract return code in success case:**
   ```python
   return_code = None
   if isinstance(result, dict) and "status_code" in result:
       return_code = str(result["status_code"])
   else:
       return_code = "200"
   ```

2. **Extract return code in error case:**
   ```python
   return_code = "N/A"
   if hasattr(e, "response") and hasattr(e.response, "status_code"):
       return_code = str(e.response.status_code)
   ```

3. **Pass return_code to log_response():**
   ```python
   api_capture.log_response(
       tool_name="my_tool",
       endpoint="/endpoint",
       input_data={"param": "value"},
       output_data=result,
       status="success",
       return_code=return_code,  # ← Add this
   )
   ```

## References

- Issue: #64
- Modified files:
  - `tests/conftest.py`
  - `.github/scripts/capture_api_responses.py`
  - `tests/integration/api/test_api_capture_example.py`
  - `tests/integration/api/test_api_direct.py`
  - `docs/API_RESPONSE_CAPTURE.md`
