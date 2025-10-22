# MARRVEL-MCP Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Assistant / Claude                     │
│                     (MCP Client Application)                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ MCP Protocol
                           │ (JSON-RPC)
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                      MARRVEL-MCP Server                          │
│                        (FastMCP/Python)                          │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    30+ MCP Tools                         │   │
│  │                                                          │   │
│  │  Gene Tools        Variant Tools      Disease Tools     │   │
│  │  ├─ By Entrez ID   ├─ dbNSFP         ├─ OMIM by MIM    │   │
│  │  ├─ By Symbol      ├─ ClinVar        ├─ OMIM by Gene   │   │
│  │  └─ By Position    ├─ gnomAD         └─ OMIM Variants  │   │
│  │                    ├─ DGV                                │   │
│  │  Ortholog Tools    ├─ DECIPHER                          │   │
│  │  ├─ DIOPT          └─ Geno2MP                           │   │
│  │  └─ Alignment                                           │   │
│  │                    Expression Tools   Utility Tools      │   │
│  │                    ├─ GTEx            ├─ HGVS Validator │   │
│  │                    ├─ Ortho. Expr.    └─ Variant Conv.  │   │
│  │                    └─ Pharos                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              HTTP Client (httpx)                         │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           │ HTTP/REST
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                     MARRVEL REST API                             │
│                  http://api.marrvel.org/data                     │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   Gene DB    │  │  Variant DB  │  │  Disease DB  │         │
│  │   (NCBI)     │  │  (ClinVar,   │  │   (OMIM)     │         │
│  │              │  │   gnomAD)    │  │              │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Ortholog DB │  │ Expression   │  │  Utility     │         │
│  │   (DIOPT)    │  │  (GTEx)      │  │  (Mutalyzer) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Example: Gene Query

```
User Query: "Tell me about the TP53 gene"
                │
                ▼
        ┌───────────────┐
        │ AI Assistant  │
        └───────┬───────┘
                │ Interprets query
                │ Selects appropriate tool
                ▼
        ┌────────────────────────┐
        │ MCP Tool Selection     │
        │ get_gene_by_entrez_id  │
        └───────┬────────────────┘
                │ tool_call(entrez_id="7157")
                ▼
        ┌────────────────────────┐
        │ MARRVEL-MCP Server     │
        │ server.py              │
        └───────┬────────────────┘
                │ fetch_marrvel_data("/gene/entrezId/7157")
                ▼
        ┌────────────────────────┐
        │ HTTP Request           │
        │ httpx.AsyncClient      │
        └───────┬────────────────┘
                │ GET http://api.marrvel.org/data/gene/entrezId/7157
                ▼
        ┌────────────────────────┐
        │ MARRVEL API            │
        │ Database Query         │
        └───────┬────────────────┘
                │ JSON Response
                ▼
        ┌────────────────────────┐
        │ Response Processing    │
        │ Format & Return        │
        └───────┬────────────────┘
                │ JSON string
                ▼
        ┌────────────────────────┐
        │ AI Assistant           │
        │ Formats for User       │
        └───────┬────────────────┘
                │
                ▼
    "TP53 (Tumor Protein P53) is a gene
     located on chromosome 17..."
```

## Tool Categories

### 1. Gene Tools (3 tools)
```
get_gene_by_entrez_id ──────► /gene/entrezId/:id
get_gene_by_symbol ──────────► /gene/taxonId/:taxon/symbol/:symbol
get_gene_by_position ────────► /gene/chr/:chr/pos/:pos
```

### 2. Variant Analysis Tools (13 tools)
```
get_variant_dbnsfp ──────────► /dbnsfp/variant/:variant
get_clinvar_* ───────────────► /clinvar/gene/...
get_gnomad_* ────────────────► /gnomad/...
get_dgv_* ───────────────────► /dgv/...
get_decipher_* ──────────────► /decipher/...
get_geno2mp_* ───────────────► /geno2mp/...
```

