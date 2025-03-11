"""
Flow Engine for Superego Agent System

Core functionality for building and executing langgraph flows with superego agents.
Minimal, elegant implementation with streaming support.
"""

import uuid
import datetime
from typing import AsyncGenerator, Dict, List, Optional, Any, Callable, Literal
import anyio
from langgraph.graph import StateGraph, END
from pydantic import BaseModel, Field


# Superego decisions as literals for type safety
SuperegoDecision = Literal["BLOCK", "ACCEPT", "CAUTION", "NEEDS_CLARIFICATION"]
BLOCK: SuperegoDecision = "BLOCK"
ACCEPT: SuperegoDecision = "ACCEPT" 
CAUTION: SuperegoDecision = "CAUTION"
NEEDS_CLARIFICATION: SuperegoDecision = "NEEDS_CLARIFICATION"


class FlowStep(BaseModel):
    """Individual step in a flow execution"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str
    timestamp: str = Field(default_factory=lambda: datetime.datetime.now().isoformat())
    role: str
    input: Optional[str] = None
    constitution: Optional[str] = None
    system_prompt: Optional[str] = None
    thinking: Optional[str] = None
    decision: Optional[SuperegoDecision] = None
    notes: Optional[str] = None
    response: Optional[str] = None
    tool_usage: Optional[Dict[str, Any]] = None
    next_agent: Optional[str] = None


class FlowState(BaseModel):
    """Flow execution state"""
    flow_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    steps: List[FlowStep] = Field(default_factory=list)
    current_node: str
    iteration_counts: Dict[str, int] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class StreamChunk(BaseModel):
    """Chunk of streaming output from a node"""
    partial_output: str
    complete: bool = False
    flow_step: Optional[FlowStep] = None

def build_flow(flow_def: Dict[str, Any], agent_nodes: Dict[str, Callable]) -> StateGraph:
    """Build a flow from a flow definition and agent nodes"""
    graph = StateGraph(FlowState)
    
    # Add nodes and set entry point
    for node_name, node_def in flow_def["graph"]["nodes"].items():
        if node_name in agent_nodes:
            graph.add_node(node_name, agent_nodes[node_name])
    
    graph.set_entry_point(flow_def["graph"]["start"])
    
    # Add edges with transition logic
    for node_name, node_def in flow_def["graph"]["nodes"].items():
        if "transitions" not in node_def:
            continue
            
        transitions = node_def["transitions"]
        max_iterations = node_def.get("max_iterations", 3)
        agent_id = node_def.get("agent_id", node_name)
        
        # Define router for this node
        def router_for(node, agent, trans, max_iter):
            def route(state: FlowState) -> str:
                # Stop if iteration limit reached
                if state.iteration_counts.get(node, 0) >= max_iter:
                    return END
                
                # Find latest relevant step
                for step in reversed(state.steps):
                    if step.agent_id != agent:
                        continue
                    
                    # Route based on decision
                    if step.decision and step.decision in trans:
                        next_node = trans[step.decision]
                        if next_node == node:  # Self-reference
                            counts = dict(state.iteration_counts)
                            counts[node] = counts.get(node, 0) + 1
                            return FlowState(
                                flow_id=state.flow_id,
                                steps=state.steps,
                                current_node=state.current_node,
                                iteration_counts=counts,
                                metadata=state.metadata
                            )
                        return next_node if next_node is not None else END
                    
                    # Route based on next_agent
                    if step.next_agent:
                        if step.next_agent == node:  # Self-reference
                            counts = dict(state.iteration_counts)
                            counts[node] = counts.get(node, 0) + 1
                            return FlowState(
                                flow_id=state.flow_id,
                                steps=state.steps,
                                current_node=state.current_node,
                                iteration_counts=counts,
                                metadata=state.metadata
                            )
                        return step.next_agent if step.next_agent in flow_def["graph"]["nodes"] else END
                    
                    # Default transition
                    if "*" in trans:
                        return trans["*"]
                    break
                
                return END
            return route
        
        # Add conditional edges
        graph.add_conditional_edges(
            node_name, 
            router_for(node_name, agent_id, transitions, max_iterations)
        )
    
    return graph.compile()


async def execute_flow(
    flow: StateGraph, 
    user_input: str, 
    flow_def: Dict[str, Any]
) -> AsyncGenerator[FlowStep, None]:
    """Execute a flow with the given input"""
    # Create initial step and state
    initial_step = FlowStep(
        agent_id="user",
        role="user",
        response=user_input,
        next_agent=flow_def["graph"]["start"]
    )
    
    state = FlowState(
        steps=[initial_step],
        current_node=flow_def["graph"]["start"]
    )
    
    # Yield the initial user step
    yield initial_step
    
    # Stream steps from flow execution
    async for event in flow.astream(state):
        new_state = event.get("state")
        if not new_state:
            continue
            
        # Yield any new steps
        if len(new_state.steps) > len(state.steps):
            yield from new_state.steps[len(state.steps):]
            
        state = new_state


async def stream_node_output(
    node_generator: AsyncGenerator[StreamChunk, None]
) -> AsyncGenerator[FlowStep, None]:
    """Stream partial and complete output from a node"""
    partial_step = None
    
    async for chunk in node_generator:
        if chunk.complete and chunk.flow_step:
            yield chunk.flow_step
            continue
            
        if chunk.partial_output:
            # Simple streaming step creation
            if not partial_step:
                partial_step = FlowStep(
                    agent_id="streaming",
                    role="assistant",
                    response=chunk.partial_output
                )
            else:
                # Update response in new step
                partial_step = FlowStep(
                    agent_id=partial_step.agent_id,
                    role=partial_step.role,
                    step_id=partial_step.step_id,
                    timestamp=partial_step.timestamp,
                    response=chunk.partial_output
                )
            
            yield partial_step
