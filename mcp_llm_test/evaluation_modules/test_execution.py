"""
Test case execution orchestration.

This module handles running individual test cases and collecting results.
"""

import asyncio
import logging
import os
from typing import Any, Dict

from fastmcp.client import Client
from marrvel_mcp import TokenLimitExceeded

from .cache import load_cached_result, save_cached_result
from .evaluation import evaluate_response, get_langchain_response, MAX_TOKENS


def update_progress_bar_with_stats(pbar, test_stats: Dict[str, int] | None):
    """Update progress bar with current test statistics on the left side."""
    if pbar and test_stats is not None:
        stats_str = (
            f"✓ {test_stats.get('yes', 0)} | "
            f"✗ {test_stats.get('no', 0)} | "
            f"⚠ {test_stats.get('failed', 0)}"
        )
        pbar.set_description_str(stats_str)


async def run_test_case(
    semaphore: asyncio.Semaphore,
    mcp_client: Client,
    test_case: Dict[str, Any],
    llm_evaluator,
    run_id: str,
    test_uuid: str,
    use_cache: bool = True,
    retry_failed: bool = False,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
    pbar=None,
    llm_instance=None,
    llm_web_instance=None,
    test_stats: Dict[str, int] | None = None,
) -> Dict[str, Any]:
    """
    Runs a single test case and returns the results for the table.

    Args:
        semaphore: Asyncio semaphore for limiting concurrency
        mcp_client: MCP client for tool calls
        test_case: Test case dictionary
        llm_evaluator: LLM instance to use for evaluation
        llm_evaluator: LLM instance to use for evaluation
        run_id: Unique identifier for the run
        test_uuid: Unique identifier for the test case
        use_cache: Whether to use cached results (default: True)
        retry_failed: Whether to re-run failed tests (default: False)
        vanilla_mode: If True, run without tool calling (default: False)
        web_mode: If True, run with web search enabled (default: False)
        model_id: Model identifier for model-specific cache (default: None)
        pbar: Optional tqdm progress bar to update
        llm_instance: LLM instance to use (if None, uses global llm)
        llm_web_instance: Web-enabled LLM instance to use (if None, uses global llm_web)
        test_stats: Optional dictionary to track test statistics (correct/incorrect/failed)
    """
    # Apply per-test timeout to prevent indefinite hanging (default 300s configurable via env TEST_CASE_TIMEOUT)
    per_test_timeout = float(os.getenv("TEST_CASE_TIMEOUT", "300"))
    async with semaphore:
        name = test_case["case"]["name"]
        user_input = test_case["case"]["input"]
        expected = test_case["case"]["expected"]

        # Check cache first if enabled
        if use_cache:
            cached = load_cached_result(run_id, test_uuid, vanilla_mode, web_mode, model_id)
            if cached is not None:
                # Check if cached result is a failure
                classification = cached.get("classification", "")
                status = cached.get("status", "")

                # Refined Retry Logic:
                # 1. ERROR status -> Retry only if retry_failed is True
                if status == "ERROR" or "error" in str(classification).lower():
                    if retry_failed:
                        if pbar:
                            mode_label = (
                                "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                            )
                            pbar.set_postfix_str(f"Retrying error ({mode_label}): {name[:40]}...")
                    else:
                        # Return cached error without re-running
                        if test_stats is not None:
                            test_stats["failed"] += 1
                        if pbar:
                            mode_label = (
                                "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                            )
                            update_progress_bar_with_stats(pbar, test_stats)
                            pbar.update(1)
                        return cached

                # 2. Incorrect answer ("no") -> Retry only if retry_failed is True
                elif str(classification).lower().startswith("no"):
                    if retry_failed:
                        if pbar:
                            mode_label = (
                                "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                            )
                            pbar.set_postfix_str(f"Retrying failed ({mode_label}): {name[:40]}...")
                    else:
                        # Return cached failure
                        if test_stats is not None:
                            test_stats["no"] += 1
                        if pbar:
                            mode_label = (
                                "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                            )
                            update_progress_bar_with_stats(pbar, test_stats)
                            pbar.update(1)
                        return cached

                # 3. Success ("yes") -> Always return cached
                else:
                    if test_stats is not None:
                        test_stats["yes"] += 1
                    if pbar:
                        mode_label = "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                        update_progress_bar_with_stats(pbar, test_stats)
                        pbar.update(1)
                    return cached

        if pbar:
            mode_label = "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
            pbar.set_postfix_str(f"Running ({mode_label}): {name[:40]}...")

        # Log test execution details in debug mode
        mode_label = "web" if web_mode else ("vanilla" if vanilla_mode else "tool")

        logging.debug("=" * 80)
        logging.debug(f"🧪 TEST EXECUTION:")
        logging.debug(f"   Test: {name}")
        logging.debug(f"   Mode: {mode_label.upper()}")
        if vanilla_mode:
            logging.debug("   ⚠️  VANILLA MODE: No tools will be called (baseline test)")
        elif web_mode:
            logging.debug("   🌐 WEB MODE: Web search enabled via :online suffix")
        else:
            logging.debug("   🔧 TOOL MODE: MARRVEL-MCP tools available")
        logging.debug(
            f"   Question: {user_input[:150]}..."
            if len(user_input) > 150
            else f"   Question: {user_input}"
        )
        logging.debug(
            f"   Expected: {expected[:150]}..."
            if len(expected) > 150
            else f"   Expected: {expected}"
        )

        try:
            langchain_response, tool_history, full_conversation, usage, metadata = (
                await asyncio.wait_for(
                    get_langchain_response(
                        mcp_client,
                        user_input,
                        vanilla_mode,
                        web_mode,
                        llm_instance,
                        llm_web_instance,
                    ),
                    timeout=per_test_timeout,
                )
            )

            # Log response details in debug mode
            logging.debug(f"   Response received: {len(langchain_response)} chars")
            logging.debug(f"   Tool calls made: {len(tool_history)}")
            if tool_history:
                logging.debug(
                    f"   Tools used: {', '.join(set(tc.get('name', 'unknown') for tc in tool_history))}"
                )
            else:
                if not vanilla_mode and not web_mode:
                    logging.debug(
                        "   ⚠️  No tools were called in TOOL mode - LLM may have answered without tools"
                    )
            logging.debug("=" * 80)

            # Use the provided evaluator LLM for consistent evaluation
            classification = await evaluate_response(langchain_response, expected, llm_evaluator)

            # Extract token counts from usage dict (backward compatible)
            tokens_used = usage.get("total_tokens", 0) if isinstance(usage, dict) else usage
            input_tokens = usage.get("input_tokens", 0) if isinstance(usage, dict) else 0
            output_tokens = usage.get("output_tokens", 0) if isinstance(usage, dict) else 0

            result = {
                "question": user_input,
                "expected": expected,
                "response": langchain_response,
                "classification": classification,
                "tool_calls": tool_history,
                "conversation": full_conversation,
                "tokens_used": tokens_used,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "mode": "web" if web_mode else ("vanilla" if vanilla_mode else "tool"),
                "metadata": metadata,
                "serialized_messages": metadata.get(
                    "serialized_messages", []
                ),  # Add serialized LangChain objects
            }

            # Update test statistics based on classification
            if test_stats is not None:
                classification_lower = str(classification).lower()
                if classification_lower.startswith("yes"):
                    test_stats["yes"] += 1
                elif classification_lower.startswith("no"):
                    test_stats["no"] += 1
                else:
                    test_stats["failed"] += 1

            # Save to cache
            save_cached_result(run_id, test_uuid, result, vanilla_mode, web_mode, model_id)
            if pbar:
                update_progress_bar_with_stats(pbar, test_stats)
                pbar.update(1)
            return result
        except TokenLimitExceeded as e:
            # Stop evaluation completely and mark as NO due to token exceed
            if test_stats is not None:
                test_stats["failed"] += 1
            if pbar:
                pbar.write(
                    f"⚠️  Token limit exceeded for {name}: {e.token_count:,} > {MAX_TOKENS:,}"
                )
            result = {
                "question": user_input,
                "expected": expected,
                "response": "",  # No response since we skipped evaluation
                "classification": f"no - token count exceeded: {e.token_count:,} > {MAX_TOKENS:,}. Please reduce the input/context.",
                "tool_calls": [],
                "conversation": [],
                "tokens_used": e.token_count,
            }
            if pbar:
                update_progress_bar_with_stats(pbar, test_stats)
                pbar.update(1)
            # Don't cache failures
            return result
        except asyncio.TimeoutError:
            timeout_msg = f"**Timeout:** Test exceeded {per_test_timeout}s limit and was aborted to prevent run stall."
            if pbar:
                pbar.write(f"⏱️ Timeout in {name} after {per_test_timeout}s")
                pbar.update(1)
            result = {
                "question": user_input,
                "expected": expected,
                "response": timeout_msg,
                "classification": "no - timeout",
                "tool_calls": [],
                "conversation": [],
                "tokens_used": 0,
                "mode": "web" if web_mode else ("vanilla" if vanilla_mode else "tool"),
                "metadata": {"timeout_seconds": per_test_timeout},
            }
            # Do not cache timeouts
            return result
        except Exception as e:
            # Always log errors, not just when pbar exists
            import traceback

            if test_stats is not None:
                test_stats["failed"] += 1

            error_details = f"❌ Error in {name}: {e}"

            if pbar:
                pbar.write(error_details)
            else:
                # In multi-model mode without pbar, print directly
                print(error_details)

            # Show error type and first part of message even in normal mode
            error_type = type(e).__name__
            error_msg = str(e)
            print(f"   Error type: {error_type}")
            print(f"   Error message: {error_msg[:500]}")

            # Show full traceback in debug mode
            logging.debug(f"Full traceback for {name}:")
            logging.debug(traceback.format_exc())

            # In verbose mode, show more context
            logging.info(f"Test case: {name}")
            logging.info(f"Question: {user_input[:200]}")
            logging.info(f"Full error: {error_msg}")

            result = {
                "question": user_input,
                "expected": expected,
                "response": "**No response generated due to error.**",
                "classification": f"**Error:** {str(e)[:200]}",  # Truncate long errors
                "tool_calls": [],
                "conversation": [],
            }
            if pbar:
                update_progress_bar_with_stats(pbar, test_stats)
                pbar.update(1)
            # Don't cache errors
            return result
