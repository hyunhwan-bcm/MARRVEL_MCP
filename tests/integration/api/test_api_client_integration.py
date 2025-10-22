"""
Integration tests for API client module (real API calls).
"""

import pytest
import sys
from pathlib import Path

# Ensure repository root is on sys.path for importing src.*
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.utils.api_client import fetch_marrvel_data


class TestFetchMarrvelDataIntegration:
    """Integration tests that make real API calls (marked for optional execution)."""

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_tp53(self):
        """Test real API call for TP53 gene (requires network access)."""
        result = await fetch_marrvel_data("/gene/entrezId/7157")
        assert "symbol" in result or "entrezId" in result

    @pytest.mark.integration
    @pytest.mark.integration_api
    @pytest.mark.asyncio
    async def test_real_api_call_invalid_endpoint(self):
        """Test real API call with invalid endpoint (requires network access)."""
        with pytest.raises(Exception):
            await fetch_marrvel_data("/invalid/nonexistent/endpoint")
