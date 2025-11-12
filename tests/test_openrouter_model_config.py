import os
import importlib

import llm_config


def test_default_model_fallback():
    """When LLM_MODEL and OPENROUTER_MODEL are unset, fallback to Gemini 2.5 Flash."""
    original_llm = os.environ.pop("LLM_MODEL", None)
    original_or = os.environ.pop("OPENROUTER_MODEL", None)
    try:
        # Reload to ensure no cached value interferes
        importlib.reload(llm_config)
        assert (
            llm_config.get_default_model() == llm_config.DEFAULT_OPENROUTER_MODEL
        ), "Expected fallback to DEFAULT_OPENROUTER_MODEL when env vars missing"
    finally:
        if original_llm is not None:
            os.environ["LLM_MODEL"] = original_llm
        if original_or is not None:
            os.environ["OPENROUTER_MODEL"] = original_or


def test_default_model_llm_model_env_override():
    """LLM_MODEL environment variable should override the default model selection."""
    override = "gpt-4"
    original_llm = os.environ.get("LLM_MODEL")
    original_or = os.environ.get("OPENROUTER_MODEL")
    os.environ["LLM_MODEL"] = override
    # Also set OPENROUTER_MODEL to verify LLM_MODEL takes precedence
    os.environ["OPENROUTER_MODEL"] = "google/gemini-2.5-flash"
    try:
        importlib.reload(llm_config)
        assert (
            llm_config.get_default_model() == override
        ), "Expected LLM_MODEL env override to take precedence"
    finally:
        # Restore original state
        if original_llm is None:
            os.environ.pop("LLM_MODEL", None)
        else:
            os.environ["LLM_MODEL"] = original_llm
        if original_or is None:
            os.environ.pop("OPENROUTER_MODEL", None)
        else:
            os.environ["OPENROUTER_MODEL"] = original_or


def test_default_model_openrouter_model_env_override():
    """OPENROUTER_MODEL environment variable should override the default when LLM_MODEL is not set."""
    override = "anthropic/claude-3.5-sonnet"
    original_llm = os.environ.get("LLM_MODEL")
    original_or = os.environ.get("OPENROUTER_MODEL")
    # Ensure LLM_MODEL is not set
    os.environ.pop("LLM_MODEL", None)
    os.environ["OPENROUTER_MODEL"] = override
    try:
        importlib.reload(llm_config)
        assert (
            llm_config.get_default_model() == override
        ), "Expected OPENROUTER_MODEL env override to take precedence when LLM_MODEL is not set"
    finally:
        # Restore original state
        if original_llm is None:
            os.environ.pop("LLM_MODEL", None)
        else:
            os.environ["LLM_MODEL"] = original_llm
        if original_or is None:
            os.environ.pop("OPENROUTER_MODEL", None)
        else:
            os.environ["OPENROUTER_MODEL"] = original_or


def test_deprecated_get_openrouter_model_fallback():
    """Deprecated function: When OPENROUTER_MODEL is unset, fallback to Gemini 2.5 Flash."""
    original = os.environ.pop("OPENROUTER_MODEL", None)
    try:
        # Reload to ensure no cached value interferes
        importlib.reload(llm_config)
        assert (
            llm_config.get_openrouter_model() == llm_config.DEFAULT_OPENROUTER_MODEL
        ), "Expected fallback to DEFAULT_OPENROUTER_MODEL when env var missing"
    finally:
        if original is not None:
            os.environ["OPENROUTER_MODEL"] = original


def test_deprecated_get_openrouter_model_env_override():
    """Deprecated function: Environment variable should override the default model selection."""
    override = "anthropic/claude-3.5-sonnet"
    original = os.environ.get("OPENROUTER_MODEL")
    os.environ["OPENROUTER_MODEL"] = override
    try:
        importlib.reload(llm_config)
        assert (
            llm_config.get_openrouter_model() == override
        ), "Expected env override to take precedence"
    finally:
        # Restore original state
        if original is None:
            os.environ.pop("OPENROUTER_MODEL", None)
        else:
            os.environ["OPENROUTER_MODEL"] = original


def test_evaluate_mcp_module_resolves_override(tmp_path):
    """Loading evaluate_mcp as a module should respect model env vars at import time."""
    from importlib.machinery import SourceFileLoader
    from importlib.util import spec_from_loader, module_from_spec

    override = "openai/gpt-4o"
    original_llm = os.environ.get("LLM_MODEL")
    original_or = os.environ.get("OPENROUTER_MODEL")
    os.environ["LLM_MODEL"] = override
    try:
        eval_path = os.path.abspath("mcp-llm-test/evaluate_mcp.py")
        loader = SourceFileLoader("evaluate_mcp_for_test", eval_path)
        spec = spec_from_loader(loader.name, loader)
        module = module_from_spec(spec)
        loader.exec_module(module)
        assert getattr(module, "MODEL") == override
    finally:
        if original_llm is None:
            os.environ.pop("LLM_MODEL", None)
        else:
            os.environ["LLM_MODEL"] = original_llm
        if original_or is None:
            os.environ.pop("OPENROUTER_MODEL", None)
        else:
            os.environ["OPENROUTER_MODEL"] = original_or
