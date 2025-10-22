## Issue Summary
The file `tests/unit/test_server_unit.py` contains multiple test classes that are just stubs (only contain `pass` statements). These stub tests provide no value and should be replaced with real unit tests that verify the MCP server initialization and tool registration functionality.

## Current State
The file currently has:
- ✅ `TestFetchMarrvelData` - Real tests (working correctly)
- ❌ `TestGeneTools` - Stub only (all methods just `pass`)
- ❌ `TestVariantTools` - Stub only (all methods just `pass`)
- ❌ `TestOMIMTools` - Stub only (all methods just `pass`)
- ❌ `TestDIOPTTools` - Stub only (all methods just `pass`)
- ❌ `TestExpressionTools` - Stub only (all methods just `pass`)
- ❌ `TestUtilityTools` - Stub only (all methods just `pass`)

## Problem
1. The stub test classes are misleading - they appear to provide coverage but don't actually test anything
2. Individual tool functions are already comprehensively tested in their respective test files:
   - `test_gene_tools.py` - Tests gene tool functions
   - `test_variant_tools.py` - Tests variant tool functions
   - `test_disease_tools.py` - Tests OMIM/disease tool functions
   - `test_ortholog_tools.py` - Tests DIOPT tool functions
   - `test_expression_tools.py` - Tests expression tool functions
   - `test_utility_tools.py` - Tests utility tool functions
3. What's missing is tests for **server initialization and tool registration**

## Proposed Solution
Replace the stub test classes with real tests that verify:

### 1. Server Creation and Initialization
- Test that `create_server()` returns a FastMCP instance
- Test that the server has the correct name ("MARRVEL")
- Test that the server is properly configured

### 2. Tool Registration
- Test that all tool modules are registered correctly
- Test that each module's `register_tools()` function is called
- Verify the correct number of tools are registered in each category:
  - Gene tools: 3 tools
  - Variant tools: 13 tools
  - Disease tools: 3 tools
  - Ortholog tools: 2 tools
  - Expression tools: 3 tools
  - Utility tools: 2 tools
  - **Total: 26 tools**

## Acceptance Criteria
- [x] Remove all stub test classes (TestGeneTools, TestVariantTools, etc.)
- [x] Add `TestServerCreation` class to test server initialization
- [x] Add `TestToolRegistration` class to verify all tools are registered
- [x] All tests use proper mocking (no real MCP server started)
- [x] Tests follow existing project patterns (Black formatted, comprehensive docstrings)
- [x] All tests pass with `pytest tests/unit/test_server_unit.py`
- [x] Maintain or improve test coverage

## Related Files
- `tests/unit/test_server_unit.py` - File to be updated
- `server.py` - Server implementation being tested
- `src/tools/*.py` - Tool modules that get registered
