"""
Agentic Loop Module for MCP LLM Evaluation

This module handles the iterative agent loop that processes multiple tool calls
and responses in the LangChain-based MCP evaluation framework. It manages:
- Tool calling iterations with LLM
- Tool result processing and conversation building
- Token counting and validation
- Error handling for tool execution
"""

import asyncio
import json
import logging
import random
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


async def invoke_with_throttle_retry(
    llm_instance,
    messages,
    max_retries: int = 5,
    initial_delay: float = 2.0,
    max_delay: float = 30.0,
    add_initial_jitter: bool = False,
):
    """
    Invoke LLM with exponential backoff for throttling exceptions.

    This wrapper handles both botocore ThrottlingException (from AWS Bedrock)
    and general rate limiting errors with exponential backoff and jitter.

    Args:
        llm_instance: LangChain LLM instance to invoke
        messages: Messages to send to the LLM
        max_retries: Maximum number of retry attempts (default: 5)
        initial_delay: Initial delay in seconds before first retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 30.0)
        add_initial_jitter: If True, add 0-1s random delay before first request.
                           If None/False, auto-detect Bedrock and add jitter for it.

    Returns:
        LLM response

    Raises:
        Last exception if all retries fail
    """
    # Auto-detect Bedrock and add initial jitter to spread out concurrent requests
    is_bedrock = "ChatBedrock" in str(type(llm_instance))
    if add_initial_jitter or (is_bedrock and add_initial_jitter is not False):
        initial_jitter = random.uniform(0, 1.0)
        await asyncio.sleep(initial_jitter)

    delay = initial_delay
    last_exception = None

    for attempt in range(max_retries + 1):
        try:
            return await llm_instance.ainvoke(messages)
        except Exception as e:
            last_exception = e

            # Check if it's a throttling exception (from botocore/AWS Bedrock)
            is_throttling = False
            error_name = type(e).__name__
            error_msg = str(e)
            error_msg_lower = error_msg.lower()

            # Debug logging to see what error we got
            logging.debug(
                f"LLM invocation failed (attempt {attempt + 1}/{max_retries + 1}): "
                f"{error_name}: {error_msg[:200]}"
            )

            # Check for throttling/rate limit indicators
            if "throttling" in error_name.lower() or "throttling" in error_msg_lower:
                is_throttling = True
            elif "rate" in error_msg_lower and "limit" in error_msg_lower:
                is_throttling = True
            elif "too many" in error_msg_lower:
                is_throttling = True
            elif "reached max retries" in error_msg_lower:
                # Boto3 exhausted its retries - we should retry at application level
                is_throttling = True

            # Only retry on throttling/rate limit errors
            if is_throttling and attempt < max_retries:
                # Add jitter to avoid thundering herd (10-30% of delay)
                jitter = delay * random.uniform(0.1, 0.3)
                sleep_time = min(delay + jitter, max_delay)

                logging.warning(
                    f"🔄 Throttling detected ({error_name}), retrying in {sleep_time:.2f}s "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )
                await asyncio.sleep(sleep_time)
                delay = min(delay * 2, max_delay)  # Exponential backoff with cap
                continue

            # For non-throttling errors or exhausted retries, raise immediately
            logging.debug(f"Non-throttling error or exhausted retries, raising: {error_name}")
            raise

    # If we get here, we exhausted all retries
    raise last_exception


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
        # Invoke LLM with current messages (with throttle retry and auto-jitter for Bedrock)
        response = await invoke_with_throttle_retry(llm_with_tools, messages)
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
