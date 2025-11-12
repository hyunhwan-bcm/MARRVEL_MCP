"""
Tool Calling Module for MCP LLM Evaluation

This module handles tool-related functionality for the LangChain-based
MCP evaluation framework, including:
- Converting FastMCP tools to LangChain format
- Tool call ID management
- Tool result parsing and processing
"""

import json
import re
import uuid
from typing import Any, Dict


def convert_tool_to_langchain_format(tool: Any) -> Dict[str, Any]:
    """Converts a FastMCP tool to the LangChain/OpenAI tool format.

    Args:
        tool: FastMCP tool object to convert

    Returns:
        Dictionary in LangChain/OpenAI tool format with type, function name,
        description, and parameters
    """
    tool_dict = tool.model_dump(exclude_none=True)

    # Get the input schema which contains the parameters
    input_schema = tool_dict.get("inputSchema", {})

    return {
        "type": "function",
        "function": {
            "name": tool_dict.get("name"),
            "description": tool_dict.get("description"),
            "parameters": input_schema,
        },
    }


def ensure_tool_call_id(tool_call: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure tool call has a unique ID, adding one if needed.

    Args:
        tool_call: Tool call dictionary that may or may not have an ID

    Returns:
        Tool call dictionary with guaranteed unique ID
    """
    if "id" not in tool_call or not tool_call["id"]:
        # Create a new dict with the ID added
        return {**tool_call, "id": f"call_{uuid.uuid4().hex[:12]}"}
    return tool_call


def parse_tool_result_content(content: Any) -> Any:
    """
    Parse tool result content to extract actual data.

    Tool results often come in the format:
    "toolNameOutput(result='<JSON_STRING>')"

    This function attempts to extract and parse the nested JSON for better display.
    Converts JSON strings to objects so that escape sequences like \n and \\
    are properly handled when rendered.

    Handles multiple layers of escaping from cached data.

    Args:
        content: Raw tool result content (can be string or already parsed object)

    Returns:
        Parsed content with proper JSON structure and unescaped strings
    """
    # If content is not a string, return as-is (already parsed)
    if not isinstance(content, str):
        return content

    original_content = content

    # Strip outer whitespace
    content = content.strip()

    # If wrapped in quotes, try to unwrap one layer by parsing as JSON string
    if content.startswith('"') and content.endswith('"'):
        try:
            content = json.loads(content)
            if not isinstance(content, str):
                # Successfully parsed to object, return it
                return content
        except json.JSONDecodeError:
            pass

    # Try to match the pattern: SomeOutput(result='<JSON>')
    match = re.search(r"Output\(result='(.+)'\)\s*$", content, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            # Try to parse as JSON directly - json.loads handles escape sequences
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If direct parsing fails, try manual unescaping for non-standard formats
            # Handle: \\n -> \n, \\" -> ", \\' -> ', but preserve \\\\ -> \\
            # Do \\\\ first to avoid conflicts
            unescaped = json_str.replace("\\\\", "\x00")  # Temp placeholder for \\
            unescaped = unescaped.replace("\\n", "\n")
            unescaped = unescaped.replace('\\"', '"')
            unescaped = unescaped.replace("\\'", "'")
            unescaped = unescaped.replace("\\t", "\t")
            unescaped = unescaped.replace("\\r", "\r")
            unescaped = unescaped.replace("\x00", "\\")  # Restore single backslash
            try:
                # Try parsing the manually unescaped version
                return json.loads(unescaped)
            except json.JSONDecodeError:
                # Return the unescaped string if parsing still fails
                return unescaped

    # If content looks like JSON (starts with { or [), try to parse it
    if content.startswith("{") or content.startswith("["):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If parsing fails, return as-is
            pass

    # Return as-is if we can't parse it
    return original_content


def format_tool_call_for_conversation(tool_call_with_id: Dict[str, Any]) -> Dict[str, Any]:
    """Format a tool call for inclusion in conversation history.

    Args:
        tool_call_with_id: Tool call dictionary with ID, name, and args

    Returns:
        Formatted tool call for conversation history with OpenAI format
    """
    return {
        "id": tool_call_with_id["id"],
        "type": "function",
        "function": {
            "name": tool_call_with_id["name"],
            "arguments": json.dumps(tool_call_with_id["args"]),
        },
    }
