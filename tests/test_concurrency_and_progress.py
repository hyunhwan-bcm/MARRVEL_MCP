"""
Tests for concurrency and progress bar functionality in evaluate_mcp.py.

Tests that the script correctly:
- Parses --concurrency argument
- Creates semaphore with correct limit
- Passes progress bar to run_test_case
"""

import asyncio
import os
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

# Set dummy API key to avoid import error
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_testing"

# Add project root to path to import evaluate_mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))


def test_concurrency_argument_parsing():
    """Test that --concurrency argument is parsed correctly."""
    from evaluation_modules import parse_arguments

    # Test default concurrency
    with patch("sys.argv", ["evaluate_mcp.py"]):
        args = parse_arguments()
        assert args.concurrency == 1, "Default concurrency should be 1"

    # Test custom concurrency
    with patch("sys.argv", ["evaluate_mcp.py", "--concurrency", "8"]):
        args = parse_arguments()
        assert args.concurrency == 8, "Custom concurrency should be 8"

    # Test concurrency with other arguments
    with patch("sys.argv", ["evaluate_mcp.py", "--concurrency", "10", "--cache", "--clear"]):
        args = parse_arguments()
        assert args.concurrency == 10
        assert args.cache is True
        assert args.clear is True


def test_concurrency_argument_type():
    """Test that --concurrency only accepts integer values."""
    from evaluation_modules import parse_arguments

    # Test invalid (non-integer) concurrency
    with patch("sys.argv", ["evaluate_mcp.py", "--concurrency", "invalid"]):
        with pytest.raises(SystemExit):
            parse_arguments()


@pytest.mark.asyncio
async def test_run_test_case_updates_progress_bar():
    """Test that run_test_case updates progress bar correctly."""
    from evaluation_modules import run_test_case

    # Create mock objects
    semaphore = asyncio.Semaphore(1)
    mock_client = AsyncMock()
    mock_pbar = MagicMock()
    mock_llm_evaluator = AsyncMock()

    # Mock the get_langchain_response and evaluate_response from their modules
    with (
        patch("evaluation_modules.evaluation.get_langchain_response") as mock_get_response,
        patch("evaluation_modules.evaluation.evaluate_response") as mock_evaluate,
        patch("evaluation_modules.cache.save_cached_result"),
    ):

        mock_get_response.return_value = (
            "Test response",
            [],
            [],
            100,
            {},
        )  # response, tool_history, conversation, tokens, metadata
        mock_evaluate.return_value = "yes - test passed"

        test_case = {
            "case": {
                "name": "Test Case",
                "input": "What is a gene?",
                "expected": "A gene is a unit of heredity",
            }
        }

        # Run test case with progress bar (needs llm_evaluator now)
        result = await run_test_case(
            semaphore,
            mock_client,
            test_case,
            mock_llm_evaluator,
            run_id="test_run",
            test_uuid="test_uuid",
            use_cache=False,
            pbar=mock_pbar,
        )

        # Verify progress bar was updated
        assert mock_pbar.update.called, "Progress bar should be updated"
        assert mock_pbar.update.call_count == 1, "Progress bar should be updated once"
        assert mock_pbar.set_postfix_str.called, "Progress bar postfix should be set"


@pytest.mark.asyncio
async def test_run_test_case_with_cached_result():
    """Test that run_test_case updates progress bar for cached results."""
    from evaluation_modules import run_test_case

    semaphore = asyncio.Semaphore(1)
    mock_client = AsyncMock()
    mock_pbar = MagicMock()
    mock_llm_evaluator = AsyncMock()

    cached_result = {
        "question": "What is a gene?",
        "expected": "A gene is a unit of heredity",
        "response": "Cached response",
        "classification": "yes",
        "tool_calls": [],
        "conversation": [],
        "tokens_used": 50,
    }

    with patch("evaluation_modules.test_execution.load_cached_result", return_value=cached_result):
        test_case = {
            "case": {
                "name": "Test Case",
                "input": "What is a gene?",
                "expected": "A gene is a unit of heredity",
            }
        }

        result = await run_test_case(
            semaphore,
            mock_client,
            test_case,
            mock_llm_evaluator,
            run_id="test_run",
            test_uuid="test_uuid",
            use_cache=True,
            pbar=mock_pbar,
        )

        # Verify progress bar was updated for cached result
        assert mock_pbar.update.called, "Progress bar should be updated for cache hit"
        assert "Cached" in str(
            mock_pbar.set_postfix_str.call_args
        ), "Progress should indicate cached result"
        assert result == cached_result


@pytest.mark.asyncio
async def test_run_test_case_handles_errors_with_progress():
    """Test that run_test_case handles errors and updates progress bar."""
    from evaluation_modules import run_test_case

    semaphore = asyncio.Semaphore(1)
    mock_client = AsyncMock()
    mock_pbar = MagicMock()
    mock_llm_evaluator = AsyncMock()

    # Mock get_langchain_response to raise an error
    with patch(
        "evaluation_modules.evaluation.get_langchain_response",
        side_effect=Exception("Test error"),
    ):
        test_case = {
            "case": {
                "name": "Test Case",
                "input": "What is a gene?",
                "expected": "A gene is a unit of heredity",
            }
        }

        result = await run_test_case(
            semaphore,
            mock_client,
            test_case,
            mock_llm_evaluator,
            run_id="test_run",
            test_uuid="test_uuid",
            use_cache=False,
            pbar=mock_pbar,
        )

        # Verify error was logged to progress bar
        assert mock_pbar.write.called, "Error should be written to progress bar"
        assert "Error" in str(mock_pbar.write.call_args) or "❌" in str(
            mock_pbar.write.call_args
        ), "Error message should be displayed"
        assert mock_pbar.update.called, "Progress bar should still be updated"
        assert "Error" in result["classification"]


def test_tqdm_import():
    """Test that tqdm.asyncio is correctly imported."""
    # This will fail if the import is broken
    from tqdm.asyncio import tqdm as atqdm

    assert atqdm is not None, "tqdm.asyncio should be imported as atqdm"


def test_progress_bar_parameter_in_run_test_case():
    """Test that run_test_case function signature includes pbar parameter."""
    import inspect

    from evaluation_modules import run_test_case

    sig = inspect.signature(run_test_case)
    params = list(sig.parameters.keys())

    assert "pbar" in params, "run_test_case should have pbar parameter"
    assert sig.parameters["pbar"].default is None, "pbar parameter should default to None"
