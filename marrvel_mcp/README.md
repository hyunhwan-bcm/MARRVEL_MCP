# marrvel_mcp Package

Python package for MARRVEL (Model organism Aggregated Resources for Rare Variant ExpLoration), providing an MCP server with 35+ genetics research tools and reusable agent components for building LLM agents with tool calling.

## Components

### `server.py`

MARRVEL MCP server with 35+ genetics research tools:

- **`create_server()`** - Creates and configures the MARRVEL MCP server instance
- Gene queries (Entrez ID, symbol, position)
- Variant annotations (dbNSFP, ClinVar, gnomAD, DGV, Geno2MP)
- Disease associations (OMIM, HPO, DECIPHER)
- Ortholog predictions (DIOPT across model organisms)
- Expression data (GTEx, drug targets)
- Literature search (PubMed, PMC)
- Coordinate conversion (hg19/hg38 liftover)

### `tool_calling.py`

- **`convert_tool_to_langchain_format(tool)`** - Converts FastMCP tools to LangChain/OpenAI format
- **`ensure_tool_call_id(tool_call)`** - Ensures tool calls have unique IDs
- **`parse_tool_result_content(content)`** - Parses and cleans tool result content
- **`format_tool_call_for_conversation(tool_call)`** - Formats tool calls for conversation history

### `agentic_loop.py`

- **`execute_agentic_loop(...)`** - Main function that executes the agentic loop with tool calling
- **`count_tokens(text, model)`** - Counts tokens using tiktoken
- **`validate_token_count(text, max_tokens)`** - Validates text against token limits
- **`TokenLimitExceeded`** - Exception raised when token limits are exceeded

## Usage

```python
from marrvel_mcp import (
    execute_agentic_loop,
    convert_tool_to_langchain_format,
    TokenLimitExceeded,
)
from marrvel_mcp.server import create_server
from fastmcp.client import Client
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

llm = ChatOpenAI(model="gpt-4", temperature=0)
mcp_client = Client(your_mcp_server)

async with mcp_client:
    mcp_tools = await mcp_client.list_tools()
    langchain_tools = [convert_tool_to_langchain_format(t) for t in mcp_tools]
    llm_with_tools = llm.bind_tools(langchain_tools)

    messages = [
        SystemMessage(content="You are a genetics research assistant."),
        HumanMessage(content="What is the function of the MECP2 gene?"),
    ]
    conversation = [
        {"role": "system", "content": messages[0].content},
        {"role": "user", "content": messages[1].content},
    ]
    tool_history = []

    final_response, tool_history, conversation, tokens_used = await execute_agentic_loop(
        mcp_client=mcp_client,
        llm_with_tools=llm_with_tools,
        messages=messages,
        conversation=conversation,
        tool_history=tool_history,
        max_tokens=100_000,
        max_iterations=10,
    )
```

## Dependencies

- `fastmcp` - MCP server framework
- `langchain-core` - Message types and abstractions (eval extra)
- `tiktoken` - Token counting (eval extra)
