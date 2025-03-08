"""API endpoints for managing system prompts."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..llm_client import get_all_sysprompts, save_sysprompt
from .utils import (
    create_success_response,
    handle_not_found,
    handle_already_exists,
    handle_bad_request,
    serialize_model,
    serialize_models
)

router = APIRouter(prefix="/api/sysprompts", tags=["sysprompts"])

# Request and response models
class SyspromptBase(BaseModel):
    """Base model for system prompt data."""
    name: str
    content: str

class SyspromptCreate(SyspromptBase):
    """Model for creating a new system prompt."""
    id: str

class SyspromptUpdate(BaseModel):
    """Model for updating an existing system prompt."""
    name: Optional[str] = None
    content: Optional[str] = None

class SyspromptResponse(SyspromptBase):
    """Model for system prompt response."""
    id: str

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_sysprompts():
    """Get all system prompts."""
    sysprompts = get_all_sysprompts()
    return create_success_response(data=list(sysprompts.values()))

@router.get("/{sysprompt_id}", response_model=Dict[str, Any])
async def get_sysprompt(sysprompt_id: str):
    """Get a specific system prompt by ID."""
    sysprompts = get_all_sysprompts()
    if sysprompt_id not in sysprompts:
        handle_not_found("System prompt", sysprompt_id)
    
    return create_success_response(data=sysprompts[sysprompt_id])

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_sysprompt(sysprompt: SyspromptCreate):
    """Create a new system prompt."""
    sysprompts = get_all_sysprompts()
    
    # Check if system prompt with this ID already exists
    if sysprompt.id in sysprompts:
        handle_already_exists("System prompt", sysprompt.id)
    
    # Save the system prompt
    success = save_sysprompt(
        sysprompt_id=sysprompt.id,
        name=sysprompt.name,
        content=sysprompt.content
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save system prompt"
        )
    
    # Get the saved system prompt
    sysprompts = get_all_sysprompts()
    saved_sysprompt = sysprompts.get(sysprompt.id)
    
    return create_success_response(
        data=saved_sysprompt,
        message=f"System prompt '{sysprompt.name}' created successfully"
    )

@router.put("/{sysprompt_id}", response_model=Dict[str, Any])
async def update_sysprompt(sysprompt_id: str, sysprompt: SyspromptUpdate):
    """Update an existing system prompt."""
    sysprompts = get_all_sysprompts()
    
    # Check if system prompt exists
    if sysprompt_id not in sysprompts:
        handle_not_found("System prompt", sysprompt_id)
    
    existing_sysprompt = sysprompts[sysprompt_id]
    
    # Update with new values or keep existing ones
    updated_name = sysprompt.name if sysprompt.name is not None else existing_sysprompt["name"]
    updated_content = sysprompt.content if sysprompt.content is not None else existing_sysprompt["content"]
    
    # Save the updated system prompt
    success = save_sysprompt(
        sysprompt_id=sysprompt_id,
        name=updated_name,
        content=updated_content
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update system prompt"
        )
    
    # Get the updated system prompt
    sysprompts = get_all_sysprompts()
    updated_sysprompt = sysprompts.get(sysprompt_id)
    
    return create_success_response(
        data=updated_sysprompt,
        message=f"System prompt '{updated_name}' updated successfully"
    )

@router.delete("/{sysprompt_id}", response_model=Dict[str, Any])
async def delete_sysprompt(sysprompt_id: str):
    """Delete a system prompt."""
    sysprompts = get_all_sysprompts()
    
    # Check if system prompt exists
    if sysprompt_id not in sysprompts:
        handle_not_found("System prompt", sysprompt_id)
    
    # Check if this is a protected system prompt
    protected_ids = ["assistant_default"]
    if sysprompt_id in protected_ids:
        handle_bad_request(f"Cannot delete protected system prompt: {sysprompt_id}")
    
    # Get the system prompt name before deleting
    sysprompt_name = sysprompts[sysprompt_id]["name"]
    
    # Delete the system prompt file
    import os
    import json
    from ..llm_client import SYSPROMPTS_FILE
    
    try:
        # Load the current sysprompts
        with open(SYSPROMPTS_FILE, 'r') as f:
            data = json.load(f)
        
        # Remove the sysprompt
        if sysprompt_id in data:
            del data[sysprompt_id]
            
            # Save the updated sysprompts
            with open(SYSPROMPTS_FILE, 'w') as f:
                json.dump(data, f, indent=2)
            
            success = True
        else:
            success = False
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting system prompt: {str(e)}"
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete system prompt"
        )
    
    return create_success_response(
        message=f"System prompt '{sysprompt_name}' deleted successfully"
    )
