"""
Unit tests for STRING interaction ENSP to ENSG conversion.

Tests the handling of Ensembl protein IDs (ENSP) in STRING interactions,
ensuring they are properly converted to Ensembl gene IDs (ENSG).
"""

import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
from pathlib import Path

# Add repo root to path so we can import server
repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))


@pytest.fixture
def mock_ensembl_responses():
    """Mock responses for Ensembl REST API calls."""
    return {
        "ENSP00000297591": {
            "protein_response": {"Parent": "ENST00000297591", "id": "ENSP00000297591"},
            "transcript_response": {"Parent": "ENSG00000188152", "id": "ENST00000297591"},
        },
        "ENSP00000123456": {
            "protein_response": {"Parent": "ENST00000123456", "id": "ENSP00000123456"},
            "transcript_response": {"Parent": "ENSG00000111111", "id": "ENST00000123456"},
        },
    }


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_ensembl_protein_to_gene_id_with_ensg():
    """Test that ENSG IDs are returned directly without conversion."""
    import server

    result = await server.resolve_ensembl_protein_to_gene_id("ENSG00000188152")

    assert "ensembl_gene_id" in result
    assert result["ensembl_gene_id"] == "ENSG00000188152"
    assert "error" not in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_ensembl_protein_to_gene_id_with_ensp(mock_ensembl_responses):
    """Test that ENSP IDs are converted to ENSG via Ensembl API."""
    import server

    ensp_id = "ENSP00000297591"
    expected_gene_id = "ENSG00000188152"

    # Mock the conversion function to return expected data
    async def mock_conversion(protein_id):
        if protein_id == ensp_id:
            return json.dumps(
                {
                    "ensembl_protein_id": protein_id,
                    "ensembl_transcript_id": "ENST00000297591",
                    "ensembl_gene_ids": expected_gene_id,
                }
            )
        return json.dumps({"error": "Not found"})

    with patch.object(server, "get_ensembl_gene_id_from_ensembl_protein_id", new=mock_conversion):
        result = await server.resolve_ensembl_protein_to_gene_id(ensp_id)

    assert "ensembl_gene_id" in result
    assert result["ensembl_gene_id"] == expected_gene_id
    assert "error" not in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_ensembl_protein_to_gene_id_with_invalid_id():
    """Test handling of invalid Ensembl ID formats."""
    import server

    result = await server.resolve_ensembl_protein_to_gene_id("INVALID_ID")

    assert "error" in result
    assert "Unknown Ensembl ID format" in result["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_resolve_ensembl_protein_to_gene_id_with_ensp_error(mock_ensembl_responses):
    """Test error handling when ENSP conversion fails."""
    import server

    ensp_id = "ENSP00000999999"

    # Mock the conversion function to return an error
    async def mock_conversion_error(protein_id):
        return json.dumps({"error": "Protein not found in Ensembl"})

    with patch.object(
        server, "get_ensembl_gene_id_from_ensembl_protein_id", new=mock_conversion_error
    ):
        result = await server.resolve_ensembl_protein_to_gene_id(ensp_id)

    assert "error" in result
    assert "Failed to convert ENSP to ENSG" in result["error"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_string_interactions_adds_gene_id_field():
    """Test that STRING interactions include connectedEnsemblGeneId field."""
    import server

    # Mock responses for the nested calls
    mock_string_response = json.dumps(
        {
            "data": {
                "stringInteractionsByEntrezId": [
                    {
                        "ensemblId1": "ENSP00000297591",
                        "ensemblId2": "ENSP00000123456",
                        "database": "STRING",
                        "combExpDb": 0.9,
                        "experiments": 5,
                    }
                ]
            }
        }
    )

    mock_gene_response = json.dumps(
        {"data": {"geneByEntrezId": {"xref": {"ensemblId": "ENSG00000100000"}}}}
    )

    mock_protein_ids_response = json.dumps(
        {
            "ensembl_protein_ids": ["ENSP00000999999"],
            "ensembl_canonical_protein_id": "ENSP00000999999",
        }
    )

    # Mock the conversion to return gene ID
    async def mock_resolve(protein_id):
        if protein_id == "ENSP00000297591":
            return {"ensembl_gene_id": "ENSG00000188152"}
        elif protein_id == "ENSP00000123456":
            return {"ensembl_gene_id": "ENSG00000111111"}
        return {"error": "Not found"}

    with (
        patch.object(
            server, "fetch_marrvel_data", new=AsyncMock(return_value=mock_string_response)
        ),
        patch.object(
            server, "get_gene_by_entrez_id", new=AsyncMock(return_value=mock_gene_response)
        ),
        patch.object(
            server,
            "get_ensembl_protein_ids_by_ensembl_gene_id",
            new=AsyncMock(return_value=mock_protein_ids_response),
        ),
        patch.object(server, "resolve_ensembl_protein_to_gene_id", new=mock_resolve),
    ):

        result = await server.get_string_interactions_by_entrez_id("441457")
        result_obj = json.loads(result)

    # Verify the response structure
    assert "data" in result_obj
    assert "stringInteractionsByEntrezId" in result_obj["data"]

    interactions = result_obj["data"]["stringInteractionsByEntrezId"]
    assert len(interactions) > 0

    # Check that the first interaction has the new field
    first_interaction = interactions[0]
    assert "connectedEnsemblId" in first_interaction
    assert "connectedEnsemblGeneId" in first_interaction

    # The connectedEnsemblId should be a protein ID (ENSP)
    assert first_interaction["connectedEnsemblId"].startswith("ENSP")

    # The connectedEnsemblGeneId should be a gene ID (ENSG)
    assert first_interaction["connectedEnsemblGeneId"].startswith("ENSG")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_string_interactions_handles_conversion_error():
    """Test that STRING interactions handle conversion errors gracefully."""
    import server

    mock_string_response = json.dumps(
        {
            "data": {
                "stringInteractionsByEntrezId": [
                    {
                        "ensemblId1": "ENSP00000297591",
                        "ensemblId2": "ENSP00000999999",
                        "database": "STRING",
                        "combExpDb": 0.9,
                        "experiments": 5,
                    }
                ]
            }
        }
    )

    mock_gene_response = json.dumps(
        {"data": {"geneByEntrezId": {"xref": {"ensemblId": "ENSG00000100000"}}}}
    )

    mock_protein_ids_response = json.dumps(
        {
            "ensembl_protein_ids": ["ENSP00000999998"],
            "ensembl_canonical_protein_id": "ENSP00000999998",
        }
    )

    # Mock the conversion to return an error
    async def mock_resolve_with_error(protein_id):
        return {"error": f"Failed to convert {protein_id}"}

    with (
        patch.object(
            server, "fetch_marrvel_data", new=AsyncMock(return_value=mock_string_response)
        ),
        patch.object(
            server, "get_gene_by_entrez_id", new=AsyncMock(return_value=mock_gene_response)
        ),
        patch.object(
            server,
            "get_ensembl_protein_ids_by_ensembl_gene_id",
            new=AsyncMock(return_value=mock_protein_ids_response),
        ),
        patch.object(server, "resolve_ensembl_protein_to_gene_id", new=mock_resolve_with_error),
    ):

        result = await server.get_string_interactions_by_entrez_id("441457")
        result_obj = json.loads(result)

    # Verify the response includes error information
    assert "data" in result_obj
    interactions = result_obj["data"]["stringInteractionsByEntrezId"]
    assert len(interactions) > 0

    first_interaction = interactions[0]
    assert "connectedEnsemblGeneId" in first_interaction
    assert first_interaction["connectedEnsemblGeneId"] is None
    assert "conversionError" in first_interaction
    assert "Failed to convert" in first_interaction["conversionError"]
