#!/usr/bin/env python3
"""
Aggregate and analyze benchmark results from multiple models.

This script reads test results from test_results/<model_id>/ directories,
aggregates them into summary tables (CSV and Markdown), and generates
comparison plots.

Usage:
    python analyze_results.py [TEST_RESULTS_DIR]

Output:
    - test_results/summary.csv: Detailed results per model and test
    - test_results/summary.md: Markdown table with pass rates per model
    - test_results/comparison.png: Bar chart comparing model performance
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Any
import csv

try:
    import matplotlib.pyplot as plt
    import matplotlib

    matplotlib.use("Agg")  # Use non-interactive backend
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not installed, plots will not be generated", file=sys.stderr)
    print("Install with: pip install matplotlib", file=sys.stderr)


def find_model_directories(results_dir: Path) -> List[Path]:
    """Find all model result directories.

    Args:
        results_dir: Base test_results directory

    Returns:
        List of paths to model directories (containing .completed marker)
    """
    model_dirs = []
    for item in results_dir.iterdir():
        if item.is_dir() and (item / ".completed").exists():
            model_dirs.append(item)
    return sorted(model_dirs)


def load_test_cases(model_dir: Path) -> List[Dict[str, Any]]:
    """Load test cases snapshot from a model directory.

    Args:
        model_dir: Path to model result directory

    Returns:
        List of test case dictionaries
    """
    snapshot_path = model_dir / "test_cases.yaml"
    if not snapshot_path.exists():
        return []

    import yaml

    with open(snapshot_path, "r", encoding="utf-8") as f:
        test_cases = yaml.safe_load(f)

    return test_cases if test_cases else []


def load_cached_results(model_dir: Path) -> Dict[str, Any]:
    """Load cached test results from a model directory.

    Args:
        model_dir: Path to model result directory

    Returns:
        Dictionary mapping test UUID to result data
    """
    cache_file = model_dir / "cache.json"
    if not cache_file.exists():
        return {}

    with open(cache_file, "r", encoding="utf-8") as f:
        cache_data = json.load(f)

    return cache_data


def extract_model_info(model_dir: Path) -> Dict[str, str]:
    """Extract model information from directory name and results.

    Args:
        model_dir: Path to model result directory

    Returns:
        Dictionary with model name, id, provider
    """
    model_id = model_dir.name.replace("_", "/")  # Restore slashes

    # Try to extract from cache or logs
    # For now, just use the directory name
    return {
        "name": model_dir.name,
        "id": model_id,
        "provider": "unknown",
    }


def compute_pass_rate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute pass/fail statistics for a set of results.

    Args:
        results: List of test result dictionaries

    Returns:
        Dictionary with pass/fail/error counts and pass rate
    """
    total = len(results)
    passed = sum(1 for r in results if r.get("classification", "").lower().startswith("yes"))
    failed = sum(1 for r in results if r.get("classification", "").lower().startswith("no"))
    errors = total - passed - failed

    pass_rate = (passed / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": pass_rate,
    }


def generate_csv_report(results_by_model: Dict[str, Dict], output_path: Path):
    """Generate detailed CSV report.

    Args:
        results_by_model: Dictionary mapping model_id to results data
        output_path: Path to output CSV file
    """
    with open(output_path, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)

        # Header
        writer.writerow(
            [
                "Model",
                "Test Index",
                "Test Name",
                "Question",
                "Expected",
                "Response",
                "Classification",
                "Status",
                "Tokens Used",
                "Tool Calls",
            ]
        )

        # Rows
        for model_id, data in results_by_model.items():
            model_name = data["info"]["name"]
            test_cases = data["test_cases"]
            results = data["results"]

            for i, (test_case, result) in enumerate(zip(test_cases, results)):
                test_name = test_case["case"].get("name", f"Test {i+1}")
                question = test_case["case"]["input"]
                expected = test_case["case"]["expected"]

                response = result.get("response", "")
                classification = result.get("classification", "")
                status = result.get("status", "OK")
                tokens = result.get("tokens_used", 0)
                tool_calls = len(result.get("tool_calls", []))

                writer.writerow(
                    [
                        model_name,
                        i + 1,
                        test_name,
                        question,
                        expected,
                        response,
                        classification,
                        status,
                        tokens,
                        tool_calls,
                    ]
                )

    print(f"✓ Generated CSV report: {output_path}")


