"""
Quick Start Guide for MARRVEL-MCP

This guide helps you get started with using the MARRVEL-MCP server.
"""

# Step 1: Installation
print("""
STEP 1: INSTALLATION
====================

# Clone the repository
cd ~/Workspaces/MARRVEL_MCP

# Install dependencies
pip install -r requirements.txt

# Or install individually
pip install "fastmcp[mcp]>=0.3.0"
pip install "httpx>=0.27.0"
""")

# Step 2: Configuration
print("""
STEP 2: CONFIGURE CLAUDE DESKTOP
=================================

Edit your Claude Desktop configuration file:

macOS: ~/Library/Application Support/Claude/claude_desktop_config.json
Windows: %APPDATA%/Claude/claude_desktop_config.json

Add this to your config:

{
  "mcpServers": {
    "marrvel": {
      "command": "python",
      "args": ["/Users/hyun-hwanjeong/Workspaces/MARRVEL_MCP/server.py"]
    }
  }
}

Save and restart Claude Desktop.
""")

# Step 3: Test the server
print("""
STEP 3: TEST THE SERVER
========================

You can test the server directly:

python server.py

Or test through Claude Desktop by asking:

"Use MARRVEL to get information about the TP53 gene"
"What's the Entrez ID 7157?"
"Find variants in BRCA1 gene"
""")

# Step 4: Common queries
print("""
STEP 4: EXAMPLE QUERIES
========================

Gene Information:
-----------------
"Get information about TP53"
"What gene is at chromosome 17 position 7577121?"
"Find the mouse ortholog of TP53"

Variant Analysis:
-----------------
"Analyze variant 17-7577121-C-T"
"Is this variant pathogenic: 17-7577121-C-T?"
"What's the population frequency of variant 17-7577121-C-T?"

Disease Information:
--------------------
"What diseases are associated with TP53?"
"Tell me about OMIM entry 151623"
"Get phenotype data for BRCA1 mutations"

Expression & Orthologs:
-----------------------
"Where is TP53 expressed in the body?"
"Show me orthologs of TP53 across species"
"Is TP53 a drug target?"
""")

# Step 5: API Reference
print("""
STEP 5: FULL API REFERENCE
===========================

See API_DOCUMENTATION.md for comprehensive documentation of all 30+ tools.

Tool Categories:
- Gene Tools (3 tools)
- Variant Analysis Tools (13 tools)
- Disease Tools - OMIM (3 tools)
- Ortholog Tools - DIOPT (2 tools)
- Expression Tools (3 tools)
- Utility Tools (2 tools)
""")

# Step 6: Troubleshooting
print("""
STEP 6: TROUBLESHOOTING
========================

Issue: Import errors
Solution: Make sure FastMCP is installed: pip install "fastmcp[mcp]>=0.3.0"

Issue: API timeout
Solution: Some queries may take longer. Increase timeout in server.py if needed.

Issue: Gene/variant not found
Solution: 
- Check gene symbol spelling
- Verify Entrez ID is correct
- Ensure variant format is: chromosome-position-ref-alt
- Use hg19 coordinates

Issue: Server not showing in Claude
Solution:
- Check config file path is correct
- Restart Claude Desktop after config changes
- Verify Python path is correct in config

For more help:
- Check README.md
- See example_queries.py for usage patterns
- Visit https://marrvel.org/doc for API details
""")
