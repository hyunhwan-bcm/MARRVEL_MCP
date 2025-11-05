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

References:
- LangChain with OpenRouter: https://openrouter.ai/docs/community/lang-chain
- Tool calling: https://docs.langchain.com/oss/python/langchain/overview
- Evaluation: https://docs.langchain.com/oss/python/langchain/overview
"""

import asyncio
import json
import os
import sys
import tempfile
import uuid
import webbrowser
from typing import Any, Dict, List, Tuple

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import yaml
from dotenv import load_dotenv
from fastmcp.client import Client
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
import tiktoken

from server import create_server

# Load environment variables from .env file
load_dotenv()

# Configure API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY not found in environment variables. "
        "Please set it in a .env file or export it as an environment variable."
    )

MODEL = "google/gemini-2.5-flash"  # Switched to a model with guaranteed tool support
MAX_TOKENS = 100_000  # Maximum tokens allowed for evaluation to prevent API errors

# Configure LangChain ChatOpenAI with OpenRouter
llm = ChatOpenAI(
    model=MODEL,
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
    temperature=0,
)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count the number of tokens in a text string using tiktoken.
    Uses gpt-4 encoding as a reasonable approximation for most models.
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base encoding if model not found
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def validate_token_count(text: str, max_tokens: int = MAX_TOKENS) -> Tuple[bool, int]:
    """
    Validate that text doesn't exceed maximum token count.
    Returns (is_valid, token_count)
    """
    token_count = count_tokens(text)
    return token_count <= max_tokens, token_count


def convert_tool_to_langchain_format(tool: Any) -> Dict[str, Any]:
    """Converts a FastMCP tool to the LangChain/OpenAI tool format."""
    tool_dict = tool.model_dump(exclude_none=True)

    # Get the input schema which contains the parameters
    input_schema = tool_dict.get("inputSchema", {})

    return {
        "type": "function",
        "function": {
            "name": tool_dict.get("name"),
            "description": tool_dict.get("description"),
            "parameters": input_schema,
        },
    }


async def get_langchain_response(
    mcp_client: Client, user_input: str
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], int]:
    """
    Get response using LangChain with OpenRouter, handling tool calls via the MCP client.
    Returns: (final_response, tool_history, full_conversation)
    """
    # Initialize LangChain messages
    messages = [
        SystemMessage(
            content="You are a helpful genetics research assistant. You have access to tools that can query genetic databases and provide accurate information. Always use the available tools to answer questions about genes, variants, and genetic data. Do not make up or guess information - use the tools to get accurate data."
        ),
        HumanMessage(content=user_input),
    ]
    tool_history = []
    conversation = []

    # Get MCP tools and convert to LangChain format
    mcp_tools_list = await mcp_client.list_tools()
    available_tools = [convert_tool_to_langchain_format(tool) for tool in mcp_tools_list]

    # Debug: Print available tools count and first tool structure
    print(f"  Available tools: {len(available_tools)}")
    if len(available_tools) > 0:
        print(f"  Sample tools: {[t['function']['name'] for t in available_tools[:3]]}")
        print(f"  First tool structure: {json.dumps(available_tools[0], indent=2)[:500]}...")

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(available_tools)

    # Store initial messages in conversation history
    conversation.append({"role": "system", "content": messages[0].content})
    conversation.append({"role": "user", "content": user_input})

    # Helper function to ensure tool call has unique ID
    def ensure_tool_call_id(tool_call: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure tool call has a unique ID, adding one if needed."""
        if "id" not in tool_call or not tool_call["id"]:
            # Create a new dict with the ID added
            return {**tool_call, "id": f"call_{uuid.uuid4().hex[:12]}"}
        return tool_call

    # Agentic loop for tool calling
    max_iterations = 10
    for iteration in range(max_iterations):
        # Invoke LLM with current messages
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        # Check if there are tool calls
        if response.tool_calls:
            # Ensure all tool calls have unique IDs
            tool_calls_with_ids = [ensure_tool_call_id(tc) for tc in response.tool_calls]

            # Store assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"]),
                        },
                    }
                    for tc in tool_calls_with_ids
                ],
            }
            conversation.append(assistant_msg)

            # Execute each tool call
            for tool_call in tool_calls_with_ids:
                function_name = tool_call["name"]
                function_args = tool_call["args"]
                tool_call_id = tool_call["id"]

                tool_history.append({"name": function_name, "args": function_args})

                try:
                    # Call the MCP tool
                    tool_result = await mcp_client.call_tool(function_name, function_args)

                    # Serialize tool result to JSON string
                    if isinstance(tool_result.data, str):
                        content = tool_result.data
                    else:
                        content = json.dumps(tool_result.data, default=str)

                        # Validate token count for tool result
                        is_valid, token_count = validate_token_count(content)
                        if not is_valid:
                            # Truncate the content if it's too long
                            warning_msg = f"[WARNING: Tool result truncated - original size was {token_count:,} tokens, which exceeds the {MAX_TOKENS:,} token limit]\n\n"
                            # Keep only first portion that fits within limit
                            encoding = tiktoken.get_encoding("cl100k_base")
                            tokens = encoding.encode(content)
                            truncated_tokens = tokens[: MAX_TOKENS - 100]  # Leave room for warning
                            content = (
                                warning_msg
                                + encoding.decode(truncated_tokens)
                                + "\n\n[... content truncated ...]"
                            )

                    # Create LangChain ToolMessage
                    tool_message = ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    messages.append(tool_message)

                    # Store in conversation history
                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": content,
                        }
                    )
                except Exception as e:
                    # Handle tool execution error
                    error_content = json.dumps({"error": str(e)})
                    tool_message = ToolMessage(
                        content=error_content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    messages.append(tool_message)

                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": error_content,
                        }
                    )
        else:
            # No more tool calls - we have the final response
            final_content = response.content if hasattr(response, "content") else str(response)
            conversation.append({"role": "assistant", "content": final_content})
            # Compute total tokens used based on conversation contents
            try:
                conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
                tokens_total = count_tokens(conv_text)
            except Exception:
                tokens_total = 0
            return final_content, tool_history, conversation, tokens_total

    # If we hit max iterations without getting a final response, return the last message
    # Note: messages should never be empty here as we start with 2 messages and append responses
    if len(messages) > 2:  # More than just system and user messages
        last_msg = messages[-1]
        final_content = last_msg.content if hasattr(last_msg, "content") else str(last_msg)
    else:
        final_content = "No response generated after max iterations"

    # Always append to conversation for consistency
    conversation.append({"role": "assistant", "content": final_content})
    try:
        conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
        tokens_total = count_tokens(conv_text)
    except Exception:
        tokens_total = 0
    return final_content, tool_history, conversation, tokens_total


