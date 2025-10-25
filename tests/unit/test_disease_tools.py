import pytest
import json
from unittest.mock import AsyncMock, patch
from src.tools import disease_tools


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_omim_by_mim_number_success():
    """Test successful OMIM lookup by MIM number."""
    mock_data = {
        "mim_number": "191170",
        "title": "Treacher Collins syndrome",
        "description": "A disorder of craniofacial development",
    }

    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_data

        result = await disease_tools.get_omim_by_mim_number("191170")
        assert result == str(mock_data)

        mock_fetch.assert_called_once_with("/omim/mimNumber/191170")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_omim_by_mim_number_error():
    """Test error handling for OMIM lookup by MIM number."""
    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        import httpx

        mock_fetch.side_effect = httpx.HTTPError("API Error")

        result = await disease_tools.get_omim_by_mim_number("191170")
        assert "Error fetching OMIM data: API Error" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_omim_by_gene_symbol_success():
    """Test successful OMIM lookup by gene symbol."""
    mock_data = {
        "gene_symbol": "TP53",
        "diseases": [
            {"mim_number": "191170", "title": "Li-Fraumeni syndrome"},
            {"mim_number": "114480", "title": "Breast cancer"},
        ],
    }

    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_data

        result = await disease_tools.get_omim_by_gene_symbol("TP53")
        assert result == str(mock_data)

        mock_fetch.assert_called_once_with("/omim/gene/symbol/TP53")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_omim_variant_success():
    """Test successful OMIM variant lookup."""
    mock_data = {
        "gene_symbol": "TP53",
        "variant": "p.R248Q",
        "disease_associations": ["Li-Fraumeni syndrome"],
    }

    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_data

        result = await disease_tools.get_omim_variant("TP53", "p.R248Q")
        assert result == str(mock_data)

        mock_fetch.assert_called_once_with("/omim/gene/symbol/TP53/variant/p.R248Q")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_omim_by_disease_name_success():
    """Test successful OMIM search by disease name."""
    mock_data = {
        "query": "breast cancer",
        "results": [
            {
                "mim_number": "114480",
                "title": "Breast cancer",
                "synonyms": ["Mammary cancer", "Breast carcinoma"],
                "description": "A malignant tumor of the breast tissue",
            },
            {
                "mim_number": "604370",
                "title": "Breast cancer, susceptibility to",
                "synonyms": ["BRCA1-related breast cancer"],
                "description": "Increased risk of breast cancer due to genetic factors",
            },
        ],
    }

    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_data

        result = await disease_tools.search_omim_by_disease_name("breast cancer")
        assert result == str(mock_data)

        mock_fetch.assert_called_once_with("/omim/phenotypes/title/breast%20cancer")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_omim_by_disease_name_with_special_chars():
    """Test OMIM search with special characters in disease name."""
    mock_data = {
        "query": "Alzheimer's disease",
        "results": [
            {
                "mim_number": "104300",
                "title": "Alzheimer disease",
                "description": "A neurodegenerative disorder",
            }
        ],
    }

    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_data

        result = await disease_tools.search_omim_by_disease_name("Alzheimer's disease")
        assert result == str(mock_data)

        mock_fetch.assert_called_once_with("/omim/phenotypes/title/Alzheimer%27s%20disease")


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_omim_by_disease_name_error():
    """Test error handling for OMIM search by disease name."""
    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        import httpx

        mock_fetch.side_effect = httpx.HTTPError("API Error")

        result = await disease_tools.search_omim_by_disease_name("breast cancer")
        assert "Error fetching OMIM data: API Error" in result


@pytest.mark.unit
@pytest.mark.asyncio
async def test_search_omim_by_disease_name_empty_input():
    """Test OMIM search with empty input."""
    mock_data = {"error": "No results found"}

    with patch("src.tools.disease_tools.fetch_marrvel_data", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = mock_data

        result = await disease_tools.search_omim_by_disease_name("")
        assert result == str(mock_data)

        mock_fetch.assert_called_once_with("/omim/phenotypes/title/")
