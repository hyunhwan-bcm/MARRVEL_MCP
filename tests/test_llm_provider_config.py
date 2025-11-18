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
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)
    monkeypatch.delenv("LM_STUDIO_API_BASE", raising=False)

    # OpenRouter should have a default base URL
    assert get_api_base("openrouter") == "https://openrouter.ai/api/v1"

    # OpenAI should return None (uses default OpenAI endpoint)
    assert get_api_base("openai") is None

    # Bedrock should return None (uses AWS SDK)
    assert get_api_base("bedrock") is None


@pytest.mark.parametrize(
    "provider,expected_default",
    [
        ("openai", None),
        ("openrouter", "https://openrouter.ai/api/v1"),
        ("bedrock", None),
    ],
)
def test_all_providers_default_base_urls(provider, expected_default, monkeypatch):
    """Parametrized test for all provider default base URLs."""
    # Clear any env var overrides
    monkeypatch.delenv("OPENROUTER_API_BASE", raising=False)
    monkeypatch.delenv("OPENAI_API_BASE", raising=False)

    assert get_api_base(provider) == expected_default
