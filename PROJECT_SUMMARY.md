# MARRVEL-MCP

Python server implementation providing MCP access to MARRVEL genetics research platform.

## Project Structure

```
MARRVEL_MCP/
├── server.py              # Main FastMCP server implementation (30+ tools)
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── README.md             # Main documentation
├── API_DOCUMENTATION.md  # Comprehensive API reference
├── QUICKSTART.md         # Quick start guide
├── CHANGELOG.md          # Version history
├── examples/
│   └── example_queries.py  # Usage examples and patterns
└── tests/
    └── test_server.py     # Unit tests
```

## Quick Links

- **Installation**: See [README.md](README.md)
- **API Reference**: See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)
- **Examples**: See [examples/example_queries.py](examples/example_queries.py)

## Tools Summary

### 30+ MCP Tools Available:

1. **Gene Tools** (3): Query gene information by ID, symbol, or position
2. **Variant Analysis** (13): Comprehensive variant annotation from multiple databases
3. **Disease Information** (3): OMIM disease associations and phenotypes
4. **Ortholog Analysis** (2): Cross-species ortholog predictions via DIOPT
5. **Expression Data** (3): GTEx tissue expression and model organism data
6. **Utilities** (2): HGVS validation and variant format conversion

## For Developers

### Running the Server

```bash
python server.py
```

### Running Tests

```bash
pytest tests/ -v
```

### Configuration

Edit `config.py` to customize:
- API endpoints and timeouts
- Logging settings
- Cache configuration (if implemented)
- Rate limiting (if implemented)

## Version

Current: 1.0.0

## License

[Add your license here]
