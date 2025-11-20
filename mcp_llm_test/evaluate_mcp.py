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
import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import datetime
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
    CACHE_DIR,
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

    # Determine output directory and run ID
    if args.output_dir:
        # Use provided output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        # Extract or generate run ID from output directory name
        run_id = output_dir.name if not args.resume else args.resume
        print(f"📁 Output directory: {output_dir}")
    elif args.resume:
        run_id = args.resume
        output_dir = CACHE_DIR / run_id
        print(f"🔄 Resuming run: {run_id}")
        if args.retry_failed:
            print("   Re-running failed tests")
    else:
        # Generate new unique ID: short UUID (8 chars)
        run_id = str(uuid.uuid4())[:8]
        output_dir = CACHE_DIR / run_id
        print(f"🆔 Run ID: {run_id}")
        print(f"📁 Output directory: {output_dir}")

    # Configure LLM with provider abstraction
    # Re-resolve model config inside main to respect any env var changes that occurred
    # after module import (e.g., in CI or wrapper scripts).
    resolved_model, provider = get_default_model_config()

    # Apply explicit CLI overrides if provided (validated set: bedrock, openai, openrouter)
    if getattr(args, "provider", None):
        override_provider = args.provider.strip().lower()
        if override_provider not in {"bedrock", "openai", "openrouter"}:
            print(
                f"❌ Error: Unsupported provider override '{override_provider}'. Allowed: bedrock, openai, openrouter"
            )
            return
        provider = override_provider  # type: ignore
        print(f"🔧 Provider explicitly set to: {provider}")
    if getattr(args, "model", None):
        resolved_model = args.model.strip()
        print(f"🔧 Model explicitly set to: {resolved_model}")

    # Configure evaluator LLM (separate from models being tested)
    evaluator_model, evaluator_provider = get_evaluation_model_config()

    # Load YAML evaluator config and override if specified
    # This applies to ALL test modes for consistency (not just multi-model mode)
    models_config_path = None  # Removed --models-config argument during refactoring
    yaml_evaluator_config = load_evaluator_config_from_yaml(models_config_path)

    # Determine the actual YAML file path for logging
    yaml_file_path = Path(__file__).parent / "models_config.yaml"

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

    # Validate provider credentials before proceeding (after overrides)
    try:
        validate_provider_credentials(provider, api_key_override=getattr(args, "api_key", None))
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
    trace_enabled = os.getenv("OPENROUTER_TRACE") or os.getenv("LLM_TRACE")
    llm = create_llm_instance(
        provider=provider,
        model_id=resolved_model,
        temperature=0,
        api_key=getattr(args, "api_key", None),
        api_base=getattr(args, "api_base", None),
    )

    # Create web-enabled LLM if provider supports it
    provider_config = get_provider_config(provider)
    if provider_config.supports_web_search:
        llm_web = create_llm_instance(
            provider=provider,
            model_id=resolved_model,
            temperature=0,
            web_search=True,
            api_key=getattr(args, "api_key", None),
            api_base=getattr(args, "api_base", None),
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
    if trace_enabled:
        from config.llm_providers import get_api_base, get_api_key

        resolved_base = getattr(args, "api_base", None) or get_api_base(provider)
        resolved_key = getattr(args, "api_key", None) or get_api_key(provider)
        masked_key = (
            (resolved_key[:6] + "..." + resolved_key[-4:])
            if resolved_key and len(resolved_key) > 10
            else "(short/none)"
        )
        print(
            f"[LLM-TRACE] provider={provider} model={resolved_model} base={resolved_base or '(default)'} key={masked_key} web_supported={provider_config.supports_web_search}"
        )

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
        clear_cache(run_id if args.resume else None)
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

    # Load test cases with snapshotting and UUID generation
    run_dir = output_dir
    run_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path = run_dir / "test_cases.yaml"

    if args.resume:
        if not snapshot_path.exists():
            print(f"❌ Error: Snapshot not found for run {run_id}")
            print(f"   Expected: {snapshot_path}")
            return

        print(f"📂 Loading test cases from snapshot: {snapshot_path}")
        with open(snapshot_path, "r", encoding="utf-8") as f:
            all_test_cases = yaml.safe_load(f)
    else:
        # Load from source
        source_path = Path(__file__).parent / "test_cases.yaml"
        with open(source_path, "r", encoding="utf-8") as f:
            all_test_cases = yaml.safe_load(f)

        # Generate deterministic UUIDs and inject into test cases
        for tc in all_test_cases:
            # Create a deterministic hash based on the test case content
            # We use the 'case' dictionary which contains the definition
            case_content = json.dumps(tc["case"], sort_keys=True)
            tc_uuid = hashlib.md5(case_content.encode()).hexdigest()[:8]
            tc["uuid"] = tc_uuid

        # Save snapshot
        print(f"📸 Saving test case snapshot to: {snapshot_path}")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            yaml.dump(all_test_cases, f, sort_keys=False)

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
    # If resuming, default to using cache unless explicitly disabled (though we don't have a disable flag yet)
    # For now, just OR it with the cache flag
    use_cache = args.cache or bool(args.resume)

    # Handle --with-web mode: run vanilla, web, and tool modes (3-way comparison)
    if args.with_web:
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
                    run_id,
                    test_case["uuid"],
                    use_cache=use_cache,
                    retry_failed=args.retry_failed,
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
                    run_id,
                    test_case["uuid"],
                    use_cache=use_cache,
                    retry_failed=args.retry_failed,
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
                    run_id,
                    test_case["uuid"],
                    use_cache=use_cache,
                    retry_failed=args.retry_failed,
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
                tested_model=resolved_model,
                tested_provider=provider,
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
                    run_id,
                    test_case["uuid"],
                    use_cache=use_cache,
                    retry_failed=args.retry_failed,
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
                    run_id,
                    test_case["uuid"],
                    use_cache=use_cache,
                    retry_failed=args.retry_failed,
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
                tested_model=resolved_model,
                tested_provider=provider,
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
                    run_id,
                    test_case["uuid"],
                    use_cache=use_cache,
                    retry_failed=args.retry_failed,
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
                tested_model=resolved_model,
                tested_provider=provider,
            )
            open_in_browser(html_path)
        except Exception as e:
            print(f"--- Error generating HTML or opening browser: {e} ---")


if __name__ == "__main__":
    asyncio.run(main())
