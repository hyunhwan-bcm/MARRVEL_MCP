import asyncio
import json
import os
import sys
from typing import Any, Dict, List, Tuple

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import google.generativeai as genai
import yaml
from dotenv import load_dotenv
from fastmcp.client import Client
from openai import AsyncOpenAI

from src.server import create_server

# Load environment variables from .env file
load_dotenv()

# Configure API keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# Configure OpenRouter client
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def convert_tool_format(tool: Any) -> Dict[str, Any]:
    """Converts a FastMCP tool to the OpenAI tool format."""
    tool_dict = tool.model_dump(exclude_none=True)
    return {
        "type": "function",
        "function": {
            "name": tool_dict.get("name"),
            "description": tool_dict.get("description"),
            "parameters": tool_dict.get("parameters"),
        },
    }


async def get_openrouter_response(
    mcp_client: Client, user_input: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Get response from OpenRouter, handling tool calls via the MCP client.
    """
    messages = [{"role": "user", "content": user_input}]
    tool_history = []

    mcp_tools_list = await mcp_client.list_tools()
    available_tools = [convert_tool_format(tool) for tool in mcp_tools_list]

    while True:
        response = await openrouter_client.chat.completions.create(
            model="google/gemini-2.5-flash",  # Switched to a model with guaranteed tool support
            messages=messages,
            tools=available_tools,
            tool_choice="auto",
        )
        message = response.choices[0].message

        if message.tool_calls:
            messages.append(message)
            for tool_call in message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                tool_history.append({"name": function_name, "args": function_args})

                try:
                    tool_result = await mcp_client.call_tool(
                        name=function_name,
                        args=function_args,
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": tool_result.data,
                        }
                    )
                except Exception as e:
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": function_name,
                            "content": f'{{"error": "{str(e)}"}}',
                        }
                    )
        else:
            return message.content, tool_history


async def evaluate_with_gemini(actual: str, expected: str) -> str:
    """
    Evaluate the response with Gemini and return the classification text.
    """
    model = genai.GenerativeModel("gemini-2.5-flash")
    prompt = f"Please evaluate if the actual response is consistent with the expected response. Provide a score from 1 to 5, where 1 is not at all consistent and 5 is perfectly consistent. Explain your reasoning.\n\nExpected: {expected}\nActual: {actual}"
    response = await model.generate_content_async(prompt)
    return response.text.strip()


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
            openrouter_response, tool_history = await get_openrouter_response(
                mcp_client, user_input
            )
            classification = await evaluate_with_gemini(openrouter_response, expected)
            print(f"--- Finished: {name} ---")
            return {
                "question": user_input,
                "expected": expected,
                "response": openrouter_response,
                "classification": classification,
                "tool_calls": tool_history,
            }
        except Exception as e:
            print(f"--- Error in {name}: {e} ---")
            return {
                "question": user_input,
                "expected": expected,
                "response": "**No response generated due to error.**",
                "classification": f"**Error:** {e}",
                "tool_calls": [],
            }


def save_markdown_table(results: List[Dict[str, Any]]):
    """Saves the final results as a Markdown table to a file."""
    output_path = os.path.join(
        os.path.dirname(__file__), "..", "test-output", "evaluation_results.md"
    )
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    content = [
        "| Question | Expected | Response | Tool Calls | Classification |",
        "|----------|----------|----------|------------|----------------|",
    ]
    for result in results:
        # Sanitize content for Markdown table cells
        question = result["question"].replace("\n", "<br>").replace("|", "\\|")
        expected = result["expected"].replace("\n", "<br>").replace("|", "\\|")
        response = result.get("response", "").replace("\n", "<br>").replace("|", "\\|")

        tool_calls_list = result.get("tool_calls", [])
        if tool_calls_list:
            tool_calls_str = "<ul>"
            for tc in tool_calls_list:
                args_str = json.dumps(tc.get("args", {}))
                tool_calls_str += f"<li><code>{tc.get('name', 'N/A')}({args_str})</code></li>"
            tool_calls_str += "</ul>"
        else:
            tool_calls_str = "None"
        tool_calls_str = tool_calls_str.replace("|", "\\|")

        classification = result["classification"].replace("\n", "<br>").replace("|", "\\|")
        content.append(
            f"| {question} | {expected} | {response} | {tool_calls_str} | {classification} |"
        )

    with open(output_path, "w") as f:
        f.write("\n".join(content))
    print(f"\n--- Evaluation results saved to {output_path} ---")


async def main():
    """
    Main function to run the evaluation concurrently.
    """
    # Load test cases
    with open("./mcp-llm-test/test_cases.yaml", "r") as f:
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

    save_markdown_table(ordered_results)


if __name__ == "__main__":
    asyncio.run(main())
