"""
Tests for the caching functionality in mcp-llm-test/evaluate_mcp.py
"""

import json
import pytest
import sys
from pathlib import Path

# Add mcp-llm-test directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp-llm-test"))

from evaluate_mcp import (
    get_cache_key,
    load_cached_result,
    save_cached_result,
    clear_cache,
    CACHE_DIR,
)


@pytest.fixture
def sample_result():
    """Sample test result data"""
    return {
        "question": "What is the capital of France?",
        "expected": "Paris",
        "response": "The capital of France is Paris.",
        "classification": "yes - the response is correct",
        "tool_calls": [],
        "conversation": [],
        "tokens_used": 100,
    }


@pytest.fixture
def failed_result():
    """Sample failed test result data"""
    return {
        "question": "What is the capital of Spain?",
        "expected": "Madrid",
        "response": "The capital is Barcelona.",
        "classification": "no - the response is incorrect",
        "tool_calls": [],
        "conversation": [],
        "tokens_used": 80,
    }


def test_get_cache_key():
    """Test that cache key generation is consistent"""
    key1 = get_cache_key("input1", "expected1")
    key2 = get_cache_key("input1", "expected1")
    key3 = get_cache_key("input2", "expected1")

    # Same inputs should produce same key
    assert key1 == key2
    # Different inputs should produce different keys
    assert key1 != key3
    # Keys should be SHA256 hashes (64 hex characters)
    assert len(key1) == 64
    assert all(c in "0123456789abcdef" for c in key1)


def test_save_and_load_cached_result(sample_result, tmp_path):
    """Test saving and loading a successful cached result"""
    # Temporarily override CACHE_DIR for testing
    import evaluate_mcp

    original_cache_dir = evaluate_mcp.CACHE_DIR
    evaluate_mcp.CACHE_DIR = tmp_path / ".cache" / "test"

    try:
        cache_key = get_cache_key(sample_result["question"], sample_result["expected"])

        # Save the result
        save_cached_result(cache_key, sample_result)

        # Verify file was created
        cache_file = evaluate_mcp.CACHE_DIR / f"{cache_key}.json"
        assert cache_file.exists()

        # Load the result
        loaded_result = load_cached_result(cache_key)

        # Verify loaded result matches original
        assert loaded_result is not None
        assert loaded_result["question"] == sample_result["question"]
        assert loaded_result["expected"] == sample_result["expected"]
        assert loaded_result["response"] == sample_result["response"]
        assert loaded_result["classification"] == sample_result["classification"]
    finally:
        # Restore original CACHE_DIR
        evaluate_mcp.CACHE_DIR = original_cache_dir


def test_failed_result_not_cached(failed_result, tmp_path):
    """Test that failed results are not cached"""
    # Temporarily override CACHE_DIR for testing
    import evaluate_mcp

    original_cache_dir = evaluate_mcp.CACHE_DIR
    evaluate_mcp.CACHE_DIR = tmp_path / ".cache" / "test"

    try:
        cache_key = get_cache_key(failed_result["question"], failed_result["expected"])

        # Try to save the failed result
        save_cached_result(cache_key, failed_result)

        # Verify file was NOT created
        cache_file = evaluate_mcp.CACHE_DIR / f"{cache_key}.json"
        assert not cache_file.exists()

        # Try to load it
        loaded_result = load_cached_result(cache_key)
        assert loaded_result is None
    finally:
        # Restore original CACHE_DIR
        evaluate_mcp.CACHE_DIR = original_cache_dir


def test_load_nonexistent_cache():
    """Test loading a cache that doesn't exist"""
    result = load_cached_result("nonexistent_key_12345")
    assert result is None


def test_clear_cache(sample_result, tmp_path):
    """Test clearing the cache"""
    # Temporarily override CACHE_DIR for testing
    import evaluate_mcp

    original_cache_dir = evaluate_mcp.CACHE_DIR
    evaluate_mcp.CACHE_DIR = tmp_path / ".cache" / "test"

    try:
        # Save a result
        cache_key = get_cache_key(sample_result["question"], sample_result["expected"])
        save_cached_result(cache_key, sample_result)

        # Verify it exists
        assert evaluate_mcp.CACHE_DIR.exists()
        assert (evaluate_mcp.CACHE_DIR / f"{cache_key}.json").exists()

        # Clear the cache
        clear_cache()

        # Verify it's gone
        assert not evaluate_mcp.CACHE_DIR.exists()
    finally:
        # Restore original CACHE_DIR
        evaluate_mcp.CACHE_DIR = original_cache_dir


def test_cache_validation_rejects_failed_results(tmp_path):
    """Test that loading rejects failed results even if they exist in cache"""
    import evaluate_mcp

    original_cache_dir = evaluate_mcp.CACHE_DIR
    evaluate_mcp.CACHE_DIR = tmp_path / ".cache" / "test"

    try:
        # Manually create a cache file with a failed result
        evaluate_mcp.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_key = "test_key_123"
        cache_file = evaluate_mcp.CACHE_DIR / f"{cache_key}.json"

        failed_result = {
            "question": "test",
            "expected": "test",
            "response": "wrong",
            "classification": "no - incorrect",
            "tool_calls": [],
            "conversation": [],
        }

        with open(cache_file, "w") as f:
            json.dump(failed_result, f)

        # Try to load it - should return None because classification is "no"
        loaded = load_cached_result(cache_key)
        assert loaded is None
    finally:
        evaluate_mcp.CACHE_DIR = original_cache_dir
