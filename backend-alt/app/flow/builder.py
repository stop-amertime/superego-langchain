#!/usr/bin/env python3
"""
flow/builder.py - Constructs LangGraph from flow definition
"""
from typing import Dict, Any, Callable, Optional
from langgraph.graph import StateGraph
from ..agents.superego import create_superego_node
from ..agents.inner_agent import create_inner_agent_node

# Map node types to their creator functions
NODE_CREATORS = {
    "superego": create_superego_node,
    "inner_agent": create_inner_agent_node
}


def build_flow(flow_def: Dict[str, Any], llm) -> StateGraph:
    """
    Constructs a StateGraph from a flow definition.
    
    Args:
        flow_def: Flow definition dictionary
        llm: Language model instance
        
    Returns:
        Compiled StateGraph with cycle support
    """
    graph_def = flow_def.get("graph", {})
    start_node = graph_def.get("start")
    nodes = graph_def.get("nodes", {})
    
    if not start_node or not nodes:
        raise ValueError("Flow definition missing required 'start' or 'nodes'")
    
    # Create state graph
    graph = StateGraph(nodes={"flow_record": list})
    
    # Register all nodes
    for node_name, config in nodes.items():
        node_type = config.get("type")
        
        # Skip if missing required fields
        if not node_type or node_type not in NODE_CREATORS:
            raise ValueError(f"Node '{node_name}' has invalid type: {node_type}")
        
        # Create node using appropriate creator function
        creator_fn = NODE_CREATORS[node_type]
        node_fn = creator_fn(
            llm=llm,
            agent_id=config.get("agent_id", node_name),
            max_iterations=config.get("max_iterations", 3),
            **({"constitution": config.get("constitution")} if node_type == "superego" else {}),
            **({"system_prompt": config.get("system_prompt")} if node_type == "inner_agent" else {}),
            **({"available_tools": _get_tools(config.get("tools", []))} if node_type == "inner_agent" else {})
        )
        
        graph.add_node(node_name, node_fn)
    
    # Set entry point
    graph.set_entry_point(start_node)
    
    # Define conditional routing
    for node_name, config in nodes.items():
        transitions = config.get("transitions", {})
        if transitions:
            graph.add_conditional_edges(
                node_name,
                _create_router(transitions, node_name)
            )
    
    return graph.compile()


def _get_tools(tool_names):
    """Convert tool names to tool references - would import actual tools in production"""
    return {name: name for name in tool_names}


def _create_router(transitions: Dict[str, Optional[str]], current_node: str):
    """Create a unified router function that handles node transitions"""
    def router(flow_record: list) -> Optional[str]:
        if not flow_record:
            return None
        
        last_step = flow_record[-1]
        
        # First check decision field (used by superego)
        decision = last_step.get("decision")
        if decision and decision in transitions:
            next_node = transitions[decision]
            return current_node if next_node == "self" else next_node
            
        # Then check next_agent field (used by inner agents)
        next_agent = last_step.get("next_agent")
        if next_agent:
            if next_agent == current_node or next_agent == "self":
                return current_node
            if next_agent in transitions:
                return transitions[next_agent]
        
        # Use wildcard if available
        if "*" in transitions:
            next_node = transitions["*"]
            return current_node if next_node == "self" else next_node
            
        return None
    
    return router
