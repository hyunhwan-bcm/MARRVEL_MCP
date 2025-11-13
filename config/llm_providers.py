"""
LLM Provider Abstraction for Multi-Provider Testing Framework

This module provides a unified interface for creating LLM instances across
different providers: Bedrock (AWS), OpenAI, OpenRouter, Ollama, and LM Studio.

Design:
- All providers except Bedrock use the OpenAI API (via langchain_openai.ChatOpenAI)
- Bedrock uses AWS Boto3 (via langchain_aws.ChatBedrock)
- Provider-specific configuration is handled through a common interface
- Supports environment-based and explicit configuration
- API base URLs can be overridden via environment variables for flexibility

Supported Providers:
1. bedrock: AWS Bedrock (uses boto3, langchain_aws)
2. openai: OpenAI direct API (uses langchain_openai)
   - Can be used with any OpenAI API-compatible service
   - Override base URL with OPENAI_API_BASE environment variable
3. openrouter: OpenRouter API (uses langchain_openai with custom base URL)
   - Override base URL with OPENROUTER_API_BASE environment variable
4. ollama: Ollama local/remote API (uses langchain_openai with custom base URL)
   - Override base URL with OLLAMA_API_BASE environment variable
5. lm-studio: LM Studio local API (uses langchain_openai with custom base URL)
   - Default endpoint: http://localhost:1234/v1
   - Override base URL with LM_STUDIO_API_BASE environment variable

Environment Variables:
- {PROVIDER}_API_KEY: API key for the provider (OPENAI_API_KEY, OPENROUTER_API_KEY, etc.)
- {PROVIDER}_API_BASE: Override the default API base URL for the provider
- LLM_PROVIDER: Explicit provider selection (bedrock, openai, openrouter, ollama, lm-studio)
- LLM_MODEL: Model ID when using explicit provider selection

Usage:
    from config.llm_providers import create_llm_instance, get_provider_config

    # Create an LLM instance for OpenRouter
    llm = create_llm_instance(
        provider="openrouter",
        model_id="google/gemini-2.5-flash",
        temperature=0,
    )

    # Use Ollama (local or remote)
    llm = create_llm_instance(
        provider="ollama",
        model_id="llama2",
        temperature=0,
    )

    # Use LM Studio (dedicated provider)
    llm = create_llm_instance(
        provider="lm-studio",
        model_id="local-model",
        temperature=0,
    )

    # Get provider configuration
    config = get_provider_config("openrouter")
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Dict, Literal

from langchain_openai import ChatOpenAI

# Optional import for Bedrock - will be imported only when needed
# from langchain_aws import ChatBedrock


ProviderType = Literal["bedrock", "openai", "openrouter", "ollama", "lm-studio"]


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider.

    Attributes:
        name: Provider name (bedrock, openai, openrouter, ollama, lm-studio)
        api_base: Default API base URL (None for Bedrock and default OpenAI)
        api_base_env: Environment variable name for overriding API base URL
        api_key_env: Environment variable name for API key
        supports_web_search: Whether the provider supports web search
        web_search_suffix: Suffix to append to model ID for web search (e.g., ":online")
        use_openai_api: Whether to use OpenAI API compatibility
    """

    name: ProviderType
    api_base: str | None
    api_base_env: str | None
    api_key_env: str
    supports_web_search: bool = False
    web_search_suffix: str = ""
    use_openai_api: bool = True


