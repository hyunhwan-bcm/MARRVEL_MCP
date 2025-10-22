"""
Integration tests that make real API calls for server utilities.

Run with: pytest -m integration_api tests/integration/api/test_server_api_integration.py
"""

import pytest
import sys
from pathlib import Path

# Ensure repository root is on sys.path for importing src.*
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.api_client import fetch_marrvel_data


class TestIntegration:
    """
    Integration tests that make real API calls.
    Skip these in CI/CD by using pytest markers.
    """

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_gene_query(self):
        """Test real API call for TP53."""
        result = await fetch_marrvel_data("/gene/entrezId/7157")
        assert result is not None

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_variant_query(self):
        """Test real API call for a variant (placeholder)."""
        # Add a concrete variant query or keep as placeholder for now
        assert True
