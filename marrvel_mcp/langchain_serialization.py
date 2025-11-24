"""
LangChain Object Serialization Utility

This module provides utilities to serialize LangChain message objects
to see what information is preserved versus lost during conversion.
"""

import json
from typing import Any, Dict, List
from datetime import datetime


def serialize_langchain_object(obj: Any) -> Dict[str, Any]:
    """
    Serialize a LangChain object to a dictionary, capturing all available properties.

    This function attempts to extract all meaningful information from a LangChain
    object (like SystemMessage, HumanMessage, AIMessage, ToolMessage, etc.) to
    understand what data is available and what might be lost during conversion.

    Args:
        obj: A LangChain object (message, tool call, etc.)

    Returns:
        Dictionary containing all serializable properties of the object
    """
    serialized = {
        "_object_type": type(obj).__name__,
        "_module": type(obj).__module__,
    }

    # Get all attributes from __dict__ if available
    if hasattr(obj, "__dict__"):
        for key, value in obj.__dict__.items():
            if key.startswith("_"):
                # Skip private attributes but note they exist
                continue
            try:
                # Try to serialize the value
                serialized[key] = _serialize_value(value)
            except Exception as e:
                serialized[key] = f"<non-serializable: {type(value).__name__}>"

    # Use dir() to find ALL public attributes (including properties, methods, etc.)
    # This ensures we don't miss anything
    all_attrs = [attr for attr in dir(obj) if not attr.startswith("_")]

    for attr in all_attrs:
        # Skip if already captured
        if attr in serialized:
            continue

        # Skip common methods that aren't data
        if attr in ["copy", "dict", "json", "parse_obj", "parse_raw", "schema",
                    "schema_json", "update_forward_refs", "validate", "construct",
                    "from_orm", "parse_file"]:
            continue

        try:
            value = getattr(obj, attr)

            # Skip methods and callables (except if they're properties that return data)
            if callable(value) and not isinstance(value, (list, dict, str, int, float, bool)):
                continue

            # Try to serialize
            serialized[attr] = _serialize_value(value)
        except Exception as e:
            # Some properties might raise exceptions when accessed
            serialized[attr] = f"<error accessing: {str(e)[:50]}>"

    # Special handling for tool calls
    if hasattr(obj, "tool_calls") and obj.tool_calls:
        serialized["tool_calls_detail"] = []
        for tc in obj.tool_calls:
            serialized["tool_calls_detail"].append(serialize_tool_call(tc))

    return serialized


def serialize_tool_call(tool_call: Any) -> Dict[str, Any]:
    """
    Serialize a tool call object to see what information it contains.

    Args:
        tool_call: A tool call object (can be dict or object)

    Returns:
        Dictionary with tool call information
    """
    if isinstance(tool_call, dict):
        return tool_call

    result = {
        "_type": type(tool_call).__name__,
    }

    # Common tool call properties
    props = ["id", "name", "args", "type", "function"]

    if hasattr(tool_call, "__dict__"):
        for key, value in tool_call.__dict__.items():
            if not key.startswith("_"):
                try:
                    result[key] = _serialize_value(value)
                except:
                    result[key] = f"<non-serializable: {type(value).__name__}>"

    for prop in props:
        if hasattr(tool_call, prop) and prop not in result:
            try:
                result[prop] = _serialize_value(getattr(tool_call, prop))
            except:
                result[prop] = f"<non-serializable>"

    return result


def _serialize_value(value: Any) -> Any:
    """
    Helper to serialize a value, handling common types.

    Args:
        value: Value to serialize

    Returns:
        Serializable version of the value
    """
    if value is None:
        return None
    elif isinstance(value, (str, int, float, bool)):
        return value
    elif isinstance(value, (list, tuple)):
        return [_serialize_value(item) for item in value]
    elif isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    elif hasattr(value, "__dict__"):
        # Try to serialize as object
        return serialize_langchain_object(value)
    else:
        # For other types, convert to string
        return str(value)


def serialize_messages_array(messages: List[Any]) -> List[Dict[str, Any]]:
    """
    Serialize an array of LangChain message objects.

    Args:
        messages: List of LangChain message objects

    Returns:
        List of dictionaries containing serialized message data
    """
    return [serialize_langchain_object(msg) for msg in messages]


def print_serialized_messages(messages: List[Any], title: str = "LangChain Messages", max_content_length: int = 200) -> None:
    """
    Print serialized messages in a readable format for debugging.

    Args:
        messages: List of LangChain message objects
        title: Title to display
        max_content_length: Maximum length of content to display (0 for unlimited)
    """
    print("=" * 80)
    print(f"{title}")
    print("=" * 80)

    serialized = serialize_messages_array(messages)

    for i, msg in enumerate(serialized):
        print(f"\n[Message {i+1}] Type: {msg.get('_object_type', 'Unknown')}")
        print("-" * 40)

        # Print each property
        for key, value in msg.items():
            if key == "_object_type":
                continue

            # Truncate long content if needed
            if key == "content" and isinstance(value, str) and max_content_length > 0:
                if len(value) > max_content_length:
                    display_value = value[:max_content_length] + f"... ({len(value)} chars total)"
                else:
                    display_value = value
            else:
                # For non-content fields or unlimited length
                if isinstance(value, (dict, list)):
                    display_value = json.dumps(value, indent=2, default=str)
                else:
                    display_value = value

            print(f"  {key}: {display_value}")

    print("\n" + "=" * 80)


def save_serialized_messages(messages: List[Any], filename: str) -> None:
    """
    Save serialized messages to a JSON file.

    Args:
        messages: List of LangChain message objects
        filename: Path to save the JSON file
    """
    serialized = serialize_messages_array(messages)

    output = {
        "timestamp": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": serialized,
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, default=str)

    print(f"✅ Serialized {len(messages)} messages to: {filename}")


