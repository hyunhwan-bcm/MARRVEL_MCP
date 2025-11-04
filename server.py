"""
MARRVEL MCP Server - Unified Implementation

A FastMCP server providing 33+ tools for rare disease genetics research through the MARRVEL platform.
This unified server follows FastMCP 2.0 best practices with minimal boilerplate and clear organization.

Features:
- Gene queries (Entrez ID, symbol, position)
- Variant annotations (dbNSFP, ClinVar, gnomAD, DGV, Geno2MP)
- Disease associations (OMIM, HPO, DECIPHER)
- Ortholog predictions (DIOPT across model organisms)
- Expression data (GTEx tissue expression, drug targets)
- Literature search (PubMed, PMC full-text)
- Coordinate conversion (hg19/hg38 liftover)
- Variant nomenclature tools (HGVS, rsID conversion)

Default genome build: hg19/GRCh37
"""

import logging
import sys
import os
import json
import ssl
import certifi
import inspect
import ast
from typing import Optional
from urllib.parse import quote
import urllib.parse

import requests

import httpx
from lxml import etree
from pymed_paperscraper import PubMed
from mcp.server.fastmcp import FastMCP

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

os.environ.pop("PYTHONLOGLEVEL", None)
os.environ.pop("LOG_LEVEL", None)

# Nuke existing handlers some lib may have added
root = logging.getLogger()
for h in list(root.handlers):
    root.removeHandler(h)
handler = logging.StreamHandler(sys.stderr)
handler.setLevel(logging.WARNING)
root.addHandler(handler)
root.setLevel(logging.WARNING)

# ============================================================================
# API CONFIGURATION
# ============================================================================

API_BASE_URL = "https://marrvel.org/graphql"
API_TIMEOUT = 30.0
VERIFY_SSL = False  # Set to True for production


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


async def fetch_marrvel_data(query: str) -> str:
    """
    Fetch data from MARRVEL API with proper error handling.

    Args:
        endpoint: API endpoint path (e.g., "/gene/entrezId/7157")

    Returns:
        JSON response as string

    Raises:
        httpx.HTTPError: If the HTTP request fails
    """
    payload = {"query": query}
    headers = {"Content-Type": "application/json"}

    verify = ssl.create_default_context(cafile=certifi.where()) if VERIFY_SSL else False

    async def _maybe_await(obj):
        """Await obj if awaitable; call it if callable and await results if needed."""
        try:
            if inspect.isawaitable(obj):
                return await obj
            if callable(obj):
                val = obj()
                if inspect.isawaitable(val):
                    return await val
                return val
            return obj
        except Exception:
            return obj

    async with httpx.AsyncClient(verify=verify, timeout=API_TIMEOUT) as client:
        response = requests.post(
            API_BASE_URL,
            json=payload,
            headers=headers,
            timeout=10,
            verify=VERIFY_SSL,  # Set a timeout for the request
        )

        # Some test mocks make raise_for_status() a coroutine
        rfs = response.raise_for_status()
        if inspect.isawaitable(rfs):
            await rfs

        # Parse JSON (handle mocks that return coroutines)
        try:
            data = response.json()

            if data.get("errors"):
                # Raise an exception if GraphQL errors are present in the response body
                error_details = json.dumps(data["errors"], indent=2)
                raise Exception(f"GraphQL query failed with execution errors:\n{error_details}")

            if inspect.isawaitable(data):
                data = await data
        except json.JSONDecodeError:
            text = await _maybe_await(getattr(response, "text", ""))
            content_type = response.headers.get("Content-Type", "").lower()
            is_json_content_type = "application/json" in content_type or "text/json" in content_type

            error_message = (
                "Invalid JSON response"
                if is_json_content_type
                else "Unexpected API response format"
            )
            err = {
                "error": error_message,
                "status_code": getattr(response, "status_code", None),
                "content": str(text),
                "content_type": content_type,
            }
            return json.dumps(err, indent=2)

        return json.dumps(data, indent=2)


# ============================================================================
# CREATE SERVER INSTANCE
# ============================================================================

