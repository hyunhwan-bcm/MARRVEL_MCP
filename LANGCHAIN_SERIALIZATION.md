# LangChain Object Serialization

This document describes the LangChain object serialization utilities added to the MARRVEL MCP codebase.

## Overview

LangChain message objects (SystemMessage, HumanMessage, AIMessage, ToolMessage, etc.) contain rich metadata that can be lost when converting to simpler dictionary representations. The serialization utilities in this package allow you to:

1. **Serialize** LangChain message arrays to see all their properties
2. **Compare** serialized messages with conversation dictionaries to identify information loss
3. **Save** serialized data to JSON files for inspection
4. **Debug** what information is being preserved vs. lost during conversion

## Key Information Often Lost

Based on our comprehensive analysis, the following information is commonly lost when converting LangChain messages to conversation dictionaries:

### For All Messages:
- `type` - The message type identifier (system, human, ai, tool)
- `_object_type` - The Python class name (e.g., SystemMessage, AIMessage)
- `_module` - The module path where the class is defined
- `id` - Unique message identifier
- `example` - Whether this is an example message

### For AI Messages (8+ attributes typically lost):

**Token Information** (captured in 3 locations):
- `usage_metadata` - Contains input_tokens, output_tokens, total_tokens
- `response_metadata.token_usage` - Contains prompt_tokens, completion_tokens, total_tokens
- `llm_output.token_usage` - Provider-specific token counts

**Response Metadata**:
- `model_name` - The specific model that generated the response (e.g., "gpt-4-turbo")
- `finish_reason` - Why the model stopped (e.g., "stop", "tool_calls", "length")
- `system_fingerprint` - Model version fingerprint
- `logprobs` - Log probabilities (if requested)

**Additional Information**:
- `additional_kwargs` - Provider-specific data (function_call, tool_calls, etc.)
- `llm_output` - Full LLM output including model name and token usage
- `response_time_ms` - Response time in milliseconds (if tracked)

### For Tool Messages:
- `type` - Message type identifier
- Metadata about tool execution timing and status

### Token Information Locations

Our **enhanced serialization** specifically searches for token information in multiple locations:
1. `usage_metadata` - LangChain's standard location
2. `response_metadata["token_usage"]` - OpenAI-style token usage
3. `llm_output["token_usage"]` - Provider-specific output
4. Any attribute with "token" in the name

This ensures **no token information is lost**, regardless of which LLM provider you're using.

## Usage

### 1. Enable Serialization in Production

Set the environment variable to enable serialization logging:

```bash
export SERIALIZE_LANGCHAIN=1
```

Optionally, save serialized messages to a file:

```bash
export SERIALIZE_LANGCHAIN_FILE=/path/to/output.json
```

### 2. Use the Serialization Functions Programmatically

```python
from marrvel_mcp import (
    serialize_messages_array,
    print_serialized_messages,
    save_serialized_messages,
    print_information_loss_analysis,
)

# Serialize messages
serialized = serialize_messages_array(messages)

# Print messages for debugging
print_serialized_messages(messages, title="My Messages")

# Save to JSON file
save_serialized_messages(messages, "output.json")

# Compare with conversation to find lost information
print_information_loss_analysis(messages, conversation)
```

### 3. Run the Test Script

A standalone test script demonstrates the serialization functionality:

```bash
python test_serialization_standalone.py
```

This will:
- Create mock LangChain message objects
- Serialize them to see all properties
- Compare with a conversation dictionary
- Show what information is lost
- Save the results to `/tmp/langchain_messages_serialized.json`

## Output Format

### Serialized Message Structure

Each serialized message includes:

```json
{
  "_object_type": "AIMessage",
  "_module": "langchain_core.messages.ai",
  "type": "ai",
  "content": "Message content here",
  "tool_calls": [...],
  "response_metadata": {
    "model_name": "gpt-4",
    "finish_reason": "stop",
    "token_usage": {
      "input_tokens": 150,
      "output_tokens": 30
    }
  },
  "usage_metadata": {
    "input_tokens": 150,
    "output_tokens": 30
  }
}
```

### Information Loss Analysis

The analysis shows which properties are lost for each message:

```
[Message 2] AIMessage
  Lost properties: usage_metadata, response_metadata, type
  Lost values:
    usage_metadata: {
      "input_tokens": 50,
      "output_tokens": 20
    }
    response_metadata: {
      "model_name": "gpt-4",
      "finish_reason": "tool_calls",
      "token_usage": {
        "input_tokens": 50,
        "output_tokens": 20
      }
    }
    type: ai
```

