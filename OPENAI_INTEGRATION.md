# Using MARRVEL-MCP with OpenAI

Since you have OpenAI instead of Claude Desktop, here are several ways to use the MARRVEL-MCP server with OpenAI's API.

## Option 1: Direct API Integration (Recommended for OpenAI)

The simplest approach is to call the MARRVEL API directly from your OpenAI application using the helper functions.

### Quick Test

```bash
# Test that the API integration works
python3 test_api_direct.py
```

### Example: OpenAI with Function Calling

```python
import openai
import asyncio
from server import fetch_marrvel_data

# Define functions for OpenAI
functions = [
    {
        "name": "get_gene_info",
        "description": "Get comprehensive gene information from MARRVEL",
        "parameters": {
            "type": "object",
            "properties": {
                "entrez_id": {
                    "type": "string",
                    "description": "NCBI Entrez Gene ID, e.g., '7157' for TP53"
                }
            },
            "required": ["entrez_id"]
        }
    },
    {
        "name": "get_variant_info",
        "description": "Get variant annotations from dbNSFP",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {
                    "type": "string",
                    "description": "Variant in format chr-pos-ref-alt, e.g., '17-7577121-C-T'"
                }
            },
            "required": ["variant"]
        }
    }
]

async def call_marrvel_function(function_name, arguments):
    """Execute MARRVEL function based on OpenAI's function call."""
    if function_name == "get_gene_info":
        endpoint = f"/gene/entrezId/{arguments['entrez_id']}"
        return await fetch_marrvel_data(endpoint)
    elif function_name == "get_variant_info":
        endpoint = f"/dbnsfp/variant/{arguments['variant']}"
        return await fetch_marrvel_data(endpoint)
    # Add more functions as needed

# Use with OpenAI
response = openai.ChatCompletion.create(
    model="gpt-5",
    messages=[
        {"role": "user", "content": "Tell me about the TP53 gene"}
    ],
    functions=functions,
    function_call="auto"
)

# If OpenAI calls a function
if response.choices[0].message.get("function_call"):
    function_name = response.choices[0].message["function_call"]["name"]
    arguments = json.loads(response.choices[0].message["function_call"]["arguments"])
    
    # Execute the function
    result = asyncio.run(call_marrvel_function(function_name, arguments))
    
    # Send result back to OpenAI
    second_response = openai.ChatCompletion.create(
        model="gpt-5",
        messages=[
            {"role": "user", "content": "Tell me about the TP53 gene"},
            response.choices[0].message,
            {
                "role": "function",
                "name": function_name,
                "content": json.dumps(result)
            }
        ]
    )
    print(second_response.choices[0].message["content"])
```

## Option 2: MCP via OpenAI Assistant API

If you want to use MCP protocol with OpenAI, you'll need a bridge. Here's a conceptual approach:

1. **Use MCP with OpenAI Assistants** (when they support external tools)
2. **Create a REST wrapper** around your MCP server
3. **Use Anthropic's MCP SDK** with OpenAI as the LLM backend

## Option 3: Simple REST Wrapper for OpenAI

Create a Flask/FastAPI wrapper that OpenAI can call:

```python
from fastapi import FastAPI
from server import fetch_marrvel_data

app = FastAPI()

@app.get("/gene/{entrez_id}")
async def get_gene(entrez_id: str):
    return await fetch_marrvel_data(f"/gene/entrezId/{entrez_id}")

@app.get("/variant/{variant}")
async def get_variant(variant: str):
    return await fetch_marrvel_data(f"/dbnsfp/variant/{variant}")

# Run with: uvicorn openai_wrapper:app --reload
```

Then OpenAI can call these as HTTP endpoints.

## Option 4: Interactive Testing (No OpenAI needed)

Test the tools manually:

```bash
# Run interactive tester
python3 test_mcp_client.py interactive

# Or run all automated tests
python3 test_mcp_client.py
```

## Complete OpenAI Integration Example

Here's a full working example:

