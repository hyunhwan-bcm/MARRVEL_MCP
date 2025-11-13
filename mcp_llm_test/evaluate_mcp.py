"""
MCP LLM Evaluation Script with LangChain Integration

This script evaluates MCP (Model Context Protocol) tools using LangChain v1 for:
- Agent-based tool calling with ChatOpenAI (via OpenRouter)
- Structured message handling (SystemMessage, HumanMessage, ToolMessage)
- Async LLM invocations with bind_tools() for tool integration
- Test case evaluation against expected responses

Architecture:
- LangChain ChatOpenAI configured for OpenRouter API
- MCP tools exposed via FastMCP client
- Concurrent test execution with asyncio semaphores
- HTML report generation with conversation history
- Result caching for faster re-runs

References:
- LangChain with OpenRouter: https://openrouter.ai/docs/community/lang-chain
- Tool calling: https://docs.langchain.com/oss/python/langchain/overview
- Evaluation: https://docs.langchain.com/oss/python/langchain/overview
"""

import argparse
import asyncio
import json
import os
import pickle
import re
import sys
import tempfile
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import yaml
from dotenv import load_dotenv
from fastmcp.client import Client
from jinja2 import Environment, FileSystemLoader
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
import tiktoken
from tqdm.asyncio import tqdm as atqdm

from marrvel_mcp.server import create_server
from config.llm_providers import create_llm_instance, get_provider_config, ProviderType
from marrvel_mcp import (
    convert_tool_to_langchain_format,
    parse_tool_result_content,
    execute_agentic_loop,
    count_tokens,
    validate_token_count,
    TokenLimitExceeded,
)


# Load environment variables from .env file
load_dotenv()

"""NOTE: Model selection

The evaluation harness now supports selecting an OpenRouter model at runtime
via the environment variable `OPENROUTER_MODEL`. If it is not set, we fall
back to the latest Gemini 2.5 Flash model (NOT any deprecated 1.5 version).

Examples:
    export OPENROUTER_MODEL="anthropic/claude-3.5-sonnet"
    export OPENROUTER_MODEL="google/gemini-2.5-pro"
    python evaluate_mcp.py

This keeps existing behavior (Gemini 2.5 Flash) when no override is provided.
"""

from config.llm_config import (
    get_openrouter_model,
    get_default_model_config,
    get_evaluation_model_config,
    DEFAULT_MODEL,
)

# Resolve model lazily at import so tests can patch env before main() runs.
MODEL = get_openrouter_model()  # default is google/gemini-2.5-flash (backward compat)
MAX_TOKENS = 100_000  # Maximum tokens allowed for evaluation to prevent API errors

# Cache settings
CACHE_DIR = Path.home() / ".cache" / "marrvel-mcp" / "evaluations"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Global variables for LLM (initialized in main after arg parsing)
llm = None
llm_web = None  # LLM with web search enabled (:online suffix)
llm_evaluator = (
    None  # LLM used for evaluating/grading responses (separate from models being tested)
)
OPENROUTER_API_KEY = None


async def invoke_with_throttle_retry(
    llm_instance,
    messages,
    max_retries: int = 8,
    initial_delay: float = 2.0,
    max_delay: float = 60.0,
    add_initial_jitter: bool = False,
):
    """
    Invoke LLM with exponential backoff for throttling exceptions.

    This wrapper handles both botocore ThrottlingException (from AWS Bedrock)
    and general rate limiting errors with exponential backoff and jitter.

    Args:
        llm_instance: LangChain LLM instance to invoke
        messages: Messages to send to the LLM
        max_retries: Maximum number of retry attempts (default: 8)
        initial_delay: Initial delay in seconds before first retry (default: 2.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        add_initial_jitter: If True, add 0-1s random delay before first request.
                           If None/False, auto-detect Bedrock and add jitter for it.

    Returns:
        LLM response

    Raises:
        Last exception if all retries fail
    """
    import logging
    import random

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
            error_msg = str(e).lower()

            if "throttling" in error_name.lower() or "throttling" in error_msg:
                is_throttling = True
            elif "rate" in error_msg and "limit" in error_msg:
                is_throttling = True
            elif "too many" in error_msg:
                is_throttling = True

            # Only retry on throttling/rate limit errors
            if is_throttling and attempt < max_retries:
                # Add jitter to avoid thundering herd (10-30% of delay)
                jitter = delay * random.uniform(0.1, 0.3)
                sleep_time = min(delay + jitter, max_delay)

                logging.warning(
                    f"Throttling detected ({error_name}), retrying in {sleep_time:.2f}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                await asyncio.sleep(sleep_time)
                delay = min(delay * 2, max_delay)  # Exponential backoff with cap
                continue

            # For non-throttling errors or exhausted retries, raise immediately
            raise

    # If we get here, we exhausted all retries
    raise last_exception


def get_cache_path(
    test_case_name: str,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
) -> Path:
    """Get the cache file path for a test case.

    Args:
        test_case_name: Name of the test case
        vanilla_mode: If True, append '_vanilla' to distinguish from tool-enabled cache
        web_mode: If True, append '_web' to distinguish from vanilla cache
        model_id: Model identifier (e.g., "google/gemini-2.5-flash"). If provided, cache is model-specific.

    Returns:
        Path to cache file
    """
    # Use sanitized test case name for filename
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in test_case_name)
    safe_name = safe_name.strip().replace(" ", "_")

    # Add model identifier if provided (sanitize it too)
    if model_id:
        safe_model = "".join(c if c.isalnum() or c in ("-", "_") else "_" for c in model_id)
        safe_model = safe_model.replace("/", "_")
        model_suffix = f"_{safe_model}"
    else:
        model_suffix = ""

    if web_mode:
        mode_suffix = "_web"
    elif vanilla_mode:
        mode_suffix = "_vanilla"
    else:
        mode_suffix = ""

    return CACHE_DIR / f"{safe_name}{model_suffix}{mode_suffix}.pkl"


def parse_subset(subset: str | None, total_count: int) -> List[int]:
    """
    Parse a subset specification string into a list of 0-based indices.

    Supported formats (1-based in the input):
    - "1-5"               -> [0,1,2,3,4]
    - "1,2,4"             -> [0,1,3]
    - "1-3,5,7-9"         -> [0,1,2,4,6,7,8]

    Rules:
    - Whitespace is ignored
    - Indices are 1-based in the input and converted to 0-based
    - Duplicates are removed; result is sorted
    - Errors:
      * index 0 -> ValueError("Index must be >= 1")
      * reversed range (e.g., 5-1) -> ValueError(f"Invalid range {start}-{end}")
      * index out of range -> ValueError(f"Index {n} out of range")
      * malformed tokens -> ValueError with message matching tests
    """
    if subset is None or subset.strip() == "":
        return list(range(total_count))

    # Remove spaces to simplify parsing
    cleaned = subset.replace(" ", "")
    indices: set[int] = set()

    # Split by comma for items that are either single indices or ranges
    tokens = [t for t in cleaned.split(",") if t != ""]
    for token in tokens:
        if "-" in token:
            # Range parsing
            parts = token.split("-")
            if len(parts) != 2 or parts[0] == "" or parts[1] == "":
                # Covers cases like "1-2-3", "-1", "1-", "-"
                raise ValueError("Invalid range format")
            start_str, end_str = parts
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError("Invalid range format")
            start = int(start_str)
            end = int(end_str)
            if start == 0 or end == 0:
                raise ValueError("Index must be >= 1")
            if start > end:
                raise ValueError(f"Invalid range {start}-{end}")
            # Validate bounds, prefer reporting the start if both are out-of-range
            if start > total_count:
                raise ValueError(f"Index {start} out of range")
            if end > total_count:
                raise ValueError(f"Index {end} out of range")
            # Convert to 0-based inclusive range
            indices.update(i - 1 for i in range(start, end + 1))
        else:
            # Single index parsing
            if not token.isdigit():
                raise ValueError("Invalid index")
            value = int(token)
            if value == 0:
                raise ValueError("Index must be >= 1")
            if value > total_count:
                raise ValueError(f"Index {value} out of range")
            indices.add(value - 1)

    return sorted(indices)


