"""
Handler for system related WebSocket messages.
This module handles getting and saving system prompts.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ...models import WebSocketMessageType
from ...llm_client import get_all_sysprompts, save_sysprompt
from ...errors import MissingParameterError, InvalidRequestError
from ..utils import create_message, create_system_message

# Set up logging
logger = logging.getLogger(__name__)

async def handle_system_message(message_type: str, context: Dict[str, Any]) -> None:
    """
    Handle system-related messages
    
    Args:
        message_type: The message type
        context: The conversation context
    """
    client_id = context["client_id"]
    manager = context["manager"]
    request_data = context["request_data"]
    
    if message_type in ["get_system_prompts", "get_sysprompts"]:
        # Return available system prompts
        sysprompts = get_all_sysprompts()
        
        if message_type == "get_sysprompts":
            # Return in format for dropdown
            await manager.send_message(
                create_message(
                    WebSocketMessageType.SYSPROMPTS_RESPONSE,
                    list(sysprompts.values()),
                    None
                ),
                client_id
            )
        else:
            # Backward compatibility format
            await manager.send_message(
                create_system_message(
                    {
                        "sysprompts": list(sysprompts.values())
                    },
                    None
                ),
                client_id
            )
    
    elif message_type == "save_system_prompt":
        # Save a new system prompt
        required_fields = ["id", "name", "content"]
        for field in required_fields:
            if field not in request_data:
                raise MissingParameterError(field)
        
        sysprompt_id = request_data.get("id")
        name = request_data.get("name")
        content = request_data.get("content")
        
        success = save_sysprompt(sysprompt_id, name, content)
        
        if not success:
            raise InvalidRequestError(f"Failed to save system prompt: {name}")
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"System prompt saved: {name}"
                },
                None
            ),
            client_id
        )
