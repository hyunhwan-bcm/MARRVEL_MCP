"""
Unit tests for API client module.

Tests the core HTTP communication functionality with the MARRVEL API.
"""

import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.api_client import fetch_marrvel_data
from config import API_BASE_URL


class TestFetchMarrvelData:
    """Test the fetch_marrvel_data API client function."""
    
    @pytest.mark.asyncio
    async def test_successful_fetch(self):
        """Test successful API request with valid response."""
        with patch('src.utils.api_client.httpx.AsyncClient') as mock_client:
            # Setup mock response
            mock_response = AsyncMock()
            mock_response.json.return_value = {"gene": "TP53", "entrezId": "7157"}
            mock_response.raise_for_status = AsyncMock()
            
            # Configure mock client
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Execute test
            result = await fetch_marrvel_data("/gene/entrezId/7157")
            
            # Verify results
            assert result["gene"] == "TP53"
            assert result["entrezId"] == "7157"
    
    @pytest.mark.asyncio
    async def test_fetch_with_http_error(self):
        """Test error handling when API returns HTTP error status."""
        with patch('src.utils.api_client.httpx.AsyncClient') as mock_client:
            # Setup mock response with error
            mock_response = AsyncMock()
            mock_response.raise_for_status.side_effect = Exception("404 Not Found")
            
            # Configure mock client
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Execute test and verify exception
            with pytest.raises(Exception) as exc_info:
                await fetch_marrvel_data("/invalid/endpoint")
            
            assert "404" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_builds_correct_url(self):
        """Test that the function builds the correct URL from base URL and endpoint."""
        with patch('src.utils.api_client.httpx.AsyncClient') as mock_client:
            # Setup mock
            mock_response = AsyncMock()
            mock_response.json.return_value = {}
            mock_response.raise_for_status = AsyncMock()
            
            mock_get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__.return_value.get = mock_get
            
            # Execute test
            await fetch_marrvel_data("/test/endpoint")
            
            # Verify correct URL was called
            expected_url = f"{API_BASE_URL}/test/endpoint"
            mock_get.assert_called_once_with(expected_url)
    
    @pytest.mark.asyncio
    async def test_fetch_with_complex_data(self):
        """Test fetching complex nested data structures."""
        with patch('src.utils.api_client.httpx.AsyncClient') as mock_client:
            # Setup mock with complex response
            complex_data = {
                "gene": {
                    "symbol": "TP53",
                    "entrezId": "7157",
                    "transcripts": [
                        {"id": "NM_000546", "version": 5},
                        {"id": "NM_001276696", "version": 2}
                    ]
                },
                "variants": []
            }
            
            mock_response = AsyncMock()
            mock_response.json.return_value = complex_data
            mock_response.raise_for_status = AsyncMock()
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Execute test
            result = await fetch_marrvel_data("/gene/entrezId/7157")
            
            # Verify complex structure preserved
            assert result["gene"]["symbol"] == "TP53"
            assert len(result["gene"]["transcripts"]) == 2
            assert result["gene"]["transcripts"][0]["id"] == "NM_000546"


# Integration tests (require actual API access)
class TestFetchMarrvelDataIntegration:
    """Integration tests that make real API calls (marked for optional execution)."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_call_tp53(self):
        """Test real API call for TP53 gene (requires network access)."""
        result = await fetch_marrvel_data("/gene/entrezId/7157")
        assert "symbol" in result or "entrezId" in result
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_api_call_invalid_endpoint(self):
        """Test real API call with invalid endpoint (requires network access)."""
        with pytest.raises(Exception):
            await fetch_marrvel_data("/invalid/nonexistent/endpoint")
