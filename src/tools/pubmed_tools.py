"""
PubMed Literature Search Tools for MARRVEL-MCP.

This module provides tools for searching PubMed and retrieving biomedical literature
using the pymed_paperscraper library. Supports flexible queries for genes, variants,
symptoms, diseases, and other biomedical terms.
"""

import json
from typing import Optional
from pymed_paperscraper import PubMed


def register_tools(mcp_instance):
    """
    Register all PubMed tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    mcp_instance.tool()(search_pubmed)
    mcp_instance.tool()(get_pubmed_article)


async def search_pubmed(
    query: str, max_results: int = 50, email: str = "marrvel@example.com"
) -> str:
    """
    Search PubMed for biomedical literature and retrieve article details.

    This tool performs comprehensive PubMed searches for any biomedical query including
    gene names, variants, diseases, symptoms, drug names, or research topics. It returns
    PubMed IDs along with article metadata including titles, abstracts, authors, and
    publication information.

    Args:
        query: Search query using any biomedical terms. Examples:
            - Gene names: "TP53 cancer", "BRCA1 breast cancer"
            - Variants: "rs1042522", "R175H TP53"
            - Diseases: "Alzheimer's disease genetics"
            - Symptoms: "fever malaria treatment"
            - Drug names: "aspirin cardiovascular disease"
            - General: "CRISPR gene editing"
        max_results: Maximum number of results to return (default: 50, max: 100)
        email: Email address for PubMed API identification (default: marrvel@example.com)

    Returns:
        JSON string containing search results with:
        - total_results: Total number of matches found
        - returned_results: Number of results in this response
        - articles: List of article objects, each containing:
            - pubmed_id: PubMed ID (PMID)
            - title: Article title
            - abstract: Article abstract (if available)
            - authors: List of author names
            - journal: Journal name
            - publication_date: Publication date
            - doi: Digital Object Identifier (if available)
            - keywords: Article keywords (if available)

    Example:
        search_pubmed("TP53 cancer therapy", max_results=10)
        search_pubmed("BRCA1 mutation breast cancer", max_results=25)
        search_pubmed("Alzheimer's disease APOE", max_results=50)

    Note:
        - Results are limited to max_results for performance
        - Not all articles have full abstracts available
        - Some articles may have limited metadata
    """
    try:
        # Validate max_results
        if max_results < 1 or max_results > 100:
            return json.dumps({"error": "max_results must be between 1 and 100"}, indent=2)

        # Initialize PubMed client
        pubmed = PubMed(tool="MARRVEL_MCP", email=email)

        # Get total count first
        try:
            total_count = pubmed.getTotalResultsCount(query)
        except Exception:
            # If count fails, set to unknown
            total_count = "unknown"

        # Perform search
        results = pubmed.query(query, max_results=max_results)

        # Process results
        articles = []
        for article in results:
            try:
                # Extract article information
                article_data = {
                    "pubmed_id": article.pubmed_id,
                    "title": article.title,
                    "abstract": article.abstract,
                    "authors": (
                        [str(author) for author in article.authors] if article.authors else []
                    ),
                    "journal": article.journal,
                    "publication_date": (
                        str(article.publication_date) if article.publication_date else None
                    ),
                    "doi": article.doi,
                    "keywords": article.keywords if article.keywords else [],
                    "methods": article.methods,
                    "conclusions": article.conclusions,
                    "results": article.results,
                }
                articles.append(article_data)
            except Exception as e:
                # If individual article processing fails, continue with others
                continue

        # Prepare response
        response = {
            "query": query,
            "total_results": total_count,
            "returned_results": len(articles),
            "max_results": max_results,
            "articles": articles,
        }

        return json.dumps(response, indent=2)

    except Exception as e:
        return json.dumps({"error": f"PubMed search failed: {str(e)}", "query": query}, indent=2)


async def get_pubmed_article(pubmed_id: str, email: str = "marrvel@example.com") -> str:
    """
    Retrieve detailed information for a specific PubMed article by PMID.

    This tool fetches comprehensive details for a single PubMed article including
    title, abstract, authors, journal information, keywords, and publication metadata.

    Args:
        pubmed_id: PubMed ID (PMID) as a string (e.g., "12345678")
        email: Email address for PubMed API identification (default: marrvel@example.com)

    Returns:
        JSON string containing article details:
        - pubmed_id: PubMed ID
        - title: Article title
        - abstract: Full abstract
        - authors: List of authors
        - journal: Journal name
        - publication_date: Date of publication
        - doi: Digital Object Identifier
        - keywords: Article keywords
        - methods: Methods section (if available)
        - results: Results section (if available)
        - conclusions: Conclusions section (if available)
        - copyrights: Copyright information (if available)

    Example:
        get_pubmed_article("32601318")  # COVID-19 related article
        get_pubmed_article("28887537")  # TP53 cancer article

    Note:
        - Not all articles have all fields available
        - Full text sections (methods, results, conclusions) may not be available
          for all articles depending on publisher restrictions
    """
    try:
        # Initialize PubMed client
        pubmed = PubMed(tool="MARRVEL_MCP", email=email)

        # Search for specific PMID
        results = pubmed.query(pubmed_id, max_results=1)

        # Get the first (and only) result
        article = next(results, None)

        if not article:
            return json.dumps({"error": f"Article with PMID {pubmed_id} not found"}, indent=2)

        # Extract comprehensive article information
        article_data = {
            "pubmed_id": article.pubmed_id,
            "title": article.title,
            "abstract": article.abstract,
            "authors": ([str(author) for author in article.authors] if article.authors else []),
            "journal": article.journal,
            "publication_date": str(article.publication_date) if article.publication_date else None,
            "doi": article.doi,
            "keywords": article.keywords if article.keywords else [],
            "methods": article.methods,
            "results": article.results,
            "conclusions": article.conclusions,
            "copyrights": article.copyrights,
        }

        return json.dumps(article_data, indent=2)

    except Exception as e:
        return json.dumps(
            {"error": f"Failed to retrieve article: {str(e)}", "pubmed_id": pubmed_id},
            indent=2,
        )
