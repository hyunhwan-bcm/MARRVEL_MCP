"""
Unit tests for pubmed_tools module.

Tests the PubMed search and article retrieval functions with mocked responses.
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os
import json

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.tools.pubmed_tools import search_pubmed, get_pubmed_article


@pytest.mark.unit
class TestSearchPubmed:
    """Test the search_pubmed function."""

    @pytest.mark.asyncio
    async def test_successful_search(self):
        """Test successful PubMed search with multiple results."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            # Create mock PubMed instance
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed

            # Mock getTotalResultsCount
            mock_pubmed.getTotalResultsCount.return_value = 100

            # Create mock articles
            mock_article1 = MagicMock()
            mock_article1.pubmed_id = "12345678"
            mock_article1.title = "TP53 mutations in cancer"
            mock_article1.abstract = "This study examines TP53 mutations."
            mock_article1.authors = ["Smith J", "Doe A"]
            mock_article1.journal = "Nature"
            mock_article1.publication_date = "2023-01-15"
            mock_article1.doi = "10.1038/example"
            mock_article1.keywords = ["TP53", "cancer"]
            mock_article1.methods = "Methods section text"
            mock_article1.conclusions = "Conclusions text"
            mock_article1.results = "Results text"

            mock_article2 = MagicMock()
            mock_article2.pubmed_id = "87654321"
            mock_article2.title = "BRCA1 and breast cancer"
            mock_article2.abstract = "This study examines BRCA1 mutations."
            mock_article2.authors = ["Johnson M"]
            mock_article2.journal = "Cell"
            mock_article2.publication_date = "2023-02-20"
            mock_article2.doi = "10.1016/example"
            mock_article2.keywords = ["BRCA1", "breast cancer"]
            mock_article2.methods = None
            mock_article2.conclusions = None
            mock_article2.results = None

            # Mock query to return articles
            mock_pubmed.query.return_value = iter([mock_article1, mock_article2])

            # Execute search
            result = await search_pubmed("TP53 cancer", max_results=2)

            # Verify PubMed was called correctly
            mock_pubmed_class.assert_called_once_with(
                tool="MARRVEL_MCP", email="marrvel@example.com"
            )
            mock_pubmed.getTotalResultsCount.assert_called_once_with("TP53 cancer")
            mock_pubmed.query.assert_called_once_with("TP53 cancer", max_results=2)

            # Parse and verify result
            result_data = json.loads(result)
            assert result_data["query"] == "TP53 cancer"
            assert result_data["total_results"] == 100
            assert result_data["returned_results"] == 2
            assert result_data["max_results"] == 2
            assert len(result_data["articles"]) == 2
            assert result_data["articles"][0]["pubmed_id"] == "12345678"
            assert result_data["articles"][0]["title"] == "TP53 mutations in cancer"
            assert result_data["articles"][1]["pubmed_id"] == "87654321"

    @pytest.mark.asyncio
    async def test_search_with_no_results(self):
        """Test PubMed search that returns no results."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.getTotalResultsCount.return_value = 0
            mock_pubmed.query.return_value = iter([])

            result = await search_pubmed("nonexistent_query_xyz123", max_results=10)

            result_data = json.loads(result)
            assert result_data["returned_results"] == 0
            assert result_data["total_results"] == 0
            assert len(result_data["articles"]) == 0

    @pytest.mark.asyncio
    async def test_search_with_invalid_max_results(self):
        """Test validation of max_results parameter."""
        # Test max_results too small
        result = await search_pubmed("test query", max_results=0)
        result_data = json.loads(result)
        assert "error" in result_data
        assert "max_results must be between 1 and 100" in result_data["error"]

        # Test max_results too large
        result = await search_pubmed("test query", max_results=101)
        result_data = json.loads(result)
        assert "error" in result_data
        assert "max_results must be between 1 and 100" in result_data["error"]

    @pytest.mark.asyncio
    async def test_search_with_api_error(self):
        """Test error handling when PubMed API fails."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.query.side_effect = Exception("API connection failed")

            result = await search_pubmed("test query", max_results=10)

            result_data = json.loads(result)
            assert "error" in result_data
            assert "PubMed search failed" in result_data["error"]
            assert result_data["query"] == "test query"

    @pytest.mark.asyncio
    async def test_search_with_custom_email(self):
        """Test that custom email is passed to PubMed client."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.getTotalResultsCount.return_value = 0
            mock_pubmed.query.return_value = iter([])

            await search_pubmed("test", max_results=10, email="custom@example.com")

            mock_pubmed_class.assert_called_once_with(
                tool="MARRVEL_MCP", email="custom@example.com"
            )

    @pytest.mark.asyncio
    async def test_search_handles_partial_article_data(self):
        """Test handling of articles with missing data fields."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.getTotalResultsCount.return_value = 1

            # Create article with minimal data
            mock_article = MagicMock()
            mock_article.pubmed_id = "12345678"
            mock_article.title = "Test Article"
            mock_article.abstract = None
            mock_article.authors = None
            mock_article.journal = None
            mock_article.publication_date = None
            mock_article.doi = None
            mock_article.keywords = None
            mock_article.methods = None
            mock_article.conclusions = None
            mock_article.results = None

            mock_pubmed.query.return_value = iter([mock_article])

            result = await search_pubmed("test", max_results=1)

            result_data = json.loads(result)
            assert result_data["returned_results"] == 1
            article = result_data["articles"][0]
            assert article["pubmed_id"] == "12345678"
            assert article["title"] == "Test Article"
            assert article["abstract"] is None
            assert article["authors"] == []
            assert article["keywords"] == []

    @pytest.mark.asyncio
    async def test_search_skips_malformed_articles(self):
        """Test that search continues when individual articles fail to process."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.getTotalResultsCount.return_value = 2

            # Create one good article and one that raises error
            mock_article_good = MagicMock()
            mock_article_good.pubmed_id = "12345678"
            mock_article_good.title = "Good Article"
            mock_article_good.abstract = "Valid abstract"
            mock_article_good.authors = []
            mock_article_good.journal = "Test Journal"
            mock_article_good.publication_date = None
            mock_article_good.doi = None
            mock_article_good.keywords = []
            mock_article_good.methods = None
            mock_article_good.conclusions = None
            mock_article_good.results = None

            mock_article_bad = MagicMock()
            mock_article_bad.pubmed_id = None  # Will cause error
            type(mock_article_bad).title = property(
                lambda self: (_ for _ in ()).throw(Exception("Error"))
            )

            mock_pubmed.query.return_value = iter([mock_article_bad, mock_article_good])

            result = await search_pubmed("test", max_results=2)

            result_data = json.loads(result)
            # Should have 1 result (the good one), skipping the bad one
            assert result_data["returned_results"] == 1
            assert result_data["articles"][0]["pubmed_id"] == "12345678"


@pytest.mark.unit
class TestGetPubmedArticle:
    """Test the get_pubmed_article function."""

    @pytest.mark.asyncio
    async def test_successful_article_retrieval(self):
        """Test successful retrieval of a specific article by PMID."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed

            # Create mock article
            mock_article = MagicMock()
            mock_article.pubmed_id = "12345678"
            mock_article.title = "TP53 mutations in cancer"
            mock_article.abstract = "Detailed abstract text here."
            mock_article.authors = ["Smith J", "Doe A", "Johnson M"]
            mock_article.journal = "Nature Genetics"
            mock_article.publication_date = "2023-05-15"
            mock_article.doi = "10.1038/ng.12345"
            mock_article.keywords = ["TP53", "cancer", "mutations"]
            mock_article.methods = "Methods text"
            mock_article.results = "Results text"
            mock_article.conclusions = "Conclusions text"
            mock_article.copyrights = "Copyright 2023"

            mock_pubmed.query.return_value = iter([mock_article])

            result = await get_pubmed_article("12345678")

            # Verify PubMed was called correctly
            mock_pubmed_class.assert_called_once_with(
                tool="MARRVEL_MCP", email="marrvel@example.com"
            )
            mock_pubmed.query.assert_called_once_with("12345678", max_results=1)

            # Parse and verify result
            result_data = json.loads(result)
            assert result_data["pubmed_id"] == "12345678"
            assert result_data["title"] == "TP53 mutations in cancer"
            assert result_data["abstract"] == "Detailed abstract text here."
            assert len(result_data["authors"]) == 3
            assert result_data["journal"] == "Nature Genetics"
            assert result_data["doi"] == "10.1038/ng.12345"
            assert "TP53" in result_data["keywords"]
            assert result_data["methods"] == "Methods text"
            assert result_data["copyrights"] == "Copyright 2023"

    @pytest.mark.asyncio
    async def test_article_not_found(self):
        """Test handling when article with given PMID is not found."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.query.return_value = iter([])  # No results

            result = await get_pubmed_article("99999999")

            result_data = json.loads(result)
            assert "error" in result_data
            assert "not found" in result_data["error"]
            assert result_data["error"] == "Article with PMID 99999999 not found"

    @pytest.mark.asyncio
    async def test_article_retrieval_with_api_error(self):
        """Test error handling when API fails."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.query.side_effect = Exception("Network error")

            result = await get_pubmed_article("12345678")

            result_data = json.loads(result)
            assert "error" in result_data
            assert "Failed to retrieve article" in result_data["error"]
            assert result_data["pubmed_id"] == "12345678"

    @pytest.mark.asyncio
    async def test_article_with_custom_email(self):
        """Test that custom email is passed correctly."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed
            mock_pubmed.query.return_value = iter([])

            await get_pubmed_article("12345678", email="researcher@university.edu")

            mock_pubmed_class.assert_called_once_with(
                tool="MARRVEL_MCP", email="researcher@university.edu"
            )

    @pytest.mark.asyncio
    async def test_article_with_minimal_data(self):
        """Test handling of article with minimal available data."""
        with patch("src.tools.pubmed_tools.PubMed") as mock_pubmed_class:
            mock_pubmed = MagicMock()
            mock_pubmed_class.return_value = mock_pubmed

            # Create article with minimal data
            mock_article = MagicMock()
            mock_article.pubmed_id = "12345678"
            mock_article.title = "Minimal Article"
            mock_article.abstract = None
            mock_article.authors = None
            mock_article.journal = None
            mock_article.publication_date = None
            mock_article.doi = None
            mock_article.keywords = None
            mock_article.methods = None
            mock_article.results = None
            mock_article.conclusions = None
            mock_article.copyrights = None

            mock_pubmed.query.return_value = iter([mock_article])

            result = await get_pubmed_article("12345678")

            result_data = json.loads(result)
            assert result_data["pubmed_id"] == "12345678"
            assert result_data["title"] == "Minimal Article"
            assert result_data["abstract"] is None
            assert result_data["authors"] == []
            assert result_data["keywords"] == []
