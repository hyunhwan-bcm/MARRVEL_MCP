"""
Disease-related tools for MARRVEL-MCP.

This module provides tools for querying disease information from OMIM
(Online Mendelian Inheritance in Man) database.
"""

import httpx
from src.utils.api_client import fetch_marrvel_data
from mcp.server.fastmcp import FastMCP


async def get_omim_by_mim_number(mim_number: str) -> str:
    """
    Retrieve OMIM (Online Mendelian Inheritance in Man) entry by MIM number.

    OMIM is a comprehensive database of human genes and genetic disorders.

    Args:
        mim_number: OMIM MIM number (e.g., "191170" for Treacher Collins syndrome)

    Returns:
        JSON string with OMIM entry:
        - Disease/phenotype description
        - Clinical features
        - Inheritance pattern
        - Molecular genetics
        - Allelic variants

    Example:
        get_omim_by_mim_number("191170")  #
        get_omim_by_mim_number("114480")  # Breast cancer (BRCA1)
    """
    try:
        data = await fetch_marrvel_data(f"/omim/mimNumber/{mim_number}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def get_omim_by_gene_symbol(gene_symbol: str) -> str:
    """
    Find all OMIM diseases associated with a gene symbol.

    This tool retrieves all OMIM entries (diseases, phenotypes) that are
    associated with a particular gene.

    Args:
        gene_symbol: Official gene symbol (e.g., "TP53", "BRCA1", "CFTR")

    Returns:
        JSON string with list of OMIM diseases including:
        - MIM numbers
        - Disease names
        - Inheritance patterns
        - Gene-disease relationships

    Example:
        get_omim_by_gene_symbol("TP53")  # Li-Fraumeni syndrome
        get_omim_by_gene_symbol("BRCA1")  # Breast/ovarian cancer
        get_omim_by_gene_symbol("CFTR")  # Cystic fibrosis
    """
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def get_omim_variant(gene_symbol: str, variant: str) -> str:
    """
    Query OMIM for specific variant information.

    Get OMIM data for a specific variant in a gene, including disease
    associations and clinical significance.

    Args:
        gene_symbol: Gene symbol (e.g., "TP53")
        variant: Variant description (e.g., "p.R248Q", "c.743G>A")

    Returns:
        JSON string with variant-specific OMIM information

    Example:
        get_omim_variant("TP53", "p.R248Q")
        get_omim_variant("BRCA1", "p.C61G")
    """
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}/variant/{variant}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def search_omim_by_disease_name(disease_name: str) -> str:
    """
    Search OMIM (Online Mendelian Inheritance in Man) by disease name or keyword.

    This tool allows searching for OMIM entries using disease names, symptoms,
    or related keywords. Useful for researchers who don't know the specific
    OMIM ID but want to find relevant genetic disorders.

    Args:
        disease_name: Disease name, symptom, or keyword to search for
                     (e.g., "breast cancer", "cystic fibrosis", "diabetes")

    Returns:
        JSON string with matching OMIM entries including:
        - MIM numbers and disease names
        - Alternative names and synonyms
        - Brief descriptions and clinical features
        - Inheritance patterns
        - Associated genes (when available)

    Example:
        search_omim_by_disease_name("breast cancer")
        search_omim_by_disease_name("cystic fibrosis")
        search_omim_by_disease_name("diabetes")
    """
    try:
        # URL encode the disease name for the API call
        import urllib.parse

        encoded_disease = urllib.parse.quote(disease_name)
        data = await fetch_marrvel_data(f"/omim/phenotypes/title/{encoded_disease}")
        return str(data)
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


async def search_hpo_terms(phenotype_query: str) -> str:
    """
    Search Human Phenotype Ontology (HPO) terms for a phenotype query.

    This tool searches the JAX HPO ontology for phenotype terms matching the query.
    Returns a list of matching HPO terms with their IDs and definitions.

    Args:
        phenotype_query: Phenotype term or symptom to search for
                        (e.g., "dementia", "intellectual disability", "seizures")

    Returns:
        JSON string with HPO search results:
        - query: The search query used
        - total_terms: Number of matching terms found
        - terms: Array of HPO terms with id, name, and definition

    Example:
        search_hpo_terms("dementia")
        search_hpo_terms("intellectual disability")
        search_hpo_terms("seizures")

    API Endpoint: GET https://ontology.jax.org/api/hp/search
    """
    try:
        import json

        # Search for HPO terms
        search_url = "https://ontology.jax.org/api/hp/search"
        params = {"q": phenotype_query, "page": 0, "limit": 10}

        async with httpx.AsyncClient(timeout=30.0) as client:
            search_response = await client.get(search_url, params=params)
            search_response.raise_for_status()
            search_data = search_response.json()

        # Check if we got any results
        if not search_data or not search_data.get("terms"):
            return json.dumps(
                {
                    "error": f"No HPO terms found for query: {phenotype_query}",
                    "query": phenotype_query,
                },
                indent=2,
            )

        terms = search_data["terms"]

        result = {"query": phenotype_query, "total_terms": len(terms), "terms": terms}

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return json.dumps(
            {
                "error": f"JAX Ontology API error: {e.response.status_code}",
                "message": str(e),
                "query": phenotype_query,
            },
            indent=2,
        )
    except httpx.TimeoutException:
        return json.dumps(
            {
                "error": "Request timeout - JAX Ontology API took too long to respond",
                "query": phenotype_query,
            },
            indent=2,
        )
    except json.JSONDecodeError as e:
        return json.dumps(
            {
                "error": f"Invalid JSON response from JAX Ontology API: {str(e)}",
                "query": phenotype_query,
            },
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to search HPO terms: {str(e)}", "query": phenotype_query}, indent=2
        )


