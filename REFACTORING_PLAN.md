# MARRVEL-MCP Refactoring Plan

## Overview
Refactor monolithic `server.py` (791 lines) into a modular, maintainable structure with clear separation of concerns.

## Current Structure
```
server.py (791 lines)
├── fetch_marrvel_data() helper
├── Gene Tools (3 functions, ~140 lines)
├── Variant Analysis Tools (13 functions, ~280 lines)
├── Disease Tools (3 functions, ~80 lines)
├── Ortholog Tools (2 functions, ~60 lines)
├── Expression Tools (3 functions, ~90 lines)
└── Utility Tools (2 functions, ~70 lines)
```

## Target Structure
```
MARRVEL_MCP/
├── server.py (main entry point, ~50 lines)
├── config.py (unchanged)
├── src/
│   ├── __init__.py
│   ├── utils/
│   │   ├── __init__.py
│   │   └── api_client.py (fetch_marrvel_data + error handling)
│   └── tools/
│       ├── __init__.py
│       ├── gene_tools.py (3 functions)
│       ├── variant_tools.py (13 functions)
│       ├── disease_tools.py (3 functions)
│       ├── ortholog_tools.py (2 functions)
│       ├── expression_tools.py (3 functions)
│       └── utility_tools.py (2 functions)
├── tests/
│   ├── test_server.py
│   ├── test_api_client.py
│   └── test_tools/
│       ├── test_gene_tools.py
│       ├── test_variant_tools.py
│       ├── test_disease_tools.py
│       ├── test_ortholog_tools.py
│       ├── test_expression_tools.py
│       └── test_utility_tools.py
└── examples/ (unchanged)
```

## Refactoring Steps (10 PRs)

### PR #1: Extract API Client Utilities
**Branch**: `hj/extract-api-client`
**Purpose**: Extract core API communication logic
**Files**:
- Create `src/utils/api_client.py`
- Move `fetch_marrvel_data()` helper
- Add enhanced error handling
- Create `src/__init__.py` and `src/utils/__init__.py`

**Benefits**:
- Centralizes API communication
- Makes it easier to add caching, retry logic, rate limiting
- Reusable across all tool modules

---

### PR #2: Extract Gene Tools Module
**Branch**: `hj/extract-gene-tools`
**Purpose**: Separate gene-related functionality
**Files**:
- Create `src/tools/gene_tools.py`
- Move 3 functions:
  - `get_gene_by_entrez_id()`
  - `get_gene_by_symbol()`
  - `get_gene_by_position()`
- Create `src/tools/__init__.py`

**Benefits**:
- Clear domain separation
- Easy to extend with new gene tools
- Simple testing of gene-specific logic

---

### PR #3: Extract Variant Analysis Tools
**Branch**: `hj/extract-variant-tools`
**Purpose**: Separate variant analysis functionality (largest module)
**Files**:
- Create `src/tools/variant_tools.py`
- Move 13 functions:
  - `get_variant_dbnsfp()`
  - `get_clinvar_by_variant()`
  - `get_clinvar_by_gene_symbol()`
  - `get_clinvar_by_entrez_id()`
  - `get_gnomad_variant()`
  - `get_gnomad_by_gene_symbol()`
  - `get_gnomad_by_entrez_id()`
  - `get_dgv_variant()`
  - `get_dgv_by_entrez_id()`
  - `get_decipher_variant()`
  - `get_decipher_by_location()`
  - `get_geno2mp_variant()`
  - `get_geno2mp_by_entrez_id()`

**Benefits**:
- Isolates complex variant logic
- Easier to maintain database-specific integrations
- Can be further subdivided if needed

---

### PR #4: Extract Disease Tools (OMIM)
**Branch**: `hj/extract-disease-tools`
**Purpose**: Separate disease/phenotype functionality
**Files**:
- Create `src/tools/disease_tools.py`
- Move 3 functions:
  - `get_omim_by_mim_number()`
  - `get_omim_by_gene_symbol()`
  - `get_omim_variant()`

**Benefits**:
- Groups OMIM-related queries
- Makes it easy to add other disease databases (HPO, Orphanet, etc.)

---

### PR #5: Extract Ortholog Tools (DIOPT)
**Branch**: `hj/extract-ortholog-tools`
**Purpose**: Separate ortholog analysis functionality
**Files**:
- Create `src/tools/ortholog_tools.py`
- Move 2 functions:
  - `get_diopt_orthologs()`
  - `get_diopt_alignment()`

