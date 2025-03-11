"""
Test script that focuses specifically on the graph traversal issue.
"""

import asyncio
import uuid
from datetime import datetime
import json
import os
import sys

from app.flow_engine import get_flow_engine, FlowDefinition, NodeConfig, EdgeConfig, FlowInstance, Message, MessageRole
from app.models import FlowStatus, SuperegoDecision, SuperegoEvaluation
from app.agents import AgentType

def print_with_flush(message):
    """Print to console with immediate flush to ensure output is visible."""
    print(message, flush=True)
    sys.stdout.flush()  # Extra flush to ensure visibility


async def test_traversal():
    """Test the flow graph traversal directly."""
    print_with_flush("\n\n===== TRAVERSAL TEST =====")
    print_with_flush("Starting traversal test")
    
    # Get the flow engine
    flow_engine = get_flow_engine()
    
    # Create a new test flow definition
    definition_id = str(uuid.uuid4())
    definition = FlowDefinition(
        id=definition_id,
        name="Test Traversal Flow",
        description="Test flow with simple nodes to test graph traversal",
        nodes={
            "node_a": NodeConfig(
                type=AgentType.INPUT_SUPEREGO,
                config={
                    "constitution": "default"
                }
            ),
            "node_b": NodeConfig(
                type=AgentType.GENERAL_ASSISTANT,
                config={
                    "system_prompt": "You are a helpful assistant."
                }
            )
        },
        edges=[
            {"from_node": "START", "to_node": "node_a", "condition": None},
            {"from_node": "node_a", "to_node": "node_b", "condition": "ALLOW"},
            {"from_node": "node_a", "to_node": "END", "condition": "BLOCK"},
            {"from_node": "node_b", "to_node": "END", "condition": None}
        ]
    )
    
    # Create the definition in the flow engine
    flow_engine.create_flow_definition(definition)
    print_with_flush(f"Created flow definition: {definition_id}")
    
    # Create a flow instance
    instance = flow_engine.create_flow_instance(
        definition_id=definition_id,
        name="Test Traversal Instance",
        description="Instance for testing graph traversal"
    )
    print_with_flush(f"Created flow instance: {instance.id}")
    
    # Process a user message
    print_with_flush("\nProcessing test message...")
    result = await flow_engine.process_user_input(
        instance_id=instance.id,
        user_input="Test message for traversal testing",
        on_token=None,
        on_thinking=None
    )
    
    # Get the final instance state
    instance = flow_engine.get_flow_instance(instance.id)
    
    # Analyze the result
    print_with_flush(f"\nRESULT:")
    print_with_flush(f"Last node: {result.get('last_node')}")
    print_with_flush(f"Current instance node: {instance.current_node}")
    print_with_flush(f"Status: {instance.status}")
    
    # Check the history to see if all nodes were visited
    print_with_flush("\nNode execution history:")
    for i, exec_record in enumerate(instance.history):
        print_with_flush(f"  Execution {i+1}:")
        print_with_flush(f"    Node: {exec_record.node_id}")
        print_with_flush(f"    Input: {exec_record.input}")
        # Check if output is a dictionary with goto
        if isinstance(exec_record.output, dict) and "goto" in exec_record.output:
            print_with_flush(f"    Output goto: {exec_record.output['goto']}")
    
    # Check if we have conversation history
    if hasattr(instance, "conversation"):
        print_with_flush("\nConversation history:")
        for i, turn in enumerate(instance.conversation):
            print_with_flush(f"  Turn {i+1}:")
            print_with_flush(f"    User input: {turn.get('user_input')}")
            print_with_flush(f"    Agent responses: {len(turn.get('agent_responses', []))}")
            for j, response in enumerate(turn.get('agent_responses', [])):
                print_with_flush(f"      Response {j+1}: {response.get('node_id')}")
    
    # Test outcome
    if instance.current_node == "node_b" or result.get('last_node') == "node_b":
        print_with_flush("\n✅ SUCCESS: Flow successfully traversed from node_a to node_b!")
    else:
        print_with_flush("\n❌ FAILURE: Flow did not complete traversal to node_b.")
    
    # Clean up - delete the test instance
    flow_engine.delete_flow_instance(instance.id)
    print_with_flush(f"Deleted test instance: {instance.id}")
    print_with_flush("===== TEST COMPLETE =====\n")

if __name__ == "__main__":
    asyncio.run(test_traversal())
