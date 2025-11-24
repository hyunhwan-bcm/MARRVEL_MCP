"""
HTML report generation and browser integration.

This module handles generating HTML reports from test results
and opening them in a web browser.
"""

import json
import logging
import os
import re
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Environment, FileSystemLoader
from marrvel_mcp import parse_tool_result_content


def generate_html_report(
    results: List[Dict[str, Any]],
    dual_mode: bool = False,
    tri_mode: bool = False,
    multi_model: bool = False,
    evaluator_model: str | None = None,
    evaluator_provider: str | None = None,
    tested_model: str | None = None,
    tested_provider: str | None = None,
) -> str:
    """Generate HTML report with modal popups, reordered columns, and success rate summary.

    Args:
        results: List of test results
        dual_mode: If True, results contain both vanilla and tool mode responses
        tri_mode: If True, results contain vanilla, web, and tool mode responses
        multi_model: If True, results contain multiple models across all three modes
        evaluator_model: Model ID used for evaluation/grading
        evaluator_provider: Provider used for evaluation model
        tested_model: Model ID being tested (MCP model)
        tested_provider: Provider of the model being tested

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

                # Skip counting N/A vanilla results
                if model_data["vanilla"].get("status") != "N/A" and re.search(
                    r"\byes\b", vanilla_classification
                ):
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
                        "is_na": vanilla_res.get("status") == "N/A",
                        "na_reason": vanilla_res.get("reason", ""),
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
                # Surface serialized LangChain messages (prefer tool mode; fallback to any present)
                "serialized_messages": result.get(
                    "serialized_messages", tool_res.get("serialized_messages", [])
                ),
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
                "serialized_messages": result.get(
                    "serialized_messages", tool_res.get("serialized_messages", [])
                ),
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
                "serialized_messages": result.get("serialized_messages", []),
            }
            enriched_results.append(enriched_result)

    # Load and render Jinja2 template
    # Find the assets directory relative to this module
    # The module is in mcp_llm_test/evaluation_modules, assets is in project root
    template_path = Path(__file__).parent.parent.parent / "assets"
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
            tested_model=tested_model,
            tested_provider=tested_provider,
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
            tested_model=tested_model,
            tested_provider=tested_provider,
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
            tested_model=tested_model,
            tested_provider=tested_provider,
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
            tested_model=tested_model,
            tested_provider=tested_provider,
        )

    temp_html.write(html_content)
    temp_html.close()
    logging.info(f"HTML report saved to: {html_path}")
    return html_path


def open_in_browser(html_path: str):
    """Open the HTML file in the default browser."""
    webbrowser.open(f"file://{os.path.abspath(html_path)}")
    logging.info(f"Opened {html_path} in browser")
