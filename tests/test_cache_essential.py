"""
Essential cache functionality tests.

Reduced test suite covering only critical cache operations:
- Basic save and load
- Cache clearing
"""

import sys
from pathlib import Path

import pytest

# Add mcp_llm_test to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))

from evaluation_modules import (
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

    # Cleanup
    if test_cache_dir.exists():
        import shutil

        shutil.rmtree(test_cache_dir)


def test_save_and_load_cache(temp_cache_dir):
    """Test basic cache save and load functionality."""
    run_id = "test_run"
    test_uuid = "test_uuid"
    test_result = {
        "question": "What is 2+2?",
        "response": "4",
        "classification": "yes",
        "tool_calls": [{"name": "tool1", "args": {"param": "value"}}],
    }

    # Save and verify file creation
    save_cached_result(run_id, test_uuid, test_result)
    cache_path = get_cache_path(run_id, test_uuid)
    assert cache_path.exists()

    # Load and verify content
    loaded_result = load_cached_result(run_id, test_uuid)
    assert loaded_result is not None
    assert loaded_result == test_result


def test_clear_cache(temp_cache_dir):
    """Test cache clearing functionality."""
    run_id = "test_run"

    # Create cache files
    save_cached_result(run_id, "test1", {"data": "test1"})
    save_cached_result(run_id, "test2", {"data": "test2"})

    run_dir = temp_cache_dir / run_id
    assert len(list(run_dir.glob("*.pkl"))) == 2

    # Clear and verify
    clear_cache(run_id)
    assert not run_dir.exists()  # Directory removed
