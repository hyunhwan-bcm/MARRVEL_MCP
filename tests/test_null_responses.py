"""
Test cases for handling null/empty responses from the MARRVEL API.

This test file ensures that the server handles cases where the API returns
null values gracefully, without raising 'NoneType' object is not iterable errors.
"""

import json
import pytest
from unittest.mock import AsyncMock, patch
import sys
from pathlib import Path

# Add the repository root to the path
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


@pytest.mark.asyncio
async def test_fix_missing_hg38_vals_with_null_response():
    """
    Test that fix_missing_hg38_vals handles null responses without raising errors.

    This addresses the issue where querying for a non-existent Ensembl ID
    (e.g., ENSP00000297591) returns null and causes 'NoneType' object is not iterable.
    """
    from server import fix_missing_hg38_vals

    # Test with null response (no data found)
    null_response = json.dumps({"data": {"geneByEnsemblId": None}})
    result = await fix_missing_hg38_vals(null_response)
    result_obj = json.loads(result)

    # Should return the original null response without error
    assert result_obj["data"]["geneByEnsemblId"] is None


@pytest.mark.asyncio
async def test_get_gene_by_ensembl_id_with_null_response():
    """
    Test that get_gene_by_ensembl_id handles null API responses gracefully.

    Simulates the case where an Ensembl protein ID (ENSP) is used instead of
    a gene ID (ENSG), which returns null from the API.
    """
    from server import fetch_marrvel_data, fix_missing_hg38_vals

    # Mock the fetch_marrvel_data to return a null response
    null_response = json.dumps({"data": {"geneByEnsemblId": None}})

    with patch("server.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = null_response

        # Import after patching
        from server import get_gene_by_ensembl_id

        # This should not raise an error
        result = await get_gene_by_ensembl_id("ENSP00000297591")
        result_obj = json.loads(result)

        # Should return the null response
        assert result_obj["data"]["geneByEnsemblId"] is None


@pytest.mark.asyncio
async def test_fix_missing_hg38_vals_with_valid_response():
    """
    Test that fix_missing_hg38_vals still works correctly with valid responses.

    Ensures the fix doesn't break the normal operation of the function.
    """
    from server import fix_missing_hg38_vals

    # Test with a valid response (but without the fields that trigger liftover)
    valid_response = json.dumps(
        {
            "data": {
                "geneByEnsemblId": {
                    "symbol": "TP53",
                    "taxonId": 10090,  # Mouse, so it won't try to liftover
                    "chr": "11",
                }
            }
        }
    )

    result = await fix_missing_hg38_vals(valid_response)
    result_obj = json.loads(result)

    # Should return a valid response
    assert result_obj["data"]["geneByEnsemblId"]["symbol"] == "TP53"


@pytest.mark.asyncio
async def test_fix_missing_hg38_vals_with_list_response():
    """
    Test that fix_missing_hg38_vals handles list responses correctly.

    Some API queries return lists instead of single objects.
    """
    from server import fix_missing_hg38_vals

    # Test with a list response
    list_response = json.dumps(
        {
            "data": {
                "genesByPosition": [
                    {
                        "symbol": "GENE1",
                        "taxonId": 10090,
                        "chr": "1",
                    }
                ]
            }
        }
    )

    result = await fix_missing_hg38_vals(list_response)
    result_obj = json.loads(result)

    # Should handle list correctly
    assert isinstance(result_obj["data"]["genesByPosition"], list)
    assert result_obj["data"]["genesByPosition"][0]["symbol"] == "GENE1"


@pytest.mark.asyncio
async def test_fix_missing_hg38_vals_with_empty_list():
    """
    Test that fix_missing_hg38_vals handles empty list responses.
    """
    from server import fix_missing_hg38_vals

    # Test with an empty list response
    empty_list_response = json.dumps({"data": {"genesByPosition": []}})

    result = await fix_missing_hg38_vals(empty_list_response)
    result_obj = json.loads(result)

    # Should handle empty list correctly
    assert result_obj["data"]["genesByPosition"] == []
