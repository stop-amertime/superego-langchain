"""
Direct test of LangGraph functionality with simplified components.
"""

import asyncio
import logging
import sys
from typing import Dict, Any, List
import uuid

from langgraph.graph import StateGraph, END
from langgraph.types import Command

# Set up logging to console with high verbosity
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

def print_header(message):
    """Print a section header."""
    print(f"\n{'='*50}\n{message}\n{'='*50}\n")

async def node_a_function(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simple node that just passes through and marks it was here."""
    print_header("EXECUTING NODE A")
    print(f"Node A received state: {state}")
    
    # Return updated state
    state.update({
        "visited_a": True,
        "last_node": "node_a"
    })
    print(f"Node A returning state: {state}")
    
    # Instead of returning state, let's return a Command object to goto node_b
    print("Node A returning Command to goto node_b")
    return Command(
        goto="node_b",
        update={"from_node_a": True, "command_used": True}
    )

async def node_b_function(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simple node that just passes through and marks it was here."""
    print_header("EXECUTING NODE B")
    print(f"Node B received state: {state}")
    
    # Return updated state
    state.update({
        "visited_b": True,
        "last_node": "node_b" 
    })
    print(f"Node B returning state: {state}")
    return state

async def test_simple_graph():
    """Test a simple LangGraph to verify routing works."""
    print_header("CREATING SIMPLE GRAPH")
    
    # Create graph
    builder = StateGraph(Dict)
    
    # Add nodes
    builder.add_node("node_a", node_a_function)
    builder.add_node("node_b", node_b_function)
    
    # Set entry point
    builder.set_entry_point("node_a")
    
    # Add edge from node_a to node_b
    builder.add_edge("node_a", "node_b")
    
    # Add edge from node_b to END
    builder.add_edge("node_b", END)
    
    # Compile graph
    graph = builder.compile()
    
    # Run the graph with a simple initial state
    initial_state = {"input": "test input", "id": str(uuid.uuid4())}
    print(f"Initial state: {initial_state}")
    
    print_header("EXECUTING GRAPH")
    # Execute the graph
    try:
        result = await graph.arun(initial_state)
        print_header("GRAPH EXECUTION COMPLETE")
        print(f"Final state: {result}")
        
        # Check if node_b was visited
        if result.get("visited_b", False):
            print_header("✅ SUCCESS: Graph traversed to node_b")
        else:
            print_header("❌ FAILURE: Graph did not reach node_b")
    except Exception as e:
        print_header(f"ERROR DURING GRAPH EXECUTION: {str(e)}")
        import traceback
        traceback.print_exc()
    
    # Also try with streaming
    print_header("TESTING WITH STREAMING")
    try:
        stream_results = []
        async for event_type, event_data in graph.astream(initial_state):
            print(f"Stream event: {event_type} - {event_data}")
            stream_results.append((event_type, event_data))
        
        print_header("STREAMING COMPLETE")
        # Check if node_b was in the stream events
        node_b_found = any(event == "node_b" for event_type, event in stream_results if event_type == "node")
        if node_b_found:
            print_header("✅ SUCCESS: Stream showed node_b execution")
        else:
            print_header("❌ FAILURE: Stream did not show node_b execution")
    except Exception as e:
        print_header(f"ERROR DURING STREAMING: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print_header("LANGGRAPH DIRECT TEST")
    asyncio.run(test_simple_graph())
