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

    # Common LangChain message properties
    common_props = [
        "content",
        "type",
        "role",
        "name",
        "additional_kwargs",
        "response_metadata",
        "usage_metadata",
        "tool_calls",
        "tool_call_id",
        "id",
        "example",
    ]

    for prop in common_props:
        if hasattr(obj, prop):
            value = getattr(obj, prop)
            if prop not in serialized:  # Don't overwrite if already captured
                try:
                    serialized[prop] = _serialize_value(value)
                except Exception as e:
                    serialized[prop] = f"<non-serializable: {type(value).__name__}>"

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
    else:
        print("\n✅ No significant information loss detected!")

    print("\n" + "=" * 80)
