#!/usr/bin/env python3
"""
Quick test script to check if a model supports web search via OpenRouter.

Usage:
    python check_web_search.py
"""

import asyncio
import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm_config import get_openrouter_model

load_dotenv()


async def test_web_search():
    """Test if the configured model supports web search."""

    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment variables")
        return

    # Get model
    model = get_openrouter_model()
    print(f"Testing model: {model}")
    print(f"Testing web search with: {model}:online\n")

    # Create LLMs
    llm_vanilla = ChatOpenAI(
        model=model,
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=api_key,
        temperature=0,
    )

    llm_web = ChatOpenAI(
        model=f"{model}:online",
        openai_api_base="https://openrouter.ai/api/v1",
        openai_api_key=api_key,
        temperature=0,
    )

    # Test question that requires recent information
    test_question = "What is the current weather in San Francisco?"

    print("=" * 80)
    print("Testing VANILLA mode (no web search):")
    print("=" * 80)
    try:
        response = await llm_vanilla.ainvoke([HumanMessage(content=test_question)])
        vanilla_content = response.content if hasattr(response, "content") else str(response)
        print(f"Response: {vanilla_content[:200]}...")
        print(f"Response length: {len(vanilla_content)} characters")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n" + "=" * 80)
    print("Testing WEB SEARCH mode (:online suffix):")
    print("=" * 80)
    try:
        response = await llm_web.ainvoke([HumanMessage(content=test_question)])
        web_content = response.content if hasattr(response, "content") else str(response)
        print(f"Response: {web_content[:200]}...")
        print(f"Response length: {len(web_content)} characters")

        if not web_content or web_content.strip() == "":
            print("\n❌ EMPTY RESPONSE - This model likely does NOT support web search")
            print("\nRecommended models that support :online:")
            print("  - openai/gpt-4")
            print("  - openai/gpt-3.5-turbo")
            print("  - anthropic/claude-3.5-sonnet")
            print("  - google/gemini-2.5-flash")
            print("\nTo change model, set OPENROUTER_MODEL environment variable:")
            print("  export OPENROUTER_MODEL='openai/gpt-4'")
        else:
            print("\n✅ SUCCESS - This model appears to support web search!")

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nThis model may not support the :online suffix for web search")


if __name__ == "__main__":
    asyncio.run(test_web_search())
