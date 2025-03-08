"""API endpoints for managing constitutions."""
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel

from ..agents import get_all_constitutions, save_constitution
from .utils import (
    create_success_response,
    handle_not_found,
    handle_already_exists,
    handle_bad_request,
    serialize_model,
    serialize_models
)

router = APIRouter(prefix="/api/constitutions", tags=["constitutions"])

# Request and response models
class ConstitutionBase(BaseModel):
    """Base model for constitution data."""
    name: str
    content: str

class ConstitutionCreate(ConstitutionBase):
    """Model for creating a new constitution."""
    id: str

class ConstitutionUpdate(BaseModel):
    """Model for updating an existing constitution."""
    name: Optional[str] = None
    content: Optional[str] = None

class ConstitutionResponse(ConstitutionBase):
    """Model for constitution response."""
    id: str

# API endpoints
@router.get("/", response_model=Dict[str, Any])
async def get_constitutions():
    """Get all constitutions."""
    constitutions = get_all_constitutions()
    return create_success_response(data=constitutions)

@router.get("/{constitution_id}", response_model=Dict[str, Any])
async def get_constitution(constitution_id: str):
    """Get a specific constitution by ID."""
    constitutions = get_all_constitutions()
    if constitution_id not in constitutions:
        handle_not_found("Constitution", constitution_id)
    
    return create_success_response(data=constitutions[constitution_id])

@router.post("/", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_constitution(constitution: ConstitutionCreate):
    """Create a new constitution."""
    constitutions = get_all_constitutions()
    
    # Check if constitution with this ID already exists
    if constitution.id in constitutions:
        handle_already_exists("Constitution", constitution.id)
    
    # Save the constitution
    success = save_constitution(
        constitution_id=constitution.id,
        name=constitution.name,
        content=constitution.content
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save constitution"
        )
    
    # Get the saved constitution
    constitutions = get_all_constitutions()
    saved_constitution = constitutions.get(constitution.id)
    
    return create_success_response(
        data=saved_constitution,
        message=f"Constitution '{constitution.name}' created successfully"
    )

@router.put("/{constitution_id}", response_model=Dict[str, Any])
async def update_constitution(constitution_id: str, constitution: ConstitutionUpdate):
    """Update an existing constitution."""
    constitutions = get_all_constitutions()
    
    # Check if constitution exists
    if constitution_id not in constitutions:
        handle_not_found("Constitution", constitution_id)
    
    existing_constitution = constitutions[constitution_id]
    
    # Update with new values or keep existing ones
    updated_name = constitution.name if constitution.name is not None else existing_constitution["name"]
    updated_content = constitution.content if constitution.content is not None else existing_constitution["content"]
    
    # Save the updated constitution
    success = save_constitution(
        constitution_id=constitution_id,
        name=updated_name,
        content=updated_content
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update constitution"
        )
    
    # Get the updated constitution
    constitutions = get_all_constitutions()
    updated_constitution = constitutions.get(constitution_id)
    
    return create_success_response(
        data=updated_constitution,
        message=f"Constitution '{updated_name}' updated successfully"
    )

@router.delete("/{constitution_id}", response_model=Dict[str, Any])
async def delete_constitution(constitution_id: str):
    """Delete a constitution."""
    constitutions = get_all_constitutions()
    
    # Check if constitution exists
    if constitution_id not in constitutions:
        handle_not_found("Constitution", constitution_id)
    
    # Check if this is a protected constitution
    protected_ids = ["default", "none"]
    if constitution_id in protected_ids:
        handle_bad_request(f"Cannot delete protected constitution: {constitution_id}")
    
    # Get the constitution name before deleting
    constitution_name = constitutions[constitution_id]["name"]
    
    # Delete the constitution file
    import os
    from ..constitution_registry import CONSTITUTIONS_DIR
    
    file_path = os.path.join(CONSTITUTIONS_DIR, f"{constitution_id}.md")
    
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            success = True
        else:
            success = False
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting constitution file: {str(e)}"
        )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete constitution file"
        )
    
    return create_success_response(
        message=f"Constitution '{constitution_name}' deleted successfully"
    )
