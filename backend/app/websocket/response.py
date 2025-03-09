"""
Response formatter for WebSocket communication.

This module provides standardized response formatting for WebSocket messages.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ..models import WebSocketMessageType
from .events import WebSocketEvents

# Set up logging
logger = logging.getLogger(__name__)

class WebSocketResponse:
    """Standard response structure for WebSocket messages"""
    
    @staticmethod
    def create(
        type: str,
        payload: Dict[str, Any],
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized WebSocket response
        
        Args:
            type: The message type
            payload: The message payload
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized response dictionary
        """
        response = {
            "type": type,
            "payload": payload,
            "timestamp": datetime.now().isoformat()
        }
        
        if flow_instance_id:
            response["flow_instance_id"] = flow_instance_id
            
        return response
    
    @staticmethod
    def error(
        message: str,
        details: Optional[Dict[str, Any]] = None,
        flow_instance_id: Optional[str] = None,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized error response
        
        Args:
            message: The error message
            details: Optional error details
            flow_instance_id: Optional flow instance ID
            error_code: Optional error code
            
        Returns:
            A standardized error response dictionary
        """
        payload = {
            "message": message
        }
        
        if details:
            payload["details"] = details
            
        if error_code:
            payload["error_code"] = error_code
            
        return WebSocketResponse.create(
            WebSocketEvents.ERROR,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def node_state_changed(
        node_id: str,
        state: str,
        data: Optional[Dict[str, Any]] = None,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized node state changed response
        
        Args:
            node_id: The node ID
            state: The new state
            data: Optional data associated with the state change
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized node state changed response
        """
        payload = {
            "node_id": node_id,
            "state": state
        }
        
        if data:
            payload["data"] = data
            
        return WebSocketResponse.create(
            WebSocketEvents.NODE_STATE_CHANGED,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def node_output(
        node_id: str,
        output: Any,
        output_type: Optional[str] = None,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized node output response
        
        Args:
            node_id: The node ID
            output: The output
            output_type: Optional output type
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized node output response
        """
        payload = {
            "node_id": node_id,
            "output": output
        }
        
        if output_type:
            payload["output_type"] = output_type
            
        return WebSocketResponse.create(
            WebSocketEvents.NODE_OUTPUT,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def node_error(
        node_id: str,
        error: str,
        details: Optional[Dict[str, Any]] = None,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized node error response
        
        Args:
            node_id: The node ID
            error: The error message
            details: Optional error details
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized node error response
        """
        payload = {
            "node_id": node_id,
            "error": error
        }
        
        if details:
            payload["details"] = details
            
        return WebSocketResponse.create(
            WebSocketEvents.NODE_ERROR,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def node_token(
        node_id: str,
        token: str,
        message_id: str,
        flow_instance_id: Optional[str] = None,
        flow_config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized node token response
        
        Args:
            node_id: The node ID
            token: The token
            message_id: The message ID
            flow_instance_id: Optional flow instance ID
            flow_config_id: Optional flow config ID
            
        Returns:
            A standardized node token response
        """
        payload = {
            "node_id": node_id,
            "token": token,
            "message_id": message_id
        }
        
        if flow_config_id:
            payload["flow_config_id"] = flow_config_id
            
        return WebSocketResponse.create(
            WebSocketEvents.NODE_TOKEN,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def node_thinking(
        node_id: str,
        thinking: str,
        message_id: str,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized node thinking response
        
        Args:
            node_id: The node ID
            thinking: The thinking content
            message_id: The message ID
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized node thinking response
        """
        payload = {
            "node_id": node_id,
            "thinking": thinking,
            "message_id": message_id
        }
        
        return WebSocketResponse.create(
            WebSocketEvents.NODE_THINKING,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def flow_started(
        flow_instance_id: str,
        flow_config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized flow started response
        
        Args:
            flow_instance_id: The flow instance ID
            flow_config_id: Optional flow config ID
            
        Returns:
            A standardized flow started response
        """
        payload = {}
        
        if flow_config_id:
            payload["flow_config_id"] = flow_config_id
            
        return WebSocketResponse.create(
            WebSocketEvents.FLOW_STARTED,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def flow_completed(
        flow_instance_id: str,
        results: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized flow completed response
        
        Args:
            flow_instance_id: The flow instance ID
            results: Optional results
            
        Returns:
            A standardized flow completed response
        """
        payload = {}
        
        if results:
            payload["results"] = results
            
        return WebSocketResponse.create(
            WebSocketEvents.FLOW_COMPLETED,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def flow_error(
        flow_instance_id: str,
        error: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized flow error response
        
        Args:
            flow_instance_id: The flow instance ID
            error: The error message
            details: Optional error details
            
        Returns:
            A standardized flow error response
        """
        payload = {
            "error": error
        }
        
        if details:
            payload["details"] = details
            
        return WebSocketResponse.create(
            WebSocketEvents.FLOW_ERROR,
            payload,
            flow_instance_id
        )
    
    @staticmethod
    def system_message(
        message: str,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized system message response
        
        Args:
            message: The message
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized system message response
        """
        return WebSocketResponse.create(
            WebSocketEvents.SYSTEM_MESSAGE,
            {
                "message": message
            },
            flow_instance_id
        )
    
    # Legacy methods for backward compatibility
    
    @staticmethod
    def superego_evaluation_started(
        constitution_id: Optional[str] = None,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized superego evaluation started response (legacy)
        
        Args:
            constitution_id: Optional constitution ID
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized superego evaluation started response
        """
        return WebSocketResponse.node_state_changed(
            node_id="input_superego",
            state="started",
            data={
                "message": "Superego is evaluating your message...",
                "constitutionId": constitution_id
            },
            flow_instance_id=flow_instance_id
        )
    
    @staticmethod
    def superego_evaluation_thinking(
        thinking: str,
        message_id: str,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized superego evaluation thinking response (legacy)
        
        Args:
            thinking: The thinking content
            message_id: The message ID
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized superego evaluation thinking response
        """
        return WebSocketResponse.node_thinking(
            node_id="input_superego",
            thinking=thinking,
            message_id=message_id,
            flow_instance_id=flow_instance_id
        )
    
    @staticmethod
    def superego_evaluation_completed(
        superego_message,
        constitution_id: Optional[str] = None,
        checkpoint_id: Optional[str] = None,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized superego evaluation completed response (legacy)
        
        Args:
            superego_message: The superego message
            constitution_id: Optional constitution ID
            checkpoint_id: Optional checkpoint ID
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized superego evaluation completed response
        """
        return WebSocketResponse.node_state_changed(
            node_id="input_superego",
            state="completed",
            data={
                "decision": superego_message.decision,
                "reason": superego_message.content,
                "thinking": superego_message.thinking,
                "id": superego_message.id,
                "constitutionId": constitution_id,
                "checkpoint_id": checkpoint_id
            },
            flow_instance_id=flow_instance_id
        )
    
    @staticmethod
    def assistant_token(
        token: str,
        message_id: str,
        flow_instance_id: Optional[str] = None,
        flow_config_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized assistant token response (legacy)
        
        Args:
            token: The token
            message_id: The message ID
            flow_instance_id: Optional flow instance ID
            flow_config_id: Optional flow config ID
            
        Returns:
            A standardized assistant token response
        """
        return WebSocketResponse.node_token(
            node_id="assistant",
            token=token,
            message_id=message_id,
            flow_instance_id=flow_instance_id,
            flow_config_id=flow_config_id
        )
    
    @staticmethod
    def assistant_message(
        message_id: str,
        content: str,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized assistant message response (legacy)
        
        Args:
            message_id: The message ID
            content: The message content
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized assistant message response
        """
        return WebSocketResponse.node_output(
            node_id="assistant",
            output={
                "id": message_id,
                "content": content
            },
            output_type="message",
            flow_instance_id=flow_instance_id
        )
    
    @staticmethod
    def parallel_flows_result(
        results: list,
        flow_instance_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a standardized parallel flows result response (legacy)
        
        Args:
            results: The results
            flow_instance_id: Optional flow instance ID
            
        Returns:
            A standardized parallel flows result response
        """
        return WebSocketResponse.flow_completed(
            flow_instance_id=flow_instance_id,
            results=[result.dict() for result in results]
        )
