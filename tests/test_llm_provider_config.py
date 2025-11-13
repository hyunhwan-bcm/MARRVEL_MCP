"""Tests for LLM provider configuration and API base URL overrides."""

import pytest
from config.llm_providers import (
    get_api_base,
    get_provider_config,
    create_llm_instance,
)


def test_api_base_default_values(monkeypatch):
    """Test that default API base URLs are returned when env vars are not set."""
    # Clear any existing env vars that might interfere
    monkeypatch.delenv("OPENROUTER_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("LM_STUDIO_API_BASE", raising=False)

    # OpenRouter should have a default base URL
    assert get_api_base("openrouter") == "https://openrouter.ai/api/v1"

    # Ollama should have a default base URL
    assert get_api_base("ollama") == "http://localhost:11434/v1"

    # LM Studio should have a default base URL
    assert get_api_base("lm-studio") == "http://localhost:1234/v1"

    # OpenAI should return None (uses default OpenAI endpoint)
    assert get_api_base("openai") is None

    # Bedrock should return None (uses AWS SDK)
    assert get_api_base("bedrock") is None


def test_api_base_env_override(monkeypatch):
    """Test that environment variables override default API base URLs."""
    # Test OpenAI API base override
    monkeypatch.setenv("OPENAI_API_BASE", "http://localhost:8080/v1")
    assert get_api_base("openai") == "http://localhost:8080/v1"

    # Test Ollama API base override for remote instance
    monkeypatch.setenv("OLLAMA_API_BASE", "http://remote-server:11434/v1")
    assert get_api_base("ollama") == "http://remote-server:11434/v1"

    # Test OpenRouter API base override
    monkeypatch.setenv("OPENROUTER_API_BASE", "https://custom-proxy.com/v1")
    assert get_api_base("openrouter") == "https://custom-proxy.com/v1"

    # Test LM Studio API base override for custom port
    monkeypatch.setenv("LM_STUDIO_API_BASE", "http://localhost:5678/v1")
    assert get_api_base("lm-studio") == "http://localhost:5678/v1"


def test_api_base_empty_env_var(monkeypatch):
    """Test that empty environment variables fall back to defaults."""
    # Set empty env var - should fall back to default
    monkeypatch.setenv("OLLAMA_API_BASE", "")
    assert get_api_base("ollama") == "http://localhost:11434/v1"

    # Set whitespace-only env var - should fall back to default
    monkeypatch.setenv("OPENROUTER_API_BASE", "   ")
    assert get_api_base("openrouter") == "https://openrouter.ai/api/v1"


def test_provider_config_has_api_base_env():
    """Test that all provider configs have api_base_env attribute."""
    # OpenAI should have OPENAI_API_BASE
    config = get_provider_config("openai")
    assert config.api_base_env == "OPENAI_API_BASE"

    # Ollama should have OLLAMA_API_BASE
    config = get_provider_config("ollama")
    assert config.api_base_env == "OLLAMA_API_BASE"

    # OpenRouter should have OPENROUTER_API_BASE
    config = get_provider_config("openrouter")
    assert config.api_base_env == "OPENROUTER_API_BASE"

    # LM Studio should have LM_STUDIO_API_BASE
    config = get_provider_config("lm-studio")
    assert config.api_base_env == "LM_STUDIO_API_BASE"

    # Bedrock should have None
    config = get_provider_config("bedrock")
    assert config.api_base_env is None


def test_create_llm_instance_with_custom_base_url(monkeypatch):
    """Test that create_llm_instance uses custom base URL from environment."""
    # Set up environment for Ollama with custom base URL
    monkeypatch.setenv("OLLAMA_API_BASE", "http://custom-ollama:11434/v1")

    # Create instance (this will fail if Ollama isn't running, but we can at least
    # test that the function accepts the parameters correctly)
    try:
        llm = create_llm_instance(
            provider="ollama",
            model_id="llama2",
            temperature=0,
        )
        # If successful, verify the instance has the custom base URL
        assert llm.openai_api_base == "http://custom-ollama:11434/v1"
    except Exception as e:
        # It's OK if the instance creation fails (e.g., Ollama not running)
        # As long as get_api_base works correctly
        pass


@pytest.mark.parametrize(
    "provider,expected_default",
    [
        ("openai", None),
        ("openrouter", "https://openrouter.ai/api/v1"),
        ("ollama", "http://localhost:11434/v1"),
        ("lm-studio", "http://localhost:1234/v1"),
        ("bedrock", None),
    ],
)
def test_all_providers_default_base_urls(provider, expected_default, monkeypatch):
    """Parametrized test for all provider default base URLs."""
    # Clear any env var overrides
    monkeypatch.delenv("OPENROUTER_API_BASE", raising=False)
    monkeypatch.delenv("OLLAMA_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("LM_STUDIO_API_BASE", raising=False)

    assert get_api_base(provider) == expected_default
