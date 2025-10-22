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

   # Run tests
   pytest tests/ -v

   # Test with Claude Desktop or MCP client
   python server.py
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "Add feature: description of your changes"
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   ```
   Then create a pull request on GitHub.

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
