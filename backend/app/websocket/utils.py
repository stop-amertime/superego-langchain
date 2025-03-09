"""
Utility functions for WebSocket message handling.
This module contains shared functions used across different message handlers
to reduce code duplication and ensure consistent behavior.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from ..models import WebSocketMessageType
from ..errors import InvalidRequestError, MissingParameterError

# Set up logging
logger = logging.getLogger(__name__)

def create_message(
    message_type: WebSocketMessageType,
    content: Any,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized WebSocket message.
    
    Args:
        message_type: The type of message
        content: The message content
        conversation_id: Optional conversation ID
        
    Returns:
        A dictionary with the formatted message
    """
    message = {
        "type": message_type,
        "content": content,
        "timestamp": datetime.now().isoformat()
    }
    
    if conversation_id:
        message["conversation_id"] = conversation_id
        
    return message

def create_system_message(
    content: Any,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized system message.
    
    Args:
        content: The message content
        conversation_id: Optional conversation ID
        
    Returns:
        A dictionary with the formatted system message
    """
    return create_message(
        message_type=WebSocketMessageType.SYSTEM_MESSAGE,
        content=content,
        conversation_id=conversation_id
    )

def create_error_message(
    content: Any,
    conversation_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized error message.
    
    Args:
        content: The error message content
        conversation_id: Optional conversation ID
        
    Returns:
        A dictionary with the formatted error message
    """
    return create_message(
        message_type=WebSocketMessageType.ERROR,
        content=content,
        conversation_id=conversation_id
    )

def generate_id() -> str:
    """
    Generate a unique ID.
    
    Returns:
        A unique ID string
    """
    return str(uuid.uuid4())

def parse_message(data: str) -> Dict[str, Any]:
    """
    Parse a WebSocket message from JSON.
    
    Args:
        data: The JSON string to parse
        
    Returns:
        A dictionary with the parsed message
        
    Raises:
        InvalidRequestError: If the message is invalid
    """
    try:
        request_data = json.loads(data)
        logger.debug(f"Parsed message: {request_data}")
        
        # Extract the message type
        if "type" not in request_data:
            raise MissingParameterError("type")
        
        # Handle nested JSON in content (common in some client implementations)
        message_content = request_data.get("content", "")
        if isinstance(message_content, str) and message_content.startswith("{"):
            try:
                # Try to parse the content as JSON
                content_json = json.loads(message_content)
                
                # If content has a 'type' field, it might be a command message nested in content
                if isinstance(content_json, dict) and "type" in content_json:
                    nested_type = content_json.get("type")
                    logger.debug(f"Found nested message of type {nested_type} in content")
                    
                    # Use the conversation_id from the nested content if available
                    if content_json.get("conversation_id"):
                        conversation_id = content_json.get("conversation_id")
                        logger.debug(f"Using conversation_id from nested content: {conversation_id}")
                    
                    # Merge the outer message fields with the inner ones, prioritizing inner values
                    merged_data = request_data.copy()
                    merged_data.update(content_json)
                    
                    # Restore the conversation_id if it was present in the outer message
                    if request_data.get("conversation_id"):
                        merged_data["conversation_id"] = request_data.get("conversation_id")
                    
                    request_data = merged_data
                    logger.debug(f"Updated message to type {request_data.get('type')}")
            except json.JSONDecodeError:
                # Not valid JSON, continue with original message
                pass
        
        return request_data
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON received: {data}")
        raise InvalidRequestError("Invalid JSON format", {"data": data[:100] + "..." if len(data) > 100 else data})
