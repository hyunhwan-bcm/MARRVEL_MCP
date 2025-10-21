#!/usr/bin/env python3
"""
OpenAI + MARRVEL Integration Example
Usage: python3 openai_marrvel_example.py
Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'
"""

import os
import json
import asyncio
from openai import OpenAI
from server import (
    get_gene_by_symbol,
    get_gene_by_entrez_id,
    get_clinvar_by_gene_symbol,
    get_omim_by_gene_symbol,
    get_gnomad_by_gene_symbol,
    get_diopt_orthologs,
    get_gtex_expression
)

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Define MARRVEL functions for OpenAI
MARRVEL_FUNCTIONS = [
    {
        "name": "get_gene_by_symbol",
        "description": "Get comprehensive gene information by gene symbol (e.g., TP53, BRCA1)",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {
                    "type": "string",
                    "description": "Official gene symbol (e.g., TP53, BRCA1)"
                },
                "taxon_id": {
                    "type": "integer",
                    "description": "Species taxonomy ID (9606 for human, 10090 for mouse)",
                    "default": 9606
                }
            },
            "required": ["gene_symbol"]
        }
    },
    {
        "name": "get_clinvar_by_gene_symbol",
        "description": "Get ClinVar variants for a gene - clinical significance and pathogenicity",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {
                    "type": "string",
                    "description": "Gene symbol (e.g., BRCA1, TP53)"
                },
                "taxon_id": {
                    "type": "integer",
                    "description": "Species taxonomy ID (default: 9606 for human)",
                    "default": 9606
                }
            },
            "required": ["gene_symbol"]
        }
    },
    {
        "name": "get_omim_by_gene_symbol",
        "description": "Get OMIM (Online Mendelian Inheritance in Man) disease associations for a gene",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {
                    "type": "string",
                    "description": "Gene symbol (e.g., BRCA1, TP53)"
                },
                "taxon_id": {
                    "type": "integer",
                    "description": "Species taxonomy ID (default: 9606 for human)",
                    "default": 9606
                }
            },
            "required": ["gene_symbol"]
        }
    },
    {
        "name": "get_diopt_orthologs",
        "description": "Get orthologous genes across species (human, mouse, fly, zebrafish, etc.)",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {
                    "type": "string",
                    "description": "Gene symbol to find orthologs for"
                },
                "taxon_id": {
                    "type": "integer",
                    "description": "Source species taxonomy ID",
                    "default": 9606
                }
            },
            "required": ["gene_symbol"]
        }
    }
]

# Map function names to actual functions
FUNCTION_MAP = {
    "get_gene_by_symbol": get_gene_by_symbol,
    "get_gene_by_entrez_id": get_gene_by_entrez_id,
    "get_clinvar_by_gene_symbol": get_clinvar_by_gene_symbol,
    "get_omim_by_gene_symbol": get_omim_by_gene_symbol,
    "get_gnomad_by_gene_symbol": get_gnomad_by_gene_symbol,
    "get_diopt_orthologs": get_diopt_orthologs,
    "get_gtex_expression": get_gtex_expression
}


async def call_marrvel_function(function_name: str, arguments: dict):
    """Execute a MARRVEL function and return the result"""
    func = FUNCTION_MAP.get(function_name)
    if not func:
        return {"error": f"Unknown function: {function_name}"}
    
    try:
        result = await func(**arguments)
        
        # For ClinVar queries specifically, return minimal summary for large datasets
        if function_name == "get_clinvar_by_gene_symbol" and isinstance(result, list):
            if len(result) > 100:  # Large ClinVar datasets
                # Just return statistics
                pathogenic_count = sum(1 for v in result if isinstance(v, dict) and 
                                     v.get('clinicalSignificance', '').lower().startswith('pathogenic'))
                benign_count = sum(1 for v in result if isinstance(v, dict) and 
                                 v.get('clinicalSignificance', '').lower().startswith('benign'))
                
                return {
                    "summary": f"Found {len(result)} ClinVar variants for {arguments.get('gene_symbol', 'gene')}",
                    "total_variants": len(result),
                    "pathogenic_likely": pathogenic_count,
                    "benign_likely": benign_count,
                    "note": "Large dataset - use specific variant queries for details (e.g., by position or variant ID)"
                }
        
        # General truncation for other large results
        result_str = json.dumps(result)
        MAX_RESULT_SIZE = 5000  # ~5KB limit
        
        if len(result_str) > MAX_RESULT_SIZE:
            if isinstance(result, list):
                return {
                    "note": "⚠️ Large dataset truncated",
                    "total_count": len(result),
                    "message": "Use more specific queries for detailed results"
                }
            elif isinstance(result, dict):
                summary = {}
                for key, value in result.items():
                    if isinstance(value, (str, int, float, bool)) or value is None:
                        summary[key] = value
                    elif isinstance(value, list):
                        summary[f"{key}_count"] = len(value)
                return {"note": "⚠️ Large result truncated", **summary}
        
        return result
    except Exception as e:
        return {"error": str(e)}


async def chat_with_marrvel(user_message: str):
    """
    Send a message to OpenAI with MARRVEL functions available.
    OpenAI will decide when to call MARRVEL functions.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a genetics research assistant with access to the MARRVEL database. "
                      "You can look up gene information, variants, diseases, orthologs, and expression data. "
                      "Always provide clear, scientific answers."
        },
        {"role": "user", "content": user_message}
    ]
    
    print(f"\n🧬 User: {user_message}")
    print("🤖 Thinking...")
    
    # First API call to OpenAI
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=MARRVEL_FUNCTIONS,
        function_call="auto"
    )
    
    response_message = response.choices[0].message
    
    # Check if OpenAI wants to call a function
    if response_message.function_call:
        function_name = response_message.function_call.name
        function_args = json.loads(response_message.function_call.arguments)
        
        print(f"📡 Calling MARRVEL function: {function_name}")
        print(f"   Arguments: {function_args}")
        
        # Execute the MARRVEL function
        function_result = await call_marrvel_function(function_name, function_args)
        
        # Add the function result to messages
        messages.append({
            "role": "assistant",
            "content": None,
            "function_call": {
                "name": function_name,
                "arguments": response_message.function_call.arguments
            }
        })
        messages.append({
            "role": "function",
            "name": function_name,
            "content": json.dumps(function_result)
        })
        
        # Second API call to get natural language response
        second_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        final_answer = second_response.choices[0].message.content
        print(f"\n✅ Assistant: {final_answer}\n")
        return final_answer
    else:
        # No function call needed
        answer = response_message.content
        print(f"\n✅ Assistant: {answer}\n")
        return answer


async def main():
    """Run example queries"""
    
    # Check for API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: Please set OPENAI_API_KEY environment variable")
        print("   Example: export OPENAI_API_KEY='sk-...'")
        return
    
    print("=" * 70)
    print("🧬 MARRVEL + OpenAI Integration Example")
    print("=" * 70)
    
    # Example queries
    queries = [
        "What is the TP53 gene?",
        "Tell me about disease associations for BRCA1",
        "Find orthologs of TP53 in other species",
        "What are the ClinVar variants for CFTR?"
    ]
    
    for query in queries:
        await chat_with_marrvel(query)
        print("-" * 70)


if __name__ == "__main__":
    asyncio.run(main())
