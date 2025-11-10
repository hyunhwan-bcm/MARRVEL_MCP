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
"""

import argparse
import asyncio
import json
import os
import pickle
import re
import sys
import tempfile
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Tuple

# Add project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import yaml
from dotenv import load_dotenv
from fastmcp.client import Client
from jinja2 import Environment, FileSystemLoader
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
import tiktoken
from tqdm.asyncio import tqdm as atqdm

from server import create_server


class TokenLimitExceeded(Exception):
    def __init__(self, token_count: int):
        super().__init__(f"TOKEN_LIMIT_EXCEEDED: {token_count}")
        self.token_count = token_count


# Load environment variables from .env file
load_dotenv()

MODEL = "google/gemini-2.5-flash"  # Switched to a model with guaranteed tool support
MAX_TOKENS = 100_000  # Maximum tokens allowed for evaluation to prevent API errors

# Cache settings
CACHE_DIR = Path.home() / ".cache" / "marrvel-mcp" / "evaluations"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Global variables for LLM (initialized in main after arg parsing)
llm = None
OPENROUTER_API_KEY = None


def get_cache_path(test_case_name: str) -> Path:
    """Get the cache file path for a test case."""
    # Use sanitized test case name for filename
    safe_name = "".join(c if c.isalnum() or c in (" ", "-", "_") else "_" for c in test_case_name)
    safe_name = safe_name.strip().replace(" ", "_")
    return CACHE_DIR / f"{safe_name}.pkl"


def parse_subset(subset: str | None, total_count: int) -> List[int]:
    """
    Parse a subset specification string into a list of 0-based indices.

    Supported formats (1-based in the input):
    - "1-5"               -> [0,1,2,3,4]
    - "1,2,4"             -> [0,1,3]
    - "1-3,5,7-9"         -> [0,1,2,4,6,7,8]

    Rules:
    - Whitespace is ignored
    - Indices are 1-based in the input and converted to 0-based
    - Duplicates are removed; result is sorted
    - Errors:
      * index 0 -> ValueError("Index must be >= 1")
      * reversed range (e.g., 5-1) -> ValueError(f"Invalid range {start}-{end}")
      * index out of range -> ValueError(f"Index {n} out of range")
      * malformed tokens -> ValueError with message matching tests
    """
    if subset is None or subset.strip() == "":
        return list(range(total_count))

    # Remove spaces to simplify parsing
    cleaned = subset.replace(" ", "")
    indices: set[int] = set()

    # Split by comma for items that are either single indices or ranges
    tokens = [t for t in cleaned.split(",") if t != ""]
    for token in tokens:
        if "-" in token:
            # Range parsing
            parts = token.split("-")
            if len(parts) != 2 or parts[0] == "" or parts[1] == "":
                # Covers cases like "1-2-3", "-1", "1-", "-"
                raise ValueError("Invalid range format")
            start_str, end_str = parts
            if not start_str.isdigit() or not end_str.isdigit():
                raise ValueError("Invalid range format")
            start = int(start_str)
            end = int(end_str)
            if start == 0 or end == 0:
                raise ValueError("Index must be >= 1")
            if start > end:
                raise ValueError(f"Invalid range {start}-{end}")
            # Validate bounds, prefer reporting the start if both are out-of-range
            if start > total_count:
                raise ValueError(f"Index {start} out of range")
            if end > total_count:
                raise ValueError(f"Index {end} out of range")
            # Convert to 0-based inclusive range
            indices.update(i - 1 for i in range(start, end + 1))
        else:
            # Single index parsing
            if not token.isdigit():
                raise ValueError("Invalid index")
            value = int(token)
            if value == 0:
                raise ValueError("Index must be >= 1")
            if value > total_count:
                raise ValueError(f"Index {value} out of range")
            indices.add(value - 1)

    return sorted(indices)


def load_cached_result(test_case_name: str) -> Dict[str, Any] | None:
    """Load cached result for a test case if it exists."""
    cache_path = get_cache_path(test_case_name)
    if cache_path.exists():
        try:
            with open(cache_path, "rb") as f:
                return pickle.load(f)
        except Exception as e:
            print(f"Warning: Failed to load cache for {test_case_name}: {e}")
            return None
    return None


def save_cached_result(test_case_name: str, result: Dict[str, Any]):
    """Save result to cache."""
    cache_path = get_cache_path(test_case_name)
    try:
        with open(cache_path, "wb") as f:
            pickle.dump(result, f)
    except Exception as e:
        print(f"Warning: Failed to save cache for {test_case_name}: {e}")


def clear_cache():
    """Clear all cached results."""
    if CACHE_DIR.exists():
        for cache_file in CACHE_DIR.glob("*.pkl"):
            try:
                cache_file.unlink()
            except Exception as e:
                print(f"Warning: Failed to delete {cache_file}: {e}")
        print(f"✅ Cache cleared: {CACHE_DIR}")


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


def parse_tool_result_content(content: Any) -> Any:
    """
    Parse tool result content to extract actual data.

    Tool results often come in the format:
    "toolNameOutput(result='<JSON_STRING>')"

    This function attempts to extract and parse the nested JSON for better display.
    Converts JSON strings to objects so that escape sequences like \n and \\
    are properly handled when rendered.

    Handles multiple layers of escaping from cached data.
    """
    # If content is not a string, return as-is (already parsed)
    if not isinstance(content, str):
        return content

    original_content = content

    # Strip outer whitespace
    content = content.strip()

    # If wrapped in quotes, try to unwrap one layer by parsing as JSON string
    if content.startswith('"') and content.endswith('"'):
        try:
            content = json.loads(content)
            if not isinstance(content, str):
                # Successfully parsed to object, return it
                return content
        except json.JSONDecodeError:
            pass

    # Try to match the pattern: SomeOutput(result='<JSON>')
    match = re.search(r"Output\(result='(.+)'\)\s*$", content, re.DOTALL)
    if match:
        json_str = match.group(1)
        try:
            # Try to parse as JSON directly - json.loads handles escape sequences
            return json.loads(json_str)
        except json.JSONDecodeError:
            # If direct parsing fails, try manual unescaping for non-standard formats
            # Handle: \\n -> \n, \\" -> ", \\' -> ', but preserve \\\\ -> \\
            # Do \\\\ first to avoid conflicts
            unescaped = json_str.replace("\\\\", "\x00")  # Temp placeholder for \\
            unescaped = unescaped.replace("\\n", "\n")
            unescaped = unescaped.replace('\\"', '"')
            unescaped = unescaped.replace("\\'", "'")
            unescaped = unescaped.replace("\\t", "\t")
            unescaped = unescaped.replace("\\r", "\r")
            unescaped = unescaped.replace("\x00", "\\")  # Restore single backslash
            try:
                # Try parsing the manually unescaped version
                return json.loads(unescaped)
            except json.JSONDecodeError:
                # Return the unescaped string if parsing still fails
                return unescaped

    # If content looks like JSON (starts with { or [), try to parse it
    if content.startswith('{') or content.startswith('['):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # If parsing fails, return as-is
            pass

    # Return as-is if we can't parse it
    return original_content


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

                    # Validate token count for tool result (regardless of original type)
                    is_valid, token_count = validate_token_count(content)
                    if not is_valid:
                        # Stop evaluation immediately and signal token exceed
                        raise TokenLimitExceeded(token_count)

                    # Create LangChain ToolMessage
                    tool_message = ToolMessage(
                        content=content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    messages.append(tool_message)

                    # Store in conversation history with parsed content for better JSON display
                    parsed_content = parse_tool_result_content(content)
                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": parsed_content,
                        }
                    )
                except TokenLimitExceeded:
                    # Re-raise TokenLimitExceeded to stop evaluation immediately
                    raise
                except Exception as e:
                    # Handle tool execution error (but not TokenLimitExceeded)
                    error_content = json.dumps({"error": str(e)})
                    tool_message = ToolMessage(
                        content=error_content,
                        tool_call_id=tool_call_id,
                        name=function_name,
                    )
                    messages.append(tool_message)

                    # Store parsed error content in conversation
                    conversation.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "name": function_name,
                            "content": {"error": str(e)},
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
    use_cache: bool = True,
    pbar=None,
) -> Dict[str, Any]:
    """
    Runs a single test case and returns the results for the table.

    Args:
        semaphore: Asyncio semaphore for limiting concurrency
        mcp_client: MCP client for tool calls
        test_case: Test case dictionary
        use_cache: Whether to use cached results (default: True)
        pbar: Optional tqdm progress bar to update
    """
    async with semaphore:
        name = test_case["case"]["name"]
        user_input = test_case["case"]["input"]
        expected = test_case["case"]["expected"]

        # Check cache first if enabled
        if use_cache:
            cached = load_cached_result(name)
            if cached is not None:
                if pbar:
                    pbar.set_postfix_str(f"Cached: {name[:40]}...")
                    pbar.update(1)
                return cached

        if pbar:
            pbar.set_postfix_str(f"Running: {name[:40]}...")

        try:
            langchain_response, tool_history, full_conversation, tokens_used = (
                await get_langchain_response(mcp_client, user_input)
            )
            classification = await evaluate_response(langchain_response, expected)
            result = {
                "question": user_input,
                "expected": expected,
                "response": langchain_response,
                "classification": classification,
                "tool_calls": tool_history,
                "conversation": full_conversation,
                "tokens_used": tokens_used,
            }
            # Save to cache
            save_cached_result(name, result)
            if pbar:
                pbar.update(1)
            return result
        except TokenLimitExceeded as e:
            # Stop evaluation completely and mark as NO due to token exceed
            if pbar:
                pbar.write(
                    f"⚠️  Token limit exceeded for {name}: {e.token_count:,} > {MAX_TOKENS:,}"
                )
            result = {
                "question": user_input,
                "expected": expected,
                "response": "",  # No response since we skipped evaluation
                "classification": f"no - token count exceeded: {e.token_count:,} > {MAX_TOKENS:,}. Please reduce the input/context.",
                "tool_calls": [],
                "conversation": [],
                "tokens_used": e.token_count,
            }
            if pbar:
                pbar.update(1)
            # Don't cache failures
            return result
        except Exception as e:
            if pbar:
                pbar.write(f"❌ Error in {name}: {e}")
            result = {
                "question": user_input,
                "expected": expected,
                "response": "**No response generated due to error.**",
                "classification": f"**Error:** {e}",
                "tool_calls": [],
                "conversation": [],
            }
            if pbar:
                pbar.update(1)
            # Don't cache errors
            return result


def generate_html_report(results: List[Dict[str, Any]]) -> str:
    """Generate HTML report with modal popups, reordered columns, and success rate summary."""
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
        }
        enriched_results.append(enriched_result)

    # Load and render Jinja2 template
    template_path = Path(__file__).parent.parent / "assets"
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
        json_str = json_str.replace('\\\\n', '\n')
        # Then replace remaining \n with newlines
        json_str = json_str.replace('\\n', '\n')
        json_str = json_str.replace('\\t', '\t')
        json_str = json_str.replace('\\r', '\r')
        return json_str

    env.filters["tojson_pretty"] = tojson_pretty
    template = env.get_template("evaluation_report_template.html")

    html_content = template.render(
        success_rate=success_rate,
        successful_tests=successful_tests,
        total_tests=total_tests,
        results=enriched_results,
    )

    temp_html.write(html_content)
    temp_html.close()
    print(f"\n--- HTML report saved to: {html_path} ---")
    return html_path


def open_in_browser(html_path: str):
    """Open the HTML file in the default browser."""
    webbrowser.open(f"file://{os.path.abspath(html_path)}")
    print(f"--- Opened {html_path} in browser ---")


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="MCP LLM Evaluation Script - Evaluate MCP tools with LangChain",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all test cases (uses cache by default)
  python evaluate_mcp.py

  # Clear cache only (does not run tests)
  python evaluate_mcp.py --clear

  # Force re-evaluation (ignore cache)
  python evaluate_mcp.py --force

  # Run specific test cases by index (1-based)
  python evaluate_mcp.py --subset "1-5"        # Run tests 1 through 5
  python evaluate_mcp.py --subset "1,3,5"      # Run tests 1, 3, and 5
  python evaluate_mcp.py --subset "1-3,5,7-9"  # Run tests 1-3, 5, and 7-9

  # Ask a custom question and get JSON response (no HTML)
  python evaluate_mcp.py --prompt "tell me about MECP2"
  python evaluate_mcp.py --prompt "What is the CADD score for chr1:12345 A>G?"

Cache Location:
  Results are cached at: {cache_dir}

  The cache stores evaluation results to avoid redundant API calls and speed up
  re-runs. Each test case result is cached separately.
        """.format(
            cache_dir=CACHE_DIR
        ),
    )

    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear the cache and exit without running evaluations. Use this to remove all cached test results.",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force re-evaluation of all test cases, ignoring cached results. Cache will be updated with new results.",
    )

    parser.add_argument(
        "--subset",
        type=str,
        metavar="INDICES",
        help="Run specific test cases by index. Supports ranges (1-5), individual indices (1,3,5), or combinations (1-3,5,7-9). Indices are 1-based.",
    )

    parser.add_argument(
        "--prompt",
        type=str,
        metavar="QUESTION",
        help="Ask a custom question directly and get JSON response without HTML report. Example: --prompt 'tell me about MECP2'",
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=4,
        metavar="N",
        help="Maximum number of concurrent test executions (default: 4). Increase for faster execution if API rate limits allow.",
    )

    return parser.parse_args()