async def evaluate_response(actual: str, expected: str) -> str:
    """
    Evaluate the response using LangChain and return the classification text.
    Be flexible - if the actual response contains the expected information plus additional details, consider it acceptable.
    """
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
    response = await llm.ainvoke(messages)
    return response.content


async def run_test_case(
    semaphore: asyncio.Semaphore,
    mcp_client: Client,
    test_case: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Runs a single test case and returns the results for the table.
    """
    async with semaphore:
        name = test_case["case"]["name"]
        user_input = test_case["case"]["input"]
        expected = test_case["case"]["expected"]

        print(f"--- Running: {name} ---")

        try:
            langchain_response, tool_history, full_conversation, tokens_used = (
                await get_langchain_response(mcp_client, user_input)
            )
            classification = await evaluate_response(langchain_response, expected)
            print(f"--- Finished: {name} ---")
            return {
                "question": user_input,
                "expected": expected,
                "response": langchain_response,
                "classification": classification,
                "tool_calls": tool_history,
                "conversation": full_conversation,
                "tokens_used": tokens_used,
            }
        except Exception as e:
            print(f"--- Error in {name}: {e} ---")
            return {
                "question": user_input,
                "expected": expected,
                "response": "**No response generated due to error.**",
                "classification": f"**Error:** {e}",
                "tool_calls": [],
                "conversation": [],
            }


def generate_html_report(results: List[Dict[str, Any]]) -> str:
    """Generate HTML report with modal popups, reordered columns, and success rate summary."""
    import html as html_module
    import re

    # Create a temporary HTML file
    temp_html = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, prefix="evaluation_results_"
    )
    html_path = temp_html.name

    # Calculate success rate
    total_tests = len(results)
    successful_tests = 0

    for result in results:
        classification = result["classification"].lower()
        # Check if evaluation contains "yes" (flexible matching)
        if re.search(r"\byes\b", classification):
            successful_tests += 1

    success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

    # Build table rows
    rows_html = ""
    for idx, result in enumerate(results):
        question = html_module.escape(result["question"])
        expected = html_module.escape(result["expected"])
        response = html_module.escape(result.get("response", ""))
        classification = result["classification"]
        classification_escaped = html_module.escape(classification)
        tokens_used = result.get("tokens_used", 0)

        # Determine if evaluation is yes or no
        classification_lower = classification.lower()
        is_yes = re.search(r"\byes\b", classification_lower)

        # Create evaluation button with clear yes/no indicator
        if is_yes:
            eval_button = f"""
            <button class="inline-flex items-center gap-x-2 rounded-md bg-green-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-green-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-green-600">
                <svg class="-ml-0.5 h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fill-rule="evenodd" d="M16.704 4.153a.75.75 0 01.143 1.052l-8 10.5a.75.75 0 01-1.127.075l-4.5-4.5a.75.75 0 011.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 011.05-.143z" clip-rule="evenodd" />
                </svg>
                YES
            </button>
            <div class="mt-2 text-xs text-gray-600">{classification_escaped}</div>
            """
        else:
            eval_button = f"""
            <button class="inline-flex items-center gap-x-2 rounded-md bg-red-600 px-3.5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-red-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-red-600">
                <svg class="-ml-0.5 h-5 w-5" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.28 7.22a.75.75 0 00-1.06 1.06L8.94 10l-1.72 1.72a.75.75 0 101.06 1.06L10 11.06l1.72 1.72a.75.75 0 101.06-1.06L11.06 10l1.72-1.72a.75.75 0 00-1.06-1.06L10 8.94 8.28 7.22z" clip-rule="evenodd" />
                </svg>
                NO
            </button>
            <div class="mt-2 text-xs text-gray-600">{classification_escaped}</div>
            """

        # Tool calls summary
        tool_calls_list = result.get("tool_calls", [])
        if tool_calls_list:
            tool_calls_html = "<ul class='list-disc list-inside text-xs'>"
            for tc in tool_calls_list:
                tool_calls_html += f"<li><code class='bg-gray-100 px-1 rounded'>{html_module.escape(tc.get('name', 'N/A'))}</code></li>"
            tool_calls_html += "</ul>"
        else:
            tool_calls_html = "<span class='text-gray-400 italic'>None</span>"

        # Full conversation JSON for modal
        conversation_json = json.dumps(result.get("conversation", []), indent=2)
        conversation_json_escaped = html_module.escape(conversation_json)

        rows_html += f"""
        <tr class="hover:bg-gray-50 border-b border-gray-200">
            <td class="px-4 py-3 text-sm">{eval_button}</td>
            <td class="px-4 py-3 text-sm">
                <div>{question}</div>
                <div class="mt-1 text-xs text-gray-500">Tokens: <span class="font-medium">{tokens_used:,}</span></div>
            </td>
            <td class="px-4 py-3 text-sm">{expected}</td>
            <td class="px-4 py-3 text-sm">
                <div class="mb-2">{response}</div>
                <button onclick="openModal({idx})" class="mt-2 text-blue-600 hover:text-blue-800 text-xs font-medium underline cursor-pointer">
                    View Full Conversation JSON
                </button>
            </td>
            <td class="px-4 py-3 text-sm">{tool_calls_html}</td>
        </tr>

        <!-- Modal for conversation JSON -->
        <div id="modal-{idx}" class="hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50" onclick="closeModal({idx})">
            <div class="relative top-20 mx-auto p-5 border w-11/12 max-w-4xl shadow-lg rounded-md bg-white" onclick="event.stopPropagation()">
                <div class="flex justify-between items-center mb-4">
                    <h3 class="text-lg font-semibold text-gray-900">Full Conversation JSON</h3>
                    <button onclick="closeModal({idx})" class="text-gray-400 hover:text-gray-600 text-2xl font-bold">&times;</button>
                </div>
                <div class="max-h-96 overflow-y-auto">
                    <pre class="p-4 bg-gray-900 text-green-400 rounded text-xs overflow-x-auto">{conversation_json_escaped}</pre>
                </div>
                <div class="mt-4 flex justify-end">
                    <button onclick="closeModal({idx})" class="px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700">
                        Close
                    </button>
                </div>
            </div>
        </div>
        """

    # Complete HTML document
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Evaluation Results</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body {{
            background: linear-gradient(to bottom right, #f3f4f6, #e5e7eb);
        }}
    </style>
    <script>
        function openModal(id) {{
            document.getElementById('modal-' + id).classList.remove('hidden');
        }}
        function closeModal(id) {{
            document.getElementById('modal-' + id).classList.add('hidden');
        }}
        // Close modal on Escape key
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                const modals = document.querySelectorAll('[id^="modal-"]');
                modals.forEach(modal => modal.classList.add('hidden'));
            }}
        }});
    </script>
</head>
<body class="min-h-screen py-8 px-4">
    <div class="max-w-[95%] mx-auto">
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
            <div class="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-8">
                <h1 class="text-3xl font-bold text-white">Evaluation Results</h1>
                <p class="text-blue-100 mt-2">MCP Test Case Evaluation Summary</p>

                <!-- Success Rate Summary -->
                <div class="mt-6 bg-white bg-opacity-20 rounded-lg p-4 backdrop-blur-sm">
                    <div class="flex items-center justify-between">
                        <div>
                            <p class="text-blue-100 text-sm font-medium">Success Rate</p>
                            <p class="text-white text-3xl font-bold mt-1">{success_rate:.1f}%</p>
                        </div>
                        <div class="text-right">
                            <p class="text-blue-100 text-sm">Passed: <span class="font-semibold text-white">{successful_tests}</span></p>
                            <p class="text-blue-100 text-sm">Total: <span class="font-semibold text-white">{total_tests}</span></p>
                        </div>
                    </div>
                    <div class="mt-3 w-full bg-blue-900 bg-opacity-30 rounded-full h-2.5">
                        <div class="bg-green-400 h-2.5 rounded-full" style="width: {success_rate}%"></div>
                    </div>
                </div>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead class="bg-gray-50 border-b-2 border-gray-300">
                        <tr>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/8">Evaluation</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Question</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Expected</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/3">Response</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Tool Calls</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white">
                        {rows_html}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>"""

    temp_html.write(html_content)
    temp_html.close()
    print(f"\n--- HTML report saved to: {html_path} ---")
    return html_path


def open_in_browser(html_path: str):
    """Open the HTML file in the default browser."""
    webbrowser.open(f"file://{os.path.abspath(html_path)}")
    print(f"--- Opened {html_path} in browser ---")


async def main():
    """
    Main function to run the evaluation concurrently.
    """
    # Load test cases
    with open("../mcp-llm-test/test_cases.yaml", "r") as f:
        test_cases = yaml.safe_load(f)

    # Create MCP server and client
    mcp_server = create_server()
    mcp_client = Client(mcp_server)

    # Create a semaphore to limit concurrency to 4
    semaphore = asyncio.Semaphore(4)

    async with mcp_client:
        tasks = [run_test_case(semaphore, mcp_client, test_case) for test_case in test_cases]
        results = await asyncio.gather(*tasks)

    # Sort results to match the original order of test cases
    results_map = {res["question"]: res for res in results}
    ordered_results = [
        results_map[tc["case"]["input"]] for tc in test_cases if tc["case"]["input"] in results_map
    ]

    # Generate HTML report and open in browser
    try:
        html_path = generate_html_report(ordered_results)
        open_in_browser(html_path)
    except Exception as e:
        print(f"--- Error generating HTML or opening browser: {e} ---")


if __name__ == "__main__":
    asyncio.run(main())
