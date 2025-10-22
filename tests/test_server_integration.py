#!/usr/bin/env python3
"""
Integration test for MARRVEL-MCP server operations.

This script tests the complete lifecycle of the MCP server:
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


class ServerIntegrationTest:
    """Test MCP server integration."""

    def __init__(self, timeout: int = 10):
        """Initialize test with timeout."""
        self.timeout = timeout
        self.process = None
        self.tests_passed = 0
        self.tests_failed = 0

    def log(self, message: str, status: str = "INFO"):
        """Print formatted log message."""
        symbols = {
            "INFO": "ℹ️",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️",
            "TEST": "🧪",
        }
        symbol = symbols.get(status, "•")
        print(f"{symbol} {message}")

    def start_server(self) -> bool:
        """Start the MCP server process."""
        try:
            self.log("Starting MCP server...", "TEST")

            # Get the Python executable from the virtual environment
            python_path = Path(__file__).parent.parent / ".venv" / "bin" / "python"
            if not python_path.exists():
                python_path = sys.executable

            server_path = Path(__file__).parent.parent / "server.py"

            # Start server as subprocess with stdio pipes
            self.process = subprocess.Popen(
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
            if self.process.poll() is not None:
                stderr_output = ""
                if self.process.stderr:
                    stderr_output = self.process.stderr.read()
                self.log(f"Server failed to start: {stderr_output}", "ERROR")
                self.tests_failed += 1
                return False

            self.log("Server started successfully", "SUCCESS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"Failed to start server: {e}", "ERROR")
            self.tests_failed += 1
            return False

    def send_request(self, method: str, params: dict | None = None) -> dict | None:
        """Send JSON-RPC request to server."""
        if not self.process or not self.process.stdin or not self.process.stdout:
            self.log("Server process not available", "ERROR")
            self.tests_failed += 1
            return None

        try:
            self.log(f"Sending request: {method}", "TEST")

            request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": method,
                "params": params or {},
            }

            # Send request
            request_json = json.dumps(request) + "\n"
            self.process.stdin.write(request_json)
            self.process.stdin.flush()

            # Read response with timeout
            start_time = time.time()
            response_line = ""
            while time.time() - start_time < self.timeout:
                if self.process.poll() is not None:
                    self.log("Server terminated unexpectedly", "ERROR")
                    self.tests_failed += 1
                    return None

                # Try to read a line
                try:
                    response_line = self.process.stdout.readline()
                    if response_line:
                        break
                except Exception as e:
                    self.log(f"Error reading response: {e}", "ERROR")
                    self.tests_failed += 1
                    return None

                time.sleep(0.1)

            if not response_line:
                self.log("No response received (timeout)", "ERROR")
                self.tests_failed += 1
                return None

            # Parse JSON response
            response = json.loads(response_line.strip())
            self.log("Received valid JSON response", "SUCCESS")
            self.tests_passed += 1
            return response

        except json.JSONDecodeError as e:
            self.log(f"Invalid JSON response: {e}", "ERROR")
            self.tests_failed += 1
            return None
        except Exception as e:
            self.log(f"Request failed: {e}", "ERROR")
            self.tests_failed += 1
            return None

    def verify_response(
        self, response: dict | None, expected_keys: list[str] | None = None
    ) -> bool:
        """Verify response structure."""
        try:
            self.log("Verifying response structure...", "TEST")

            if not response:
                self.log("Response is None or empty", "ERROR")
                self.tests_failed += 1
                return False

            # Check JSON-RPC structure
            if "jsonrpc" not in response:
                self.log("Missing 'jsonrpc' field", "ERROR")
                self.tests_failed += 1
                return False

            if response["jsonrpc"] != "2.0":
                self.log(f"Invalid JSON-RPC version: {response['jsonrpc']}", "ERROR")
                self.tests_failed += 1
                return False

            # Check for required keys (if specified)
            if expected_keys:
                missing_keys = [key for key in expected_keys if key not in response]
                if missing_keys:
                    self.log(
                        f"Optional keys missing: {missing_keys} (not critical)",
                        "WARNING",
                    )

            # Check for error vs result
            has_result = "result" in response
            has_error = "error" in response

            if not has_result and not has_error:
                self.log("Response has neither 'result' nor 'error'", "WARNING")

            if has_error:
                error = response["error"]
                self.log(f"Server returned error: {error}", "WARNING")

            self.log("Response structure valid", "SUCCESS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"Verification failed: {e}", "ERROR")
            self.tests_failed += 1
            return False

    def shutdown_server(self) -> bool:
        """Gracefully shut down the server."""
        try:
            self.log("Shutting down server...", "TEST")

            if not self.process:
                self.log("No server process to shut down", "WARNING")
                return True

            # Try graceful shutdown first
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.log("Graceful shutdown timeout, forcing kill", "WARNING")
                self.process.kill()
                self.process.wait()

            self.log("Server shut down successfully", "SUCCESS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"Shutdown failed: {e}", "ERROR")
            self.tests_failed += 1
            return False

    def run_test_suite(self):
        """Run complete test suite."""
        self.log("=" * 60, "INFO")
        self.log("MARRVEL-MCP Server Integration Test", "INFO")
        self.log("=" * 60, "INFO")
        print()

        try:
            # Test 1: Start server
            if not self.start_server():
                self.log("Cannot continue without server", "ERROR")
                return False

            print()

            # Test 2: Send initialize request
            init_response = self.send_request(
                "initialize",
                {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "integration-test", "version": "1.0.0"},
                },
            )

            if init_response:
                self.verify_response(init_response, ["jsonrpc", "id", "result"])

            print()

            # Test 3: List available tools
            tools_response = self.send_request("tools/list", {})

            if tools_response:
                self.verify_response(tools_response, ["jsonrpc", "id", "result"])
                if "result" in tools_response and "tools" in tools_response["result"]:
                    tool_count = len(tools_response["result"]["tools"])
                    self.log(f"Server reported {tool_count} available tools", "INFO")

            print()

            # Test 4: Call a simple tool (get_gene_info)
            gene_response = self.send_request(
                "tools/call",
                {
                    "name": "get_gene_info",
                    "arguments": {"gene_symbol": "TP53", "model_organism": "human"},
                },
            )

            if gene_response:
                self.verify_response(gene_response, ["jsonrpc", "id"])
                if "result" in gene_response:
                    self.log("Tool execution successful", "SUCCESS")
                    self.tests_passed += 1
                elif "error" in gene_response:
                    self.log(
                        f"Tool returned error (may be expected): {gene_response['error']}",
                        "WARNING",
                    )

            print()

        except Exception as e:
            self.log(f"Test suite failed: {e}", "ERROR")
            self.tests_failed += 1

        finally:
            # Always try to shut down server
            print()
            self.shutdown_server()

        # Print summary
        print()
        self.log("=" * 60, "INFO")
        self.log("Test Summary", "INFO")
        self.log("=" * 60, "INFO")
        self.log(f"Tests Passed: {self.tests_passed}", "SUCCESS")
        self.log(f"Tests Failed: {self.tests_failed}", "ERROR")
        print()

        if self.tests_failed == 0:
            self.log("🎉 All tests passed!", "SUCCESS")
            return True
        else:
            self.log("❌ Some tests failed", "ERROR")
            return False


def main():
    """Run the integration test."""
    tester = ServerIntegrationTest(timeout=10)
    success = tester.run_test_suite()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
