# STRING Interaction ENSP ID Handling

## Overview

The STRING interaction tools in MARRVEL-MCP have been enhanced to properly handle Ensembl Protein IDs (ENSP) returned by the STRING database. Previously, these protein IDs could cause issues when downstream code expected Ensembl Gene IDs (ENSG).

## Problem

When querying STRING protein interactions using `get_string_interactions_by_entrez_id`, the API returns connections with Ensembl protein IDs (e.g., `ENSP00000297591`). If users attempted to look up gene information using these IDs with `get_gene_by_ensembl_id`, it would fail because that function expected gene IDs (e.g., `ENSG00000188152`).

## Solution

### 1. New Helper Function

A new internal helper function `resolve_ensembl_protein_to_gene_id()` has been added that:
- Detects whether an ID is a gene ID (ENSG) or protein ID (ENSP)
- Returns gene IDs directly without conversion
- Converts protein IDs to gene IDs using the Ensembl REST API
- Provides graceful error handling with informative messages

### 2. Enhanced STRING Interactions

The `get_string_interactions_by_entrez_id` function now returns an additional field for each interaction:

```json
{
  "data": {
    "stringInteractionsByEntrezId": [
      {
        "connectedEnsemblId": "ENSP00000297591",
        "connectedEnsemblGeneId": "ENSG00000188152",
        "database": "STRING",
        "combExpDb": 0.9,
        "experiments": 5
      }
    ]
  }
}
```

**New Fields:**
- `connectedEnsemblGeneId`: The Ensembl gene ID (ENSG) corresponding to the connected protein
- `conversionError`: Only present if the conversion from ENSP to ENSG fails, contains error details

**Backward Compatibility:**
- `connectedEnsemblId`: Still present with the original protein ID (ENSP) for backward compatibility

### 3. Enhanced Gene Lookup

The `get_gene_by_ensembl_id` function now accepts both:
- Ensembl Gene IDs (ENSG...) - works as before
- Ensembl Protein IDs (ENSP...) - automatically converted to gene IDs

Example usage:
```python
# Both of these now work:
await get_gene_by_ensembl_id("ENSG00000188152")  # Gene ID
await get_gene_by_ensembl_id("ENSP00000297591")  # Protein ID - auto-converted
```

## Error Handling

If a protein ID cannot be resolved to a gene ID:
- The `connectedEnsemblGeneId` field will be `null`
- A `conversionError` field will be added with details
- The operation continues for other interactions

Example error response:
```json
{
  "connectedEnsemblId": "ENSP99999999",
  "connectedEnsemblGeneId": null,
  "conversionError": "Failed to convert ENSP to ENSG: Protein not found in Ensembl"
}
```

## Testing

Comprehensive unit tests have been added in `tests/test_string_ensp_handling.py`:
- Tests for ENSG passthrough (no conversion)
- Tests for ENSP to ENSG conversion
- Tests for invalid ID format handling
- Tests for conversion error handling
- Tests for STRING interaction integration
- Tests for enhanced gene lookup with both ID types

All tests use mocked API responses to avoid external dependencies in CI/CD.

## Implementation Details

The conversion uses the existing `get_ensembl_gene_id_from_ensembl_protein_id` function, which:
1. Queries the Ensembl REST API for the protein ID
2. Retrieves the parent transcript ID
3. Queries for the transcript to get the parent gene ID
4. Returns the gene ID

## Migration Guide

No migration is required. This is a backward-compatible enhancement:
- Existing code using `connectedEnsemblId` continues to work
- New code can use `connectedEnsemblGeneId` for direct gene ID access
- The `get_gene_by_ensembl_id` function now handles both ID types automatically
