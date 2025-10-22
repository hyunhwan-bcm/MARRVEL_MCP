"""
Pytest plugin to capture MARRVEL API responses during test execution.

This plugin intercepts API calls and stores the responses for later analysis.
"""

import json
import pytest
from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime


class APIResponseLogger:
    """Logger for capturing API call responses during tests."""

    def __init__(self):
        self.responses: List[Dict[str, Any]] = []
        self.current_test = None

    def log_api_call(
        self,
        tool_name: str,
        endpoint: str,
        input_params: Dict[str, Any],
        response_data: Any,
        status: str = "success",
        error: str = None,
    ):
        """Log an API call and its response."""
        record = {
            "test_name": self.current_test or "unknown",
            "tool_name": tool_name,
            "endpoint": endpoint,
            "input": input_params,
            "output": response_data,
            "status": status,
            "error": error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.responses.append(record)

    def save_to_file(self, filepath: str):
        """Save all logged responses to a JSON file."""
        output = {
            "total_api_calls": len(self.responses),
            "generated_at": datetime.utcnow().isoformat(),
            "api_calls": self.responses,
        }

        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

        return filepath


# Global logger instance
api_logger = APIResponseLogger()


@pytest.fixture(scope="function", autouse=True)
def capture_api_responses(request):
    """Fixture to capture API responses for each test."""
    # Set current test name
    api_logger.current_test = request.node.nodeid

    yield api_logger

    # Reset after test
    api_logger.current_test = None


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    """Configure the plugin."""
    config.api_response_logger = api_logger


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    """Save all captured API responses at the end of the test session."""
    if api_logger.responses:
        output_dir = Path("test-output")
        output_dir.mkdir(exist_ok=True)

        filepath = output_dir / "api_responses.json"
        api_logger.save_to_file(str(filepath))

        print(f"\n✅ Captured {len(api_logger.responses)} API responses")
        print(f"   Saved to: {filepath}")


def get_api_logger():
    """Get the global API logger instance."""
    return api_logger
