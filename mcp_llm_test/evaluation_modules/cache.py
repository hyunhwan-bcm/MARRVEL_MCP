"""
Cache management for evaluation results.

This module provides functions to cache test results to speed up
re-runs and avoid redundant API calls.
"""

import pickle
from pathlib import Path
from typing import Any, Dict

# Cache settings
CACHE_DIR = Path.home() / ".cache" / "marrvel-mcp" / "evaluations"
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cache_path(
    test_case_name: str,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
) -> Path:
    """Get the cache file path for a test case.

    Args:
        test_case_name: Name of the test case
        vanilla_mode: If True, append '_vanilla' to distinguish from tool-enabled cache
        web_mode: If True, append '_web' to distinguish from vanilla cache
        model_id: Model identifier (e.g., "google/gemini-2.5-flash"). If provided, cache is model-specific.

    Returns:
        Path to cache file
    """
    # Use sanitized test case name for filename
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in test_case_name)
    safe_name = safe_name.strip().replace(" ", "_")

    # Add model identifier if provided (sanitize it too)
    if model_id:
        safe_model = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in model_id)
        safe_model = safe_model.replace("/", "_")
        model_suffix = f"_{safe_model}"
    else:
        model_suffix = ""

    if web_mode:
        mode_suffix = "_web"
    elif vanilla_mode:
        mode_suffix = "_vanilla"
    else:
        mode_suffix = ""

    return CACHE_DIR / f"{safe_name}{model_suffix}{mode_suffix}.pkl"


def load_cached_result(
    test_case_name: str,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
) -> Dict[str, Any] | None:
    """Load cached result for a test case if it exists.

    Args:
        test_case_name: Name of the test case
        vanilla_mode: If True, load from vanilla cache
        web_mode: If True, load from web cache
        model_id: Model identifier for model-specific cache

    Returns:
        Cached result or None if not found
    """
    cache_path = get_cache_path(test_case_name, vanilla_mode, web_mode, model_id)
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache for {test_case_name}: {e}")
            return None
    return None


def save_cached_result(
    test_case_name: str,
    result: Dict[str, Any],
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
):
    """Save result to cache.

    Args:
        test_case_name: Name of the test case
        result: Test result to cache
        vanilla_mode: If True, save to vanilla cache
        web_mode: If True, save to web cache
        model_id: Model identifier for model-specific cache
    """
    cache_path = get_cache_path(test_case_name, vanilla_mode, web_mode, model_id)
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(result, f)
    except Exception as e:
        print(f"Warning: Failed to save cache for {test_case_name}: {e}")


def clear_cache():
    """Clear all cached results."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {cache_file}: {e}")
        print(f"✅ Cache cleared: {CACHE_DIR}")
