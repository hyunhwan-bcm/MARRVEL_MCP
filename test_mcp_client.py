"""
Quick MCP Client Test for MARRVEL-MCP Server

This script directly calls the MCP tools to test the server without needing
Claude Desktop. Useful for testing with OpenAI or other LLM integrations.
"""

import asyncio
from server import (
    get_gene_by_entrez_id,
    get_gene_by_symbol,
    get_variant_dbnsfp,
    get_clinvar_by_variant,
    get_gnomad_variant,
    get_omim_by_gene_symbol,
    get_diopt_orthologs,
    get_gtex_expression
)


async def test_gene_tools():
    """Test gene information tools."""
    print("\n" + "="*70)
    print("TESTING GENE TOOLS")
    print("="*70)
    
    # Test 1: Get gene by Entrez ID
    print("\n1. Getting TP53 by Entrez ID (7157)...")
    result = await get_gene_by_entrez_id("7157")
    print(f"✓ Result: {result[:200]}...")  # First 200 chars
    
    # Test 2: Get gene by symbol
    print("\n2. Getting human BRCA1 by symbol...")
    result = await get_gene_by_symbol("BRCA1", "9606")
    print(f"✓ Result: {result[:200]}...")


async def test_variant_tools():
    """Test variant analysis tools."""
    print("\n" + "="*70)
    print("TESTING VARIANT TOOLS")
    print("="*70)
    
    # Test 3: Get dbNSFP annotations
    print("\n3. Getting dbNSFP data for variant 17-7577121-C-T...")
    result = await get_variant_dbnsfp("17-7577121-C-T")
    print(f"✓ Result: {result[:200]}...")
    
    # Test 4: Get ClinVar data
    print("\n4. Getting ClinVar data for same variant...")
    result = await get_clinvar_by_variant("17-7577121-C-T")
    print(f"✓ Result: {result[:200]}...")
    
    # Test 5: Get gnomAD frequency
    print("\n5. Getting gnomAD frequency for same variant...")
    result = await get_gnomad_variant("17-7577121-C-T")
    print(f"✓ Result: {result[:200]}...")


async def test_disease_tools():
    """Test disease/OMIM tools."""
    print("\n" + "="*70)
    print("TESTING DISEASE TOOLS (OMIM)")
    print("="*70)
    
    # Test 6: Get OMIM diseases for TP53
    print("\n6. Getting OMIM diseases associated with TP53...")
    result = await get_omim_by_gene_symbol("TP53")
    print(f"✓ Result: {result[:200]}...")


async def test_ortholog_tools():
    """Test ortholog and expression tools."""
    print("\n" + "="*70)
    print("TESTING ORTHOLOG & EXPRESSION TOOLS")
    print("="*70)
    
    # Test 7: Get orthologs
    print("\n7. Getting DIOPT orthologs for TP53 (7157)...")
    result = await get_diopt_orthologs("7157")
    print(f"✓ Result: {result[:200]}...")
    
    # Test 8: Get GTEx expression
    print("\n8. Getting GTEx expression for TP53...")
    result = await get_gtex_expression("7157")
    print(f"✓ Result: {result[:200]}...")


async def run_all_tests():
    """Run all test suites."""
    print("\n" + "="*70)
    print("MARRVEL-MCP SERVER TEST SUITE")
    print("Testing direct tool calls without MCP protocol")
    print("="*70)
    
    try:
        await test_gene_tools()
        await test_variant_tools()
        await test_disease_tools()
        await test_ortholog_tools()
        
        print("\n" + "="*70)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY!")
        print("="*70)
        print("\nThe MCP server tools are working correctly.")
        print("You can now integrate these with OpenAI or other LLM APIs.")
        
    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def interactive_test():
    """Interactive test - prompt user for tool to test."""
    print("\n" + "="*70)
    print("INTERACTIVE MCP TOOL TESTER")
    print("="*70)
    
    tools = {
        "1": ("get_gene_by_entrez_id", "Gene by Entrez ID (e.g., 7157 for TP53)"),
        "2": ("get_gene_by_symbol", "Gene by symbol (e.g., TP53, 9606)"),
        "3": ("get_variant_dbnsfp", "Variant dbNSFP (e.g., 17-7577121-C-T)"),
        "4": ("get_clinvar_by_variant", "ClinVar variant (e.g., 17-7577121-C-T)"),
        "5": ("get_gnomad_variant", "gnomAD variant (e.g., 17-7577121-C-T)"),
        "6": ("get_omim_by_gene_symbol", "OMIM by gene (e.g., TP53)"),
        "7": ("get_diopt_orthologs", "DIOPT orthologs (e.g., 7157)"),
        "8": ("get_gtex_expression", "GTEx expression (e.g., 7157)"),
    }
    
    print("\nAvailable tools:")
    for key, (tool_name, desc) in tools.items():
        print(f"  {key}. {desc}")
    
    choice = input("\nEnter tool number (or 'all' for all tests): ").strip()
    
    if choice.lower() == 'all':
        await run_all_tests()
    elif choice in tools:
        tool_name, desc = tools[choice]
        param = input(f"Enter parameter for {desc}: ").strip()
        
        tool_func = globals()[tool_name]
        print(f"\nCalling {tool_name}({param})...")
        
        if tool_name == "get_gene_by_symbol":
            # Special case: needs two params
            taxon = input("Enter taxon ID (default 9606 for human): ").strip() or "9606"
            result = await tool_func(param, taxon)
        else:
            result = await tool_func(param)
        
        print(f"\nResult:\n{result}")
    else:
        print("Invalid choice.")


if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("MARRVEL-MCP Tool Tester")
    print("Direct testing of MCP server tools (no MCP protocol needed)")
    print("="*70)
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        asyncio.run(interactive_test())
    else:
        print("\nRunning automated test suite...")
        print("(Use 'python test_mcp_client.py interactive' for interactive mode)")
        asyncio.run(run_all_tests())
