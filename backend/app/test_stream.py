#!/usr/bin/env python
"""
Test script to check how the AutoGen agent's streaming works.
"""
import asyncio
import os
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

# Load environment variables
load_dotenv()

async def main():
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return
    
    # Create the model client
    model_client = OpenAIChatCompletionClient(
        model="anthropic/claude-3.7-sonnet",
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        model_info={
            "name": "anthropic/claude-3.7-sonnet",
            "context_length": 100000,
            "max_tokens": 4096,
            "is_chat_model": True,
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "family": "anthropic"
        }
    )
    
    # Create the AutoGen agent
    agent = AssistantAgent(
        name="assistant",
        model_client=model_client,
        system_message="You are a helpful assistant.",
        model_client_stream=True
    )
    
    # Test the streaming
    print("Testing on_messages_stream:")
    async for message in agent.on_messages_stream(
        [TextMessage(content="Hello, how are you?", source="user")],
        CancellationToken()
    ):
        print(f"Type: {type(message)}, Content: {message}")
    
    print("\nTesting run_stream:")
    async for message in agent.run_stream(task="Hello, how are you?"):
        print(f"Type: {type(message)}, Content: {message}")

if __name__ == "__main__":
    asyncio.run(main())
