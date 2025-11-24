#!/usr/bin/env python3
"""
Quick test to verify serialized_messages flow through the evaluation pipeline.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


# Mock the key parts
class MockMessage:
    def __init__(self):
        self.content = "Test response"
        self.type = "ai"
        self.usage_metadata = {"input_tokens": 10, "output_tokens": 5}


# Test serialization
from marrvel_mcp import serialize_messages_array

messages = [MockMessage(), MockMessage()]
serialized = serialize_messages_array(messages)

print("✅ Serialization works!")
print(f"   Serialized {len(serialized)} messages")
print(f"   First message has {len(serialized[0])} attributes")
print(f"   Attributes: {list(serialized[0].keys())}")

# Check if usage_metadata is captured
if "usage_metadata" in serialized[0]:
    print(f"   ✅ Token info captured: {serialized[0]['usage_metadata']}")
else:
    print("   ❌ Token info NOT captured")

# Simulate what goes into result dict
result = {
    "question": "test",
    "response": "test response",
    "serialized_messages": serialized,
}

print(f"\n✅ Result dict structure:")
print(f"   Has serialized_messages: {('serialized_messages' in result)}")
print(f"   serialized_messages length: {len(result['serialized_messages'])}")

# Test metadata dict structure
metadata = {"serialized_messages": serialized}
extracted = metadata.get("serialized_messages", [])
print(f"\n✅ Metadata extraction:")
print(f"   Extracted length: {len(extracted)}")
print(f"   Matches original: {extracted == serialized}")
