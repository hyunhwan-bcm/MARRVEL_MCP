"""
Cost tracking utilities for LLM API usage.

This module provides functions to calculate and track costs based on
token usage and model pricing.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class TokenUsage:
    """Tracks token usage with separate input/output counts."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.input_tokens + self.output_tokens

    def add(self, input_tokens: int = 0, output_tokens: int = 0) -> None:
        """Accumulate token counts."""
        self.input_tokens += input_tokens
        self.output_tokens += output_tokens

    def to_dict(self) -> Dict[str, int]:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
        }


@dataclass
class ModelPricing:
    """Pricing information for a model."""

    input_cost_per_million: float = 0.0
    output_cost_per_million: float = 0.0

    @classmethod
    def from_config(cls, config: Dict) -> "ModelPricing":
        """Create ModelPricing from a model config dict."""
        return cls(
            input_cost_per_million=config.get("input_cost_per_million", 0.0),
            output_cost_per_million=config.get("output_cost_per_million", 0.0),
        )


@dataclass
class UsageWithCost:
    """Complete usage information including tokens and cost."""

    input_tokens: int = 0
    output_tokens: int = 0
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0

    @property
    def total_tokens(self) -> int:
        """Total tokens (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def total_cost_usd(self) -> float:
        """Total cost in USD."""
        return self.input_cost_usd + self.output_cost_usd

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "input_cost_usd": self.input_cost_usd,
            "output_cost_usd": self.output_cost_usd,
            "total_cost_usd": self.total_cost_usd,
        }

    def format_cost(self) -> str:
        """Format cost as a readable string."""
        if self.total_cost_usd == 0:
            return "$0.00"
        elif self.total_cost_usd < 0.01:
            return f"${self.total_cost_usd:.6f}"
        elif self.total_cost_usd < 1.0:
            return f"${self.total_cost_usd:.4f}"
        else:
            return f"${self.total_cost_usd:.2f}"


def calculate_cost(
    input_tokens: int,
    output_tokens: int,
    pricing: Optional[ModelPricing] = None,
    input_cost_per_million: float = 0.0,
    output_cost_per_million: float = 0.0,
) -> UsageWithCost:
    """
    Calculate cost based on token usage and pricing.

    Args:
        input_tokens: Number of input/prompt tokens
        output_tokens: Number of output/completion tokens
        pricing: ModelPricing object (optional, takes precedence)
        input_cost_per_million: Cost per 1M input tokens in USD
        output_cost_per_million: Cost per 1M output tokens in USD

    Returns:
        UsageWithCost object with tokens and calculated costs
    """
    if pricing is not None:
        input_cost_per_million = pricing.input_cost_per_million
        output_cost_per_million = pricing.output_cost_per_million

    input_cost = (input_tokens / 1_000_000) * input_cost_per_million
    output_cost = (output_tokens / 1_000_000) * output_cost_per_million

    return UsageWithCost(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost_usd=input_cost,
        output_cost_usd=output_cost,
    )


def calculate_cost_from_usage(
    usage: TokenUsage,
    pricing: Optional[ModelPricing] = None,
    input_cost_per_million: float = 0.0,
    output_cost_per_million: float = 0.0,
) -> UsageWithCost:
    """
    Calculate cost from a TokenUsage object.

    Args:
        usage: TokenUsage object with input/output token counts
        pricing: ModelPricing object (optional, takes precedence)
        input_cost_per_million: Cost per 1M input tokens in USD
        output_cost_per_million: Cost per 1M output tokens in USD

    Returns:
        UsageWithCost object with tokens and calculated costs
    """
    return calculate_cost(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        pricing=pricing,
        input_cost_per_million=input_cost_per_million,
        output_cost_per_million=output_cost_per_million,
    )


# Default pricing for common models (can be overridden via config)
DEFAULT_MODEL_PRICING: Dict[str, ModelPricing] = {
    # OpenRouter models
    "meta-llama/llama-3.2-3b-instruct": ModelPricing(0.03, 0.06),
    "meta-llama/llama-3.1-8b-instruct": ModelPricing(0.02, 0.03),
    "qwen/qwen3-14b": ModelPricing(0.05, 0.22),
    "openai/gpt-oss-20b": ModelPricing(0.03, 0.14),
    "openai/gpt-oss-120b": ModelPricing(0.04, 0.22),
    # OpenAI models
    "gpt-4o": ModelPricing(2.50, 10.00),
    "gpt-4o-mini": ModelPricing(0.15, 0.60),
    "gpt-4-turbo": ModelPricing(10.00, 30.00),
    "gpt-3.5-turbo": ModelPricing(0.50, 1.50),
    # Bedrock Claude models
    "us.anthropic.claude-3-5-sonnet-20241022-v2:0": ModelPricing(3.00, 15.00),
    "us.anthropic.claude-3-5-haiku-20241022-v1:0": ModelPricing(0.80, 4.00),
    "us.anthropic.claude-sonnet-4-20250514-v1:0": ModelPricing(3.00, 15.00),
}


def get_model_pricing(model_id: str, config: Optional[Dict] = None) -> ModelPricing:
    """
    Get pricing for a model.

    Args:
        model_id: Model identifier
        config: Optional model config dict with pricing fields

    Returns:
        ModelPricing object (defaults to zero if unknown)
    """
    # Config takes precedence
    if config is not None:
        if config.get("input_cost_per_million") or config.get("output_cost_per_million"):
            return ModelPricing.from_config(config)

    # Check default pricing
    if model_id in DEFAULT_MODEL_PRICING:
        return DEFAULT_MODEL_PRICING[model_id]

    # Unknown model - return zero pricing
    return ModelPricing(0.0, 0.0)
