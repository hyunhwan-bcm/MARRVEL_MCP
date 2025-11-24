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
import os
from typing import Any, Dict, List, Tuple

from fastmcp.client import Client
from langchain_core.messages import ToolMessage
import tiktoken

from .tool_calling import (
    ensure_tool_call_id,
    format_tool_call_for_conversation,
    parse_tool_result_content,
)
from .langchain_serialization import (
    print_serialized_messages,
    save_serialized_messages,
    print_information_loss_analysis,
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

    # Allow override of connection-error specific max backoff via env var
    # LLM_CONN_MAX_BACKOFF: caps exponential backoff for classified connection errors (default 15s)
    try:
        conn_max_backoff = float(os.getenv("LLM_CONN_MAX_BACKOFF", "15"))
    except ValueError:
        conn_max_backoff = 15.0

    if os.getenv("OPENROUTER_TRACE") or os.getenv("LLM_TRACE"):
        logging.warning(
            "[LLM-TRACE] Backoff settings initial_delay=%.2f max_delay=%.2f conn_max_backoff=%.2f max_retries=%d",
            initial_delay,
            max_delay,
            conn_max_backoff,
            max_retries,
        )

    for attempt in range(max_retries + 1):
        try:
            # Log the actual endpoint being used
            if attempt == 0:  # Only log on first attempt
                # Try multiple attributes where the endpoint might be stored
                endpoint = (
                    getattr(llm_instance, "openai_api_base", None)
                    or getattr(llm_instance, "base_url", None)
                    or (
                        hasattr(llm_instance, "client")
                        and getattr(llm_instance.client, "base_url", None)
                    )
                    or "https://api.openai.com/v1 (default)"
                )
                model_name = getattr(llm_instance, "model_name", "unknown")
                # Suppress invoke banner when QUIET/LLM_QUIET env set; downgrade to debug by default
                if not (os.getenv("QUIET") or os.getenv("LLM_QUIET")):
                    logging.debug(f"🌐 Invoking LLM | model={model_name} endpoint={endpoint}")

            result = await llm_instance.ainvoke(messages)
            if os.getenv("OPENROUTER_TRACE") or os.getenv("LLM_TRACE"):
                logging.warning(
                    "[LLM-TRACE] Successful invoke attempt=%d tokens_in=%s tool_calls=%d",
                    attempt + 1,
                    getattr(result, "usage_metadata", {}).get("input_tokens", "?"),
                    len(getattr(result, "tool_calls", []) or []),
                )
            return result
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

            # Determine classification (throttling vs connection)
            classification = None
            name_lower = error_name.lower()

            throttling_indicators = [
                "throttling",
                "rate limit",
                "too many",
                "reached max retries",
            ]
            connection_indicators = [
                "apiconnectionerror",
                "connection error",
                "connecttimeout",
                "timeout",
            ]

            if any(ind in name_lower or ind in error_msg_lower for ind in throttling_indicators):
                classification = "throttling"
            elif any(ind in name_lower or ind in error_msg_lower for ind in connection_indicators):
                classification = "connection"

            # Try to refine using SDK exception types if available
            try:
                import openai  # type: ignore

                if isinstance(e, openai.APIConnectionError):
                    classification = "connection"
                if isinstance(e, openai.RateLimitError):
                    classification = "throttling"
            except Exception:
                pass

            if classification == "throttling":
                is_throttling = True
            elif classification == "connection":
                # Retry connection errors (transient network issues) with capped backoff
                is_throttling = True  # reuse same loop
                # Clamp delay growth for connection errors using env-configurable limit
                max_delay = min(max_delay, conn_max_backoff)
                if os.getenv("OPENROUTER_TRACE") or os.getenv("LLM_TRACE"):
                    logging.warning(
                        "[LLM-TRACE] Connection error backoff clamp applied max_delay=%.2f (conn_max_backoff=%.2f)",
                        max_delay,
                        conn_max_backoff,
                    )

            if classification:
                logging.warning(
                    f"🔍 Transient error classified as '{classification}': {error_name} | Will retry"
                )
                logging.warning(f"   ↳ Error detail: {error_msg[:300]}")
                logging.debug(f"Error message detail (full): {error_msg[:500]}")

            if os.getenv("OPENROUTER_TRACE") or os.getenv("LLM_TRACE"):
                logging.warning(
                    "[LLM-TRACE] Invoke failure attempt=%d type=%s classification=%s will_retry=%s msg=%s",
                    attempt + 1,
                    error_name,
                    classification or "unknown",
                    is_throttling and attempt < max_retries,
                    error_msg[:200],
                )

            # Only retry on throttling/rate limit errors
            if is_throttling and attempt < max_retries:
                # Add jitter to avoid thundering herd (10-30% of delay)
                jitter = delay * random.uniform(0.1, 0.3)
                sleep_time = min(delay + jitter, max_delay)

                logging.warning(
                    f"🔄 Retry scheduled in {sleep_time:.2f}s "
                    f"(attempt {attempt + 1}/{max_retries + 1}, classification={classification})"
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
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int]]:
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
        - usage: Dict with token usage {input_tokens, output_tokens, total_tokens}

    Raises:
        TokenLimitExceeded: If tool result exceeds max_tokens
    """
    # Accumulate server-reported token usage across all LLM calls
    total_input_tokens = 0
    total_output_tokens = 0

    for iteration in range(max_iterations):
        # Invoke LLM with current messages (with throttle retry and auto-jitter for Bedrock)
        response = await invoke_with_throttle_retry(llm_with_tools, messages)
        messages.append(response)

        # Accumulate server-reported token usage from this call
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            usage = response.usage_metadata
            total_input_tokens += usage.get("input_tokens", 0)
            total_output_tokens += usage.get("output_tokens", 0)
            logging.debug(
                f"[Token Tracking] Iteration {iteration + 1}: "
                f"input={usage.get('input_tokens', 0)}, output={usage.get('output_tokens', 0)}, "
                f"cumulative_total={total_input_tokens + total_output_tokens}"
            )

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

            # Use accumulated server-reported tokens; fallback to tiktoken if server didn't report
            tokens_total = total_input_tokens + total_output_tokens
            if tokens_total == 0:
                # Fallback to tiktoken-based estimate if server didn't report usage
                try:
                    conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
                    tokens_total = count_tokens(conv_text)
                    # Split evenly for fallback (rough approximation)
                    total_input_tokens = tokens_total // 2
                    total_output_tokens = tokens_total - total_input_tokens
                    logging.debug(
                        "[Token Tracking] No server-reported tokens, using tiktoken fallback: %d",
                        tokens_total,
                    )
                except Exception:
                    tokens_total = 0

            # Serialize and log LangChain messages if debug serialization is enabled
            if os.getenv("SERIALIZE_LANGCHAIN"):
                logging.info("\n" + "=" * 80)
                logging.info("🔍 LANGCHAIN MESSAGES SERIALIZATION")
                logging.info("=" * 80)

                # Print serialized messages
                print_serialized_messages(messages, title="LangChain Messages Array")

                # Compare with conversation to identify information loss
                print_information_loss_analysis(messages, conversation)

                # Save to file if requested
                if os.getenv("SERIALIZE_LANGCHAIN_FILE"):
                    output_path = os.getenv("SERIALIZE_LANGCHAIN_FILE")
                    save_serialized_messages(messages, output_path)

            return final_content, tool_history, conversation, tokens_total
            logging.debug(
                "[Token Tracking] Final: input=%d, output=%d, total=%d",
                total_input_tokens,
                total_output_tokens,
                tokens_total,
            )
            usage = {
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "total_tokens": tokens_total,
            }
            return final_content, tool_history, conversation, tokens_total

    # If we hit max iterations without getting a final response, return the last message
    if len(messages) > 2:  # More than just system and user messages
        last_msg = messages[-1]
        final_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    else:
        final_content = "No response generated after max iterations"

    # Always append to conversation for consistency
    conversation.append({"role": "assistant", "content": final_content})

    # Serialize and log LangChain messages if debug serialization is enabled
    if os.getenv("SERIALIZE_LANGCHAIN"):
        logging.info("\n" + "=" * 80)
        logging.info("🔍 LANGCHAIN MESSAGES SERIALIZATION")
        logging.info("=" * 80)

        # Print serialized messages
        print_serialized_messages(messages, title="LangChain Messages Array")

        # Compare with conversation to identify information loss
        print_information_loss_analysis(messages, conversation)

        # Save to file if requested
        if os.getenv("SERIALIZE_LANGCHAIN_FILE"):
            output_path = os.getenv("SERIALIZE_LANGCHAIN_FILE")
            save_serialized_messages(messages, output_path)

    return final_content, tool_history, conversation, tokens_total
    # Use accumulated server-reported tokens; fallback to tiktoken if server didn't report
    tokens_total = total_input_tokens + total_output_tokens
    if tokens_total == 0:
        try:
            conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
            tokens_total = count_tokens(conv_text)
            # Split evenly for fallback (rough approximation)
            total_input_tokens = tokens_total // 2
            total_output_tokens = tokens_total - total_input_tokens
            logging.debug(
                "[Token Tracking] Max iterations reached, no server tokens, tiktoken fallback: %d",
                tokens_total,
            )
        except Exception:
            tokens_total = 0

    logging.debug(
        "[Token Tracking] Max iterations final: input=%d, output=%d, total=%d",
        total_input_tokens,
        total_output_tokens,
        tokens_total,
    )
    usage = {
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "total_tokens": tokens_total,
    }
    return final_content, tool_history, conversation, usage