async def main():
    """
    Main function to run the evaluation concurrently.
    """
    global llm, OPENROUTER_API_KEY

    # Parse command-line arguments
    args = parse_arguments()

    # Configure API keys (after argument parsing so --help works)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    if not OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found in environment variables. "
            "Please set it in a .env file or export it as an environment variable."
        )

    # Configure LangChain ChatOpenAI with OpenRouter
    llm = ChatOpenAI(
        model=MODEL,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=OPENROUTER_API_KEY,
        temperature=0,
    )

    # Clear cache if requested
    if args.clear:
        clear_cache()
        return  # Exit without running any tests

    # Handle --prompt mode (ad-hoc question)
    if args.prompt:
        print(f"🔍 Processing prompt: {args.prompt}")
        print("=" * 80)

        # Create MCP server and client
        mcp_server = create_server()
        mcp_client = Client(mcp_server)

        async with mcp_client:
            try:
                response, tool_history, conversation, tokens_used = await get_langchain_response(
                    mcp_client, args.prompt
                )

                # Output as JSON
                result = {
                    "question": args.prompt,
                    "response": response,
                    "tool_calls": tool_history,
                    "conversation": conversation,
                    "tokens_used": tokens_used,
                }

                print("\n📊 RESULT (JSON):")
                print(json.dumps(result, indent=2))
                print("\n" + "=" * 80)

            except TokenLimitExceeded as e:
                print(f"❌ Token limit exceeded: {e.token_count:,} > {MAX_TOKENS:,}")
                print("   Please reduce the complexity of your question or context.")
            except Exception as e:
                print(f"❌ Error processing prompt: {e}")
                import traceback

                traceback.print_exc()

        return  # Exit after handling prompt

    # Load test cases
    test_cases_path = Path(__file__).parent / "test_cases.yaml"
    with open(test_cases_path, "r", encoding="utf-8") as f:
        all_test_cases = yaml.safe_load(f)

    # Filter test cases if subset is specified
    if args.subset:
        try:
            subset_indices = parse_subset(args.subset, len(all_test_cases))
            test_cases = [all_test_cases[i] for i in subset_indices]
            print(f"📋 Running subset: {len(test_cases)}/{len(all_test_cases)} test cases")
            print(f"   Indices (1-based): {', '.join(str(i+1) for i in subset_indices)}")
        except ValueError as e:
            print(f"❌ Error parsing subset: {e}")
            return
    else:
        test_cases = all_test_cases

    # Create MCP server and client
    mcp_server = create_server()
    mcp_client = Client(mcp_server)

    # Create a semaphore to limit concurrency
    semaphore = asyncio.Semaphore(args.concurrency)

    # Determine whether to use cache
    use_cache = not args.force

    print(f"🚀 Running {len(test_cases)} test case(s) with concurrency={args.concurrency}")
    print(f"💾 Cache {'disabled (--force)' if not use_cache else 'enabled'}")

    async with mcp_client:
        # Create progress bar
        pbar = atqdm(total=len(test_cases), desc="Evaluating tests", unit="test")

        tasks = [
            run_test_case(semaphore, mcp_client, test_case, use_cache=use_cache, pbar=pbar)
            for test_case in test_cases
        ]
        results = await asyncio.gather(*tasks)

        pbar.close()

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
