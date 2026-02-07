# Tests

Essential test suite for the MARRVEL-MCP project, optimized for fast CI execution (~2 seconds).

## Test Files

| File | Tests | Description |
|------|:-----:|-------------|
| `test_tools_smoke.py` | 8 | Integration smoke tests for core MCP tools (gene, variant, disease, ortholog, literature, liftover) |
| `test_llm_provider_config.py` | 4 | API base URL defaults and provider-specific configuration |
| `test_openrouter_model_config.py` | 3 | Model configuration, env var overrides, model resolution |
| `test_cache_essential.py` | 2 | Cache save/load and clearing |
| `test_subset_essential.py` | 3 | Subset range parsing |
| `test_cost_tracking.py` | - | Cost tracking functionality |
| `test_token_usage_counting.py` | - | Token usage counting |

## Running Tests

```bash
# All tests
pytest tests/

# Specific file
pytest tests/test_tools_smoke.py

# Verbose output
pytest tests/ -v

# With coverage
pytest tests/ --cov=marrvel_mcp --cov-report=html
```

## Test Markers

- `@pytest.mark.integration` - Integration tests (requires network)
- `@pytest.mark.integration_mcp` - MCP server integration tests
- `@pytest.mark.asyncio` - Async tests

## Adding Tests

Add new tests when:
1. A bug is found that wasn't caught by existing tests
2. A new MCP tool category is introduced
3. Core configuration or integration points change
