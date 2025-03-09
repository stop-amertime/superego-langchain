"""
Flow handler for WebSocket communication.

This module provides a handler for flow-related messages using flow_engine.py.
"""

import logging
from typing import Dict, Any

from ..message_handlers.flow_engine import handle_flow_message
from .base import MessageHandler

# Set up logging
logger = logging.getLogger(__name__)

class FlowHandler(MessageHandler):
    """Handler for flow-related messages"""
    
    async def handle(
        self, 
        client_id: str, 
        request_data: Dict[str, Any]
    ) -> None:
        """
        Handle a flow-related message
        
        Args:
            client_id: The client's unique ID
            request_data: The request data
        """
        # Get the message type
        message_type = request_data.get("payload", {}).get("type")
        
        if not message_type:
            await self.send_error(
                client_id=client_id,
                message="Invalid flow message: missing type",
                error_code="INVALID_REQUEST"
            )
            return
            
        # Create a context for the message handler
        context = {
            "client_id": client_id,
            "conversation_id": request_data.get("conversation_id"),
            "messages": [],
            "manager": None,  # Will be set by the message handler
            "request_data": request_data.get("payload", {})
        }
        
        # Get the message handler
        try:
            from ..core import manager
            context["manager"] = manager
            
            # Handle the message
            updated_context = await handle_flow_message(message_type, context)
            
            # Update the context with any changes
            context.update(updated_context)
            
        except Exception as e:
            logger.error(f"Error handling flow message: {e}")
            await self.send_error(
                client_id=client_id,
                message=f"Error handling flow message: {e}",
                flow_instance_id=request_data.get("flow_instance_id"),
                error_code="INTERNAL_ERROR"
            )
