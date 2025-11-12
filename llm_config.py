"""
LLM configuration helpers for OpenRouter.

This module centralizes environment-driven configuration for the model
used via OpenRouter. It allows selecting any provider/model pair using
an environment variable while keeping a sensible default for local runs.

Contract:
- Input: environment variable OPENROUTER_MODEL (optional)
- Output: fully-qualified OpenRouter model id (e.g., "google/gemini-2.5-flash")
- Fallback: defaults to Gemini 2.5 Flash when env var is unset/empty

For evaluation/judging:
- Input: environment variable EVALUATOR_MODEL (optional)
- Output: fully-qualified OpenRouter model id for evaluation
- Fallback: defaults to Gemini 2.5 Pro for consistent evaluation

Notes:
- We intentionally default to Gemini 2.5 (latest requested by project)
  and NOT to any older 1.5 variants.
- The evaluator model is separate from the tested model to ensure
  consistent evaluation across different test runs.
"""

from __future__ import annotations

import os


# Default model: latest Gemini 2.5 variant with reliable tool support
DEFAULT_OPENROUTER_MODEL = "google/gemini-2.5-flash"

# Default evaluator model: Gemini 2.5 Pro for consistent evaluation
DEFAULT_EVALUATOR_MODEL = "google/gemini-2.5-pro"


def get_openrouter_model() -> str:
    """Return the OpenRouter model id from env or the project default.

    Priority:
    1) OPENROUTER_MODEL env var if set and non-empty
    2) DEFAULT_OPENROUTER_MODEL (Gemini 2.5 Flash)
    """
    model = os.getenv("OPENROUTER_MODEL", "").strip()
    return model if model else DEFAULT_OPENROUTER_MODEL


def get_evaluator_model() -> str:
    """Return the evaluator model id from env or the project default.

    This model is used for evaluation/judging responses in the test harness.
    It should be kept separate from the tested model to ensure consistent
    evaluation across different test runs.

    Priority:
    1) EVALUATOR_MODEL env var if set and non-empty
    2) DEFAULT_EVALUATOR_MODEL (Gemini 2.5 Pro)
    """
    model = os.getenv("EVALUATOR_MODEL", "").strip()
    return model if model else DEFAULT_EVALUATOR_MODEL


__all__ = [
    "get_openrouter_model",
    "get_evaluator_model",
    "DEFAULT_OPENROUTER_MODEL",
    "DEFAULT_EVALUATOR_MODEL",
]