def compare_with_conversation(
    messages: List[Any],
    conversation: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Compare serialized LangChain messages with conversation dictionaries
    to identify what information is lost.

    Args:
        messages: List of LangChain message objects
        conversation: List of conversation dictionaries

    Returns:
        Dictionary containing comparison analysis
    """
    serialized = serialize_messages_array(messages)

    analysis = {
        "message_count": len(messages),
        "conversation_count": len(conversation),
        "information_loss": [],
    }

    for i, (msg, conv) in enumerate(zip(serialized, conversation)):
        msg_keys = set(msg.keys())
        conv_keys = set(conv.keys())

        lost_keys = msg_keys - conv_keys - {"_object_type", "_module"}

        if lost_keys:
            loss_detail = {
                "index": i,
                "message_type": msg.get("_object_type"),
                "lost_properties": list(lost_keys),
                "lost_values": {key: msg.get(key) for key in lost_keys if msg.get(key) not in (None, "", [], {})},
            }
            analysis["information_loss"].append(loss_detail)

    return analysis


def extract_token_info(obj: Any) -> Dict[str, Any]:
    """
    Extract all token-related information from a LangChain object.

    This searches multiple possible locations where token information might be stored:
    - usage_metadata
    - response_metadata
    - token_usage (direct attribute)
    - llm_output
    - And any other attributes containing 'token' in the name

    Args:
        obj: LangChain object (typically an AIMessage)

    Returns:
        Dictionary containing all token information found
    """
    token_info = {}

    # Check usage_metadata
    if hasattr(obj, "usage_metadata") and obj.usage_metadata:
        token_info["usage_metadata"] = obj.usage_metadata

    # Check response_metadata
    if hasattr(obj, "response_metadata") and obj.response_metadata:
        metadata = obj.response_metadata
        if isinstance(metadata, dict):
            # Look for token usage in response_metadata
            if "token_usage" in metadata:
                token_info["response_metadata.token_usage"] = metadata["token_usage"]
            if "usage" in metadata:
                token_info["response_metadata.usage"] = metadata["usage"]
            # Store full response_metadata for context
            token_info["response_metadata"] = metadata

    # Check for direct token_usage attribute
    if hasattr(obj, "token_usage"):
        token_info["token_usage"] = getattr(obj, "token_usage")

    # Check llm_output (some providers use this)
    if hasattr(obj, "llm_output") and obj.llm_output:
        llm_output = obj.llm_output
        if isinstance(llm_output, dict) and "token_usage" in llm_output:
            token_info["llm_output.token_usage"] = llm_output["token_usage"]

    # Search all attributes for anything with 'token' in the name
    if hasattr(obj, "__dict__"):
        for key, value in obj.__dict__.items():
            if "token" in key.lower() and key not in token_info:
                token_info[key] = value

    # Use dir() to find any token-related properties
    for attr in dir(obj):
        if "token" in attr.lower() and not attr.startswith("_"):
            if attr not in token_info and attr not in ["token_usage", "usage_metadata"]:
                try:
                    value = getattr(obj, attr)
                    if not callable(value):
                        token_info[attr] = value
                except Exception:
                    pass

    return token_info


def print_information_loss_analysis(
    messages: List[Any],
    conversation: List[Dict[str, Any]]
) -> None:
    """
    Print an analysis of what information is lost when converting
    LangChain messages to conversation dictionaries.

    Args:
        messages: List of LangChain message objects
        conversation: List of conversation dictionaries
    """
    analysis = compare_with_conversation(messages, conversation)

    print("=" * 80)
    print("INFORMATION LOSS ANALYSIS")
    print("=" * 80)
    print(f"Total messages: {analysis['message_count']}")
    print(f"Total conversation entries: {analysis['conversation_count']}")
    print(f"Messages with information loss: {len(analysis['information_loss'])}")
    print("=" * 80)

    if analysis["information_loss"]:
        for loss in analysis["information_loss"]:
            print(f"\n[Message {loss['index']}] {loss['message_type']}")
            print(f"  Lost properties: {', '.join(loss['lost_properties'])}")
            if loss["lost_values"]:
                print("  Lost values:")
                for key, value in loss["lost_values"].items():
                    if isinstance(value, (dict, list)):
                        print(f"    {key}: {json.dumps(value, indent=6, default=str)}")
                    else:
                        print(f"    {key}: {value}")

            # Special focus on token information
            msg = messages[loss['index']]
            token_info = extract_token_info(msg)
            if token_info:
                print(f"\n  🔍 Token Information Found:")
                for key, value in token_info.items():
                    if isinstance(value, dict):
                        print(f"    {key}: {json.dumps(value, indent=6, default=str)}")
                    else:
                        print(f"    {key}: {value}")
    else:
        print("\n✅ No significant information loss detected!")

    # Print summary of token information across all messages
    print("\n" + "=" * 80)
    print("TOKEN INFORMATION SUMMARY")
    print("=" * 80)
    total_tokens_found = 0
    for i, msg in enumerate(messages):
        token_info = extract_token_info(msg)
        if token_info:
            total_tokens_found += 1
            print(f"\n[Message {i}] {type(msg).__name__}")
            for key, value in token_info.items():
                if isinstance(value, dict):
                    print(f"  {key}: {json.dumps(value, default=str)}")
                else:
                    print(f"  {key}: {value}")

    if total_tokens_found == 0:
        print("\n⚠️  No token information found in any messages")

    print("\n" + "=" * 80)
