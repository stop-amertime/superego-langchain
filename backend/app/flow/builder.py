#!/usr/bin/env python3
"""
flow/builder.py - Constructs LangGraph from flow definition
"""
from typing import Dict, Any, Callable, Optional, List
from langgraph.graph import StateGraph
from pydantic import BaseModel, Field
from ..agents.superego import create_superego_node
from ..agents.inner_agent import create_inner_agent_node

# Define a proper schema with BaseModel which is hashable
class FlowState(BaseModel):
    flow_record: list = Field(default_factory=list)
    instance_id: Optional[str] = Field(default=None)

# Map node types to their creator functions
NODE_CREATORS = {
    "superego": create_superego_node,
    "inner_agent": create_inner_agent_node
}


async def build_flow(flow_def: Dict[str, Any], llm) -> StateGraph:
    """
    Constructs a StateGraph from a flow definition.
    
    Args:
        flow_def: Flow definition dictionary
        llm: Language model instance
        
    Returns:
        Compiled StateGraph with cycle support
    """
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info("Starting build_flow")
    
    graph_def = flow_def.get("graph", {})
    start_node = graph_def.get("start")
    nodes = graph_def.get("nodes", {})
    
    if not start_node or not nodes:
        raise ValueError("Flow definition missing required 'start' or 'nodes'")
    
    # Initialize graph with input/output types
    graph = StateGraph(input=FlowState, output=FlowState)
    logger.info(f"Created StateGraph with schema FlowState")
    
    # Register all nodes
    for node_name, config in nodes.items():
        node_type = config.get("type")
        logger.info(f"Building node '{node_name}' of type '{node_type}'")
        
        # Skip if missing required fields
        if not node_type or node_type not in NODE_CREATORS:
            raise ValueError(f"Node '{node_name}' has invalid type: {node_type}")
        
        # Create node using appropriate creator function
        creator_fn = NODE_CREATORS[node_type]
        if node_type == "inner_agent" and "tools" in config:
            tools = config.get("tools", [])
            logger.info(f"Node '{node_name}' uses tools: {tools}")
            
            # Get actual tool functions
            tool_functions = _get_tools(tools)
            logger.info(f"Retrieved functions for tools: {list(tool_functions.keys())}")
            
            for tool_name, tool_fn in tool_functions.items():
                logger.info(f"Tool '{tool_name}' function type: {type(tool_fn).__name__}")
        
        logger.info(f"Creating node function for '{node_name}'")
        node_fn = await creator_fn(
            llm=llm,
            agent_id=config.get("agent_id", node_name),
            max_iterations=config.get("max_iterations", 3),
            **({"constitution": config.get("constitution")} if node_type == "superego" else {}),
            **({"system_prompt": config.get("system_prompt")} if node_type == "inner_agent" else {}),
            **({"available_tools": _get_tools(config.get("tools", []))} if node_type == "inner_agent" else {})
        )
        logger.info(f"Adding node '{node_name}' to graph with function type: {type(node_fn).__name__}")
        
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
    """Convert tool names to actual tool functions"""
    # We need to import the real tools
    from ..tools.calculator import calculate, register_tools
    
    # Get all registered tools properly
    registered_tools = register_tools()
    
    # Double check we have all tools and create a map with actual functions
    result = {}
    for name in tool_names:
        if name in registered_tools:
            # Add the actual function
            result[name] = registered_tools[name]
        else:
            print(f"Warning: Tool '{name}' not found in registered tools")
    
    return result


def _create_router(transitions: Dict[str, Optional[str]], current_node: str):
    """Create a unified router function that handles node transitions"""
    async def router(state: FlowState) -> Optional[str]:
        import logging
        logger = logging.getLogger("uvicorn")
        
        flow_record = state.flow_record
        if not flow_record:
            logger.debug(f"Router: No flow record, returning None")
            return None
        
        last_step = flow_record[-1]
        
        # Log the decision and next_agent fields
        decision = last_step.get("decision")
        next_agent = last_step.get("next_agent")
        logger.debug(f"Router ({current_node}): Decision={decision}, next_agent={next_agent}")
        logger.debug(f"Router ({current_node}): Available transitions={transitions}")
        
        # First check decision field (used by superego)
        if decision and decision in transitions:
            next_node = transitions[decision]
            logger.debug(f"Router: Using decision '{decision}', next_node={next_node}")
            return current_node if next_node == "self" else next_node
            
        # Then check next_agent field (used by inner agents)
        if next_agent:
            if next_agent == current_node or next_agent == "self":
                logger.debug(f"Router: next_agent self-loop, returning {current_node}")
                return current_node
            if next_agent in transitions:
                logger.debug(f"Router: Using next_agent '{next_agent}', transition={transitions[next_agent]}")
                return transitions[next_agent]
            logger.debug(f"Router: next_agent '{next_agent}' not in transitions")
        
        # Use wildcard if available
        if "*" in transitions:
            next_node = transitions["*"]
            logger.debug(f"Router: Using wildcard, next_node={next_node}")
            return current_node if next_node == "self" else next_node
        
        logger.debug(f"Router: No matching transition, returning None")
        return None
    
    return router
