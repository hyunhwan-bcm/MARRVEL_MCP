"""
Pytest configuration and fixtures for MARRVEL-MCP tests.

This module provides:
- SSL certificate verification check for integration tests
- Custom pytest markers for test categorization
- Shared fixtures
- API response capture for logging and analysis
"""

import pytest
import ssl
import certifi
import httpx
import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


# Global storage for API responses
_api_responses = []


class APIResponseCapture:
    """Captures API responses during test execution."""

    def __init__(self, test_name: str):
        self.test_name = test_name
        self.responses = []

    def log_response(
        self,
        tool_name: str,
        endpoint: str,
        input_data: Dict[str, Any],
        output_data: Any,
        status: str = "success",
        error: Optional[str] = None,
        return_code: Optional[str] = None,
    ):
        """Log an API response."""
        global _api_responses

        record = {
            "test_name": self.test_name,
            "tool_name": tool_name,
            "endpoint": endpoint,
            "input": input_data,
            "output": output_data,
            "status": status,
            "error": error,
            "return_code": return_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        self.responses.append(record)
        _api_responses.append(record)


@pytest.fixture
def api_capture(request):
    """Fixture to capture API responses during tests."""
    capture = APIResponseCapture(request.node.nodeid)
    yield capture


def pytest_sessionfinish(session, exitstatus):
    """Save captured API responses at end of test session."""
    global _api_responses

    if _api_responses:
        output_dir = Path("test-output")
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / "api_responses.json"

        output = {
            "total_api_calls": len(_api_responses),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "test_session": {
                "exit_status": exitstatus,
            },
            "api_calls": _api_responses,
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        # Also save markdown version
        md_filepath = output_dir / "api_responses.md"
        with open(md_filepath, "w") as f:
            f.write(_generate_markdown_table(_api_responses))

        print(f"\n✅ Captured {len(_api_responses)} API responses")
        print(f"   JSON: {filepath}")
        print(f"   Markdown: {md_filepath}")


def _generate_markdown_table(responses: List[Dict[str, Any]]) -> str:
    """Generate markdown table from API responses."""
    from config import API_BASE_URL

    lines = [
        "# MARRVEL API Test Responses",
        "",
        f"**Total API Calls:** {len(responses)}",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        "",
        "## Summary Table",
        "",
        "| Test Name | Tool | Endpoint | Input | Output Preview | # Output Keys | Return Code | Status |",
        "|-----------|------|----------|-------|----------------|---------------|-------------|--------|",
    ]

    for resp in responses:
        # Show full test name (don't truncate)
        test_name = resp["test_name"].split("::")[-1]  # Get last part of test path
        tool = resp["tool_name"]
        endpoint = resp["endpoint"]

        # Make endpoint a clickable link to MARRVEL API
        endpoint_link = f"[{endpoint}]({API_BASE_URL}{endpoint})"

        # Format input
        input_str = str(resp["input"])
        if len(input_str) > 40:
            input_str = input_str[:37] + "..."

        # Format output preview - show JSON only for successful calls, empty for errors
        output_preview = ""
        num_keys = "N/A"
        try:
            output_data = resp["output"]

            # If there's no output, leave preview empty
            if output_data is None:
                output_preview = ""
                num_keys = "0"
            else:
                # If output is a JSON string, attempt to parse it
                if isinstance(output_data, str):
                    try:
                        output_data = json.loads(output_data)
                    except Exception:
                        # leave as string
                        pass

                # Handle dict responses
                if isinstance(output_data, dict):
                    # If this is a structured error with 'content', show sanitized preview
                    if (
                        "error" in output_data
                        and "content" in output_data
                        and output_data.get("content")
                    ):
                        error_msg = output_data.get("error", "")
                        status_code = output_data.get("status_code", "N/A")
                        content_preview = output_data.get("content", "")
                        # Decide whether to show content preview: only for 200 (HTML pages)
                        # or server errors (>=500). Hide for common client errors like 404.
                        try:
                            sc_int = int(status_code)
                        except Exception:
                            sc_int = None

                        show_content = sc_int == 200 or (sc_int is not None and sc_int >= 500)
                        if show_content:
                            # Sanitize and truncate content to keep table safe
                            import re

                            content_preview = (
                                content_preview.replace("\n", " ")
                                .replace("\r", " ")
                                .replace("\t", " ")
                            )
                            content_preview = re.sub(r"\s+", " ", content_preview).strip()
                            if len(content_preview) > 50:
                                content_preview = content_preview[:50]
                            output_preview = (
                                f'❌ {error_msg} (HTTP {status_code}): "{content_preview}"'
                            )
                        else:
                            # Hide content preview for other status codes (e.g., 404)
                            output_preview = ""
                        num_keys = str(len(output_data))
                    elif resp.get("status") == "error":
                        # Generic error with no content - hide preview
                        output_preview = ""
                        num_keys = "0"
                    elif "error" in output_data:
                        # Generic error object (no content)
                        error_msg = output_data.get("error", "Unknown error")
                        output_preview = f"❌ Error: {error_msg}"
                        num_keys = str(len(output_data))
                    else:
                        # Normal dict response - show key names for better visibility
                        num_keys = str(len(output_data))
                        all_keys = list(output_data.keys())
                        if len(all_keys) <= 5:
                            keys_preview = ", ".join(all_keys)
                            output_preview = f"{{{keys_preview}}}"
                        else:
                            keys_preview = ", ".join(all_keys[:4])
                            remaining = len(all_keys) - 4
                            output_preview = f"{{{keys_preview}, +{remaining} more}}"

                elif isinstance(output_data, list):
                    num_keys = f"{len(output_data)} items"
                    json_str = json.dumps(output_data, ensure_ascii=False)
                    output_preview = json_str[:77] + "..." if len(json_str) > 80 else json_str
                else:
                    output_preview = str(output_data)[:80]
                    num_keys = "1"
        except Exception:
            # On display error, leave output empty to avoid breaking table
            output_preview = ""
            num_keys = "N/A"

        # Get return code
        return_code = resp.get("return_code", "N/A")
        if return_code is None:
            return_code = "N/A"

        status_icon = "✅" if resp["status"] == "success" else "❌"

        lines.append(
            f"| {test_name} | {tool} | {endpoint_link} | `{input_str}` | {output_preview} | {num_keys} | {return_code} | {status_icon} |"
        )

    return "\n".join(lines)


def pytest_configure(config):
    """Configure custom pytest markers for test categorization."""
    config.addinivalue_line(
        "markers", "unit: Unit tests with mocked dependencies (fast, no network)"
    )
    config.addinivalue_line(
        "markers",
        "integration_api: Integration tests that call real MARRVEL API (requires network)",
    )
    config.addinivalue_line(
        "markers",
        "integration_mcp: Integration tests that run MCP server (requires server startup)",
    )


def check_ssl_configuration() -> bool:
    """
    Check if SSL certificates are properly configured.

    Attempts to verify SSL configuration by creating an SSL context
    and checking if certifi's CA bundle is accessible.

    Returns:
        bool: True if SSL is properly configured, False otherwise
    """
    try:
        # Check if certifi can locate the CA bundle
        ca_bundle = certifi.where()
        if not ca_bundle:
            return False

        # Try to create an SSL context
        ssl_context = ssl.create_default_context(cafile=ca_bundle)
        return True
    except (ssl.SSLError, OSError, Exception):
        return False


def check_network_connectivity() -> bool:
    """
    Check if network connectivity to MARRVEL API is available.

    Returns:
        bool: True if network is accessible, False otherwise
    """
    try:
        # Simple check - just attempt to resolve the domain
        import socket

        socket.gethostbyname("marrvel.org")
        return True
    except Exception:
        return False


# Marker for skipping tests when SSL is not properly configured
skip_if_ssl_broken = pytest.mark.skipif(
    not check_ssl_configuration(),
    reason="SSL certificates not properly configured. " "Run: pip install --upgrade certifi",
)

# Marker for skipping tests when network is unavailable
skip_if_no_network = pytest.mark.skipif(
    not check_network_connectivity(),
    reason="Network connectivity to MARRVEL API unavailable",
)
