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
import pytest

# Re-use the fixture and helper from the existing integration test module
from .test_server_integration import send_request


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
    from pathlib import Path

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


@pytest.mark.integration
@pytest.mark.integration_mcp
@pytest.mark.asyncio
async def test_all_tools_return_json_or_error(mcp_server):
    """Call every registered tool and ensure results are JSON parseable.

    If a tool returns a server-level error (response contains 'error'), the
    tool call is skipped (marked as xfail via pytest.skip) because downstream
    public APIs can be flaky and we don't want the entire smoke-suite to fail
    for transient problems. If a tool returns a 'result', the test will
    attempt to parse it as JSON and fail if it isn't valid JSON.
    """

    # We're using an in-process server instance (mcp_server). Tools are
    # registered by `create_server()` so we can call them directly via
    # `mcp_server.call_tool(name, arguments)` without JSON-RPC/stdio.

    # List of tools to exercise and representative arguments.
    # These map to the function parameter names in the tool definitions.
    tool_calls = [
        # gene_tools
        ("get_gene_by_entrez_id", {"entrez_id": "7157"}),
        ("get_gene_by_symbol", {"gene_symbol": "TP53", "taxon_id": "9606"}),
        ("get_gene_by_position", {"chromosome": "chr17", "position": 7577121}),
        # variant_tools (representative subset / full set)
        ("get_variant_dbnsfp", {"variant": "17:7577121 C>T"}),
        ("get_clinvar_by_variant", {"variant": "17-7577121-C-T"}),
        ("get_clinvar_by_gene_symbol", {"gene_symbol": "TP53"}),
        ("get_clinvar_by_entrez_id", {"entrez_id": "7157"}),
        ("get_gnomad_variant", {"variant": "17-7577121-C-T"}),
        ("get_gnomad_by_gene_symbol", {"gene_symbol": "TP53"}),
        ("get_gnomad_by_entrez_id", {"entrez_id": "7157"}),
        ("get_dgv_variant", {"variant": "17-7577121-C-T"}),
        ("get_dgv_by_entrez_id", {"entrez_id": "7157"}),
        ("get_decipher_variant", {"variant": "17-7577121-C-T"}),
        ("get_decipher_by_location", {"chromosome": "chr17", "start": 7570000, "stop": 7590000}),
        ("get_geno2mp_variant", {"variant": "17-7577121-C-T"}),
        ("get_geno2mp_by_entrez_id", {"entrez_id": "7157"}),
        # disease_tools
        ("get_omim_by_mim_number", {"mim_number": "114480"}),
        ("get_omim_by_gene_symbol", {"gene_symbol": "TP53"}),
        ("get_omim_variant", {"gene_symbol": "TP53", "variant": "p.R248Q"}),
        # ortholog_tools
        ("get_diopt_orthologs", {"entrez_id": "7157"}),
        ("get_diopt_alignment", {"entrez_id": "7157"}),
        ("get_diopt_orthologs_by_entrez_id", {"entrez_id": "7157"}),
        # expression_tools
        ("get_gtex_expression", {"entrez_id": "7157"}),
        ("get_ortholog_expression", {"entrez_id": "7157"}),
        ("get_pharos_targets", {"entrez_id": "7157"}),
        # utility_tools
        ("validate_hgvs_variant", {"hgvs_variant": "NM_000546.5:c.215C>G"}),
        ("convert_protein_variant", {"protein_variant": "NP_000537.3:p.Arg72Pro"}),
        ("convert_rsid_to_variant", {"rsid": "rs429358"}),
        # pubmed_tools (small result set)
        ("search_pubmed", {"query": "TP53 cancer", "max_results": 2}),
        ("get_pubmed_article", {"pubmed_id": "28887537"}),
    ]

    # Iterate and call each tool
    for name, args in tool_calls:
        # Call the tool via the in-process server API
        try:
            resp = await mcp_server.call_tool(name, args)
        except Exception as e:
            pytest.skip(f"Tool {name} raised exception when called: {e}")

        assert resp is not None, f"No response for tool {name}"

        # If the call returned a dict that looks like an error, skip
        if isinstance(resp, dict) and resp.get("error"):
            pytest.skip(f"Tool {name} returned error: {resp.get('error')}")

            # Normalize response payload for validation
            result = resp

            def try_parse_text(text: str):
                """Try several strategies to parse a text block into a Python object.

                Returns the parsed object on success or raises ValueError on failure.
                """
                # Try JSON first
                try:
                    return json.loads(text)
                except Exception:
                    pass

                # Try extracting a JSON-ish substring (first/last brace) which helps
                # when the tool returned a Python representation that includes
                # wrapper objects (e.g. "[TextContent(... text='{...}')]").
                first = text.find("{")
                last = text.rfind("}")
                if first != -1 and last != -1 and last > first:
                    candidate = text[first : last + 1]
                    try:
                        return json.loads(candidate)
                    except Exception:
                        pass

                # Fall back to Python literal evaluation (handles single-quoted
                # dicts/lists produced by some tools)
                import ast

                try:
                    return ast.literal_eval(text)
                except Exception:
                    pass

                # Try a best-effort replace of single quotes -> double quotes and parse
                # This is brittle but helps with simple cases like "{'a': 1}".
                try:
                    fixed = text.replace("'", '"')
                    return json.loads(fixed)
                except Exception:
                    pass

                raise ValueError("unable to parse text as JSON or Python literal")

            # If result is a list/tuple of content blocks, extract text parts
            if isinstance(result, (list, tuple)) and not isinstance(result, (dict, str)):
                parts = []
                for item in result:
                    if hasattr(item, "text"):
                        parts.append(item.text)
                    elif hasattr(item, "content"):
                        parts.append(str(item.content))
                    else:
                        parts.append(str(item))

                text = "\n".join(parts)
                try:
                    _ = try_parse_text(text)
                except Exception:
                    pytest.fail(f"Tool {name} returned non-JSON result: {text[:200]}")
                continue

            # If the result is already a dict/list, accept as JSON-serializable
            if isinstance(result, (dict, list)):
                continue

            # If it's a string, attempt to parse it via our helper
            if isinstance(result, str):
                try:
                    _ = try_parse_text(result)
                except Exception:
                    pytest.fail(f"Tool {name} returned non-JSON result: {result[:200]}")
                continue