```python
"""
openai_marrvel_integration.py
Complete example of using MARRVEL with OpenAI function calling
"""

import openai
import asyncio
import json
from server import fetch_marrvel_data

openai.api_key = "your-api-key-here"

# Define all MARRVEL tools as OpenAI functions
MARRVEL_FUNCTIONS = [
    {
        "name": "get_gene_by_entrez_id",
        "description": "Get gene information using NCBI Entrez Gene ID",
        "parameters": {
            "type": "object",
            "properties": {
                "entrez_id": {"type": "string", "description": "NCBI Entrez Gene ID"}
            },
            "required": ["entrez_id"]
        }
    },
    {
        "name": "get_variant_dbnsfp",
        "description": "Get variant functional predictions from dbNSFP",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string", "description": "Variant in format chr-pos-ref-alt"}
            },
            "required": ["variant"]
        }
    },
    {
        "name": "get_clinvar_variant",
        "description": "Get clinical significance from ClinVar",
        "parameters": {
            "type": "object",
            "properties": {
                "variant": {"type": "string", "description": "Variant identifier"}
            },
            "required": ["variant"]
        }
    },
    {
        "name": "get_omim_by_gene_symbol",
        "description": "Get OMIM diseases associated with a gene",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol like TP53 or BRCA1"}
            },
            "required": ["gene_symbol"]
        }
    }
]

async def execute_marrvel_function(function_name: str, arguments: dict) -> dict:
    """Map OpenAI function calls to MARRVEL API endpoints."""
    endpoint_map = {
        "get_gene_by_entrez_id": "/gene/entrezId/{entrez_id}",
        "get_variant_dbnsfp": "/dbnsfp/variant/{variant}",
        "get_clinvar_variant": "/clinvar/gene/variant/{variant}",
        "get_omim_by_gene_symbol": "/omim/gene/symbol/{gene_symbol}"
    }
    
    endpoint_template = endpoint_map.get(function_name)
    if not endpoint_template:
        return {"error": f"Unknown function: {function_name}"}
    
    endpoint = endpoint_template.format(**arguments)
    return await fetch_marrvel_data(endpoint)

def chat_with_marrvel(user_message: str):
    """Chat with OpenAI using MARRVEL tools."""
    messages = [{"role": "user", "content": user_message}]
    
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=MARRVEL_FUNCTIONS,
        function_call="auto"
    )
    
    response_message = response.choices[0].message
    
    # Check if OpenAI wants to call a function
    if response_message.get("function_call"):
        function_name = response_message["function_call"]["name"]
        arguments = json.loads(response_message["function_call"]["arguments"])
        
        print(f"🔧 Calling {function_name} with {arguments}")
        
        # Execute MARRVEL function
        function_result = asyncio.run(execute_marrvel_function(function_name, arguments))
        
        # Send result back to OpenAI
        messages.append(response_message)
        messages.append({
            "role": "function",
            "name": function_name,
            "content": json.dumps(function_result)
        })
        
        second_response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        return second_response.choices[0].message["content"]
    
    return response_message["content"]

# Example usage
if __name__ == "__main__":
    queries = [
        "What is the TP53 gene?",
        "Is variant 17-7577121-C-T pathogenic?",
        "What diseases are associated with BRCA1?"
    ]
    
    for query in queries:
        print(f"\n{'='*70}")
        print(f"Q: {query}")
        print('='*70)
        answer = chat_with_marrvel(query)
        print(f"A: {answer}")
```

## Setup Instructions

1. **Install OpenAI SDK:**
```bash
pip install openai
```

2. **Set your API key:**
```bash
export OPENAI_API_KEY="your-key-here"
```

3. **Run the integration:**
```bash
python3 openai_marrvel_integration.py
```

## Comparison: OpenAI vs Claude Desktop

| Feature | OpenAI (Function Calling) | Claude Desktop (MCP) |
|---------|---------------------------|----------------------|
| Setup | Manual function definitions | Automatic tool discovery |
| Protocol | REST/HTTP | MCP (stdio) |
| Integration | Code required | Config file only |
| Flexibility | High (custom logic) | Medium (standardized) |
| Best for | Custom applications | Desktop usage |

## Next Steps

1. **For quick testing**: Use `test_api_direct.py`
2. **For OpenAI integration**: Adapt the example above
3. **For production**: Create a REST API wrapper with FastAPI
4. **For Claude Desktop**: Follow the main README.md instructions

## Need Help?

- Test connectivity: `python3 test_api_direct.py`
- See all tools: Check `TOOL_REFERENCE.md`
- API details: See `API_DOCUMENTATION.md`
- Examples: See `examples/example_queries.py`

---

**Note**: The MCP server (`server.py`) is designed for Claude Desktop, but all the underlying functions work with any LLM. The key is mapping the LLM's function/tool calling format to MARRVEL API endpoints.
