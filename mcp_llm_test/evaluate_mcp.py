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

from export_json import build_export_json

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

    # Configure logging based on flags/environment
    quiet_enabled = getattr(args, "quiet", False)
    debug_enabled = (args.debug_timing and not quiet_enabled) or (
        os.getenv("DEBUG", "").lower() in ("1", "true", "yes") and not quiet_enabled
    )
    verbose_enabled = args.verbose and not quiet_enabled

    if quiet_enabled:
        logging.basicConfig(level=logging.ERROR, format="%(levelname)s - %(message)s")
        # Suppress warnings and noisy third-party loggers
        import warnings

        warnings.filterwarnings("ignore")
        # Propagate quiet intent to submodules that check env vars
        os.environ["QUIET"] = "1"
        for noisy in [
            "langchain",
            "httpx",
            "urllib3",
            "fastmcp",
            "asyncio",
        ]:
            logging.getLogger(noisy).setLevel(logging.ERROR)
    elif debug_enabled:
        logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
        logging.debug(
            "🐛 Debug logging enabled - showing detailed timing and diagnostic information"
        )
        if os.getenv("DEBUG"):
            logging.debug("(via DEBUG environment variable)")
    elif verbose_enabled:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
        logging.info("📢 Verbose mode enabled - showing detailed error messages")
    else:
        logging.basicConfig(level=logging.WARNING)

    # Helper for conditional info output (suppressed in quiet mode)
    def vprint(*a, **k):
        if not quiet_enabled:
            print(*a, **k)

    # Determine output directory and run ID
    if args.output_dir:
        # Use provided output directory
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        # Extract or generate run ID from output directory name
        run_id = output_dir.name if not args.resume else args.resume
        vprint(f"📁 Output directory: {output_dir}")
    elif args.resume:
        run_id = args.resume
        output_dir = CACHE_DIR / run_id
        vprint(f"🔄 Resuming run: {run_id}")
        if args.retry_failed:
            vprint("   Re-running failed tests")
    else:
        # Generate new unique ID: short UUID (8 chars)
        run_id = str(uuid.uuid4())[:8]
        output_dir = CACHE_DIR / run_id
        vprint(f"🆔 Run ID: {run_id}")
        vprint(f"📁 Output directory: {output_dir}")

    # Canonical run metadata/cache directory (stable regardless of --output-dir)
    run_dir = CACHE_DIR / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    mirror_metadata_to_output = output_dir.resolve() != run_dir.resolve()

    # Configure LLM with provider abstraction
    # Re-resolve model config inside main to respect any env var changes that occurred
    # after module import (e.g., in CI or wrapper scripts).
    resolved_model, provider = get_default_model_config()

    # Apply explicit CLI overrides if provided (validated set: bedrock, openai, openrouter)
    if getattr(args, "provider", None):
        override_provider = args.provider.strip().lower()
        if override_provider not in {
            "bedrock",
            "openai",
            "openrouter",
            "ollama",
            "lm-studio",
            "llama_cpp",
        }:
            logging.error(
                f"❌ Error: Unsupported provider override '{override_provider}'. Allowed: bedrock, openai, openrouter, ollama, lm-studio, llama_cpp"
            )
            return
        provider = override_provider  # type: ignore
        vprint(f"🔧 Provider explicitly set to: {provider}")
    if getattr(args, "model", None):
        resolved_model = args.model.strip()
        vprint(f"🔧 Model explicitly set to: {resolved_model}")

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
            vprint(f"📊 Using evaluator from YAML: {yaml_provider}/{yaml_model}")
        except Exception as e:
            logging.warning(f"Failed to apply YAML evaluator config: {e}")
            vprint(
                f"⚠️  Continuing with environment/default evaluator: "
                f"{evaluator_provider} / {evaluator_model}"
            )
            # Reset overrides if validation failed
            evaluator_api_key_override = None
            evaluator_api_base_override = None

    # Validate provider credentials before proceeding (after overrides)
    try:
        validate_provider_credentials(provider, api_key_override=getattr(args, "api_key", None))
    except ValueError as e:
        logging.error(f"❌ Error validating provider credentials: {e}")
        return

    # Validate evaluator provider credentials
    try:
        validate_provider_credentials(evaluator_provider)
    except ValueError as e:
        logging.error(f"❌ Error validating evaluator credentials: {e}")
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
    vprint(f"🔧 Model: {provider} / {resolved_model}")
    if trace_enabled:
        from config.llm_providers import get_api_base, get_api_key

        resolved_base = getattr(args, "api_base", None) or get_api_base(provider)
        resolved_key = getattr(args, "api_key", None) or get_api_key(provider)
        masked_key = (
            (resolved_key[:6] + "..." + resolved_key[-4:])
            if resolved_key and len(resolved_key) > 10
            else "(short/none)"
        )
        logging.warning(
            f"[LLM-TRACE] provider={provider} model={resolved_model} base={resolved_base or '(default)'} key={masked_key} web_supported={provider_config.supports_web_search}"
        )

    if args.with_web:
        vprint(f"🌐 Web search enabled (model: {resolved_model}:online)")
        vprint(
            f"⚠️  Note: Not all models support web search - check provider docs for compatibility"
        )

    # Clear cache if requested
    if args.clear:
        clear_cache(run_id if args.resume else None)
        return  # Exit without running any tests

    # Handle --prompt mode (ad-hoc question)
    if args.prompt:
        vprint(f"🔍 Processing prompt: {args.prompt}")
        vprint("=" * 80)

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

                vprint("\n📊 RESULT (JSON):")
                if not quiet_enabled:
                    print(json.dumps(result, indent=2))  # large JSON omitted in quiet mode
                vprint("\n" + "=" * 80)

            except TokenLimitExceeded as e:
                logging.error(f"❌ Token limit exceeded: {e.token_count:,} > {100_000:,}")
                vprint("   Please reduce the complexity of your question or context.")
            except Exception as e:
                logging.error(f"❌ Error processing prompt: {e}")
                import traceback

                traceback.print_exc()

        return  # Exit after handling prompt

    # Determine whether to use cache
    # If resuming, default to using cache unless explicitly disabled (though we don't have a disable flag yet)
    # For now, just OR it with the cache flag
    use_cache = args.cache or bool(args.resume)

    # Load test cases with snapshotting and UUID generation
    snapshot_path = run_dir / "test_cases.yaml"
    output_snapshot_path = output_dir / "test_cases.yaml"

    if args.resume:
        if not snapshot_path.exists():
            # Backward compatibility: older runs might have snapshots only in output_dir
            if mirror_metadata_to_output and output_snapshot_path.exists():
                snapshot_path = output_snapshot_path
                vprint(f"📂 Loading legacy snapshot from output directory: {snapshot_path}")
            else:
                logging.error(f"❌ Error: Snapshot not found for run {run_id}")
                if not quiet_enabled:
                    print(f"   Expected: {snapshot_path}")
                return
        else:
            vprint(f"📂 Loading test cases from snapshot: {snapshot_path}")

        with open(snapshot_path, "r", encoding="utf-8") as f:
            all_test_cases = yaml.safe_load(f)
    else:
        # Load from source
        source_path = Path(args.test_cases)
        with open(source_path, "r", encoding="utf-8") as f:
            all_test_cases = yaml.safe_load(f)

        # Generate deterministic UUIDs and inject into test cases
        for tc in all_test_cases:
            # Create a deterministic hash based on the test case content
            # We use the 'case' dictionary which contains the definition
            case_content = json.dumps(tc["case"], sort_keys=True)
            tc_uuid = hashlib.md5(case_content.encode()).hexdigest()[:8]
            tc["uuid"] = tc_uuid

        # Save snapshot in the canonical cache run directory
        vprint(f"📸 Saving test case snapshot to: {snapshot_path}")
        with open(snapshot_path, "w", encoding="utf-8") as f:
            yaml.dump(all_test_cases, f, sort_keys=False)

        # Mirror snapshot to output directory for convenience when different
        if mirror_metadata_to_output:
            with open(output_snapshot_path, "w", encoding="utf-8") as f:
                yaml.dump(all_test_cases, f, sort_keys=False)
            vprint(f"📸 Mirroring test case snapshot to: {output_snapshot_path}")

    # Save/update run configuration for reproducibility
    run_config_path = run_dir / "run_config.yaml"
    existing_run_config = {}
    if run_config_path.exists():
        try:
            with open(run_config_path, "r", encoding="utf-8") as f:
                existing_run_config = yaml.safe_load(f) or {}
        except Exception as e:
            logging.warning(f"Failed to load existing run config from {run_config_path}: {e}")

    run_config = {
        "run_id": run_id,
        "created_at": existing_run_config.get("created_at", datetime.utcnow().isoformat() + "Z"),
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "is_resume": bool(args.resume),
        "resume_from_run_id": args.resume if args.resume else None,
        "cache_requested": bool(args.cache),
        "cache_enabled": bool(use_cache),
        "retry_failed": bool(args.retry_failed),
        "tested_model": resolved_model,
        "tested_provider": provider,
        "evaluator_model": evaluator_model,
        "evaluator_provider": evaluator_provider,
        "concurrency": args.concurrency,
        "only_vanilla": args.only_vanilla,
        "with_vanilla": args.with_vanilla,
        "with_web": args.with_web,
        "subset": args.subset,
        "output_dir": str(output_dir),
        "cache_run_dir": str(run_dir),
    }
    if getattr(args, "api_base", None):
        run_config["api_base"] = args.api_base

    with open(run_config_path, "w", encoding="utf-8") as f:
        yaml.dump(run_config, f, sort_keys=False)
    vprint(f"📋 Saving run config to: {run_config_path}")

    if mirror_metadata_to_output:
        output_run_config_path = output_dir / "run_config.yaml"
        with open(output_run_config_path, "w", encoding="utf-8") as f:
            yaml.dump(run_config, f, sort_keys=False)
        vprint(f"📋 Mirroring run config to: {output_run_config_path}")

    # Filter test cases if subset is specified
    if args.subset:
        try:
            subset_indices = parse_subset(args.subset, len(all_test_cases))
            test_cases = [all_test_cases[i] for i in subset_indices]
            vprint(
                f"📋 Running {len(test_cases)} out of {len(all_test_cases)} test cases: indices {', '.join(str(i+1) for i in subset_indices)}"
            )
        except ValueError as e:
            logging.error(f"❌ Error parsing subset: {e}")
            return
    else:
        test_cases = all_test_cases

    # Create MCP server and client
    mcp_server = create_server()
    mcp_client = Client(mcp_server)

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(args.concurrency)

    # Handle --with-web mode: run vanilla, web, and tool modes (3-way comparison)
    if args.with_web:
        vprint(
            f"🚀 Running {len(test_cases)} test case(s) with THREE modes: "
            f"vanilla, web search, and MARRVEL-MCP"
        )
        vprint(f"   Concurrency: {args.concurrency}")
        if use_cache:
            vprint(f"💾 Cache enabled")

        async with mcp_client:
            # Run vanilla mode tests
            vprint("\n🍦 Running VANILLA mode...")
            test_stats_vanilla = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats_vanilla,
                )
                for test_case in test_cases
            ]
            vanilla_results = await asyncio.gather(*vanilla_tasks)
            pbar_vanilla.close()

            # Run web search mode tests
            vprint("\n🌐 Running WEB SEARCH mode...")
            test_stats_web = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats_web,
                )
                for test_case in test_cases
            ]
            web_results = await asyncio.gather(*web_tasks)
            pbar_web.close()

            # Run tool mode tests
            vprint("\n🔧 Running MARRVEL-MCP mode...")
            test_stats_tool = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats_tool,
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
            logging.error(f"Error generating HTML or opening browser: {e}")

    # Handle --with-vanilla mode: run both vanilla and tool modes
    elif args.with_vanilla:
        vprint(f"🚀 Running {len(test_cases)} test case(s) with BOTH vanilla and tool modes")
        vprint(f"   Concurrency: {args.concurrency}")
        if use_cache:
            vprint(f"💾 Cache enabled")

        async with mcp_client:
            # Run vanilla mode tests
            vprint("\n🍦 Running VANILLA mode...")
            test_stats_vanilla = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats_vanilla,
                )
                for test_case in test_cases
            ]
            vanilla_results = await asyncio.gather(*vanilla_tasks)
            pbar_vanilla.close()

            # Run tool mode tests
            vprint("\n🔧 Running TOOL mode...")
            test_stats_tool = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats_tool,
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
            logging.error(f"Error generating HTML or opening browser: {e}")

    elif args.only_vanilla:
        vprint(f"🚀 Running {len(test_cases)} test case(s) with ONLY vanilla (no mcp tools)")
        vprint(f"   Concurrency: {args.concurrency}")
        if use_cache:
            vprint(f"💾 Cache enabled")

        async with mcp_client:
            # Run vanilla mode tests
            vprint("\n🍦 Running VANILLA mode...")
            test_stats_vanilla = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats_vanilla,
                )
                for test_case in test_cases
            ]
            vanilla_results = await asyncio.gather(*vanilla_tasks)
            pbar_vanilla.close()

        # Sort results to match the original order of test cases
        results_map = {res["question"]: res for res in vanilla_results}
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
            logging.error(f"Error generating HTML or opening browser: {e}")

    else:
        # Normal mode: run with tools only
        vprint(f"🚀 Running {len(test_cases)} test case(s) with concurrency={args.concurrency}")
        if use_cache:
            vprint(f"💾 Cache enabled")

        async with mcp_client:
            # Create progress bar and test statistics
            test_stats = {"yes": 0, "no": 0, "failed": 0}
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
                    test_stats=test_stats,
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
            logging.error(f"Error generating HTML or opening browser: {e}")

    # Export JSON if requested (applies to all code paths)
    if getattr(args, "export_json", None):
        try:
            run_metadata = {
                "tested_model": resolved_model,
                "tested_provider": provider,
                "evaluator_model": evaluator_model,
                "evaluator_provider": evaluator_provider,
                "concurrency": args.concurrency,
                "modes": [],
            }
            if args.with_web:
                run_metadata["modes"] = ["vanilla", "web", "tool"]
            elif args.with_vanilla:
                run_metadata["modes"] = ["vanilla", "tool"]
            else:
                run_metadata["modes"] = ["tool"]

            export_data = build_export_json(
                run_id=run_id,
                compact=True,
                run_metadata=run_metadata,
            )

            if args.export_json == "auto":
                json_path = Path(str(output_dir)) / "results.json"
            else:
                json_path = Path(args.export_json)
            json_path.parent.mkdir(parents=True, exist_ok=True)

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)

            vprint(f"📄 JSON export saved to: {json_path}")
        except Exception as e:
            logging.error(f"Error exporting JSON: {e}")


if __name__ == "__main__":
    asyncio.run(main())
