"""
Unit tests for cache functionality in evaluate_mcp.py

Tests the caching system used by the MCP LLM evaluation tool including:
- Cache path generation
- Saving and loading cached results
- Cache clearing
- Cache directory creation
"""

import pickle
import sys
import tempfile
from pathlib import Path

import pytest

# Add mcp_llm_test to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))

from evaluate_mcp import (
    CACHE_DIR,
    clear_cache,
    get_cache_path,
    load_cached_result,
    save_cached_result,
)


@pytest.fixture
def temp_cache_dir(monkeypatch, tmp_path):
    """Use a temporary directory for cache during tests."""
    test_cache_dir = tmp_path / "test_cache"
    test_cache_dir.mkdir(parents=True, exist_ok=True)

    # Monkeypatch the CACHE_DIR in the module
    import evaluate_mcp

    monkeypatch.setattr(evaluate_mcp, "CACHE_DIR", test_cache_dir)

    yield test_cache_dir

    # Cleanup
    if test_cache_dir.exists():
        for file in test_cache_dir.glob("*"):
            file.unlink()


class TestCachePath:
    """Tests for cache path generation."""

    def test_simple_name(self, temp_cache_dir):
        """Test cache path generation for simple test case name."""
        test_name = "Simple Test"
        cache_path = get_cache_path(test_name)

        assert cache_path.parent == temp_cache_dir
        assert cache_path.name == "Simple_Test.pkl"
        assert cache_path.suffix == ".pkl"

    def test_name_with_special_characters(self, temp_cache_dir):
        """Test cache path generation sanitizes special characters."""
        test_name = "Test: Gene for NM_001045477.4:c.187C>T"
        cache_path = get_cache_path(test_name)

        # Special characters should be replaced with underscores
        assert ":" not in cache_path.name
        assert ">" not in cache_path.name
        assert cache_path.name.endswith(".pkl")

    def test_name_with_multiple_spaces(self, temp_cache_dir):
        """Test cache path generation handles multiple spaces."""
        test_name = "Test   With   Multiple   Spaces"
        cache_path = get_cache_path(test_name)

        # Multiple spaces should become single underscores
        assert cache_path.name == "Test___With___Multiple___Spaces.pkl"

    def test_empty_name(self, temp_cache_dir):
        """Test cache path generation for empty name."""
        test_name = ""
        cache_path = get_cache_path(test_name)

        assert cache_path.parent == temp_cache_dir
        assert cache_path.name == ".pkl"


class TestSaveAndLoadCache:
    """Tests for saving and loading cached results."""

    def test_save_and_load_simple_result(self, temp_cache_dir):
        """Test saving and loading a simple cached result."""
        test_name = "Simple Test"
        test_result = {
            "question": "What is 2+2?",
            "response": "4",
            "classification": "yes",
            "tool_calls": [],
            "conversation": [],
        }

        # Save the result
        save_cached_result(test_name, test_result)

        # Verify file was created
        cache_path = get_cache_path(test_name)
        assert cache_path.exists()

        # Load the result
        loaded_result = load_cached_result(test_name)

        assert loaded_result is not None
        assert loaded_result == test_result

    def test_save_and_load_complex_result(self, temp_cache_dir):
        """Test saving and loading a complex cached result with nested data."""
        test_name = "Complex Test"
        test_result = {
            "question": "Complex question",
            "response": "Complex response",
            "classification": "yes - detailed reason",
            "tool_calls": [
                {"name": "tool1", "args": {"param": "value"}},
                {"name": "tool2", "args": {"param": "value2"}},
            ],
            "conversation": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there"},
            ],
            "tokens_used": 1234,
        }

        # Save the result
        save_cached_result(test_name, test_result)

        # Load the result
        loaded_result = load_cached_result(test_name)

        assert loaded_result is not None
        assert loaded_result == test_result
        assert loaded_result["tool_calls"] == test_result["tool_calls"]
        assert loaded_result["conversation"] == test_result["conversation"]

    def test_load_nonexistent_cache(self, temp_cache_dir):
        """Test loading cache for non-existent test case."""
        test_name = "Nonexistent Test"
        loaded_result = load_cached_result(test_name)

        assert loaded_result is None

    def test_save_overwrites_existing_cache(self, temp_cache_dir):
        """Test that saving overwrites existing cache."""
        test_name = "Overwrite Test"
        result1 = {"response": "First response"}
        result2 = {"response": "Second response"}

        # Save first result
        save_cached_result(test_name, result1)
        loaded1 = load_cached_result(test_name)
        assert loaded1 == result1

        # Save second result (should overwrite)
        save_cached_result(test_name, result2)
        loaded2 = load_cached_result(test_name)
        assert loaded2 == result2
        assert loaded2 != result1


