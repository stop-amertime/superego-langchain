"""API endpoints for managing flow templates."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..models import FlowConfig
from ..flow_manager import (
    get_all_flow_templates, 
    get_flow_template, 
    create_flow_template, 
    update_flow_template, 
    delete_flow_template,
    create_flow_config
)
from .utils import (
    create_success_response,
    handle_not_found,
    handle_already_exists,
    handle_bad_request,
    serialize_model,
    serialize_models
)

router = APIRouter(prefix="/api/flow-templates", tags=["flow-templates"])

# Request and response models
class FlowConfigData(BaseModel):
    """Model for flow configuration data within a template."""
    name: str
    constitution_id: str = "default"
    sysprompt_id: Optional[str] = "assistant_default"
    superego_enabled: bool = True
    description: Optional[str] = None

class FlowTemplateBase(BaseModel):
    """Base model for flow template data."""
    name: str
    description: str
    config: FlowConfigData
    is_default: bool = False

class FlowTemplateCreate(FlowTemplateBase):
    """Model for creating a new flow template."""
    pass

class FlowTemplateUpdate(BaseModel):
    """Model for updating an existing flow template."""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[FlowConfigData] = None
    is_default: Optional[bool] = None

class FlowTemplateResponse(FlowTemplateBase):
    """Model for flow template response."""
    id: str
    created_at: str
    updated_at: str

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_flow_templates():
    """Get all flow templates."""
    templates = get_all_flow_templates()
    return create_success_response(data=list(templates.values()))

@router.get("/{template_id}", response_model=Dict[str, Any])
async def get_flow_template_by_id(template_id: str):
    """Get a specific flow template by ID."""
    template = get_flow_template(template_id)
    if not template:
        handle_not_found("Flow template", template_id)
    
    return create_success_response(data=template)

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_new_flow_template(template: FlowTemplateCreate):
    """Create a new flow template."""
    # Create a new flow config for this template
    config = FlowConfig(
        id="",  # Will be generated in create_flow_config
        name=template.config.name,
        constitution_id=template.config.constitution_id,
        sysprompt_id=template.config.sysprompt_id,
        superego_enabled=template.config.superego_enabled,
        description=template.config.description
    )
    
    # Create the flow template
    new_template = create_flow_template(
        name=template.name,
        description=template.description,
        config=config,
        is_default=template.is_default
    )
    
    return create_success_response(
        data=new_template,
        message=f"Flow template '{template.name}' created successfully"
    )

@router.put("/{template_id}", response_model=Dict[str, Any])
async def update_flow_template_by_id(template_id: str, template: FlowTemplateUpdate):
    """Update an existing flow template."""
    # Check if flow template exists
    existing_template = get_flow_template(template_id)
    if not existing_template:
        handle_not_found("Flow template", template_id)
    
    # Prepare config update if provided
    config = None
    if template.config:
        config = FlowConfig(
            id=existing_template.config.id,
            name=template.config.name,
            constitution_id=template.config.constitution_id,
            sysprompt_id=template.config.sysprompt_id,
            superego_enabled=template.config.superego_enabled,
            description=template.config.description
        )
    
    # Update the flow template
    updated_template = update_flow_template(
        template_id=template_id,
        name=template.name,
        description=template.description,
        config=config,
        is_default=template.is_default
    )
    
    if not updated_template:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update flow template"
        )
    
    return create_success_response(
        data=updated_template,
        message=f"Flow template '{updated_template.name}' updated successfully"
    )

@router.delete("/{template_id}", response_model=Dict[str, Any])
async def delete_flow_template_by_id(template_id: str):
    """Delete a flow template."""
    # Check if flow template exists
    existing_template = get_flow_template(template_id)
    if not existing_template:
        handle_not_found("Flow template", template_id)
    
    # Delete the flow template
    success = delete_flow_template(template_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete flow template"
        )
    
    return create_success_response(
        message=f"Flow template '{existing_template.name}' deleted successfully"
    )
