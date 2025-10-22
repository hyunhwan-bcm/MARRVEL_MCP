# Tests Directory

This directory contains all test files for the MARRVEL-MCP project, organized by test type for easy execution and maintenance.

## Test Organization

Tests are categorized using pytest markers for flexible execution:

- **`@pytest.mark.unit`** - Fast unit tests with mocked dependencies (no network required)
- **`@pytest.mark.integration_api`** - Integration tests that call real MARRVEL API (requires network)
- **`@pytest.mark.integration_mcp`** - Integration tests that run MCP server (requires server startup)
- **`@pytest.mark.integration`** - Generic integration marker (deprecated, use specific markers)

## Test Files

### Unit Tests (Mock-based, No Network)

These tests use `unittest.mock` to mock API responses and run very fast (~0.7 seconds for 141 tests):

- **`test_gene_tools.py`** - Gene query functions (get_gene_by_entrez_id, get_gene_by_symbol, get_gene_by_position)
- **`test_disease_tools.py`** - Disease/OMIM query functions
- **`test_expression_tools.py`** - Expression data functions (GTEx, orthologs, Pharos)
- **`test_ortholog_tools.py`** - DIOPT ortholog query functions
- **`test_utility_tools.py`** - Utility functions (HGVS validation, protein variant conversion)
- **`test_variant_tools.py`** - Variant annotation functions (dbNSFP, ClinVar, gnomAD, DGV, DECIPHER, Geno2MP)
- **`test_api_client.py`** - API client helper functions
- **`test_server.py`** - Core server functionality

### Integration Tests - API (Real API Calls)

These tests make actual HTTP calls to the MARRVEL API and require network connectivity:

- **`test_api_direct.py`** - Direct API endpoint verification
- **`test_mcp_client.py`** - MCP tool testing with real API calls
- Integration test methods within unit test files (marked with `@pytest.mark.integration_api`)

### Integration Tests - MCP (Server Lifecycle)

These tests start and interact with the full MCP server:

- **`test_server_integration.py`** - Complete MCP server lifecycle tests
  - Server start, initialize, list tools, call tool, shutdown
  - JSON-RPC 2.0 protocol compliance validation

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Only Fast Unit Tests (Development)
```bash
pytest -m unit
# or exclude integration tests
pytest -m "not integration_api and not integration_mcp"
```

### Run Only API Integration Tests
```bash
pytest -m integration_api
```

### Run Only MCP Server Integration Tests
```bash
pytest -m integration_mcp
```

### Run All Integration Tests
```bash
pytest -m "integration_api or integration_mcp"
```

### Run Specific Test File
```bash
pytest tests/test_gene_tools.py
pytest tests/test_gene_tools.py::TestGetGeneByEntrezId
pytest tests/test_gene_tools.py::TestGetGeneByEntrezId::test_successful_query
```

### Run with Verbose Output
```bash
pytest tests/ -v
pytest tests/ -m unit -v
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
pytest tests/ -m unit --cov=. --cov-report=html
```

### Skip Network-Dependent Tests (CI/CD)
```bash
pytest tests/ -m "not integration_api and not integration_mcp"
```

### Run Tests and Show Print Output
```bash
pytest tests/ -s
```

## Test Execution Examples

### Development Workflow
```bash
# Quick feedback during development (fast unit tests only)
pytest -m unit

# Test changes with real API (slower)
pytest -m integration_api

# Full test suite before committing
pytest tests/
```

### CI/CD Stages
```bash
# Stage 1: Fast unit tests (always run)
pytest -m unit

# Stage 2: API integration tests (run with network)
pytest -m integration_api

# Stage 3: MCP server tests (run in isolated environment)
pytest -m integration_mcp
```

## Test Configuration

Test configuration is defined in:
- **`pytest.ini`** - Pytest settings and marker definitions
- **`conftest.py`** - Custom fixtures and marker registration
  - SSL certificate verification checks
  - Network connectivity checks
  - Custom markers: `skip_if_ssl_broken`, `skip_if_no_network`

## Dependencies

```bash
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.27.0
certifi>=2023.7.22
```

## Writing New Tests

### Unit Test (Mock-based)

```python
import pytest
from unittest.mock import patch

@pytest.mark.unit
class TestMyFeature:
    """Unit tests with mocked dependencies."""

    @pytest.mark.asyncio
    async def test_successful_call(self):
        """Test successful API call."""
        with patch("src.tools.my_tool.fetch_marrvel_data") as mock_fetch:
            mock_fetch.return_value = {"data": "value"}
            result = await my_function()
            assert "value" in result
```

### Integration Test (Real API)

```python
import pytest

@pytest.mark.integration_api
@pytest.mark.asyncio
async def test_real_api_call():
    """Integration test with real API (requires network)."""
    result = await my_function()
    assert isinstance(result, str)
    assert len(result) > 0
```

### Integration Test (MCP Server)

```python
import pytest

@pytest.mark.integration_mcp
def test_server_functionality(mcp_server):
    """Test MCP server (requires server startup)."""
    # Use mcp_server fixture from conftest.py
    result = send_request_to_server(mcp_server)
    assert result["status"] == "success"
```

## Test Coverage

Current test coverage by category:
- **Unit tests**: 141 tests covering all tool functions with mocked APIs
- **API Integration tests**: 40 tests with real MARRVEL API calls
- **MCP Integration tests**: 6 tests covering server lifecycle

Coverage areas:
- ✅ Gene queries (Entrez ID, symbol, position)
- ✅ Variant annotations (dbNSFP, ClinVar, gnomAD, DGV, DECIPHER, Geno2MP)
- ✅ Disease data (OMIM)
- ✅ Ortholog information (DIOPT)
- ✅ Expression data (GTEx, ortholog expression, Pharos)
- ✅ Utility functions (HGVS validation, variant conversion)
- ✅ API client functions
- ✅ MCP server protocol compliance
- ✅ Error handling
- ✅ Mock handling

## CI/CD Integration

Tests are designed for flexible CI/CD execution:

```yaml
# Example GitHub Actions workflow
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m unit  # Fast, no network needed

  integration-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m integration_api  # Requires network

  server-tests:
    runs-on: ubuntu-latest
    steps:
      - run: pytest -m integration_mcp  # Requires server environment
```

## Troubleshooting

### SSL Certificate Errors
If you encounter SSL certificate errors:
```bash
pip install --upgrade certifi
```

Tests with SSL issues are automatically skipped using the `skip_if_ssl_broken` marker.

### Network Connectivity Issues
Tests requiring network access are automatically skipped using the `skip_if_no_network` marker when the network is unavailable.

### Test Collection Issues
If tests aren't being collected:
```bash
# Verify pytest configuration
pytest --collect-only

# Check marker registration
pytest --markers
```

## Related Documentation

- [Contributing Guide](../CONTRIBUTING.md) - How to contribute tests
- [API Documentation](../docs/API_DOCUMENTATION.md) - API reference for tools being tested
- [Architecture](../docs/ARCHITECTURE.md) - System architecture
