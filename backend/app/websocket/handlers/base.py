"""
Base message handler for WebSocket communication.

This module provides a base class for all message handlers.
"""

import logging
from typing import Dict, Any, Optional, List, Type

from ...models import Message
from ..response import WebSocketResponse
from ..events import emitter, WebSocketEvents

# Set up logging
logger = logging.getLogger(__name__)

class MessageHandler:
    """Base class for message handlers"""
    
    async def handle(
        self, 
        client_id: str, 
        request_data: Dict[str, Any]
    ) -> None:
        """
        Handle a message
        
        Args:
            client_id: The client's unique ID
            request_data: The request data
        """
        raise NotImplementedError("Subclasses must implement handle()")
    
    def validate_payload(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate the payload of a request
        
        Args:
            request_data: The request data
            
        Returns:
            True if the payload is valid, False otherwise
        """
        return "payload" in request_data
    
    def validate_flow_instance_id(self, request_data: Dict[str, Any]) -> bool:
        """
        Validate the flow_instance_id of a request
        
        Args:
            request_data: The request data
            
        Returns:
            True if the flow_instance_id is valid, False otherwise
        """
        return "flow_instance_id" in request_data
    
    def get_payload(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get the payload from a request
        
        Args:
            request_data: The request data
            
        Returns:
            The payload
        """
        return request_data.get("payload", {})
    
    def get_flow_instance_id(self, request_data: Dict[str, Any]) -> Optional[str]:
        """
        Get the flow_instance_id from a request
        
        Args:
            request_data: The request data
            
        Returns:
            The flow_instance_id, or None if not present
        """
        return request_data.get("flow_instance_id")
    
    async def send_error(
        self,
        client_id: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        flow_instance_id: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> None:
        """
        Send an error response
        
        Args:
            client_id: The client's unique ID
            message: The error message
            details: Optional error details
            flow_instance_id: Optional flow instance ID
            error_code: Optional error code
        """
        from ..core import manager
        
        response = WebSocketResponse.error(
            message=message,
            details=details,
            flow_instance_id=flow_instance_id,
            error_code=error_code
        )
        
        await manager.send_message(response, client_id)
        
        # Emit an error event
        await emitter.emit(
            WebSocketEvents.ERROR,
            client_id=client_id,
            message=message,
            details=details,
            flow_instance_id=flow_instance_id,
            error_code=error_code
        )
    
    async def send_system_message(
        self,
        client_id: str,
        message: str,
        flow_instance_id: Optional[str] = None
    ) -> None:
        """
        Send a system message
        
        Args:
            client_id: The client's unique ID
            message: The message
            flow_instance_id: Optional flow instance ID
        """
        from ..core import manager
        
        response = WebSocketResponse.system_message(
            message=message,
            flow_instance_id=flow_instance_id
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a system message event
        await emitter.emit(
            WebSocketEvents.SYSTEM_MESSAGE,
            client_id=client_id,
            message=message,
            flow_instance_id=flow_instance_id
        )
    
    async def send_node_state_changed(
        self,
        client_id: str,
        node_id: str,
        state: str,
        data: Optional[Dict[str, Any]] = None,
        flow_instance_id: Optional[str] = None
    ) -> None:
        """
        Send a node state changed response
        
        Args:
            client_id: The client's unique ID
            node_id: The node ID
            state: The new state
            data: Optional data associated with the state change
            flow_instance_id: Optional flow instance ID
        """
        from ..core import manager
        
        response = WebSocketResponse.node_state_changed(
            node_id=node_id,
            state=state,
            data=data,
            flow_instance_id=flow_instance_id
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a node state changed event
        await emitter.emit(
            WebSocketEvents.NODE_STATE_CHANGED,
            client_id=client_id,
            node_id=node_id,
            state=state,
            data=data,
            flow_instance_id=flow_instance_id
        )
    
    async def send_node_output(
        self,
        client_id: str,
        node_id: str,
        output: Any,
        output_type: Optional[str] = None,
        flow_instance_id: Optional[str] = None
    ) -> None:
        """
        Send a node output response
        
        Args:
            client_id: The client's unique ID
            node_id: The node ID
            output: The output
            output_type: Optional output type
            flow_instance_id: Optional flow instance ID
        """
        from ..core import manager
        
        response = WebSocketResponse.node_output(
            node_id=node_id,
            output=output,
            output_type=output_type,
            flow_instance_id=flow_instance_id
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a node output event
        await emitter.emit(
            WebSocketEvents.NODE_OUTPUT,
            client_id=client_id,
            node_id=node_id,
            output=output,
            output_type=output_type,
            flow_instance_id=flow_instance_id
        )
    
    async def send_node_token(
        self,
        client_id: str,
        node_id: str,
        token: str,
        message_id: str,
        flow_instance_id: Optional[str] = None,
        flow_config_id: Optional[str] = None
    ) -> None:
        """
        Send a node token response
        
        Args:
            client_id: The client's unique ID
            node_id: The node ID
            token: The token
            message_id: The message ID
            flow_instance_id: Optional flow instance ID
            flow_config_id: Optional flow config ID
        """
        from ..core import manager
        
        response = WebSocketResponse.node_token(
            node_id=node_id,
            token=token,
            message_id=message_id,
            flow_instance_id=flow_instance_id,
            flow_config_id=flow_config_id
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a node token event
        await emitter.emit(
            WebSocketEvents.NODE_TOKEN,
            client_id=client_id,
            node_id=node_id,
            token=token,
            message_id=message_id,
            flow_instance_id=flow_instance_id,
            flow_config_id=flow_config_id
        )
    
    async def send_node_thinking(
        self,
        client_id: str,
        node_id: str,
        thinking: str,
        message_id: str,
        flow_instance_id: Optional[str] = None
    ) -> None:
        """
        Send a node thinking response
        
        Args:
            client_id: The client's unique ID
            node_id: The node ID
            thinking: The thinking content
            message_id: The message ID
            flow_instance_id: Optional flow instance ID
        """
        from ..core import manager
        
        response = WebSocketResponse.node_thinking(
            node_id=node_id,
            thinking=thinking,
            message_id=message_id,
            flow_instance_id=flow_instance_id
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a node thinking event
        await emitter.emit(
            WebSocketEvents.NODE_THINKING,
            client_id=client_id,
            node_id=node_id,
            thinking=thinking,
            message_id=message_id,
            flow_instance_id=flow_instance_id
        )
    
    async def send_flow_started(
        self,
        client_id: str,
        flow_instance_id: str,
        flow_config_id: Optional[str] = None
    ) -> None:
        """
        Send a flow started response
        
        Args:
            client_id: The client's unique ID
            flow_instance_id: The flow instance ID
            flow_config_id: Optional flow config ID
        """
        from ..core import manager
        
        response = WebSocketResponse.flow_started(
            flow_instance_id=flow_instance_id,
            flow_config_id=flow_config_id
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a flow started event
        await emitter.emit(
            WebSocketEvents.FLOW_STARTED,
            client_id=client_id,
            flow_instance_id=flow_instance_id,
            flow_config_id=flow_config_id
        )
    
    async def send_flow_completed(
        self,
        client_id: str,
        flow_instance_id: str,
        results: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Send a flow completed response
        
        Args:
            client_id: The client's unique ID
            flow_instance_id: The flow instance ID
            results: Optional results
        """
        from ..core import manager
        
        response = WebSocketResponse.flow_completed(
            flow_instance_id=flow_instance_id,
            results=results
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a flow completed event
        await emitter.emit(
            WebSocketEvents.FLOW_COMPLETED,
            client_id=client_id,
            flow_instance_id=flow_instance_id,
            results=results
        )
    
    async def send_flow_error(
        self,
        client_id: str,
        flow_instance_id: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Send a flow error response
        
        Args:
            client_id: The client's unique ID
            flow_instance_id: The flow instance ID
            error: The error message
            details: Optional error details
        """
        from ..core import manager
        
        response = WebSocketResponse.flow_error(
            flow_instance_id=flow_instance_id,
            error=error,
            details=details
        )
        
        await manager.send_message(response, client_id)
        
        # Emit a flow error event
        await emitter.emit(
            WebSocketEvents.FLOW_ERROR,
            client_id=client_id,
            flow_instance_id=flow_instance_id,
            error=error,
            details=details
        )
