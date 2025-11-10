"""
Smoke tests for all registered MCP tools.

This test file creates an in-process MCP server using the project's
`create_server()` helper and calls each registered tool directly via the
`mcp.call_tool(name, arguments)` API. For each tool we assert the returned
payload can be interpreted as JSON (or a Python literal that can be
converted to JSON).

These are integration smoke tests and can be slow because they hit
external APIs. They are marked with the same markers used elsewhere in
the suite.
"""

import json
import os
from pathlib import Path
import pytest

# Re-use the fixture and helper from the existing integration test module


@pytest.fixture
def mcp_server():
    """Create an in-process FastMCP server instance for direct calls.

    This fixture returns the FastMCP instance created by `create_server()` so
    tests can call tools via `mcp_server.call_tool(name, arguments)` without
    going through the stdio JSON-RPC transport.
    """
    # Dynamically load server.py as a module so tests can import it reliably
    # regardless of package import paths used by pytest.
    import importlib.util
    import sys

    repo_root = None
    for p in Path(__file__).resolve().parents:
        if (p / "server.py").exists():
            repo_root = p
            break
    if repo_root is None:
        pytest.skip("Could not locate repo root containing server.py")

    server_path = repo_root / "server.py"
    spec = importlib.util.spec_from_file_location("marrvel_server", server_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["marrvel_server"] = module

    # Ensure repository root is on sys.path so imports like `src.tools` work
    repo_str = str(repo_root)
    if repo_str not in sys.path:
        sys.path.insert(0, repo_str)

    spec.loader.exec_module(module)

    mcp = module.create_server()
    return mcp


"""
Parametrized per-tool smoke tests.

Each registered tool is exercised as its own pytest case so test output
reports one line per tool. If a tool's returned payload cannot be parsed as
JSON (or a Python literal convertible to JSON), the test will fail.
"""


# List of tools to exercise and representative arguments. Keep this small
# but representative; add/remove entries as needed.
TEST_VARIANT = {"chr": "6", "pos": "98917691", "ref": "T", "alt": "C", "build": "hg38"}
tool_calls = [
    ("get_gene_by_entrez_id", {"entrez_id": "7157"}),
    ("get_gene_by_symbol", {"gene_symbol": "TP53", "taxon_id": "9606"}),
    ("get_gene_by_position", {"chromosome": "17", "position": 7565099, "taxon_id": "9606"}),
    ("get_variant_dbnsfp", TEST_VARIANT),
    ("get_variant_annotation_by_genomic_position", TEST_VARIANT),
    ("get_clinvar_by_variant", TEST_VARIANT),
    ("get_gnomad_variant", TEST_VARIANT),
    ("get_gnomad_by_entrez_id", {"entrez_id": "1080"}),
    ("get_dgv_by_entrez_id", {"entrez_id": "26235"}),
    ("get_geno2mp_by_entrez_id", {"entrez_id": "1080"}),
    ("get_clinvar_by_entrez_id", {"entrez_id": "1080"}),
    ("get_clinvar_counts_by_entrez_id", {"entrez_id": "1080"}),
    ("get_clinvar_by_gene_symbol", {"gene_symbol": "TP53"}),
    ("get_omim_by_gene_symbol", {"gene_symbol": "TP53"}),
    ("search_omim_by_disease_name", {"disease_name": "breast cancer"}),
    ("get_diopt_orthologs_by_entrez_id", {"entrez_id": "7157"}),
    ("get_ontology_across_diopt_orthologs", {"entrez_id": "7157"}),
    ("get_gtex_expression", {"entrez_id": "7157"}),
    ("convert_hgvs_to_genomic", {"hgvs_variant": "NM_000546.5:c.215C>G"}),
    ("search_pubmed", {"query": "MECP2 Rett Syndrome", "max_results": 1}),
    ("pmid_to_pmcid", {"pmid": "23251661"}),
    ("get_pmc_abstract_by_pmcid", {"pmcid": "PMC3518823"}),
    ("get_pmc_fulltext_by_pmcid", {"pmcid": "PMC3518823"}),
    ("get_pmc_tables_by_pmcid", {"pmcid": "PMC3518823"}),
    ("get_pmc_figure_captions_by_pmcid", {"pmcid": "PMC3518823"}),
    ("liftover_hg38_to_hg19", {"chr": "3", "pos": 12345}),
    ("liftover_hg19_to_hg38", {"chr": "3", "pos": 75271215}),
    ("get_decipher_by_location", {"chr": "6", "start": 99316420, "stop": 99395849}),
]


@pytest.mark.integration
@pytest.mark.integration_mcp
@pytest.mark.asyncio
@pytest.mark.parametrize("name,args", tool_calls)
async def test_tool_returns_json_or_fail(mcp_server, name, args):
    """
    Call a single tool and assert the returned payload is JSON-parseable.

    This test is parametrized so pytest shows one pass/fail line per tool.
    If the SAVE_SMOKE_TEST_OUTPUT environment variable is set, the JSON response
    for each tool will be saved to `test-output/smoke-test-json/{tool_name}.json`.
    """
    try:
        resp = await mcp_server.call_tool(name, args)
        resp = resp[-1]["result"]
    except Exception as e:
        pytest.fail(f"Tool {name} raised exception when called: {type(e).__name__}: {e}")

    assert resp is not None, f"No response for tool {name}"

    # Save output if requested
    if os.getenv("SAVE_SMOKE_TEST_OUTPUT"):
        project_root = Path(__file__).resolve().parents[3]
        output_dir = project_root / "test-output" / "smoke-test-json"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{name}.json"

        with open(output_file, "w") as f:
            f.write(resp)
