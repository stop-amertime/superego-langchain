#!/usr/bin/env python
import asyncio
import argparse
import os
import sys
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from autogen_agentchat.ui import Console

from .agents import AgentFactory, get_default_constitution, get_all_constitutions, save_constitution
from .models import Message, MessageRole, SuperegoDecision
# Import the superego_agent module to register the InputSuperego agent
from . import superego_agent
# Import the flow module
from .flow import SuperegoFlow, FlowResult

# Load environment variables
load_dotenv()

async def test_autogen_agent(system_prompt: Optional[str] = None):
    """Test the AutoGen agent with a simple CLI interface"""
    print("AutoGen Agent CLI Test Harness")
    print("Type 'exit' to quit")
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return
    
    # Create the AutoGen agent
    agent_config = {
        "model": os.getenv("BASE_MODEL", "anthropic/claude-3.7-sonnet"),
        "system_prompt": system_prompt or "You are a helpful AI assistant.",
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1"
    }
    
    try:
        agent = AgentFactory.create("autogen", agent_config)
        print(f"Created AutoGen agent with model: {agent_config['model']}")
        print(f"System prompt: {agent_config['system_prompt']}")
    except Exception as e:
        print(f"Error creating agent: {e}")
        return
    
    # Conversation history
    messages = []
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        
        # Add user message to history
        user_message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=user_input,
            timestamp=datetime.now().isoformat()
        )
        messages.append(user_message)
        
        # Process with agent
        print("\nProcessing...")
        
        try:
            # Use the Console UI to display the streaming response
            print()  # Add a blank line before the response
            full_response = ""
            
            # Use our stream method which handles the AutoGen streaming format
            async for token in agent.stream(user_input, {"messages": messages}):
                print(token, end="", flush=True)
                full_response += token
            
            print()  # Add a newline at the end
            
            # Add assistant message to history
            assistant_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.ASSISTANT,
                content=full_response,
                timestamp=datetime.now().isoformat()
            )
            messages.append(assistant_message)
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

async def test_input_superego(constitution: Optional[str] = None):
    """Test the InputSuperego agent with a simple CLI interface"""
    print("InputSuperego Agent CLI Test Harness")
    print("Type 'exit' to quit")
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return
    
    # Get the constitution content
    from .agents import get_default_constitution
    constitution_content = constitution or get_default_constitution()
    
    # Create the InputSuperego agent
    agent_config = {
        "model": os.getenv("SUPEREGO_MODEL", "anthropic/claude-3.7-sonnet:thinking"),
        "constitution": constitution_content,
        "api_key": api_key,
        "base_url": "https://openrouter.ai/api/v1"
    }
    
    try:
        agent = AgentFactory.create("input_superego", agent_config)
        print(f"Created InputSuperego agent with model: {agent_config['model']}")
        print("Constitution loaded successfully")
    except Exception as e:
        print(f"Error creating agent: {e}")
        return
    
    while True:
        # Get user input
        user_input = input("\nEvaluate> ")
        if user_input.lower() == "exit":
            break
        
        # Process with agent
        print("\nEvaluating...")
        
        try:
            # Use the stream method to get the evaluation
            print()  # Add a blank line before the response
            full_response = ""
            
            # Use our stream method which handles the AutoGen streaming format
            async for token in agent.stream(user_input, {}):
                print(token, end="", flush=True)
                full_response += token
            
            print()  # Add a newline at the end
            
            # Check if the decision is BLOCK
            if "DECISION: BLOCK" in full_response.upper():
                print("\n⛔ This input would be BLOCKED")
            # Check if the decision is CAUTION
            elif "DECISION: CAUTION" in full_response.upper():
                print("\n⚠️ This input would be processed with CAUTION")
            # Otherwise, it's ALLOW
            else:
                print("\n✅ This input would be ALLOWED")
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

