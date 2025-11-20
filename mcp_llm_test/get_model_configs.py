#!/usr/bin/env python3
"""
Helper script to extract enabled model configurations from models_config.yaml.

This script parses the YAML configuration file and outputs a JSON array of enabled
models with their provider, model ID, and optional API overrides. This is used by
the bash benchmark script to iterate through models.

Usage:
    python get_model_configs.py [--config PATH] [--all]

Output Format (JSON):
    [
        {
            "name": "Model Display Name",
            "id": "model-id-string",
            "provider": "openrouter|bedrock|openai|ollama",
            "api_key": "optional-override",
            "api_base": "optional-override",
            "skip_vanilla": false,
            "skip_web_search": false
        },
        ...
    ]
"""

import argparse
import json
import sys
from pathlib import Path

import yaml


def load_models_config(config_path=None):
    """Load and parse models_config.yaml file.

    Args:
        config_path: Optional path to config file. Defaults to models_config.yaml in script dir.

    Returns:
        Tuple of (models_list, config_dict)
    """
    if config_path is None:
        config_path = Path(__file__).parent / "models_config.yaml"
    else:
        config_path = Path(config_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    models = config.get("models", [])
    config_options = config.get("config", {})

    return models, config_options


def filter_enabled_models(models, config_options, include_all=False):
    """Filter models based on enabled flag.

    Args:
        models: List of model configurations from YAML
        config_options: Global config options (contains only_enabled flag)
        include_all: If True, ignore enabled flag and return all models

    Returns:
        List of enabled models
    """
    if include_all:
        return models

    only_enabled = config_options.get("only_enabled", True)
    if only_enabled:
        return [m for m in models if m.get("enabled", False)]
    else:
        return models


def extract_model_info(model):
    """Extract relevant fields from a model config entry.

    Args:
        model: Model configuration dictionary

    Returns:
        Dictionary with standardized fields for bash script consumption
    """
    provider = model.get("provider", "openrouter")
    api_base = model.get("api_base")

    # Apply default api_base for openrouter if not specified
    if provider == "openrouter" and not api_base:
        api_base = "https://openrouter.ai/api/v1"

    return {
        "name": model.get("name", "Unknown"),
        "id": model.get("id", ""),
        "provider": provider,
        "api_key": model.get("api_key"),
        "api_base": api_base,
        "skip_vanilla": model.get("skip_vanilla", False),
        "skip_web_search": model.get("skip_web_search", False),
    }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Extract enabled model configurations from models_config.yaml"
    )
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to models_config.yaml file. Defaults to mcp_llm_test/models_config.yaml",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Include all models, ignoring enabled flag",
    )
    parser.add_argument(
        "--format",
        choices=["json", "bash"],
        default="json",
        help="Output format: json (default) or bash (for sourcing in scripts)",
    )

    args = parser.parse_args()

    try:
        # Load configuration
        models, config_options = load_models_config(args.config)

        # Filter to enabled models
        enabled_models = filter_enabled_models(models, config_options, args.all)

        # Extract relevant info
        model_infos = [extract_model_info(m) for m in enabled_models]

        # Output in requested format
        if args.format == "json":
            print(json.dumps(model_infos, indent=2))
        elif args.format == "bash":
            # Output as bash-friendly format (one line per model, tab-separated)
            for model in model_infos:
                # Format: name|id|provider|api_key|api_base|skip_vanilla|skip_web_search
                api_key = model.get("api_key") or ""
                api_base = model.get("api_base") or ""
                skip_vanilla = "true" if model.get("skip_vanilla") else "false"
                skip_web = "true" if model.get("skip_web_search") else "false"
                print(
                    f"{model['name']}|{model['id']}|{model['provider']}|{api_key}|{api_base}|{skip_vanilla}|{skip_web}"
                )

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
