"""
Core WebSocket functionality.

This module provides the core WebSocket functionality, including the connection manager
and handler registry.
"""

import logging
from typing import Dict, Any, Optional, List, Type, Set
import json
from fastapi import WebSocket, WebSocketDisconnect

from .events import emitter, WebSocketEvents
from .handlers.base import MessageHandler

# Set up logging
logger = logging.getLogger(__name__)

class ConnectionManager:
    """
    WebSocket connection manager.
    
    This class manages WebSocket connections and message sending.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: Dict[str, WebSocket] = {}
        self.client_to_flow_instance: Dict[str, str] = {}
        self.flow_instance_to_clients: Dict[str, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Connect a WebSocket client.
        
        Args:
            websocket: The WebSocket connection
            client_id: The client's unique ID
        """
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"Client connected: {client_id}")
        
        # Emit a connection established event
        await emitter.emit(
            WebSocketEvents.CONNECTION_ESTABLISHED,
            client_id=client_id
        )
    
    async def disconnect(self, client_id: str) -> None:
        """
        Disconnect a WebSocket client.
        
        Args:
            client_id: The client's unique ID
        """
        if client_id in self.active_connections:
            # Remove the client from flow instance mappings
            if client_id in self.client_to_flow_instance:
                flow_instance_id = self.client_to_flow_instance[client_id]
                if flow_instance_id in self.flow_instance_to_clients:
                    self.flow_instance_to_clients[flow_instance_id].remove(client_id)
                    if not self.flow_instance_to_clients[flow_instance_id]:
                        del self.flow_instance_to_clients[flow_instance_id]
                del self.client_to_flow_instance[client_id]
            
            # Remove the client from active connections
            del self.active_connections[client_id]
            logger.info(f"Client disconnected: {client_id}")
            
            # Emit a connection closed event
            await emitter.emit(
                WebSocketEvents.CONNECTION_CLOSED,
                client_id=client_id
            )
    
    async def send_message(self, message: Dict[str, Any], client_id: str) -> None:
        """
        Send a message to a specific client.
        
        Args:
            message: The message to send
            client_id: The client's unique ID
        """
        if client_id in self.active_connections:
            websocket = self.active_connections[client_id]
            try:
                await websocket.send_json(message)
                
                # Emit a message sent event
                await emitter.emit(
                    WebSocketEvents.MESSAGE_SENT,
                    client_id=client_id,
                    message=message
                )
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast(self, message: Dict[str, Any]) -> None:
        """
        Broadcast a message to all connected clients.
        
        Args:
            message: The message to broadcast
        """
        for client_id in list(self.active_connections.keys()):
            await self.send_message(message, client_id)
    
    async def broadcast_to_flow_instance(
        self, 
        message: Dict[str, Any], 
        flow_instance_id: str
    ) -> None:
        """
        Broadcast a message to all clients connected to a flow instance.
        
        Args:
            message: The message to broadcast
            flow_instance_id: The flow instance ID
        """
        if flow_instance_id in self.flow_instance_to_clients:
            for client_id in list(self.flow_instance_to_clients[flow_instance_id]):
                await self.send_message(message, client_id)
    
    def associate_client_with_flow_instance(
        self, 
        client_id: str, 
        flow_instance_id: str
    ) -> None:
        """
        Associate a client with a flow instance.
        
        Args:
            client_id: The client's unique ID
            flow_instance_id: The flow instance ID
        """
        self.client_to_flow_instance[client_id] = flow_instance_id
        if flow_instance_id not in self.flow_instance_to_clients:
            self.flow_instance_to_clients[flow_instance_id] = set()
        self.flow_instance_to_clients[flow_instance_id].add(client_id)
        logger.info(f"Associated client {client_id} with flow instance {flow_instance_id}")

class HandlerRegistry:
    """
    Registry for message handlers.
    
    This class manages the registration and retrieval of message handlers.
    """
    
    def __init__(self):
        """Initialize the handler registry."""
        self.handlers: Dict[str, Type[MessageHandler]] = {}
    
    def register(self, message_type: str, handler_class: Type[MessageHandler]) -> None:
        """
        Register a handler for a message type.
        
        Args:
            message_type: The message type
            handler_class: The handler class
        """
        self.handlers[message_type] = handler_class
        logger.info(f"Registered handler for message type: {message_type}")
    
    def get_handler(self, message_type: str) -> Optional[MessageHandler]:
        """
        Get a handler for a message type.
        
        Args:
            message_type: The message type
            
        Returns:
            A handler instance, or None if not found
        """
        handler_class = self.handlers.get(message_type)
        if handler_class:
            return handler_class()
        return None

# Singleton instances
manager = ConnectionManager()
registry = HandlerRegistry()
