# PR Title
Reorganize project structure, add OpenAI integration, and fix ClinVar endpoint bug

# PR Description

## Summary
This PR improves project organization, adds OpenAI integration support, and fixes a critical API endpoint bug that was causing test failures.

## Changes

### 🗂️ Project Reorganization
- Move test files to `tests/` directory
- Move OpenAI examples to `examples/openai/` directory
- Add comprehensive READMEs for both directories
- Update main README with new structure

### 🤖 OpenAI Integration
- Add production-ready OpenAI function calling examples
- Support gpt-4o-mini model
- Include working example scripts with documentation
- Provide quick start guide and troubleshooting

### 🐛 Bug Fix
- Fix incorrect ClinVar API endpoint (`/clinvar/gene/variant/` → `/clinvar/variant/`)
- Add missing `@pytest.mark.asyncio` decorators to async tests

## Impact

**Files Changed:** 8 files, +283/-9 lines

**Before:**
- ❌ 1/17 tests failing (wrong API endpoint)
- Files scattered in root directory

**After:**
- ✅ 17/17 tests passing (100%)
- Clean, organized directory structure
- Comprehensive documentation

## Testing
```bash
pytest tests/ -v
# Result: 17 passed in 4.63s ✅
```

## Breaking Changes
None - only file relocations, all functionality preserved

## Documentation
- ✅ `tests/README.md` - Test documentation (90 lines)
- ✅ `examples/openai/README.md` - OpenAI integration guide (145 lines)
- ✅ Updated main `README.md` with new structure

## Review Focus
1. Directory structure makes sense?
2. Documentation is clear?
3. OpenAI examples work correctly?
4. Bug fix resolves the issue?

---

See `PULL_REQUEST.md` for complete details and migration guide.
