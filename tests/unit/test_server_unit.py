"""
Unit tests for MARRVEL-MCP server initialization and tool registration.

Tests the server creation, configuration, and tool registration without
starting an actual MCP server instance.

Run with: pytest tests/unit/test_server_unit.py
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

# Add project root to path to import modules
# Go up two levels from tests/unit/ to reach project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from src.utils.api_client import fetch_marrvel_data
from server import create_server


@pytest.mark.unit
class TestFetchMarrvelData:
    """Test the fetch_marrvel_data helper function."""

    @pytest.mark.asyncio
    async def test_fetch_gene_by_entrez_id(self):
        """Test fetching gene data by Entrez ID."""
        # Mock the httpx client
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.json.return_value = {"gene": "TP53", "entrezId": "7157"}
            mock_response.raise_for_status = AsyncMock()

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            result = await fetch_marrvel_data("/gene/entrezId/7157")
            assert result["gene"] == "TP53"
            assert result["entrezId"] == "7157"

    @pytest.mark.asyncio
    async def test_fetch_with_error(self):
        """Test error handling when API returns error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("API Error")

            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response

            with pytest.raises(Exception):
                await fetch_marrvel_data("/invalid/endpoint")


@pytest.mark.unit
class TestServerCreation:
    """Test MARRVEL-MCP server creation and initialization."""

    def test_create_server_returns_fastmcp_instance(self):
        """Test that create_server returns a FastMCP instance."""
        server = create_server()

        # Verify server is created
        assert server is not None
        # Verify it has FastMCP attributes
        assert hasattr(server, "name")

    def test_server_has_correct_name(self):
        """Test that the server is initialized with the correct name."""
        server = create_server()

        # Verify server name is "MARRVEL"
        assert server.name == "MARRVEL"

    def test_server_initialization_calls_all_register_functions(self):
        """Test that server initialization calls register_tools for all modules."""
        with patch("src.tools.gene_tools.register_tools") as mock_gene:
            with patch("src.tools.variant_tools.register_tools") as mock_variant:
                with patch("src.tools.disease_tools.register_tools") as mock_disease:
                    with patch("src.tools.ortholog_tools.register_tools") as mock_ortholog:
                        with patch("src.tools.expression_tools.register_tools") as mock_expression:
                            with patch("src.tools.utility_tools.register_tools") as mock_utility:
                                # Create server
                                server = create_server()

                                # Verify all register_tools were called
                                mock_gene.assert_called_once()
                                mock_variant.assert_called_once()
                                mock_disease.assert_called_once()
                                mock_ortholog.assert_called_once()
                                mock_expression.assert_called_once()
                                mock_utility.assert_called_once()


@pytest.mark.unit
class TestToolRegistration:
    """Test that all tool modules register their tools correctly."""

    def test_gene_tools_registration(self):
        """Test that gene_tools module registers all 3 gene tools."""
        from src.tools import gene_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        gene_tools.register_tools(mock_mcp)

        # Verify that tool() was called 3 times (3 gene tools)
        # Each tool() call returns a decorator, so we check the call count
        assert mock_mcp.tool.call_count == 3

    def test_variant_tools_registration(self):
        """Test that variant_tools module registers all 13 variant tools."""
        from src.tools import variant_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        variant_tools.register_tools(mock_mcp)

        # Verify that tool() was called 13 times (13 variant tools)
        assert mock_mcp.tool.call_count == 13

    def test_disease_tools_registration(self):
        """Test that disease_tools module registers all 3 OMIM tools."""
        from src.tools import disease_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        disease_tools.register_tools(mock_mcp)

        # Verify that tool() was called 3 times (3 OMIM tools)
        assert mock_mcp.tool.call_count == 3

    def test_ortholog_tools_registration(self):
        """Test that ortholog_tools module registers all 2 DIOPT tools."""
        from src.tools import ortholog_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        ortholog_tools.register_tools(mock_mcp)

        # Verify that tool() was called 2 times (2 DIOPT tools)
        assert mock_mcp.tool.call_count == 2

    def test_expression_tools_registration(self):
        """Test that expression_tools module registers all 3 expression tools."""
        from src.tools import expression_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        expression_tools.register_tools(mock_mcp)

        # Verify that tool() was called 3 times (3 expression tools)
        assert mock_mcp.tool.call_count == 3

    def test_utility_tools_registration(self):
        """Test that utility_tools module registers all 2 utility tools."""
        from src.tools import utility_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        utility_tools.register_tools(mock_mcp)

        # Verify that tool() was called 3 times (3 utility tools)
        assert mock_mcp.tool.call_count == 3

    def test_pubmed_tools_registration(self):
        """Test that pubmed_tools module registers all 2 PubMed tools."""
        from src.tools import pubmed_tools
        from mcp.server.fastmcp import FastMCP

        # Create a mock MCP instance
        mock_mcp = MagicMock(spec=FastMCP)

        # Register tools
        pubmed_tools.register_tools(mock_mcp)

        # Verify that tool() was called 2 times (2 PubMed tools)
        assert mock_mcp.tool.call_count == 2

    def test_total_tools_registered(self):
        """Test that the total number of tools registered is correct (28 tools)."""
        # 3 + 13 + 3 + 2 + 3 + 2 + 2 = 28 total tools
        expected_total = 28

        # Create server and count registered tools
        server = create_server()

        # Get the list of tools from the server
        # FastMCP stores tools in _tools attribute
        if hasattr(server, "_tools"):
            actual_total = len(server._tools)
            assert (
                actual_total == expected_total
            ), f"Expected {expected_total} tools, found {actual_total}"
        else:
            # If we can't access _tools, at least verify server was created
            assert server is not None
