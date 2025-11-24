"""
Tests for cost tracking utilities.
"""

import pytest
from marrvel_mcp.cost_tracking import (
    TokenUsage,
    ModelPricing,
    UsageWithCost,
    calculate_cost,
    calculate_cost_from_usage,
    get_model_pricing,
    DEFAULT_MODEL_PRICING,
)


class TestTokenUsage:
    """Tests for TokenUsage dataclass."""

    def test_token_usage_defaults(self):
        """Test default values."""
        usage = TokenUsage()
        assert usage.input_tokens == 0
        assert usage.output_tokens == 0
        assert usage.total_tokens == 0

    def test_token_usage_with_values(self):
        """Test with provided values."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        assert usage.input_tokens == 100
        assert usage.output_tokens == 50
        assert usage.total_tokens == 150

    def test_token_usage_add(self):
        """Test accumulating tokens."""
        usage = TokenUsage()
        usage.add(input_tokens=100, output_tokens=50)
        assert usage.total_tokens == 150

        usage.add(input_tokens=200, output_tokens=100)
        assert usage.input_tokens == 300
        assert usage.output_tokens == 150
        assert usage.total_tokens == 450

    def test_token_usage_to_dict(self):
        """Test conversion to dict."""
        usage = TokenUsage(input_tokens=100, output_tokens=50)
        d = usage.to_dict()
        assert d == {"input_tokens": 100, "output_tokens": 50, "total_tokens": 150}


class TestModelPricing:
    """Tests for ModelPricing dataclass."""

    def test_model_pricing_defaults(self):
        """Test default values."""
        pricing = ModelPricing()
        assert pricing.input_cost_per_million == 0.0
        assert pricing.output_cost_per_million == 0.0

    def test_model_pricing_from_config(self):
        """Test creating from config dict."""
        config = {
            "input_cost_per_million": 3.0,
            "output_cost_per_million": 15.0,
        }
        pricing = ModelPricing.from_config(config)
        assert pricing.input_cost_per_million == 3.0
        assert pricing.output_cost_per_million == 15.0

    def test_model_pricing_from_config_partial(self):
        """Test creating from partial config dict."""
        config = {"input_cost_per_million": 2.5}
        pricing = ModelPricing.from_config(config)
        assert pricing.input_cost_per_million == 2.5
        assert pricing.output_cost_per_million == 0.0


class TestUsageWithCost:
    """Tests for UsageWithCost dataclass."""

    def test_usage_with_cost_total(self):
        """Test total cost calculation."""
        usage = UsageWithCost(
            input_tokens=1000,
            output_tokens=500,
            input_cost_usd=0.003,
            output_cost_usd=0.0075,
        )
        assert usage.total_tokens == 1500
        assert usage.total_cost_usd == pytest.approx(0.0105)

    def test_usage_with_cost_to_dict(self):
        """Test conversion to dict."""
        usage = UsageWithCost(
            input_tokens=1000,
            output_tokens=500,
            input_cost_usd=0.003,
            output_cost_usd=0.0075,
        )
        d = usage.to_dict()
        assert d["input_tokens"] == 1000
        assert d["output_tokens"] == 500
        assert d["total_tokens"] == 1500
        assert d["input_cost_usd"] == pytest.approx(0.003)
        assert d["output_cost_usd"] == pytest.approx(0.0075)
        assert d["total_cost_usd"] == pytest.approx(0.0105)

    def test_format_cost_zero(self):
        """Test formatting zero cost."""
        usage = UsageWithCost()
        assert usage.format_cost() == "$0.00"

    def test_format_cost_small(self):
        """Test formatting small cost."""
        usage = UsageWithCost(input_cost_usd=0.000123)
        assert usage.format_cost() == "$0.000123"

    def test_format_cost_medium(self):
        """Test formatting medium cost."""
        usage = UsageWithCost(input_cost_usd=0.0123)
        assert usage.format_cost() == "$0.0123"

    def test_format_cost_large(self):
        """Test formatting large cost."""
        usage = UsageWithCost(input_cost_usd=12.34)
        assert usage.format_cost() == "$12.34"


class TestCalculateCost:
    """Tests for cost calculation functions."""

    def test_calculate_cost_basic(self):
        """Test basic cost calculation."""
        result = calculate_cost(
            input_tokens=1_000_000,
            output_tokens=500_000,
            input_cost_per_million=3.0,
            output_cost_per_million=15.0,
        )
        assert result.input_tokens == 1_000_000
        assert result.output_tokens == 500_000
        assert result.input_cost_usd == 3.0
        assert result.output_cost_usd == 7.5
        assert result.total_cost_usd == 10.5

    def test_calculate_cost_small_amounts(self):
        """Test cost calculation with small token amounts."""
        result = calculate_cost(
            input_tokens=1000,
            output_tokens=500,
            input_cost_per_million=3.0,
            output_cost_per_million=15.0,
        )
        assert result.input_cost_usd == pytest.approx(0.003)
        assert result.output_cost_usd == pytest.approx(0.0075)
        assert result.total_cost_usd == pytest.approx(0.0105)

    def test_calculate_cost_with_pricing_object(self):
        """Test cost calculation with ModelPricing object."""
        pricing = ModelPricing(
            input_cost_per_million=0.02,
            output_cost_per_million=0.03,
        )
        result = calculate_cost(
            input_tokens=100_000,
            output_tokens=50_000,
            pricing=pricing,
        )
        assert result.input_cost_usd == 0.002
        assert result.output_cost_usd == 0.0015
        assert result.total_cost_usd == 0.0035

    def test_calculate_cost_from_usage(self):
        """Test cost calculation from TokenUsage object."""
        usage = TokenUsage(input_tokens=100_000, output_tokens=50_000)
        pricing = ModelPricing(
            input_cost_per_million=3.0,
            output_cost_per_million=15.0,
        )
        result = calculate_cost_from_usage(usage, pricing=pricing)
        assert result.input_cost_usd == pytest.approx(0.3)
        assert result.output_cost_usd == pytest.approx(0.75)
        assert result.total_cost_usd == pytest.approx(1.05)


class TestGetModelPricing:
    """Tests for get_model_pricing function."""

    def test_known_model(self):
        """Test getting pricing for a known model."""
        pricing = get_model_pricing("gpt-4o")
        assert pricing.input_cost_per_million == 2.50
        assert pricing.output_cost_per_million == 10.00

    def test_unknown_model(self):
        """Test getting pricing for an unknown model."""
        pricing = get_model_pricing("unknown-model-xyz")
        assert pricing.input_cost_per_million == 0.0
        assert pricing.output_cost_per_million == 0.0

    def test_config_override(self):
        """Test config overriding default pricing."""
        config = {
            "input_cost_per_million": 1.23,
            "output_cost_per_million": 4.56,
        }
        pricing = get_model_pricing("gpt-4o", config=config)
        assert pricing.input_cost_per_million == 1.23
        assert pricing.output_cost_per_million == 4.56

    def test_bedrock_model(self):
        """Test Bedrock model pricing."""
        pricing = get_model_pricing("us.anthropic.claude-3-5-haiku-20241022-v1:0")
        assert pricing.input_cost_per_million == 0.80
        assert pricing.output_cost_per_million == 4.00


class TestDefaultPricing:
    """Tests for DEFAULT_MODEL_PRICING dictionary."""

    def test_openrouter_models_in_defaults(self):
        """Test OpenRouter models have pricing."""
        assert "meta-llama/llama-3.1-8b-instruct" in DEFAULT_MODEL_PRICING
        assert "qwen/qwen3-14b" in DEFAULT_MODEL_PRICING

    def test_openai_models_in_defaults(self):
        """Test OpenAI models have pricing."""
        assert "gpt-4o" in DEFAULT_MODEL_PRICING
        assert "gpt-4o-mini" in DEFAULT_MODEL_PRICING

    def test_bedrock_models_in_defaults(self):
        """Test Bedrock models have pricing."""
        assert "us.anthropic.claude-3-5-haiku-20241022-v1:0" in DEFAULT_MODEL_PRICING
        assert "us.anthropic.claude-sonnet-4-20250514-v1:0" in DEFAULT_MODEL_PRICING
