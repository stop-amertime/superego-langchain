#!/usr/bin/env python
"""
Core flow engine module for Superego Agent System.
Provides a unified interface for managing flow state and execution.
"""
from typing import Dict, List, Optional, Any, AsyncGenerator
import uuid
from datetime import datetime
import asyncio
from pydantic import BaseModel, Field

from flow.builder import build_flow
from flow.executor import execute_flow
from flow.loader import load_flow, embed_constitutions, get_constitutions_map


class StreamChunk(BaseModel):
    """A chunk of streaming output from the flow execution."""
    partial_output: str = Field(description="Partial output content")
    complete: bool = Field(description="Whether this is the final chunk")
    flow_step: Optional[Dict[str, Any]] = Field(None, description="Complete flow step (only present on final chunk)")


class FlowStep(BaseModel):
    """A step in the flow execution."""
    step_id: str = Field(description="Unique identifier for this step")
    agent_id: str = Field(description="Identifier for the agent that produced this step")
    timestamp: str = Field(description="ISO timestamp when this step was created")
    role: str = Field(description="Role of the agent (user, assistant, etc.)")
    input: Optional[str] = Field(None, description="Input provided to this step")
    system_prompt: Optional[str] = Field(None, description="System prompt used for this step")
    thinking: Optional[str] = Field(None, description="Agent's thinking process (not shown to user)")
    tool_usage: Optional[Dict[str, Any]] = Field(None, description="Record of any tool usage in this step")
    agent_guidance: Optional[str] = Field(None, description="Guidance provided to the next agent")
    response: str = Field(description="Response content from this step")
    next_agent: Optional[str] = Field(None, description="ID of the next agent to call")


class FlowEngine:
    """Minimalist flow orchestration engine. Provides a unified interface for 
    creating, executing, and managing flows without unnecessary abstractions.
    """
    
    def __init__(self):
        """Initialize the flow engine with empty registries."""
        self.flow_definitions = {}
        self.active_flows = {}
        self.constitutions = {}
    
    async def load_constitutions(self, directory: str) -> None:
        """Load constitutions from directory."""
        self.constitutions = get_constitutions_map(directory)
    
    async def load_flow_definitions(self, directory: str) -> List[str]:
        """Load flow definitions from directory."""
        from pathlib import Path
        
        flow_ids = []
        for file_path in Path(directory).glob("*.json"):
            flow_def = load_flow(str(file_path))
            
            # Embed constitutions
            flow_def = embed_constitutions(flow_def, self.constitutions)
            
            # Store with ID
            flow_id = flow_def.get("id", str(uuid.uuid4()))
            self.flow_definitions[flow_id] = flow_def
            flow_ids.append(flow_id)
            
        return flow_ids
    
    async def create_flow(self, flow_id: str, llm: Any) -> str:
        """Create a flow instance from a flow definition."""
        if flow_id not in self.flow_definitions:
            raise ValueError(f"Flow definition {flow_id} not found")
        
        # Generate instance ID
        instance_id = str(uuid.uuid4())
        
        # Build flow graph
        flow_def = self.flow_definitions[flow_id]
        flow_graph = build_flow(flow_def, llm)
        
        # Store in active flows with default tool confirmation settings
        self.active_flows[instance_id] = {
            "graph": flow_graph,
            "definition": flow_def,
            "history": [],
            "tool_confirmation_settings": {
                "confirm_all": True,
                "exempted_tools": []
            },
            "pending_tool_executions": {}
        }
        
        return instance_id
    
    async def execute(self, instance_id: str, input_message: str) -> AsyncGenerator[Dict, None]:
        """Execute a flow instance with the given input message."""
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
        
        flow_data = self.active_flows[instance_id]
        flow_graph = flow_data["graph"]
        
        # Create user step
        user_step = {
            "step_id": str(uuid.uuid4()),
            "agent_id": "user",
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "input": None,
            "response": input_message,
            "next_agent": flow_data["definition"]["graph"]["start"]
        }
        
        # Update history
        flow_data["history"].append(user_step)
        
        # Execute flow
        async for step in execute_flow(flow_graph, user_step):
            # Store complete steps in history
            if step.get("complete", False) and "flow_step" in step:
                flow_data["history"].append(step["flow_step"])
            
            # Yield step for streaming
            yield step
    
    def get_flow_history(self, instance_id: str) -> List[Dict]:
        """Get the history of a flow instance."""
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
        
        return self.active_flows[instance_id]["history"]
    
    def get_flow_definition(self, flow_id: str) -> Dict:
        """Get a flow definition by ID."""
        if flow_id not in self.flow_definitions:
            raise ValueError(f"Flow definition {flow_id} not found")
        
        return self.flow_definitions[flow_id]
    
    def get_available_flows(self) -> List[Dict]:
        """Get a list of available flow definitions."""
        return [
            {
                "id": flow_id,
                "name": flow_def.get("name", "Unnamed Flow"),
                "description": flow_def.get("description", "")
            }
            for flow_id, flow_def in self.flow_definitions.items()
        ]
        
    async def execute_pending_tool(self, instance_id: str, tool_execution_id: str) -> Dict:
        """Execute a pending tool after user confirmation.
        
        Args:
            instance_id: ID of the flow instance
            tool_execution_id: ID of the pending tool execution
            
        Returns:
            Result of tool execution
            
        Raises:
            ValueError: If the instance or tool execution is not found
        """
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
            
        flow_instance = self.active_flows[instance_id]
        
        if tool_execution_id not in flow_instance["pending_tool_executions"]:
            raise ValueError(f"Tool execution {tool_execution_id} not found")
            
        # Get tool execution details
        pending_execution = flow_instance["pending_tool_executions"][tool_execution_id]
        tool_name = pending_execution["tool_name"]
        tool_input = pending_execution["tool_input"]
        
        # Import tool execution function
        from ..agents.inner_agent import execute_tool
        
        # For simplicity, we're using a stub for available_tools
        # In a real implementation, this would come from the flow state
        from ..tools.calculator import register_tools
        available_tools = register_tools()
        
        # Execute the tool
        result = await execute_tool(tool_name, tool_input, available_tools)
        
        # Update the flow state with the result
        # This would normally trigger a continuation of the flow
        pending_execution["result"] = result
        
        # Remove the pending execution
        del flow_instance["pending_tool_executions"][tool_execution_id]
        
        return {
            "tool_name": tool_name,
            "input": tool_input,
            "result": result
        }


# Singleton instance for global access
# This avoids unnecessary class instantiation while maintaining a clear API
flow_engine = FlowEngine()


async def initialize_engine(constitutions_dir: str, flow_defs_dir: str) -> FlowEngine:
    """Initialize the flow engine with constitutions and flow definitions."""
    await flow_engine.load_constitutions(constitutions_dir)
    await flow_engine.load_flow_definitions(flow_defs_dir)
    return flow_engine