def load_cached_result(
    test_case_name: str,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
) -> Dict[str, Any] | None:
    """Load cached result for a test case if it exists.

    Args:
        test_case_name: Name of the test case
        vanilla_mode: If True, load from vanilla cache
        web_mode: If True, load from web cache
        model_id: Model identifier for model-specific cache

    Returns:
        Cached result or None if not found
    """
    cache_path = get_cache_path(test_case_name, vanilla_mode, web_mode, model_id)
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache for {test_case_name}: {e}")
            return None
    return None


def save_cached_result(
    test_case_name: str,
    result: Dict[str, Any],
    vanilla_mode: bool = False,
    web_mode: bool = False,
    model_id: str | None = None,
):
    """Save result to cache.

    Args:
        test_case_name: Name of the test case
        result: Test result to cache
        vanilla_mode: If True, save to vanilla cache
        web_mode: If True, save to web cache
        model_id: Model identifier for model-specific cache
    """
    cache_path = get_cache_path(test_case_name, vanilla_mode, web_mode, model_id)
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(result, f)
    except Exception as e:
        print(f"Warning: Failed to save cache for {test_case_name}: {e}")


def clear_cache():
    """Clear all cached results."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {cache_file}: {e}")
        print(f"✅ Cache cleared: {CACHE_DIR}")


async def get_langchain_response(
    mcp_client: Client,
    user_input: str,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    llm_instance=None,
    llm_web_instance=None,
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], int, Dict[str, Any]]:
    """
    Get response using LangChain with OpenRouter, handling tool calls via the MCP client.

    Args:
        mcp_client: MCP client for tool calls
        user_input: User question/prompt
        vanilla_mode: If True, LLM responds without tool calling capabilities
        web_mode: If True, LLM responds with web search enabled (no tool calling)
        llm_instance: LLM instance to use (if None, uses global llm)
        llm_web_instance: Web-enabled LLM instance to use (if None, uses global llm_web)

    Returns: (final_response, tool_history, full_conversation, tokens_used, metadata)
    """
    # Use provided instances or fall back to globals for backward compatibility
    active_llm_base = llm_instance if llm_instance is not None else llm
    active_llm_web = llm_web_instance if llm_web_instance is not None else llm_web

    # Initialize LangChain messages
    if vanilla_mode:
        system_message = """You are an expert genetics research assistant. Answer questions about genes, variants, and genetic data with confidence and precision.

When answering:
- Provide clear, definitive answers based on your knowledge
- Use standard genetic nomenclature and bioinformatics principles
- If asked about specific variants, analyze the mutation type and predict the likely protein change
- Structure your response to end with a clear, concise answer to the question
- Avoid apologetic language - focus on providing the most accurate information possible"""
    elif web_mode:
        system_message = """You are an expert genetics research assistant with web search capabilities. Search for accurate, up-to-date information from scientific databases and reliable sources.

When answering:
- Search for the specific information requested (genes, transcripts, variants, proteins)
- If exact matches aren't found, search for related variants, similar mutations, or the gene/transcript in question
- Analyze the genetic nomenclature (e.g., c.187C>T means codon 63, C to T substitution) and infer the protein change
- Use information from similar cases or the gene's annotation to provide informed responses
- ALWAYS provide a clear, definitive answer at the end of your response
- Do NOT say "I cannot answer" - instead, work with available information to provide the best possible answer
- Cite specific sources when available
- Structure your response to conclude with a direct answer to the question asked"""
    else:
        system_message = "You are a helpful genetics research assistant. You have access to tools that can query genetic databases and provide accurate information. Always use the available tools to answer questions about genes, variants, and genetic data. Do not use pubmed tools unless pubmed is mentioned in the question. Do not make up or guess information - use the tools to get accurate data."

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_input),
    ]
    tool_history = []
    conversation = []

    # In vanilla or web mode, skip tool binding and just get a direct response
    if vanilla_mode or web_mode:
        # Store initial messages in conversation history
        conversation.append({"role": "system", "content": system_message})
        conversation.append({"role": "user", "content": user_input})

        # Use web-enabled LLM for web mode, regular LLM for vanilla mode
        active_llm = active_llm_web if web_mode else active_llm_base

        # Get direct response without tool calling
        try:
            response = await invoke_with_throttle_retry(active_llm, messages)

            # Collect metadata (especially useful for web_mode debugging)
            response_metadata = {}
            if web_mode or vanilla_mode:
                if hasattr(response, "__dict__"):
                    response_metadata["response_type"] = str(type(response))
                    response_metadata["has_content_attr"] = hasattr(response, "content")
                    if hasattr(response, "content"):
                        response_metadata["content_length"] = (
                            len(response.content) if response.content else 0
                        )
                        response_metadata["content_preview"] = str(response.content)[:100]
                    if hasattr(response, "response_metadata"):
                        metadata = response.response_metadata
                        response_metadata["model_used"] = metadata.get("model_name", "N/A")
                        if "finish_reason" in metadata:
                            response_metadata["finish_reason"] = metadata["finish_reason"]
                    if hasattr(response, "usage_metadata"):
                        usage = response.usage_metadata
                        response_metadata["input_tokens"] = usage.get("input_tokens", 0)
                        response_metadata["output_tokens"] = usage.get("output_tokens", 0)

            final_content = response.content if hasattr(response, "content") else str(response)

            # Check if response is empty and warn
            if not final_content or final_content.strip() == "":
                mode_name = "web search" if web_mode else "vanilla"
                print(
                    f"⚠️  Warning: Empty response from {mode_name} mode. Model may not support this mode or encountered an error."
                )
                print(f"  Question was: {user_input}")
                final_content = f"**No response generated from {mode_name} mode. The model may not support this feature or encountered an API error.**"

            conversation.append({"role": "assistant", "content": final_content})

            # Compute total tokens used
            try:
                conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
                tokens_total = count_tokens(conv_text)
            except Exception:
                tokens_total = 0

            return final_content, tool_history, conversation, tokens_total, response_metadata

        except Exception as e:
            mode_name = "web search" if web_mode else "vanilla"
            error_msg = f"**Error in {mode_name} mode: {str(e)}**"
            print(f"❌ Error in {mode_name} mode: {e}")
            conversation.append({"role": "assistant", "content": error_msg})
            return error_msg, tool_history, conversation, 0, {"error": str(e)}

    # Get MCP tools and convert to LangChain format
    mcp_tools_list = await mcp_client.list_tools()
    available_tools = [convert_tool_to_langchain_format(tool) for tool in mcp_tools_list]

    # Bind tools to LLM
    llm_with_tools = active_llm_base.bind_tools(available_tools)

    # Store initial messages in conversation history
    conversation.append({"role": "system", "content": messages[0].content})
    conversation.append({"role": "user", "content": user_input})

    # Execute agentic loop with tool calling
    final_content, tool_history, conversation, tokens_total = await execute_agentic_loop(
        mcp_client=mcp_client,
        llm_with_tools=llm_with_tools,
        messages=messages,
        conversation=conversation,
        tool_history=tool_history,
        max_tokens=MAX_TOKENS,
        max_iterations=10,
    )

    return final_content, tool_history, conversation, tokens_total, {}


async def evaluate_response(actual: str, expected: str, llm_instance=None) -> str:
    """
    Evaluate the response using LangChain and return the classification text.
    Be flexible - if the actual response contains the expected information plus additional details, consider it acceptable.

    Args:
        actual: The actual response text
        expected: The expected response text
        llm_instance: DEPRECATED - kept for backward compatibility, ignored
    """
    # Always use the dedicated evaluator LLM for consistent evaluation
    # The llm_instance parameter is kept for backward compatibility but ignored
    active_llm = llm_evaluator

    prompt = f"""Is the actual response consistent with the expected response?