**Benefits**:
- Isolates cross-species comparison logic
- Easy to extend with other ortholog tools

---

### PR #6: Extract Expression Tools
**Branch**: `hj/extract-expression-tools`
**Purpose**: Separate expression and druggability functionality
**Files**:
- Create `src/tools/expression_tools.py`
- Move 3 functions:
  - `get_gtex_expression()`
  - `get_ortholog_expression()`
  - `get_pharos_targets()`

**Benefits**:
- Groups expression-related queries
- Makes it easy to add more expression databases

---

### PR #7: Extract Utility Tools
**Branch**: `hj/extract-utility-tools`
**Purpose**: Separate utility/helper functionality
**Files**:
- Create `src/tools/utility_tools.py`
- Move 2 functions:
  - `validate_hgvs_variant()`
  - `convert_protein_variant()`

**Benefits**:
- Groups validation and conversion utilities
- Easy to add more utility functions

---

### PR #8: Refactor Main Server
**Branch**: `hj/refactor-main-server`
**Purpose**: Update server.py to use modular structure
**Files**:
- Refactor `server.py` to import from modules
- Keep only MCP initialization and tool registration
- Update imports

**New server.py structure**:
```python
from mcp.server.fastmcp import FastMCP
from src.tools import gene_tools, variant_tools, disease_tools
from src.tools import ortholog_tools, expression_tools, utility_tools

mcp = FastMCP("MARRVEL")

# Tools are automatically registered via decorators
# Just need to import the modules

if __name__ == "__main__":
    mcp.run()
```

**Benefits**:
- Clean, minimal main file
- Clear overview of all tool modules
- Easy to add/remove tool categories

---

### PR #9: Update Tests
**Branch**: `hj/update-tests`
**Purpose**: Update test structure to match new modules
**Files**:
- Create `tests/test_api_client.py`
- Create `tests/test_tools/` directory
- Create individual test files for each tool module
- Update existing `tests/test_server.py`

**Benefits**:
- Better test organization
- Easier to run targeted tests
- Clearer test coverage per module

---

### PR #10: Update Documentation
**Branch**: `hj/update-documentation`
**Purpose**: Update all documentation to reflect new structure
**Files**:
- Update `README.md` with new structure
- Update `ARCHITECTURE.md` with module diagrams
- Update `CONTRIBUTING.md` with module guidelines
- Update `API_DOCUMENTATION.md` if needed
- Add `MIGRATION_GUIDE.md` for users

**Benefits**:
- Keeps documentation in sync
- Helps new contributors understand structure
- Provides migration path for existing users

---

## Design Principles

### 1. Single Responsibility
Each module handles one category of tools

### 2. Minimal Dependencies
- Modules depend only on `api_client`
- No circular dependencies
- Clear import hierarchy

### 3. Backward Compatibility
- All existing tool names unchanged
- Same API interface
- Same MCP behavior

### 4. Easy Testing
- Each module independently testable
- Mock API client for unit tests
- Integration tests still work

### 5. Easy Extension
- Add new tools to appropriate module
- Create new modules for new categories
- No changes to other modules needed

## Import Hierarchy
```
server.py
    ↓
src/tools/*.py (tool modules)
    ↓
src/utils/api_client.py
    ↓
config.py
```

## Benefits of This Approach

1. **Maintainability**: Each module is ~100-200 lines, easy to understand
2. **Testability**: Can test each module independently
3. **Extensibility**: Easy to add new tools or categories
4. **Collaboration**: Multiple developers can work on different modules
5. **Debugging**: Easier to locate and fix issues
6. **Performance**: Can optimize individual modules without affecting others
7. **Documentation**: Clearer structure for documentation

## Risk Mitigation

1. **Incremental Changes**: Each PR is small and reviewable
2. **Testing**: Existing tests ensure backward compatibility
3. **Documentation**: Update docs with each PR
4. **Review Points**: Natural checkpoints after each PR
5. **Rollback**: Can revert individual PRs if issues arise

## Timeline

Each PR should take ~30-60 minutes to implement and review:
- PRs #1-7: Extract modules (7 PRs)
- PR #8: Refactor main server (critical)
- PR #9: Update tests
- PR #10: Update documentation

Total estimated time: 1-2 days for all PRs

## Success Criteria

✅ All existing tests pass
✅ No API changes (backward compatible)
✅ All tools still work via MCP
✅ Code is more maintainable
✅ Documentation is updated
✅ Clear module boundaries
