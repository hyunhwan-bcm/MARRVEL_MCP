# Tests Directory

This directory contains all test files for the MARRVEL-MCP project.

## Test Organization

Tests are organized by type using pytest markers:

### Unit Tests (`@pytest.mark.unit`)
- Fast, mock-based tests that don't require network access
- Test individual functions and components in isolation
- Use `unittest.mock` to simulate API responses
- Should run in < 1 second

### Integration Tests - API (`@pytest.mark.integration_api`)
- Tests that make real calls to the MARRVEL API
- Require network connectivity
- Validate actual API responses and data formats
- May be slower depending on network/API response time

### Integration Tests - MCP Server (`@pytest.mark.integration_mcp`)
- Tests that start and interact with the full MCP server
- Test the complete MCP protocol lifecycle
- Require server startup time
- Most comprehensive but slowest tests

## Test Files

### Mock-Based Unit Tests
- **`test_gene_tools.py`** - Gene query functions (by Entrez ID, symbol, position)
- **`test_disease_tools.py`** - OMIM disease information queries
- **`test_expression_tools.py`** - GTEx, Pharos, and ortholog expression data
- **`test_ortholog_tools.py`** - DIOPT ortholog and alignment queries
- **`test_variant_tools.py`** - Variant databases (dbNSFP, ClinVar, gnomAD, DGV, DECIPHER, Geno2MP)
- **`test_utility_tools.py`** - HGVS validation and protein variant conversion
- **`test_api_client.py`** - Core HTTP API client functionality
- **`test_server.py`** - Basic server setup and mock tests

### Real API Integration Tests
- **`test_api_direct.py`** - Direct API endpoint validation
- **`test_mcp_client.py`** - Tool testing through direct function calls
- Integration test methods in all tool test files (marked with `@pytest.mark.integration_api`)

### MCP Server Integration Tests
- **`test_server_integration.py`** - Full MCP server lifecycle tests
  - Server startup and initialization
  - Tool listing and calling
  - Graceful shutdown
  - JSON-RPC 2.0 protocol compliance

## Running Tests

### Run Only Fast Unit Tests (Recommended for Development)
```bash
pytest -m "unit and not integration_api"
```

### Run All Unit Tests (Including Integration Tests Within Test Classes)
```bash
pytest -m unit
```

### Run Only Real API Integration Tests
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

### Run Everything Except Integration Tests
```bash
pytest -m "not integration_api and not integration_mcp"
```

### Run All Tests (Default)
```bash
pytest
```

### Run Specific Test File
```bash
pytest tests/test_gene_tools.py
pytest tests/test_gene_tools.py::TestGetGeneByEntrezId
```

### Run with Verbose Output
```bash
pytest -v
pytest -v -m unit
```

### Run with Coverage
```bash
pytest --cov=. --cov-report=html
pytest -m unit --cov=. --cov-report=html
```

## Test Configuration

Test configuration is defined in:
- `pytest.ini` - Test discovery and markers
- `pyproject.toml` - Additional pytest options
- `tests/conftest.py` - Custom markers and fixtures

Available markers:
- `unit` - Unit tests with mocked dependencies (fast, no network required)
- `integration_api` - Integration tests that call real MARRVEL API (requires network)
- `integration_mcp` - Integration tests that run MCP server (requires server startup)
- `integration` - (Legacy) Kept for backward compatibility

## Dependencies

```bash
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.27.0
```

## Writing New Tests

### Unit Tests (Mock-Based)
1. Create test in appropriate `test_*.py` file
2. Add `@pytest.mark.unit` to test class
3. Use `unittest.mock` to mock API calls
4. Use `async def` for async tests
5. Test both success and error cases

Example:
```python
import pytest
from unittest.mock import patch

@pytest.mark.unit
class TestMyFunction:
    @pytest.mark.asyncio
    async def test_successful_call(self):
        with patch("src.utils.api_client.fetch_marrvel_data") as mock:
            mock.return_value = {"result": "data"}
            result = await my_function()
            assert "data" in result
```

### Integration Tests (Real API)
1. Add `@pytest.mark.integration_api` to test method or class
2. No mocking - let tests make real API calls
3. Use well-known, stable data (e.g., TP53, BRCA1)
4. Test should be resilient to minor API changes

Example:
```python
@pytest.mark.unit  # Class can still be marked as unit
class TestMyFunction:
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call(self):
        result = await my_function("TP53")
        assert isinstance(result, str)
        assert "TP53" in result
```

### MCP Server Integration Tests
1. Add `@pytest.mark.integration_mcp` to test
2. Use fixtures for server lifecycle management
3. Test complete request/response cycles
4. Validate JSON-RPC protocol compliance

## Test Coverage

Current test coverage by category:
- **Unit Tests**: 125+ tests covering all tools and utilities
- **API Integration Tests**: 40+ tests validating real API responses
- **MCP Server Tests**: 6 tests covering server lifecycle
- **Total**: 171 tests

## CI/CD Integration

Recommended CI/CD test strategy:
```bash
# Stage 1: Fast feedback (< 30 seconds)
pytest -m "unit and not integration_api"

# Stage 2: API integration (< 2 minutes, requires network)
pytest -m integration_api

# Stage 3: Full integration (< 5 minutes, isolated environment)
pytest -m integration_mcp
```

## Troubleshooting

### SSL Certificate Issues
Some integration tests may fail with SSL errors. Install/update certifi:
```bash
pip install --upgrade certifi
```

Tests will automatically skip if SSL is misconfigured (see `conftest.py`).

### Network Issues
Integration tests require network access to `marrvel.org`. Tests will skip if network is unavailable.

### MCP Server Tests Hanging
If MCP server tests hang, ensure no other instance is running:
```bash
pkill -f "python.*server.py"
```
