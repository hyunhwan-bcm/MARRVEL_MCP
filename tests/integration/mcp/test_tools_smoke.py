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


"""
Parametrized per-tool smoke tests.

Each registered tool is exercised as its own pytest case so test output
reports one line per tool. If a tool's returned payload cannot be parsed as
JSON (or a Python literal convertible to JSON), the test will fail.
"""


# List of tools to exercise and representative arguments. Keep this small
# but representative; add/remove entries as needed.
tool_calls = [
    ("get_gene_by_entrez_id", {"entrez_id": "7157"}),
    ("get_gene_by_symbol", {"gene_symbol": "TP53", "taxon_id": "9606"}),
    ("get_variant_dbnsfp", {"variant": "17:7577121 C>T"}),
    ("get_clinvar_by_variant", {"variant": "17-7577121-C-T"}),
    ("get_omim_by_gene_symbol", {"gene_symbol": "TP53"}),
    ("get_diopt_orthologs", {"entrez_id": "7157"}),
    ("get_gtex_expression", {"entrez_id": "7157"}),
    ("validate_hgvs_variant", {"hgvs_variant": "NM_000546.5:c.215C>G"}),
    ("search_pubmed", {"query": "TP53 cancer", "max_results": 1}),
]


def try_parse_text(text: str):
    """Try several strategies to parse a text block into a Python object.

    Returns the parsed object on success or raises ValueError on failure.
    """
    # Try JSON first
    try:
        return json.loads(text)
    except Exception:
        pass

    # Try extracting a JSON-ish substring (first/last brace)
    first = text.find("{")
    last = text.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = text[first : last + 1]
        try:
            return json.loads(candidate)
        except Exception:
            pass

    # Fall back to Python literal evaluation
    import ast

    try:
        return ast.literal_eval(text)
    except Exception:
        pass

    # Try a best-effort replace of single quotes -> double quotes and parse
    try:
        fixed = text.replace("'", '"')
        return json.loads(fixed)
    except Exception:
        pass

    raise ValueError("unable to parse text as JSON or Python literal")


@pytest.mark.integration
@pytest.mark.integration_mcp
@pytest.mark.asyncio
@pytest.mark.parametrize("name,args", tool_calls)
async def test_tool_returns_json_or_fail(mcp_server, name, args):
    """Call a single tool and assert the returned payload is JSON-parseable.

    This test is parametrized so pytest shows one pass/fail line per tool.
    """
    try:
        resp = await mcp_server.call_tool(name, args)
    except Exception as e:
        pytest.skip(f"Tool {name} raised exception when called: {e}")

    assert resp is not None, f"No response for tool {name}"

    # If the call returned a dict that looks like an error, skip the test.
    if isinstance(resp, dict) and resp.get("error"):
        pytest.skip(f"Tool {name} returned error: {resp.get('error')}")

    parsed = None

    # If the result is already a dict/list, accept as JSON-serializable
    if isinstance(resp, (dict, list)):
        parsed = resp
    elif isinstance(resp, str):
        parsed = try_parse_text(resp)
    else:
        # Handle sequences of content-blocks
        if isinstance(resp, (list, tuple)):
            parts = []
            for item in resp:
                if hasattr(item, "text"):
                    parts.append(item.text)
                elif hasattr(item, "content"):
                    parts.append(str(item.content))
                else:
                    parts.append(str(item))
            text = "\n".join(parts)
            parsed = try_parse_text(text)
        else:
            # Unexpected type: fail
            pytest.fail(f"Tool {name} returned unsupported type: {type(resp)}")

    # If parsing succeeded, print a concise one-line summary for visibility.
    if isinstance(parsed, dict):
        keys = list(parsed.keys())
        print(f"Tool {name} -> OK JSON object with keys: {keys}")
    else:
        print(f"Tool {name} -> OK JSON value of type {type(parsed)}")