mcp = FastMCP(
    name="MARRVEL-MCP",
    instructions=(
        "MARRVEL-MCP enables rare disease research through 32+ genetics tools. "
        "Query genes (symbol/ID/position), analyze variants (dbNSFP, ClinVar, gnomAD), "
        "find disease associations (OMIM, DECIPHER), discover orthologs (DIOPT), "
        "search tissue expression (GTEx), identify drug targets (Pharos), and search "
        "literature (PubMed). Supports liftover between genome builds. "
        "Default coordinates: hg19/GRCh37. State clearly when data is unavailable."
    ),
)


# ============================================================================
# RESOURCES - Static Reference Data
# ============================================================================


@mcp.resource("config://api")
def get_api_config() -> dict:
    """Provides MARRVEL API configuration and settings."""
    return {
        "base_url": API_BASE_URL,
        "timeout": API_TIMEOUT,
        "verify_ssl": VERIFY_SSL,
        "default_genome_build": "hg19/GRCh37",
    }


@mcp.resource("reference://taxonomy-ids")
def get_taxonomy_reference() -> dict:
    """Provides NCBI taxonomy IDs for common model organisms."""
    return {
        "human": {"id": "9606", "name": "Homo sapiens"},
        "mouse": {"id": "10090", "name": "Mus musculus"},
        "rat": {"id": "10116", "name": "Rattus norvegicus"},
        "zebrafish": {"id": "7955", "name": "Danio rerio"},
        "fly": {"id": "7227", "name": "Drosophila melanogaster"},
        "worm": {"id": "6239", "name": "Caenorhabditis elegans"},
        "yeast": {"id": "4932", "name": "Saccharomyces cerevisiae"},
    }


@mcp.resource("reference://genome-builds")
def get_genome_builds() -> dict:
    """Provides information about supported genome builds and coordinates."""
    return {
        "default": "hg19",
        "builds": {
            "hg19": {
                "aliases": ["GRCh37"],
                "description": "Human genome build 19 (Feb 2009)",
                "usage": "Default for MARRVEL tools",
            },
            "hg38": {
                "aliases": ["GRCh38"],
                "description": "Human genome build 38 (Dec 2013)",
                "usage": "Use liftover tools to convert",
            },
        },
    }


@mcp.resource("reference://example-genes")
def get_example_genes() -> dict:
    """Provides example gene symbols and Entrez IDs for testing."""
    return {
        "TP53": {"entrez_id": "7157", "description": "Tumor protein p53"},
        "BRCA1": {"entrez_id": "672", "description": "Breast cancer 1"},
        "BRCA2": {"entrez_id": "675", "description": "Breast cancer 2"},
        "CFTR": {
            "entrez_id": "1080",
            "description": "Cystic fibrosis transmembrane conductance regulator",
        },
        "APOE": {"entrez_id": "348", "description": "Apolipoprotein E"},
    }


# ============================================================================
# GENE TOOLS
# ============================================================================


