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

This script has been refactored into modular components in the evaluation_modules package:
- cache: Cache management for test results
- llm_retry: LLM invocation with exponential backoff retry logic
- evaluation: Core evaluation logic for test responses
- test_execution: Test case execution orchestration
- reporting: HTML report generation and browser integration
- config_loader: Configuration file loading
- cli: Command-line interface argument parsing
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import yaml
from dotenv import load_dotenv
from fastmcp.client import Client
from tqdm.asyncio import tqdm as atqdm

from marrvel_mcp.server import create_server
from config.llm_providers import (
    create_llm_instance,
    get_provider_config,
    validate_provider_credentials,
)
from config.llm_config import get_default_model_config, get_evaluation_model_config
from marrvel_mcp import TokenLimitExceeded

# Import all evaluation modules
from evaluation_modules import (
    # Cache management
    clear_cache,
    # Evaluation
    get_langchain_response,
    # Test execution
    run_test_case,
    # Reporting
    generate_html_report,
    open_in_browser,
    # Config loading
    load_models_config,
    load_evaluator_config_from_yaml,
    # CLI
    parse_arguments,
    parse_subset,
)

# Load environment variables from .env file
load_dotenv()


async def main():
    """
    Main function to run the evaluation concurrently.

    This orchestrator coordinates:
    1. Argument parsing and configuration loading
    2. LLM instance creation (tested models and evaluator)
    3. Test case loading and filtering
    4. Concurrent test execution across different modes
    5. HTML report generation
    """
    # Parse command-line arguments
    args = parse_arguments()

    # Configure logging based on --debug-timing flag or DEBUG environment variable
    debug_enabled = args.debug_timing or os.getenv("DEBUG", "").lower() in ("1", "true", "yes")
    verbose_enabled = args.verbose

    if debug_enabled:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
        print("🐛 Debug logging enabled - showing detailed timing and diagnostic information")
        if os.getenv("DEBUG"):
            print("   (via DEBUG environment variable)")
    elif verbose_enabled:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
        print("📢 Verbose mode enabled - showing detailed error messages")
    else:
        logging.basicConfig(level=logging.WARNING)

    # Configure LLM with provider abstraction
    # Re-resolve model config inside main to respect any env var changes that occurred
    # after module import (e.g., in CI or wrapper scripts).
    resolved_model, provider = get_default_model_config()

    # Configure evaluator LLM (separate from models being tested)
    evaluator_model, evaluator_provider = get_evaluation_model_config()

    # Load YAML evaluator config and override if specified
    # This applies to ALL test modes for consistency (not just multi-model mode)
    models_config_path = Path(args.models_config) if args.models_config else None
    yaml_evaluator_config = load_evaluator_config_from_yaml(models_config_path)

    # Determine the actual YAML file path for logging
    yaml_file_path = (
        models_config_path if models_config_path else Path(__file__).parent / "models_config.yaml"
    )

    # Extract evaluator overrides (api_key, api_base) from YAML config
    evaluator_api_key_override = None
    evaluator_api_base_override = None

    # Override evaluator configuration from YAML if provided
    if (
        yaml_evaluator_config
        and "provider" in yaml_evaluator_config
        and "model" in yaml_evaluator_config
    ):
        yaml_provider = yaml_evaluator_config["provider"]
        yaml_model = yaml_evaluator_config["model"]
        evaluator_api_key_override = yaml_evaluator_config.get("api_key")
        evaluator_api_base_override = yaml_evaluator_config.get("api_base")

        # Validate YAML evaluator provider before applying
        try:
            validate_provider_credentials(
                yaml_provider, api_key_override=evaluator_api_key_override
            )

            # Apply YAML evaluator config
            evaluator_model = yaml_model
            evaluator_provider = yaml_provider
            print(f"📊 Evaluator config loaded from YAML: {yaml_file_path}")
            print(f"   Using: {yaml_provider} / {yaml_model} (applies to ALL test modes)")
        except Exception as e:
            print(f"⚠️  Warning: Failed to apply YAML evaluator config: {e}")
            print(
                f"   Continuing with environment/default evaluator: "
                f"{evaluator_provider} / {evaluator_model}"
            )
            # Reset overrides if validation failed
            evaluator_api_key_override = None
            evaluator_api_base_override = None

    # Validate provider credentials before proceeding
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
        api_key=evaluator_api_key_override,
        api_base=evaluator_api_base_override,
    )

    # Display configuration - provider-agnostic messaging
    print(f"🔧 Model: {provider} / {resolved_model}")

    if args.with_web:
        print(f"🌐 Web search enabled for comparison (model: {resolved_model}:online)")
        print(
            f"⚠️  Note: Not all models support web search. "
            f"Check OpenRouter docs for compatibility."
        )
        print(
            f"   Models known to support :online - "
            f"OpenAI (gpt-4, gpt-3.5-turbo, etc), Anthropic Claude"
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
                    await get_langchain_response(
                        mcp_client, args.prompt, llm_instance=llm, llm_web_instance=llm_web
                    )
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
                print(f"❌ Token limit exceeded: {e.token_count:,} > {100_000:,}")
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
        # Note: Multi-model mode logic is extensive (~530 lines) and kept in main
        # for now to avoid excessive abstraction. Future refactoring could extract
        # this to a separate module if needed.
        print("⚠️  Multi-model mode is not yet fully refactored.")
        print("   Please use the original evaluate_mcp_backup.py for this mode.")
        print("   Or run without --multi-model to test the refactored code.")
    # Handle --multi-model mode: test multiple models across all three modes
    if args.multi_model:
        # Load models configuration
        try:
            models_config_path = Path(args.models_config) if args.models_config else None
            models, _ = load_models_config(models_config_path)

            # Note: Evaluator config is now loaded globally (before this mode)
            # and llm_evaluator is already created with the correct config

            print(f"📊 Evaluator: {evaluator_provider} / {evaluator_model}")
            print(f"🎯 Multi-Model Testing Mode")
            print(f"   Models to test: {len(models)}")
            for model in models:
                print(f"     • {model['name']} ({model['id']})")
            print(f"   Test cases: {len(test_cases)}")
            print(f"   Modes per model: 3 (vanilla, web, MARRVEL-MCP)")
            total_evals = len(models) * 3 * len(test_cases)
            print(
                f"   Total evaluations: {len(models)} models × 3 modes × "
                f"{len(test_cases)} tests = {total_evals}"
            )
            print(f"   Concurrency: {args.concurrency}")
            timeout_mins = args.timeout // 60
            print(f"   Timeout per test: {args.timeout} seconds ({timeout_mins} minutes)")
            cache_status = "enabled (--cache)" if use_cache else "disabled - re-running all tests"
            print(f"💾 Cache {cache_status}")
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

                # Extract per-model overrides from YAML config
                api_key_override = model_config.get("api_key")
                api_base_override = model_config.get("api_base")

                # Validate provider credentials for each model
                try:
                    validate_provider_credentials(model_provider, api_key_override=api_key_override)
                except ValueError as e:
                    print(f"⚠️  Skipping model {model_id}: {e}")
                    continue

                # Create base LLM instance with per-model overrides
                model_llm_instances[model_id] = {
                    "llm": create_llm_instance(
                        provider=model_provider,
                        model_id=model_id,
                        temperature=0,
                        api_key=api_key_override,
                        api_base=api_base_override,
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
                        api_key=api_key_override,
                        api_base=api_base_override,
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
                skip_vanilla = model_config.get("skip_vanilla", False)
                skip_web_search = model_config.get("skip_web_search", False)
                model_llm = model_llm_instances[model_id]["llm"]
                model_llm_web = model_llm_instances[model_id]["llm_web"]

                # Vanilla mode tasks (or N/A placeholders if not supported)
                if skip_vanilla:
                    # Don't create tasks, we'll fill in N/A results later
                    for i in enumerate(test_cases):
                        task_metadata.append(
                            {
                                "model_id": model_id,
                                "model_name": model_name,
                                "mode": "vanilla",
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
                            llm_evaluator,
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
                            llm_evaluator,
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
                        llm_evaluator,
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

            # Track test results for progress bar
            test_stats = {"yes": 0, "no": 0, "failed": 0}

            # For concurrency=1, use simple sequential execution to make debugging easier
            if args.concurrency == 1:
                # Filter out skipped tests - only include metadata entries that have actual tasks
                active_metadata = [meta for meta in task_metadata if not meta.get("skip", False)]

                print(
                    f"\n🔍 Running {len(all_tasks)} tests SEQUENTIALLY "
                    f"(concurrency=1 for easier debugging)..."
                )
                print("   Errors will be shown immediately as they occur.")
                if len(active_metadata) != len(all_tasks):
                    skipped_count = len(task_metadata) - len(active_metadata)
                    print(
                        f"   ⚠️  Note: {skipped_count} tests skipped "
                        f"(skip_vanilla or skip_web_search)"
                    )

                task_results = []
                for idx, (task, meta) in enumerate(zip(all_tasks, active_metadata)):
                    model_name = meta.get("model_name", "Unknown")
                    mode = meta.get("mode", "Unknown")
                    test_idx = meta.get("test_index", 0)
                    test_name = (
                        test_cases[test_idx]["case"]["name"]
                        if test_idx < len(test_cases)
                        else "Unknown"
                    )

                    print(
                        f"\n[{idx+1}/{len(all_tasks)}] {model_name} / {mode.upper()} / {test_name}"
                    )

                    try:
                        # Run task with timeout
                        result = await asyncio.wait_for(task, timeout=args.timeout)

                        # Track stats and show detailed output
                        if isinstance(result, dict) and "classification" in result:
                            # Show model's actual response
                            response = result.get("response", "")
                            if response:
                                response_preview = (
                                    response[:300] + "..." if len(response) > 300 else response
                                )
                                print(f"   📝 Model response: {response_preview}")

                            # Show tool calls if any
                            tool_calls = result.get("tool_calls", [])
                            if tool_calls:
                                tool_names = [tc.get("name", "unknown") for tc in tool_calls]
                                tools_str = ', '.join(tool_names)
                                num_calls = len(tool_calls)
                                print(f"   🔧 Tools called: {tools_str} ({num_calls} calls)")
                            elif mode == "tool":
                                print(f"   ⚠️  No tools called in TOOL mode")

                            # Show classification
                            classification = result.get("classification", "").lower()
                            if classification.startswith("yes"):
                                test_stats["yes"] += 1
                                print(f"   ✅ EVALUATOR: PASSED")
                            elif classification.startswith("no"):
                                test_stats["no"] += 1
                                print(f"   ❌ EVALUATOR: FAILED - {classification}")
                            else:
                                test_stats["failed"] += 1
                                print(f"   ⚠️  EVALUATOR: ERROR - {classification}")
                        elif isinstance(result, Exception):
                            test_stats["failed"] += 1
                            print(f"   ⚠ EXCEPTION: {result}")

                        task_results.append(result)

                    except asyncio.TimeoutError:
                        test_stats["failed"] += 1
                        error_msg = f"⏱️  TIMEOUT after {args.timeout}s"
                        print(f"   {error_msg}")
                        task_results.append(
                            Exception(f"Task timed out after {args.timeout} seconds")
                        )

                    except Exception as e:
                        test_stats["failed"] += 1
                        print(f"   ⚠ EXCEPTION: {e}")
                        task_results.append(e)

                # Print summary
                print(f"\n📊 Sequential Execution Complete:")
                print(f"   ✓ Passed: {test_stats['yes']}")
                print(f"   ✗ Failed: {test_stats['no']}")
                print(f"   ⚠ Errors/Timeouts: {test_stats['failed']}")

            else:
                # Filter out skipped tests - only include metadata entries that have actual tasks
                active_metadata = [meta for meta in task_metadata if not meta.get("skip", False)]

                # Execute ALL tasks concurrently!
                print(
                    f"\n🔥 Executing {len(all_tasks)} tasks concurrently "
                    f"(concurrency limit: {args.concurrency})..."
                )
                print(f"   This will run ALL models × modes × tests in parallel!")
                if len(active_metadata) != len(all_tasks):
                    skipped_count = len(task_metadata) - len(active_metadata)
                    print(
                        f"   ⚠️  Note: {skipped_count} tests skipped "
                        f"(skip_vanilla or skip_web_search)"
                    )
                pbar_global = atqdm(total=len(all_tasks), desc="All tests", unit="test")

                def update_progress_bar():
                    """Update progress bar with current test statistics."""
                    stats_str = (
                        f"✓ {test_stats['yes']} | "
                        f"✗ {test_stats['no']} | "
                        f"⚠ {test_stats['failed']}"
                    )
                    pbar_global.set_postfix_str(stats_str)

                # Run all tasks concurrently using gather, which preserves order
                # We'll update the progress bar as tasks complete using a callback
                # Add timeout to prevent hanging tasks
                async def run_task_with_progress(task, metadata):
                    try:
                        # Set a timeout per task (configurable via --timeout)
                        result = await asyncio.wait_for(task, timeout=args.timeout)

                        # Track success/failure based on classification
                        if isinstance(result, dict) and "classification" in result:
                            classification = result.get("classification", "").lower()
                            if classification.startswith("yes"):
                                test_stats["yes"] += 1
                            elif classification.startswith("no"):
                                test_stats["no"] += 1
                            else:
                                test_stats["failed"] += 1
                        elif isinstance(result, Exception):
                            test_stats["failed"] += 1

                        pbar_global.update(1)
                        update_progress_bar()
                        return result
                    except asyncio.TimeoutError:
                        test_stats["failed"] += 1
                        pbar_global.update(1)
                        update_progress_bar()

                        # Provide detailed information about which task timed out
                        model_name = metadata.get("model_name", "Unknown")
                        mode = metadata.get("mode", "Unknown")
                        test_idx = metadata.get("test_index", "?")
                        test_name = (
                            test_cases[test_idx]["case"]["name"]
                            if test_idx < len(test_cases)
                            else "Unknown"
                        )
                        error_msg = (
                            f"⏱️  TIMEOUT after {args.timeout}s ({args.timeout // 60}min): "
                            f"{model_name} / {mode} / Test #{test_idx + 1}: {test_name[:50]}"
                        )
                        print(error_msg)
                        print(
                            f"    💡 This usually means the API is slow or the query is complex. "
                            f"Try: --timeout {args.timeout * 2}"
                        )
                        return Exception(f"Task timed out after {args.timeout} seconds")
                    except Exception as e:
                        test_stats["failed"] += 1
                        pbar_global.update(1)
                        update_progress_bar()
                        print(f"❌ Task failed: {e}")
                        return e

                # Wrap all tasks with progress tracking and metadata
                # Only zip with active_metadata (skipped tests filtered out)
                tasks_with_progress = [
                    run_task_with_progress(task, meta)
                    for task, meta in zip(all_tasks, active_metadata)
                ]

                # Execute all tasks concurrently and get results in order
                # Use return_exceptions=True to prevent one failed task from blocking all others
                task_results = await asyncio.gather(*tasks_with_progress, return_exceptions=True)
                pbar_global.close()

                # Print summary statistics
                print(f"\n📊 Test Summary:")
                print(f"   ✓ Passed: {test_stats['yes']}")
                print(f"   ✗ Failed: {test_stats['no']}")
                print(f"   ⚠ Errors/Timeouts: {test_stats['failed']}")
                print(f"   Total: {len(all_tasks)}")

            # Check for any exceptions in results and log them
            exception_count = 0
            for idx, result in enumerate(task_results):
                if isinstance(result, Exception):
                    exception_count += 1
                    if debug_enabled:
                        print(f"⚠️  Task {idx} failed with exception: {result}")

            if exception_count > 0:
                print(
                    f"\n⚠️  Warning: {exception_count} task(s) failed with exceptions "
                    f"but execution continued."
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
                skip_vanilla = model_config.get("skip_vanilla", False)
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
                if skip_vanilla:
                    vanilla_results = [
                        {
                            "status": "N/A",
                            "reason": "Vanilla mode not supported by this model",
                            "response": "N/A",
                            "classification": "N/A",
                            "tokens_used": 0,
                            "tool_calls": [],
                            "conversation": [],
                        }
                        for _ in test_cases
                    ]
                else:
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

    # Handle --multi-model mode: test multiple models across all three modes
    if args.multi_model:
        # Note: Multi-model mode logic is extensive (~530 lines) and kept in main
        # for now to avoid excessive abstraction. Future refactoring could extract
        # this to a separate module if needed.
        print("⚠️  Multi-model mode is not yet fully refactored.")
        print("   Please use the original evaluate_mcp_backup.py for this mode.")
        print("   Or run without --multi-model to test the refactored code.")
        return

    # Handle --with-web mode: run vanilla, web, and tool modes (3-way comparison)
    elif args.with_web:
        print(
            f"🚀 Running {len(test_cases)} test case(s) with THREE modes: "
            f"vanilla, web search, and MARRVEL-MCP"
        )
        print(f"   Concurrency: {args.concurrency}")
        cache_status = "enabled (--cache)" if use_cache else "disabled - re-running all tests"
        print(f"💾 Cache {cache_status}")

        async with mcp_client:
            # Run vanilla mode tests
            print("\n🍦 Running VANILLA mode (no tools, no web search)...")
            pbar_vanilla = atqdm(total=len(test_cases), desc="Vanilla mode", unit="test")

            vanilla_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    llm_evaluator,
                    use_cache=use_cache,
                    vanilla_mode=True,
                    pbar=pbar_vanilla,
                    llm_instance=llm,
                    llm_web_instance=llm_web,
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
                    llm_evaluator,
                    use_cache=use_cache,
                    web_mode=True,
                    pbar=pbar_web,
                    llm_instance=llm,
                    llm_web_instance=llm_web,
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
                    llm_evaluator,
                    use_cache=use_cache,
                    vanilla_mode=False,
                    pbar=pbar_tool,
                    llm_instance=llm,
                    llm_web_instance=llm_web,
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
        cache_status = "enabled (--cache)" if use_cache else "disabled - re-running all tests"
        print(f"💾 Cache {cache_status}")

        async with mcp_client:
            # Run vanilla mode tests
            print("\n🍦 Running VANILLA mode (without tool calling)...")
            pbar_vanilla = atqdm(total=len(test_cases), desc="Vanilla mode", unit="test")

            vanilla_tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    llm_evaluator,
                    use_cache=use_cache,
                    vanilla_mode=True,
                    pbar=pbar_vanilla,
                    llm_instance=llm,
                    llm_web_instance=llm_web,
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
                    llm_evaluator,
                    use_cache=use_cache,
                    vanilla_mode=False,
                    pbar=pbar_tool,
                    llm_instance=llm,
                    llm_web_instance=llm_web,
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
        cache_status = "enabled (--cache)" if use_cache else "disabled - re-running all tests"
        print(f"💾 Cache {cache_status}")

        async with mcp_client:
            # Create progress bar
            pbar = atqdm(total=len(test_cases), desc="Evaluating tests", unit="test")

            tasks = [
                run_test_case(
                    semaphore,
                    mcp_client,
                    test_case,
                    llm_evaluator,
                    use_cache=use_cache,
                    vanilla_mode=False,
                    pbar=pbar,
                    llm_instance=llm,
                    llm_web_instance=llm_web,
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
