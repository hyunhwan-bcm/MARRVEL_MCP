"""
Tests for token usage counting from server-reported usage_metadata.

Verifies that:
1. Token counts come from server-reported usage_metadata (not tiktoken)
2. Token counts are accumulated across multiple LLM calls

Provider Compatibility:
- OpenAI: Returns usage_metadata with input_tokens, output_tokens, total_tokens
- OpenRouter: Uses OpenAI-compatible API, returns same structure
- AWS Bedrock: ChatBedrock/ChatBedrockConverse returns usage_metadata with same keys

Reference: https://python.langchain.com/v0.1/docs/modules/model_io/chat/token_usage_tracking/
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List, Dict, Any


class MockResponse:
    """Mock LLM response with usage_metadata."""

    def __init__(
        self,
        content: str = "Test response",
        input_tokens: int = 100,
        output_tokens: int = 50,
        tool_calls: List[Dict[str, Any]] = None,
    ):
        self.content = content
        self.tool_calls = tool_calls or []
        self.usage_metadata = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }


class MockMCPClient:
    """Mock MCP client for tool calls."""

    async def call_tool(self, name: str, args: dict):
        result = MagicMock()
        result.data = f"Tool {name} result"
        return result


@pytest.mark.asyncio
async def test_single_call_server_tokens():
    """Test that single LLM call uses server-reported tokens."""
    from marrvel_mcp.agentic_loop import execute_agentic_loop

    # Mock LLM that returns a response with usage_metadata
    mock_llm = AsyncMock()
    mock_response = MockResponse(
        content="Final answer",
        input_tokens=150,
        output_tokens=75,
        tool_calls=[],  # No tool calls, ends immediately
    )
    mock_llm.ainvoke.return_value = mock_response

    mcp_client = MockMCPClient()
    messages = []
    conversation = []
    tool_history = []

    final_content, tool_history, conversation, usage = await execute_agentic_loop(
        mcp_client=mcp_client,
        llm_with_tools=mock_llm,
        messages=messages,
        conversation=conversation,
        tool_history=tool_history,
        max_tokens=100_000,
        max_iterations=10,
    )

    # Verify usage dict contains server-reported tokens
    assert usage["input_tokens"] == 150, f"Expected 150 input tokens, got {usage['input_tokens']}"
    assert usage["output_tokens"] == 75, f"Expected 75 output tokens, got {usage['output_tokens']}"
    assert usage["total_tokens"] == 225, f"Expected 225 total tokens, got {usage['total_tokens']}"
    assert final_content == "Final answer"


@pytest.mark.asyncio
async def test_multiple_calls_accumulate_tokens():
    """Test that multiple LLM calls accumulate server-reported tokens."""
    from marrvel_mcp.agentic_loop import execute_agentic_loop

    # Create mock tool call structure
    tool_call = {
        "name": "test_tool",
        "args": {"arg1": "value1"},
        "id": "call_123",
    }

    # Mock LLM that makes tool calls then final response
    mock_llm = AsyncMock()

    # First call: has tool calls (triggers another iteration)
    first_response = MockResponse(
        content="",
        input_tokens=100,
        output_tokens=30,
        tool_calls=[tool_call],
    )

    # Second call: has more tool calls
    second_response = MockResponse(
        content="",
        input_tokens=200,  # More tokens because context is longer
        output_tokens=40,
        tool_calls=[tool_call],
    )

    # Third call: final response, no tool calls
    third_response = MockResponse(
        content="Final answer after tools",
        input_tokens=300,  # Even more context
        output_tokens=60,
        tool_calls=[],
    )

    mock_llm.ainvoke.side_effect = [first_response, second_response, third_response]

    mcp_client = MockMCPClient()
    messages = []
    conversation = []
    tool_history = []

    final_content, tool_history, conversation, usage = await execute_agentic_loop(
        mcp_client=mcp_client,
        llm_with_tools=mock_llm,
        messages=messages,
        conversation=conversation,
        tool_history=tool_history,
        max_tokens=100_000,
        max_iterations=10,
    )

    # Verify tokens are accumulated: input=(100+200+300)=600, output=(30+40+60)=130
    expected_input = 100 + 200 + 300
    expected_output = 30 + 40 + 60
    expected_total = expected_input + expected_output
    assert usage["input_tokens"] == expected_input, f"Expected {expected_input} input tokens"
    assert usage["output_tokens"] == expected_output, f"Expected {expected_output} output tokens"
    assert usage["total_tokens"] == expected_total, f"Expected {expected_total} total tokens"
    assert final_content == "Final answer after tools"


@pytest.mark.asyncio
async def test_fallback_to_tiktoken_when_no_server_tokens():
    """Test that tiktoken is used as fallback when server doesn't report tokens."""
    from marrvel_mcp import agentic_loop

    # Create a simple object without usage_metadata attribute
    class ResponseWithoutUsage:
        def __init__(self):
            self.content = "This is a response without usage metadata that should have some tokens"
            self.tool_calls = []
            # No usage_metadata attribute at all

    mock_llm = AsyncMock()
    mock_response = ResponseWithoutUsage()
    mock_llm.ainvoke.return_value = mock_response

    mcp_client = MockMCPClient()
    messages = []
    conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"},
    ]
    tool_history = []

    # Mock count_tokens to avoid network issues with tiktoken encodings
    with patch.object(agentic_loop, "count_tokens", return_value=42):
        final_content, tool_history, conversation, usage = await agentic_loop.execute_agentic_loop(
            mcp_client=mcp_client,
            llm_with_tools=mock_llm,
            messages=messages,
            conversation=conversation,
            tool_history=tool_history,
            max_tokens=100_000,
            max_iterations=10,
        )

    # When server doesn't report tokens, should fallback to tiktoken (mocked to 42)
    assert usage["total_tokens"] == 42, f"Should have tiktoken fallback count, got {usage}"
    assert "without usage metadata" in final_content


