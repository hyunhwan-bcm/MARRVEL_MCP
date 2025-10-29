"""
PubMed and PubMed Central tools for MARRVEL-MCP.

This module provides tools for searching biomedical literature and retrieving
full-text articles from PubMed and PubMed Central databases.
"""

import json
from typing import Optional

import httpx
from lxml import etree
from pymed_paperscraper import PubMed


async def search_pubmed(
    query: str, max_results: int = 50, email: str = "marrvel@example.com"
) -> str:
    """
    Search PubMed for biomedical literature on genes, variants, diseases, or drugs.

    Returns PMIDs with titles, abstracts, authors, journal, and publication metadata.
    Essential for literature review and evidence gathering.

    Args:
        query: Biomedical search terms (e.g., "TP53 cancer", "BRCA1 mutation",
            "Alzheimer's disease genetics")
        max_results: Maximum results to return (default: 50, max: 100)
        email: Email for PubMed API (default: marrvel@example.com)

    Returns:
        JSON with total_results, returned_results, and articles array containing
        pubmed_id, title, abstract, authors, journal, publication_date, doi, keywords

    Example:
        search_pubmed("TP53 cancer therapy", max_results=10)
        search_pubmed("BRCA1 mutation breast cancer")
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


async def get_pmc_fulltext_by_pmcid(pmcid: str) -> str:
    """
    Retrieve full text of a PubMed Central (PMC) open-access article.

    Returns plain text body of the article. Use for detailed content analysis
    when abstract isn't sufficient.

    Args:
        pmcid: PMC ID (e.g., "PMC3257301")

    Returns:
        JSON with pmcid, fulltext (plain text body), and error (if applicable)

    Example:
        get_pmc_fulltext_by_pmcid("PMC3257301")
    """
    try:
        if not pmcid or not pmcid.startswith("PMC"):
            return json.dumps({"pmcid": pmcid, "fulltext": "", "error": "Invalid PMCID"}, indent=2)

        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pmc&id={pmcid}"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            xml = resp.content
        root = etree.fromstring(xml)
        body = root.find(".//body")
        if body is None:
            return json.dumps(
                {"pmcid": pmcid, "fulltext": "", "error": "No full text body found."}, indent=2
            )
        text_parts = []
        for elem in body.iter():
            if elem.tag in ("p", "sec", "title"):
                if elem.text:
                    cleaned = " ".join(elem.text.split())
                    if cleaned:
                        text_parts.append(cleaned)
        output = "\n".join([line for line in text_parts if line.strip()])
        return json.dumps({"pmcid": pmcid, "fulltext": output}, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps(
            {"pmcid": pmcid, "fulltext": "", "error": f"HTTP error: {e.response.status_code}"},
            indent=2,
        )
    except Exception as e:
        return json.dumps({"pmcid": pmcid, "fulltext": "", "error": str(e)}, indent=2)


def _init_pubmed_client(email: str) -> PubMed:
    """
    Initialize and return a PubMed client.

    Args:
        email: Email address for PubMed API identification

    Returns:
        PubMed client instance
    """
    return PubMed(tool="MARRVEL_MCP", email=email)


async def pmid_to_pmcid(pmid: str) -> str:
    """
    Convert PubMed ID (PMID) to PMC ID (PMCID) for full-text access.

    Returns PMCID if the article is available in PMC open-access. Use before
    fetching full text with get_pmc_fulltext_by_pmcid.

    Args:
        pmid: PubMed ID (e.g., "37741276")

    Returns:
        JSON with pmid, pmcid (format "PMC{ID}" or empty if not available), and error

    Example:
        pmid_to_pmcid("37741276")
    """
    try:
        if not pmid or not pmid.isdigit():
            return json.dumps({"pmid": pmid, "pmcid": "", "error": "Invalid PMID"}, indent=2)

        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

        # Parse PMCID from response
        pmcid = ""
        try:
            linksets = data.get("linksets", [])
            if linksets:
                linksetdbs = linksets[0].get("linksetdbs", [])
                if linksetdbs and "links" in linksetdbs[0]:
                    pmc_id_num = linksetdbs[0]["links"][0]
                    pmcid = f"PMC{pmc_id_num}"
        except Exception:
            pmcid = ""

        return json.dumps({"pmid": pmid, "pmcid": pmcid}, indent=2)
    except httpx.HTTPStatusError as e:
        return json.dumps(
            {"pmid": pmid, "pmcid": "", "error": f"HTTP error: {e.response.status_code}"}, indent=2
        )
    except Exception as e:
        return json.dumps({"pmid": pmid, "pmcid": "", "error": str(e)}, indent=2)


async def get_pubmed_article(pubmed_id: str, email: str = "zhandongliulab@bcm.edu") -> str:
    """
    Retrieve detailed information for a specific PubMed article by PMID.

    Returns comprehensive metadata for a single article. Use when you have a specific
    PMID and need detailed information.

    Args:
        pubmed_id: PubMed ID (e.g., "32601318")
        email: Email for PubMed API (default: zhandongliulab@bcm.edu)

    Returns:
        JSON with pubmed_id, title, abstract, authors, journal, publication_date, doi,
        keywords, methods, results, conclusions, copyrights

    Example:
        get_pubmed_article("32601318")  # COVID-19 article
        get_pubmed_article("28887537")  # TP53 cancer article

    Note: Full text sections may not be available for all articles.
    """
    try:
        # Initialize PubMed client
        pubmed = _init_pubmed_client(email)

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


def register_tools(mcp_instance):
    """
    Register PubMed/PMC tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    mcp_instance.tool()(search_pubmed)
    mcp_instance.tool()(get_pmc_fulltext_by_pmcid)
    mcp_instance.tool()(pmid_to_pmcid)
    mcp_instance.tool()(get_pubmed_article)
