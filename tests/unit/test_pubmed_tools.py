import pytest
import json
import asyncio
from src.tools import pubmed_tools


@pytest.mark.asyncio
async def test_pmid_to_pmcid_valid():
    # Example PMID with known PMC mapping
    pmid = "37741276"
    result_json = await pubmed_tools.pmid_to_pmcid(pmid)
    result = json.loads(result_json)
    assert result["pmid"] == pmid
    assert result["pmcid"].startswith("PMC")
    assert result["pmcid"] != ""
    assert "error" not in result or not result["error"]


@pytest.mark.asyncio
async def test_pmid_to_pmcid_invalid():
    # Example PMID with no PMC mapping
    pmid = "00000000"
    result_json = await pubmed_tools.pmid_to_pmcid(pmid)
    result = json.loads(result_json)
    assert result["pmid"] == pmid
    assert result["pmcid"] == ""
    assert "error" not in result or not result["error"]


@pytest.mark.asyncio
async def test_get_pmc_fulltext_by_pmcid_valid():
    pmcid = "PMC3257301"
    result_json = await pubmed_tools.get_pmc_fulltext_by_pmcid(pmcid)
    result = json.loads(result_json)
    assert result["pmcid"] == pmcid
    assert isinstance(result["fulltext"], str)
    assert len(result["fulltext"]) > 100
    assert "error" not in result or not result["error"]


@pytest.mark.asyncio
async def test_get_pmc_fulltext_by_pmcid_invalid():
    pmcid = "PMC0000000"
    result_json = await pubmed_tools.get_pmc_fulltext_by_pmcid(pmcid)
    result = json.loads(result_json)
    assert result["pmcid"] == pmcid
    assert result["fulltext"] == ""
    assert "error" in result
