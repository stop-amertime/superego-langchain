from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union, TypedDict, Literal
from enum import Enum
from datetime import datetime


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SUPEREGO = "superego"
    SYSTEM = "system"


class Message(BaseModel):
    id: str
    role: MessageRole
    content: str
    timestamp: str
    decision: Optional[str] = None
    constitutionId: Optional[str] = None
    thinking: Optional[str] = None
    thinkingTime: Optional[str] = None
    withoutSuperego: Optional[str] = None


class SuperegoDecision(str, Enum):
    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    CAUTION = "CAUTION"
    ANALYZING = "ANALYZING"
    ERROR = "ERROR"


class SuperegoEvaluation(BaseModel):
    decision: SuperegoDecision
    reason: str
    thinking: Optional[str] = None
    timestamp: Optional[str] = None
    constitutionId: Optional[str] = None
    status: Optional[str] = None
    id: Optional[str] = None


class UserRequest(BaseModel):
    message: str
    conversationId: Optional[str] = None


# State for LangGraph agents
class AgentState(TypedDict):
    conversation_id: str
    messages: List[Message]
    user_input: str
    superego_evaluation: Optional[SuperegoEvaluation]
    current_output: str
    interrupted: bool
    tools_used: List[Dict[str, Any]]


# WebSocket message types
class WebSocketMessageType(str, Enum):
    USER_MESSAGE = "user_message"
    SUPEREGO_EVALUATION = "superego_evaluation" 
    ASSISTANT_MESSAGE = "assistant_message"
    ASSISTANT_TOKEN = "assistant_token"
    TOOL_USAGE = "tool_usage"
    SUPEREGO_INTERVENTION = "superego_intervention"
    ERROR = "error"
    SYSTEM_MESSAGE = "system_message"
    CONSTITUTIONS_RESPONSE = "constitutions_response"
    RERUN_FROM_CONSTITUTION = "rerun_from_constitution"
    SYSPROMPTS_RESPONSE = "sysprompts_response"
    CONVERSATION_UPDATE = "conversation_update"  # New type for full conversation updates
    FLOW_TEMPLATES_RESPONSE = "flow_templates_response"  # Response with available flow templates
    FLOW_CONFIGS_RESPONSE = "flow_configs_response"  # Response with flow configurations
    FLOW_INSTANCES_RESPONSE = "flow_instances_response"  # Response with flow instances
    PARALLEL_FLOWS_RESULT = "parallel_flows_result"  # Result from running multiple flows


class WebSocketMessage(BaseModel):
    type: WebSocketMessageType
    content: Any
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# Flow-related models
class FlowConfig(BaseModel):
    """Configuration for a flow execution."""
    id: str
    name: str
    constitution_id: str = "default"
    sysprompt_id: Optional[str] = "assistant_default"
    superego_enabled: bool = True
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class FlowTemplate(BaseModel):
    """Template for creating flows with predefined configurations."""
    id: str
    name: str
    description: str
    config: FlowConfig
    is_default: bool = False
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class FlowInstance(BaseModel):
    """An instance of a flow with its own conversation history."""
    id: str
    flow_config_id: str
    conversation_id: str
    name: str
    description: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    last_message_at: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ParallelFlowsRequest(BaseModel):
    """Request to run multiple flows in parallel."""
    flow_config_ids: List[str]
    user_input: str
    conversation_id: Optional[str] = None
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


class ParallelFlowResult(BaseModel):
    """Result from a single flow in a parallel execution."""
    flow_config_id: str
    flow_name: str
    superego_evaluation: Optional[SuperegoEvaluation] = None
    assistant_message: Optional[Message] = None
    constitution_id: Optional[str] = None
    sysprompt_id: Optional[str] = None
    superego_enabled: bool = True
    
    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }


# Tool-related models
class ToolInput(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolOutput(BaseModel):
    name: str
    output: Any


def init_models():
    """Initialize any models or resources needed for the application"""
    print("Initializing models and resources...")
    # This function is a hook for any initialization that needs to happen
    # when the server starts up. For now, it's just a placeholder.
    pass
