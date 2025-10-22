# Contributing to MARRVEL-MCP

Thank you for your interest in contributing to MARRVEL-MCP! This document provides guidelines for contributing to the project.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker to report bugs
- Describe the issue in detail
- Include steps to reproduce
- Provide example queries that demonstrate the issue
- Include your environment details (Python version, OS, etc.)

### Suggesting Enhancements

- Use GitHub issues to suggest new features
- Clearly describe the feature and its use case
- Explain why this feature would be useful to genetics researchers
- Provide examples of how it would be used

### Code Contributions

1. **Fork the Repository**
   ```bash
   git fork <repository-url>
   cd MARRVEL_MCP
   ```

2. **Create a Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make Your Changes**
   - Follow the existing code style
   - Add docstrings to all functions
   - Include type hints
   - Update documentation as needed

4. **Test Your Changes**
   ```bash
   # Install development dependencies
   pip install -r requirements.txt

   # Install pre-commit hooks
   pre-commit install

   # Run tests
   pytest tests/ -v

   # Run pre-commit checks
   pre-commit run --all-files

   # Test with Claude Desktop or MCP client
   python server.py
   ```

   **Note:** If you encounter SSL certificate verification errors, see the
   [Troubleshooting SSL Certificates](#troubleshooting-ssl-certificates) section below.

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```
   Note: Pre-commit hooks will automatically run and may fix formatting issues.
   If they make changes, review them and commit again.

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

   **Important:** Your PR must pass all CI checks:
   - ✅ Pre-commit hooks (Black formatting, trailing whitespace, etc.)
   - ✅ Unit tests across Python 3.10-3.13
   - ✅ Integration tests (may be skipped if API is unavailable)

## Code Quality & CI

### Automated Checks

All pull requests are automatically checked by GitHub Actions:

1. **Pre-commit Checks** - Runs Black formatting and code quality hooks
2. **Tests** - Runs unit and integration tests on multiple Python versions
3. **Code Style** - Verifies Black formatting compliance

### Pre-commit Hooks

Pre-commit hooks run automatically when you commit. They will:
- Format code with Black (line-length=100)
- Remove trailing whitespace
- Fix end-of-file issues
- Check YAML/JSON/TOML syntax
- Detect merge conflicts

If hooks make changes, you'll need to review and commit again.

To run manually:
```bash
# Run on all files
pre-commit run --all-files

# Run only Black
black .

# Skip hooks (emergency only)
git commit --no-verify
```

## Code Style Guidelines

### Python Style

- Follow PEP 8 style guide
- Use meaningful variable and function names
- Maximum line length: 100 characters
- Use type hints for function parameters and return values

### Documentation Style

- All functions must have comprehensive docstrings
- Include:
  - Brief description
  - Detailed explanation
  - Args with types and descriptions
  - Returns description
  - Example usage
  - API endpoint reference

Example:
```python
@mcp.tool()
async def get_gene_by_entrez_id(entrez_id: str) -> str:
    """
    Retrieve comprehensive gene information using NCBI Entrez Gene ID.

    This tool provides detailed information about a gene including its symbol,
    name, chromosomal location, summary, transcripts, and links to various databases.

    Args:
        entrez_id: NCBI Entrez Gene ID (e.g., "7157" for TP53)

    Returns:
        JSON string with gene information

    Example:
        get_gene_by_entrez_id("7157")  # TP53

    API Endpoint: GET /gene/entrezId/:entrezId
    """
    # Implementation
```

## Adding New Tools

When adding new MCP tools:

1. **Add the tool function** to `server.py`
   - Use `@mcp.tool()` decorator
   - Follow naming convention: verb_noun_by_identifier
   - Add comprehensive docstring

2. **Update documentation**
   - Add entry to `API_DOCUMENTATION.md`
   - Include in appropriate category
   - Provide usage examples

3. **Add tests**
   - Create unit test in `tests/test_server.py`
   - Create integration test (marked with `@pytest.mark.integration`)

4. **Update examples**
   - Add example queries to `examples/example_queries.py`
   - Show real-world use cases

5. **Update README**
   - Add tool to the count/summary if needed
   - Update feature list if it's a new category

## Testing Guidelines

### Unit Tests

- Test each tool function independently
- Mock API responses
- Test error handling
- Test input validation

### Integration Tests

- Test with real API calls
- Mark with `@pytest.mark.integration`
- Can be skipped in CI/CD

### Manual Testing

- Test with Claude Desktop or another MCP client
- Try various query types
- Test edge cases
- Verify error messages are helpful

## Commit Message Guidelines

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove, etc.)
- Keep first line under 72 characters
- Add details in the body if needed

Examples:
```
Add support for hg38 coordinates
Fix error handling in variant queries
Update API documentation for new tools
Remove deprecated cache configuration
```

## Pull Request Guidelines

- One feature/fix per pull request
- Update all relevant documentation
- Add tests for new features
- Ensure all tests pass
- Reference any related issues

## Documentation

When updating documentation:

- Keep README.md concise and focused on getting started
- Put detailed information in API_DOCUMENTATION.md
- Update CHANGELOG.md for all notable changes
- Keep examples/example_queries.py up to date

## Troubleshooting SSL Certificates

If you encounter SSL certificate verification errors when running integration tests:

```
httpx.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate
```

This is a common issue, especially on macOS, where Python doesn't automatically use
the system's SSL certificates.

### Quick Fix

```bash
# Upgrade certifi to get the latest CA certificates
pip install --upgrade certifi

# Reinstall httpx to ensure it uses the updated certificates
pip install --force-reinstall httpx
```

### Platform-Specific Solutions

**macOS:**
1. Install or update certificates via pip:
   ```bash
   pip install --upgrade certifi
   ```

2. If you installed Python from python.org, run the certificate installer:
   ```bash
   /Applications/Python\ 3.XX/Install\ Certificates.command
   ```
   (Replace 3.XX with your Python version, e.g., 3.12)

3. Restart your terminal and try again

**Linux:**
1. Update system CA certificates:
   ```bash
   sudo apt-get update
   sudo apt-get install ca-certificates
   sudo update-ca-certificates
   ```

2. Update Python's certifi:
   ```bash
   pip install --upgrade certifi
   ```

**Windows:**
1. Update certifi:
   ```bash
   pip install --upgrade certifi
   ```

2. Reinstall httpx:
   ```bash
   pip install --force-reinstall httpx
   ```

### Additional Checks

If problems persist:

1. **Verify certifi installation:**
   ```bash
   pip show certifi
   python -c "import certifi; print(certifi.where())"
   ```

2. **Check for proxy issues:**
   - Ensure you're not behind a corporate proxy that intercepts SSL
   - If using a proxy, you may need to configure SSL certificate verification differently

3. **Test SSL connectivity:**
   ```python
   import ssl
   import certifi
   context = ssl.create_default_context(cafile=certifi.where())
   print("SSL context created successfully")
   ```

### Running Tests Without Network Access

Integration tests require network access to the MARRVEL API. If you're working
offline or SSL certificates cannot be fixed, you can skip integration tests:

```bash
# Run only unit tests (skip integration tests)
pytest -m "not integration"

# This will run all tests except those marked with @pytest.mark.integration
```

The CI/CD pipeline will still run all tests, including integration tests,
in an environment with proper SSL configuration.

## Questions?

If you have questions about contributing:
- Open a GitHub issue
- Check existing documentation
- Review similar tools in the codebase

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards other contributors

## Recognition

All contributors will be recognized in the project documentation.

Thank you for contributing to MARRVEL-MCP!
