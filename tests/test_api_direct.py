"""
Simple Direct Tool Test for MARRVEL-MCP

Tests the core functions directly without running the MCP server.
Perfect for validating the API integration works.
"""

import asyncio
import sys
sys.path.insert(0, '/Users/hyun-hwanjeong/Workspaces/MARRVEL_MCP')

# Import the fetch function and BASE_URL directly
from server import fetch_marrvel_data, BASE_URL


async def test_basic_queries():
    """Test a few basic MARRVEL API queries."""
    print("\n" + "="*70)
    print("MARRVEL API DIRECT TEST")
    print("="*70)
    print(f"Base URL: {BASE_URL}\n")
    
    tests = [
        ("Gene by Entrez ID (TP53)", "/gene/entrezId/7157"),
        ("Gene by Symbol (BRCA1)", "/gene/taxonId/9606/symbol/BRCA1"),
        ("OMIM for TP53", "/omim/gene/symbol/TP53"),
    ]
    
    for test_name, endpoint in tests:
        print(f"\n{'─'*70}")
        print(f"Test: {test_name}")
        print(f"Endpoint: {endpoint}")
        print('─'*70)
        
        try:
            result = await fetch_marrvel_data(endpoint)
            
            # Pretty print key information
            if isinstance(result, dict):
                # Show first few keys
                keys = list(result.keys())[:5]
                print(f"✓ Response type: dict with {len(result)} keys")
                print(f"  First keys: {keys}")
                
                # Show some data
                if 'symbol' in result:
                    print(f"  Gene symbol: {result.get('symbol')}")
                if 'name' in result:
                    print(f"  Gene name: {result.get('name')}")
                if 'entrezId' in result:
                    print(f"  Entrez ID: {result.get('entrezId')}")
            elif isinstance(result, list):
                print(f"✓ Response type: list with {len(result)} items")
                if result:
                    print(f"  First item keys: {list(result[0].keys())[:5]}")
            else:
                print(f"✓ Response: {str(result)[:200]}")
                
            print("✓ SUCCESS")
            
        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)


if __name__ == "__main__":
    print("\nTesting MARRVEL API integration...")
    print("(This tests the core API calls without MCP protocol)")
    asyncio.run(test_basic_queries())