class TestClearCache:
    """Tests for cache clearing functionality."""

    def test_clear_empty_cache(self, temp_cache_dir):
        """Test clearing an empty cache directory."""
        # Should not raise an error
        clear_cache()

        assert len(list(temp_cache_dir.glob("*.pkl"))) == 0

    def test_clear_cache_with_files(self, temp_cache_dir):
        """Test clearing cache with multiple files."""
        # Create multiple cache files
        test_cases = ["Test 1", "Test 2", "Test 3"]
        for test_name in test_cases:
            save_cached_result(test_name, {"response": f"Response for {test_name}"})

        # Verify files were created
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 3

        # Clear cache
        clear_cache()

        # Verify all files were deleted
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 0

    def test_clear_cache_preserves_directory(self, temp_cache_dir):
        """Test that clearing cache preserves the directory."""
        # Create some cache files
        save_cached_result("Test", {"response": "Response"})

        # Clear cache
        clear_cache()

        # Directory should still exist
        assert temp_cache_dir.exists()

    def test_clear_cache_ignores_non_pkl_files(self, temp_cache_dir):
        """Test that clearing cache only removes .pkl files."""
        # Create a cache file
        save_cached_result("Test", {"response": "Response"})

        # Create a non-pkl file
        other_file = temp_cache_dir / "other_file.txt"
        other_file.write_text("Some content")

        # Clear cache
        clear_cache()

        # Only .pkl files should be deleted
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 0
        assert other_file.exists()


class TestCacheIntegration:
    """Integration tests for cache functionality."""

    def test_multiple_test_cases(self, temp_cache_dir):
        """Test caching multiple test cases independently."""
        test_cases = {
            "Gene Query": {"response": "TP53"},
            "Variant Query": {"response": "Pathogenic"},
            "OMIM Query": {"response": "Disease info"},
        }

        # Save all test cases
        for name, result in test_cases.items():
            save_cached_result(name, result)

        # Verify all were saved
        assert len(list(temp_cache_dir.glob("*.pkl"))) == 3

        # Load and verify each
        for name, expected_result in test_cases.items():
            loaded_result = load_cached_result(name)
            assert loaded_result == expected_result

    def test_cache_persistence(self, temp_cache_dir):
        """Test that cache persists across multiple operations."""
        test_name = "Persistence Test"
        test_result = {"response": "Persistent response"}

        # Save result
        save_cached_result(test_name, test_result)

        # Load multiple times
        for _ in range(5):
            loaded_result = load_cached_result(test_name)
            assert loaded_result == test_result

    def test_cache_with_unicode_characters(self, temp_cache_dir):
        """Test cache handles Unicode characters in test names and results."""
        test_name = "Test with émojis 🧬 and ünïcode"
        test_result = {
            "response": "Response with émojis 🧬 and ünïcode",
            "classification": "yes",
        }

        # Save and load
        save_cached_result(test_name, test_result)
        loaded_result = load_cached_result(test_name)

        assert loaded_result is not None
        assert loaded_result == test_result
