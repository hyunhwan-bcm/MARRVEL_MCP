# MARRVEL-MCP Package Structure

This directory contains the refactored MARRVEL-MCP package organized into modules for better maintainability and readability.

## Directory Structure

```
marrvel_mcp/
├── __init__.py              # Package initialization
├── config.py                # Configuration settings
├── client.py                # HTTP client for MARRVEL API
├── server.py                # Main server creation and entry point
└── tools/                   # Tool modules organized by category
    ├── __init__.py          # Tools package initialization
    ├── gene_tools.py        # Gene information tools (3 tools)
    ├── variant_tools.py     # Variant analysis tools (13 tools)
    ├── disease_tools.py     # Disease/OMIM tools (3 tools)
    ├── ortholog_tools.py    # Ortholog prediction tools (2 tools)
    ├── expression_tools.py  # Expression data tools (3 tools)
    └── utility_tools.py     # Utility tools (2 tools)
```

## Module Organization

### Core Modules

- **`config.py`**: Central configuration (BASE_URL, TIMEOUT, SERVER_NAME)
- **`client.py`**: HTTP client with `fetch_marrvel_data()` function
- **`server.py`**: Server initialization with `create_server()` and `run_server()`

### Tool Modules

Each tool module follows this pattern:
1. Imports necessary dependencies
2. Defines a `register_*_tools(mcp)` function
3. Contains related tool implementations

#### Tool Categories

1. **Gene Tools** (`gene_tools.py`)
   - `get_gene_by_entrez_id`
   - `get_gene_by_symbol`
   - `get_gene_by_position`

2. **Variant Tools** (`variant_tools.py`)
   - dbNSFP annotations
   - ClinVar data
   - gnomAD frequencies
   - DGV structural variants
   - DECIPHER data
   - Geno2MP associations

3. **Disease Tools** (`disease_tools.py`)
   - OMIM by MIM number
   - OMIM by gene symbol
   - OMIM variant information

4. **Ortholog Tools** (`ortholog_tools.py`)
   - DIOPT ortholog predictions
   - Protein sequence alignments

5. **Expression Tools** (`expression_tools.py`)
   - GTEx expression data
   - Ortholog expression
   - Pharos drug targets

6. **Utility Tools** (`utility_tools.py`)
   - HGVS variant validation
   - Protein variant conversion

## Usage

### As a Package

```python
from marrvel_mcp import create_server

# Create server instance
mcp = create_server()

# Run the server
mcp.run()
```

### Command Line

After installation:

```bash
# Install the package
pip install -e .

# Run the server
marrvel-mcp
```

### Importing Specific Components

```python
from marrvel_mcp.client import fetch_marrvel_data
from marrvel_mcp.config import BASE_URL
from marrvel_mcp.tools import register_gene_tools
```

## Benefits of This Structure

1. **Modularity**: Each tool category is in its own file
2. **Maintainability**: Easy to find and update specific tools
3. **Testability**: Can test individual modules independently
4. **Readability**: Smaller files are easier to understand
5. **Scalability**: Easy to add new tool categories
6. **Reusability**: Can import specific components as needed

## Adding New Tools

To add a new tool:

1. Choose the appropriate module (or create a new one)
2. Add the tool function with `@mcp.tool()` decorator
3. If creating a new module:
   - Create `marrvel_mcp/tools/new_tools.py`
   - Add `register_new_tools(mcp)` function
   - Import and call in `server.py`
   - Export in `tools/__init__.py`

## Migration from Old server.py

The old monolithic `server.py` has been refactored into this package structure. The root `server.py` can be updated to use the package:

```python
from marrvel_mcp.server import run_server

if __name__ == "__main__":
    run_server()
```
