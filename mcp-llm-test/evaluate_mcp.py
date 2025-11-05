import asyncio
import json
import os
import sys
import tempfile
import webbrowser
from typing import Any, Dict, List, Tuple

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import yaml
from dotenv import load_dotenv
from fastmcp.client import Client
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_core.tools import tool as langchain_tool
from langchain_core.utils.function_calling import convert_to_openai_tool

from server import create_server

# Load environment variables from .env file
load_dotenv()

# Configure API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

MODEL = "google/gemini-2.5-flash"  # Switched to a model with guaranteed tool support

# Configure LangChain ChatOpenAI with OpenRouter
llm = ChatOpenAI(
    model=MODEL,
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
    temperature=0,
)


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
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
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

    # Agentic loop for tool calling
    max_iterations = 10
    for iteration in range(max_iterations):
        # Invoke LLM with current messages
        response = await llm_with_tools.ainvoke(messages)
        messages.append(response)

        # Check if there are tool calls
        if response.tool_calls:
            # Store assistant message with tool calls
            assistant_msg = {
                "role": "assistant",
                "content": response.content or "",
                "tool_calls": [
                    {
                        "id": tc.get("id", f"call_{tc['name']}"),
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["args"]),
                        },
                    }
                    for tc in response.tool_calls
                ],
            }
            conversation.append(assistant_msg)

            # Execute each tool call
            for tool_call in response.tool_calls:
                function_name = tool_call["name"]
                function_args = tool_call["args"]
                tool_call_id = tool_call.get("id", f"call_{function_name}")

                tool_history.append({"name": function_name, "args": function_args})

                try:
                    # Call the MCP tool
                    tool_result = await mcp_client.call_tool(function_name, function_args)

                    # Serialize tool result to JSON string
                    if isinstance(tool_result.data, str):
                        content = tool_result.data
                    else:
                        content = json.dumps(tool_result.data, default=str)

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
            return final_content, tool_history, conversation

    # If we hit max iterations, return what we have
    final_content = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])
    return final_content, tool_history, conversation


async def evaluate_response(actual: str, expected: str) -> str:
    """
    Evaluate the response using LangChain and return the classification text.
    """
    prompt = f"Is the actual response consistent with the expected response? Answer 'yes' or 'no', and provide a brief reason.\n\nExpected: {expected}\nActual: {actual}"
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
            langchain_response, tool_history, full_conversation = await get_langchain_response(
                mcp_client, user_input
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
    """Generate HTML report directly with Tailwind CSS styling and collapsible conversation details."""
    import html as html_module

    # Create a temporary HTML file
    temp_html = tempfile.NamedTemporaryFile(
        mode="w", suffix=".html", delete=False, prefix="evaluation_results_"
    )
    html_path = temp_html.name

    # Build table rows
    rows_html = ""
    for result in results:
        question = html_module.escape(result["question"])
        expected = html_module.escape(result["expected"])
        response = html_module.escape(result.get("response", ""))
        classification = html_module.escape(result["classification"])

        # Tool calls summary
        tool_calls_list = result.get("tool_calls", [])
        if tool_calls_list:
            tool_calls_html = "<ul class='list-disc list-inside text-xs'>"
            for tc in tool_calls_list:
                tool_calls_html += f"<li><code class='bg-gray-100 px-1 rounded'>{html_module.escape(tc.get('name', 'N/A'))}</code></li>"
            tool_calls_html += "</ul>"
        else:
            tool_calls_html = "<span class='text-gray-400 italic'>None</span>"

        # Full conversation JSON (collapsible)
        conversation_json = json.dumps(result.get("conversation", []), indent=2)

        rows_html += f"""
        <tr class="hover:bg-gray-50 border-b border-gray-200">
            <td class="px-4 py-3 text-sm">{question}</td>
            <td class="px-4 py-3 text-sm">{expected}</td>
            <td class="px-4 py-3 text-sm">
                <div class="mb-2">{response}</div>
                <details class="mt-2">
                    <summary class="cursor-pointer text-blue-600 hover:text-blue-800 text-xs font-medium">
                        View Full Conversation JSON
                    </summary>
                    <pre class="mt-2 p-3 bg-gray-900 text-green-400 rounded text-xs overflow-x-auto max-h-96 overflow-y-auto">{html_module.escape(conversation_json)}</pre>
                </details>
            </td>
            <td class="px-4 py-3 text-sm">{tool_calls_html}</td>
            <td class="px-4 py-3 text-sm">{classification}</td>
        </tr>
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
        details summary::marker {{
            color: #2563eb;
        }}
        details[open] summary {{
            margin-bottom: 0.5rem;
        }}
    </style>
</head>
<body class="min-h-screen py-8 px-4">
    <div class="max-w-[95%] mx-auto">
        <div class="bg-white rounded-lg shadow-lg overflow-hidden">
            <div class="bg-gradient-to-r from-blue-600 to-indigo-700 px-6 py-8">
                <h1 class="text-3xl font-bold text-white">Evaluation Results</h1>
                <p class="text-blue-100 mt-2">MCP Test Case Evaluation Summary</p>
            </div>
            <div class="overflow-x-auto">
                <table class="min-w-full">
                    <thead class="bg-gray-50 border-b-2 border-gray-300">
                        <tr>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Question</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Expected</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/3">Response</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Tool Calls</th>
                            <th class="px-4 py-3 text-left text-xs font-bold text-gray-700 uppercase tracking-wider w-1/6">Classification</th>
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