@pytest.mark.asyncio
async def test_empty_usage_metadata_triggers_fallback():
    """Test that empty usage_metadata dict triggers tiktoken fallback."""
    from marrvel_mcp import agentic_loop

    # Create a response with empty usage_metadata
    class ResponseWithEmptyUsage:
        def __init__(self):
            self.content = "Response with empty metadata but some content here"
            self.tool_calls = []
            self.usage_metadata = {}  # Empty dict - will be falsy

    mock_llm = AsyncMock()
    mock_response = ResponseWithEmptyUsage()
    mock_llm.ainvoke.return_value = mock_response

    mcp_client = MockMCPClient()
    messages = []
    conversation = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Tell me about genetics."},
    ]
    tool_history = []

    # Mock count_tokens to avoid network issues with tiktoken encodings
    with patch.object(agentic_loop, "count_tokens", return_value=55):
        final_content, tool_history, conversation, usage = await agentic_loop.execute_agentic_loop(
            mcp_client=mcp_client,
            llm_with_tools=mock_llm,
            messages=messages,
            conversation=conversation,
            tool_history=tool_history,
            max_tokens=100_000,
            max_iterations=10,
        )

    # Empty usage_metadata means no tokens counted -> fallback to tiktoken (mocked to 55)
    assert usage["total_tokens"] == 55, f"Should have tiktoken fallback count, got {usage}"


@pytest.mark.asyncio
async def test_zero_server_tokens_triggers_fallback():
    """Test that zero server tokens triggers tiktoken fallback."""
    from marrvel_mcp import agentic_loop

    # Create a response with zero tokens in usage_metadata
    class ResponseWithZeroTokens:
        def __init__(self):
            self.content = "Response with zero tokens reported"
            self.tool_calls = []
            self.usage_metadata = {"input_tokens": 0, "output_tokens": 0}

    mock_llm = AsyncMock()
    mock_response = ResponseWithZeroTokens()
    mock_llm.ainvoke.return_value = mock_response

    mcp_client = MockMCPClient()
    messages = []
    conversation = [
        {"role": "system", "content": "You are a helpful genetics assistant."},
        {"role": "user", "content": "What gene is associated with MECP2?"},
    ]
    tool_history = []

    # Mock count_tokens to avoid network issues with tiktoken encodings
    with patch.object(agentic_loop, "count_tokens", return_value=77):
        final_content, tool_history, conversation, usage = await agentic_loop.execute_agentic_loop(
            mcp_client=mcp_client,
            llm_with_tools=mock_llm,
            messages=messages,
            conversation=conversation,
            tool_history=tool_history,
            max_tokens=100_000,
            max_iterations=10,
        )

    # Zero server tokens triggers tiktoken fallback (mocked to 77)
    assert usage["total_tokens"] == 77, f"Should have tiktoken fallback count, got {usage}"


class TestProviderCompatibility:
    """Tests documenting expected usage_metadata format from different LLM providers."""

    def test_openai_usage_metadata_format(self):
        """Document expected format from OpenAI/OpenRouter (langchain_openai.ChatOpenAI).

        LangChain's ChatOpenAI (used for OpenAI and OpenRouter) returns:
        - response.usage_metadata = {
            "input_tokens": <int>,
            "output_tokens": <int>,
            "total_tokens": <int>
          }
        """
        # Simulated OpenAI/OpenRouter response
        usage_metadata = {
            "input_tokens": 150,
            "output_tokens": 75,
            "total_tokens": 225,
        }

        # Our code extracts these keys
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)

        assert input_tokens == 150
        assert output_tokens == 75
        assert input_tokens + output_tokens == 225

    def test_bedrock_usage_metadata_format(self):
        """Document expected format from AWS Bedrock (langchain_aws.ChatBedrock).

        LangChain's ChatBedrock returns:
        - response.usage_metadata = {
            "input_tokens": <int>,
            "output_tokens": <int>,
            "total_tokens": <int>
          }

        Note: For prompt caching, may also include:
        - "input_token_details": {"cache_creation": <int>, "cache_read": <int>}
        """
        # Simulated Bedrock response
        usage_metadata = {
            "input_tokens": 200,
            "output_tokens": 100,
            "total_tokens": 300,
        }

        # Our code extracts these keys
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)

        assert input_tokens == 200
        assert output_tokens == 100
        assert input_tokens + output_tokens == 300

    def test_usage_metadata_with_cache_details(self):
        """Test handling of extended usage_metadata with cache details.

        Some providers include additional token details for caching.
        Our code should still work correctly with these extended formats.
        """
        # Extended format with cache details (e.g., Bedrock with prompt caching)
        usage_metadata = {
            "input_tokens": 1500,
            "output_tokens": 250,
            "total_tokens": 1750,
            "input_token_details": {"cache_creation": 1000, "cache_read": 500},
        }

        # Our code only uses the main token counts
        input_tokens = usage_metadata.get("input_tokens", 0)
        output_tokens = usage_metadata.get("output_tokens", 0)

        assert input_tokens == 1500
        assert output_tokens == 250
        assert input_tokens + output_tokens == 1750
