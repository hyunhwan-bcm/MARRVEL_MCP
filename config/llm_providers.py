"""
LLM Provider Abstraction for Multi-Provider Testing Framework

This module provides a unified interface for creating LLM instances across
different providers using a unified OpenAI-compatible protocol, with the
exception of Amazon Bedrock which uses AWS-specific configuration.

Design Philosophy:
- All providers except Bedrock use the unified OpenAI-compatible API
- Bedrock uses AWS Boto3 (via langchain_aws.ChatBedrock)
- Global defaults with per-model overrides for maximum flexibility
- No provider-specific environment variables (except Bedrock)

Supported Providers:
1. bedrock: AWS Bedrock (separate AWS-based configuration)
   - Uses AWS credentials: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
   - Bedrock model specified via BEDROCK_MODEL_ID or per-model override
2. All others: OpenAI-compatible API (openai, openrouter, ollama, lm-studio, groq,
   mistral, deepseek, openrouter, vllm, llama.cpp, custom inference servers, etc.)
   - Uses unified OpenAI-compatible configuration
   - No automatic provider detection or validation

Environment Variables (Global Defaults for OpenAI-compatible):
- OPENAI_API_KEY: API key for OpenAI-compatible providers (global default)
- OPENAI_API_BASE: Server address for OpenAI-compatible providers (global default)
- OPENAI_MODEL: Default model name (global default)

Environment Variables (Bedrock only):
- AWS_ACCESS_KEY_ID: AWS access key
- AWS_SECRET_ACCESS_KEY: AWS secret key
- AWS_REGION: AWS region (defaults to us-east-1)
- BEDROCK_MODEL_ID: Default Bedrock model ID

Per-Model Overrides (via function parameters):
- api_key: Override OPENAI_API_KEY for this specific model
- api_base: Override OPENAI_API_BASE for this specific model
- model: Override model name for this specific model

Resolution Rules:
1. If provider is bedrock:
   - Use AWS credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION)
   - Use BEDROCK_MODEL_ID or model parameter
   - Ignore OPENAI_* variables

2. Otherwise (OpenAI-compatible):
   - Start from global defaults (OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL)
   - Apply per-model overrides (api_key, api_base, model) if provided
   - No auto-detection of compatibility; trust the configuration

Usage:
    from config.llm_providers import create_llm_instance, get_provider_config

    # Using global defaults (OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL)
    llm = create_llm_instance(
        provider="openrouter",
        model_id="google/gemini-2.5-flash",
        temperature=0,
    )

    # Using per-model overrides
    llm = create_llm_instance(
        provider="ollama",
        model_id="llama2",
        temperature=0,
        api_base="http://localhost:11434/v1",  # Override for this model
    )

    # AWS Bedrock (separate configuration)
    llm = create_llm_instance(
        provider="bedrock",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature=0,
    )
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
        name: Provider name (bedrock, openai, openrouter, ollama, lm-studio, etc.)
        default_api_base: Default API base URL for this provider type
                         (None means use global OPENAI_API_BASE for OpenAI-compatible,
                          or AWS SDK for Bedrock)
        supports_web_search: Whether the provider supports web search
        web_search_suffix: Suffix to append to model ID for web search (e.g., ":online")
        use_openai_api: Whether to use OpenAI API compatibility (False for Bedrock only)
    """

    name: ProviderType
    default_api_base: str | None
    supports_web_search: bool = False
    web_search_suffix: str = ""
    use_openai_api: bool = True


