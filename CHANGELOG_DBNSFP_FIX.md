# DbNSFP GraphQL to REST API Migration

## Issue Summary

The `get_variant_dbnsfp` tool was experiencing GraphQL query failures due to schema incompatibilities on the MARRVEL backend API. Specifically, certain fields (FATHMM, MetaSVM, MetaLR, PROVEAN) were causing errors when queried through the GraphQL endpoint.

### Error Example
```
GraphQL query failed with execution errors:
[
  {
    "message": "Cannot query field \"FATHMM\" on type \"DbNSFPScores\".",
    "locations": [
      {
        "line": 44,
        "column": 25
      }
    ]
  },
  ...
]
```

## Root Cause Analysis

The GraphQL schema for the `dbnsfpByVariant` query had been modified on the backend, making certain prediction score fields unavailable. The large, explicit GraphQL query with dozens of field selections became fragile to backend schema changes.

## Solution

Migrated `get_variant_dbnsfp` from GraphQL to REST API, following the established pattern used by other variant tools (gnomAD, DGV, Geno2MP, etc.).

### Changes Made

1. **API Endpoint Change**
   - **Before**: GraphQL POST to `https://marrvel.org/graphql` with complex query
   - **After**: REST GET to `https://marrvel.org/data/dbNSFP/variant/{encoded_variant}`

2. **Code Simplification**
   - Removed 120+ lines of explicit GraphQL field selections
   - Simplified to 4 lines for REST API call
   - Follows the same pattern as `get_gnomad_variant`

3. **Response Format Handling**
   - **Before**: Response wrapped in `data.dbnsfpByVariant.scores`
   - **After**: Direct response with `scores` at top level
   - Updated parsing logic to handle REST API format

4. **Maintained Functionality**
   - All existing summary calculations preserved
   - Average rank score computation still works
   - Individual rank scores extraction unchanged
   - Error handling maintained

### Code Diff

**Before (GraphQL)**:
```python
async def get_variant_dbnsfp(chr: str, pos: str, ref: str, alt: str) -> str:
    try:
        data = await fetch_marrvel_data(
            f"""
            query MyQuery {{
                dbnsfpByVariant(chr: "{chr}", pos: {pos}, alt: "{alt}", ref: "{ref}", build: "hg38") {{
                    scores {{
                        CADD {{ phred rankscore rawScore }}
                        Polyphen2HDIV {{ predictions rankscore scores }}
                        # ... 20+ more method blocks ...
                    }}
                }}
            }}
            """
        )
        data_obj = json.loads(data)
        if "data" in data_obj and data_obj["data"] and "dbnsfpByVariant" in data_obj["data"]:
            variant_data = data_obj["data"]["dbnsfpByVariant"]
            # ... process scores ...
```

**After (REST API)**:
```python
async def get_variant_dbnsfp(chr: str, pos: str, ref: str, alt: str) -> str:
    try:
        # Use REST API instead of GraphQL to avoid schema compatibility issues
        # Format variant like gnomAD does: "chr:pos ref>alt"
        variant = f"{chr}:{pos} {ref}>{alt}"
        variant_uri = quote(variant, safe="")
        data = await fetch_marrvel_data(f"/dbNSFP/variant/{variant_uri}", is_graphql=False)
        
        data_obj = json.loads(data)
        # REST API returns data directly without GraphQL wrapper
        if data_obj and isinstance(data_obj, dict) and "scores" in data_obj:
            scores = data_obj["scores"]
            # ... process scores ...
```

## Benefits

1. **Resilience**: REST API is less likely to break due to schema changes
2. **Simplicity**: Code reduced from ~170 lines to ~60 lines
3. **Consistency**: Now follows the same pattern as other variant tools
4. **Maintainability**: Easier to understand and modify
5. **Performance**: Potentially faster as REST API may be more optimized

## Testing

All tests pass successfully:
- ✅ `test_tools_smoke.py` - 21 tests passed
- ✅ All repository tests - 71 tests passed
- ✅ Syntax validation with `black` formatter

## Backward Compatibility

The change is backward compatible from an API consumer perspective:
- Function signature unchanged: `get_variant_dbnsfp(chr, pos, ref, alt)`
- Output format preserved with same fields and structure
- Summary calculations maintained
- Error handling consistent

## Future Considerations

1. **Other GraphQL Tools**: Consider migrating other tools using GraphQL if REST endpoints exist:
   - `get_gene_by_entrez_id`
   - `get_gene_by_symbol`
   - `get_gene_by_position`
   - `get_clinvar_by_variant`
   - `get_diopt_orthologs_by_entrez_id`

2. **Monitoring**: Track the REST API endpoint for any changes or deprecations

3. **Documentation**: MARRVEL API documentation should document REST endpoints for all resources

## Related Files

- `server.py` - Main implementation file
- `tests/test_tools_smoke.py` - Smoke tests for all tools

## References

- MARRVEL Website: https://marrvel.org
- MARRVEL API Docs: https://marrvel.org/doc
- Issue: GraphQL query errors for dbnsfp tool
