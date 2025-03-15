#!/usr/bin/env python3
from typing import AsyncGenerator, Dict, Any, Optional
from langgraph.graph import StateGraph
from collections import defaultdict
from ..agents.commands import AWAITING_TOOL_CONFIRMATION, ACCEPT

async def execute_flow(flow: StateGraph, input_message: str, flow_def: Dict) -> AsyncGenerator[Dict[Any, Any], None]:
    """Execute a flow graph with streaming output.
    
    Args:
        flow: Compiled StateGraph instance
        input_message: User input message
        flow_def: Required flow definition with instance_id
        
    Yields:
        Stream of flow record steps with sensitive fields filtered
        
    Raises:
        ValueError: If flow_def is missing or doesn't contain instance_id
    """
    import logging
    import traceback
    logger = logging.getLogger("uvicorn")
    logger.info("Started execute_flow")
    
    # Validate required parameters
    if not flow_def:
        raise ValueError("Flow definition is required for execution")
        
    if "instance_id" not in flow_def:
        raise ValueError("Flow definition must contain an instance_id for execution")
    
    # Get the starting node - either from flow.config or fallback to flow_def
    start_node = None
    if flow.config and "graph" in flow.config and "start" in flow.config["graph"]:
        start_node = flow.config["graph"]["start"]
    else:
        # Fallback to the flow definition if flow.config is not available
        start_node = flow_def.get("graph", {}).get("start")
        if not start_node:
            raise ValueError("Could not determine start node from flow or flow definition")
        logger.info(f"Using start node from flow definition: {start_node}")
    
    # Create initial user step with required instance_id
    user_step = {
        "agent_id": "user",
        "role": "user",
        "response": input_message,
        "next_agent": start_node,
        "instance_id": flow_def["instance_id"]  # Required field
    }
    
    # Create the initial state with the instance_id
    initial_state = {
        "flow_record": [user_step],
        "instance_id": flow_def["instance_id"]  # Set instance_id explicitly in the state
    }
    
    # Log initial state
    logger.info(f"Initial state created with instance_id: {flow_def['instance_id']}")
    logger.info(f"First node will be: {start_node}")
    
    try:
        # Log when starting astream execution
        logger.info("Beginning flow.astream execution")
        
        # Execute flow graph with the initial state
        async for step in flow.astream(initial_state):
            logger.info(f"Received step from flow.astream: {type(step).__name__}")
            logger.info(f"Step keys: {list(step.keys() if isinstance(step, dict) else [])}")
            
            if isinstance(step, dict) and "flow_record" in step:
                # Extract latest step from state
                latest = step["flow_record"][-1]
                logger.info(f"Latest step keys: {list(latest.keys() if isinstance(latest, dict) else [])}")
                
                # Add special handling for awaiting tool confirmation
                if latest.get("next_agent") == AWAITING_TOOL_CONFIRMATION:
                    logger.info("Step is awaiting tool confirmation")
                    # The actual response is set in inner_agent.py already
                    pass
                
                # Filter sensitive fields from user-visible output
                filtered = {k: v for k, v in latest.items() 
                           if k not in ["thinking", "agent_guidance"]}
                
                # Include instance_id if available
                if flow_def and "instance_id" in flow_def:
                    filtered["instance_id"] = flow_def["instance_id"]
                
                logger.info(f"Yielding filtered step with keys: {list(filtered.keys())}")
                yield filtered
            else:
                # Streaming responses from inner_agent_node through StreamChunk
                logger.info(f"Direct yield of step: {type(step).__name__}")
                if hasattr(step, 'partial_output'):
                    logger.debug(f"Streaming partial output: '{step.partial_output[:50]}...'")
                    logger.debug(f"Complete: {step.complete}")
                    if hasattr(step, 'flow_step') and step.flow_step:
                        logger.debug(f"With flow_step: {step.flow_step}")
                yield step
    except Exception as e:
        logger.error(f"Error in execute_flow: {str(e)}")
        logger.error(traceback.format_exc())
        raise
