"""
API Routes for Superego Agent System

FastAPI endpoints that interface with the flow execution engine.
Provides routes for executing flows and retrieving available flows.
"""

from typing import Dict, List, Any, Optional
import os
import json
from pathlib import Path
from datetime import datetime

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
    instance_id: str = Field(..., description="Required flow instance ID")
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
FLOWS_DIRECTORY = os.environ.get("FLOWS_DIRECTORY", "app/data/flow_definitions")
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
    """Execute a flow with the given input (POST method)
    
    Args:
        request: Flow execution request
        
    Returns:
        Server-sent events stream of flow execution steps
    
    Raises:
        HTTPException: If the flow is not found or instance ID is missing
    """
    return await _execute_flow(
        request.flow_id, 
        request.input, 
        request.instance_id,  # Use the required instance_id 
        request.metadata, 
        flow_registry
    )


@router.get("/flow/execute")
async def execute_flow_get(
    flow_id: str,
    input: str,
    instance_id: str,  # Now required, not optional
    metadata: Optional[str] = None,
    flow_registry: Dict[str, Any] = Depends(get_flow_registry)
):
    """Execute a flow with the given input (GET method for EventSource)
    
    Args:
        flow_id: ID of the flow to execute
        input: User input to process
        instance_id: Required flow instance ID
        metadata: Optional JSON-encoded metadata
        
    Returns:
        Server-sent events stream of flow execution steps
    
    Raises:
        HTTPException: If the flow is not found or instance ID is missing
    """
    # Parse metadata if provided
    parsed_metadata = {}
    if metadata:
        try:
            parsed_metadata = json.loads(metadata)
        except:
            pass
    
    return await _execute_flow(
        flow_id, 
        input, 
        instance_id,  # Pass instance_id directly
        parsed_metadata, 
        flow_registry
    )