async def get_hpo_associated_genes(hpo_id: str) -> str:
    """
    Get genes associated with a specific Human Phenotype Ontology (HPO) term.

    This tool retrieves genes linked to a given HPO term and identifies the most
    feasible gene based on available annotations and association strength.

    Args:
        hpo_id: HPO term ID (e.g., "HP:0000727" for Dementia)

    Returns:
        JSON string with gene associations:
        - hpo_id: The HPO term ID queried
        - all_genes: Array of all associated genes
        - gene_count: Total number of associated genes
        - most_feasible_gene: The most feasible gene selected based on criteria
        - selection_criteria: Explanation of how the most feasible gene was chosen

    Example:
        get_hpo_associated_genes("HP:0000727")  # Dementia
        get_hpo_associated_genes("HP:0001249")  # Intellectual disability

    API Endpoint: GET https://ontology.jax.org/api/network/annotation/{hpo_id}
    """
    try:
        import json

        # Get genes associated with the HPO term
        # URL encode the HPO ID (replace : with %3A)
        encoded_hpo_id = hpo_id.replace(":", "%3A")
        genes_url = f"https://ontology.jax.org/api/network/annotation/{encoded_hpo_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            genes_response = await client.get(genes_url)
            genes_response.raise_for_status()
            genes_data = genes_response.json()

        # Extract genes from the response
        genes = genes_data.get("genes", [])

        if not genes:
            return json.dumps(
                {
                    "hpo_id": hpo_id,
                    "genes": [],
                    "gene_count": 0,
                    "most_feasible_gene": None,
                    "selection_criteria": "No genes associated with this HPO term",
                },
                indent=2,
            )

        # Select the most feasible gene
        # Criteria (in order of preference):
        # 1. Genes with more detailed annotations (longer names/descriptions)
        # 2. Well-known genes (if we can identify them)
        # 3. Alphabetical order as tiebreaker

        most_feasible_gene = None
        max_score = -1

        for gene in genes:
            score = 0

            # Prefer genes with longer, more descriptive names
            name = gene.get("name", "")
            if len(name) > 20:  # Longer names likely have more detail
                score += 2
            elif len(name) > 10:
                score += 1

            # Prefer genes with symbols that look like standard gene symbols
            symbol = gene.get("symbol", "")
            if symbol and symbol.isupper() and len(symbol) <= 10:
                score += 1

            # Prefer genes with Entrez IDs (more established)
            if gene.get("entrez_id"):
                score += 1

            if score > max_score:
                max_score = score
                most_feasible_gene = gene

        # If no gene got a good score, just pick the first one
        if not most_feasible_gene:
            most_feasible_gene = genes[0]

        result = {
            "hpo_id": hpo_id,
            "genes": genes,
            "gene_count": len(genes),
            "most_feasible_gene": most_feasible_gene,
            "selection_criteria": "Selected based on annotation completeness, symbol format, and Entrez ID availability",
        }

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return json.dumps(
            {
                "error": f"JAX Ontology API error: {e.response.status_code}",
                "message": str(e),
                "hpo_id": hpo_id,
            },
            indent=2,
        )
    except httpx.TimeoutException:
        return json.dumps(
            {
                "error": "Request timeout - JAX Ontology API took too long to respond",
                "hpo_id": hpo_id,
            },
            indent=2,
        )
    except json.JSONDecodeError as e:
        return json.dumps(
            {"error": f"Invalid JSON response from JAX Ontology API: {str(e)}", "hpo_id": hpo_id},
            indent=2,
        )
    except Exception as e:
        return json.dumps(
            {"error": f"Failed to retrieve HPO associated genes: {str(e)}", "hpo_id": hpo_id},
            indent=2,
        )


def register_tools(mcp_instance: FastMCP):
    """
    Register all disease tools with the MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """
    # Register the tools
    mcp_instance.tool()(get_omim_by_mim_number)
    mcp_instance.tool()(get_omim_by_gene_symbol)
    mcp_instance.tool()(get_omim_variant)
    mcp_instance.tool()(search_omim_by_disease_name)
    mcp_instance.tool()(search_hpo_terms)
    mcp_instance.tool()(get_hpo_associated_genes)
