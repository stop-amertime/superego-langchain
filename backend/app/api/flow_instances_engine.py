"""API endpoints for managing flow instances using flow_engine."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..flow_engine import get_flow_engine
from .utils import (
    create_success_response,
    handle_not_found,
    handle_already_exists,
    handle_bad_request,
    serialize_model,
    serialize_models
)

router = APIRouter(prefix="/api/flow-instances", tags=["flow-instances"])

# Request and response models
class FlowInstanceBase(BaseModel):
    """Base model for flow instance data."""
    name: str
    flow_definition_id: str
    description: Optional[str] = None
    parameters: Optional[Dict[str, Dict[str, Any]]] = None

class FlowInstanceCreate(FlowInstanceBase):
    """Model for creating a new flow instance."""
    pass

class FlowInstanceUpdate(BaseModel):
    """Model for updating an existing flow instance."""
    name: Optional[str] = None
    description: Optional[str] = None

class FlowInstanceResponse(FlowInstanceBase):
    """Model for flow instance response."""
    id: str
    created_at: str
    updated_at: str
    last_message_at: Optional[str] = None
    status: str
    current_node: Optional[str] = None

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_flow_instances():
    """Get all flow instances."""
    flow_engine = get_flow_engine()
    instances = flow_engine.flow_instances
    return create_success_response(data=list(instances.values()))

@router.get("/{instance_id}", response_model=Dict[str, Any])
async def get_flow_instance_by_id(instance_id: str):
    """Get a specific flow instance by ID."""
    flow_engine = get_flow_engine()
    instance = flow_engine.get_flow_instance(instance_id)
    if not instance:
        handle_not_found("Flow instance", instance_id)
    
    return create_success_response(data=instance)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_new_flow_instance(instance: FlowInstanceCreate):
    """Create a new flow instance."""
    flow_engine = get_flow_engine()
    
    # Create the flow instance
    new_instance = flow_engine.create_flow_instance(
        definition_id=instance.flow_definition_id,
        name=instance.name,
        description=instance.description,
        parameters=instance.parameters
    )
    
    if not new_instance:
        handle_not_found("Flow definition", instance.flow_definition_id)
    
    return create_success_response(
        data=new_instance,
        message=f"Flow instance '{instance.name}' created successfully"
    )

@router.put("/{instance_id}", response_model=Dict[str, Any])
async def update_flow_instance_by_id(instance_id: str, instance: FlowInstanceUpdate):
    """Update an existing flow instance."""
    flow_engine = get_flow_engine()
    
    # Check if flow instance exists
    existing_instance = flow_engine.get_flow_instance(instance_id)
    if not existing_instance:
        handle_not_found("Flow instance", instance_id)
    
    # Update the name and description if provided
    if instance.name is not None:
        existing_instance.name = instance.name
    if instance.description is not None:
        existing_instance.description = instance.description
    
    # Update the instance
    flow_engine.update_flow_instance(existing_instance)
    
    # Get the updated instance
    updated_instance = flow_engine.get_flow_instance(instance_id)
    
    return create_success_response(
        data=updated_instance,
        message=f"Flow instance '{updated_instance.name}' updated successfully"
    )

@router.delete("/{instance_id}", response_model=Dict[str, Any])
async def delete_flow_instance_by_id(instance_id: str):
    """Delete a flow instance."""
    flow_engine = get_flow_engine()
    
    # Check if flow instance exists
    existing_instance = flow_engine.get_flow_instance(instance_id)
    if not existing_instance:
        handle_not_found("Flow instance", instance_id)
    
    # Store the name for the response message
    instance_name = existing_instance.name
    
    # Delete the flow instance
    success = flow_engine.delete_flow_instance(instance_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete flow instance"
        )
    
    return create_success_response(
        message=f"Flow instance '{instance_name}' deleted successfully"
    )
