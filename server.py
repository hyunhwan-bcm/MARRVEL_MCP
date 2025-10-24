"""
Backward-compatible entry point for running the MARRVEL MCP server.

The authoritative implementation now lives in ``src.server`` so that tests and
installed packages can import ``server`` without relying on the repository
layout.  This wrapper simply re-exports the public API and keeps the executable
behaviour unchanged.
"""

from src.server import create_server, mcp  # Re-export for local scripts.


if __name__ == "__main__":
    mcp.run()
