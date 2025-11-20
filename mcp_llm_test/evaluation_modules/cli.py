"""
Command-line interface argument parsing.

This module handles parsing of command-line arguments and subset specifications.
"""

import argparse
from typing import List

from .cache import CACHE_DIR


def parse_subset(subset: str | None, total_count: int) -> List[int]:
    """
    Parse a subset specification string into a list of 0-based indices.

    Supported formats (1-based in the input):
    - "1-5"               -> [0,1,2,3,4]
    - "1,2,4"             -> [0,1,3]
    - "1-3,5,7-9"         -> [0,1,2,4,6,7,8]

    Rules:
    - Whitespace is ignored
    - Indices are 1-based in the input and converted to 0-based
    - Duplicates are removed; result is sorted
    - Errors:
      * index 0 -> ValueError("Index must be >= 1")
      * reversed range (e.g., 5-1) -> ValueError(f"Invalid range {start}-{end}")
      * index out of range -> ValueError(f"Index {n} out of range")
      * malformed tokens -> ValueError with message matching tests
    """
    if subset is None or subset.strip() == "":
        return list(range(total_count))

    # Remove spaces to simplify parsing
    cleaned = subset.replace(" ", "")
    indices: set[int] = set()

    # Split by comma for items that are either single indices or ranges
    tokens = [t for t in cleaned.split(",") if t != ""]
    for token in tokens:
        if "-" in token:
            # Range parsing
            parts = token.split("-")
            if len(parts) != 2 or parts[0] == "" or parts[1] == "":
                # Covers cases like "1-2-3", "-1", "1-", "-"
                raise ValueError("Invalid range format")
            start_str, end_str = parts
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError("Invalid range format")
            start = int(start_str)
            end = int(end_str)
            if start == 0 or end == 0:
                raise ValueError("Index must be >= 1")
            if start > end:
                raise ValueError(f"Invalid range {start}-{end}")
            # Validate bounds, prefer reporting the start if both are out-of-range
            if start > total_count:
                raise ValueError(f"Index {start} out of range")
            if end > total_count:
                raise ValueError(f"Index {end} out of range")
            # Convert to 0-based inclusive range
            indices.update(i - 1 for i in range(start, end + 1))
        else:
            # Single index parsing
            if not token.isdigit():
                raise ValueError("Invalid index")
            value = int(token)
            if value == 0:
                raise ValueError("Index must be >= 1")
            if value > total_count:
                raise ValueError(f"Index {value} out of range")
            indices.add(value - 1)

    return sorted(indices)


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP LLM Evaluation Script - Evaluate MCP tools with LangChain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all test cases (fresh evaluation, results saved to cache)
  python evaluate_mcp.py

  # Use cached results (re-run only failed tests)
  python evaluate_mcp.py --cache

  # Clear cache only (does not run tests)
  python evaluate_mcp.py --clear

  # Run specific test cases by index (1-based)
  python evaluate_mcp.py --subset "1-5"        # Run tests 1 through 5
  python evaluate_mcp.py --subset "1,3,5"      # Run tests 1, 3, and 5
  python evaluate_mcp.py --subset "1-3,5,7-9"  # Run tests 1-3, 5, and 7-9

  # Ask a custom question and get JSON response (no HTML)
  python evaluate_mcp.py --prompt "tell me about MECP2"
  python evaluate_mcp.py --prompt "What is the CADD score for chr1:12345 A>G?"

  # Run multi-model comparison (test multiple models across vanilla, web, MARRVEL-MCP modes)
  python evaluate_mcp.py --multi-model
  python evaluate_mcp.py --multi-model --models-config custom_models.yaml

  # Increase timeout for slow models or complex queries
  python evaluate_mcp.py --timeout 1200  # 20 minutes per test
  python evaluate_mcp.py --multi-model --timeout 900 --concurrency 2

  # Debug timeout issues (shows API call timing)
  python evaluate_mcp.py --debug-timing --timeout 1200

  # Show detailed error messages when tests fail
  python evaluate_mcp.py --verbose --multi-model
  python evaluate_mcp.py -v --multi-model  # short form

  # Or use DEBUG environment variable
  DEBUG=1 python evaluate_mcp.py --multi-model

Cache Behavior:
  Results are always cached at: {cache_dir}

  Cache is stored after every run. Use --cache to reuse successful results
  and re-run only failed tests. Without --cache, all tests are re-evaluated.
        """.format(
            cache_dir=CACHE_DIR
        ),
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the cache and exit without running evaluations. Use this to remove all cached test results.",
    )

    parser.add_argument(
        "--cache",
        action="store_true",
        help="Use cached results from previous runs. Failed test cases will be re-run. Without this flag, all tests are re-evaluated.",
    )

    parser.add_argument(
        "--resume",
        type=str,
        metavar="RUN_ID",
        help="Resume a previous run by providing its Run ID. Skips successfully completed tests.",
    )

    parser.add_argument(
        "--retry-failed",
        action="store_true",
        help="Re-run failed tests when resuming a run. If not specified, failed tests are skipped (loaded from cache).",
    )

    parser.add_argument(
        "--subset",
        type=str,
        metavar="INDICES",
        help="Run specific test cases by index. Supports ranges (1-5), individual indices (1,3,5), or combinations (1-3,5,7-9). Indices are 1-based.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        metavar="QUESTION",
        help="Ask a custom question directly and get JSON response without HTML report. Example: --prompt 'tell me about MECP2'",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        metavar="N",
        help="Maximum number of concurrent test executions (default: 4 for most providers, 1 for Bedrock). "
        "Bedrock has strict rate limits and connection pool constraints (max 10 connections). "
        "Increase for faster execution if API rate limits allow, but be cautious with Bedrock.",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        metavar="SECONDS",
        help="Timeout per test case in seconds (default: 600 = 10 minutes). "
        "Increase this if you have complex queries or slow models that need more time.",
    )

    parser.add_argument(
        "--debug-timing",
        action="store_true",
        help="Enable debug logging to show API call timing and help diagnose timeout issues. "
        "Can also use DEBUG=1 environment variable.",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed error messages and test execution information. "
        "Useful for troubleshooting when tests are failing.",
    )

    parser.add_argument(
        "--with-vanilla",
        action="store_true",
        help="Run tests in both vanilla mode (without tool calling) and with tool calling, then combine results for comparison.",
    )

    parser.add_argument(
        "--with-web",
        action="store_true",
        help="Run tests in three modes: vanilla (no tools, no web), web search (:online suffix), and MARRVEL-MCP (with tools). Creates 3-way comparison.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        metavar="PATH",
        help="Directory to save test results (CSV, cache, HTML report). Defaults to test-output/<timestamp>",
    )

    parser.add_argument(
        "--api-key",
        type=str,
        metavar="KEY",
        help="Per-run API key override (preferred over environment OPENAI_API_KEY / OPENROUTER_API_KEY).",
    )

    parser.add_argument(
        "--api-base",
        type=str,
        metavar="URL",
        help="Per-run API base override (e.g. https://openrouter.ai/api/v1). Does not modify environment.",
    )

    parser.add_argument(
        "--provider",
        type=str,
        metavar="NAME",
        help="Override provider for this run (allowed: openrouter, openai, bedrock).",
    )

    parser.add_argument(
        "--model",
        type=str,
        metavar="MODEL_ID",
        help="Override model for this run (e.g. meta-llama/llama-3.1-8b-instruct, gpt-4o).",
    )

    return parser.parse_args()
