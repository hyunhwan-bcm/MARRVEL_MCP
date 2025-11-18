"""
Evaluation modules for MARRVEL-MCP testing.

This package contains modular components extracted from the monolithic
evaluate_mcp.py script to improve maintainability and enable better
LLM-assisted development.

Modules:
- cache: Cache management for test results
- llm_retry: LLM invocation with exponential backoff retry logic
- evaluation: Core evaluation logic for test responses
- test_execution: Test case execution orchestration
- reporting: HTML report generation and browser integration
- config_loader: Configuration file loading
- cli: Command-line interface argument parsing
"""

# Version info
__version__ = "1.0.0"

# Public API - import key components
from .cache import (
    get_cache_path,
    load_cached_result,
    save_cached_result,
    clear_cache,
    CACHE_DIR,
)

from .llm_retry import invoke_with_throttle_retry

from .evaluation import (
    evaluate_response,
    get_langchain_response,
)

from .test_execution import run_test_case

from .reporting import (
    generate_html_report,
    open_in_browser,
)

from .config_loader import (
    load_models_config,
    load_evaluator_config_from_yaml,
)

from .cli import (
    parse_arguments,
    parse_subset,
)

__all__ = [
    # Cache management
    "get_cache_path",
    "load_cached_result",
    "save_cached_result",
    "clear_cache",
    "CACHE_DIR",
    # LLM retry
    "invoke_with_throttle_retry",
    # Evaluation
    "evaluate_response",
    "get_langchain_response",
    # Test execution
    "run_test_case",
    # Reporting
    "generate_html_report",
    "open_in_browser",
    # Config loading
    "load_models_config",
    "load_evaluator_config_from_yaml",
    # CLI
    "parse_arguments",
    "parse_subset",
]