## API Reference

### `serialize_langchain_object(obj: Any) -> Dict[str, Any]`

Serialize a single LangChain object to a dictionary.

**Returns:** Dictionary containing all serializable properties

### `serialize_messages_array(messages: List[Any]) -> List[Dict[str, Any]]`

Serialize an array of LangChain message objects.

**Returns:** List of dictionaries containing serialized message data

### `print_serialized_messages(messages: List[Any], title: str = "LangChain Messages", max_content_length: int = 200) -> None`

Print serialized messages in a readable format for debugging.

**Args:**
- `messages` - List of LangChain message objects
- `title` - Title to display
- `max_content_length` - Maximum length of content to display (0 for unlimited)

### `save_serialized_messages(messages: List[Any], filename: str) -> None`

Save serialized messages to a JSON file.

**Args:**
- `messages` - List of LangChain message objects
- `filename` - Path to save the JSON file

### `compare_with_conversation(messages: List[Any], conversation: List[Dict[str, Any]]) -> Dict[str, Any]`

Compare serialized LangChain messages with conversation dictionaries to identify what information is lost.

**Returns:** Dictionary containing comparison analysis

### `print_information_loss_analysis(messages: List[Any], conversation: List[Dict[str, Any]]) -> None`

Print an analysis of what information is lost when converting LangChain messages to conversation dictionaries. Includes a special **Token Information Summary** section showing all token data found across all messages.

### `extract_token_info(obj: Any) -> Dict[str, Any]`

Extract all token-related information from a LangChain object. Searches multiple locations:
- `usage_metadata`
- `response_metadata.token_usage`
- `llm_output.token_usage`
- Any attribute containing 'token' in the name

**Args:**
- `obj` - LangChain object (typically an AIMessage)

**Returns:** Dictionary containing all token information found

## Integration

The serialization is automatically integrated into the agentic loop:

- **File:** `marrvel_mcp/agentic_loop.py`
- **Location:** At the end of `execute_agentic_loop()` function
- **Trigger:** Environment variable `SERIALIZE_LANGCHAIN=1`

When enabled, it will:
1. Print all serialized messages to console
2. Show information loss analysis
3. Optionally save to file if `SERIALIZE_LANGCHAIN_FILE` is set

## Example Output

```
================================================================================
LANGCHAIN MESSAGES SERIALIZATION
================================================================================

[Message 1] Type: SystemMessage
----------------------------------------
  _module: langchain_core.messages.system
  type: system
  content: You are a helpful genetics research assistant.

[Message 2] Type: AIMessage
----------------------------------------
  _module: langchain_core.messages.ai
  type: ai
  content: Let me search for information about BRCA1.
  tool_calls: [...]
  response_metadata: {
    "model_name": "gpt-4",
    "finish_reason": "tool_calls",
    "token_usage": {"input_tokens": 50, "output_tokens": 20}
  }
  usage_metadata: {"input_tokens": 50, "output_tokens": 20}

================================================================================
INFORMATION LOSS ANALYSIS
================================================================================
Total messages: 5
Total conversation entries: 5
Messages with information loss: 3

[Message 2] AIMessage
  Lost properties: usage_metadata, response_metadata, type
  Lost values:
    usage_metadata: {"input_tokens": 50, "output_tokens": 20}
    response_metadata: {
      "model_name": "gpt-4",
      "finish_reason": "tool_calls",
      "token_usage": {"input_tokens": 50, "output_tokens": 20}
    }
```

## Files Added/Modified

### New Files:
- `marrvel_mcp/langchain_serialization.py` - Serialization utilities
- `test_serialization_standalone.py` - Standalone test script
- `LANGCHAIN_SERIALIZATION.md` - This documentation

### Modified Files:
- `marrvel_mcp/__init__.py` - Added serialization exports
- `marrvel_mcp/agentic_loop.py` - Integrated serialization into agentic loop

## Benefits

1. **Debugging** - Easily see what data is in LangChain messages
2. **Transparency** - Understand what information is preserved vs. lost
3. **Optimization** - Identify opportunities to preserve more useful data
4. **Analysis** - Save and analyze message data for research purposes
5. **Troubleshooting** - Diagnose issues with LLM responses and tool calls

## Future Enhancements

Potential improvements:
- Add serialization for other LangChain objects (documents, chains, etc.)
- Create a web-based viewer for serialized data
- Add filtering options to focus on specific message types
- Implement deserialization to reconstruct LangChain objects from JSON
- Add diff utilities to compare message arrays across different runs
