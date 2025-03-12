"""
API Routes for Superego Agent System

FastAPI endpoints that interface with the flow execution engine.
Provides routes for executing flows and retrieving available flows.
"""

from typing import Dict, List, Any, Optional
import os
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from ..flow.loader import load_flow, load_flows_from_directory, get_constitutions_map, embed_constitutions
from .stream import stream_response


# Define API models
class FlowExecuteRequest(BaseModel):
    """Request model for flow execution"""
    flow_id: str = Field(..., description="ID of the flow to execute")
    input: str = Field(..., description="User input to process")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for context")
    metadata: Optional[Dict[str, Any]] = Field({}, description="Additional metadata")


class FlowResponse(BaseModel):
    """Response model for flow information"""
    id: str = Field(..., description="Flow ID")
    name: str = Field(..., description="Flow name")
    description: Optional[str] = Field(None, description="Flow description")


class ToolConfirmationSettings(BaseModel):
    """Settings for tool confirmation"""
    confirm_all: bool = Field(True, description="Whether to confirm all tool uses by default")
    exempted_tools: List[str] = Field(default_factory=list, description="List of tools exempted from confirmation")


class ToolConfirmationRequest(BaseModel):
    """Request model for tool execution confirmation"""
    tool_execution_id: str = Field(..., description="ID of the pending tool execution")
    confirmed: bool = Field(..., description="Whether the tool execution is confirmed")


# Create router
router = APIRouter(tags=["flows"])


# Configuration
FLOWS_DIRECTORY = os.environ.get("FLOWS_DIRECTORY", "app/data/flows")
CONSTITUTIONS_DIRECTORY = os.environ.get("CONSTITUTIONS_DIRECTORY", "app/data/constitutions")


# Dependency to get flow registry
async def get_flow_registry():
    """Get the flow registry containing all available flows"""
    # Get constitutions
    constitutions = await get_constitutions_map(CONSTITUTIONS_DIRECTORY)
    
    # Load flows
    flows = await load_flows_from_directory(FLOWS_DIRECTORY)
    
    # Create flow registry with embedded constitutions
    flow_registry = {}
    for flow in flows:
        # Generate ID from flow name if not present
        flow_id = flow.get("id", flow.get("name", "").lower().replace(" ", "-"))
        
        # Embed constitutions
        flow_with_constitutions = await embed_constitutions(flow, constitutions)
        
        # Store in registry
        flow_registry[flow_id] = flow_with_constitutions
    
    return flow_registry


@router.get("/flows", response_model=List[FlowResponse])
async def list_flows(
    flow_registry: Dict[str, Any] = Depends(get_flow_registry)
):
    """List all available flows
    
    Returns:
        List of flow information
    """
    flow_list = []
    for flow_id, flow in flow_registry.items():
        flow_list.append({
            "id": flow_id,
            "name": flow.get("name", "Unnamed Flow"),
            "description": flow.get("description")
        })
    
    return flow_list


@router.post("/flow/execute")
async def execute_flow(
    request: FlowExecuteRequest,
    flow_registry: Dict[str, Any] = Depends(get_flow_registry)
):
    """Execute a flow with the given input
    
    Args:
        request: Flow execution request
        
    Returns:
        Server-sent events stream of flow execution steps
    
    Raises:
        HTTPException: If the flow is not found
    """
    # Check if flow exists
    if request.flow_id not in flow_registry:
        raise HTTPException(status_code=404, detail=f"Flow with ID {request.flow_id} not found")
    
    # Get flow definition
    flow_def = flow_registry[request.flow_id]
    
    # Import here to avoid circular imports
    from ..flow.executor import execute_flow
    
    # Execute flow and return stream
    try:
        # Build flow executor
        from ..flow import builder
        from langchain_openai import ChatOpenAI
        
        # Get LLM (in production this would use env variables or config)
        llm = ChatOpenAI(temperature=0)
        
        # Build flow
        flow = builder.build_flow(flow_def, llm)
        
        # Execute flow and create stream response
        return stream_response(execute_flow(flow, request.input, flow_def))
    
    except Exception as e:
        # Log error and return error response
        import logging
        logging.error(f"Error executing flow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing flow: {str(e)}")


