"""
Agentic Loop Module for MCP LLM Evaluation

This module handles the iterative agent loop that processes multiple tool calls
and responses in the LangChain-based MCP evaluation framework. It manages:
- Tool calling iterations with LLM
- Tool result processing and conversation building
- Token counting and validation
- Error handling for tool execution
"""

import json
from typing import Any, Dict, List, Tuple

from fastmcp.client import Client
from langchain_core.messages import ToolMessage
import tiktoken

from .tool_calling import (
    ensure_tool_call_id,
    format_tool_call_for_conversation,
    parse_tool_result_content,
)


class TokenLimitExceeded(Exception):
    """Exception raised when token count exceeds maximum allowed."""

    def __init__(self, token_count: int):
        super().__init__(f"TOKEN_LIMIT_EXCEEDED: {token_count}")
        self.token_count = token_count


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string using tiktoken.
    Uses gpt-4 encoding as a reasonable approximation for most models.

    Args:
        text: Text string to count tokens for
        model: Model name for tiktoken encoding (default: gpt-4)

    Returns:
        Number of tokens in the text
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base encoding if model not found
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def validate_token_count(text: str, max_tokens: int = 100_000) -> Tuple[bool, int]:
    """
    Validate that text doesn't exceed maximum token count.

    Args:
        text: Text to validate
        max_tokens: Maximum allowed tokens (default: 100,000)

    Returns:
        Tuple of (is_valid, token_count) where is_valid is True if within limit
    """
    token_count = count_tokens(text)
    return token_count <= max_tokens, token_count


async def execute_agentic_loop(
    mcp_client: Client,
    llm_with_tools: Any,
    messages: List[Any],
    conversation: List[Dict[str, Any]],
    tool_history: List[Dict[str, Any]],
    max_tokens: int = 100_000,
    max_iterations: int = 10,
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Execute the agentic loop that iteratively calls tools until a final response is reached.

    This function manages the core agent loop:
    1. Invoke LLM with current messages
    2. If tool calls present, execute them and add results to messages
    3. Repeat until no more tool calls or max iterations reached
    4. Return final response

    Args:
        mcp_client: MCP client for executing tool calls
        llm_with_tools: LLM instance with tools bound
        messages: LangChain message list (SystemMessage, HumanMessage, etc.)
        conversation: Conversation history for tracking (will be modified in-place)
        tool_history: Tool call history for tracking (will be modified in-place)
        max_tokens: Maximum allowed tokens for tool results (default: 100,000)
        max_iterations: Maximum iterations for agentic loop (default: 10)

    Returns:
        Tuple of:
        - final_response: Final text response from LLM
        - tool_history: Updated list of tool calls executed
        - conversation: Updated conversation history
        - tokens_used: Total tokens used in conversation

    Raises:
        TokenLimitExceeded: If tool result exceeds max_tokens
    """
    for iteration in range(max_iterations):
        # Invoke LLM with current messages
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        # Check if there are tool calls
        if response.tool_calls:
            # Ensure all tool calls have unique IDs
            tool_calls_with_ids = [ensure_tool_call_id(tc) for tc in response.tool_calls]

            # Store assistant message with tool calls in conversation
            assistant_msg = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [format_tool_call_for_conversation(tc) for tc in tool_calls_with_ids],
            }
            conversation.append(assistant_msg)

            # Execute each tool call
            for tool_call in tool_calls_with_ids:
                function_name = tool_call["name"]
                function_args = tool_call["args"]
                tool_call_id = tool_call["id"]

                tool_history.append({"name": function_name, "args": function_args})

                try:
                    # Call the MCP tool
                    tool_result = await mcp_client.call_tool(function_name, function_args)

                    # Serialize tool result to JSON string
                    if isinstance(tool_result.data, str):
                        content = tool_result.data
                    else:
                        content = json.dumps(tool_result.data, default=str)

                    # Validate token count for tool result
                    is_valid, token_count = validate_token_count(content, max_tokens)
                    if not is_valid:
                        # Stop evaluation immediately and signal token exceed
                        raise TokenLimitExceeded(token_count)

                    # Create LangChain ToolMessage
                    tool_message = ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    messages.append(tool_message)

                    # Store in conversation history with parsed content for better JSON display
                    parsed_content = parse_tool_result_content(content)
                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": parsed_content,
                        }
                    )
                except TokenLimitExceeded:
                    # Re-raise TokenLimitExceeded to stop evaluation immediately
                    raise
                except Exception as e:
                    # Handle tool execution error (but not TokenLimitExceeded)
                    error_content = json.dumps({"error": str(e)})
                    tool_message = ToolMessage(
                        content=error_content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    messages.append(tool_message)

                    # Store parsed error content in conversation
                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": {"error": str(e)},
                        }
                    )
        else:
            # No more tool calls - we have the final response
            final_content = response.content if hasattr(response, "content") else str(response)
            conversation.append({"role": "assistant", "content": final_content})

            # Compute total tokens used based on conversation contents
            try:
                conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
                tokens_total = count_tokens(conv_text)
            except Exception:
                tokens_total = 0

            return final_content, tool_history, conversation, tokens_total

    # If we hit max iterations without getting a final response, return the last message
    if len(messages) > 2:  # More than just system and user messages
        last_msg = messages[-1]
        final_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    else:
        final_content = "No response generated after max iterations"

    # Always append to conversation for consistency
    conversation.append({"role": "assistant", "content": final_content})
    try:
        conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
        tokens_total = count_tokens(conv_text)
    except Exception:
        tokens_total = 0

    return final_content, tool_history, conversation, tokens_total
