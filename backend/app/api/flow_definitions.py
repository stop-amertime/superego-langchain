"""API endpoints for managing flow definitions."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..flow_engine import get_flow_engine
from ..models import NodeConfig, EdgeConfig
from .utils import (
    create_success_response,
    handle_not_found,
    handle_already_exists,
    handle_bad_request,
    serialize_model,
    serialize_models
)

router = APIRouter(prefix="/api/flow-definitions", tags=["flow-definitions"])

# Request and response models
class FlowDefinitionBase(BaseModel):
    """Base model for flow definition data."""
    name: str
    description: Optional[str] = None
    nodes: Dict[str, NodeConfig]
    edges: List[EdgeConfig]

class FlowDefinitionCreate(FlowDefinitionBase):
    """Model for creating a new flow definition."""
    pass

class FlowDefinitionUpdate(BaseModel):
    """Model for updating an existing flow definition."""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[Dict[str, NodeConfig]] = None
    edges: Optional[List[EdgeConfig]] = None

class FlowDefinitionResponse(FlowDefinitionBase):
    """Model for flow definition response."""
    id: str
    created_at: str
    updated_at: str

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_flow_definitions():
    """Get all flow definitions."""
    flow_engine = get_flow_engine()
    definitions = flow_engine.flow_definitions
    return create_success_response(data=list(definitions.values()))

@router.get("/{definition_id}", response_model=Dict[str, Any])
async def get_flow_definition_by_id(definition_id: str):
    """Get a specific flow definition by ID."""
    flow_engine = get_flow_engine()
    definition = flow_engine.get_flow_definition(definition_id)
    if not definition:
        handle_not_found("Flow definition", definition_id)
    
    return create_success_response(data=definition)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_new_flow_definition(definition: FlowDefinitionCreate):
    """Create a new flow definition."""
    flow_engine = get_flow_engine()
    
    # Convert pydantic model to dictionary
    definition_dict = definition.dict()
    
    # Import the FlowDefinition model from models
    from ..models import FlowDefinition
    
    # Create a FlowDefinition object
    flow_definition = FlowDefinition(**definition_dict)
    
    # Create the flow definition
    new_definition = flow_engine.create_flow_definition(flow_definition)
    
    return create_success_response(
        data=new_definition,
        message=f"Flow definition '{definition.name}' created successfully"
    )

@router.put("/{definition_id}", response_model=Dict[str, Any])
async def update_flow_definition_by_id(definition_id: str, definition: FlowDefinitionUpdate):
    """Update an existing flow definition."""
    flow_engine = get_flow_engine()
    
    # Check if flow definition exists
    existing_definition = flow_engine.get_flow_definition(definition_id)
    if not existing_definition:
        handle_not_found("Flow definition", definition_id)
    
    # Update the definition properties if provided
    if definition.name is not None:
        existing_definition.name = definition.name
    if definition.description is not None:
        existing_definition.description = definition.description
    if definition.nodes is not None:
        existing_definition.nodes = definition.nodes
    if definition.edges is not None:
        existing_definition.edges = definition.edges
    
    # Save the updated definition
    flow_engine.save_flow_definition(existing_definition)
    
    # Get the updated definition
    updated_definition = flow_engine.get_flow_definition(definition_id)
    
    return create_success_response(
        data=updated_definition,
        message=f"Flow definition '{updated_definition.name}' updated successfully"
    )

@router.delete("/{definition_id}", response_model=Dict[str, Any])
async def delete_flow_definition_by_id(definition_id: str):
    """Delete a flow definition."""
    # This endpoint is intentionally not implemented 
    # as it's not clear from flow_engine.py how to delete a flow definition
    # and it might be dangerous to delete definitions that instances depend on
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Deleting flow definitions is not supported"
    )

@router.post("/default", response_model=Dict[str, Any])
async def create_default_flow_definition():
    """Create a default flow definition."""
    flow_engine = get_flow_engine()
    
    # Create the default flow definition
    new_definition = flow_engine.create_default_flow_definition()
    
    return create_success_response(
        data=new_definition,
        message="Default flow definition created successfully"
    )
