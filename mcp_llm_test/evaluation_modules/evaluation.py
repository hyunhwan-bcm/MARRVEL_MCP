"""
Core evaluation logic for test responses.

This module handles evaluation of LLM responses against expected outputs
and coordinates the LangChain response generation.
"""

import logging
from typing import Any, Dict, List, Tuple

from langchain_core.messages import HumanMessage, SystemMessage
from fastmcp.client import Client

from marrvel_mcp import (
    convert_tool_to_langchain_format,
    execute_agentic_loop,
    count_tokens,
    validate_token_count,
)

from .llm_retry import invoke_with_throttle_retry


# Maximum tokens allowed for evaluation to prevent API errors
MAX_TOKENS = 100_000


async def evaluate_response(actual: str, expected: str, llm_evaluator) -> str:
    """
    Evaluate the response using LangChain and return the classification text.
    Be flexible - if the actual response contains the expected information plus additional details, consider it acceptable.

    Args:
        actual: The actual response text
        expected: The expected response text
        llm_evaluator: LLM instance to use for evaluation

    Returns:
        Classification string (e.g., "yes - matches expected" or "no - incorrect")
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

    # Log evaluator input in debug mode
    logging.debug("=" * 80)
    logging.debug("🔍 EVALUATOR INPUT:")
    logging.debug(
        f"   Expected answer: {expected[:200]}..."
        if len(expected) > 200
        else f"   Expected answer: {expected}"
    )
    logging.debug(
        f"   Actual response: {actual[:200]}..."
        if len(actual) > 200
        else f"   Actual response: {actual}"
    )
    logging.debug(f"   Full prompt length: {len(prompt)} chars")

    # Validate token count before making API call
    is_valid, token_count = validate_token_count(prompt)
    if not is_valid:
        error_msg = f"no - Evaluation skipped: Input token count ({token_count:,}) exceeds maximum allowed ({MAX_TOKENS:,}). The response or context is excessively long. Please reduce the input size."
        logging.debug(f"   ❌ Token limit exceeded: {error_msg}")
        logging.debug("=" * 80)
        return error_msg

    messages = [HumanMessage(content=prompt)]

    logging.debug(f"   Calling evaluator LLM ({type(llm_evaluator).__name__})...")
    response = await invoke_with_throttle_retry(llm_evaluator, messages)

    classification = response.content
    logging.debug(f"   ✅ Evaluator classification: {classification}")
    logging.debug("=" * 80)

    return classification


async def get_langchain_response(
    mcp_client: Client,
    user_input: str,
    vanilla_mode: bool = False,
    web_mode: bool = False,
    llm_instance=None,
    llm_web_instance=None,
) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, int], Dict[str, Any]]:
    """
    Get response using LangChain with OpenRouter, handling tool calls via the MCP client.

    Args:
        mcp_client: MCP client for tool calls
        user_input: User question/prompt
        vanilla_mode: If True, LLM responds without tool calling capabilities
        web_mode: If True, LLM responds with web search enabled (no tool calling)
        llm_instance: LLM instance to use (required)
        llm_web_instance: Web-enabled LLM instance to use (required for web_mode)

    Returns: (final_response, tool_history, full_conversation, usage_dict, metadata)
        where usage_dict has {input_tokens, output_tokens, total_tokens}
    """
    # Initialize LangChain messages
    if vanilla_mode:
        system_message = """You are an expert genetics research assistant. Answer questions about genes, variants, and genetic data with confidence and precision.

When answering:
- Provide clear, definitive answers based on your knowledge
- Use standard genetic nomenclature and bioinformatics principles
- If asked about specific variants, analyze the mutation type and predict the likely protein change
- Structure your response to end with a clear, concise answer to the question
- Avoid apologetic language - focus on providing the most accurate information possible"""
    elif web_mode:
        system_message = """You are an expert genetics research assistant with web search capabilities. Search for accurate, up-to-date information from scientific databases and reliable sources.

