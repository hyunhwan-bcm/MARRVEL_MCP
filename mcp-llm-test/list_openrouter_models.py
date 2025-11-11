#!/usr/bin/env python3
"""
List available models from OpenRouter and search for specific models.

Usage:
    python list_openrouter_models.py
    python list_openrouter_models.py --search "gpt"
"""

import argparse
import os
import requests
from dotenv import load_dotenv

load_dotenv()


def list_models(search_term=None):
    """List available models from OpenRouter."""

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        return

    print("Fetching available models from OpenRouter...")
    print("=" * 80)

    try:
        response = requests.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
        response.raise_for_status()
        data = response.json()

        models = data.get("data", [])
        print(f"\nFound {len(models)} models total")

        if search_term:
            print(f"\nSearching for models matching: '{search_term}'")
            print("=" * 80)
            matching = [m for m in models if search_term.lower() in m.get("id", "").lower()]

            if matching:
                print(f"\nFound {len(matching)} matching models:\n")
                for model in matching:
                    model_id = model.get("id", "N/A")
                    name = model.get("name", "N/A")
                    context = model.get("context_length", "N/A")
                    pricing = model.get("pricing", {})
                    prompt_price = pricing.get("prompt", "N/A")

                    print(f"ID: {model_id}")
                    print(f"  Name: {name}")
                    print(f"  Context: {context} tokens")
                    print(f"  Prompt Price: ${prompt_price}/token")
                    print()
            else:
                print(f"\n❌ No models found matching '{search_term}'")
                print("\nDid you mean one of these?")
                # Show some popular models
                popular = ["gpt-4", "gpt-3.5", "claude", "gemini"]
                for pop in popular:
                    pop_models = [m.get("id") for m in models if pop in m.get("id", "").lower()]
                    if pop_models:
                        print(f"\n{pop.upper()} models:")
                        for pm in pop_models[:5]:  # Show first 5
                            print(f"  - {pm}")

        else:
            # Show all models grouped by provider
            print("\nAll available models (showing first 50):\n")
            for i, model in enumerate(models[:50]):
                model_id = model.get("id", "N/A")
                name = model.get("name", "N/A")
                print(f"{i+1}. {model_id}")
                print(f"   {name}")

            if len(models) > 50:
                print(f"\n... and {len(models) - 50} more models")
                print("\nUse --search to filter models")

    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching models: {e}")
        return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="List and search OpenRouter models")
    parser.add_argument(
        "--search",
        type=str,
        help="Search for models containing this term (case-insensitive)",
    )
    args = parser.parse_args()

    list_models(args.search)
