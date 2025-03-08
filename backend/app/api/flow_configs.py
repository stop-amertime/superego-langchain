"""API endpoints for managing flow configurations."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..flow_manager import (
    get_all_flow_configs, 
    get_flow_config, 
    create_flow_config, 
    update_flow_config, 
    delete_flow_config
)
from .utils import (
    create_success_response,
    handle_not_found,
    handle_already_exists,
    handle_bad_request,
    serialize_model,
    serialize_models
)

router = APIRouter(prefix="/api/flow-configs", tags=["flow-configs"])

# Request and response models
class FlowConfigBase(BaseModel):
    """Base model for flow configuration data."""
    name: str
    constitution_id: str = "default"
    sysprompt_id: Optional[str] = "assistant_default"
    superego_enabled: bool = True
    description: Optional[str] = None

class FlowConfigCreate(FlowConfigBase):
    """Model for creating a new flow configuration."""
    pass

class FlowConfigUpdate(BaseModel):
    """Model for updating an existing flow configuration."""
    name: Optional[str] = None
    constitution_id: Optional[str] = None
    sysprompt_id: Optional[str] = None
    superego_enabled: Optional[bool] = None
    description: Optional[str] = None

class FlowConfigResponse(FlowConfigBase):
    """Model for flow configuration response."""
    id: str
    created_at: str
    updated_at: str

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_flow_configs():
    """Get all flow configurations."""
    configs = get_all_flow_configs()
    return create_success_response(data=list(configs.values()))

@router.get("/{config_id}", response_model=Dict[str, Any])
async def get_flow_config_by_id(config_id: str):
    """Get a specific flow configuration by ID."""
    config = get_flow_config(config_id)
    if not config:
        handle_not_found("Flow configuration", config_id)
    
    return create_success_response(data=config)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_new_flow_config(config: FlowConfigCreate):
    """Create a new flow configuration."""
    # Create the flow configuration
    new_config = create_flow_config(
        name=config.name,
        constitution_id=config.constitution_id,
        sysprompt_id=config.sysprompt_id,
        superego_enabled=config.superego_enabled,
        description=config.description
    )
    
    return create_success_response(
        data=new_config,
        message=f"Flow configuration '{config.name}' created successfully"
    )

@router.put("/{config_id}", response_model=Dict[str, Any])
async def update_flow_config_by_id(config_id: str, config: FlowConfigUpdate):
    """Update an existing flow configuration."""
    # Check if flow configuration exists
    existing_config = get_flow_config(config_id)
    if not existing_config:
        handle_not_found("Flow configuration", config_id)
    
    # Update the flow configuration
    updated_config = update_flow_config(
        config_id=config_id,
        name=config.name,
        constitution_id=config.constitution_id,
        sysprompt_id=config.sysprompt_id,
        superego_enabled=config.superego_enabled,
        description=config.description
    )
    
    if not updated_config:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flow configuration"
        )
    
    return create_success_response(
        data=updated_config,
        message=f"Flow configuration '{updated_config.name}' updated successfully"
    )

@router.delete("/{config_id}", response_model=Dict[str, Any])
async def delete_flow_config_by_id(config_id: str):
    """Delete a flow configuration."""
    # Check if flow configuration exists
    existing_config = get_flow_config(config_id)
    if not existing_config:
        handle_not_found("Flow configuration", config_id)
    
    # Delete the flow configuration
    success = delete_flow_config(config_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete flow configuration that is in use by templates"
        )
    
    return create_success_response(
        message=f"Flow configuration '{existing_config.name}' deleted successfully"
    )