# Provider configurations
# All OpenAI-compatible providers use global OPENAI_API_KEY and OPENAI_API_BASE
# unless overridden per-model. Only Bedrock uses separate AWS credentials.
PROVIDER_CONFIGS: Dict[ProviderType, ProviderConfig] = {
    "bedrock": ProviderConfig(
        name="bedrock",
        default_api_base=None,  # Uses AWS SDK, not HTTP endpoint
        supports_web_search=False,
        use_openai_api=False,
    ),
    "openai": ProviderConfig(
        name="openai",
        default_api_base=None,  # Uses default OpenAI endpoint (https://api.openai.com/v1)
        supports_web_search=False,
    ),
    "openrouter": ProviderConfig(
        name="openrouter",
        default_api_base="https://openrouter.ai/api/v1",
        supports_web_search=True,
        web_search_suffix=":online",
    ),
    "ollama": ProviderConfig(
        name="ollama",
        default_api_base="http://localhost:11434/v1",
        supports_web_search=False,
    ),
    "lm-studio": ProviderConfig(
        name="lm-studio",
        default_api_base="http://localhost:1234/v1",
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


def get_api_base(provider: ProviderType, api_base_override: str | None = None) -> str | None:
    """Get API base URL for a provider using unified OpenAI-compatible configuration.

    Resolution order for OpenAI-compatible providers:
    1. Per-model override (api_base_override parameter)
    2. Global default (OPENAI_API_BASE environment variable)
    3. Provider-specific default (from PROVIDER_CONFIGS)

    For Bedrock: Returns None (uses AWS SDK, not HTTP endpoint)

    Args:
        provider: Provider type
        api_base_override: Per-model API base override (optional)

    Returns:
        API base URL or None if not applicable
    """
    config = get_provider_config(provider)

    # Bedrock doesn't use HTTP endpoint
    if not config.use_openai_api:
        return None

    # 1. Per-model override has highest priority
    if api_base_override:
        return api_base_override.strip()

    # 2. Global OPENAI_API_BASE
    global_base = os.getenv("OPENAI_API_BASE", "").strip()
    if global_base:
        return global_base

    # 3. Provider-specific default
    return config.default_api_base


def get_api_key(provider: ProviderType, api_key_override: str | None = None) -> str | None:
    """Get API key for a provider using unified OpenAI-compatible configuration.

    Resolution order for OpenAI-compatible providers:
    1. Per-model override (api_key_override parameter)
    2. Global default (OPENAI_API_KEY environment variable)

    For Bedrock: Not used (uses AWS credentials instead)

    Args:
        provider: Provider type
        api_key_override: Per-model API key override (optional)

    Returns:
        API key or None if not found
    """
    config = get_provider_config(provider)

    # Bedrock uses AWS credentials, not API key
    if not config.use_openai_api:
        return None

    # 1. Per-model override has highest priority
    if api_key_override:
        return api_key_override.strip()

    # 2. Global OPENAI_API_KEY
    api_key = os.getenv("OPENAI_API_KEY", "").strip()

    # Ollama and LM Studio don't require API keys by default
    if not api_key:
        if provider == "ollama":
            return "ollama"  # Dummy key for compatibility
        if provider == "lm-studio":
            return "lm-studio"  # Dummy key for compatibility

    return api_key if api_key else None


def validate_provider_credentials(
    provider: ProviderType,
    api_key_override: str | None = None,
) -> bool:
    """Validate that required credentials are available for a provider.

    For OpenAI-compatible providers: Checks OPENAI_API_KEY (or per-model override)
    For Bedrock: Checks AWS credentials

    Args:
        provider: Provider type
        api_key_override: Per-model API key override (optional)

    Returns:
        True if credentials are valid/available

    Raises:
        ValueError: If required credentials are missing
    """
    config = get_provider_config(provider)

    # Bedrock requires AWS credentials
    if provider == "bedrock":
        if not os.getenv("AWS_ACCESS_KEY_ID") or not os.getenv("AWS_SECRET_ACCESS_KEY"):
            raise ValueError(
                "Missing AWS credentials for Bedrock. "
                "Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables."
            )
        return True

    # Ollama and LM Studio don't require credentials
    if provider in ("ollama", "lm-studio"):
        return True

    # Other OpenAI-compatible providers require API key
    api_key = get_api_key(provider, api_key_override)
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in a .env file or export it as an environment variable, "
            "or provide api_key parameter for per-model override."
        )

    return True


def create_llm_instance(
    provider: ProviderType,
    model_id: str,
    temperature: float = 0,
    web_search: bool = False,
    api_key: str | None = None,
    api_base: str | None = None,
    **kwargs: Any,
) -> Any:
    """Create an LLM instance for the specified provider with unified OpenAI-compatible configuration.

    This is the main factory function for creating LLM instances. It implements the unified
    configuration spec:
    - All OpenAI-compatible providers use OPENAI_API_KEY and OPENAI_API_BASE by default
    - Per-model overrides via api_key and api_base parameters
    - Bedrock uses separate AWS credentials

    Args:
        provider: Provider type (bedrock, openai, openrouter, ollama, lm-studio, etc.)
        model_id: Model identifier (provider-specific format)
        temperature: Temperature for sampling (0-1)
        web_search: Enable web search if supported by provider
        api_key: Per-model API key override (overrides OPENAI_API_KEY)
        api_base: Per-model API base URL override (overrides OPENAI_API_BASE)
        **kwargs: Additional provider-specific arguments

    Returns:
        LangChain LLM instance (ChatOpenAI or ChatBedrock)

    Raises:
        ValueError: If provider is not supported or credentials are missing
        ImportError: If required dependencies are not installed

    Examples:
        >>> # Using global OPENAI_API_KEY and OPENAI_API_BASE
        >>> llm = create_llm_instance("openrouter", "google/gemini-2.5-flash")

        >>> # Using per-model overrides
        >>> llm = create_llm_instance(
        ...     "ollama",
        ...     "llama2",
        ...     api_base="http://localhost:11434/v1"
        ... )

        >>> # AWS Bedrock (separate configuration)
        >>> llm = create_llm_instance("bedrock", "anthropic.claude-3-5-sonnet-20241022-v2:0")
    """
    # Validate credentials (with per-model override support)
    validate_provider_credentials(provider, api_key_override=api_key)

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
        # Get API key and base using unified configuration with per-model overrides
        resolved_api_key = get_api_key(provider, api_key_override=api_key)
        resolved_api_base = get_api_base(provider, api_base_override=api_base)

        # Build kwargs for ChatOpenAI
        openai_kwargs: Dict[str, Any] = {
            "model": effective_model_id,
            "temperature": temperature,
            "timeout": 300,  # 5 minute timeout to prevent hanging
            "max_retries": 2,  # Reduce retries to fail faster
            **kwargs,
        }

        # Add API key
        openai_kwargs["openai_api_key"] = resolved_api_key

        # Set base URL if specified (per-model override, global default, or provider default)
        if resolved_api_base:
            openai_kwargs["openai_api_base"] = resolved_api_base

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
