"""
Simple debug script to trace flow execution.
"""

import asyncio
import logging
import sys
import uuid
from datetime import datetime

from app.flow_engine import get_flow_engine, FlowDefinition, NodeConfig, EdgeConfig
from app.models import FlowStatus
from app.agents import AgentType

# Set up logging to console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Additional loggers
for name in ["app.flow_engine", "langgraph"]:
    module_logger = logging.getLogger(name)
    module_logger.setLevel(logging.INFO)

def print_big(message):
    """Print a message with emphasis."""
    line = "=" * 50
    print(f"\n{line}\n{message}\n{line}\n")

async def test_flow_traversal():
    """Test if flow can traverse from input_superego to assistant."""
    print_big("STARTING FLOW TRAVERSAL TEST")
    
    # Get the flow engine
    flow_engine = get_flow_engine()
    
    print("Creating test flow definition...")
    # Create a test flow definition with the simplest possible path
    definition_id = str(uuid.uuid4())
    definition = FlowDefinition(
        id=definition_id,
        name="Debug Flow",
        description="Simple flow for debugging",
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
            {"from_node": "node_a", "to_node": "node_b"},  # Unconditional edge for testing
            {"from_node": "node_b", "to_node": "END"}
        ]
    )
    
    # Create the definition in the flow engine
    flow_engine.create_flow_definition(definition)
    print(f"Created flow definition: {definition_id}")
    
    # Create a flow instance
    print("Creating test flow instance...")
    instance = flow_engine.create_flow_instance(
        definition_id=definition_id,
        name="Debug Test Instance",
        description="Instance for debugging traversal"
    )
    print(f"Created flow instance: {instance.id}")
    
    # Process a user message
    print_big("PROCESSING TEST MESSAGE")
    result = await flow_engine.process_user_input(
        instance_id=instance.id,
        user_input="This is a test message for flow traversal",
        on_token=None,
        on_thinking=None
    )
    
    # Get the final instance state
    instance = flow_engine.get_flow_instance(instance.id)
    
    # Print the result
    print_big("TEST RESULTS")
    print(f"Current node: {instance.current_node}")
    print(f"Last node: {result.get('last_node')}")
    print(f"Status: {instance.status}")
    
    # Check execution history
    print("\nNode execution history:")
    for i, exec_record in enumerate(instance.history):
        print(f"  {i+1}. Node: {exec_record.node_id}")
    
    # Test outcome
    if result.get('last_node') == "node_b" or instance.current_node == "node_b":
        print_big("✅ SUCCESS: Flow successfully traversed to node_b!")
    else:
        print_big("❌ FAILURE: Flow did not complete traversal to node_b.")
    
    # Clean up - delete the test instance
    flow_engine.delete_flow_instance(instance.id)
    print(f"Deleted test instance: {instance.id}")

if __name__ == "__main__":
    asyncio.run(test_flow_traversal())
