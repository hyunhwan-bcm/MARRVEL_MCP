# MCP Agent Package

A reusable Python package for building LLM agents with tool calling capabilities using the Model Context Protocol (MCP) and LangChain.

## Overview

This package provides core components for implementing agentic workflows with LLMs that can call tools iteratively until a task is complete. It's designed to work with FastMCP servers and LangChain LLM instances.

## Components

### `tool_calling.py`

Handles tool-related operations:

- **`convert_tool_to_langchain_format(tool)`** - Converts FastMCP tools to LangChain/OpenAI format
- **`ensure_tool_call_id(tool_call)`** - Ensures tool calls have unique IDs
- **`parse_tool_result_content(content)`** - Parses and cleans tool result content (handles JSON escaping, etc.)
- **`format_tool_call_for_conversation(tool_call)`** - Formats tool calls for conversation history

### `agentic_loop.py`

Manages the iterative agent loop:

- **`execute_agentic_loop(...)`** - Main function that executes the agentic loop with tool calling
- **`count_tokens(text, model)`** - Counts tokens in text using tiktoken
- **`validate_token_count(text, max_tokens)`** - Validates text against token limits
- **`TokenLimitExceeded`** - Exception raised when token limits are exceeded

## Installation

Since this is part of the MARRVEL_MCP project, it's already available. Simply ensure the project root is in your Python path:

```python
import sys
sys.path.insert(0, '/path/to/MARRVEL_MCP')

from mcp_agent import execute_agentic_loop, convert_tool_to_langchain_format
```

## Usage Example

### Basic Agentic Loop

```python
from mcp_agent import (
    execute_agentic_loop,
    convert_tool_to_langchain_format,
    TokenLimitExceeded,
)
from fastmcp.client import Client
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

# Initialize LLM and MCP client
llm = ChatOpenAI(model="gpt-4", temperature=0)
mcp_client = Client(your_mcp_server)

async with mcp_client:
    # Get and convert MCP tools
    mcp_tools = await mcp_client.list_tools()
    langchain_tools = [convert_tool_to_langchain_format(t) for t in mcp_tools]

    # Bind tools to LLM
    llm_with_tools = llm.bind_tools(langchain_tools)

    # Prepare messages
    messages = [
        SystemMessage(content="You are a helpful assistant with access to tools."),
        HumanMessage(content="What is the weather in San Francisco?"),
    ]

    # Initialize tracking lists
    conversation = [
        {"role": "system", "content": messages[0].content},
        {"role": "user", "content": messages[1].content},
    ]
    tool_history = []

    # Execute agentic loop
    try:
        final_response, tool_history, conversation, tokens_used = await execute_agentic_loop(
            mcp_client=mcp_client,
            llm_with_tools=llm_with_tools,
            messages=messages,
            conversation=conversation,
            tool_history=tool_history,
            max_tokens=100_000,
            max_iterations=10,
        )

        print(f"Response: {final_response}")
        print(f"Tools called: {len(tool_history)}")
        print(f"Tokens used: {tokens_used}")

    except TokenLimitExceeded as e:
        print(f"Token limit exceeded: {e.token_count}")
```

### Using Individual Functions

```python
from mcp_agent import (
    parse_tool_result_content,
    count_tokens,
    validate_token_count,
)

# Parse tool results
raw_result = 'ToolOutput(result=\'{"data": "value"}\')'
parsed = parse_tool_result_content(raw_result)
print(parsed)  # {"data": "value"}

# Token counting
text = "This is some text to count tokens for."
token_count = count_tokens(text)
print(f"Token count: {token_count}")

# Validate token count
is_valid, count = validate_token_count(text, max_tokens=1000)
if is_valid:
    print(f"Text is within limit: {count} tokens")
```

## Integration Points

This package is designed to integrate with:

1. **FastMCP Servers** - For tool execution via `Client.call_tool()`
2. **LangChain LLMs** - For language model inference with tool binding
3. **OpenRouter/OpenAI** - Compatible with any OpenAI-compatible API

## Architecture

```
User Input
    ↓
[LLM with Tools] → Tool Call? → Yes → [Execute Tool via MCP]
    ↑                                        ↓
    └────────────────────────────────────────┘
                                             ↓
                                    Add Result to Messages
                                             ↓
                                    Repeat (max 10 iterations)
                                             ↓
                                    Final Response
```

## Error Handling

The package includes robust error handling:

- **`TokenLimitExceeded`** - Raised when tool results exceed token limits
- **Tool execution errors** - Caught and added to conversation as error messages
- **Empty responses** - Handled gracefully with appropriate messaging

## Token Management

Token limits are enforced to prevent API errors:

- Default maximum: 100,000 tokens
- Configurable per request
- Uses tiktoken for accurate counting
- Validates both input and tool result sizes

## Dependencies

- `fastmcp` - MCP client for tool execution
- `langchain-core` - Message types and abstractions
- `tiktoken` - Token counting
- `typing` - Type hints

## Future Enhancements

Potential improvements:

1. Add retry logic for failed tool calls
2. Support for parallel tool execution
3. Streaming response support
4. Tool call caching
5. Enhanced error recovery strategies
6. Metrics and observability hooks

## License

Part of the MARRVEL_MCP project.
