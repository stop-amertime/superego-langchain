"""
REST API endpoints for conversation management.
This module provides endpoints for getting, updating, and deleting conversations.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query

from ..models import Message
from ..conversation_manager import (
    get_conversation,
    update_conversation,
    delete_conversation,
    get_all_conversations
)
from .utils import create_response

# Create router
router = APIRouter(
    prefix="/api/conversations",
    tags=["conversations"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def get_all_conversations_endpoint(
    limit: Optional[int] = Query(None, description="Limit the number of conversations returned"),
    offset: Optional[int] = Query(None, description="Offset for pagination")
):
    """
    Get all conversations with optional pagination.
    
    Args:
        limit: Optional limit for the number of conversations to return
        offset: Optional offset for pagination
        
    Returns:
        List of conversations
    """
    conversations = get_all_conversations()
    
    # Convert to list for pagination
    conversation_list = [
        {
            "id": conv_id,
            "messages": [msg.dict() for msg in messages],
            "message_count": len(messages),
            "last_updated": max([msg.timestamp for msg in messages]) if messages else None
        }
        for conv_id, messages in conversations.items()
    ]
    
    # Sort by last updated timestamp (newest first)
    conversation_list.sort(
        key=lambda x: x["last_updated"] if x["last_updated"] else "",
        reverse=True
    )
    
    # Apply pagination if specified
    if offset is not None and limit is not None:
        conversation_list = conversation_list[offset:offset + limit]
    elif offset is not None:
        conversation_list = conversation_list[offset:]
    elif limit is not None:
        conversation_list = conversation_list[:limit]
    
    return create_response(conversation_list)

@router.get("/{conversation_id}")
async def get_conversation_endpoint(
    conversation_id: str,
    limit: Optional[int] = Query(None, description="Limit the number of messages returned"),
    offset: Optional[int] = Query(None, description="Offset for pagination")
):
    """
    Get a conversation by ID with optional pagination.
    
    Args:
        conversation_id: The conversation ID
        limit: Optional limit for the number of messages to return
        offset: Optional offset for pagination
        
    Returns:
        Conversation with messages
    """
    messages = get_conversation(conversation_id)
    
    if not messages:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
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
        "id": conversation_id,
        "messages": [msg.dict() for msg in paginated_messages],
        "total_messages": len(messages)
    })

@router.post("/")
async def create_conversation_endpoint():
    """
    Create a new conversation.
    
    Returns:
        New conversation ID
    """
    conversation_id = str(uuid.uuid4())
    update_conversation(conversation_id, [])
    
    return create_response({
        "id": conversation_id,
        "messages": []
    })

@router.put("/{conversation_id}")
async def update_conversation_endpoint(conversation_id: str, messages: List[dict]):
    """
    Update a conversation with new messages.
    
    Args:
        conversation_id: The conversation ID
        messages: The updated list of messages
        
    Returns:
        Updated conversation
    """
    # Convert dict messages to Message objects
    message_objects = [Message.parse_obj(msg) for msg in messages]
    
    # Update the conversation
    update_conversation(conversation_id, message_objects)
    
    return create_response({
        "id": conversation_id,
        "messages": messages,
        "message_count": len(messages)
    })

@router.delete("/{conversation_id}")
async def delete_conversation_endpoint(conversation_id: str):
    """
    Delete a conversation.
    
    Args:
        conversation_id: The conversation ID
        
    Returns:
        Success message
    """
    success = delete_conversation(conversation_id)
    
    if not success:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
    
    return create_response({
        "message": f"Conversation {conversation_id} deleted successfully"
    })
