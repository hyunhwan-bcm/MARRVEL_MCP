import os
import importlib

from config import llm_config


def test_default_openrouter_model_fallback():
    """When OPENROUTER_MODEL is unset, fallback to Gemini 2.5 Flash."""
    original = os.environ.pop("OPENROUTER_MODEL", None)
    try:
        # Reload to ensure no cached value interferes
        importlib.reload(llm_config)
        assert (
            llm_config.get_openrouter_model() == llm_config.DEFAULT_MODEL
        ), "Expected fallback to DEFAULT_MODEL when env var missing"
    finally:
        if original is not None:
            os.environ["OPENROUTER_MODEL"] = original


def test_openrouter_model_env_override():
    """Environment variable should override the default model selection."""
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
    """Loading evaluate_mcp as a module should respect OPENROUTER_MODEL at import time."""
    from importlib.machinery import SourceFileLoader
    from importlib.util import spec_from_loader, module_from_spec

    override = "openai/gpt-4o"
    original = os.environ.get("OPENROUTER_MODEL")
    os.environ["OPENROUTER_MODEL"] = override
    try:
        eval_path = os.path.abspath("mcp_llm_test/evaluate_mcp.py")
        loader = SourceFileLoader("evaluate_mcp_for_test", eval_path)
        spec = spec_from_loader(loader.name, loader)
        module = module_from_spec(spec)
        loader.exec_module(module)
        assert getattr(module, "MODEL") == override
    finally:
        if original is None:
            os.environ.pop("OPENROUTER_MODEL", None)
        else:
            os.environ["OPENROUTER_MODEL"] = original