async def test_superego_flow(system_prompt: Optional[str] = None, constitution: Optional[str] = None):
    """Test the SuperegoFlow with a simple CLI interface"""
    print("SuperegoFlow CLI Test Harness")
    print("Type 'exit' to quit")
    
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY environment variable not set")
        return
    
    # Get the constitution content
    constitution_content = constitution or get_default_constitution()
    
    # Create the flow
    flow_config = {
        "input_superego_config": {
            "model": os.getenv("SUPEREGO_MODEL", "anthropic/claude-3.7-sonnet:thinking"),
            "constitution": constitution_content,
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1"
        },
        "autogen_config": {
            "model": os.getenv("BASE_MODEL", "anthropic/claude-3.7-sonnet"),
            "system_prompt": system_prompt or "You are a helpful AI assistant.",
            "api_key": api_key,
            "base_url": "https://openrouter.ai/api/v1"
        }
    }
    
    try:
        flow = SuperegoFlow(flow_config)
        print(f"Created SuperegoFlow with:")
        print(f"  - InputSuperego model: {flow_config['input_superego_config']['model']}")
        print(f"  - AutoGen model: {flow_config['autogen_config']['model']}")
        print(f"  - System prompt: {flow_config['autogen_config']['system_prompt']}")
        print("Constitution loaded successfully")
    except Exception as e:
        print(f"Error creating flow: {e}")
        return
    
    # Conversation history
    messages = []
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        if user_input.lower() == "exit":
            break
        
        # Add user message to history
        user_message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=user_input,
            timestamp=datetime.now().isoformat()
        )
        messages.append(user_message)
        
        # Process with flow
        print("\nProcessing...")
        
        try:
            # Use the stream method to get the response
            print()  # Add a blank line before the response
            full_response = ""
            result = FlowResult.SUCCESS  # Default result
            
            # First, evaluate the input with the InputSuperego agent
            evaluation = await flow.input_superego.evaluate_input(user_input)
            
            # Show the superego evaluation
            print(f"\n🧠 Superego evaluation: {evaluation.decision.value}")
            print(f"Reason: {evaluation.reason.strip()}")
            
            # If the input is blocked, don't process it further
            if evaluation.decision == SuperegoDecision.BLOCK:
                print("\n⛔ This input was BLOCKED by the Superego agent")
                continue
            
            # Stream the response from the flow
            async for flow_result, token in flow.stream(user_input, {"messages": messages}):
                result = flow_result  # Update the result
                print(token, end="", flush=True)
                full_response += token
            
            print()  # Add a newline at the end
            
            # Add a visual indicator based on the result
            if result == FlowResult.ERROR:
                print("\n❌ An error occurred while processing this input")
            else:
                # Add assistant message to history
                assistant_message = Message(
                    id=str(uuid.uuid4()),
                    role=MessageRole.ASSISTANT,
                    content=full_response,
                    timestamp=datetime.now().isoformat()
                )
                messages.append(assistant_message)
            
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

async def test_constitutions():
    """Test the constitution system"""
    print("Constitution System Test")
    print("Available constitutions:")
    
    constitutions = get_all_constitutions()
    for constitution_id, constitution in constitutions.items():
        print(f"  - {constitution['name']} (ID: {constitution_id})")
    
    while True:
        print("\nOptions:")
        print("1. View constitution")
        print("2. Create new constitution")
        print("3. Test constitution with InputSuperego")
        print("4. Exit")
        
        choice = input("\nChoice: ")
        
        if choice == "1":
            constitution_id = input("Enter constitution ID: ")
            constitution = get_all_constitutions().get(constitution_id)
            if constitution:
                print(f"\n{constitution['name']}:\n")
                print(constitution['content'])
            else:
                print(f"Constitution with ID {constitution_id} not found")
        
        elif choice == "2":
            constitution_id = input("Enter new constitution ID: ")
            name = input("Enter constitution name: ")
            print("Enter constitution content (end with a line containing only 'END'):")
            
            content_lines = []
            while True:
                line = input()
                if line == "END":
                    break
                content_lines.append(line)
            
            content = "\n".join(content_lines)
            success = save_constitution(constitution_id, name, content)
            
            if success:
                print(f"Constitution '{name}' saved successfully")
            else:
                print("Failed to save constitution")
        
        elif choice == "3":
            constitution_id = input("Enter constitution ID to test: ")
            constitution = get_all_constitutions().get(constitution_id)
            if not constitution:
                print(f"Constitution with ID {constitution_id} not found")
                continue
                
            print(f"Testing constitution: {constitution['name']}")
            await test_input_superego(constitution['content'])
        
        elif choice == "4":
            break
        
        else:
            print("Invalid choice")

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(description="Superego-LangChain CLI Test Harness")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # AutoGen agent command
    autogen_parser = subparsers.add_parser("autogen", help="Test the AutoGen agent")
    autogen_parser.add_argument("--system-prompt", help="System prompt for the agent")
    
    # InputSuperego agent command
    superego_parser = subparsers.add_parser("superego", help="Test the InputSuperego agent")
    superego_parser.add_argument("--constitution", help="Constitution for the agent")
    
    # SuperegoFlow command
    flow_parser = subparsers.add_parser("flow", help="Test the SuperegoFlow")
    flow_parser.add_argument("--system-prompt", help="System prompt for the AutoGen agent")
    flow_parser.add_argument("--constitution", help="Constitution for the InputSuperego agent")
    
    # Constitutions command
    subparsers.add_parser("constitutions", help="Test the constitution system")
    
    args = parser.parse_args()
    
    if args.command == "autogen":
        asyncio.run(test_autogen_agent(args.system_prompt))
    elif args.command == "superego":
        asyncio.run(test_input_superego(args.constitution))
    elif args.command == "flow":
        asyncio.run(test_superego_flow(args.system_prompt, args.constitution))
    elif args.command == "constitutions":
        asyncio.run(test_constitutions())
    else:
        # Default to AutoGen agent if no command is specified
        asyncio.run(test_autogen_agent(None))

if __name__ == "__main__":
    main()
