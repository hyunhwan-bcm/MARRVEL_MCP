#!/usr/bin/env python3
"""
Capture and store API responses from MARRVEL tests.

This script processes test results and extracts JSON responses from API calls,
storing them in a structured format for GitHub display.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime


class APIResponseCollector:
    """Collects and formats API responses from test execution."""

    def __init__(self):
        self.responses = []

    def add_response(
        self, test_name: str, tool_name: str, input_params: Dict, output_json: Any, status: str
    ):
        """Add an API response record."""
        self.responses.append(
            {
                "test_name": test_name,
                "tool_name": tool_name,
                "input": input_params,
                "output": output_json,
                "status": status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    def save_to_json(self, filepath: str):
        """Save all responses to JSON file."""
        with open(filepath, "w") as f:
            json.dump(
                {
                    "total_responses": len(self.responses),
                    "generated_at": datetime.utcnow().isoformat(),
                    "responses": self.responses,
                },
                f,
                indent=2,
            )

    def generate_markdown_table(self) -> str:
        """Generate a markdown table of responses."""
        lines = [
            "# MARRVEL API Test Responses",
            "",
            f"**Total API Calls Captured:** {len(self.responses)}",
            f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
            "",
            "## Response Summary Table",
            "",
            "| Test Name | Tool | Input | Output Preview | Status |",
            "|-----------|------|-------|----------------|--------|",
        ]

        for resp in self.responses:
            test_name = resp["test_name"][:40]  # Truncate long names
            tool_name = resp["tool_name"]

            # Format input
            input_str = json.dumps(resp["input"])
            if len(input_str) > 50:
                input_str = input_str[:47] + "..."

            # Format output preview
            try:
                if isinstance(resp["output"], str):
                    output_data = json.loads(resp["output"])
                else:
                    output_data = resp["output"]

                # Get first key or truncate
                if isinstance(output_data, dict):
                    keys = list(output_data.keys())[:3]
                    output_preview = f"Keys: {', '.join(keys)}"
                elif isinstance(output_data, list):
                    output_preview = f"Array[{len(output_data)}]"
                else:
                    output_preview = str(output_data)[:50]
            except:
                output_preview = "N/A"

            if len(output_preview) > 50:
                output_preview = output_preview[:47] + "..."

            status_icon = "✅" if resp["status"] == "success" else "❌"

            lines.append(
                f"| {test_name} | {tool_name} | `{input_str}` | {output_preview} | {status_icon} |"
            )

        lines.extend(["", "## Detailed Responses", ""])

        # Add detailed sections for each response
        for i, resp in enumerate(self.responses, 1):
            lines.extend(
                [
                    f"### {i}. {resp['test_name']}",
                    f"**Tool:** `{resp['tool_name']}`",
                    f"**Status:** {resp['status']}",
                    "",
                    "**Input:**",
                    "```json",
                    json.dumps(resp["input"], indent=2),
                    "```",
                    "",
                    "**Output:**",
                    "```json",
                    (
                        json.dumps(resp["output"], indent=2)
                        if isinstance(resp["output"], (dict, list))
                        else resp["output"]
                    ),
                    "```",
                    "",
                    "---",
                    "",
                ]
            )

        return "\n".join(lines)

    def save_to_markdown(self, filepath: str):
        """Save responses as markdown file."""
        with open(filepath, "w") as f:
            f.write(self.generate_markdown_table())


def parse_pytest_json_report(json_file: str) -> APIResponseCollector:
    """Parse pytest JSON report and extract API responses."""
    collector = APIResponseCollector()

    try:
        with open(json_file) as f:
            data = json.load(f)

        tests = data.get("tests", [])

        for test in tests:
            test_name = test.get("nodeid", "unknown")
            outcome = test.get("outcome", "unknown")

            # Extract captured output if available
            call_info = test.get("call", {})
            stdout = call_info.get("stdout", "")

            # Look for JSON in stdout (tests should print their responses)
            # This is a placeholder - tests need to be instrumented to output JSON

            # For now, just record that the test ran
            # We'll need to modify tests to capture actual responses

        return collector

    except Exception as e:
        print(f"Error parsing JSON report: {e}", file=sys.stderr)
        return collector


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: capture_api_responses.py <pytest-json-report>")
        sys.exit(1)

    json_file = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else "api-responses.json"
    output_md = sys.argv[3] if len(sys.argv) > 3 else "api-responses.md"

    collector = parse_pytest_json_report(json_file)

    if collector.responses:
        collector.save_to_json(output_json)
        collector.save_to_markdown(output_md)
        print(f"✅ Saved {len(collector.responses)} API responses")
        print(f"   JSON: {output_json}")
        print(f"   Markdown: {output_md}")
    else:
        print("⚠️  No API responses captured")
        print("   Tests need to be instrumented to log responses")
