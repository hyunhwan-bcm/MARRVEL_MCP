#!/usr/bin/env python3
"""
Simplified OpenAI + MARRVEL Integration - Each query is independent
Usage: python3 openai_marrvel_simple.py
Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'
"""

import os
import json
import asyncio
from openai import OpenAI
from server import (
    get_gene_by_symbol,
    get_clinvar_by_gene_symbol,
    get_omim_by_gene_symbol,
    get_diopt_orthologs
)

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Define MARRVEL functions for OpenAI
MARRVEL_FUNCTIONS = [
    {
        "name": "get_gene_by_symbol",
        "description": "Get comprehensive gene information by gene symbol (e.g., TP53, BRCA1)",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Official gene symbol"},
                "taxon_id": {"type": "integer", "description": "Species taxonomy ID (default: 9606 for human)", "default": 9606}
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
                "gene_symbol": {"type": "string", "description": "Gene symbol"},
                "taxon_id": {"type": "integer", "description": "Species taxonomy ID (default: 9606)", "default": 9606}
            },
            "required": ["gene_symbol"]
        }
    },
    {
        "name": "get_omim_by_gene_symbol",
        "description": "Get OMIM disease associations for a gene",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol"},
                "taxon_id": {"type": "integer", "description": "Species taxonomy ID (default: 9606)", "default": 9606}
            },
            "required": ["gene_symbol"]
        }
    },
    {
        "name": "get_diopt_orthologs",
        "description": "Get orthologous genes across species",
        "parameters": {
            "type": "object",
            "properties": {
                "gene_symbol": {"type": "string", "description": "Gene symbol"},
                "taxon_id": {"type": "integer", "description": "Source species taxonomy ID", "default": 9606}
            },
            "required": ["gene_symbol"]
        }
    }
]

FUNCTION_MAP = {
    "get_gene_by_symbol": get_gene_by_symbol,
    "get_clinvar_by_gene_symbol": get_clinvar_by_gene_symbol,
    "get_omim_by_gene_symbol": get_omim_by_gene_symbol,
    "get_diopt_orthologs": get_diopt_orthologs
}


async def call_marrvel_function(function_name: str, arguments: dict):
    """Execute a MARRVEL function with smart truncation"""
    func = FUNCTION_MAP.get(function_name)
    if not func:
        return {"error": f"Unknown function: {function_name}"}
    
    try:
        result = await func(**arguments)
        
        # For ClinVar, always return just statistics for large datasets
        if function_name == "get_clinvar_by_gene_symbol" and isinstance(result, list):
            if len(result) > 50:
                pathogenic = sum(1 for v in result if isinstance(v, dict) and 
                               'pathogenic' in v.get('clinicalSignificance', '').lower())
                benign = sum(1 for v in result if isinstance(v, dict) and 
                           'benign' in v.get('clinicalSignificance', '').lower())
                
                return {
                    "summary": f"Found {len(result)} ClinVar variants for {arguments.get('gene_symbol')}",
                    "total_variants": len(result),
                    "pathogenic_or_likely": pathogenic,
                    "benign_or_likely": benign,
                    "recommendation": "Use specific variant queries for individual variant details"
                }
        
        # For other large datasets, truncate
        result_str = json.dumps(result)
        if len(result_str) > 10000 and isinstance(result, list):
            return {
                "total_count": len(result),
                "sample_data": result[:3],
                "note": "Showing first 3 items only"
            }
        
        return result
    except Exception as e:
        return {"error": str(e)}


async def single_query(user_message: str):
    """
    Process a single independent query with OpenAI + MARRVEL
    Each query starts fresh to avoid token limits from conversation history
    """
    print(f"\n🧬 Query: {user_message}")
    print("🤖 Processing...")
    
    messages = [
        {
            "role": "system",
            "content": "You are a genetics research assistant with access to the MARRVEL database. "
                      "Provide clear, scientific answers. Keep responses concise."
        },
        {"role": "user", "content": user_message}
    ]
    
    # First API call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        functions=MARRVEL_FUNCTIONS,
        function_call="auto"
    )
    
    response_message = response.choices[0].message
    
    # Check if function call needed
    if response_message.function_call:
        function_name = response_message.function_call.name
        function_args = json.loads(response_message.function_call.arguments)
        
        print(f"📡 Calling: {function_name}({json.dumps(function_args)})")
        
        # Execute MARRVEL function
        function_result = await call_marrvel_function(function_name, function_args)
        
        # Send result back for interpretation
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
        
        # Get final answer
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages
        )
        
        answer = final_response.choices[0].message.content
    else:
        answer = response_message.content
    
    print(f"\n✅ Answer:\n{answer}\n")
    print("-" * 70)
    return answer


async def main():
    """Run example queries - each is independent"""
    
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ Error: Please set OPENAI_API_KEY environment variable")
        return
    
    print("=" * 70)
    print("🧬 MARRVEL + OpenAI Integration (gpt-4o-mini)")
    print("=" * 70)
    
    queries = [
        "What is the TP53 gene?",
        "Tell me about BRCA1 disease associations",
        "Find orthologs of TP53 across different species"
        # Note: ClinVar queries return very large datasets that may exceed token limits
        # For ClinVar, use the MCP server directly or query specific variants
    ]
    
    for query in queries:
        await single_query(query)


if __name__ == "__main__":
    asyncio.run(main())