Consider the response as acceptable (answer 'yes') if:
- It contains the expected information, even if it includes additional details
- The core facts/data match the expected response
- Any additional information provided is accurate and relevant

Only answer 'no' if:
- The response contradicts the expected information
- Key information from the expected response is missing
- The response is factually incorrect

Answer with 'yes' or 'no' followed by a brief reason.

Expected: {expected}
Actual: {actual}"""

    # Validate token count before making API call
    is_valid, token_count = validate_token_count(prompt)
    if not is_valid:
        return f"no - Evaluation skipped: Input token count ({token_count:,}) exceeds maximum allowed ({MAX_TOKENS:,}). The response or context is excessively long. Please reduce the input size."

    messages = [HumanMessage(content=prompt)]
    response = await invoke_with_throttle_retry(active_llm, messages)
    return response.content


async def run_test_case(
    semaphore: asyncio.Semaphore,
    mcp_client: Client,
    test_case: Dict[str, Any],
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

        try:
            langchain_response, tool_history, full_conversation, tokens_used, metadata = (
                await get_langchain_response(
                    mcp_client, user_input, vanilla_mode, web_mode, llm_instance, llm_web_instance
                )
            )
            # Use the global evaluator LLM (not the model being tested) for consistent evaluation
            classification = await evaluate_response(langchain_response, expected)
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
            if pbar:
                pbar.write(f"❌ Error in {name}: {e}")
            result = {
                "question": user_input,
                "expected": expected,
                "response": "**No response generated due to error.**",
                "classification": f"**Error:** {e}",
                "tool_calls": [],
                "conversation": [],
            }
            if pbar:
                pbar.update(1)
            # Don't cache errors
            return result


def generate_html_report(
    results: List[Dict[str, Any]],
    dual_mode: bool = False,
    tri_mode: bool = False,
    multi_model: bool = False,
    evaluator_model: str | None = None,
    evaluator_provider: str | None = None,
) -> str:
    """Generate HTML report with modal popups, reordered columns, and success rate summary.

    Args:
        results: List of test results
        dual_mode: If True, results contain both vanilla and tool mode responses
        tri_mode: If True, results contain vanilla, web, and tool mode responses
        multi_model: If True, results contain multiple models across all three modes
        evaluator_model: Model ID used for evaluation/grading
        evaluator_provider: Provider used for evaluation model

    Returns:
        Path to generated HTML file
    """
    # Create a temporary HTML file
    temp_html = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, prefix="evaluation_results_"
    )
    html_path = temp_html.name

    # Calculate success rate
    total_tests = len(results)
    successful_tests = 0
    successful_vanilla = 0
    successful_web = 0
    successful_tool = 0

    if multi_model:
        # Calculate success rates for each model across all modes
        models_stats = {}
        for result in results:
            for model_id, model_data in result["models"].items():
                if model_id not in models_stats:
                    models_stats[model_id] = {
                        "name": model_data["name"],
                        "provider": model_data.get("provider", "unknown"),
                        "vanilla_success": 0,
                        "web_success": 0,
                        "tool_success": 0,
                    }

                vanilla_classification = model_data["vanilla"]["classification"].lower()
                web_classification = model_data["web"].get("classification", "").lower()
                tool_classification = model_data["tool"]["classification"].lower()

                if re.search(r"\byes\b", vanilla_classification):
                    models_stats[model_id]["vanilla_success"] += 1
                # Skip counting N/A web results
                if model_data["web"].get("status") != "N/A" and re.search(
                    r"\byes\b", web_classification
                ):
                    models_stats[model_id]["web_success"] += 1
                if re.search(r"\byes\b", tool_classification):
                    models_stats[model_id]["tool_success"] += 1

        # Calculate percentages
        for model_id in models_stats:
            models_stats[model_id]["vanilla_rate"] = (
                models_stats[model_id]["vanilla_success"] / total_tests * 100
                if total_tests > 0
                else 0
            )
            models_stats[model_id]["web_rate"] = (
                models_stats[model_id]["web_success"] / total_tests * 100 if total_tests > 0 else 0
            )
            models_stats[model_id]["tool_rate"] = (
                models_stats[model_id]["tool_success"] / total_tests * 100 if total_tests > 0 else 0
            )
    elif tri_mode:
        # Calculate success rates for all three modes
        for result in results:
            vanilla_classification = result["vanilla"]["classification"].lower()
            web_classification = result["web"]["classification"].lower()
            tool_classification = result["tool"]["classification"].lower()

            if re.search(r"\byes\b", vanilla_classification):
                successful_vanilla += 1
            if re.search(r"\byes\b", web_classification):
                successful_web += 1
            if re.search(r"\byes\b", tool_classification):
                successful_tool += 1

        vanilla_success_rate = (successful_vanilla / total_tests * 100) if total_tests > 0 else 0
        web_success_rate = (successful_web / total_tests * 100) if total_tests > 0 else 0
        tool_success_rate = (successful_tool / total_tests * 100) if total_tests > 0 else 0
    elif dual_mode:
        # Calculate success rates for both modes
        for result in results:
            vanilla_classification = result["vanilla"]["classification"].lower()
            tool_classification = result["tool"]["classification"].lower()

            if re.search(r"\byes\b", vanilla_classification):
                successful_vanilla += 1
            if re.search(r"\byes\b", tool_classification):
                successful_tool += 1

        vanilla_success_rate = (successful_vanilla / total_tests * 100) if total_tests > 0 else 0
        tool_success_rate = (successful_tool / total_tests * 100) if total_tests > 0 else 0
    else:
        # Calculate success rate for single mode
        for result in results:
            classification = result["classification"].lower()
            # Check if evaluation contains "yes" (flexible matching)
            if re.search(r"\byes\b", classification):
                successful_tests += 1

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

    # Helper function to clean conversation data
    def clean_conversation(conversation: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Parse any escaped JSON strings in conversation for better display."""
        cleaned = []
        for msg in conversation:
            cleaned_msg = dict(msg)
            # Parse content if it's a string that looks like escaped JSON
            if isinstance(cleaned_msg.get("content"), str):
                cleaned_msg["content"] = parse_tool_result_content(cleaned_msg["content"])

            # Parse arguments in tool_calls if present
            if "tool_calls" in cleaned_msg and isinstance(cleaned_msg["tool_calls"], list):
                cleaned_tool_calls = []
                for tool_call in cleaned_msg["tool_calls"]:
                    cleaned_tool_call = dict(tool_call)
                    # Parse the arguments field if it's a JSON string
                    if "function" in cleaned_tool_call and isinstance(
                        cleaned_tool_call["function"], dict
                    ):
                        function = dict(cleaned_tool_call["function"])
                        if isinstance(function.get("arguments"), str):
                            try:
                                function["arguments"] = json.loads(function["arguments"])
                            except (json.JSONDecodeError, TypeError):
                                # Keep as-is if parsing fails
                                pass
                        cleaned_tool_call["function"] = function
                    cleaned_tool_calls.append(cleaned_tool_call)
                cleaned_msg["tool_calls"] = cleaned_tool_calls

            cleaned.append(cleaned_msg)
        return cleaned

    # Prepare data for template - add metadata to each result
    enriched_results = []

    if multi_model:
        # Prepare multi-model results with all models across all three modes
        for idx, result in enumerate(results):
            enriched_result = {
                "idx": idx,
                "question": result["question"],
                "expected": result["expected"],
                "models": {},
            }

            for model_id, model_data in result["models"].items():
                vanilla_res = model_data["vanilla"]
                web_res = model_data["web"]
                tool_res = model_data["tool"]

                vanilla_classification_lower = vanilla_res["classification"].lower()
                web_classification_lower = web_res.get("classification", "").lower()
                tool_classification_lower = tool_res["classification"].lower()

                vanilla_is_yes = re.search(r"\byes\b", vanilla_classification_lower)
                web_is_yes = (
                    re.search(r"\byes\b", web_classification_lower)
                    if web_res.get("status") != "N/A"
                    else None
                )
                tool_is_yes = re.search(r"\byes\b", tool_classification_lower)

                # Clean up conversation data for all three modes
                vanilla_conversation = clean_conversation(vanilla_res.get("conversation", []))
                web_conversation = (
                    clean_conversation(web_res.get("conversation", []))
                    if web_res.get("status") != "N/A"
                    else []
                )
                tool_conversation = clean_conversation(tool_res.get("conversation", []))

                enriched_result["models"][model_id] = {
                    "name": model_data["name"],
                    "vanilla": {
                        "response": vanilla_res.get("response", ""),
                        "classification": vanilla_res["classification"],
                        "is_yes": vanilla_is_yes is not None,
                        "tokens_used": vanilla_res.get("tokens_used", 0),
                        "tool_calls": vanilla_res.get("tool_calls", []),
                        "conversation": vanilla_conversation,
                    },
                    "web": {
                        "response": web_res.get("response", "N/A"),
                        "classification": web_res.get("classification", "N/A"),
                        "is_yes": (
                            web_is_yes is not None if web_res.get("status") != "N/A" else False
                        ),
                        "tokens_used": web_res.get("tokens_used", 0),
                        "tool_calls": web_res.get("tool_calls", []),
                        "conversation": web_conversation,
                        "is_na": web_res.get("status") == "N/A",
                        "na_reason": web_res.get("reason", ""),
                    },
                    "tool": {
                        "response": tool_res.get("response", ""),
                        "classification": tool_res["classification"],
                        "is_yes": tool_is_yes is not None,
                        "tokens_used": tool_res.get("tokens_used", 0),
                        "tool_calls": tool_res.get("tool_calls", []),
                        "conversation": tool_conversation,
                    },
                }

            enriched_results.append(enriched_result)
    elif tri_mode:
        # Prepare tri-mode results with vanilla, web, and tool responses
        for idx, result in enumerate(results):
            vanilla_res = result["vanilla"]
            web_res = result["web"]
            tool_res = result["tool"]

            vanilla_classification_lower = vanilla_res["classification"].lower()
            web_classification_lower = web_res["classification"].lower()
            tool_classification_lower = tool_res["classification"].lower()

            vanilla_is_yes = re.search(r"\byes\b", vanilla_classification_lower)
            web_is_yes = re.search(r"\byes\b", web_classification_lower)
            tool_is_yes = re.search(r"\byes\b", tool_classification_lower)

            # Clean up conversation data for all three modes
            vanilla_conversation = clean_conversation(vanilla_res.get("conversation", []))
            web_conversation = clean_conversation(web_res.get("conversation", []))
            tool_conversation = clean_conversation(tool_res.get("conversation", []))

            enriched_result = {
                "idx": idx,
                "question": result["question"],
                "expected": result["expected"],
                "vanilla": {
                    "response": vanilla_res.get("response", ""),
                    "classification": vanilla_res["classification"],
                    "is_yes": vanilla_is_yes is not None,
                    "tokens_used": vanilla_res.get("tokens_used", 0),
                    "tool_calls": vanilla_res.get("tool_calls", []),
                    "conversation": vanilla_conversation,
                },
                "web": {
                    "response": web_res.get("response", ""),
                    "classification": web_res["classification"],
                    "is_yes": web_is_yes is not None,
                    "tokens_used": web_res.get("tokens_used", 0),
                    "tool_calls": web_res.get("tool_calls", []),
                    "conversation": web_conversation,
                },
                "tool": {
                    "response": tool_res.get("response", ""),
                    "classification": tool_res["classification"],
                    "is_yes": tool_is_yes is not None,
                    "tokens_used": tool_res.get("tokens_used", 0),
                    "tool_calls": tool_res.get("tool_calls", []),
                    "conversation": tool_conversation,
                },
            }
            enriched_results.append(enriched_result)
    elif dual_mode:
        # Prepare dual-mode results with both vanilla and tool responses
        for idx, result in enumerate(results):
            vanilla_res = result["vanilla"]
            tool_res = result["tool"]

            vanilla_classification_lower = vanilla_res["classification"].lower()
            tool_classification_lower = tool_res["classification"].lower()

            vanilla_is_yes = re.search(r"\byes\b", vanilla_classification_lower)
            tool_is_yes = re.search(r"\byes\b", tool_classification_lower)

            # Clean up conversation data for both modes
            vanilla_conversation = clean_conversation(vanilla_res.get("conversation", []))
            tool_conversation = clean_conversation(tool_res.get("conversation", []))

            enriched_result = {
                "idx": idx,
                "question": result["question"],
                "expected": result["expected"],
                "vanilla": {
                    "response": vanilla_res.get("response", ""),
                    "classification": vanilla_res["classification"],
                    "is_yes": vanilla_is_yes is not None,
                    "tokens_used": vanilla_res.get("tokens_used", 0),
                    "tool_calls": vanilla_res.get("tool_calls", []),
                    "conversation": vanilla_conversation,
                },
                "tool": {
                    "response": tool_res.get("response", ""),
                    "classification": tool_res["classification"],
                    "is_yes": tool_is_yes is not None,
                    "tokens_used": tool_res.get("tokens_used", 0),
                    "tool_calls": tool_res.get("tool_calls", []),
                    "conversation": tool_conversation,
                },
            }
            enriched_results.append(enriched_result)
    else:
        # Single-mode results (original behavior)
        for idx, result in enumerate(results):
            classification_lower = result["classification"].lower()
            is_yes = re.search(r"\byes\b", classification_lower)

            # Clean up conversation data for better JSON display
            conversation = result.get("conversation", [])
            cleaned_conversation = clean_conversation(conversation)

            enriched_result = {
                "idx": idx,
                "question": result["question"],
                "expected": result["expected"],
                "response": result.get("response", ""),
                "classification": result["classification"],
                "is_yes": is_yes is not None,
                "tokens_used": result.get("tokens_used", 0),
                "tool_calls": result.get("tool_calls", []),
                "conversation": cleaned_conversation,
            }
            enriched_results.append(enriched_result)

    # Load and render Jinja2 template
    template_path = Path(__file__).parent.parent / "assets"
    env = Environment(loader=FileSystemLoader(template_path), autoescape=True)

    # Add custom filter for JSON serialization with proper formatting
    def tojson_pretty(value):
        """
        Format JSON with proper indentation for better readability.

        Converts escape sequences in string values to actual characters:
        - \\n becomes actual newline (and removes preceding backslash if present)
        - \\t becomes actual tab
        - \\r becomes actual carriage return

        This makes multiline strings (like markdown tables) display with
        proper line breaks instead of showing \\n escape sequences.
        """
        json_str = json.dumps(value, indent=2, ensure_ascii=False, sort_keys=False)
        # Replace escape sequences with actual characters for better readability
        # First replace \\\n (backslash-newline) with just newline to clean up markdown
        json_str = json_str.replace("\\\\n", "\n")
        # Then replace remaining \n with newlines
        json_str = json_str.replace("\\n", "\n")
        json_str = json_str.replace("\\t", "\t")
        json_str = json_str.replace("\\r", "\r")
        return json_str

    env.filters["tojson_pretty"] = tojson_pretty
    template = env.get_template("evaluation_report_template.html")

    if multi_model:
        html_content = template.render(
            multi_model=True,
            models_stats=models_stats,
            total_tests=total_tests,
            results=enriched_results,
            evaluator_model=evaluator_model,
            evaluator_provider=evaluator_provider,
        )
    elif tri_mode:
        html_content = template.render(
            tri_mode=True,
            vanilla_success_rate=vanilla_success_rate,
            web_success_rate=web_success_rate,
            tool_success_rate=tool_success_rate,
            successful_vanilla=successful_vanilla,
            successful_web=successful_web,
            successful_tool=successful_tool,
            total_tests=total_tests,
            results=enriched_results,
            evaluator_model=evaluator_model,
            evaluator_provider=evaluator_provider,
        )
    elif dual_mode:
        html_content = template.render(
            dual_mode=True,
            vanilla_success_rate=vanilla_success_rate,
            tool_success_rate=tool_success_rate,
            successful_vanilla=successful_vanilla,
            successful_tool=successful_tool,
            total_tests=total_tests,
            results=enriched_results,
            evaluator_model=evaluator_model,
            evaluator_provider=evaluator_provider,
        )
    else:
        html_content = template.render(
            dual_mode=False,
            success_rate=success_rate,
            successful_tests=successful_tests,
            total_tests=total_tests,
            results=enriched_results,
            evaluator_model=evaluator_model,
            evaluator_provider=evaluator_provider,
        )

    temp_html.write(html_content)
    temp_html.close()
    print(f"\n--- HTML report saved to: {html_path} ---")
    return html_path


