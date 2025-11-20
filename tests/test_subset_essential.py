"""
Essential subset parsing tests.

Reduced test suite covering only critical parsing scenarios.
"""

import os
import sys
from pathlib import Path

import pytest

# Set dummy API key to avoid import error
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_testing"

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))

from evaluation_modules import parse_subset


def test_parse_subset_basic_range():
    """Test parsing a basic range."""
    result = parse_subset("1-5", 10)
    assert result == [0, 1, 2, 3, 4]  # 0-based indices


def test_parse_subset_combination():
    """Test parsing combination of ranges and individual indices."""
    result = parse_subset("1-3,5,7-9", 10)
    assert result == [0, 1, 2, 4, 6, 7, 8]


def test_parse_subset_empty_returns_all():
    """Test that empty string returns all indices."""
    result = parse_subset("", 5)
    assert result == [0, 1, 2, 3, 4]
