"""
Handler for constitution related WebSocket messages.
This module handles getting, creating, updating, and deleting constitutions.
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime

from ...models import WebSocketMessageType
from ...agents import get_all_constitutions, save_constitution
from ...errors import (
    MissingParameterError, NotFoundError, ProtectedConstitutionError,
    ConstitutionError, format_websocket_error
)
from ..utils import create_message, create_system_message

# Set up logging
logger = logging.getLogger(__name__)

async def handle_constitution_message(message_type: str, context: Dict[str, Any]) -> None:
    """
    Handle constitution-related messages
    
    Args:
        message_type: The message type
        context: The conversation context
    """
    client_id = context["client_id"]
    manager = context["manager"]
    request_data = context["request_data"]
    
    if message_type == "get_constitutions":
        # Return available constitutions
        constitutions = get_all_constitutions()
        await manager.send_message(
            create_message(
                WebSocketMessageType.CONSTITUTIONS_RESPONSE,
                list(constitutions.values()),
                None
            ),
            client_id
        )
    
    elif message_type in ["save_constitution", "create_constitution"]:
        # Save a new constitution
        required_fields = ["id", "name", "content"]
        for field in required_fields:
            if field not in request_data:
                raise MissingParameterError(field)
        
        constitution_id = request_data.get("id")
        name = request_data.get("name")
        content = request_data.get("content")
        
        success = save_constitution(constitution_id, name, content)
        
        # Get the saved constitution to return to the client
        saved_constitution = None
        if success:
            constitutions = get_all_constitutions()
            saved_constitution = constitutions.get(constitution_id)
        else:
            # If save failed, raise an error
            raise ConstitutionError(f"Failed to save constitution: {name}")
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Constitution saved: {name}",
                    "constitution": saved_constitution
                },
                None
            ),
            client_id
        )
    
    elif message_type == "update_constitution":
        # Update an existing constitution
        if "id" not in request_data:
            raise MissingParameterError("id")
        
        constitution_id = request_data.get("id")
        name = request_data.get("name")
        content = request_data.get("content")
        
        # Get the existing constitution
        constitutions = get_all_constitutions()
        existing_constitution = constitutions.get(constitution_id)
        
        if not existing_constitution:
            raise NotFoundError("Constitution", constitution_id)
        
        # Update with new values or keep existing ones
        updated_name = name if name is not None else existing_constitution["name"]
        updated_content = content if content is not None else existing_constitution["content"]
        
        success = save_constitution(constitution_id, updated_name, updated_content)
        
        # Get the updated constitution to return to the client
        updated_constitution = None
        if success:
            constitutions = get_all_constitutions()
            updated_constitution = constitutions.get(constitution_id)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": success,
                    "message": f"Constitution {'updated' if success else 'failed to update'}: {updated_name}",
                    "constitution": updated_constitution
                },
                None
            ),
            client_id
        )
    
    elif message_type == "delete_constitution":
        # Delete a constitution
        if "id" not in request_data:
            raise MissingParameterError("id")
        
        constitution_id = request_data.get("id")
        
        # Check if this is a protected constitution
        protected_ids = ["default", "none"]
        if constitution_id in protected_ids:
            raise ProtectedConstitutionError(constitution_id)
        
        # Get the constitution name before deleting
        constitutions = get_all_constitutions()
        constitution = constitutions.get(constitution_id)
        
        if not constitution:
            raise NotFoundError("Constitution", constitution_id)
        
        constitution_name = constitution["name"]
        
        # Delete the constitution file
        from ...constitution_registry import CONSTITUTIONS_DIR
        
        file_path = os.path.join(CONSTITUTIONS_DIR, f"{constitution_id}.md")
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                success = True
            else:
                success = False
        except Exception as e:
            logger.error(f"Error deleting constitution file: {str(e)}")
            success = False
        
        await manager.send_message(
            create_system_message(
                {
                    "success": success,
                    "message": f"Constitution {'deleted' if success else 'failed to delete'}: {constitution_name}"
                },
                None
            ),
            client_id
        )
