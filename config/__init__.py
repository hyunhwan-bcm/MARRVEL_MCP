"""
Configuration package for LLM providers and models.

This package contains modules for managing LLM provider configuration and model selection
across different providers (Bedrock, OpenAI, OpenRouter, Ollama, LM Studio).
"""

from config.llm_config import (
    DEFAULT_MODEL,
    DEFAULT_PROVIDER,
    EVALUATION_MODEL,
    EVALUATION_PROVIDER,
    get_default_model_config,
    get_evaluation_model_config,
    get_openrouter_model,
)
from config.llm_providers import (
    PROVIDER_CONFIGS,
    ProviderConfig,
    ProviderType,
    create_llm_instance,
    get_api_base,
    get_api_key,
    get_provider_config,
    infer_provider_from_model_id,
    validate_provider_credentials,
)

__all__ = [
    # From llm_config
    "get_openrouter_model",
    "get_default_model_config",
    "get_evaluation_model_config",
    "DEFAULT_MODEL",
    "DEFAULT_PROVIDER",
    "EVALUATION_MODEL",
    "EVALUATION_PROVIDER",
    # From llm_providers
    "ProviderType",
    "ProviderConfig",
    "PROVIDER_CONFIGS",
    "get_provider_config",
    "get_api_base",
    "get_api_key",
    "validate_provider_credentials",
    "create_llm_instance",
    "infer_provider_from_model_id",
]
