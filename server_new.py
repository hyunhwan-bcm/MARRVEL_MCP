"""
MARRVEL-MCP Server Entry Point

This is a backward-compatible entry point that uses the refactored package.
For new code, consider importing from marrvel_mcp package directly.
"""

from marrvel_mcp.server import run_server

if __name__ == "__main__":
    run_server()
