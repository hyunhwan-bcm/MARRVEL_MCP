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

from evaluation_modules import (
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

    # Monkeypatch the CACHE_DIR in the cache module
    import evaluation_modules.cache as cache_module

    monkeypatch.setattr(cache_module, "CACHE_DIR", test_cache_dir)

    yield test_cache_dir

    # Cleanup - handle directories and files
    if test_cache_dir.exists():
        import shutil

        shutil.rmtree(test_cache_dir)
        test_cache_dir.mkdir(parents=True, exist_ok=True)


class TestCachePath:
    """Tests for cache path generation."""

    def test_simple_name(self, temp_cache_dir):
        """Test cache path generation for simple test case name."""
        run_id = "test_run"
        test_uuid = "simple_test_uuid"
        cache_path = get_cache_path(run_id, test_uuid)

        # Check that the path is in the run-specific subdirectory
        assert cache_path.parent == temp_cache_dir / run_id
        assert cache_path.name == f"{test_uuid}.pkl"
        assert cache_path.suffix == ".pkl"

    def test_name_with_special_characters(self, temp_cache_dir):
        """Test cache path generation with UUID (no special character sanitization needed)."""
        run_id = "test_run"
        test_uuid = "test_uuid_with_special_chars"
        cache_path = get_cache_path(run_id, test_uuid)

        # UUIDs don't have special characters, they're already sanitized
        assert cache_path.name == f"{test_uuid}.pkl"
        assert cache_path.suffix == ".pkl"

    def test_name_with_multiple_spaces(self, temp_cache_dir):
        """Test cache path generation with UUID."""
        run_id = "test_run"
        test_uuid = "test_uuid_with_underscores"
        cache_path = get_cache_path(run_id, test_uuid)

        # UUIDs are used directly as filenames
        assert cache_path.name == f"{test_uuid}.pkl"

    def test_empty_name(self, temp_cache_dir):
        """Test cache path generation for empty UUID."""
        run_id = "test_run"
        test_uuid = ""
        cache_path = get_cache_path(run_id, test_uuid)

        assert cache_path.parent == temp_cache_dir / run_id
        assert cache_path.name == ".pkl"


class TestSaveAndLoadCache:
    """Tests for saving and loading cached results."""

    def test_save_and_load_simple_result(self, temp_cache_dir):
        """Test saving and loading a simple cached result."""
        run_id = "test_run"
        test_uuid = "simple_test_uuid"
        test_result = {
            "question": "What is 2+2?",
            "response": "4",
            "classification": "yes",
            "tool_calls": [],
            "conversation": [],
        }

        # Save the result
        save_cached_result(run_id, test_uuid, test_result)

        # Verify file was created
        cache_path = get_cache_path(run_id, test_uuid)
        assert cache_path.exists()

        # Load the result
        loaded_result = load_cached_result(run_id, test_uuid)

        assert loaded_result is not None
        assert loaded_result == test_result

    def test_save_and_load_complex_result(self, temp_cache_dir):
        """Test saving and loading a complex cached result with nested data."""
        run_id = "test_run"
        test_uuid = "complex_test_uuid"
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
        save_cached_result(run_id, test_uuid, test_result)

        # Load the result
        loaded_result = load_cached_result(run_id, test_uuid)

        assert loaded_result is not None
        assert loaded_result == test_result
        assert loaded_result["tool_calls"] == test_result["tool_calls"]
        assert loaded_result["conversation"] == test_result["conversation"]

    def test_load_nonexistent_cache(self, temp_cache_dir):
        """Test loading cache for non-existent test case."""
        run_id = "test_run"
        test_uuid = "nonexistent_test_uuid"
        loaded_result = load_cached_result(run_id, test_uuid)

        assert loaded_result is None

    def test_save_overwrites_existing_cache(self, temp_cache_dir):
        """Test that saving overwrites existing cache."""
        run_id = "test_run"
        test_uuid = "overwrite_test_uuid"
        result1 = {"response": "First response"}
        result2 = {"response": "Second response"}

        # Save first result
        save_cached_result(run_id, test_uuid, result1)
        loaded1 = load_cached_result(run_id, test_uuid)
        assert loaded1 == result1

        # Save second result (should overwrite)
        save_cached_result(run_id, test_uuid, result2)
        loaded2 = load_cached_result(run_id, test_uuid)
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
        run_id = "test_run"
        # Create multiple cache files
        test_cases = [
            ("test_uuid_1", {"response": "Response for test 1"}),
            ("test_uuid_2", {"response": "Response for test 2"}),
            ("test_uuid_3", {"response": "Response for test 3"}),
        ]
        for test_uuid, result in test_cases:
            save_cached_result(run_id, test_uuid, result)

        # Verify files were created
        run_dir = temp_cache_dir / run_id
        assert len(list(run_dir.glob("*.pkl"))) == 3

        # Clear cache for this run
        clear_cache(run_id)

        # Verify all files were deleted (directory should be gone)
        assert not run_dir.exists()

    def test_clear_cache_preserves_directory(self, temp_cache_dir):
        """Test that clearing cache for a specific run removes the run directory."""
        run_id = "test_run"
        # Create some cache files
        save_cached_result(run_id, "test_uuid", {"response": "Response"})

        # Clear cache for this run
        clear_cache(run_id)

        # Run directory should not exist anymore
        run_dir = temp_cache_dir / run_id
        assert not run_dir.exists()

        # But the main cache directory should still exist
        assert temp_cache_dir.exists()

    def test_clear_cache_ignores_non_pkl_files(self, temp_cache_dir):
        """Test that clearing cache removes run directory with .pkl files."""
        run_id = "test_run"
        # Create a cache file
        save_cached_result(run_id, "test_uuid", {"response": "Response"})

        # Create a non-pkl file in the run directory
        run_dir = temp_cache_dir / run_id
        other_file = run_dir / "other_file.txt"
        other_file.write_text("Some content")

        # Clear cache for this run
        clear_cache(run_id)

        # The entire run directory should be deleted (including non-pkl files)
        assert not run_dir.exists()
        assert not other_file.exists()


class TestCacheIntegration:
    """Integration tests for cache functionality."""

    def test_multiple_test_cases(self, temp_cache_dir):
        """Test caching multiple test cases independently."""
        run_id = "test_run"
        test_cases = {
            "gene_query_uuid": {"response": "TP53"},
            "variant_query_uuid": {"response": "Pathogenic"},
            "omim_query_uuid": {"response": "Disease info"},
        }

        # Save all test cases
        for test_uuid, result in test_cases.items():
            save_cached_result(run_id, test_uuid, result)

        # Verify all were saved
        run_dir = temp_cache_dir / run_id
        assert len(list(run_dir.glob("*.pkl"))) == 3

        # Load and verify each
        for test_uuid, expected_result in test_cases.items():
            loaded_result = load_cached_result(run_id, test_uuid)
            assert loaded_result == expected_result

    def test_cache_persistence(self, temp_cache_dir):
        """Test that cache persists across multiple operations."""
        run_id = "test_run"
        test_uuid = "persistence_test_uuid"
        test_result = {"response": "Persistent response"}

        # Save result
        save_cached_result(run_id, test_uuid, test_result)

        # Load multiple times
        for _ in range(5):
            loaded_result = load_cached_result(run_id, test_uuid)
            assert loaded_result == test_result

    def test_cache_with_unicode_characters(self, temp_cache_dir):
        """Test cache handles Unicode characters in results (UUIDs don't have unicode)."""
        run_id = "test_run"
        test_uuid = "unicode_test_uuid"
        test_result = {
            "response": "Response with émojis 🧬 and ünïcode",
            "classification": "yes",
        }

        # Save and load
        save_cached_result(run_id, test_uuid, test_result)
        loaded_result = load_cached_result(run_id, test_uuid)

        assert loaded_result is not None
        assert loaded_result == test_result
