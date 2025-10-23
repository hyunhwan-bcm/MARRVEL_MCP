"""
Integration tests for PubMed tools.

These tests make real API calls to PubMed and verify the complete functionality.
They are marked with @pytest.mark.integration and can be skipped with:
    pytest -m "not integration"
"""

import pytest
import json
import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.tools.pubmed_tools import search_pubmed, get_pubmed_article


@pytest.mark.integration
class TestPubmedSearchIntegration:
    """Integration tests for PubMed search functionality."""

    @pytest.mark.asyncio
    async def test_search_with_gene_name(self):
        """Test searching PubMed with a gene name."""
        result = await search_pubmed("TP53", max_results=5)
        result_data = json.loads(result)

        # Verify response structure
        assert "query" in result_data
        assert "total_results" in result_data
        assert "returned_results" in result_data
        assert "articles" in result_data

        # Should find many results for TP53
        assert result_data["total_results"] > 0 or result_data["total_results"] == "unknown"
        assert result_data["returned_results"] > 0
        assert len(result_data["articles"]) > 0

        # Verify article structure
        article = result_data["articles"][0]
        assert "pubmed_id" in article
        assert "title" in article
        assert article["pubmed_id"] is not None

    @pytest.mark.asyncio
    async def test_search_with_disease_term(self):
        """Test searching with a disease term."""
        result = await search_pubmed("breast cancer BRCA1", max_results=10)
        result_data = json.loads(result)

        assert result_data["returned_results"] > 0
        assert len(result_data["articles"]) > 0

    @pytest.mark.asyncio
    async def test_search_with_specific_query(self):
        """Test searching with a more specific query."""
        result = await search_pubmed("Alzheimer disease genetics", max_results=3)
        result_data = json.loads(result)

        assert result_data["returned_results"] > 0
        for article in result_data["articles"]:
            assert article["pubmed_id"] is not None
            assert article["title"] is not None

    @pytest.mark.asyncio
    async def test_search_returns_abstracts(self):
        """Test that search returns articles with abstracts."""
        result = await search_pubmed("COVID-19 vaccine", max_results=5)
        result_data = json.loads(result)

        assert result_data["returned_results"] > 0

        # At least some articles should have abstracts
        articles_with_abstracts = [
            a for a in result_data["articles"] if a.get("abstract") is not None
        ]
        assert len(articles_with_abstracts) > 0


@pytest.mark.integration
class TestGetPubmedArticleIntegration:
    """Integration tests for retrieving specific PubMed articles."""

    @pytest.mark.asyncio
    async def test_get_known_article(self):
        """Test retrieving a known article by PMID."""
        # PMID 32601318 is a known COVID-19 related article
        result = await get_pubmed_article("32601318")
        result_data = json.loads(result)

        # Should not have error
        assert "error" not in result_data

        # Verify article details
        assert result_data["pubmed_id"] == "32601318"
        assert result_data["title"] is not None
        assert result_data["abstract"] is not None
        assert len(result_data["authors"]) > 0

    @pytest.mark.asyncio
    async def test_get_nonexistent_article(self):
        """Test handling of invalid PMID."""
        # Use a very unlikely PMID
        result = await get_pubmed_article("99999999999")
        result_data = json.loads(result)

        # Should return error or empty result
        # Note: PubMed might handle this differently
        assert "error" in result_data or result_data.get("pubmed_id") is None

    @pytest.mark.asyncio
    async def test_get_article_has_required_fields(self):
        """Test that retrieved article has expected fields."""
        result = await get_pubmed_article("28887537")  # Another known article
        result_data = json.loads(result)

        if "error" not in result_data:
            # Verify all expected fields are present
            expected_fields = [
                "pubmed_id",
                "title",
                "abstract",
                "authors",
                "journal",
                "publication_date",
                "doi",
                "keywords",
            ]
            for field in expected_fields:
                assert field in result_data