When answering:
- Search for the specific information requested (genes, transcripts, variants, proteins)
- If exact matches aren't found, search for related variants, similar mutations, or the gene/transcript in question
- Analyze the genetic nomenclature (e.g., c.187C>T means codon 63, C to T substitution) and infer the protein change
- Use information from similar cases or the gene's annotation to provide informed responses
- ALWAYS provide a clear, definitive answer at the end of your response
- Do NOT say "I cannot answer" - instead, work with available information to provide the best possible answer
- Cite specific sources when available
- Structure your response to conclude with a direct answer to the question asked"""
    else:
        system_message = "You are a helpful genetics research assistant. You have access to tools that can query genetic databases and provide accurate information. Always use the available tools to answer questions about genes, variants, and genetic data. Do not use pubmed tools unless pubmed is mentioned in the question. Do not make up or guess information - use the tools to get accurate data."

    messages = [
        SystemMessage(content=system_message),
        HumanMessage(content=user_input),
    ]
    tool_history = []
    conversation = []

    # In vanilla or web mode, skip tool binding and just get a direct response
    if vanilla_mode or web_mode:
        # Store initial messages in conversation history
        conversation.append({"role": "system", "content": system_message})
        conversation.append({"role": "user", "content": user_input})

        # Use web-enabled LLM for web mode, regular LLM for vanilla mode
        active_llm = llm_web_instance if web_mode else llm_instance

        # Get direct response without tool calling
        try:
            response = await invoke_with_throttle_retry(active_llm, messages)

            # Collect metadata (especially useful for web_mode debugging)
            response_metadata = {}
            if web_mode or vanilla_mode:
                if hasattr(response, "__dict__"):
                    response_metadata["response_type"] = str(type(response))
                    response_metadata["has_content_attr"] = hasattr(response, "content")
                    if hasattr(response, "content"):
                        response_metadata["content_length"] = (
                            len(response.content) if response.content else 0
                        )
                        response_metadata["content_preview"] = str(response.content)[:100]
                    if hasattr(response, "response_metadata"):
                        metadata = response.response_metadata
                        response_metadata["model_used"] = metadata.get("model_name", "N/A")
                        if "finish_reason" in metadata:
                            response_metadata["finish_reason"] = metadata["finish_reason"]
                    if hasattr(response, "usage_metadata"):
                        usage = response.usage_metadata
                        response_metadata["input_tokens"] = usage.get("input_tokens", 0)
                        response_metadata["output_tokens"] = usage.get("output_tokens", 0)

            final_content = response.content if hasattr(response, "content") else str(response)

            # Check if response is empty and warn
            if not final_content or final_content.strip() == "":
                mode_name = "web search" if web_mode else "vanilla"
                print(
                    f"⚠️  Warning: Empty response from {mode_name} mode. Model may not support this mode or encountered an error."
                )
                print(f"  Question was: {user_input}")
                final_content = f"**No response generated from {mode_name} mode. The model may not support this feature or encountered an API error.**"

            conversation.append({"role": "assistant", "content": final_content})

            # Use server-reported token counts; fallback to tiktoken if not available
            input_tokens = response_metadata.get("input_tokens", 0)
            output_tokens = response_metadata.get("output_tokens", 0)
            tokens_total = input_tokens + output_tokens
            if tokens_total == 0:
                # Fallback to tiktoken-based estimate if server didn't report usage
                try:
                    conv_text = "\n".join([str(item.get("content", "")) for item in conversation])
                    tokens_total = count_tokens(conv_text)
                    # Split evenly for fallback (rough approximation)
                    input_tokens = tokens_total // 2
                    output_tokens = tokens_total - input_tokens
                    logging.debug(
                        "[Token Tracking] No server-reported tokens in %s mode, using tiktoken fallback: %d",
                        "web" if web_mode else "vanilla",
                        tokens_total,
                    )
                except Exception:
                    tokens_total = 0
            else:
                logging.debug(
                    "[Token Tracking] %s mode: input=%d, output=%d, total=%d",
                    "web" if web_mode else "vanilla",
                    input_tokens,
                    output_tokens,
                    tokens_total,
                )

            usage = {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": tokens_total,
            }
            return final_content, tool_history, conversation, usage, response_metadata

        except Exception as e:
            mode_name = "web search" if web_mode else "vanilla"
            error_msg = f"**Error in {mode_name} mode: {str(e)}**"
            print(f"❌ Error in {mode_name} mode: {e}")
            conversation.append({"role": "assistant", "content": error_msg})
            usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
            return error_msg, tool_history, conversation, usage, {"error": str(e)}

    # Get MCP tools and convert to LangChain format
    mcp_tools_list = await mcp_client.list_tools()
    available_tools = [convert_tool_to_langchain_format(tool) for tool in mcp_tools_list]

    # Bind tools to LLM
    llm_with_tools = llm_instance.bind_tools(available_tools)

    # Store initial messages in conversation history
    conversation.append({"role": "system", "content": messages[0].content})
    conversation.append({"role": "user", "content": user_input})

    # Execute agentic loop with tool calling
    final_content, tool_history, conversation, usage, langchain_messages = (
        await execute_agentic_loop(
            mcp_client=mcp_client,
            llm_with_tools=llm_with_tools,
            messages=messages,
            conversation=conversation,
            tool_history=tool_history,
            max_tokens=MAX_TOKENS,
            max_iterations=10,
        )
    )

    # Serialize LangChain messages for HTML display
    from marrvel_mcp import serialize_messages_array

    serialized_messages = serialize_messages_array(langchain_messages)

    return (
        final_content,
        tool_history,
        conversation,
        usage,
        {"serialized_messages": serialized_messages},
    )
