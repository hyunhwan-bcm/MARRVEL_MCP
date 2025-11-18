"""
Unit tests for HTML report generation in evaluate_mcp.py

Tests that the HTML report generation loads the template from the assets
directory and correctly replaces placeholders with test data.
"""

import os
import sys
from pathlib import Path

import pytest

# Set dummy API key to avoid import error
os.environ["OPENROUTER_API_KEY"] = "dummy_key_for_testing"

# Add project root to path to import evaluate_mcp
sys.path.insert(0, str(Path(__file__).parent.parent / "mcp_llm_test"))

from evaluation_modules import generate_html_report


def test_html_template_exists():
    """Test that the HTML template file exists in the assets directory."""
    template_path = Path(__file__).parent.parent / "assets" / "evaluation_report_template.html"
    assert template_path.exists(), f"Template file not found at {template_path}"


def test_generate_html_report_with_sample_data():
    """Test HTML report generation with sample test results."""
    # Sample test results
    sample_results = [
        {
            "question": "What is TP53?",
            "expected": "A tumor suppressor gene",
            "response": "TP53 is a tumor suppressor gene that encodes the p53 protein.",
            "classification": "yes, the response correctly identifies TP53 as a tumor suppressor gene",
            "tool_calls": [{"name": "get_gene_by_symbol", "args": {"gene_symbol": "TP53"}}],
            "conversation": [
                {"role": "user", "content": "What is TP53?"},
                {"role": "assistant", "content": "TP53 is a tumor suppressor gene."},
            ],
        },
        {
            "question": "What is BRCA1?",
            "expected": "A breast cancer gene",
            "response": "BRCA1 is a different gene unrelated to breast cancer",
            "classification": "no, the response is incorrect",
            "tool_calls": [],
            "conversation": [
                {"role": "user", "content": "What is BRCA1?"},
                {"role": "assistant", "content": "BRCA1 is unrelated to breast cancer"},
            ],
        },
    ]

    # Generate HTML report
    html_path = generate_html_report(sample_results)

    try:
        # Verify the file was created
        assert os.path.exists(html_path), f"HTML file not created at {html_path}"

        # Read the generated HTML
        with open(html_path, "r") as f:
            html_content = f.read()

        # Verify key elements are present in the HTML
        assert "<!DOCTYPE html>" in html_content
        assert "<title>Evaluation Results</title>" in html_content
        assert "Evaluation Results" in html_content
        assert "Success Rate" in html_content

        # Verify questions are in the HTML
        assert "What is TP53?" in html_content
        assert "What is BRCA1?" in html_content

        # Verify responses are in the HTML
        assert "tumor suppressor gene" in html_content

        # Verify success rate calculation (1 out of 2 = 50%)
        assert "50.0%" in html_content
        assert "Passed:" in html_content
        assert ">1<" in html_content  # 1 successful test
        assert ">2<" in html_content  # 2 total tests

        # Verify Tailwind CSS is included
        assert "cdn.tailwindcss.com" in html_content

        # Verify modal functionality
        assert "openModal" in html_content
        assert "closeModal" in html_content

    finally:
        # Clean up the temporary HTML file
        if os.path.exists(html_path):
            os.unlink(html_path)


def test_html_report_handles_empty_results():
    """Test that HTML report generation handles empty results gracefully."""
    empty_results = []

    # Generate HTML report with empty results
    html_path = generate_html_report(empty_results)

    try:
        # Verify the file was created
        assert os.path.exists(html_path), f"HTML file not created at {html_path}"

        # Read the generated HTML
        with open(html_path, "r") as f:
            html_content = f.read()

        # Verify basic structure is present
        assert "<!DOCTYPE html>" in html_content
        assert "Evaluation Results" in html_content

        # Verify success rate shows 0 when no tests
        # The calculation should handle division by zero
        assert "Success Rate" in html_content

    finally:
        # Clean up the temporary HTML file
        if os.path.exists(html_path):
            os.unlink(html_path)


def test_html_report_escapes_special_characters():
    """Test that HTML report properly escapes special characters."""
    results_with_special_chars = [
        {
            "question": "Test <script>alert('xss')</script>",
            "expected": "Safe & secure",
            "response": "Response with <tags> & special chars",
            "classification": "yes",
            "tool_calls": [],
            "conversation": [],
        }
    ]

    html_path = generate_html_report(results_with_special_chars)

    try:
        with open(html_path, "r") as f:
            html_content = f.read()

        # Verify that special characters are escaped
        # The actual <script> tag in the question should be escaped
        assert "&lt;script&gt;" in html_content or "alert(&#x27;xss&#x27;)" in html_content
        assert "&amp;" in html_content  # & should be escaped
        assert "&lt;tags&gt;" in html_content  # <tags> should be escaped

    finally:
        if os.path.exists(html_path):
            os.unlink(html_path)


def test_multi_model_report_has_export_buttons():
    """Test that multi-model HTML report includes CSV/TSV export buttons."""
    # Sample multi-model results
    multi_model_results = [
        {
            "question": "What is TP53?",
            "expected": "A tumor suppressor gene",
            "models": {
                "gpt-4": {
                    "name": "GPT-4",
                    "provider": "openai",
                    "vanilla": {
                        "response": "TP53 is a tumor suppressor gene.",
                        "classification": "yes",
                        "tokens_used": 100,
                        "tool_calls": [],
                        "conversation": [],
                    },
                    "web": {
                        "response": "TP53 is a tumor suppressor gene.",
                        "classification": "yes",
                        "tokens_used": 120,
                        "tool_calls": [],
                        "conversation": [],
                    },
                    "tool": {
                        "response": "TP53 is a tumor suppressor gene that encodes p53.",
                        "classification": "yes",
                        "tokens_used": 150,
                        "tool_calls": [{"name": "get_gene_by_symbol"}],
                        "conversation": [],
                    },
                },
            },
        }
    ]

    # Generate multi-model HTML report
    html_path = generate_html_report(
        multi_model_results,
        multi_model=True,
        evaluator_model="gpt-4",
        evaluator_provider="openai",
    )

    try:
        # Verify the file was created
        assert os.path.exists(html_path), f"HTML file not created at {html_path}"

        # Read the generated HTML
        with open(html_path, "r") as f:
            html_content = f.read()

        # Verify export buttons are present
        assert "Export CSV" in html_content
        assert "Export TSV" in html_content
        assert "onclick=\"exportResults('csv')\"" in html_content
        assert "onclick=\"exportResults('tsv')\"" in html_content

        # Verify export function is defined
        assert "function exportResults(format)" in html_content
        assert "function escapeField(field, delimiter)" in html_content

        # Verify data attributes are present for export functionality
        assert 'data-multi-model="true"' in html_content
        assert "data-model-id=" in html_content
        assert "data-model-name=" in html_content
        assert "data-vanilla-rate=" in html_content
        assert "data-web-rate=" in html_content
        assert "data-tool-rate=" in html_content

        # Verify multi-model comparison structure
        assert "Multi-Model Comparison" in html_content
        assert "GPT-4" in html_content

    finally:
        # Clean up the temporary HTML file
        if os.path.exists(html_path):
            os.unlink(html_path)