@mcp.tool(
    name="get_gene_by_entrez_id",
    description="Retrieve comprehensive gene information by NCBI Entrez Gene ID including symbol, location, summary, and transcripts",
    meta={"category": "gene", "version": "1.0"},
)
async def get_gene_by_entrez_id(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(
            f"""
            query MyQuery {{
                geneByEntrezId(entrezId: {entrez_id}) {{
                    alias
                    chr
                    entrezId
                    hg19Start
                    hg19Stop
                    hg38Start
                    hg38Stop
                    hgncId
                    locusType
                    name
                    status
                    taxonId
                    symbol
                    uniprotKBId
                }}
            }}
            """
        )
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


@mcp.tool(
    name="get_gene_by_symbol",
    description="Find gene information by gene symbol across multiple species (human, mouse, fly, worm, etc.)",
    meta={"category": "gene", "version": "1.0"},
)
async def get_gene_by_symbol(gene_symbol: str, taxon_id: str = "9606") -> str:
    try:
        data = await fetch_marrvel_data(
            f"""
            query MyQuery {{
                geneBySymbol(symbol: "{gene_symbol}", taxonId: {taxon_id}) {{
                    alias
                    chr
                    entrezId
                    hg19Start
                    hg19Stop
                    hg38Stop
                    hgncId
                    uniprotKBId
                    taxonId
                    symbol
                    status
                    name
                    locusType
                    hg38Start
                    xref {{
                        ensemblId
                        hgncId
                        mgiId
                        omimId
                        pomBaseId
                    }}
                }}
            }}
            """
        )
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


@mcp.tool(
    name="get_gene_by_position",
    description="Identify genes at a specific chromosomal position in hg19/GRCh37 coordinates",
    meta={"category": "gene", "version": "1.0", "genome_build": "hg19"},
)
async def get_gene_by_position(chromosome: str, position: int, build: str = "hg19") -> str:
    try:
        data = await fetch_marrvel_data(
            f"""
            query MyQuery {{
                genesByGenomicLocation(chr: "{chromosome}", posStart: {position}, posStop: {position}, build: "{build}") {{
                    alias
                    chr
                    entrezId
                    hg19Start
                    hg38Start
                    hg19Stop
                    hg38Stop
                    hgncId
                    locusType
                    name
                    status
                    symbol
                    taxonId
                    uniprotKBId
                    xref {{
                        ensemblId
                        mgiId
                        hgncId
                        omimId
                        pomBaseId
                    }}
                }}
            }}
            """
        )
        return data
    except httpx.HTTPError as e:
        return f"Error fetching gene data: {str(e)}"


# ============================================================================
# VARIANT TOOLS - dbNSFP
# ============================================================================


@mcp.tool(
    name="get_variant_dbnsfp",
    description="Get comprehensive pathogenicity predictions and functional annotations from dbNSFP including SIFT, PolyPhen2, CADD scores",
    meta={"category": "variant", "database": "dbNSFP", "version": "1.0"},
)
async def get_variant_dbnsfp(chr: str, pos: str, ref: str, alt: str, build: str) -> str:
    try:
        data = await fetch_marrvel_data(
            f"""
            query MyQuery {{
                dbnsfpByVariant(build: "{build}", chr: "{chr}", pos: {pos}, alt: "{alt}", ref: "{ref}") {{
                    scores {{
                        CADD {{
                            phred
                            rankscore
                            rawScore
                        }}
                        Polyphen2HDIV {{
                            predictions
                            rankscore
                            scores
                        }}
                        Polyphen2HVAR {{
                            predictions
                            rankscore
                            scores
                        }}
                        SIFT {{
                            predictions
                            scores
                        }}
                        SIFT4G {{
                            predictions
                            rankscore
                        }}
                    }}
                }}
            }}
            """
        )
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# VARIANT TOOLS - ClinVar
# ============================================================================


@mcp.tool(
    name="get_clinvar_by_variant",
    description="Get ClinVar clinical significance and interpretation for a specific variant including pathogenic/benign classification",
    meta={"category": "variant", "database": "ClinVar", "version": "1.0"},
)
async def get_clinvar_by_variant(chr: str, pos: str, ref: str, alt: str) -> str:
    try:
        variant = f"{chr}:{pos} {ref}>{alt}"
        variant_uri = quote(variant, safe="")
        data = await fetch_marrvel_data(f"/clinvar/variant/{variant_uri}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


@mcp.tool(
    name="get_clinvar_by_gene_symbol",
    description="Get all ClinVar variants for a gene by symbol for comprehensive gene-level variant review",
    meta={"category": "variant", "database": "ClinVar", "version": "1.0"},
)
async def get_clinvar_by_gene_symbol(gene_symbol: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/clinvar/gene/symbol/{gene_symbol}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


@mcp.tool(
    name="get_clinvar_by_entrez_id",
    description="Get all ClinVar variants for a gene by Entrez ID with clinical significance data",
    meta={"category": "variant", "database": "ClinVar", "version": "1.0"},
)
async def get_clinvar_by_entrez_id(entrez_id: str, build: str = "hg19") -> str:
    try:
        data = await fetch_marrvel_data(
            f"""
            query MyQuery {{
                clinvarByGeneEntrezId(entrezId: {entrez_id}) {{
                    uid
                    ref
                    alt
                    band
                    chr
                    {"""start
                    stop""" if build == "hg19" else """grch38Start
                    grch38Stop"""}
                    condition
                    interpretation
                    significance {{
                    description
                    }}
                }}
            }}
            """
        )
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# VARIANT TOOLS - gnomAD
# ============================================================================


@mcp.tool(
    name="get_gnomad_variant",
    description="Get population allele frequencies from gnomAD for a specific variant across global and ancestry-specific populations",
    meta={"category": "variant", "database": "gnomAD", "version": "1.0"},
)
async def get_gnomad_variant(chr: str, pos: str, ref: str, alt: str) -> str:
    try:
        variant = f"{chr}:{pos} {ref}>{alt}"
        variant_uri = quote(variant, safe="")
        data = await fetch_marrvel_data(f"/gnomAD/variant/{variant_uri}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


@mcp.tool(
    name="get_gnomad_by_gene_symbol",
    description="Get gnomAD population frequencies for all variants in a gene to identify common vs rare variants",
    meta={"category": "variant", "database": "gnomAD", "version": "1.0"},
)
async def get_gnomad_by_gene_symbol(gene_symbol: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/gnomAD/gene/symbol/{gene_symbol}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


@mcp.tool(
    name="get_gnomad_by_entrez_id",
    description="Get gnomAD population frequencies for a gene by Entrez ID with allele frequency data",
    meta={"category": "variant", "database": "gnomAD", "version": "1.0"},
)
async def get_gnomad_by_entrez_id(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/gnomad/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# VARIANT TOOLS - DGV & Geno2MP
# ============================================================================


@mcp.tool(
    name="get_dgv_by_entrez_id",
    description="Get DGV structural variants and copy number variations (CNVs) for a gene to identify benign structural variants",
    meta={"category": "variant", "database": "DGV", "version": "1.0"},
)
async def get_dgv_by_entrez_id(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/DGV/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


@mcp.tool(
    name="get_geno2mp_by_entrez_id",
    description="Get Geno2MP phenotypes matched to a gene for phenotype-driven gene prioritization in rare disease diagnosis",
    meta={"category": "variant", "database": "Geno2MP", "version": "1.0"},
)
async def get_geno2mp_by_entrez_id(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/geno2mp/gene/entrezId/{entrez_id}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# DISEASE TOOLS - OMIM
# ============================================================================


@mcp.tool(
    name="get_omim_by_mim_number",
    description="Retrieve OMIM disease entry by MIM number with detailed genetic disorder information and clinical features",
    meta={"category": "disease", "database": "OMIM", "version": "1.0"},
)
async def get_omim_by_mim_number(mim_number: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/omim/mimNumber/{mim_number}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


@mcp.tool(
    name="get_omim_by_gene_symbol",
    description="Find all OMIM diseases associated with a gene by symbol for gene-disease relationship analysis",
    meta={"category": "disease", "database": "OMIM", "version": "1.0"},
)
async def get_omim_by_gene_symbol(gene_symbol: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


@mcp.tool(
    name="get_omim_variant",
    description="Get OMIM data for a specific variant with disease associations and clinical significance",
    meta={"category": "disease", "database": "OMIM", "version": "1.0"},
)
async def get_omim_variant(gene_symbol: str, variant: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/omim/gene/symbol/{gene_symbol}/variant/{variant}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


@mcp.tool(
    name="search_omim_by_disease_name",
    description="Search OMIM by disease name or keyword to find matching genetic disorders and associated genes",
    meta={"category": "disease", "database": "OMIM", "version": "1.0"},
)
async def search_omim_by_disease_name(disease_name: str) -> str:
    try:
        encoded_disease = urllib.parse.quote(disease_name)
        data = await fetch_marrvel_data(f"/omim/phenotypes/title/{encoded_disease}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching OMIM data: {str(e)}"


# ============================================================================
# DISEASE TOOLS - HPO
# ============================================================================


@mcp.tool(
    name="search_hpo_terms",
    description="Search Human Phenotype Ontology (HPO) terms by phenotype for standardized clinical phenotype representation",
    meta={"category": "disease", "database": "HPO", "version": "1.0"},
)
async def search_hpo_terms(phenotype_query: str) -> str:
    try:
        search_url = "https://ontology.jax.org/api/hp/search"
        params = {"q": phenotype_query, "page": 0, "limit": 10}

        async with httpx.AsyncClient(timeout=30.0) as client:
            search_response = await client.get(search_url, params=params)
            search_response.raise_for_status()
            search_data = search_response.json()

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


@mcp.tool(
    name="get_hpo_associated_genes",
    description="Get genes associated with an HPO term for phenotype-driven gene discovery and reverse phenotyping",
    meta={"category": "disease", "database": "HPO", "version": "1.0"},
)
async def get_hpo_associated_genes(hpo_id: str) -> str:
    try:
        encoded_hpo_id = hpo_id.replace(":", "%3A")
        genes_url = f"https://ontology.jax.org/api/network/annotation/{encoded_hpo_id}"

        async with httpx.AsyncClient(timeout=30.0) as client:
            genes_response = await client.get(genes_url)
            genes_response.raise_for_status()
            genes_data = genes_response.json()

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

        # Select the most feasible gene based on annotation completeness
        most_feasible_gene = None
        max_score = -1

        for gene in genes:
            score = 0
            name = gene.get("name", "")
            if len(name) > 20:
                score += 2
            elif len(name) > 10:
                score += 1

            symbol = gene.get("symbol", "")
            if symbol and symbol.isupper() and len(symbol) <= 10:
                score += 1

            if gene.get("entrez_id"):
                score += 1

            if score > max_score:
                max_score = score
                most_feasible_gene = gene

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


# ============================================================================
# ORTHOLOG TOOLS - DIOPT
# ============================================================================


@mcp.tool(
    name="get_diopt_orthologs_by_entrez_id",
    description="Find high-confidence orthologs across model organisms (mouse, fly, worm, zebrafish) using DIOPT",
    meta={"category": "ortholog", "database": "DIOPT", "version": "1.0"},
)
async def get_diopt_orthologs_by_entrez_id(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/diopt/ortholog/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT data: {str(e)}"


@mcp.tool(
    name="get_diopt_alignment",
    description="Get protein sequence alignment across orthologous species showing conservation patterns and functional domains",
    meta={"category": "ortholog", "database": "DIOPT", "version": "1.0"},
)
async def get_diopt_alignment(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/diopt/alignment/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching DIOPT alignment data: {str(e)}"


# ============================================================================
# EXPRESSION TOOLS
# ============================================================================


@mcp.tool(
    name="get_gtex_expression",
    description="Get GTEx tissue-specific gene expression across 54 human tissues with median TPM values",
    meta={"category": "expression", "database": "GTEx", "version": "1.0"},
)
async def get_gtex_expression(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/gtex/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching GTEx data: {str(e)}"


@mcp.tool(
    name="get_ortholog_expression",
    description="Get expression patterns for orthologs across model organisms including developmental stages and tissues",
    meta={"category": "expression", "version": "1.0"},
)
async def get_ortholog_expression(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/expression/orthologs/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching ortholog expression data: {str(e)}"


@mcp.tool(
    name="get_pharos_targets",
    description="Get drug target information and druggability assessment from Pharos including approved drugs and clinical trials",
    meta={"category": "expression", "database": "Pharos", "version": "1.0"},
)
async def get_pharos_targets(entrez_id: str) -> str:
    try:
        data = await fetch_marrvel_data(f"/pharos/targets/gene/entrezId/{entrez_id}")
        return data
    except httpx.HTTPError as e:
        return f"Error fetching Pharos data: {str(e)}"


# ============================================================================
# UTILITY TOOLS - Variant Nomenclature & Conversion
# ============================================================================


@mcp.tool(
    name="convert_hgvs_to_genomic",
    description="Convert and validate HGVS variant nomenclature to genomic coordinates using Mutalyzer",
    meta={"category": "utility", "service": "Mutalyzer", "version": "1.0"},
)
async def convert_hgvs_to_genomic(hgvs_variant: str) -> str:
    try:
        encoded_variant = quote(hgvs_variant)
        data = await fetch_marrvel_data(f"/mutalyzer/hgvs/{encoded_variant}")
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error converting HGVS variant: {str(e)}"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)


@mcp.tool(
    name="convert_protein_variant",
    description="Convert protein-level variant to genomic coordinates using Transvar across multiple transcripts",
    meta={"category": "utility", "service": "Transvar", "version": "1.0"},
)
async def convert_protein_variant(protein_variant: str) -> str:
    try:
        encoded_variant = quote(protein_variant)
        data = await fetch_marrvel_data(f"/transvar/protein/{encoded_variant}")
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error converting protein variant: {str(e)}"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"An unexpected error occurred: {str(e)}"}, indent=2)


@mcp.tool(
    name="convert_rsid_to_variant",
    description="Convert dbSNP rsID to MARRVEL variant format with GRCh37/hg19 coordinates",
    meta={"category": "utility", "service": "dbSNP", "version": "1.0", "genome_build": "hg19"},
)
async def convert_rsid_to_variant(rsid: str) -> str:
    try:
        if not rsid.startswith("rs"):
            rsid = f"rs{rsid}"

        url = f"https://clinicaltables.nlm.nih.gov/api/snps/v3/search"
        params = {"terms": rsid, "ef": "37.chr,37.pos,37.alleles,37.gene"}

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

        if not data or len(data) < 3:
            return json.dumps({"error": "Invalid API response format"}, indent=2)

        total_count = data[0]
        if total_count == 0:
            return json.dumps({"error": f"rsID '{rsid}' not found in dbSNP"}, indent=2)

        rsid_list = data[1]
        field_data = data[2]

        if rsid not in rsid_list:
            return json.dumps(
                {"error": f"Exact match for '{rsid}' not found", "suggestions": rsid_list[:5]},
                indent=2,
            )

        idx = rsid_list.index(rsid)

        chr_data = field_data.get("37.chr", [])
        pos_data = field_data.get("37.pos", [])
        alleles_data = field_data.get("37.alleles", [])
        gene_data = field_data.get("37.gene", [])

        if idx >= len(chr_data) or idx >= len(pos_data) or idx >= len(alleles_data):
            return json.dumps({"error": "Incomplete GRCh37 data for this rsID"}, indent=2)

        chromosome = chr_data[idx]
        position = pos_data[idx]
        alleles = alleles_data[idx]
        gene = gene_data[idx] if idx < len(gene_data) and gene_data[idx] is not None else ""

        if not chromosome or not position or not alleles:
            return json.dumps({"error": "Missing required GRCh37 coordinate data"}, indent=2)

        allele_pairs = alleles.split(",")[0].strip().split("/")
        if len(allele_pairs) < 2:
            return json.dumps({"error": f"Invalid allele format: {alleles}"}, indent=2)

        reference = allele_pairs[0].strip()
        alternate = allele_pairs[1].strip()

        variant = f"{chromosome}-{position}-{reference}-{alternate}"

        result = {
            "rsid": rsid,
            "variant": variant,
            "chr": chromosome,
            "pos": position,
            "ref": reference,
            "alt": alternate,
            "alleles": alleles,
            "gene": gene,
            "assembly": "GRCh37",
        }

        return json.dumps(result, indent=2)

    except httpx.HTTPStatusError as e:
        return json.dumps(
            {"error": f"API error: {e.response.status_code}", "message": str(e)}, indent=2
        )
    except httpx.TimeoutException:
        return json.dumps({"error": "Request timeout - API took too long to respond"}, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to convert rsID: {str(e)}"}, indent=2)


# ============================================================================
# PUBMED TOOLS
# ============================================================================


@mcp.tool(
    name="search_pubmed",
    description="Search PubMed for biomedical literature on genes, variants, diseases, or drugs with titles, abstracts, and metadata",
    meta={"category": "literature", "database": "PubMed", "version": "1.0"},
)
async def search_pubmed(
    query: str, max_results: int = 50, email: str = "marrvel@example.com"
) -> str:
    try:
        if max_results < 1 or max_results > 100:
            return json.dumps({"error": "max_results must be between 1 and 100"}, indent=2)

        pubmed = PubMed(tool="MARRVEL_MCP", email=email)

        try:
            total_count = pubmed.getTotalResultsCount(query)
        except Exception:
            total_count = "unknown"

        results = pubmed.query(query, max_results=max_results)

        articles = []
        for article in results:
            try:
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
            except Exception:
                continue

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


@mcp.tool(
    name="get_pmc_fulltext_by_pmcid",
    description="Retrieve full text of a PubMed Central (PMC) open-access article for detailed content analysis",
    meta={"category": "literature", "database": "PMC", "version": "1.0"},
)
async def get_pmc_fulltext_by_pmcid(pmcid: str) -> str:
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


@mcp.tool(
    name="pmid_to_pmcid",
    description="Convert PubMed ID (PMID) to PMC ID (PMCID) for full-text access to open-access articles",
    meta={"category": "literature", "version": "1.0"},
)
async def pmid_to_pmcid(pmid: str) -> str:
    try:
        if not pmid or not pmid.isdigit():
            return json.dumps({"pmid": pmid, "pmcid": "", "error": "Invalid PMID"}, indent=2)

        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json"
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            data = resp.json()

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


@mcp.tool(
    name="get_pubmed_article",
    description="Retrieve detailed information for a specific PubMed article by PMID with comprehensive metadata",
    meta={"category": "literature", "database": "PubMed", "version": "1.0"},
)
async def get_pubmed_article(pubmed_id: str, email: str = "zhandongliulab@bcm.edu") -> str:
    try:
        pubmed = PubMed(tool="MARRVEL_MCP", email=email)
        results = pubmed.query(pubmed_id, max_results=1)
        article = next(results, None)

        if not article:
            return json.dumps({"error": f"Article with PMID {pubmed_id} not found"}, indent=2)

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


# ============================================================================
# LIFTOVER TOOLS
# ============================================================================


@mcp.tool(
    name="liftover_hg38_to_hg19",
    description="Convert genome coordinates from hg38/GRCh38 to hg19/GRCh37 for MARRVEL tool compatibility",
    meta={"category": "liftover", "from": "hg38", "to": "hg19", "version": "1.0"},
)
async def liftover_hg38_to_hg19(chr: str, pos: int) -> str:
    try:
        endpoint = f"/liftover/hg38/chr/{chr}/pos/{pos}/hg19"
        data = await fetch_marrvel_data(endpoint)
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error fetching liftover data: {str(e)}"})


@mcp.tool(
    name="liftover_hg19_to_hg38",
    description="Convert genome coordinates from hg19/GRCh37 to hg38/GRCh38 for modern genome builds",
    meta={"category": "liftover", "from": "hg19", "to": "hg38", "version": "1.0"},
)
async def liftover_hg19_to_hg38(chr: str, pos: int) -> str:
    try:
        endpoint = f"/liftover/hg19/chr/{chr}/pos/{pos}/hg38"
        data = await fetch_marrvel_data(endpoint)
        return data
    except httpx.HTTPError as e:
        return json.dumps({"error": f"Error fetching liftover data: {str(e)}"})


# ============================================================================
# DECIPHER TOOLS
# ============================================================================


@mcp.tool(
    name="get_decipher_by_location",
    description="Query DECIPHER for control variant statistics in a genomic region for developmental disorders",
    meta={"category": "variant", "database": "DECIPHER", "version": "1.0", "genome_build": "hg19"},
)
async def get_decipher_by_location(chr: str, start: int, stop: int) -> str:
    try:
        data = await fetch_marrvel_data(f"/DECIPHER/genomloc/{chr}/{start}/{stop}")
        return data
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch data: {str(e)}"})


# ============================================================================
# ENTRY POINT
# ============================================================================


def create_server():
    """
    Return the FastMCP server instance for testing or programmatic usage.

    Returns:
        FastMCP: The configured MARRVEL MCP server instance
    """
    return mcp


if __name__ == "__main__":
    mcp.run()