async def _execute_flow(
    flow_id: str,
    input: str,
    instance_id: str,  # Now a required parameter
    metadata: Optional[Dict[str, Any]],
    flow_registry: Dict[str, Any]
):
    """Execute a flow with the given input
    
    Args:
        flow_id: ID of the flow to execute
        input: User input to process
        instance_id: Required flow instance ID
        metadata: Optional metadata
        flow_registry: Registry of available flows
        
    Returns:
        Server-sent events stream of flow execution steps
    
    Raises:
        HTTPException: If the flow is not found or instance doesn't exist
    """
    # Import flow engine
    from ..flow.engine import flow_engine
    import logging
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.DEBUG)
    
    # Check if flow exists
    if flow_id not in flow_registry:
        raise HTTPException(status_code=404, detail=f"Flow with ID {flow_id} not found")
    
    # Fail fast if instance_id is not provided
    if not instance_id:
        raise HTTPException(
            status_code=400, 
            detail="Missing required parameter: instance_id must be provided for flow execution"
        )
    
    # Check if instance exists in the flow engine
    if instance_id not in flow_engine.active_flows:
        raise HTTPException(
            status_code=404, 
            detail=f"Flow instance {instance_id} not found. Please create an instance first."
        )
    
    # Get flow definition and add instance_id
    flow_def = flow_registry[flow_id].copy()  # Make a copy to avoid modifying the registry
    
    # Always include instance_id in the flow_def
    flow_def['instance_id'] = instance_id
    logger.debug(f"Using flow instance ID: {instance_id}")
    
    # Import here to avoid circular imports
    from ..flow.executor import execute_flow
    
    # Execute flow and return stream
    try:
        # Build flow executor
        from ..flow import builder
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        
        # Load from .env file
        load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"))
        
        # Get OpenRouter API key and model from .env
        api_key = os.environ.get("OPENROUTER_API_KEY")
        base_model = os.environ.get("BASE_MODEL", "anthropic/claude-3.5-sonnet")
        
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")
            
        # Configure for OpenRouter
        llm = ChatOpenAI(
            temperature=0,
            model=base_model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        # Build flow
        flow = await builder.build_flow(flow_def, llm)
        
        # Execute flow and create stream response
        return await stream_response(execute_flow(flow, input, flow_def))
    
    except Exception as e:
        # Log error and return error response
        import logging
        logging.error(f"Error executing flow: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error executing flow: {str(e)}")


@router.get("/flow/instances")
async def list_flow_instances():
    """List all active flow instances
    
    Returns:
        List of flow instance information
    """
    # Import flow engine
    from ..flow.engine import flow_engine
    
    # Get all active flow instances
    instances = []
    for instance_id, instance_data in flow_engine.active_flows.items():
        # Get flow definition information
        flow_def = instance_data.get("definition", {})
        
        # Get history to determine creation time and last activity
        history = instance_data.get("history", [])
        created_at = history[0]["timestamp"] if history else None
        last_activity = history[-1]["timestamp"] if history else None
        
        # Add instance info to list
        instances.append({
            "id": instance_id,
            "flow_id": flow_def.get("id", "unknown"),
            "flow_name": flow_def.get("name", "Unnamed Flow"),
            "created_at": created_at,
            "last_activity": last_activity,
            "step_count": len(history)
        })
    
    return instances


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


@router.post("/flow/create_instance")
async def create_flow_instance(
    request: Request
):
    """Create a new flow instance
    
    Args:
        request: Request body containing flow_id and optional instance_id
        
    Returns:
        Created flow instance information
    """
    import logging
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.DEBUG)
    
    try:
        logger.debug("Starting create_flow_instance")
        
        # Parse request body
        body = await request.json()
        flow_id = body.get("flow_id")
        instance_id = body.get("instance_id", f"flow-{int(datetime.now().timestamp())}")
        
        logger.debug(f"Request parameters: flow_id={flow_id}, instance_id={instance_id}")
        
        # Import flow engine
        from ..flow.engine import flow_engine
        logger.debug(f"Flow registry has {len(flow_engine.flow_definitions)} definitions")
        
        # Validate flow ID
        if flow_id not in flow_engine.flow_definitions:
            logger.error(f"Flow definition {flow_id} not found in registry")
            available_flows = list(flow_engine.flow_definitions.keys())
            logger.debug(f"Available flows: {available_flows}")
            raise HTTPException(
                status_code=404, 
                detail=f"Flow definition {flow_id} not found. Available: {available_flows}"
            )
        
        # Get flow definition
        flow_def = flow_engine.flow_definitions[flow_id]
        logger.debug(f"Found flow definition: {flow_def.get('name', 'Unnamed Flow')}")
        
        # Create LLM
        logger.debug("Creating ChatOpenAI instance")
        from langchain_openai import ChatOpenAI
        from dotenv import load_dotenv
        
        # Load from .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
        logger.debug(f"Loading .env from {env_path}")
        load_dotenv(dotenv_path=env_path)
        
        # Get OpenRouter API key and model from .env
        api_key = os.environ.get("OPENROUTER_API_KEY")
        base_model = os.environ.get("BASE_MODEL", "anthropic/claude-3.5-sonnet")
        
        logger.debug(f"Using model: {base_model}")
        if not api_key:
            logger.error("OPENROUTER_API_KEY not found in environment")
            raise HTTPException(
                status_code=500, 
                detail="OpenRouter API key not configured"
            )
        
        logger.debug("Creating ChatOpenAI instance")
        # Configure for OpenRouter
        llm = ChatOpenAI(
            temperature=0,
            model=base_model,
            openai_api_key=api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        logger.debug("ChatOpenAI instance created successfully")
        
        # Create flow graph
        logger.debug("Building flow graph")
        from ..flow.builder import build_flow
        try:
            flow_graph = await build_flow(flow_def, llm)
            logger.debug("Flow graph built successfully")
        except Exception as e:
            logger.error(f"Error building flow graph: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500,
                detail=f"Error building flow graph: {str(e)}"
            )
        
        # Setup instance
        logger.debug(f"Setting up flow instance {instance_id}")
        flow_engine.active_flows[instance_id] = {
            "graph": flow_graph,
            "definition": flow_def,
            "history": [],
            "tool_confirmation_settings": {"confirm_all": True, "exempted_tools": []},
            "pending_tool_executions": {},
            "created_at": datetime.now().isoformat()
        }
        
        # Save the instance
        logger.debug("Saving flow instance")
        try:
            # Check if directory exists and create if needed
            from pathlib import Path
            instances_dir = Path("app/data/flow_instances")
            instances_dir.mkdir(exist_ok=True, parents=True)
            logger.debug(f"Flow instances directory: {instances_dir}")
            
            flow_engine.save_flow_instance(instance_id)
            logger.debug("Flow instance saved successfully")
        except Exception as e:
            logger.error(f"Error saving flow instance: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            # Clean up if saving fails
            if instance_id in flow_engine.active_flows:
                del flow_engine.active_flows[instance_id]
            raise HTTPException(
                status_code=500,
                detail=f"Error saving flow instance: {str(e)}"
            )
        
        # Return instance details
        logger.debug("Returning instance details")
        return {
            "id": instance_id,
            "flow_id": flow_id,
            "flow_name": flow_def.get("name", "Unnamed Flow"),
            "created_at": flow_engine.active_flows[instance_id]["created_at"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in create_flow_instance: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/flow/instance/{instance_id}")
async def get_flow_instance_history(
    instance_id: str
):
    """Get the history of a specific flow instance
    
    Args:
        instance_id: Flow instance ID
        
    Returns:
        Flow instance history steps
        
    Raises:
        HTTPException: If the flow instance is not found
    """
    import logging
    import traceback
    
    logger = logging.getLogger("uvicorn")
    logger.setLevel(logging.DEBUG)
    
    logger.debug(f"Starting get_flow_instance_history for instance_id: {instance_id}")
    
    try:
        # Import flow engine
        from ..flow.engine import flow_engine
        logger.debug("Imported flow_engine")
        
        # Check if flow instance exists
        logger.debug(f"Checking if {instance_id} exists in active_flows")
        if instance_id not in flow_engine.active_flows:
            logger.debug(f"Instance {instance_id} not found in active_flows")
            raise HTTPException(status_code=404, detail=f"Flow instance {instance_id} not found")
        
        # Return flow history
        logger.debug("Fetching flow history")
        try:
            history = flow_engine.get_flow_history(instance_id)
            logger.debug("Flow history fetched successfully")
            return history
        except Exception as history_error:
            logger.error(f"Error fetching flow history: {str(history_error)}")
            logger.error(traceback.format_exc())
            raise HTTPException(
                status_code=500, 
                detail=f"Error fetching flow history: {str(history_error)}"
            )
    except HTTPException:
        # Re-raise HTTPExceptions as is
        raise
    except Exception as unexpected_error:
        # Catch any other unexpected errors
        logger.error(f"Unexpected error in get_flow_instance_history: {str(unexpected_error)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(unexpected_error)}"
        )
