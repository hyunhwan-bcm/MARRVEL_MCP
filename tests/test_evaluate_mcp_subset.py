"""
Integration tests for evaluate_mcp.py --subset parameter.

Tests that the script correctly filters test cases based on the --subset argument.
"""

import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

# Set dummy API key to avoid import error
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_testing"

# Add project root to path to import evaluate_mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))


def test_subset_argument_filters_test_cases():
    """Test that --subset argument correctly filters test cases."""
    from evaluate_mcp import parse_subset

    # Load actual test cases to get the count
    test_cases_path = Path(__file__).parent.parent / "mcp_llm_test" / "test_cases.yaml"
    with open(test_cases_path, "r") as f:
        test_cases = yaml.safe_load(f)

    total_count = len(test_cases)

    # Test that subset "1-5" returns indices for the first 5 test cases
    subset_indices = parse_subset("1-5", total_count)
    assert len(subset_indices) == 5
    assert subset_indices == [0, 1, 2, 3, 4]

    # Test that subset "1,3,5" returns specific indices
    subset_indices = parse_subset("1,3,5", total_count)
    assert len(subset_indices) == 3
    assert subset_indices == [0, 2, 4]

    # Test that no subset returns all test cases
    subset_indices = parse_subset("", total_count)
    assert len(subset_indices) == total_count


def test_subset_with_invalid_index_fails():
    """Test that invalid subset indices raise appropriate errors."""
    from evaluate_mcp import parse_subset

    # Load actual test cases to get the count
    test_cases_path = Path(__file__).parent.parent / "mcp_llm_test" / "test_cases.yaml"
    with open(test_cases_path, "r") as f:
        test_cases = yaml.safe_load(f)

    total_count = len(test_cases)

    # Test that index beyond total_count raises error
    with pytest.raises(ValueError, match=f"Index {total_count + 1} out of range"):
        parse_subset(f"{total_count + 1}", total_count)

    # Test that index 0 raises error
    with pytest.raises(ValueError, match="Index must be >= 1"):
        parse_subset("0", total_count)


def test_load_test_cases_file_exists():
    """Verify that the test_cases.yaml file exists and can be loaded."""
    test_cases_path = Path(__file__).parent.parent / "mcp_llm_test" / "test_cases.yaml"
    assert test_cases_path.exists(), f"Test cases file not found at {test_cases_path}"

    with open(test_cases_path, "r") as f:
        test_cases = yaml.safe_load(f)

    assert isinstance(test_cases, list)
    assert len(test_cases) > 0

    # Verify structure of first test case
    first_case = test_cases[0]
    assert "case" in first_case
    assert "name" in first_case["case"]
    assert "input" in first_case["case"]
    assert "expected" in first_case["case"]
