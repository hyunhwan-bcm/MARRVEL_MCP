# Tests Directory

This directory contains the **essential test suite** for the MARRVEL-MCP project, focused on critical functionality for fast CI execution.

## Essential Test Suite (22 tests)

The test suite has been optimized to retain only the most critical tests for repository health while maintaining fast execution (~2 seconds).

### Test Files

1. **`test_tools_smoke.py` (8 tests)** - Integration smoke tests for core MCP tools
   - Gene queries: `get_gene_by_entrez_id`, `get_gene_by_symbol`
   - Variant analysis: `get_variant_annotation_by_genomic_position`, `get_clinvar_by_variant`
   - Disease associations: `search_omim_by_disease_name`
   - Orthologs: `get_diopt_orthologs_by_entrez_id`
   - Literature: `search_pubmed`
   - Utilities: `liftover_hg38_to_hg19`

2. **`test_llm_provider_config.py` (4 tests)** - LLM provider configuration
   - API base URL defaults for different providers
   - Provider-specific configuration

3. **`test_openrouter_model_config.py` (3 tests)** - Model configuration
   - Default model fallback
   - Environment variable overrides
   - Model resolution

4. **`test_cache_essential.py` (2 tests)** - Core cache functionality
   - Basic save and load operations
   - Cache clearing

5. **`test_subset_essential.py` (3 tests)** - Subset parsing
   - Range parsing
   - Combined range and individual indices
   - Empty string handling

6. **`test_retry_essential.py` (2 tests)** - Retry logic
   - Successful first attempt
   - Retry with 500 error

### Selection Criteria

Tests were selected based on:
- **Critical for core functionality**: Essential MCP tools and configuration
- **High impact on repository health**: Catches breaking changes in critical paths
- **Representative coverage**: Covers different functional areas without redundancy
- **Fast execution**: All tests run in under 2 seconds

See [ESSENTIAL_TESTS.md](./ESSENTIAL_TESTS.md) for detailed rationale and maintenance guidelines.

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_tools_smoke.py
pytest tests/test_llm_provider_config.py
```

### Run with Verbose Output
```bash
pytest tests/ -v
```

### Run with Coverage
```bash
pytest tests/ --cov=marrvel_mcp --cov-report=html
```

## Test Markers

Tests use pytest markers for categorization:

- **`@pytest.mark.integration`** - Integration tests (requires network)
- **`@pytest.mark.integration_mcp`** - MCP server integration tests
- **`@pytest.mark.asyncio`** - Async tests

## Test Configuration

- **`pytest.ini`** - Pytest settings and marker definitions
- **`conftest.py`** - Custom fixtures (e.g., mcp_server fixture for smoke tests)

## Writing New Tests

When adding new tests, follow the principle: **Add tests only for critical functionality**.

### Integration Smoke Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.integration_mcp
@pytest.mark.asyncio
@pytest.mark.parametrize("name,args", [("tool_name", {"param": "value"})])
async def test_tool_returns_json(mcp_server, name, args):
    """Test that a tool returns valid JSON."""
    resp = await mcp_server.call_tool(name, args)
    resp = resp[-1]["result"]
    assert resp is not None
```

### Unit Test Example

```python
def test_configuration_default():
    """Test configuration defaults."""
    result = get_config_value("key")
    assert result == "expected_default"
```

## When to Add Tests

Add new tests only when:
1. A bug is found that wasn't caught by existing tests
2. A new critical MCP tool category is introduced
3. Core configuration or integration points change
4. A critical feature is added that affects repository health

**Do not add tests for:**
- Edge cases that rarely occur in production
- Exhaustive permutations of similar functionality
- Non-critical features like HTML report formatting
- Detailed internal implementation details

## Test Execution Time

- **Target**: Under 2 seconds for full suite
- **Current**: ~1.8 seconds (22 tests)

If tests start taking longer than 5 seconds, review and reduce non-essential tests.

## CI/CD Integration

Tests are designed for fast CI execution:

```yaml
# Example GitHub Actions workflow
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/ -v --tb=short
```

## Related Documentation

- [ESSENTIAL_TESTS.md](./ESSENTIAL_TESTS.md) - Detailed test selection rationale
- [Contributing Guide](../CONTRIBUTING.md) - How to contribute
- [README](../README.md) - Project overview
