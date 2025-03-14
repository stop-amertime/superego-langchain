#!/usr/bin/env python3
from typing import AsyncGenerator, Dict, Any, Optional
from langgraph.graph import StateGraph
from ..agents.commands import AWAITING_TOOL_CONFIRMATION

async def execute_flow(flow: StateGraph, input_message: str, flow_def: Optional[Dict] = None) -> AsyncGenerator[Dict[Any, Any], None]:
    """Execute a flow graph with streaming output.
    
    Args:
        flow: Compiled StateGraph instance
        input_message: User input message
        flow_def: Optional flow definition for additional context
        
    Yields:
        Stream of flow record steps with sensitive fields filtered
    """
    # Create initial user step
    user_step = {
        "agent_id": "user",
        "role": "user",
        "response": input_message,
        "next_agent": flow.config["graph"]["start"],
        "instance_id": flow_def.get("instance_id") if flow_def else None
    }
    
    # Execute flow graph
    async for step in flow.astream({"messages": [user_step]}):
        # Extract latest step from state
        latest = step["messages"][-1]
        
        # Add special handling for awaiting tool confirmation
        if latest.get("next_agent") == AWAITING_TOOL_CONFIRMATION:
            # Change response to indicate waiting for confirmation
            # (The actual response is set in inner_agent.py already)
            pass
        
        # Filter sensitive fields from user-visible output
        filtered = {k: v for k, v in latest.items() 
                   if k not in ["thinking", "agent_guidance"]}
        
        # Include instance_id if available
        if flow_def and "instance_id" in flow_def:
            filtered["instance_id"] = flow_def["instance_id"]
        
        yield filtered