def generate_markdown_report(results_by_model: Dict[str, Dict], output_path: Path):
    """Generate Markdown summary table.

    Args:
        results_by_model: Dictionary mapping model_id to results data
        output_path: Path to output Markdown file
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("# Multi-Model Benchmark Results\n\n")
        f.write(f"Total models tested: {len(results_by_model)}\n\n")

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Model | Provider | Total Tests | Passed | Failed | Errors | Pass Rate |\n")
        f.write("|-------|----------|-------------|--------|--------|--------|------------|\n")

        for model_id, data in sorted(
            results_by_model.items(), key=lambda x: x[1]["stats"]["pass_rate"], reverse=True
        ):
            info = data["info"]
            stats = data["stats"]

            f.write(
                f"| {info['name']} | {info['provider']} | "
                f"{stats['total']} | {stats['passed']} | {stats['failed']} | "
                f"{stats['errors']} | {stats['pass_rate']:.1f}% |\n"
            )

        f.write("\n")

        # Per-model details
        f.write("## Detailed Results\n\n")
        for model_id, data in results_by_model.items():
            info = data["info"]
            stats = data["stats"]

            f.write(f"### {info['name']}\n\n")
            f.write(f"- **Model ID**: `{info['id']}`\n")
            f.write(f"- **Provider**: {info['provider']}\n")
            f.write(f"- **Pass Rate**: {stats['pass_rate']:.1f}%\n")
            f.write(
                f"- **Results**: {stats['passed']} passed, {stats['failed']} failed, {stats['errors']} errors\n\n"
            )

    print(f"✓ Generated Markdown report: {output_path}")


def generate_comparison_plot(results_by_model: Dict[str, Dict], output_path: Path):
    """Generate bar chart comparing model performance.

    Args:
        results_by_model: Dictionary mapping model_id to results data
        output_path: Path to output PNG file
    """
    if not HAS_MATPLOTLIB:
        print("⚠ Skipping plot generation (matplotlib not installed)")
        return

    # Extract data for plotting
    model_names = []
    pass_rates = []

    for model_id, data in sorted(
        results_by_model.items(), key=lambda x: x[1]["stats"]["pass_rate"], reverse=True
    ):
        model_names.append(data["info"]["name"])
        pass_rates.append(data["stats"]["pass_rate"])

    # Create bar chart
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.bar(range(len(model_names)), pass_rates, color="steelblue")

    # Customize chart
    ax.set_xlabel("Model", fontsize=12)
    ax.set_ylabel("Pass Rate (%)", fontsize=12)
    ax.set_title("Multi-Model Benchmark Comparison", fontsize=14, fontweight="bold")
    ax.set_xticks(range(len(model_names)))
    ax.set_xticklabels(model_names, rotation=45, ha="right")
    ax.set_ylim(0, 100)
    ax.grid(axis="y", alpha=0.3)

    # Add value labels on bars
    for i, (bar, rate) in enumerate(zip(bars, pass_rates)):
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=10,
        )

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()

    print(f"✓ Generated comparison plot: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Aggregate and analyze multi-model benchmark results"
    )
    parser.add_argument(
        "results_dir",
        nargs="?",
        default="test_results",
        help="Directory containing model result subdirectories (default: test_results)",
    )

    args = parser.parse_args()
    results_dir = Path(args.results_dir)

    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}", file=sys.stderr)
        sys.exit(1)

    print(f"📊 Analyzing results from: {results_dir}")
    print()

    # Find all model directories
    model_dirs = find_model_directories(results_dir)

    if not model_dirs:
        print("⚠ No completed model results found", file=sys.stderr)
        sys.exit(1)

    print(f"Found {len(model_dirs)} completed model(s):")
    for d in model_dirs:
        print(f"  - {d.name}")
    print()

    # Load results for each model
    results_by_model = {}

    for model_dir in model_dirs:
        model_id = model_dir.name
        print(f"Loading results for {model_id}...")

        # Load test cases and results
        test_cases = load_test_cases(model_dir)
        cache_data = load_cached_results(model_dir)

        if not test_cases:
            print(f"  ⚠ No test cases found, skipping")
            continue

        # Extract results in test case order
        results = []
        for tc in test_cases:
            tc_uuid = tc.get("uuid", "")
            # Cache key format: <run_id>:<test_uuid>:<vanilla/web/tool>:<model_id>
            # We need to find the matching cache entry
            matching_result = None
            for cache_key, cache_value in cache_data.items():
                if tc_uuid in cache_key:
                    matching_result = cache_value
                    break

            if matching_result:
                results.append(matching_result)
            else:
                # No cached result found
                results.append(
                    {
                        "status": "NOT_FOUND",
                        "classification": "ERROR",
                        "response": "No cached result",
                        "tokens_used": 0,
                        "tool_calls": [],
                    }
                )

        # Compute statistics
        stats = compute_pass_rate(results)

        # Store aggregated data
        results_by_model[model_id] = {
            "info": extract_model_info(model_dir),
            "test_cases": test_cases,
            "results": results,
            "stats": stats,
        }

        print(f"  ✓ Loaded {len(test_cases)} test(s), pass rate: {stats['pass_rate']:.1f}%")

    print()

    if not results_by_model:
        print("⚠ No valid results to analyze", file=sys.stderr)
        sys.exit(1)

    # Generate reports
    print("Generating reports...")

    csv_path = results_dir / "summary.csv"
    generate_csv_report(results_by_model, csv_path)

    md_path = results_dir / "summary.md"
    generate_markdown_report(results_by_model, md_path)

    plot_path = results_dir / "comparison.png"
    generate_comparison_plot(results_by_model, plot_path)

    print()
    print("✓ Analysis complete!")
    print(f"  Summary CSV: {csv_path}")
    print(f"  Summary Markdown: {md_path}")
    if HAS_MATPLOTLIB:
        print(f"  Comparison plot: {plot_path}")


if __name__ == "__main__":
    main()
