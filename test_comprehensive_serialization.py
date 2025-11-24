#!/usr/bin/env python3
"""
Comprehensive demonstration of LangChain message serialization.

This script shows ALL attributes captured from LangChain message objects,
including token information, metadata, and other properties.
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Import directly to avoid dependency issues
import importlib.util
spec = importlib.util.spec_from_file_location(
    "langchain_serialization",
    os.path.join(os.path.dirname(__file__), "marrvel_mcp", "langchain_serialization.py")
)
langchain_serialization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(langchain_serialization)

serialize_langchain_object = langchain_serialization.serialize_langchain_object
extract_token_info = langchain_serialization.extract_token_info


class MockAIMessage:
    """Enhanced mock AIMessage with comprehensive attributes."""

    def __init__(self):
        # Content
        self.content = "The BRCA1 gene is located on chromosome 17."
        self.type = "ai"

        # Token information (multiple locations)
        self.usage_metadata = {
            "input_tokens": 245,
            "output_tokens": 87,
            "total_tokens": 332
        }

        self.response_metadata = {
            "model_name": "gpt-4-turbo",
            "finish_reason": "stop",
            "system_fingerprint": "fp_abc123",
            "token_usage": {
                "prompt_tokens": 245,
                "completion_tokens": 87,
                "total_tokens": 332
            },
            "logprobs": None,
        }

        # Additional LLM-specific metadata
        self.llm_output = {
            "token_usage": {
                "prompt_tokens": 245,
                "completion_tokens": 87,
                "total_tokens": 332
            },
            "model_name": "gpt-4-turbo",
        }

        # Additional kwargs that might contain provider-specific info
        self.additional_kwargs = {
            "function_call": None,
            "tool_calls": None,
        }

        # Timing information
        self.response_time_ms = 1234

        # Other attributes
        self.id = "msg_abc123xyz"
        self.example = False


def main():
    """Demonstrate comprehensive serialization."""
    print("=" * 80)
    print("COMPREHENSIVE LANGCHAIN MESSAGE SERIALIZATION DEMO")
    print("=" * 80)
    print()

    # Create a message with rich metadata
    message = MockAIMessage()

    print("📦 Created MockAIMessage with comprehensive attributes")
    print()

    # Test 1: Full serialization
    print("=" * 80)
    print("TEST 1: Full Serialization (ALL attributes)")
    print("=" * 80)
    serialized = serialize_langchain_object(message)
    print(json.dumps(serialized, indent=2, default=str))

    # Test 2: Token information extraction
    print("\n" + "=" * 80)
    print("TEST 2: Token Information Extraction")
    print("=" * 80)
    token_info = extract_token_info(message)
    print(json.dumps(token_info, indent=2, default=str))

    # Test 3: Count attributes
    print("\n" + "=" * 80)
    print("TEST 3: Attribute Count Analysis")
    print("=" * 80)
    print(f"Total attributes captured: {len(serialized)}")
    print(f"Token-related attributes found: {len(token_info)}")
    print()
    print("Attributes captured:")
    for key in sorted(serialized.keys()):
        value_type = type(serialized[key]).__name__
        value_preview = str(serialized[key])[:50]
        print(f"  - {key:25s} ({value_type:10s}): {value_preview}")

    # Test 4: Show what would be lost
    print("\n" + "=" * 80)
    print("TEST 4: What Gets Lost in Conversation Dictionary")
    print("=" * 80)

    # Typical conversation dictionary format
    conversation_entry = {
        "role": "assistant",
        "content": message.content
    }

    print("Typical conversation format only stores:")
    print(json.dumps(conversation_entry, indent=2))

    lost_attrs = set(serialized.keys()) - set(conversation_entry.keys()) - {"_object_type", "_module"}
    print(f"\n⚠️  {len(lost_attrs)} attributes are lost:")
    for attr in sorted(lost_attrs):
        print(f"  - {attr}")

    # Test 5: Token information summary
    print("\n" + "=" * 80)
    print("TEST 5: Token Information Summary")
    print("=" * 80)

    # Extract token counts from various locations
    token_locations = []
    if "usage_metadata" in token_info:
        token_locations.append(("usage_metadata", token_info["usage_metadata"]))
    if "response_metadata.token_usage" in token_info:
        token_locations.append(("response_metadata.token_usage", token_info["response_metadata.token_usage"]))
    if "llm_output.token_usage" in token_info:
        token_locations.append(("llm_output.token_usage", token_info["llm_output.token_usage"]))

    print(f"Found token information in {len(token_locations)} locations:")
    for location, data in token_locations:
        print(f"\n  {location}:")
        if isinstance(data, dict):
            for k, v in data.items():
                print(f"    {k}: {v}")

    print("\n" + "=" * 80)
    print("✅ COMPREHENSIVE SERIALIZATION COMPLETE")
    print("=" * 80)
    print()
    print("Summary:")
    print(f"  ✓ Captured {len(serialized)} attributes from LangChain message")
    print(f"  ✓ Found token information in {len(token_locations)} locations")
    print(f"  ✓ Identified {len(lost_attrs)} attributes that would be lost")
    print()
    print("The serialization utility ensures NO information is lost!")


if __name__ == "__main__":
    main()
