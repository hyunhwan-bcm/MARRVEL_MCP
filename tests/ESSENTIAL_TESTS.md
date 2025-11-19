# Essential Test Suite - Selection Criteria

## Overview

This document explains the rationale behind the reduced test suite for faster CI execution while maintaining critical code coverage.

## Test Reduction Summary

- **Previous:** 100 tests across 9 test files
- **Current:** 22 tests across 6 test files
- **Reduction:** 78% fewer tests (~1.8s runtime vs ~3.8s previously)

## Selection Criteria

Tests were retained based on the following criteria:

1. **Critical for Core Functionality**: Tests that validate the essential features of the MARRVEL-MCP server
2. **High Impact on Repository Health**: Tests that catch breaking changes in critical code paths
3. **Representative Coverage**: Tests that cover different functional areas without exhaustive permutations
4. **Integration Smoke Tests**: Essential API integration tests to verify external dependencies work

## Retained Tests by Category

### 1. MCP Tool Smoke Tests (8 tests)
**File:** `test_tools_smoke.py`

Selected 8 representative tools from 33 original tool tests, covering:
- Gene queries: `get_gene_by_entrez_id`, `get_gene_by_symbol`
- Variant analysis: `get_variant_annotation_by_genomic_position`, `get_clinvar_by_variant`
- Disease associations: `search_omim_by_disease_name`
- Ortholog information: `get_diopt_orthologs_by_entrez_id` (unique DIOPT integration)
- Literature search: `search_pubmed`
- Coordinate conversion: `liftover_hg38_to_hg19`

**Rationale:** These tests exercise the main categories of MARRVEL functionality without testing every variation of similar tools.

### 2. Configuration Tests (7 tests)
**Files:** `test_llm_provider_config.py`, `test_openrouter_model_config.py`

All configuration tests retained:
- API base URL resolution for different providers
- Model configuration and environment variable overrides
- Provider-specific defaults

**Rationale:** Configuration is critical for the system to function correctly with various LLM providers.

### 3. Cache Functionality (2 tests)
**File:** `test_cache_essential.py`

Retained only:
- Basic save and load operations
- Cache clearing functionality

**Rationale:** Validates the core cache mechanism works without exhaustively testing every edge case.

### 4. Subset Parsing (3 tests)
**File:** `test_subset_essential.py`

Retained only:
- Basic range parsing
- Combined range and individual indices
- Empty string handling

**Rationale:** Covers the main parsing scenarios without testing every edge case.

### 5. Retry Logic (2 tests)
**File:** `test_retry_essential.py`

Retained only:
- Successful call on first attempt
- Retry with 500 error

**Rationale:** Validates the retry mechanism works for the most common scenario (server errors).

## Removed Test Categories

### Non-Essential Tests Removed:
1. **Extensive Cache Tests** (13 tests removed): Detailed path generation, unicode handling, multiple edge cases
2. **Exhaustive Subset Parsing** (18 tests removed): Extensive edge case testing, error conditions
3. **Detailed Retry Logic** (7 tests removed): All retry delay patterns, logging verification
4. **Concurrency Tests** (7 tests removed): Progress bar functionality, concurrency parameter parsing
5. **HTML Report Tests** (5 tests removed): Report generation, which is not critical for core MCP functionality
6. **MCP Subset Evaluation** (3 tests removed): Test case filtering functionality
7. **Redundant Tool Tests** (25 tests removed): Similar tools that provide overlapping coverage

## Benefits

1. **Faster CI Execution**: ~50% reduction in test execution time
2. **Easier Maintenance**: Fewer tests to maintain and update
3. **Clear Focus**: Tests focus on critical functionality
4. **Quick Feedback**: Developers get faster feedback on PR checks

## Coverage Philosophy

The essential test suite follows the **80/20 rule**: 
- 20% of tests provide 80% of the value in catching real bugs
- Focus on integration and critical path testing
- Avoid exhaustive unit testing of edge cases that rarely occur in production

## When to Add Tests

New tests should be added when:
1. A bug is found that wasn't caught by existing tests
2. A new critical feature is added
3. A new MCP tool category is introduced
4. Configuration or integration points change

## Maintenance

This test suite should be reviewed periodically to ensure:
- All retained tests still provide value
- New critical functionality is adequately covered
- Test execution time remains under 5 seconds