@router.get("/flow/{flow_id}")
async def get_flow(
    flow_id: str,
    flow_registry: Dict[str, Any] = Depends(get_flow_registry)
):
    """Get a specific flow by ID
    
    Args:
        flow_id: Flow ID
        
    Returns:
        Flow definition
    
    Raises:
        HTTPException: If the flow is not found
    """
    # Check if flow exists
    if flow_id not in flow_registry:
        raise HTTPException(status_code=404, detail=f"Flow with ID {flow_id} not found")
    
    # Get flow definition (without sensitive information)
    flow_def = flow_registry[flow_id]
    
    # Remove embedded constitutions for security
    sanitized_flow = flow_def.copy()
    
    # Remove any sensitive data from nodes
    if "graph" in sanitized_flow and "nodes" in sanitized_flow["graph"]:
        for node in sanitized_flow["graph"]["nodes"].values():
            # Don't return full constitution text
            if "constitution" in node and len(node["constitution"]) > 100:
                node["constitution"] = f"{node['constitution'][:100]}... [truncated]"
    
    return sanitized_flow


@router.post("/flow/{instance_id}/confirm_tool")
async def confirm_tool_execution(
    instance_id: str,
    confirmation: ToolConfirmationRequest
):
    """Confirm or deny a pending tool execution
    
    Args:
        instance_id: Flow instance ID
        confirmation: Tool confirmation request
        
    Returns:
        Confirmation result
        
    Raises:
        HTTPException: If the flow instance or tool execution is not found
    """
    # Import flow engine
    from ..flow.engine import flow_engine
    
    # Check if flow instance exists
    if instance_id not in flow_engine.active_flows:
        raise HTTPException(status_code=404, detail=f"Flow instance {instance_id} not found")
    
    # Get flow instance
    flow_instance = flow_engine.active_flows[instance_id]
    
    # Check if tool execution exists
    if confirmation.tool_execution_id not in flow_instance["pending_tool_executions"]:
        raise HTTPException(
            status_code=404, 
            detail=f"Tool execution {confirmation.tool_execution_id} not found"
        )
    
    # Get pending tool execution
    pending_execution = flow_instance["pending_tool_executions"][confirmation.tool_execution_id]
    
    # If confirmed, execute the tool and continue the flow
    if confirmation.confirmed:
        try:
            # Execute the tool using the flow engine method
            result = await flow_engine.execute_pending_tool(
                instance_id,
                confirmation.tool_execution_id
            )
            
            return {
                "status": "success",
                "result": result,
                "message": f"Tool {result['tool_name']} executed successfully"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error executing tool: {str(e)}"
            }
    else:
        # If not confirmed, remove the pending execution
        del flow_instance["pending_tool_executions"][confirmation.tool_execution_id]
        
        return {
            "status": "cancelled",
            "message": "Tool execution cancelled by user"
        }


@router.post("/flow/{instance_id}/confirmation_settings")
async def update_confirmation_settings(
    instance_id: str,
    settings: ToolConfirmationSettings
):
    """Update tool confirmation settings for a flow instance
    
    Args:
        instance_id: Flow instance ID
        settings: Tool confirmation settings
        
    Returns:
        Updated settings
        
    Raises:
        HTTPException: If the flow instance is not found
    """
    # Import flow engine
    from ..flow.engine import flow_engine
    
    # Check if flow instance exists
    if instance_id not in flow_engine.active_flows:
        raise HTTPException(status_code=404, detail=f"Flow instance {instance_id} not found")
    
    # Get flow instance
    flow_instance = flow_engine.active_flows[instance_id]
    
    # Update settings
    flow_instance["tool_confirmation_settings"] = {
        "confirm_all": settings.confirm_all,
        "exempted_tools": settings.exempted_tools
    }
    
    return {
        "status": "success",
        "message": "Tool confirmation settings updated",
        "settings": flow_instance["tool_confirmation_settings"]
    }


@router.get("/flow/{instance_id}/confirmation_settings")
async def get_confirmation_settings(
    instance_id: str
):
    """Get tool confirmation settings for a flow instance
    
    Args:
        instance_id: Flow instance ID
        
    Returns:
        Current settings
        
    Raises:
        HTTPException: If the flow instance is not found
    """
    # Import flow engine
    from ..flow.engine import flow_engine
    
    # Check if flow instance exists
    if instance_id not in flow_engine.active_flows:
        raise HTTPException(status_code=404, detail=f"Flow instance {instance_id} not found")
    
    # Get flow instance
    flow_instance = flow_engine.active_flows[instance_id]
    
    # Return settings
    return flow_instance.get("tool_confirmation_settings", {
        "confirm_all": True,
        "exempted_tools": []
    })
