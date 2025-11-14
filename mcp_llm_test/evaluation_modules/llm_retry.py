"""
LLM invocation with exponential backoff retry logic.

This module handles retries for LLM API calls with exponential backoff
to handle throttling and rate limiting errors gracefully.
"""

import asyncio
import logging
import random
import time


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
            # Add timing to help debug slow API calls
            start_time = time.time()

            # Log request details in debug mode
            logging.debug(f"Starting LLM API call (attempt {attempt + 1}/{max_retries + 1})...")
            logging.debug(f"LLM instance type: {type(llm_instance).__name__}")
            logging.debug(f"Number of messages: {len(messages)}")
            for i, msg in enumerate(messages):
                msg_type = type(msg).__name__
                content_preview = (
                    str(msg.content)[:200] if hasattr(msg, "content") else str(msg)[:200]
                )
                logging.debug(f"  Message {i} ({msg_type}): {content_preview}...")

            result = await llm_instance.ainvoke(messages)

            elapsed = time.time() - start_time

            # Log response details in debug mode
            logging.debug(f"LLM API call completed in {elapsed:.2f}s")
            logging.debug(f"Response type: {type(result).__name__}")
            if hasattr(result, "content"):
                logging.debug(f"Response content preview: {str(result.content)[:200]}...")
            else:
                logging.debug(f"Response: {str(result)[:200]}...")

            # Log response metadata if available
            if hasattr(result, "response_metadata"):
                logging.debug(f"Response metadata: {result.response_metadata}")
            if hasattr(result, "usage_metadata"):
                logging.debug(f"Usage metadata: {result.usage_metadata}")

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
            # Log at warning level (not just debug) so users see the error
            if attempt >= max_retries:
                logging.warning(
                    f"⚠️  LLM API call failed after {max_retries + 1} attempts: {error_name}: {error_msg[:200]}"
                )
            else:
                logging.debug(f"Non-throttling error or exhausted retries, raising: {error_name}")
            raise

    # If we get here, we exhausted all retries
    logging.warning(
        f"⚠️  LLM API call exhausted all {max_retries + 1} retries. Last error: {type(last_exception).__name__}: {str(last_exception)[:200]}"
    )
    raise last_exception