def open_in_browser(html_path: str):
    """Open the HTML file in the default browser."""
    webbrowser.open(f"file://{os.path.abspath(html_path)}")
    print(f"--- Opened {html_path} in browser ---")


def load_models_config(
    config_path: Path | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load models configuration from YAML file.

    Args:
        config_path: Path to models configuration YAML file.
                     If None, uses default models_config.yaml in mcp-llm-test directory.

    Returns:
        Tuple of (enabled_models, evaluator_config)
        - enabled_models: List of enabled model configurations
        - evaluator_config: Dict with 'provider' and 'model' keys for evaluator, or empty dict
    """
    if config_path is None:
        config_path = Path(__file__).parent / "models_config.yaml"

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f)

        models = config_data.get("models", [])
        config = config_data.get("config", {})
        only_enabled = config.get("only_enabled", True)

        if only_enabled:
            enabled_models = [m for m in models if m.get("enabled", False)]
        else:
            enabled_models = models

        if not enabled_models:
            raise ValueError("No enabled models found in configuration file")

        # Extract evaluator configuration if present
        evaluator_config = config.get("evaluator", {})

        return enabled_models, evaluator_config
    except Exception as e:
        raise ValueError(f"Failed to load models configuration: {e}")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP LLM Evaluation Script - Evaluate MCP tools with LangChain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all test cases (fresh evaluation, results saved to cache)
  python evaluate_mcp.py

  # Use cached results (re-run only failed tests)
  python evaluate_mcp.py --cache

  # Clear cache only (does not run tests)
  python evaluate_mcp.py --clear

  # Run specific test cases by index (1-based)
  python evaluate_mcp.py --subset "1-5"        # Run tests 1 through 5
  python evaluate_mcp.py --subset "1,3,5"      # Run tests 1, 3, and 5
  python evaluate_mcp.py --subset "1-3,5,7-9"  # Run tests 1-3, 5, and 7-9

  # Ask a custom question and get JSON response (no HTML)
  python evaluate_mcp.py --prompt "tell me about MECP2"
  python evaluate_mcp.py --prompt "What is the CADD score for chr1:12345 A>G?"

  # Run multi-model comparison (test multiple models across vanilla, web, MARRVEL-MCP modes)
  python evaluate_mcp.py --multi-model
  python evaluate_mcp.py --multi-model --models-config custom_models.yaml

Cache Behavior:
  Results are always cached at: {cache_dir}

  Cache is stored after every run. Use --cache to reuse successful results
  and re-run only failed tests. Without --cache, all tests are re-evaluated.
        """.format(
            cache_dir=CACHE_DIR
        ),
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the cache and exit without running evaluations. Use this to remove all cached test results.",
    )

    parser.add_argument(
        "--cache",
        action="store_true",
        help="Use cached results from previous runs. Failed test cases will be re-run. Without this flag, all tests are re-evaluated.",
    )

    parser.add_argument(
        "--subset",
        type=str,
        metavar="INDICES",
        help="Run specific test cases by index. Supports ranges (1-5), individual indices (1,3,5), or combinations (1-3,5,7-9). Indices are 1-based.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        metavar="QUESTION",
        help="Ask a custom question directly and get JSON response without HTML report. Example: --prompt 'tell me about MECP2'",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=1,
        metavar="N",
        help="Maximum number of concurrent test executions (default: 4 for most providers, 1 for Bedrock). "
        "Bedrock has strict rate limits and connection pool constraints (max 10 connections). "
        "Increase for faster execution if API rate limits allow, but be cautious with Bedrock.",
    )

    parser.add_argument(
        "--with-vanilla",
        action="store_true",
        help="Run tests in both vanilla mode (without tool calling) and with tool calling, then combine results for comparison.",
    )

    parser.add_argument(
        "--with-web",
        action="store_true",
        help="Run tests in three modes: vanilla (no tools, no web), web search (:online suffix), and MARRVEL-MCP (with tools). Creates 3-way comparison.",
    )

    parser.add_argument(
        "--multi-model",
        action="store_true",
        help="Run tests with multiple LLM models across all three modes (vanilla, web, MARRVEL-MCP). Each model * mode combination is tested. Results are shown in a grid format.",
    )

    parser.add_argument(
        "--models-config",
        type=str,
        metavar="PATH",
        help="Path to models configuration YAML file for --multi-model mode. Defaults to mcp-llm-test/models_config.yaml",
    )

    return parser.parse_args()


