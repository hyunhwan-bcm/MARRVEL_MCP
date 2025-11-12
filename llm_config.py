"""
LLM configuration helpers for multi-provider support.

This module centralizes environment-driven configuration for the model
used across different providers (OpenRouter, OpenAI, Bedrock, Ollama).
It maintains backward compatibility with the original OpenRouter-only setup.

Contract:
- Input: environment variables (LLM_MODEL, OPENROUTER_MODEL, LLM_PROVIDER, etc.)
- Output: model id and provider configuration
- Fallback: defaults to Gemini 2.5 Flash via OpenRouter

Main Functions:
- get_default_model(): Returns the default model ID from environment variables
- get_default_model_config(): Returns both model ID and provider type
- get_openrouter_model(): Deprecated, preserved for backward compatibility

Migration Notes:
- New code should use `get_default_model()` or `get_default_model_config()`
- Legacy `get_openrouter_model()` is preserved for backward compatibility
- Existing code using `get_openrouter_model()` will continue to work unchanged
"""

from __future__ import annotations

import os
from typing import Tuple

from llm_providers import ProviderType, infer_provider_from_model_id


# Default model: latest Gemini 2.5 variant with reliable tool support
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"
DEFAULT_PROVIDER: ProviderType = "openrouter"


def get_default_model() -> str:
    """Return the default model id from environment or the project default.

    This is a general-purpose function that returns a model ID, checking
    environment variables in priority order.

    Priority:
    1) LLM_MODEL env var if set and non-empty
    2) OPENROUTER_MODEL env var if set and non-empty (backward compatibility)
    3) DEFAULT_OPENROUTER_MODEL (Gemini 2.5 Flash)

    Returns:
        Model ID string (e.g., "google/gemini-2.5-flash", "gpt-4", etc.)
    """
    # Check for generic LLM_MODEL first
    model = os.getenv("LLM_MODEL", "").strip()
    if model:
        return model

    # Fall back to legacy OPENROUTER_MODEL for backward compatibility
    model = os.getenv("OPENROUTER_MODEL", "").strip()
    if model:
        return model

    # Default fallback
    return DEFAULT_OPENROUTER_MODEL


def get_openrouter_model() -> str:
    """Return the OpenRouter model id from env or the project default.

    .. deprecated::
        Use :func:`get_default_model` instead. This function is preserved
        for backward compatibility with existing code.

    Priority:
    1) OPENROUTER_MODEL env var if set and non-empty
    2) DEFAULT_OPENROUTER_MODEL (Gemini 2.5 Flash)

    Returns:
        Model ID string (e.g., "google/gemini-2.5-flash")
    """
    model = os.getenv("OPENROUTER_MODEL", "").strip()
    return model if model else DEFAULT_OPENROUTER_MODEL


def get_default_model_config() -> Tuple[str, ProviderType]:
    """Get the default model ID and provider from environment or defaults.

    This is the new provider-aware configuration function. It checks:
    1. LLM_PROVIDER and LLM_MODEL environment variables (explicit provider)
    2. OPENROUTER_MODEL environment variable (backward compatibility)
    3. Falls back to DEFAULT_OPENROUTER_MODEL and DEFAULT_PROVIDER

    Environment Variables:
        LLM_PROVIDER: Provider type (bedrock, openai, openrouter, ollama)
        LLM_MODEL: Model ID for the specified provider
        OPENROUTER_MODEL: OpenRouter model ID (legacy, for backward compatibility)

    Returns:
        Tuple of (model_id, provider)

    Examples:
        >>> # Explicit provider configuration
        >>> os.environ["LLM_PROVIDER"] = "openai"
        >>> os.environ["LLM_MODEL"] = "gpt-4"
        >>> get_default_model_config()
        ('gpt-4', 'openai')

        >>> # Backward compatible OpenRouter configuration
        >>> os.environ["OPENROUTER_MODEL"] = "anthropic/claude-3.5-sonnet"
        >>> get_default_model_config()
        ('anthropic/claude-3.5-sonnet', 'openrouter')

        >>> # Default fallback
        >>> get_default_model_config()
        ('google/gemini-2.5-flash', 'openrouter')
    """
    # Check for explicit provider configuration first
    provider_env = os.getenv("LLM_PROVIDER", "").strip().lower()
    model_env = os.getenv("LLM_MODEL", "").strip()

    if provider_env and model_env:
        # Explicit provider and model specified
        return (model_env, provider_env)  # type: ignore

    # Check for legacy OpenRouter configuration
    openrouter_model = os.getenv("OPENROUTER_MODEL", "").strip()
    if openrouter_model:
        return (openrouter_model, "openrouter")

    # Check for generic model without explicit provider (try to infer)
    if model_env:
        inferred_provider = infer_provider_from_model_id(model_env)
        return (model_env, inferred_provider)

    # Fall back to default
    return (DEFAULT_OPENROUTER_MODEL, DEFAULT_PROVIDER)


__all__ = [
    "get_default_model",
    "get_openrouter_model",  # Deprecated, kept for backward compatibility
    "get_default_model_config",
    "DEFAULT_OPENROUTER_MODEL",
    "DEFAULT_PROVIDER",
]
