# GitHub Copilot Instructions for MARRVEL-MCP

## Project Overview

MARRVEL-MCP is a Model Context Protocol (MCP) server that provides AI assistants with access to the MARRVEL (Model organism Aggregated Resources for Rare Variant ExpLoration) genomics database. The project consists of 30+ MCP tools for querying genes, variants, diseases, orthologs, and expression data.

**Base Technologies:**
- Python 3.10+
- FastMCP framework
- httpx for async HTTP requests
- pytest for testing
- Black for code formatting (line-length=100)

## Development Workflow

### 1. Issue-Driven Development

**Every task must start with a GitHub issue:**

- Before writing code, create or reference a GitHub issue
- Issue should clearly describe:
  - Problem or feature request
  - Acceptance criteria
  - Expected outcomes
  - Related issues or context
- Work is committed as a Pull Request (PR) that references the issue
- Use keywords in PR description: "Fixes #123" or "Closes #456"

**Issue Scope Guidelines:**
- **Right-sized**: Issues should be small enough for human review but not micro-tasks
- **Reviewable**: A PR should be reviewable in 15-30 minutes
- **Focused**: One clear objective per issue
- **Modular**: Separate concerns (e.g., don't mix refactoring with feature addition)
- **Examples of good scope:**
  - "Add pytest markers to separate unit vs integration tests"
  - "Implement get_variant_cosmic tool"
  - "Refactor error handling in variant tools"
- **Examples of too large:**
  - "Rewrite entire test suite" (split into multiple issues)
  - "Add 10 new variant tools" (create separate issues per tool or related groups)
- **Examples of too small:**
  - "Fix typo in comment" (batch with other small fixes)
  - "Add one docstring" (include with related changes)

### 2. Pull Request Workflow

**Every code change goes through PR:**

```
Issue Created → Branch Created → Code + Tests → PR Opened → Review → Merge
```

**PR Requirements:**
- Reference the issue number in PR title or description
- Pass all CI checks:
  - ✅ Pre-commit hooks (Black formatting)
  - ✅ Unit tests (Python 3.10-3.13)
  - ✅ Integration tests (when applicable)
- Include:
  - Code changes
  - Tests for new functionality
  - Updated documentation
  - Updated examples (if adding tools)

**Branch Naming:**
- Feature: `feature/issue-123-short-description`
- Bug fix: `fix/issue-123-bug-description`
- Refactor: `refactor/issue-123-description`

### 3. Modular Development

**Favor modularity and separation of concerns:**

- **Don't create excessive files**: Balance between modularity and maintainability
- **Current structure is good**: Tools are grouped by category in `src/tools/`
- **When to create new files:**
  - New tool category (e.g., if adding protein structure tools)
  - Shared utilities used across multiple tools
  - Complex logic that warrants separation
- **When NOT to create new files:**
  - Single tool addition (add to existing category file)
  - Small helper functions (add to relevant module)
  - One-off utilities (include in the module using it)

**File Organization:**
```
src/
├── tools/
│   ├── __init__.py
│   ├── gene_tools.py          # Gene-related tools (3 tools)
│   ├── variant_tools.py       # Variant analysis (13 tools)
│   ├── disease_tools.py       # OMIM queries (3 tools)
│   ├── ortholog_tools.py      # DIOPT orthologs (2 tools)
│   ├── expression_tools.py    # Expression data (3 tools)
│   └── utility_tools.py       # HGVS validation, etc. (2 tools)
└── utils/
    ├── __init__.py
    └── api_client.py          # Shared HTTP client
```

## Code Quality Standards

### 1. Code Formatting with Black

**All Python code must be formatted with Black:**

```bash
# Black is configured in pyproject.toml:
# - line-length = 100
# - target-version = py313
```

**Pre-commit hooks automatically run Black:**
- Installed via `.pre-commit-config.yaml`
- Runs on every commit
- Auto-fixes formatting issues
- You must review and re-commit if hooks make changes

**Manual formatting:**
```bash
# Format all files
black .

# Format specific file
black src/tools/gene_tools.py

# Check without making changes
black --check .
```

### 2. Code Style Guidelines

**Follow existing patterns:**

```python
# Tool function template
@mcp.tool()
async def tool_name(param: str) -> str:
    """
    Brief one-line description.

    Detailed explanation of what this tool does, including context
    about when and why to use it.

    Args:
        param: Description of parameter with type info

    Returns:
        JSON string with result data

    Example:
        tool_name("example_value")

    API Endpoint: GET /api/endpoint/:param
    """
    try:
        # Input validation
        if not param:
            return json.dumps({"error": "Parameter required"})

        # API call
        endpoint = f"/api/endpoint/{param}"
        data = await fetch_marrvel_data(endpoint)

        # Return formatted result
        return json.dumps(data, indent=2)

    except httpx.HTTPStatusError as e:
        return json.dumps({"error": f"API error: {e.response.status_code}"})
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})
```

**Key principles:**
- Type hints for all function parameters and returns
- Comprehensive docstrings (see template above)
- Try-except blocks for error handling
- Descriptive error messages
- JSON formatted returns
- Follow async/await patterns

### 3. Testing Requirements

**Every code change must include tests:**

**Test Structure:**
```
tests/
├── conftest.py              # Shared fixtures and markers
├── test_gene_tools.py       # Unit tests (mocked)
├── test_variant_tools.py    # Unit tests (mocked)
├── test_api_client.py       # Integration tests (real API)
├── test_api_direct.py       # Integration tests (real API)
└── test_server_integration.py  # MCP server tests
```

**Test Markers:**
```python
# Unit tests (default - always run)
def test_gene_tool_success():
    """Fast test with mocked API response."""
    pass

# Integration tests (can be skipped)
@pytest.mark.integration
async def test_real_api_call():
    """Test with real MARRVEL API."""
    pass
```

**Running tests:**
```bash
# Run all tests
pytest

# Run only unit tests (fast)
pytest -m "not integration"

# Run only integration tests
pytest -m integration

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_gene_tools.py
```

**Test Requirements for PRs:**
- Add unit tests with mocked responses for new tools
- Add integration tests for end-to-end validation
- Maintain or improve test coverage
- All tests must pass in CI

### 4. Documentation Requirements

**Update documentation for all changes:**

**Files to update:**
- `README.md` - High-level overview (if adding major features)
- `docs/API_DOCUMENTATION.md` - Detailed tool documentation (always for new tools)
- `docs/ARCHITECTURE.md` - System design (for architectural changes)
- `CONTRIBUTING.md` - Guidelines (if changing dev workflow)
- `examples/example_queries.py` - Usage examples (for new tools)

**Documentation must include:**
- Clear description of functionality
- Parameter specifications
- Return value format
- Example usage with real-world scenarios
- API endpoint reference
- Error handling information

## Architecture Patterns

### MCP Tool Pattern

**Every tool follows this pattern:**

```python
from src.utils.api_client import fetch_marrvel_data
import json
import httpx

@mcp.tool()
async def get_resource_by_identifier(identifier: str) -> str:
    """Tool description."""
    try:
        endpoint = f"/resource/identifier/{identifier}"
        data = await fetch_marrvel_data(endpoint)
        return json.dumps(data, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps({
            "error": f"HTTP {e.response.status_code}",
            "message": str(e)
        })
    except Exception as e:
        return json.dumps({"error": str(e)})
```

### API Client Pattern

**Use shared HTTP client:**

```python
# Good - use shared client
from src.utils.api_client import fetch_marrvel_data

data = await fetch_marrvel_data("/endpoint")

# Bad - don't create new clients
import httpx
async with httpx.AsyncClient() as client:
    response = await client.get(...)  # Don't do this
```

### Error Handling Pattern

**Consistent error handling:**

```python
# Always return JSON, even for errors
try:
    # operation
    return json.dumps(data)
except httpx.HTTPStatusError as e:
    # HTTP errors (4xx, 5xx)
    return json.dumps({
        "error": "API_ERROR",
        "status_code": e.response.status_code,
        "message": "Detailed error message"
    })
except ValueError as e:
    # Input validation errors
    return json.dumps({
        "error": "INVALID_INPUT",
        "message": str(e)
    })
except Exception as e:
    # Unexpected errors
    return json.dumps({
        "error": "UNKNOWN_ERROR",
        "message": str(e)
    })
```

## Common Patterns and Anti-Patterns

### ✅ Good Patterns

```python
# Clear, descriptive naming
async def get_gene_by_entrez_id(entrez_id: str) -> str:
    """Get gene info using Entrez ID."""
    pass

# Comprehensive docstrings
"""
Brief description.

Detailed explanation with context and usage guidance.

Args:
    param: Clear description with examples

Returns:
    JSON string with data structure description

Example:
    get_gene_by_entrez_id("7157")  # TP53
"""

# Type hints everywhere
def process_data(input: str, count: int = 10) -> dict[str, Any]:
    pass

# Modular tool organization
# gene_tools.py contains all gene-related tools
# variant_tools.py contains all variant-related tools
```

### ❌ Anti-Patterns

```python
# Vague naming
async def get_data(id: str):  # Too generic
    pass

# Missing docstrings
async def tool(param):  # No documentation
    return data

# No type hints
def process(data):  # What type is data?
    pass

# Excessive file creation
# Don't create one file per tool
# single_tool.py  # Bad - group related tools
```

## Data Formats and Standards

### Variant Format
```python
# Standard: "chromosome-position-reference-alternate"
variant = "17-7577121-C-T"  # hg19/GRCh37 coordinates

# HGVS format
hgvs = "NM_000546.5:c.215C>G"
```

### Taxonomy IDs
```python
TAXONOMY_IDS = {
    "human": "9606",
    "mouse": "10090",
    "zebrafish": "7955",
    "drosophila": "7227",
    "c_elegans": "6239"
}
```

### Chromosome Format
```python
# Always include "chr" prefix
chromosome = "chr17"  # Good
chromosome = "17"     # Bad

# Valid: chr1-chr22, chrX, chrY, chrM
```

### Response Format
```python
# Always return JSON strings from tools
return json.dumps({
    "status": "success",
    "data": result_data,
    "metadata": {
        "source": "MARRVEL",
        "version": "2.0"
    }
}, indent=2)
```

## Common Tasks

### Adding a New Tool

**Checklist for new tool:**
- [ ] Create GitHub issue describing the tool
- [ ] Create feature branch
- [ ] Add tool function to appropriate file in `src/tools/`
- [ ] Follow tool pattern (see above)
- [ ] Add comprehensive docstring
- [ ] Add unit tests (mocked) in `tests/test_*_tools.py`
- [ ] Add integration test (real API) if applicable
- [ ] Update `docs/API_DOCUMENTATION.md`
- [ ] Add example to `examples/example_queries.py`
- [ ] Run Black: `black .`
- [ ] Run tests: `pytest`
- [ ] Create PR referencing issue
- [ ] Ensure CI passes

### Refactoring Code

**Approach:**
1. Create issue describing refactoring goal
2. Run tests before changes: `pytest`
3. Make changes incrementally
4. Run tests after each change
5. Ensure no functionality changes (tests should still pass)
6. Update documentation if interface changes
7. Create PR with clear explanation

### Fixing Bugs

**Approach:**
1. Create issue with bug reproduction steps
2. Add failing test that demonstrates bug
3. Fix the bug
4. Verify test now passes
5. Add additional tests for edge cases
6. Update docs if behavior changes
7. Create PR with "Fixes #issue-number"

## CI/CD Pipeline

**GitHub Actions automatically run:**

1. **Pre-commit checks** (`.github/workflows/pre-commit.yml`)
   - Black formatting
   - Trailing whitespace
   - YAML/JSON validation
   - Runs on: `[push, pull_request]`

2. **Test suite** (`.github/workflows/test.yml`)
   - Unit tests on Python 3.10, 3.11, 3.12, 3.13
   - Integration tests (may skip if API unavailable)
   - Runs on: `[push, pull_request]`

**All checks must pass before merge.**

## Review Guidelines

**When reviewing PRs:**
- ✅ Issue is referenced in PR
- ✅ Code follows Black formatting
- ✅ Tests are included and pass
- ✅ Documentation is updated
- ✅ Changes are focused and modular
- ✅ Commit messages are clear
- ✅ No excessive file creation
- ✅ Error handling is comprehensive
- ✅ Docstrings follow template

## Getting Help

**Resources:**
- `README.md` - Quick start guide
- `docs/API_DOCUMENTATION.md` - Complete tool reference
- `docs/ARCHITECTURE.md` - System design
- `CONTRIBUTING.md` - Contribution guidelines
- `examples/example_queries.py` - Usage examples

**When stuck:**
1. Check existing similar tools
2. Review test files for patterns
3. Read MARRVEL API docs: https://marrvel.org/doc
4. Create GitHub issue for discussion

## Summary

**Remember:**
1. 📝 Every task gets a GitHub issue
2. 🔄 Every change goes through PR
3. 📦 Keep changes modular but not micro
4. 🎨 Black formatting is mandatory (line-length=100)
5. ✅ Tests are required
6. 📚 Documentation must be updated
7. 🏗️ Follow established patterns
8. 🚫 Don't create excessive files
9. 👥 PRs should be human-reviewable (15-30 min)
10. 🔍 Reference API_DOCUMENTATION.md and ARCHITECTURE.md

**Goal:** Write clean, maintainable, well-tested code that helps genetics researchers access MARRVEL data through AI assistants.
