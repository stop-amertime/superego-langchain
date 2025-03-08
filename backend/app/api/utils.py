"""Utility functions for the API."""
import json
from typing import Any, Dict, List, Optional, Type, TypeVar, Union
from pydantic import BaseModel
from fastapi import HTTPException, status

T = TypeVar('T', bound=BaseModel)

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create a standardized error response."""
    return {
        "status": "error",
        "code": status_code,
        "message": message
    }

def create_success_response(data: Any = None, message: Optional[str] = None) -> Dict[str, Any]:
    """Create a standardized success response."""
    response = {
        "status": "success",
    }
    
    if data is not None:
        response["data"] = data
    
    if message is not None:
        response["message"] = message
    
    return response

def handle_not_found(item_type: str, item_id: str) -> None:
    """Raise a standardized 404 error for items not found."""
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"{item_type} with ID {item_id} not found"
    )

def handle_already_exists(item_type: str, item_id: str) -> None:
    """Raise a standardized 409 error for items that already exist."""
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=f"{item_type} with ID {item_id} already exists"
    )

def handle_bad_request(message: str) -> None:
    """Raise a standardized 400 error for bad requests."""
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=message
    )

def custom_json_encoder(obj: Any) -> Any:
    """Custom JSON encoder for objects that aren't natively JSON serializable."""
    if hasattr(obj, 'dict'):
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    else:
        return str(obj)

def serialize_model(model: BaseModel) -> Dict[str, Any]:
    """Serialize a Pydantic model to a dictionary."""
    return json.loads(json.dumps(model.dict(), default=custom_json_encoder))

def serialize_models(models: List[BaseModel]) -> List[Dict[str, Any]]:
    """Serialize a list of Pydantic models to a list of dictionaries."""
    return [serialize_model(model) for model in models]
