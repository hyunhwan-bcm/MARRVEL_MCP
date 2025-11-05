"""Integration tests for evaluate_mcp.py CLI flags"""

import subprocess
import sys
from pathlib import Path

import pytest

# Path to the evaluate_mcp.py script
EVALUATE_SCRIPT = Path(__file__).parent.parent / "mcp-llm-test" / "evaluate_mcp.py"


def test_help_flag_works():
    """Test that --help flag works without requiring API credentials"""
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "MCP LLM Evaluation Script" in result.stdout
    assert "--clear" in result.stdout
    assert "--force" in result.stdout


def test_help_shows_examples():
    """Test that help text includes usage examples"""
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Examples:" in result.stdout
    assert "python evaluate_mcp.py --clear" in result.stdout
    assert "python evaluate_mcp.py --force" in result.stdout


def test_help_describes_clear_flag():
    """Test that --clear flag description is in help"""
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert (
        "Remove existing cache before starting tests" in result.stdout
        or "fresh run" in result.stdout
    )


def test_help_describes_force_flag():
    """Test that --force flag description is in help"""
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Ignore success entries in cache" in result.stdout or "rerun all jobs" in result.stdout


def test_clear_and_force_flags_accepted():
    """Test that both flags can be used together (script accepts the flags)"""
    # This test verifies the script accepts both flags without argument parsing errors
    # The script will fail due to missing API key, but that's after parsing succeeds
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), "--clear", "--force"],
        capture_output=True,
        text=True,
        timeout=30,  # Allow time for script to start and fail on API key
    )
    # Verify that the script accepted the flags (no argument error)
    # The script may succeed (returncode=0) if it generates an HTML report even with errors
    # or may fail (returncode!=0) - either way, no argument parsing errors
    assert "unrecognized arguments" not in result.stderr
    assert "invalid choice" not in result.stderr
    # Verify the script actually ran and tried to clear cache
    assert "cache" in result.stdout.lower() or result.returncode == 0
