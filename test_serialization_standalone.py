#!/usr/bin/env python3
"""
Standalone test script for LangChain message serialization.

This script imports the serialization module directly to avoid
dependency issues.
"""

import json
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

# Import directly from the module file to avoid __init__ dependencies
import importlib.util

spec = importlib.util.spec_from_file_location(
    "langchain_serialization",
    os.path.join(os.path.dirname(__file__), "marrvel_mcp", "langchain_serialization.py"),
)
langchain_serialization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(langchain_serialization)

# Use the functions
serialize_messages_array = langchain_serialization.serialize_messages_array
print_serialized_messages = langchain_serialization.print_serialized_messages
save_serialized_messages = langchain_serialization.save_serialized_messages
print_information_loss_analysis = langchain_serialization.print_information_loss_analysis


class MockMessage:
    """Mock LangChain message for testing."""

    def __init__(self, message_type, content, **kwargs):
        self.type = message_type
        self.content = content
        for key, value in kwargs.items():
            setattr(self, key, value)


class MockSystemMessage(MockMessage):
    def __init__(self, content):
        super().__init__("system", content)


class MockHumanMessage(MockMessage):
    def __init__(self, content):
        super().__init__("human", content)


class MockAIMessage(MockMessage):
    def __init__(self, content, **kwargs):
        super().__init__("ai", content, **kwargs)


class MockToolMessage(MockMessage):
    def __init__(self, content, tool_call_id, name):
        super().__init__("tool", content, tool_call_id=tool_call_id, name=name)


def main():
    """Run standalone serialization test."""
    print("=" * 80)
    print("LANGCHAIN MESSAGE SERIALIZATION TEST (STANDALONE)")
    print("=" * 80)
    print()

    # Create sample messages with mock objects
    messages = [
        MockSystemMessage(content="You are a helpful genetics research assistant."),
        MockHumanMessage(content="What is the function of the BRCA1 gene?"),
        MockAIMessage(
            content="Let me search for information about BRCA1.",
            tool_calls=[
                {
                    "id": "call_abc123",
                    "name": "search_gene",
                    "args": {"gene_symbol": "BRCA1"},
                }
            ],
            response_metadata={
                "model_name": "gpt-4",
                "finish_reason": "tool_calls",
                "token_usage": {"input_tokens": 50, "output_tokens": 20},
            },
            usage_metadata={"input_tokens": 50, "output_tokens": 20},
        ),
        MockToolMessage(
            content='{"gene": "BRCA1", "function": "DNA repair", "chromosome": "17"}',
            tool_call_id="call_abc123",
            name="search_gene",
        ),
        MockAIMessage(
            content="BRCA1 is a gene involved in DNA repair located on chromosome 17.",
            response_metadata={
                "model_name": "gpt-4",
                "finish_reason": "stop",
                "token_usage": {"input_tokens": 150, "output_tokens": 30},
            },
            usage_metadata={"input_tokens": 150, "output_tokens": 30},
        ),
    ]

    # Create sample conversation (what we currently store)
    conversation = [
        {"role": "system", "content": "You are a helpful genetics research assistant."},
        {"role": "user", "content": "What is the function of the BRCA1 gene?"},
        {
            "role": "assistant",
            "content": "Let me search for information about BRCA1.",
            "tool_calls": [
                {
                    "id": "call_abc123",
                    "type": "function",
                    "function": {
                        "name": "search_gene",
                        "arguments": '{"gene_symbol": "BRCA1"}',
                    },
                }
            ],
        },
        {
            "role": "tool",
            "tool_call_id": "call_abc123",
            "name": "search_gene",
            "content": {"gene": "BRCA1", "function": "DNA repair", "chromosome": "17"},
        },
        {
            "role": "assistant",
            "content": "BRCA1 is a gene involved in DNA repair located on chromosome 17.",
        },
    ]

    print(f"✅ Created {len(messages)} mock LangChain message objects")
    print(f"✅ Created {len(conversation)} conversation dictionary entries")
    print()

    # Test 1: Print serialized messages
    print("\n" + "=" * 80)
    print("TEST 1: Serialize and print messages")
    print("=" * 80)
    print_serialized_messages(messages, title="Sample LangChain Messages")

    # Test 2: Compare with conversation to find information loss
    print("\n" + "=" * 80)
    print("TEST 2: Information loss analysis")
    print("=" * 80)
    print_information_loss_analysis(messages, conversation)

    # Test 3: Save to JSON file
    print("\n" + "=" * 80)
    print("TEST 3: Save serialized messages to JSON")
    print("=" * 80)
    output_file = "/tmp/langchain_messages_serialized.json"
    save_serialized_messages(messages, output_file)

    # Show a snippet of what was saved
    with open(output_file, "r") as f:
        data = json.load(f)
        print(f"\n📊 Summary of saved data:")
        print(f"   - Timestamp: {data['timestamp']}")
        print(f"   - Message count: {data['message_count']}")
        print(f"   - First message type: {data['messages'][0]['_object_type']}")

    print("\n" + "=" * 80)
    print("✅ All serialization tests completed successfully!")
    print("=" * 80)
    print(f"\n💡 To enable serialization in production, set environment variable:")
    print(f"   export SERIALIZE_LANGCHAIN=1")
    print(f"   export SERIALIZE_LANGCHAIN_FILE=/path/to/output.json  # Optional")


if __name__ == "__main__":
    main()
