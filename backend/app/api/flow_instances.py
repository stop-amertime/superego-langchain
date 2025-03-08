"""API endpoints for managing flow instances."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..flow_manager import (
    get_all_flow_instances, 
    get_flow_instance, 
    create_flow_instance, 
    update_flow_instance, 
    delete_flow_instance,
    update_flow_instance_last_message
)
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
    flow_config_id: str
    description: Optional[str] = None

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
    conversation_id: str
    created_at: str
    updated_at: str
    last_message_at: Optional[str] = None

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_flow_instances():
    """Get all flow instances."""
    instances = get_all_flow_instances()
    return create_success_response(data=list(instances.values()))

@router.get("/{instance_id}", response_model=Dict[str, Any])
async def get_flow_instance_by_id(instance_id: str):
    """Get a specific flow instance by ID."""
    instance = get_flow_instance(instance_id)
    if not instance:
        handle_not_found("Flow instance", instance_id)
    
    return create_success_response(data=instance)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_new_flow_instance(instance: FlowInstanceCreate):
    """Create a new flow instance."""
    # Create the flow instance
    new_instance = create_flow_instance(
        flow_config_id=instance.flow_config_id,
        name=instance.name,
        description=instance.description
    )
    
    return create_success_response(
        data=new_instance,
        message=f"Flow instance '{instance.name}' created successfully"
    )

@router.put("/{instance_id}", response_model=Dict[str, Any])
async def update_flow_instance_by_id(instance_id: str, instance: FlowInstanceUpdate):
    """Update an existing flow instance."""
    # Check if flow instance exists
    existing_instance = get_flow_instance(instance_id)
    if not existing_instance:
        handle_not_found("Flow instance", instance_id)
    
    # Update the flow instance
    updated_instance = update_flow_instance(
        instance_id=instance_id,
        name=instance.name,
        description=instance.description
    )
    
    if not updated_instance:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flow instance"
        )
    
    return create_success_response(
        data=updated_instance,
        message=f"Flow instance '{updated_instance.name}' updated successfully"
    )

@router.delete("/{instance_id}", response_model=Dict[str, Any])
async def delete_flow_instance_by_id(instance_id: str):
    """Delete a flow instance."""
    # Check if flow instance exists
    existing_instance = get_flow_instance(instance_id)
    if not existing_instance:
        handle_not_found("Flow instance", instance_id)
    
    # Delete the flow instance
    success = delete_flow_instance(instance_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete flow instance"
        )
    
    return create_success_response(
        message=f"Flow instance '{existing_instance.name}' deleted successfully"
    )

@router.post("/{instance_id}/update-last-message", response_model=Dict[str, Any])
async def update_instance_last_message(instance_id: str):
    """Update the last_message_at timestamp for a flow instance."""
    # Check if flow instance exists
    existing_instance = get_flow_instance(instance_id)
    if not existing_instance:
        handle_not_found("Flow instance", instance_id)
    
    # Update the last message timestamp
    success = update_flow_instance_last_message(instance_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update last message timestamp"
        )
    
    # Get the updated instance
    updated_instance = get_flow_instance(instance_id)
    
    return create_success_response(
        data=updated_instance,
        message=f"Last message timestamp updated for flow instance '{existing_instance.name}'"
    )