# Provider configurations
PROVIDER_CONFIGS: Dict[ProviderType, ProviderConfig] = {
    "bedrock": ProviderConfig(
        name="bedrock",
        api_base=None,  # Uses AWS SDK
        api_base_env=None,
        api_key_env="AWS_ACCESS_KEY_ID",  # Bedrock uses AWS credentials
        supports_web_search=False,
        use_openai_api=False,
    ),
    "openai": ProviderConfig(
        name="openai",
        api_base=None,  # Uses default OpenAI endpoint
        api_base_env="OPENAI_API_BASE",  # Can override base URL for OpenAI-compatible services
        api_key_env="OPENAI_API_KEY",
        supports_web_search=False,
    ),
    "openrouter": ProviderConfig(
        name="openrouter",
        api_base="https://openrouter.ai/api/v1",
        api_base_env="OPENROUTER_API_BASE",  # Can override for testing/proxies
        api_key_env="OPENROUTER_API_KEY",
        supports_web_search=True,
        web_search_suffix=":online",
    ),
    "ollama": ProviderConfig(
        name="ollama",
        api_base="http://localhost:11434/v1",  # Default Ollama endpoint
        api_base_env="OLLAMA_API_BASE",  # Can override for remote Ollama instances
        api_key_env="OLLAMA_API_KEY",  # Optional, Ollama doesn't require auth by default
        supports_web_search=False,
    ),
    "lm-studio": ProviderConfig(
        name="lm-studio",
        api_base="http://localhost:1234/v1",  # Default LM Studio endpoint
        api_base_env="LM_STUDIO_API_BASE",  # Can override for custom ports
        api_key_env="LM_STUDIO_API_KEY",  # LM Studio accepts any key
        supports_web_search=False,
    ),
}


def get_provider_config(provider: ProviderType) -> ProviderConfig:
    """Get configuration for a specific provider.

    Args:
        provider: Provider type (bedrock, openai, openrouter, ollama)

    Returns:
        ProviderConfig for the specified provider

    Raises:
        ValueError: If provider is not supported
    """
    if provider not in PROVIDER_CONFIGS:
        raise ValueError(
            f"Unsupported provider: {provider}. "
            f"Supported providers: {', '.join(PROVIDER_CONFIGS.keys())}"
        )
    return PROVIDER_CONFIGS[provider]


def get_api_base(provider: ProviderType) -> str | None:
    """Get API base URL for a provider, checking environment variable override first.

    Args:
        provider: Provider type

    Returns:
        API base URL from environment or default configuration, or None if not applicable
    """
    config = get_provider_config(provider)

    # Check for environment variable override
    if config.api_base_env:
        env_base = os.getenv(config.api_base_env, "").strip()
        if env_base:
            return env_base

    # Return default from config
    return config.api_base


def get_api_key(provider: ProviderType) -> str | None:
    """Get API key for a provider from environment variables.

    Args:
        provider: Provider type

    Returns:
        API key from environment or None if not found
    """
    config = get_provider_config(provider)
    api_key = os.getenv(config.api_key_env, "").strip()

    # Ollama and LM Studio don't require API keys by default
    if provider == "ollama" and not api_key:
        return "ollama"  # Dummy key for compatibility

    if provider == "lm-studio" and not api_key:
        return "lm-studio"  # Dummy key for compatibility

    return api_key if api_key else None


def validate_provider_credentials(provider: ProviderType) -> bool:
    """Validate that required credentials are available for a provider.

    Args:
        provider: Provider type

    Returns:
        True if credentials are valid/available

    Raises:
        ValueError: If required credentials are missing
    """
    config = get_provider_config(provider)

    # Ollama and LM Studio don't require credentials
    if provider in ("ollama", "lm-studio"):
        return True

    # Bedrock requires AWS credentials
    if provider == "bedrock":
        if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
            raise ValueError(
                f"Missing AWS credentials for Bedrock. "
                f"Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
            )
        return True

    # Other providers require API key
    api_key = get_api_key(provider)
    if not api_key:
        raise ValueError(
            f"{config.api_key_env} not found in environment variables. "
            f"Please set it in a .env file or export it as an environment variable."
        )

    return True


