#!/usr/bin/env python3
"""Generate test summary for GitHub Actions."""

import json
import sys
import xml.etree.ElementTree as ET


def generate_test_summary(json_file, coverage_file):
    """Generate markdown summary from test results."""
    output = []

    # Parse JSON test report
    if json_file:
        try:
            with open(json_file) as f:
                data = json.load(f)

            summary = data.get("summary", {})
            total = summary.get("total", 0)
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0)
            skipped = summary.get("skipped", 0)
            duration = data.get("duration", 0)

            output.append("| Metric | Value |")
            output.append("|--------|-------|")
            output.append(f"| Total Tests | {total} |")
            output.append(f"| ✅ Passed | {passed} |")
            output.append(f"| ❌ Failed | {failed} |")
            output.append(f"| ⏭️ Skipped | {skipped} |")
            output.append(f"| ⏱️ Duration | {duration:.2f}s |")
            output.append("")
        except Exception as e:
            output.append(f"⚠️ Could not parse test results: {e}")
            output.append("")

    # Parse coverage report
    if coverage_file:
        try:
            tree = ET.parse(coverage_file)
            root = tree.getroot()
            coverage = root.attrib

            line_rate = float(coverage.get("line-rate", 0)) * 100
            branch_rate = float(coverage.get("branch-rate", 0)) * 100

            output.append("### Coverage Report")
            output.append(f"- **Line Coverage:** {line_rate:.1f}%")
            output.append(f"- **Branch Coverage:** {branch_rate:.1f}%")
            output.append("")
        except Exception as e:
            output.append(f"⚠️ Could not parse coverage: {e}")
            output.append("")

    print("\n".join(output))


if __name__ == "__main__":
    json_file = sys.argv[1] if len(sys.argv) > 1 else None
    coverage_file = sys.argv[2] if len(sys.argv) > 2 else None
    generate_test_summary(json_file, coverage_file)
