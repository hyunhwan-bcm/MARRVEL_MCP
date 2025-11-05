"""
Unit tests for caching and CLI functionality in evaluate_mcp.py

Tests the caching mechanism, CLI argument parsing, and subset selection.
"""

import json
import os
import sys
from pathlib import Path
import tempfile
import shutil

import pytest

# Set dummy API key to avoid import error
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_testing"

# Add project root to path to import evaluate_mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-llm-test"))

from evaluate_mcp import (
    load_cache,
    save_cache,
    clear_cache,
    is_test_successful,
    parse_subset,
    CACHE_DIR,
    CACHE_FILE,
)


@pytest.fixture
def temp_cache_dir(monkeypatch):
    """Create a temporary cache directory for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    temp_cache_file = temp_dir / "test_results.json"

    # Monkeypatch the cache directory and file
    monkeypatch.setattr("evaluate_mcp.CACHE_DIR", temp_dir)
    monkeypatch.setattr("evaluate_mcp.CACHE_FILE", temp_cache_file)

    yield temp_dir, temp_cache_file

    # Cleanup
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


def test_parse_subset_single():
    """Test parsing a single question number."""
    result = parse_subset("1")
    assert result == [1]


def test_parse_subset_multiple():
    """Test parsing multiple comma-separated question numbers."""
    result = parse_subset("1,2,4")
    assert result == [1, 2, 4]


def test_parse_subset_range():
    """Test parsing a range of question numbers."""
    result = parse_subset("1-5")
    assert result == [1, 2, 3, 4, 5]


def test_parse_subset_mixed():
    """Test parsing mixed format (ranges and individual numbers)."""
    result = parse_subset("1,3-5,8")
    assert result == [1, 3, 4, 5, 8]


def test_parse_subset_duplicates():
    """Test that duplicate numbers are removed."""
    result = parse_subset("1,1,2,2,3")
    assert result == [1, 2, 3]


def test_is_test_successful_with_yes():
    """Test that classifications with 'yes' are recognized as successful."""
    assert is_test_successful("yes, the response is correct")
    assert is_test_successful("Yes - matches expected output")
    assert is_test_successful("YES")


def test_is_test_successful_with_no():
    """Test that classifications with 'no' are recognized as unsuccessful."""
    assert not is_test_successful("no, the response is incorrect")
    assert not is_test_successful("No - missing information")
    assert not is_test_successful("NO")


def test_is_test_successful_edge_cases():
    """Test edge cases in classification."""
    # Should not match 'yes' inside other words
    assert not is_test_successful("yesterday")
    # Should match 'yes' as a word boundary
    assert is_test_successful("yes.")


def test_save_and_load_cache(temp_cache_dir):
    """Test saving and loading cache data."""
    temp_dir, temp_cache_file = temp_cache_dir

    # Sample cache data
    test_cache = {
        "What is TP53?": {
            "question": "What is TP53?",
            "expected": "A tumor suppressor gene",
            "response": "TP53 is a tumor suppressor gene.",
            "classification": "yes - correct",
            "tool_calls": [],
            "conversation": [],
        }
    }

    # Save cache
    save_cache(test_cache)

    # Verify file was created
    assert temp_cache_file.exists()

    # Load cache
    loaded_cache = load_cache()

    # Verify loaded data matches saved data
    assert loaded_cache == test_cache
    assert "What is TP53?" in loaded_cache


def test_load_cache_when_not_exists(temp_cache_dir):
    """Test loading cache when file doesn't exist returns empty dict."""
    loaded_cache = load_cache()
    assert loaded_cache == {}


def test_clear_cache(temp_cache_dir, capsys):
    """Test clearing the cache."""
    temp_dir, temp_cache_file = temp_cache_dir

    # Create a cache file
    test_cache = {"test": "data"}
    save_cache(test_cache)
    assert temp_cache_file.exists()

    # Clear cache
    clear_cache()

    # Verify file was deleted
    assert not temp_cache_file.exists()

    # Check output message
    captured = capsys.readouterr()
    assert "Cache cleared" in captured.out


def test_clear_cache_when_not_exists(temp_cache_dir, capsys):
    """Test clearing cache when no cache exists."""
    clear_cache()

    # Check output message
    captured = capsys.readouterr()
    assert "No cache to clear" in captured.out


def test_cache_directory_created_on_save(temp_cache_dir):
    """Test that cache directory is created if it doesn't exist."""
    temp_dir, temp_cache_file = temp_cache_dir

    # Remove the temp directory to simulate first run
    if temp_dir.exists():
        shutil.rmtree(temp_dir)

    assert not temp_dir.exists()

    # Save cache should create the directory
    test_cache = {"test": "data"}
    save_cache(test_cache)

    # Verify directory and file were created
    assert temp_dir.exists()
    assert temp_cache_file.exists()


def test_save_cache_preserves_json_format(temp_cache_dir):
    """Test that saved cache is valid JSON with proper formatting."""
    temp_dir, temp_cache_file = temp_cache_dir

    test_cache = {
        "question1": {
            "response": "answer1",
            "classification": "yes",
        },
        "question2": {
            "response": "answer2",
            "classification": "no",
        },
    }

    save_cache(test_cache)

    # Read the file directly and verify it's valid JSON
    with open(temp_cache_file, "r") as f:
        file_content = f.read()
        loaded_data = json.loads(file_content)

    # Verify data integrity
    assert loaded_data == test_cache

    # Verify it's formatted with indentation (for readability)
    assert "\n" in file_content  # Should have line breaks
    assert "  " in file_content  # Should have indentation
