"""
Core WebSocket connection handling.
This module contains the main WebSocket connection handler that delegates
to specific message handlers based on the message type.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Any, Optional

from fastapi import WebSocket, WebSocketDisconnect

from ..models import Message, WebSocketMessageType
from ..connection_manager import ConnectionManager
from ..conversation_manager import get_conversation
from ..errors import (
    AppError, InvalidRequestError, MissingParameterError, 
    WebSocketError, handle_exception, format_websocket_error
)
from .utils import parse_message

# Import message handlers (will be implemented in separate files)
from .message_handlers import user_messages, constitution, flow, system

# Set up logging
logger = logging.getLogger(__name__)

# Import the connection manager instance
from ..connection_manager import manager

async def handle_websocket_connection(websocket: WebSocket, client_id: str, conversations: Dict[str, List[Message]]):
    """
    Handle a WebSocket connection
    
    Args:
        websocket: The WebSocket connection
        client_id: The client's unique ID
        conversations: Dictionary of conversations
    """
    if not client_id:
        client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id)
    
    try:
        # Small delay to ensure connection is stable
        await asyncio.sleep(0.2)
        
        conversation_id = None
        messages: List[Message] = []
        
        while True:
            data = await websocket.receive_text()
            
            try:
                # Parse the message using the utility function
                request_data = parse_message(data)
                logger.info(f"Received message from client {client_id}: {request_data}")
                
                # Extract the message type
                message_type = request_data.get("type")
                logger.info(f"Processing message type: {message_type}")
                
                # Extract conversation ID
                conversation_id = request_data.get("conversation_id", conversation_id)
                
                # Get messages from persistent storage if conversation_id is available
                if conversation_id:
                    messages = get_conversation(conversation_id)
                
                # Initialize conversation context
                context = {
                    "client_id": client_id,
                    "conversation_id": conversation_id,
                    "conversations": conversations,
                    "messages": messages,
                    "manager": manager,
                    "request_data": request_data
                }
                
                # Route to the appropriate message handler based on message type
                if message_type == "user_message":
                    # Handle user message
                    result = await user_messages.handle_user_message(context)
                    if result:
                        messages = result.get("messages", messages)
                        conversation_id = result.get("conversation_id", conversation_id)
                
                elif message_type in ["get_constitutions", "save_constitution", "create_constitution", 
                                     "update_constitution", "delete_constitution"]:
                    # Handle constitution-related messages
                    await constitution.handle_constitution_message(message_type, context)
                
                elif message_type in ["get_flow_templates", "get_flow_configs", "get_flow_instances",
                                     "get_flow_instance", "create_flow_template", "create_flow_config",
                                     "create_flow_instance", "update_flow_template", "update_flow_config",
                                     "update_flow_instance", "delete_flow_template", "delete_flow_config",
                                     "delete_flow_instance", "run_parallel_flows", "get_conversation_history"]:
                    # Handle flow-related messages
                    result = await flow.handle_flow_message(message_type, context)
                    if result:
                        messages = result.get("messages", messages)
                        conversation_id = result.get("conversation_id", conversation_id)
                
                elif message_type in ["get_system_prompts", "get_sysprompts", "save_system_prompt"]:
                    # Handle system prompt-related messages
                    await system.handle_system_message(message_type, context)
                
                elif message_type in ["rerun_message", "rerun_from_constitution"]:
                    # Handle message rerun
                    result = await user_messages.handle_rerun_message(message_type, context)
                    if result:
                        messages = result.get("messages", messages)
                
                else:
                    # Unhandled message type
                    logger.warning(f"Unhandled message type: {message_type}")
                    error = InvalidRequestError(f"Unhandled message type: {message_type}")
                    error.log(logging.WARNING)
                    await manager.send_message(
                        format_websocket_error(error, conversation_id),
                        client_id
                    )
                
            except ValueError as e:
                # Convert ValueError to InvalidRequestError
                error = InvalidRequestError(str(e))
                error.log()
                await manager.send_message(
                    format_websocket_error(error, conversation_id),
                    client_id
                )
            except AppError as e:
                # Already an AppError, just log and send
                e.log()
                await manager.send_message(
                    format_websocket_error(e, conversation_id),
                    client_id
                )
            except Exception as e:
                # Convert generic exception to AppError
                error = handle_exception(e, {"message_type": message_type})
                await manager.send_message(
                    format_websocket_error(error, conversation_id),
                    client_id
                )
                
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        manager.disconnect(client_id)
    except Exception as e:
        # Handle unexpected errors in the WebSocket connection
        error = handle_exception(e, {"client_id": client_id})
        logger.error(f"Unexpected error in WebSocket connection: {error.message}")
        manager.disconnect(client_id)
