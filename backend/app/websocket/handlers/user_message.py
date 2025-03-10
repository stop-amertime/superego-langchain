"""
User message handler for WebSocket communication.

This module provides a handler for user messages.
"""

import logging
import uuid
from typing import Dict, Any, Optional, Callable

from ...flow_engine import get_flow_engine
from ...models import Message, MessageRole
from ..events import emitter, WebSocketEvents
from .base import MessageHandler

# Set up logging
logger = logging.getLogger(__name__)

class UserMessageHandler(MessageHandler):
    """Handler for user messages"""
    
    async def handle(
        self, 
        client_id: str, 
        request_data: Dict[str, Any]
    ) -> None:
        """
        Handle a user message
        
        Args:
            client_id: The client's unique ID
            request_data: The request data
        """
        # Validate the request
        if not self.validate_payload(request_data):
            await self.send_error(
                client_id=client_id,
                message="Invalid request: missing payload",
                error_code="INVALID_REQUEST"
            )
            return
        
        # Get the payload
        payload = self.get_payload(request_data)
        
        # Get the message content
        message_content = payload.get("message")
        if not message_content:
            await self.send_error(
                client_id=client_id,
                message="Invalid request: missing message content",
                error_code="INVALID_REQUEST"
            )
            return
        
        # Get the flow instance ID
        flow_instance_id = self.get_flow_instance_id(request_data)
        if not flow_instance_id:
            await self.send_error(
                client_id=client_id,
                message="Invalid request: missing flow_instance_id",
                error_code="INVALID_REQUEST"
            )
            return
        
        # Get the flow engine
        flow_engine = get_flow_engine()
        
        # Get the flow instance
        flow_instance = flow_engine.get_flow_instance(flow_instance_id)
        if not flow_instance:
            await self.send_error(
                client_id=client_id,
                message=f"Flow instance not found: {flow_instance_id}",
                flow_instance_id=flow_instance_id,
                error_code="NOT_FOUND"
            )
            return
        
        # Create callbacks for token and thinking streaming
        on_token = self._create_token_callback(client_id, flow_instance_id)
        on_thinking = self._create_thinking_callback(client_id, flow_instance_id)
        
        try:
            # Notify that the flow has started
            await self.send_flow_started(
                client_id=client_id,
                flow_instance_id=flow_instance_id,
                flow_config_id=flow_instance.flow_config_id
            )
            
            # Process the user input
            result = await flow_engine.process_user_input(
                instance_id=flow_instance_id,
                user_input=message_content,
                on_token=on_token,
                on_thinking=on_thinking
            )
            
            # Check for errors
            if "error" in result:
                await self.send_flow_error(
                    client_id=client_id,
                    flow_instance_id=flow_instance_id,
                    error=result["error"]
                )
                return
            
            # Notify that the flow has completed
            await self.send_flow_completed(
                client_id=client_id,
                flow_instance_id=flow_instance_id
            )
            
        except Exception as e:
            logger.error(f"Error processing user message: {e}")
            await self.send_flow_error(
                client_id=client_id,
                flow_instance_id=flow_instance_id,
                error=f"Error processing user message: {e}"
            )
    
    def _create_token_callback(
        self, 
        client_id: str, 
        flow_instance_id: str
    ) -> Callable[[str, str, str], None]:
        """
        Create a callback for token streaming
        
        Args:
            client_id: The client's unique ID
            flow_instance_id: The flow instance ID
            
        Returns:
            A callback function
        """
        async def on_token(node_id: str, token: str, message_id: str) -> None:
            """
            Callback for token streaming
            
            Args:
                node_id: The node ID
                token: The token
                message_id: The message ID
            """
            await self.send_node_token(
                client_id=client_id,
                node_id=node_id,
                token=token,
                message_id=message_id,
                flow_instance_id=flow_instance_id
            )
        
        return on_token
    
    def _create_thinking_callback(
        self, 
        client_id: str, 
        flow_instance_id: str
    ) -> Callable[[str, str, str], None]:
        """
        Create a callback for thinking streaming
        
        Args:
            client_id: The client's unique ID
            flow_instance_id: The flow instance ID
            
        Returns:
            A callback function
        """
        async def on_thinking(node_id: str, thinking: str, message_id: str) -> None:
            """
            Callback for thinking streaming
            
            Args:
                node_id: The node ID
                thinking: The thinking content
                message_id: The message ID
            """
            await self.send_node_thinking(
                client_id=client_id,
                node_id=node_id,
                thinking=thinking,
                message_id=message_id,
                flow_instance_id=flow_instance_id
            )
        
        return on_thinking
