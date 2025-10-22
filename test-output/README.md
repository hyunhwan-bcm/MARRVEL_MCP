# Test Output Directory

This directory contains captured API responses and test artifacts generated during test execution.

## Files

### `api_responses.json`
Structured JSON file containing all captured API calls:
- Test name
- Tool name
- API endpoint
- Input parameters
- Output JSON
- Status (success/error)
- Timestamp

### `api_responses.md`
Human-readable markdown table with the same information, formatted for:
- GitHub PR comments
- GitHub Actions summaries
- Local viewing

## Usage

These files are automatically generated when running integration tests:

```bash
pytest tests/ -m integration_api -v
```

## GitHub Integration

In CI/CD, these files are:
1. **Uploaded as artifacts** - downloadable from Actions tab
2. **Posted as PR comments** - automatic table in pull requests
3. **Added to job summary** - visible in Actions summary page

See [docs/API_RESPONSE_CAPTURE.md](../docs/API_RESPONSE_CAPTURE.md) for full documentation.
