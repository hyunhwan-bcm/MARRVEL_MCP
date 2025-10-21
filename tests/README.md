# Tests Directory

This directory contains all test files for the MARRVEL-MCP project.

## Test Files

### Unit & Integration Tests
- **`test_server.py`** - Core server functionality tests
  - Tests for `fetch_marrvel_data()` function
  - Mock-based unit tests
  - Integration tests marked with `@pytest.mark.integration`
  - Run: `pytest tests/test_server.py`
  - Run without integration tests: `pytest tests/test_server.py -m "not integration"`

### API Testing
- **`test_api_direct.py`** - Direct API verification tests
  - Tests MARRVEL API endpoints directly
  - Validates real API responses
  - No MCP protocol overhead
  - Run: `python3 tests/test_api_direct.py`

### MCP Client Testing
- **`test_mcp_client.py`** - Interactive MCP tool tester
  - Tests MCP tools through the protocol
  - Interactive and automated modes
  - Predefined test cases for common queries
  - Run: `python3 tests/test_mcp_client.py`

## Running Tests

### Run All Tests
```bash
pytest tests/
```

### Run Specific Test File
```bash
pytest tests/test_server.py
pytest tests/test_server.py::TestFetchMarrvelData
```

### Run with Coverage
```bash
pytest tests/ --cov=. --cov-report=html
```

### Skip Integration Tests
```bash
pytest tests/ -m "not integration"
```

### Run Only Integration Tests
```bash
pytest tests/ -m integration
```

## Test Configuration

Test configuration is defined in `pytest.ini` at the project root:
- Integration marker registered
- Concise output format enabled

## Dependencies

```bash
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.27.0
```

## Writing New Tests

1. Create test file: `tests/test_*.py`
2. Use `async def` for async tests
3. Mark integration tests: `@pytest.mark.integration`
4. Follow existing patterns in `test_server.py`

## Test Coverage

Current test coverage:
- Core server functions: ✅
- API integration: ✅
- Mock handling: ✅
- Error cases: ✅

## CI/CD

Tests are designed to run in CI/CD pipelines:
- Fast unit tests run on every commit
- Integration tests can be skipped in CI with `-m "not integration"`
