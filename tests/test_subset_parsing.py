"""
Unit tests for subset parsing functionality in evaluate_mcp.py

Tests the parse_subset function which handles:
- Range specifications (e.g., "1-5")
- Individual indices (e.g., "1,2,4")
- Combination of both (e.g., "1-3,5,7-9")
"""

import os
import sys
from pathlib import Path

import pytest

# Set dummy API key to avoid import error
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_testing"

# Add project root to path to import evaluate_mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))

from evaluate_mcp import parse_subset


def test_parse_subset_single_range():
    """Test parsing a single range like '1-5'."""
    result = parse_subset("1-5", 10)
    assert result == [0, 1, 2, 3, 4]  # 0-based indices


def test_parse_subset_individual_indices():
    """Test parsing individual indices like '1,2,4'."""
    result = parse_subset("1,2,4", 10)
    assert result == [0, 1, 3]  # 0-based indices


def test_parse_subset_combination():
    """Test parsing combination of ranges and indices like '1-3,5,7-9'."""
    result = parse_subset("1-3,5,7-9", 10)
    assert result == [0, 1, 2, 4, 6, 7, 8]  # 0-based indices


def test_parse_subset_single_index():
    """Test parsing a single index like '3'."""
    result = parse_subset("3", 10)
    assert result == [2]  # 0-based index


def test_parse_subset_empty_string():
    """Test that empty string returns all indices."""
    result = parse_subset("", 5)
    assert result == [0, 1, 2, 3, 4]


def test_parse_subset_none():
    """Test that None returns all indices."""
    result = parse_subset(None, 5)
    assert result == [0, 1, 2, 3, 4]


def test_parse_subset_with_spaces():
    """Test parsing with spaces in the input."""
    result = parse_subset(" 1 - 3 , 5 , 7 - 9 ", 10)
    assert result == [0, 1, 2, 4, 6, 7, 8]


def test_parse_subset_out_of_range_single():
    """Test that out of range single index raises ValueError."""
    with pytest.raises(ValueError, match="Index 11 out of range"):
        parse_subset("11", 10)


def test_parse_subset_out_of_range_in_range():
    """Test that out of range in a range raises ValueError."""
    with pytest.raises(ValueError, match="Index 11 out of range"):
        parse_subset("1-11", 10)


def test_parse_subset_invalid_range_reversed():
    """Test that reversed range raises ValueError."""
    with pytest.raises(ValueError, match="Invalid range 5-1"):
        parse_subset("5-1", 10)


def test_parse_subset_zero_index():
    """Test that index 0 raises ValueError (1-based indexing)."""
    with pytest.raises(ValueError, match="Index must be >= 1"):
        parse_subset("0", 10)


def test_parse_subset_negative_index():
    """Test that negative index raises ValueError."""
    with pytest.raises(ValueError, match="Invalid range format"):
        parse_subset("-1", 10)


def test_parse_subset_invalid_format():
    """Test that invalid format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid index"):
        parse_subset("1,abc,3", 10)


def test_parse_subset_invalid_range_format():
    """Test that invalid range format raises ValueError."""
    with pytest.raises(ValueError, match="Invalid range format"):
        parse_subset("1-2-3", 10)


def test_parse_subset_duplicate_indices():
    """Test that duplicate indices are handled correctly (deduplicated)."""
    result = parse_subset("1,1,2,2", 10)
    assert result == [0, 1]  # Duplicates removed, sorted


def test_parse_subset_overlapping_ranges():
    """Test that overlapping ranges are handled correctly."""
    result = parse_subset("1-3,2-4", 10)
    assert result == [0, 1, 2, 3]  # Overlaps resolved, sorted


def test_parse_subset_full_range():
    """Test parsing a range that covers all test cases."""
    result = parse_subset("1-10", 10)
    assert result == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_parse_subset_last_index():
    """Test parsing the last valid index."""
    result = parse_subset("10", 10)
    assert result == [9]  # Last index (0-based)


def test_parse_subset_first_index():
    """Test parsing the first valid index."""
    result = parse_subset("1", 10)
    assert result == [0]  # First index (0-based)


def test_parse_subset_complex_combination():
    """Test parsing a complex combination."""
    result = parse_subset("1,3-5,2,8-10,7", 10)
    assert result == [0, 1, 2, 3, 4, 6, 7, 8, 9]  # All sorted and deduplicated


def test_parse_subset_start_index_out_of_range():
    """Test that start index in range out of bounds raises ValueError."""
    with pytest.raises(ValueError, match="Index 15 out of range"):
        parse_subset("15-20", 10)
