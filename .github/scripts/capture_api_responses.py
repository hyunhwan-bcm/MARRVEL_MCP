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
        self,
        test_name: str,
        tool_name: str,
        input_params: Dict,
        output_json: Any,
        status: str,
        return_code: str = None,
    ):
        """Add an API response record."""
        self.responses.append(
            {
                "test_name": test_name,
                "tool_name": tool_name,
                "input": input_params,
                "output": output_json,
                "status": status,
                "return_code": return_code,
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
            "| Test Name | Tool | Input | Output Preview | # Output Keys | Return Code | Status |",
            "|-----------|------|-------|----------------|---------------|-------------|--------|",
        ]

        for resp in self.responses:
            # Show full test name (don't truncate)
            test_name = resp["test_name"]
            tool_name = resp["tool_name"]

            # Format input
            input_str = json.dumps(resp["input"])
            if len(input_str) > 50:
                input_str = input_str[:47] + "..."

            # Format output preview - show JSON only for successful calls, empty for errors
            output_preview = ""
            num_keys = "N/A"
            try:
                output_data = resp["output"]

                # If status is error or output is None, leave output preview empty
                if resp["status"] == "error" or output_data is None:
                    output_preview = ""
                    num_keys = "0"
                else:
                    # Success case - show JSON output
                    if isinstance(output_data, str):
                        try:
                            output_data = json.loads(output_data)
                        except:
                            pass

                    if isinstance(output_data, dict):
                        # Normal dict response - show key names for better visibility
                        num_keys = str(len(output_data))
                        all_keys = list(output_data.keys())

                        # Show up to first 5 keys
                        if len(all_keys) <= 5:
                            keys_preview = ", ".join(all_keys)
                            output_preview = f"{{{keys_preview}}}"
                        else:
                            # Show first 4 keys + count of remaining
                            keys_preview = ", ".join(all_keys[:4])
                            remaining = len(all_keys) - 4
                            output_preview = f"{{{keys_preview}, +{remaining} more}}"
                    elif isinstance(output_data, list):
                        num_keys = f"{len(output_data)} items"
                        # Show first few bytes of JSON
                        json_str = json.dumps(output_data, ensure_ascii=False)
                        if len(json_str) > 80:
                            output_preview = json_str[:77] + "..."
                        else:
                            output_preview = json_str
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
                f"| {test_name} | {tool_name} | `{input_str}` | {output_preview} | {num_keys} | {return_code} | {status_icon} |"
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
