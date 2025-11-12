import os
import importlib

import llm_config


def test_default_openrouter_model_fallback():
    """When OPENROUTER_MODEL is unset, fallback to Gemini 2.5 Flash."""
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


def test_default_evaluator_model_fallback():
    """When EVALUATOR_MODEL is unset, fallback to Gemini 2.5 Pro."""
    original = os.environ.pop("EVALUATOR_MODEL", None)
    try:
        # Reload to ensure no cached value interferes
        importlib.reload(llm_config)
        assert (
            llm_config.get_evaluator_model() == llm_config.DEFAULT_EVALUATOR_MODEL
        ), "Expected fallback to DEFAULT_EVALUATOR_MODEL when env var missing"
        assert (
            llm_config.get_evaluator_model() == "google/gemini-2.5-pro"
        ), "Expected evaluator to default to Gemini 2.5 Pro"
    finally:
        if original is not None:
            os.environ["EVALUATOR_MODEL"] = original


def test_evaluator_model_env_override():
    """Environment variable should override the default evaluator model."""
    override = "anthropic/claude-3.5-sonnet"
    original = os.environ.get("EVALUATOR_MODEL")
    os.environ["EVALUATOR_MODEL"] = override
    try:
        importlib.reload(llm_config)
        assert (
            llm_config.get_evaluator_model() == override
        ), "Expected evaluator env override to take precedence"
    finally:
        # Restore original state
        if original is None:
            os.environ.pop("EVALUATOR_MODEL", None)
        else:
            os.environ["EVALUATOR_MODEL"] = original


def test_evaluate_mcp_module_resolves_evaluator_model(tmp_path):
    """Loading evaluate_mcp as a module should use EVALUATOR_MODEL for evaluation, not OPENROUTER_MODEL."""
    from importlib.machinery import SourceFileLoader
    from importlib.util import spec_from_loader, module_from_spec

    test_override = "openai/gpt-4o"
    evaluator_override = "anthropic/claude-3.5-sonnet"

    original_test = os.environ.get("OPENROUTER_MODEL")
    original_eval = os.environ.get("EVALUATOR_MODEL")

    # Set OPENROUTER_MODEL for tested model
    os.environ["OPENROUTER_MODEL"] = test_override
    # Set EVALUATOR_MODEL for evaluation
    os.environ["EVALUATOR_MODEL"] = evaluator_override

    try:
        eval_path = os.path.abspath("mcp-llm-test/evaluate_mcp.py")
        loader = SourceFileLoader("evaluate_mcp_for_test", eval_path)
        spec = spec_from_loader(loader.name, loader)
        module = module_from_spec(spec)
        loader.exec_module(module)

        # EVALUATOR_MODEL should be used for evaluation
        assert (
            getattr(module, "EVALUATOR_MODEL") == evaluator_override
        ), "Expected EVALUATOR_MODEL to match environment variable"

        # MODEL is deprecated but should still be set to default evaluator model
        assert (
            getattr(module, "MODEL") == "google/gemini-2.5-pro"
        ), "Expected MODEL to remain as hardcoded evaluator (deprecated)"
    finally:
        if original_test is None:
            os.environ.pop("OPENROUTER_MODEL", None)
        else:
            os.environ["OPENROUTER_MODEL"] = original_test
        if original_eval is None:
            os.environ.pop("EVALUATOR_MODEL", None)
        else:
            os.environ["EVALUATOR_MODEL"] = original_eval