async def main():
    """
    Main function to run the evaluation concurrently.
    """
    global llm, llm_web, llm_evaluator, OPENROUTER_API_KEY

    # Parse command-line arguments
    args = parse_arguments()

    # Configure API keys (after argument parsing so --help works)
    # Note: Provider-specific credential validation is done later
    # This preserves backward compatibility for OpenRouter-only usage
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

    # Configure LLM with provider abstraction
    # Re-resolve model config inside main to respect any env var changes that occurred
    # after module import (e.g., in CI or wrapper scripts).
    resolved_model, provider = get_default_model_config()

    # Configure evaluator LLM (separate from models being tested)
    evaluator_model, evaluator_provider = get_evaluation_model_config()

    # Validate provider credentials before proceeding
    from config.llm_providers import validate_provider_credentials

    try:
        validate_provider_credentials(provider)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    # Validate evaluator provider credentials
    try:
        validate_provider_credentials(evaluator_provider)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return

    # Create LLM instances using the provider abstraction
    llm = create_llm_instance(
        provider=provider,
        model_id=resolved_model,
        temperature=0,
    )

    # Create web-enabled LLM if provider supports it
    provider_config = get_provider_config(provider)
    if provider_config.supports_web_search:
        llm_web = create_llm_instance(
            provider=provider,
            model_id=resolved_model,
            temperature=0,
            web_search=True,
        )
    else:
        # Fall back to regular LLM if web search is not supported
        llm_web = llm

    # Create dedicated evaluator LLM instance for consistent evaluation
    llm_evaluator = create_llm_instance(
        provider=evaluator_provider,
        model_id=evaluator_model,
        temperature=0,
    )

    # Display configuration
    if provider == "openrouter":
        if resolved_model != DEFAULT_MODEL:
            print(f"🔧 Using overridden OpenRouter model: {resolved_model}")
        else:
            print(f"✨ Using default OpenRouter model: {resolved_model}")
    else:
        print(f"🔧 Using provider: {provider}, model: {resolved_model}")

    # Display evaluator configuration
    print(f"📊 Evaluator: {evaluator_provider} / {evaluator_model}")

    if args.with_web:
        print(f"🌐 Web search enabled for comparison (model: {resolved_model}:online)")
        print(
            f"⚠️  Note: Not all models support web search. Check OpenRouter docs for compatibility."
        )
        print(
            f"   Models known to support :online - OpenAI (gpt-4, gpt-3.5-turbo, etc), Anthropic Claude"
        )
        print(f"   If you see empty responses, try a different model that supports web search.")

    # Clear cache if requested
    if args.clear:
        clear_cache()
        return  # Exit without running any tests

    # Handle --prompt mode (ad-hoc question)
    if args.prompt:
        print(f"🔍 Processing prompt: {args.prompt}")
        print("=" * 80)

        # Create MCP server and client
        mcp_server = create_server()
        mcp_client = Client(mcp_server)

        async with mcp_client:
            try:
                response, tool_history, conversation, tokens_used, metadata = (
                    await get_langchain_response(mcp_client, args.prompt)
                )

                # Output as JSON
                result = {
                    "question": args.prompt,
                    "response": response,
                    "tool_calls": tool_history,
                    "conversation": conversation,
                    "tokens_used": tokens_used,
                    "metadata": metadata,
                }

                print("\n📊 RESULT (JSON):")
                print(json.dumps(result, indent=2))
                print("\n" + "=" * 80)

            except TokenLimitExceeded as e:
                print(f"❌ Token limit exceeded: {e.token_count:,} > {MAX_TOKENS:,}")
                print("   Please reduce the complexity of your question or context.")
            except Exception as e:
                print(f"❌ Error processing prompt: {e}")
                import traceback

                traceback.print_exc()

        return  # Exit after handling prompt

    # Load test cases
    test_cases_path = Path(__file__).parent / "test_cases.yaml"
    with open(test_cases_path, "r", encoding="utf-8") as f:
        all_test_cases = yaml.safe_load(f)

    # Filter test cases if subset is specified
    if args.subset:
        try:
            subset_indices = parse_subset(args.subset, len(all_test_cases))
            test_cases = [all_test_cases[i] for i in subset_indices]
            print(f"📋 Running subset: {len(test_cases)}/{len(all_test_cases)} test cases")
            print(f"   Indices (1-based): {', '.join(str(i+1) for i in subset_indices)}")
        except ValueError as e:
            print(f"❌ Error parsing subset: {e}")
            return
    else:
        test_cases = all_test_cases

    # Create MCP server and client
    mcp_server = create_server()
    mcp_client = Client(mcp_server)

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(args.concurrency)

    # Determine whether to use cache
    use_cache = args.cache

    # Handle --multi-model mode: test multiple models across all three modes
    if args.multi_model:
        # Load models configuration
        try:
            models_config_path = Path(args.models_config) if args.models_config else None
            models, yaml_evaluator_config = load_models_config(models_config_path)

            # Override evaluator configuration from YAML if provided
            if (
                yaml_evaluator_config
                and "provider" in yaml_evaluator_config
                and "model" in yaml_evaluator_config
            ):
                yaml_provider = yaml_evaluator_config["provider"]
                yaml_model = yaml_evaluator_config["model"]
                print(f"🔄 Overriding evaluator from YAML config: {yaml_provider} / {yaml_model}")

                # Validate and create new evaluator instance
                try:
                    from config.llm_providers import validate_provider_credentials

                    validate_provider_credentials(yaml_provider)

                    # Update global evaluator variables
                    evaluator_model = yaml_model
                    evaluator_provider = yaml_provider
                    llm_evaluator = create_llm_instance(
                        provider=yaml_provider,
                        model_id=yaml_model,
                        temperature=0,
                    )
                    print(f"✅ Evaluator updated: {yaml_provider} / {yaml_model}")
                except Exception as e:
                    print(f"⚠️  Warning: Failed to apply YAML evaluator config: {e}")
                    print(
                        f"   Continuing with environment/default evaluator: {evaluator_provider} / {evaluator_model}"
                    )

            print(f"🎯 Multi-Model Testing Mode")
            print(f"   Models to test: {len(models)}")
            for model in models:
                print(f"     • {model['name']} ({model['id']})")
            print(f"   Test cases: {len(test_cases)}")
            print(f"   Modes per model: 3 (vanilla, web, MARRVEL-MCP)")
            print(
                f"   Total evaluations: {len(models)} models × 3 modes × {len(test_cases)} tests = {len(models) * 3 * len(test_cases)}"
            )
            print(f"   Concurrency: {args.concurrency}")
            print(
                f"💾 Cache {'enabled (--cache)' if use_cache else 'disabled - re-running all tests'}"
            )
        except ValueError as e:
            print(f"❌ Error loading models configuration: {e}")
            return

        # Dictionary to store results for each model
        all_models_results = {}

        async with mcp_client:
            # Create all LLM instances upfront for each model
            print(f"\n🚀 Creating LLM instances for all models...")
            model_llm_instances = {}
            for model_config in models:
                model_id = model_config["id"]
                model_provider = model_config.get("provider", "openrouter")

                # Validate provider credentials for each model
                try:
                    from config.llm_providers import validate_provider_credentials

                    validate_provider_credentials(model_provider)
                except ValueError as e:
                    print(f"⚠️  Skipping model {model_id}: {e}")
                    continue

                # Create base LLM instance
                model_llm_instances[model_id] = {
                    "llm": create_llm_instance(
                        provider=model_provider,
                        model_id=model_id,
                        temperature=0,
                    ),
                    "llm_web": None,  # Will be set below if web search is supported
                }

                # Create web-enabled LLM if provider supports it
                provider_config = get_provider_config(model_provider)
                if provider_config.supports_web_search:
                    model_llm_instances[model_id]["llm_web"] = create_llm_instance(
                        provider=model_provider,
                        model_id=model_id,
                        temperature=0,
                        web_search=True,
                    )
                else:
                    # Fall back to regular LLM
                    model_llm_instances[model_id]["llm_web"] = model_llm_instances[model_id]["llm"]

            # Create ALL tasks at once (across all models, modes, and test cases)
            # This enables full parallelization!
            print(f"\n⚡ Creating task list for concurrent execution...")
            all_tasks = []
            task_metadata = []  # Track which task belongs to which model/mode/test

            for model_config in models:
                model_name = model_config["name"]
                model_id = model_config["id"]
                skip_web_search = model_config.get("skip_web_search", False)
                model_llm = model_llm_instances[model_id]["llm"]
                model_llm_web = model_llm_instances[model_id]["llm_web"]

                # Vanilla mode tasks
                for i, test_case in enumerate(test_cases):
                    task = run_test_case(
                        semaphore,
                        mcp_client,
                        test_case,
                        use_cache=use_cache,
                        vanilla_mode=True,
                        web_mode=False,
                        model_id=model_id,
                        pbar=None,
                        llm_instance=model_llm,
                        llm_web_instance=model_llm_web,
                    )
                    all_tasks.append(task)
                    task_metadata.append(
                        {
                            "model_id": model_id,
                            "model_name": model_name,
                            "mode": "vanilla",
                            "test_index": i,
                        }
                    )

                # Web mode tasks (or N/A placeholders if not supported)
                if skip_web_search:
                    # Don't create tasks, we'll fill in N/A results later
                    for i in enumerate(test_cases):
                        task_metadata.append(
                            {
                                "model_id": model_id,
                                "model_name": model_name,
                                "mode": "web",
                                "test_index": i[0],
                                "skip": True,
                            }
                        )
                else:
                    for i, test_case in enumerate(test_cases):
                        task = run_test_case(
                            semaphore,
                            mcp_client,
                            test_case,
                            use_cache=use_cache,
                            vanilla_mode=False,
                            web_mode=True,
                            model_id=model_id,
                            pbar=None,
                            llm_instance=model_llm,
                            llm_web_instance=model_llm_web,
                        )
                        all_tasks.append(task)
                        task_metadata.append(
                            {
                                "model_id": model_id,
                                "model_name": model_name,
                                "mode": "web",
                                "test_index": i,
                            }
                        )

                # Tool mode tasks
                for i, test_case in enumerate(test_cases):
                    task = run_test_case(
                        semaphore,
                        mcp_client,
                        test_case,
                        use_cache=use_cache,
                        vanilla_mode=False,
                        web_mode=False,
                        model_id=model_id,
                        pbar=None,
                        llm_instance=model_llm,
                        llm_web_instance=model_llm_web,
                    )
                    all_tasks.append(task)
                    task_metadata.append(
                        {
                            "model_id": model_id,
                            "model_name": model_name,
                            "mode": "tool",
                            "test_index": i,
                        }
                    )

            # Execute ALL tasks concurrently!
            print(
                f"\n🔥 Executing {len(all_tasks)} tasks concurrently (concurrency limit: {args.concurrency})..."
            )
            print(f"   This will run ALL models × modes × tests in parallel!")
            pbar_global = atqdm(total=len(all_tasks), desc="All tests", unit="test")

            # Run all tasks concurrently using gather, which preserves order
            # We'll update the progress bar as tasks complete using a callback
            # Add timeout to prevent hanging tasks
            async def run_task_with_progress(task):
                try:
                    # Set a timeout of 5 minutes per task
                    result = await asyncio.wait_for(task, timeout=300)
                    pbar_global.update(1)
                    return result
                except asyncio.TimeoutError:
                    pbar_global.update(1)
                    error_msg = "Task timed out after 5 minutes"
                    print(f"⏱️  {error_msg}")
                    return Exception(error_msg)
                except Exception as e:
                    pbar_global.update(1)
                    print(f"❌ Task failed: {e}")
                    return e

            # Wrap all tasks with progress tracking
            tasks_with_progress = [run_task_with_progress(task) for task in all_tasks]

            # Execute all tasks concurrently and get results in order
            # Use return_exceptions=True to prevent one failed task from blocking all others
            task_results = await asyncio.gather(*tasks_with_progress, return_exceptions=True)
            pbar_global.close()

            # Check for any exceptions in results and log them
            exception_count = 0
            for idx, result in enumerate(task_results):
                if isinstance(result, Exception):
                    exception_count += 1
                    print(f"⚠️  Task {idx} failed with exception: {result}")

            if exception_count > 0:
                print(
                    f"\n⚠️  Warning: {exception_count} task(s) failed with exceptions but execution continued."
                )

            # Map results back to their metadata indices (only non-skipped tasks have results)
            # Replace exceptions with error result objects
            results_map = {}
            task_idx = 0
            for metadata_idx, meta in enumerate(task_metadata):
                if not meta.get("skip", False):
                    result = task_results[task_idx]

                    # If the task failed with an exception, create an error result
                    if isinstance(result, Exception):
                        result = {
                            "status": "ERROR",
                            "reason": f"Task failed with exception: {str(result)}",
                            "response": f"ERROR: {str(result)}",
                            "classification": "ERROR",
                            "tokens_used": 0,
                            "tool_calls": [],
                            "conversation": [
                                {"role": "system", "content": "Error occurred during execution"},
                                {"role": "assistant", "content": f"ERROR: {str(result)}"},
                            ],
                        }

                    results_map[metadata_idx] = result
                    task_idx += 1

            # Reorganize results back into the expected structure
            print(f"\n📊 Organizing results...")
            result_index = 0
            for model_config in models:
                model_name = model_config["name"]
                model_id = model_config["id"]
                model_provider = model_config.get("provider", "openrouter")
                skip_web_search = model_config.get("skip_web_search", False)

                if model_id not in all_models_results:
                    all_models_results[model_id] = {
                        "name": model_name,
                        "id": model_id,
                        "provider": model_provider,
                        "vanilla": [],
                        "web": [],
                        "tool": [],
                    }

                # Collect results for this model (they're in order: vanilla, web, tool)
                # Vanilla results
                vanilla_results = []
                for i in range(len(test_cases)):
                    # Find the corresponding result
                    for idx, meta in enumerate(task_metadata):
                        if (
                            meta["model_id"] == model_id
                            and meta["mode"] == "vanilla"
                            and meta["test_index"] == i
                            and not meta.get("skip", False)
                        ):
                            vanilla_results.append(results_map[idx])
                            break
                all_models_results[model_id]["vanilla"] = vanilla_results

                # Web results
                if skip_web_search:
                    web_results = [
                        {
                            "status": "N/A",
                            "reason": "Web search not supported by this model",
                            "response": "N/A",
                            "classification": "N/A",
                            "tokens_used": 0,
                            "tool_calls": [],
                            "conversation": [],
                        }
                        for _ in test_cases
                    ]
                else:
                    web_results = []
                    for i in range(len(test_cases)):
                        for idx, meta in enumerate(task_metadata):
                            if (
                                meta["model_id"] == model_id
                                and meta["mode"] == "web"
                                and meta["test_index"] == i
                                and not meta.get("skip", False)
                            ):
                                web_results.append(results_map[idx])
                                break
                all_models_results[model_id]["web"] = web_results

                # Tool results
                tool_results = []
                for i in range(len(test_cases)):
                    for idx, meta in enumerate(task_metadata):
                        if (
                            meta["model_id"] == model_id
                            and meta["mode"] == "tool"
                            and meta["test_index"] == i
                        ):
                            tool_results.append(results_map[idx])
                            break
                all_models_results[model_id]["tool"] = tool_results

        # Combine results into multi-model format
        combined_results = []
        for i, test_case in enumerate(test_cases):
            test_result = {
                "question": test_case["case"]["input"],
                "expected": test_case["case"]["expected"],
                "models": {},
            }
            for model_id, model_data in all_models_results.items():
                test_result["models"][model_id] = {
                    "name": model_data["name"],
                    "provider": model_data["provider"],
                    "vanilla": model_data["vanilla"][i],
                    "web": model_data["web"][i],
                    "tool": model_data["tool"][i],
                }
            combined_results.append(test_result)

        # Generate HTML report with multi-model comparison
        try:
            html_path = generate_html_report(
                combined_results,
                multi_model=True,
                evaluator_model=evaluator_model,
                evaluator_provider=evaluator_provider,
            )
            open_in_browser(html_path)
        except Exception as e:
            print(f"--- Error generating HTML or opening browser: {e} ---")
            import traceback

            traceback.print_exc()

    # Handle --with-web mode: run vanilla, web, and tool modes (3-way comparison)
    elif args.with_web:
        print(
            f"🚀 Running {len(test_cases)} test case(s) with THREE modes: vanilla, web search, and MARRVEL-MCP"
        )
        print(f"   Concurrency: {args.concurrency}")
        print(f"💾 Cache {'enabled (--cache)' if use_cache else 'disabled - re-running all tests'}")

        async with mcp_client:
            # Run vanilla mode tests
            print("\n🍦 Running VANILLA mode (no tools, no web search)...")
            pbar_vanilla = atqdm(total=len(test_cases), desc="Vanilla mode", unit="test")

            vanilla_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    use_cache=use_cache,
                    vanilla_mode=True,
                    pbar=pbar_vanilla,
                )
                for test_case in test_cases
            ]
            vanilla_results = await asyncio.gather(*vanilla_tasks)
            pbar_vanilla.close()

            # Run web search mode tests
            print("\n🌐 Running WEB SEARCH mode (web search enabled via :online)...")
            pbar_web = atqdm(total=len(test_cases), desc="Web search mode", unit="test")

            web_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    use_cache=use_cache,
                    web_mode=True,
                    pbar=pbar_web,
                )
                for test_case in test_cases
            ]
            web_results = await asyncio.gather(*web_tasks)
            pbar_web.close()

            # Run tool mode tests
            print("\n🔧 Running MARRVEL-MCP mode (with specialized tools)...")
            pbar_tool = atqdm(total=len(test_cases), desc="Tool mode", unit="test")

            tool_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    use_cache=use_cache,
                    vanilla_mode=False,
                    pbar=pbar_tool,
                )
                for test_case in test_cases
            ]
            tool_results = await asyncio.gather(*tool_tasks)
            pbar_tool.close()

        # Combine results - create 3-way comparison
        combined_results = []
        for i, test_case in enumerate(test_cases):
            combined_results.append(
                {
                    "question": test_case["case"]["input"],
                    "expected": test_case["case"]["expected"],
                    "vanilla": vanilla_results[i],
                    "web": web_results[i],
                    "tool": tool_results[i],
                }
            )

        # Generate HTML report with 3-way comparison
        try:
            html_path = generate_html_report(
                combined_results,
                tri_mode=True,
                evaluator_model=evaluator_model,
                evaluator_provider=evaluator_provider,
            )
            open_in_browser(html_path)
        except Exception as e:
            print(f"--- Error generating HTML or opening browser: {e} ---")

    # Handle --with-vanilla mode: run both vanilla and tool modes
    elif args.with_vanilla:
        print(f"🚀 Running {len(test_cases)} test case(s) with BOTH vanilla and tool modes")
        print(f"   Concurrency: {args.concurrency}")
        print(f"💾 Cache {'enabled (--cache)' if use_cache else 'disabled - re-running all tests'}")

        async with mcp_client:
            # Run vanilla mode tests
            print("\n🍦 Running VANILLA mode (without tool calling)...")
            pbar_vanilla = atqdm(total=len(test_cases), desc="Vanilla mode", unit="test")

            vanilla_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    use_cache=use_cache,
                    vanilla_mode=True,
                    pbar=pbar_vanilla,
                )
                for test_case in test_cases
            ]
            vanilla_results = await asyncio.gather(*vanilla_tasks)
            pbar_vanilla.close()

            # Run tool mode tests
            print("\n🔧 Running TOOL mode (with tool calling)...")
            pbar_tool = atqdm(total=len(test_cases), desc="Tool mode", unit="test")

            tool_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    use_cache=use_cache,
                    vanilla_mode=False,
                    pbar=pbar_tool,
                )
                for test_case in test_cases
            ]
            tool_results = await asyncio.gather(*tool_tasks)
            pbar_tool.close()

        # Combine results - create paired results for comparison
        combined_results = []
        for i, test_case in enumerate(test_cases):
            combined_results.append(
                {
                    "question": test_case["case"]["input"],
                    "expected": test_case["case"]["expected"],
                    "vanilla": vanilla_results[i],
                    "tool": tool_results[i],
                }
            )

        # Generate HTML report with dual-mode results
        try:
            html_path = generate_html_report(
                combined_results,
                dual_mode=True,
                evaluator_model=evaluator_model,
                evaluator_provider=evaluator_provider,
            )
            open_in_browser(html_path)
        except Exception as e:
            print(f"--- Error generating HTML or opening browser: {e} ---")

    else:
        # Normal mode: run with tools only
        print(f"🚀 Running {len(test_cases)} test case(s) with concurrency={args.concurrency}")
        print(f"💾 Cache {'enabled (--cache)' if use_cache else 'disabled - re-running all tests'}")

        async with mcp_client:
            # Create progress bar
            pbar = atqdm(total=len(test_cases), desc="Evaluating tests", unit="test")

            tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    use_cache=use_cache,
                    vanilla_mode=False,
                    pbar=pbar,
                )
                for test_case in test_cases
            ]
            results = await asyncio.gather(*tasks)

            pbar.close()

        # Sort results to match the original order of test cases
        results_map = {res["question"]: res for res in results}
        ordered_results = [
            results_map[tc["case"]["input"]]
            for tc in test_cases
            if tc["case"]["input"] in results_map
        ]

        # Generate HTML report and open in browser
        try:
            html_path = generate_html_report(
                ordered_results,
                evaluator_model=evaluator_model,
                evaluator_provider=evaluator_provider,
            )
            open_in_browser(html_path)
        except Exception as e:
            print(f"--- Error generating HTML or opening browser: {e} ---")


if __name__ == "__main__":
    asyncio.run(main())
