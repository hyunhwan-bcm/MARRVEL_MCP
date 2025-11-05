"""Tests for cache functionality in evaluate_mcp.py"""

import json
import sys
from pathlib import Path

import pytest

# Add mcp-llm-test to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-llm-test"))

from evaluate_mcp import (
    CACHE_DIR,
    CACHE_FILE,
    clear_cache,
    is_test_successful,
    load_cache,
    save_cache,
)


@pytest.fixture
def cleanup_cache():
    """Fixture to clean up cache before and after tests"""
    # Clean up before test
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    yield
    # Clean up after test
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
    if CACHE_DIR.exists() and not any(CACHE_DIR.iterdir()):
        CACHE_DIR.rmdir()


def test_cache_directory_creation(cleanup_cache):
    """Test that cache directory is created when saving cache"""
    test_cache = {"key1": "value1"}
    save_cache(test_cache)
    assert CACHE_DIR.exists()
    assert CACHE_FILE.exists()


def test_save_and_load_cache(cleanup_cache):
    """Test saving and loading cache"""
    test_cache = {
        "test_question||test_expected": {
            "question": "test_question",
            "expected": "test_expected",
            "response": "test_response",
            "classification": "yes - matches",
        }
    }
    save_cache(test_cache)
    loaded_cache = load_cache()
    assert loaded_cache == test_cache


def test_load_empty_cache(cleanup_cache):
    """Test loading cache when file doesn't exist"""
    loaded_cache = load_cache()
    assert loaded_cache == {}


def test_clear_cache(cleanup_cache):
    """Test clearing cache"""
    test_cache = {"key1": "value1"}
    save_cache(test_cache)
    assert CACHE_FILE.exists()

    clear_cache()
    assert not CACHE_FILE.exists()


def test_clear_nonexistent_cache(cleanup_cache, capsys):
    """Test clearing cache when it doesn't exist"""
    clear_cache()
    captured = capsys.readouterr()
    assert "No cache to clear" in captured.out


def test_is_test_successful():
    """Test the is_test_successful function"""
    # Test successful classifications
    assert is_test_successful("yes - matches expected")
    assert is_test_successful("YES - correct")
    assert is_test_successful("The answer is yes")

    # Test failed classifications
    assert not is_test_successful("no - doesn't match")
    assert not is_test_successful("NO - incorrect")
    assert not is_test_successful("error occurred")


def test_cache_persistence_across_loads(cleanup_cache):
    """Test that cache persists across multiple save/load cycles"""
    cache1 = {"key1": "value1"}
    save_cache(cache1)

    # Load and modify
    loaded = load_cache()
    loaded["key2"] = "value2"
    save_cache(loaded)

    # Load again and verify both values
    final = load_cache()
    assert final == {"key1": "value1", "key2": "value2"}


def test_cache_handles_invalid_json(cleanup_cache):
    """Test that load_cache handles invalid JSON gracefully"""
    # Create cache directory and write invalid JSON
    CACHE_DIR.mkdir(exist_ok=True)
    with open(CACHE_FILE, "w") as f:
        f.write("invalid json {{{")

    # Should return empty dict without crashing
    loaded = load_cache()
    assert loaded == {}