def create_llm_instance(
    provider: ProviderType,
    model_id: str,
    temperature: float = 0,
    web_search: bool = False,
    **kwargs: Any,
) -> Any:
    """Create an LLM instance for the specified provider.

    This is the main factory function for creating LLM instances. It handles
    provider-specific configuration and returns the appropriate LangChain LLM object.

    Args:
        provider: Provider type (bedrock, openai, openrouter, ollama)
        model_id: Model identifier (provider-specific format)
        temperature: Temperature for sampling (0-1)
        web_search: Enable web search if supported by provider
        **kwargs: Additional provider-specific arguments

    Returns:
        LangChain LLM instance (ChatOpenAI or ChatBedrock)

    Raises:
        ValueError: If provider is not supported or credentials are missing
        ImportError: If required dependencies are not installed

    Examples:
        >>> # OpenRouter (via OpenAI API)
        >>> llm = create_llm_instance("openrouter", "google/gemini-2.5-flash")

        >>> # OpenAI direct
        >>> llm = create_llm_instance("openai", "gpt-4")

        >>> # Ollama local
        >>> llm = create_llm_instance("ollama", "llama2")

        >>> # Bedrock (AWS)
        >>> llm = create_llm_instance("bedrock", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    """
    # Validate credentials
    validate_provider_credentials(provider)

    config = get_provider_config(provider)

    # Apply web search suffix if requested and supported
    effective_model_id = model_id
    if web_search:
        if config.supports_web_search:
            effective_model_id = f"{model_id}{config.web_search_suffix}"
        else:
            # Silently ignore web search for providers that don't support it
            pass

    # Bedrock uses a different LangChain class
    if provider == "bedrock":
        try:
            from langchain_aws import ChatBedrock
            import boto3
            from botocore.config import Config
        except ImportError:
            raise ImportError(
                "langchain_aws is required for Bedrock support. "
                "Install it with: pip install langchain-aws boto3"
            )

        # Bedrock-specific configuration
        region = kwargs.pop("region_name", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))

        # Configure boto3 client with retry and connection pool settings
        # This helps handle ThrottlingException and connection pool limits
        boto_config = Config(
            region_name=region,
            retries={
                "max_attempts": 10,  # Increased from default 4
                "mode": "adaptive",  # Adaptive retry mode for better throttling handling
            },
            max_pool_connections=10,  # Match AWS Bedrock's connection limit
            connect_timeout=60,  # Longer timeout for throttled requests
            read_timeout=60,
        )

        # Create boto3 client with custom config
        bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=region,
            config=boto_config,
        )

        return ChatBedrock(
            model_id=effective_model_id,
            model_kwargs={"temperature": temperature, **kwargs.get("model_kwargs", {})},
            client=bedrock_client,
            **{k: v for k, v in kwargs.items() if k != "model_kwargs"},
        )

    # All other providers use OpenAI API
    if config.use_openai_api:
        api_key = get_api_key(provider)
        api_base = get_api_base(provider)

        # Build kwargs for ChatOpenAI
        openai_kwargs: Dict[str, Any] = {
            "model": effective_model_id,
            "temperature": temperature,
            **kwargs,
        }

        # Add API key and base URL
        openai_kwargs["openai_api_key"] = api_key

        # Set base URL if provider uses a custom endpoint or if overridden via env
        if api_base:
            openai_kwargs["openai_api_base"] = api_base

        return ChatOpenAI(**openai_kwargs)

    raise ValueError(f"Provider {provider} configuration error: no compatible API")


def infer_provider_from_model_id(model_id: str) -> ProviderType:
    """Infer provider from model ID based on naming conventions.

    This is a heuristic function to automatically detect the provider
    from the model ID format.

    Args:
        model_id: Model identifier

    Returns:
        Inferred provider type

    Examples:
        >>> infer_provider_from_model_id("google/gemini-2.5-flash")
        'openrouter'
        >>> infer_provider_from_model_id("gpt-4")
        'openai'
        >>> infer_provider_from_model_id("anthropic.claude-3-5-sonnet-20241022-v2:0")
        'bedrock'
        >>> infer_provider_from_model_id("llama2")
        'ollama'
    """
    # Bedrock models use dot notation and version suffixes
    if "." in model_id and model_id.endswith(":0"):
        return "bedrock"

    # OpenRouter models use provider/model format
    if "/" in model_id:
        return "openrouter"

    # OpenAI models use specific naming
    if model_id.startswith("gpt-") or model_id.startswith("o1-"):
        return "openai"

    # Default to Ollama for simple names
    return "ollama"


__all__ = [
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
