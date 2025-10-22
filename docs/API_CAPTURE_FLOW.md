# API Response Capture - System Flow

## Overview Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Developer Workflow                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. Write Integration Test with api_capture Fixture            │
│                                                                 │
│     @pytest.mark.integration_api                                │
│     async def test_my_api(api_capture):                         │
│         result = await fetch_marrvel_data("/endpoint")          │
│         api_capture.log_response(...)  # ← Capture!             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. Run Tests Locally or in CI                                  │
│                                                                 │
│     pytest tests/ -m integration_api -v                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. conftest.py Captures Responses Automatically                │
│                                                                 │
│     • Stores in global _api_responses list                      │
│     • Tracks test name, tool, endpoint, I/O, status             │
│     • Includes timestamps and error messages                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. pytest_sessionfinish Hook (end of tests)                    │
│                                                                 │
│     • Generates api_responses.json                              │
│     • Generates api_responses.md                                │
│     • Saves to test-output/ directory                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. Local Use: View Files Directly                              │
│                                                                 │
│     cat test-output/api_responses.md                            │
│     cat test-output/api_responses.json | jq                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  5. GitHub CI: Automatic Processing                             │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┴───────────────────┐
          │                                       │
          ▼                                       ▼
┌──────────────────────┐               ┌──────────────────────┐
│  Upload Artifacts    │               │  PR Comment          │
│                      │               │                      │
│  • JSON files        │               │  • Summary table     │
│  • Markdown files    │               │  • Detailed JSON     │
│  • Test reports      │               │  • Auto-truncate     │
│  • Coverage data     │               │    if too large      │
└──────────────────────┘               └──────────────────────┘
          │                                       │
          ▼                                       ▼
┌──────────────────────┐               ┌──────────────────────┐
│  Actions Summary     │               │  Download & View     │
│                      │               │                      │
│  • Test metrics      │               │  • Click artifact    │
│  • Coverage %        │               │  • Extract ZIP       │
│  • API response      │               │  • Open in browser   │
│    table             │               │    or editor         │
└──────────────────────┘               └──────────────────────┘
```

## Data Flow

```
Test Execution
    │
    ├─► API Call: fetch_marrvel_data("/gene/entrezId/7157")
    │       │
    │       ▼
    │   MARRVEL API
    │       │
    │       ▼
    │   JSON Response: {"symbol": "TP53", "entrezId": "7157", ...}
    │       │
    │       ▼
    ├─► api_capture.log_response(...)
    │       │
    │       ▼
    │   Stored in _api_responses[] global list
    │       │
    │       ▼
    ├─► Test Continues...
    │
    ▼
Test Session Ends
    │
    ▼
pytest_sessionfinish()
    │
    ├─► Generate JSON
    │   │
    │   ▼
    │   {
    │     "total_api_calls": 5,
    │     "api_calls": [
    │       {
    │         "test_name": "...",
    │         "tool_name": "get_gene_by_entrez_id",
    │         "endpoint": "/gene/entrezId/7157",
    │         "input": {"entrez_id": "7157"},
    │         "output": {...full response...},
    │         "status": "success",
    │         "timestamp": "..."
    │       }
    │     ]
    │   }
    │   │
    │   ▼
    │   Save to test-output/api_responses.json
    │
    ├─► Generate Markdown
    │   │
    │   ▼
    │   # MARRVEL API Test Responses
    │
    │   | Test | Tool | Endpoint | Input | Output | Status |
    │   |------|------|----------|-------|--------|--------|
    │   | test_gene_api | get_gene... | /gene/... | {...} | {...} | ✅ |
    │
    │   ## Detailed Responses
    │   ...full JSON for each call...
    │   │
    │   ▼
    │   Save to test-output/api_responses.md
    │
    ▼
Done!
```

## GitHub Integration Flow

```
Push to GitHub / Create PR
    │
    ▼
GitHub Actions Triggered
    │
    ├─► Setup Python 3.10, 3.11, 3.12, 3.13
    │
    ├─► Install Dependencies
    │   └─► pytest, pytest-html, pytest-json-report, pytest-cov, etc.
    │
    ├─► Run Unit Tests
    │   └─► Generate coverage reports
    │
    ├─► Run Integration Tests
    │   └─► API responses captured automatically
    │
    ├─► Upload Artifacts
    │   └─► test-output/ directory with all JSON/MD files
    │
    ├─► Generate Summary
    │   ├─► Parse test-report-unit-*.json
    │   ├─► Parse coverage-*.xml
    │   └─► Add to $GITHUB_STEP_SUMMARY
    │
    └─► Post PR Comment (if PR)
        ├─► Read test-output/api_responses.md
        ├─► Truncate if > 65KB
        └─► Post as comment using github-script
```

## File Locations

### Local Development
```
your-workspace/
└── test-output/
    ├── api_responses.json     ← Machine-readable
    └── api_responses.md       ← Human-readable
```

### GitHub CI Artifacts
```
Actions > Workflow Run > Artifacts
└── test-reports-py3.13.zip
    ├── test-report-unit-3.13.html
    ├── test-report-integration-3.13.html
    ├── junit-*.xml
    ├── coverage-3.13.xml
    ├── htmlcov-3.13/
    └── test-output/
        ├── api_responses.json  ← Download this!
        └── api_responses.md    ← Or this!
```

### GitHub PR
```
Pull Request
├── Checks Tab
│   └── CI > Run Tests (Python 3.13)
│       └── Summary (scroll to bottom)
│           └── Test Results Summary 🧪
│               └── API Response Capture 📡
│                   └── Full table with all responses
│
└── Conversation Tab
    └── Bot Comment
        └── # MARRVEL API Test Responses
            └── Summary table + detailed JSON
```

## Data Format Example

### Single API Call Record
```json
{
  "test_name": "tests/integration/api/test_api_capture_example.py::test_gene_api_with_capture",
  "tool_name": "get_gene_by_entrez_id",
  "endpoint": "/gene/entrezId/7157",
  "input": {
    "entrez_id": "7157"
  },
  "output": {
    "symbol": "TP53",
    "entrezId": "7157",
    "name": "tumor protein p53",
    "chr": "17",
    "type": "protein-coding",
    ... (full response)
  },
  "status": "success",
  "error": null,
  "timestamp": "2025-10-22T20:34:20.995165+00:00"
}
```

### Error Record
```json
{
  "test_name": "tests/integration/api/test_api_capture_example.py::test_variant_api_with_capture",
  "tool_name": "get_variant_dbnsfp",
  "endpoint": "/variant/dbnsfp/17-7577121-C-T",
  "input": {
    "variant": "17-7577121-C-T"
  },
  "output": null,
  "status": "error",
  "error": "JSONDecodeError: Expecting value: line 1 column 1 (char 0)",
  "timestamp": "2025-10-22T20:35:37.954368+00:00"
}
```

## Summary

This system provides **end-to-end traceability** of API interactions:

1. ✅ **Capture**: Automatic during test execution
2. ✅ **Store**: JSON + Markdown formats
3. ✅ **Display**: GitHub PR comments + Actions summary
4. ✅ **Archive**: Downloadable artifacts
5. ✅ **Review**: Human-readable tables

All without manual intervention - just add the `api_capture` fixture to your tests!
