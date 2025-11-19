"""
LLM configuration helpers for multi-provider support.

This module centralizes environment-driven configuration for the model
used across different providers (OpenRouter, OpenAI, Bedrock, Ollama).
It maintains backward compatibility with the original OpenRouter-only setup.

All providers except Bedrock use the OpenAI API standard, making it easy to
work with OpenAI-compatible services like Ollama, LM Studio, and others.

Contract:
- Input: environment variables (OPENROUTER_MODEL, LLM_PROVIDER, etc.)
- Output: model id and provider configuration
- Fallback: defaults to Gemini 2.5 Flash via OpenRouter

Environment Variables for Provider Configuration:
- LLM_PROVIDER: Provider type (bedrock, openai, openrouter, ollama, lm-studio)
- LLM_MODEL: Model ID for the specified provider
- OPENROUTER_MODEL: OpenRouter model ID (legacy, for backward compatibility)

Environment Variables for API Access:
- {PROVIDER}_API_KEY: API key (e.g., OPENAI_API_KEY, OLLAMA_API_KEY, LM_STUDIO_API_KEY)
- {PROVIDER}_API_BASE: Override default base URL (e.g., OPENAI_API_BASE, OLLAMA_API_BASE, LM_STUDIO_API_BASE)

Examples:
    # Use Ollama locally
    export LLM_PROVIDER=ollama
    export LLM_MODEL=llama2
    # OLLAMA_API_BASE defaults to http://localhost:11434/v1

    # Use LM Studio
    export LLM_PROVIDER=lm-studio
    export LLM_MODEL=local-model
    # LM_STUDIO_API_BASE defaults to http://localhost:1234/v1

    # Use remote Ollama instance
    export LLM_PROVIDER=ollama
    export LLM_MODEL=llama2
    export OLLAMA_API_BASE=http://remote-server:11434/v1

Migration Notes:
- Original `get_openrouter_model()` function is preserved for backward compatibility
- New `get_default_model_config()` function provides provider-aware configuration
- Existing code using `get_openrouter_model()` will continue to work unchanged
"""

from __future__ import annotations

import os
from typing import Tuple

from config.llm_providers import ProviderType, infer_provider_from_model_id


# Default model: latest Gemini 2.5 variant with reliable tool support
DEFAULT_MODEL = "google/gemini-2.5-flash"
DEFAULT_PROVIDER: ProviderType = "openrouter"

# Evaluation model: used for evaluating/classifying responses
EVALUATION_MODEL = "google/gemini-2.5-pro"
EVALUATION_PROVIDER: ProviderType = "openrouter"


def get_openrouter_model() -> str:
    """Return the OpenRouter model id from env or the project default.

    This function is preserved for backward compatibility with existing code.

    Priority:
    1) OPENROUTER_MODEL env var if set and non-empty
    2) DEFAULT_MODEL (Gemini 2.5 Flash)

    Returns:
        Model ID string (e.g., "google/gemini-2.5-flash")
    """
    model = os.getenv("OPENROUTER_MODEL", "").strip()
    return model if model else DEFAULT_MODEL


def get_default_model_config() -> Tuple[str, ProviderType]:
    """Get the default model ID and provider from environment or defaults.

    This is the new provider-aware configuration function. It checks:
    1. LLM_PROVIDER and LLM_MODEL environment variables (explicit provider)
    2. OPENROUTER_MODEL environment variable (backward compatibility)
    3. Falls back to DEFAULT_MODEL and DEFAULT_PROVIDER

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

    # If both are set, use them
    if provider_env and model_env:
        return (model_env, provider_env)  # type: ignore

    # Check for backward compatible OPENROUTER_MODEL
    openrouter_model = os.getenv("OPENROUTER_MODEL", "").strip()
    if openrouter_model:
        return (openrouter_model, "openrouter")

    # Fall back to defaults
    return (DEFAULT_MODEL, DEFAULT_PROVIDER)


def get_evaluation_model_config() -> Tuple[str, ProviderType]:
    """Get the evaluation model ID and provider from environment or defaults.

    This function returns the model configuration used for evaluating/classifying
    test responses. It checks:
    1. EVALUATION_PROVIDER and EVALUATION_MODEL environment variables
    2. Falls back to EVALUATION_MODEL and EVALUATION_PROVIDER constants

    Environment Variables:
        EVALUATION_PROVIDER: Provider type for evaluation (bedrock, openai, openrouter, ollama)
        EVALUATION_MODEL: Model ID for evaluation

    Returns:
        Tuple of (model_id, provider)

    Examples:
        >>> # Custom evaluation model
        >>> os.environ["EVALUATION_PROVIDER"] = "openai"
        >>> os.environ["EVALUATION_MODEL"] = "gpt-4o"
        >>> get_evaluation_model_config()
        ('gpt-4o', 'openai')

        >>> # Default evaluation model
        >>> get_evaluation_model_config()
        ('google/gemini-2.5-pro', 'openrouter')
    """
    # Check for explicit evaluation configuration
    provider_env = os.getenv("EVALUATION_PROVIDER", "").strip().lower()
    model_env = os.getenv("EVALUATION_MODEL", "").strip()

    # If both are set, use them
    if provider_env and model_env:
        return (model_env, provider_env)  # type: ignore

    # Fall back to defaults
    return (EVALUATION_MODEL, EVALUATION_PROVIDER)


__all__ = [
    "get_openrouter_model",
    "get_default_model_config",
    "get_evaluation_model_config",
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "EVALUATION_MODEL",
    "EVALUATION_PROVIDER",
]
