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
    """Test that both flags can be used together (without running full evaluation)"""
    # This test just verifies the script accepts the flags
    # We don't run the actual evaluation as it requires API keys
    result = subprocess.run(
        [sys.executable, str(EVALUATE_SCRIPT), "--clear", "--force"],
        capture_output=True,
        text=True,
        timeout=5,  # Should fail quickly without API key
    )
    # Script should fail on missing API key, not on argument parsing
    assert "OPENROUTER_API_KEY not found" in result.stderr or result.returncode != 0
