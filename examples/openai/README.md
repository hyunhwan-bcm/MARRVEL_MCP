# OpenAI Integration Examples

This directory contains example scripts demonstrating how to use MARRVEL-MCP with OpenAI's API.

## Files

### Production-Ready Example
**`openai_marrvel_simple.py`** ✅ **Recommended**
- Clean, working example with 3 query types
- Independent queries (no context accumulation)
- Handles token limits properly
- **Model**: gpt-4o-mini (latest efficient model)

**Usage:**
```bash
export OPENAI_API_KEY='sk-...'
python3 examples/openai/openai_marrvel_simple.py
```

**Queries demonstrated:**
1. Gene information lookup (TP53)
2. Disease associations (BRCA1)
3. Ortholog search (TP53 across species)

### Advanced Example
**`openai_marrvel_example.py`**
- Includes truncation logic for large datasets
- Conversational context accumulation
- More complex error handling

**Note:** May encounter token limits with ClinVar queries due to large datasets.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set your API key:**
   ```bash
   export OPENAI_API_KEY='your-openai-api-key'
   ```

3. **Run the example:**
   ```bash
   python3 examples/openai/openai_marrvel_simple.py
   ```

## Expected Output

```
======================================================================
🧬 MARRVEL + OpenAI Integration (gpt-4o-mini)
======================================================================

🧬 Query: What is the TP53 gene?
🤖 Processing...
📡 Calling: get_gene_by_symbol({"gene_symbol": "TP53"})
✅ Answer:
The TP53 gene encodes the tumor protein p53, a crucial protein involved
in regulating the cell cycle and maintaining genomic stability...
----------------------------------------------------------------------
```

## Available Functions

The examples use these MARRVEL functions:
- `get_gene_by_symbol()` - Gene information
- `get_omim_by_gene_symbol()` - Disease associations
- `get_diopt_orthologs()` - Cross-species orthologs
- `get_clinvar_by_gene_symbol()` - Clinical variants (large datasets!)

## Known Limitations

### ClinVar Queries
ClinVar datasets for genes like CFTR, TP53, BRCA1 can be **very large** (500KB-800KB):
- Exceed OpenAI's 128K token context limit
- Cannot be passed through function calling

**Workarounds:**
1. Use the MCP server directly
2. Query specific variants instead of entire gene sets
3. Implement server-side summarization

## Configuration

### Model Selection
Both examples use `gpt-4o-mini` by default. To change:

```python
response = client.chat.completions.create(
    model="gpt-4o-mini",  # Change to gpt-4, gpt-4-turbo, etc.
    messages=messages,
    functions=MARRVEL_FUNCTIONS,
    function_call="auto"
)
```

### Adding More Functions
To add additional MARRVEL tools:

1. Import from `server.py`:
   ```python
   from server import get_gnomad_by_gene_symbol
   ```

2. Add to `MARRVEL_FUNCTIONS` list with OpenAI function schema

3. Add to `FUNCTION_MAP` dictionary

## Performance

- **Response Time**: 3-8 seconds per query
- **Cost**: ~$0.001-0.002 per query (gpt-4o-mini)
- **Token Usage**: ~2,000-5,000 tokens per query

## Troubleshooting

**"context_length_exceeded" error:**
- Dataset too large for OpenAI's token limit
- Solution: Use more specific queries or implement summarization

**"Invalid API key":**
- Verify: `echo $OPENAI_API_KEY`
- Key should start with `sk-`

**ModuleNotFoundError:**
- Run: `pip install -r requirements.txt`
- Ensure you're in the project root

## More Information

See the main documentation:
- `OPENAI_INTEGRATION.md` - Complete integration guide
- `OPENAI_INTEGRATION_SUMMARY.md` - Results and limitations
- `API_DOCUMENTATION.md` - All available MARRVEL functions

## Contributing

To improve these examples:
1. Test with different genes and queries
2. Add error handling for edge cases
3. Implement caching for frequent queries
4. Add streaming support for long responses
