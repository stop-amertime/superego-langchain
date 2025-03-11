"""
Test script with a simplified flow to confirm graph traversal is working.
"""

import asyncio
import logging
import sys
import uuid

from app.flow_engine import get_flow_engine, FlowDefinition, NodeConfig
from app.models import FlowStatus
from app.agents import AgentType

# Set up logging to console
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def print_highlight(message):
    """Print a message highlighted."""
    print(f"\n{'*'*70}\n* {message}\n{'*'*70}\n")

async def test_very_simple_flow():
    """Create and test the simplest possible flow between two nodes."""
    print_highlight("CREATING MINIMAL FLOW TEST")
    
    # Get the flow engine
    flow_engine = get_flow_engine()
    
    # Create a new simplified test flow definition
    # This flow has NO conditional edges - just direct traversal from A to B
    definition_id = str(uuid.uuid4())
    definition = FlowDefinition(
        id=definition_id,
        name="Minimal Test Flow",
        description="Simplest possible flow between two nodes",
        nodes={
            "node_a": NodeConfig(
                type=AgentType.INPUT_SUPEREGO,
                config={"constitution": "default"}
            ),
            "node_b": NodeConfig(
                type=AgentType.GENERAL_ASSISTANT,
                config={"system_prompt": "You are a helpful assistant."}
            )
        },
        edges=[
            {"from_node": "START", "to_node": "node_a"},
            {"from_node": "node_a", "to_node": "node_b"},  # Direct edge, no condition
            {"from_node": "node_b", "to_node": "END"}
        ]
    )
    
    # Create the definition and a test instance
    flow_engine.create_flow_definition(definition)
    instance = flow_engine.create_flow_instance(
        definition_id=definition_id,
        name="Minimal Test Instance",
        description="Test instance with simple direct routing"
    )
    print_highlight(f"Created flow: {definition_id}\nCreated instance: {instance.id}")
    
    # Process a test message
    print_highlight("PROCESSING TEST MESSAGE")
    result = await flow_engine.process_user_input(
        instance_id=instance.id,
        user_input="This is a simple test message",
        on_token=None,
        on_thinking=None
    )
    
    # Get the final instance state
    instance = flow_engine.get_flow_instance(instance.id)
    
    # Check results
    print_highlight("TEST RESULTS")
    print(f"Final instance node: {instance.current_node}")
    print(f"Result last_node: {result.get('last_node')}")
    print(f"Status: {instance.status}")
    
    # Check history
    print("\nExecution History:")
    for i, record in enumerate(instance.history):
        print(f"{i+1}. Node: {record.node_id}")
    
    # Check traversal outcome
    if instance.current_node == "node_b" or result.get('last_node') == "node_b":
        print_highlight("SUCCESS: Flow traversed completely from node_a to node_b!")
    else:
        print_highlight("FAILURE: Flow did not complete the traversal to node_b")
    
    # Clean up
    flow_engine.delete_flow_instance(instance.id)
    print(f"Deleted test instance: {instance.id}")

if __name__ == "__main__":
    print_highlight("MINIMAL FLOW TRAVERSAL TEST")
    asyncio.run(test_very_simple_flow())
