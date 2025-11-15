"""
Configuration file loading.

This module handles loading and parsing of YAML configuration files
for models and evaluator settings.
"""

from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml


def load_evaluator_config_from_yaml(
    config_path: Path | None = None,
) -> Dict[str, Any]:
    """Load only the evaluator configuration from YAML file.

    This function extracts just the evaluator config without requiring
    models to be defined. Used for single test modes that want to respect
    YAML evaluator config.

    Args:
        config_path: Path to models configuration YAML file.
                     If None, uses default models_config.yaml in mcp-llm-test directory.

    Returns:
        Dict with 'provider' and 'model' keys for evaluator, or empty dict if not found
    """
    if config_path is None:
        # Use the module's parent directory to find models_config.yaml
        config_path = Path(__file__).parent.parent / "models_config.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        config = config_data.get("config", {})
        evaluator_config = config.get("evaluator", {})

        return evaluator_config
    except Exception:
        # File not found or parse error - return empty dict
        return {}


def load_models_config(
    config_path: Path | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load models configuration from YAML file.

    Args:
        config_path: Path to models configuration YAML file.
                     If None, uses default models_config.yaml in mcp-llm-test directory.

    Returns:
        Tuple of (enabled_models, evaluator_config)
        - enabled_models: List of enabled model configurations
        - evaluator_config: Dict with 'provider' and 'model' keys for evaluator, or empty dict
    """
    if config_path is None:
        # Use the module's parent directory to find models_config.yaml
        config_path = Path(__file__).parent.parent / "models_config.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        models = config_data.get("models", [])
        config = config_data.get("config", {})
        only_enabled = config.get("only_enabled", True)

        if only_enabled:
            enabled_models = [m for m in models if m.get("enabled", False)]
        else:
            enabled_models = models

        if not enabled_models:
            raise ValueError("No enabled models found in configuration file")

        # Extract evaluator configuration if present
        evaluator_config = config.get("evaluator", {})

        return enabled_models, evaluator_config
    except Exception as e:
        raise ValueError(f"Failed to load models configuration: {e}")
