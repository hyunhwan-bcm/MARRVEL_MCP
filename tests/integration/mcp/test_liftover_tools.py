import pytest
import json
import importlib
import asyncio


@pytest.fixture(scope="module")
def mcp_server():
    server_module = importlib.import_module("server")
    mcp = server_module.create_server()
    return mcp


@pytest.mark.integration_mcp
@pytest.mark.asyncio
@pytest.mark.parametrize(
    "chr,pos,expected_key",
    [
        ("3", 12345, "hg19Chr"),
        ("3", 75271215, "hg38Chr"),
    ],
)
async def test_liftover_tools(mcp_server, chr, pos, expected_key):
    if expected_key == "hg19Chr":
        result = await mcp_server.call_tool("liftover_hg38_to_hg19", {"chr": chr, "pos": pos})
    else:
        result = await mcp_server.call_tool("liftover_hg19_to_hg38", {"chr": chr, "pos": pos})
    try:
        data = json.loads(result)
    except Exception:
        pytest.fail(f"Returned value is not valid JSON: {result}")
    assert expected_key in data, f"Expected key '{expected_key}' not found in result: {data}"
    assert data[expected_key] == chr, f"Expected chromosome '{chr}' in result: {data}"
    assert isinstance(
        data.get(f"{expected_key[:-3]}Pos", None), int
    ), f"Expected integer position in result: {data}"
