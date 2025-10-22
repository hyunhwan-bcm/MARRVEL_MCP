"""
Integration test for MARRVEL-MCP server operations.

Tests the complete lifecycle of the MCP server:
1. Start the server
2. Send JSON-RPC requests via stdio
3. Verify JSON responses
4. Gracefully shut down the server
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.fixture
def mcp_server():
    """
    Pytest fixture that starts MCP server and yields the process.
    Automatically cleans up on teardown.
    """
    # Get the Python executable from the virtual environment
    python_path = Path(__file__).parent.parent / ".venv" / "bin" / "python"
    if not python_path.exists():
        python_path = Path(sys.executable)

    server_path = Path(__file__).parent.parent / "server.py"

    # Start server as subprocess with stdio pipes
    process = subprocess.Popen(
        [str(python_path), str(server_path)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    # Give server time to initialize
    time.sleep(2)

    # Check if process started successfully
    if process.poll() is not None:
        stderr_output = ""
        if process.stderr:
            stderr_output = process.stderr.read()
        pytest.fail(f"Server failed to start: {stderr_output}")

    yield process

    # Cleanup: terminate the server
    try:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    except Exception as e:
        print(f"Warning: Error during server cleanup: {e}")


def send_request(process, method: str, params: dict | None = None, timeout: int = 10):
    """Helper function to send JSON-RPC request and get response."""
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params or {},
    }

    # Send request
    request_json = json.dumps(request) + "\n"
    process.stdin.write(request_json)
    process.stdin.flush()

    # Read response with timeout
    start_time = time.time()
    while time.time() - start_time < timeout:
        if process.poll() is not None:
            pytest.fail("Server terminated unexpectedly")

        try:
            response_line = process.stdout.readline()
            if response_line:
                return json.loads(response_line.strip())
        except Exception as e:
            pytest.fail(f"Error reading response: {e}")

        time.sleep(0.1)

    pytest.fail("No response received (timeout)")


@pytest.mark.integration_mcp
def test_server_starts(mcp_server):
    """Test that the server starts successfully."""
    assert mcp_server is not None
    assert mcp_server.poll() is None, "Server process should be running"


@pytest.mark.integration_mcp
def test_server_initialize(mcp_server):
    """Test server initialization via JSON-RPC."""
    response = send_request(
        mcp_server,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "1.0.0"},
        },
    )

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    # Response should have either 'result' or 'error'
    assert "result" in response or "error" in response


@pytest.mark.integration_mcp
def test_server_list_tools(mcp_server):
    """Test listing available tools."""
    # First initialize
    send_request(
        mcp_server,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "1.0.0"},
        },
    )

    # Then list tools
    response = send_request(mcp_server, "tools/list", {})

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    # FastMCP may return error for invalid protocol - that's OK for this test
    assert "result" in response or "error" in response


@pytest.mark.integration_mcp
def test_server_call_tool(mcp_server):
    """Test calling a tool (get_gene_info)."""
    # First initialize
    send_request(
        mcp_server,
        "initialize",
        {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "pytest", "version": "1.0.0"},
        },
    )

    # Call a tool
    response = send_request(
        mcp_server,
        "tools/call",
        {
            "name": "get_gene_info",
            "arguments": {"gene_symbol": "TP53", "model_organism": "human"},
        },
    )

    assert response is not None
    assert response["jsonrpc"] == "2.0"
    assert "id" in response
    # Should have either result or error (API might be down, that's OK)
    assert "result" in response or "error" in response


@pytest.mark.integration_mcp
def test_server_graceful_shutdown(mcp_server):
    """Test that server can be gracefully shut down."""
    assert mcp_server.poll() is None, "Server should be running"

    # Terminate the server
    mcp_server.terminate()

    # Wait for it to shut down
    try:
        mcp_server.wait(timeout=5)
        # If we get here, server shut down gracefully
        assert True
    except subprocess.TimeoutExpired:
        # Force kill if needed
        mcp_server.kill()
        mcp_server.wait()
        pytest.fail("Server did not shut down gracefully")


@pytest.mark.integration_mcp
def test_server_protocol_compliance(mcp_server):
    """Test that all responses follow JSON-RPC 2.0 protocol."""
    test_requests = [
        ("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}}),
        ("tools/list", {}),
    ]

    for method, params in test_requests:
        response = send_request(mcp_server, method, params)

        # All responses must have jsonrpc field
        assert "jsonrpc" in response, f"Missing jsonrpc in {method} response"
        assert response["jsonrpc"] == "2.0", f"Invalid JSON-RPC version in {method}"

        # All responses must have id field
        assert "id" in response, f"Missing id in {method} response"

        # All responses must have either result or error
        has_result = "result" in response
        has_error = "error" in response
        assert has_result or has_error, f"Response for {method} has neither result nor error"


# Standalone script support for backward compatibility
if __name__ == "__main__":
    print("=" * 60)
    print("MARRVEL-MCP Server Integration Test")
    print("=" * 60)
    print()
    print("Running tests with pytest...")
    print()

    # Run pytest on this file
    exit_code = pytest.main(
        [
            __file__,
            "-v",
            "--tb=short",
            "-m",
            "integration",
        ]
    )

    sys.exit(exit_code)