### 3. Disease Tools (3 tools)
```
get_omim_by_mim_number ──────► /omim/mimNumber/:mim
get_omim_by_gene_symbol ─────► /omim/gene/symbol/:symbol
get_omim_variant ────────────► /omim/gene/symbol/:symbol/variant/:var
```

### 4. Ortholog Tools (2 tools)
```
get_diopt_orthologs ─────────► /diopt/ortholog/gene/entrezId/:id
get_diopt_alignment ─────────► /diopt/alignment/gene/entrezId/:id
```

### 5. Expression Tools (3 tools)
```
get_gtex_expression ─────────► /gtex/gene/entrezId/:id
get_ortholog_expression ─────► /expression/orthologs/gene/entrezId/:id
get_pharos_targets ──────────► /pharos/targets/gene/entrezId/:id
```

### 6. Utility Tools (2 tools)
```
validate_hgvs_variant ───────► /mutalyzer/hgvs/:hgvs
convert_protein_variant ─────► /transvar/protein/:protein
```

## Component Details

### FastMCP Server (`server.py`)
- **Framework**: FastMCP (Model Context Protocol)
- **Language**: Python 3.10+
- **Async Support**: Uses `asyncio` and `httpx` for async HTTP
- **Tool Decorator**: `@mcp.tool()` registers functions as MCP tools
- **Error Handling**: Try-catch blocks with descriptive error messages

### HTTP Client
- **Library**: httpx (async HTTP client)
- **Timeout**: 30 seconds (configurable in `config.py`)
- **Base URL**: http://api.marrvel.org/data
- **Response Format**: JSON

### Configuration (`config.py`)
- API settings (URL, timeout, retries)
- Taxonomy IDs for common species
- Logging configuration
- Error message templates
- Tool categorization

## Error Handling

```
User Query
    │
    ▼
MCP Tool Call
    │
    ├─► Valid Input ──► API Call ──┬─► Success ──► Return Data
    │                               │
    │                               └─► API Error ──► Error Message
    │
    └─► Invalid Input ──► Validation Error ──► Helpful Message
```

## Security Considerations

1. **Read-Only Access**: All operations are GET requests (read-only)
2. **No Authentication**: MARRVEL API is public (no API keys needed)
3. **Input Validation**: Tools validate input format before API calls
4. **Rate Limiting**: Consider implementing in `config.py` if needed
5. **Timeout Protection**: 30-second timeout prevents hanging requests

## Performance Optimization

### Current
- Async HTTP requests for non-blocking I/O
- Single request per tool call

### Future Enhancements
- Response caching (template in `config.py`)
- Batch requests for multiple variants
- Connection pooling
- Request retries with exponential backoff

## Deployment Options

### Option 1: Claude Desktop (Recommended)
```
claude_desktop_config.json
    │
    └─► Python Process
            │
            └─► server.py (FastMCP)
                    │
                    └─► MARRVEL API
```

### Option 2: Standalone Server
```
$ python server.py
Listening on stdio for MCP connections...
```

### Option 3: Custom MCP Client
```python
from mcp import ClientSession

async with ClientSession(...) as session:
    result = await session.call_tool("get_gene_by_entrez_id",
                                     {"entrez_id": "7157"})
```

## Testing Strategy

### Unit Tests
- Mock API responses
- Test tool logic
- Validate error handling

### Integration Tests
- Real API calls
- End-to-end workflows
- Performance testing

### Manual Testing
- Claude Desktop integration
- Real-world queries
- Edge case scenarios

## Monitoring & Logging

```python
# Future enhancement: Structured logging
import logging

logger = logging.getLogger(__name__)
logger.info(f"Tool called: {tool_name}")
logger.debug(f"API request: {endpoint}")
logger.error(f"Error: {error_message}")
```

## Version Compatibility

- **Python**: 3.10+
- **FastMCP**: 0.3.0+
- **httpx**: 0.27.0+
- **MARRVEL API**: v2
- **MCP Protocol**: Latest

---

For implementation details, see `server.py`
For configuration options, see `config.py`
For usage examples, see `examples/example_queries.py`
