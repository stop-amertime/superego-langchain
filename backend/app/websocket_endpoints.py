"""
WebSocket endpoints for the Superego LangGraph application.

This module provides a stateless, event-based WebSocket interface with standardized
message formats and clear separation of concerns.
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional, List, Type
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from .models import WebSocketMessageType
from .websocket.core import manager, registry
from .websocket.handlers import UserMessageHandler
from .websocket.handlers.flow import FlowHandler
from .websocket.events import WebSocketEvents

# Set up logging
logger = logging.getLogger(__name__)

# Create a router for WebSocket endpoints
router = APIRouter()

@router.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for client connections.
    
    Args:
        websocket: The WebSocket connection
        client_id: The client's unique ID
    """
    # Register handlers
    registry.register("user_message", UserMessageHandler)
    registry.register("flow", FlowHandler)
    
    # Connect the client
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive a message from the client
            data = await websocket.receive_text()
            
            try:
                # Parse the message
                request_data = json.loads(data)
                
                # Get the message type
                message_type = request_data.get("type")
                
                # Get a handler for the message type
                handler = registry.get_handler(message_type)
                
                if handler:
                    # Handle the message
                    await handler.handle(client_id, request_data)
                else:
                    # Unknown message type
                    logger.warning(f"Unknown message type: {message_type}")
                    from .websocket.response import WebSocketResponse
                    
                    response = WebSocketResponse.error(
                        message=f"Unknown message type: {message_type}",
                        error_code="UNKNOWN_MESSAGE_TYPE"
                    )
                    
                    await manager.send_message(response, client_id)
                    
            except json.JSONDecodeError:
                # Invalid JSON
                logger.error("Invalid JSON received")
                from .websocket.response import WebSocketResponse
                
                response = WebSocketResponse.error(
                    message="Invalid JSON",
                    error_code="INVALID_JSON"
                )
                
                await manager.send_message(response, client_id)
                
            except Exception as e:
                # Other errors
                logger.error(f"Error handling message: {e}")
                from .websocket.response import WebSocketResponse
                
                response = WebSocketResponse.error(
                    message=f"Error handling message: {e}",
                    error_code="INTERNAL_ERROR"
                )
                
                await manager.send_message(response, client_id)
                
    except WebSocketDisconnect:
        # Client disconnected
        await manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {e}")
        await manager.disconnect(client_id)
