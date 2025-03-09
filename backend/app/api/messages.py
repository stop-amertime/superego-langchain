"""
REST API endpoints for message store management.
This module provides endpoints for getting, updating, and deleting message stores.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from ..models import Message
from ..message_store import (
    get_messages,
    update_messages,
    delete_message_store,
    get_all_message_stores
)
from .utils import create_response

# Create router
router = APIRouter(
    prefix="/api/messages",
    tags=["messages"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_all_messages_endpoint(
    limit: Optional[int] = Query(None, description="Limit the number of message stores returned"),
    offset: Optional[int] = Query(None, description="Offset for pagination")
):
    """
    Get all message stores with optional pagination.
    
    Args:
        limit: Optional limit for the number of message stores to return
        offset: Optional offset for pagination
        
    Returns:
        List of message stores
    """
    message_stores = get_all_message_stores()
    
    # Convert to list for pagination
    message_store_list = [
        {
            "id": store_id,
            "messages": [msg.dict() for msg in messages],
            "message_count": len(messages),
            "last_updated": max([msg.timestamp for msg in messages]) if messages else None
        }
        for store_id, messages in message_stores.items()
    ]
    
    # Sort by last updated timestamp (newest first)
    message_store_list.sort(
        key=lambda x: x["last_updated"] if x["last_updated"] else "",
        reverse=True
    )
    
    # Apply pagination if specified
    if offset is not None and limit is not None:
        message_store_list = message_store_list[offset:offset + limit]
    elif offset is not None:
        message_store_list = message_store_list[offset:]
    elif limit is not None:
        message_store_list = message_store_list[:limit]
    
    return create_response(message_store_list)

@router.get("/{message_store_id}")
async def get_messages_endpoint(
    message_store_id: str,
    limit: Optional[int] = Query(None, description="Limit the number of messages returned"),
    offset: Optional[int] = Query(None, description="Offset for pagination")
):
    """
    Get messages by message store ID with optional pagination.
    
    Args:
        message_store_id: The message store ID
        limit: Optional limit for the number of messages to return
        offset: Optional offset for pagination
        
    Returns:
        Message store with messages
    """
    messages = get_messages(message_store_id)
    
    if not messages:
        raise HTTPException(status_code=404, detail=f"Message store {message_store_id} not found")
    
    # Apply pagination if specified
    if offset is not None and limit is not None:
        paginated_messages = messages[offset:offset + limit]
    elif offset is not None:
        paginated_messages = messages[offset:]
    elif limit is not None:
        paginated_messages = messages[:limit]
    else:
        paginated_messages = messages
    
    return create_response({
        "id": message_store_id,
        "messages": [msg.dict() for msg in paginated_messages],
        "total_messages": len(messages)
    })

@router.post("/")
async def create_message_store_endpoint():
    """
    Create a new message store.
    
    Returns:
        New message store ID
    """
    message_store_id = str(uuid.uuid4())
    update_messages(message_store_id, [])
    
    return create_response({
        "id": message_store_id,
        "messages": []
    })

@router.put("/{message_store_id}")
async def update_messages_endpoint(message_store_id: str, messages: List[dict]):
    """
    Update a message store with new messages.
    
    Args:
        message_store_id: The message store ID
        messages: The updated list of messages
        
    Returns:
        Updated message store
    """
    # Convert dict messages to Message objects
    message_objects = [Message.parse_obj(msg) for msg in messages]
    
    # Update the message store
    update_messages(message_store_id, message_objects)
    
    return create_response({
        "id": message_store_id,
        "messages": messages,
        "message_count": len(messages)
    })

@router.delete("/{message_store_id}")
async def delete_message_store_endpoint(message_store_id: str):
    """
    Delete a message store.
    
    Args:
        message_store_id: The message store ID
        
    Returns:
        Success message
    """
    success = delete_message_store(message_store_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Message store {message_store_id} not found")
    
    return create_response({
        "message": f"Message store {message_store_id} deleted successfully"
    })
