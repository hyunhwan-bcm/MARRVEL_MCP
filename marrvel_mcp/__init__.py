"""
MARRVEL MCP Package

This package provides the MARRVEL MCP server and reusable agent components for
building LLM agents with tool calling capabilities using the Model Context
Protocol (MCP) and LangChain.

Modules:
    server: MARRVEL MCP server with 35+ genetics research tools
    tool_calling: Tool conversion, ID management, and result parsing
    agentic_loop: Iterative agent loop for multiple tool calls and responses

Key Components:

Server:
    - create_server: Create and configure the MARRVEL MCP server instance
    - 35+ genetics research tools (gene queries, variants, orthologs, etc.)

Tool Calling:
    - convert_tool_to_langchain_format: Convert FastMCP tools to LangChain format
    - ensure_tool_call_id: Ensure tool calls have unique IDs
    - parse_tool_result_content: Parse and clean tool result content
    - format_tool_call_for_conversation: Format tool calls for conversation history

Agentic Loop:
    - execute_agentic_loop: Main iterative loop for tool calling
    - count_tokens: Count tokens in text using tiktoken
    - validate_token_count: Validate text against token limits
    - TokenLimitExceeded: Exception for token limit violations

Example:
    >>> from marrvel_mcp import execute_agentic_loop, convert_tool_to_langchain_format
    >>> from marrvel_mcp.server import create_server
    >>> from marrvel_mcp import TokenLimitExceeded
    >>>
    >>> # Create MCP server
    >>> server = create_server()
    >>>
    >>> # Convert MCP tools to LangChain format
    >>> tools = [convert_tool_to_langchain_format(tool) for tool in mcp_tools]
    >>> llm_with_tools = llm.bind_tools(tools)
    >>>
    >>> # Execute agentic loop
    >>> try:
    >>>     response, tools_used, conversation, tokens = await execute_agentic_loop(
    >>>         mcp_client=client,
    >>>         llm_with_tools=llm_with_tools,
    >>>         messages=messages,
    >>>         conversation=[],
    >>>         tool_history=[],
    >>>     )
    >>> except TokenLimitExceeded as e:
    >>>     print(f"Token limit exceeded: {e.token_count}")
"""

# Import from tool_calling module
from .tool_calling import (
    convert_tool_to_langchain_format,
    ensure_tool_call_id,
    parse_tool_result_content,
    format_tool_call_for_conversation,
)

# Import from agentic_loop module
from .agentic_loop import (
    execute_agentic_loop,
    count_tokens,
    validate_token_count,
    TokenLimitExceeded,
)

# Define public API
__all__ = [
    # Tool calling functions
    "convert_tool_to_langchain_format",
    "ensure_tool_call_id",
    "parse_tool_result_content",
    "format_tool_call_for_conversation",
    # Agentic loop functions
    "execute_agentic_loop",
    "count_tokens",
    "validate_token_count",
    # Exceptions
    "TokenLimitExceeded",
]

# Package metadata
__version__ = "1.0.0"
__author__ = "MARRVEL Team"
__description__ = "MARRVEL MCP server and agent components for genetics research with LLM tool calling"
