"""
Shared models for Superego Agent System

Contains Pydantic models used across multiple modules to avoid circular imports.
"""

from typing import Dict, Optional, Any
from pydantic import BaseModel, Field


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
    constitution: Optional[str] = Field(None, description="Constitution text (for superego agents)")
    decision: Optional[str] = Field(None, description="Decision made by a superego agent")
