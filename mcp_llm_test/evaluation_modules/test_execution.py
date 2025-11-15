"""
Test case execution orchestration.

This module handles running individual test cases and collecting results.
"""

import asyncio
import logging
from typing import Any, Dict

from fastmcp.client import Client
from marrvel_mcp import TokenLimitExceeded

from .cache import load_cached_result, save_cached_result
from .evaluation import evaluate_response, get_langchain_response, MAX_TOKENS


async def run_test_case(
    semaphore: asyncio.Semaphore,
    mcp_client: Client,
    test_case: Dict[str, Any],
    llm_evaluator,
    use_cache: bool = True,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
    pbar=None,
    llm_instance=None,
    llm_web_instance=None,
) -> Dict[str, Any]:
    """
    Runs a single test case and returns the results for the table.

    Args:
        semaphore: Asyncio semaphore for limiting concurrency
        mcp_client: MCP client for tool calls
        test_case: Test case dictionary
        llm_evaluator: LLM instance to use for evaluation
        use_cache: Whether to use cached results (default: True)
        vanilla_mode: If True, run without tool calling (default: False)
        web_mode: If True, run with web search enabled (default: False)
        model_id: Model identifier for model-specific cache (default: None)
        pbar: Optional tqdm progress bar to update
        llm_instance: LLM instance to use (if None, uses global llm)
        llm_web_instance: Web-enabled LLM instance to use (if None, uses global llm_web)
    """
    async with semaphore:
        name = test_case["case"]["name"]
        user_input = test_case["case"]["input"]
        expected = test_case["case"]["expected"]

        # Check cache first if enabled
        if use_cache:
            cached = load_cached_result(name, vanilla_mode, web_mode, model_id)
            if cached is not None:
                # Check if cached result is a failure
                classification = cached.get("classification", "")
                is_failure = (
                    classification.lower().startswith("no")
                    or "error" in classification.lower()
                    or "token" in classification.lower()
                )

                # If cached result was successful, reuse it
                if not is_failure:
                    if pbar:
                        mode_label = "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                        pbar.set_postfix_str(f"Cached ({mode_label}): {name[:40]}...")
                        pbar.update(1)
                    return cached

                # Otherwise, re-run the failed test
                if pbar:
                    mode_label = "web" if web_mode else ("vanilla" if vanilla_mode else "tool")
                    pbar.set_postfix_str(f"Re-running failed ({mode_label}): {name[:40]}...")

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
            langchain_response, tool_history, full_conversation, tokens_used, metadata = (
                await get_langchain_response(
                    mcp_client, user_input, vanilla_mode, web_mode, llm_instance, llm_web_instance
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
            result = {
                "question": user_input,
                "expected": expected,
                "response": langchain_response,
                "classification": classification,
                "tool_calls": tool_history,
                "conversation": full_conversation,
                "tokens_used": tokens_used,
                "mode": "web" if web_mode else ("vanilla" if vanilla_mode else "tool"),
                "metadata": metadata,
            }
            # Save to cache
            save_cached_result(name, result, vanilla_mode, web_mode, model_id)
            if pbar:
                pbar.update(1)
            return result
        except TokenLimitExceeded as e:
            # Stop evaluation completely and mark as NO due to token exceed
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
                pbar.update(1)
            # Don't cache failures
            return result
        except Exception as e:
            # Always log errors, not just when pbar exists
            import traceback

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
                pbar.update(1)
            # Don't cache errors
            return result
