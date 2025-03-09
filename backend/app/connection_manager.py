import logging
import asyncio
from typing import Dict, Any, Optional
from fastapi import WebSocket

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectionManager:
    """WebSocket connection manager for handling client connections"""
    
    def __init__(self):
        """Initialize the connection manager with an empty dictionary of active connections"""
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a client to the WebSocket server
        
        Args:
            websocket: The WebSocket connection
            client_id: The client's unique ID
        """
        try:
            # Check if there's already a connection for this client
            if client_id in self.active_connections:
                # Existing connection for this client ID
                logger.info(f"Client {client_id} already has an active connection, replacing it")
                try:
                    # Try to gracefully close the existing connection
                    await self.active_connections[client_id].close()
                except Exception:
                    # Ignore errors when closing existing connection
                    pass
                # Remove from active connections
                del self.active_connections[client_id]
            
            # Accept the new connection
            await websocket.accept()
            # Store the connection
            self.active_connections[client_id] = websocket
            logger.info(f"Client {client_id} connected. Active connections: {len(self.active_connections)}")
            
            # Add a small delay (needed for some clients)
            await asyncio.sleep(0.1)
        except Exception as e:
            logger.error(f"Error accepting WebSocket connection: {str(e)}")

    def disconnect(self, client_id: str):
        """
        Disconnect a client from the WebSocket server
        
        Args:
            client_id: The client's unique ID
        """
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"Client {client_id} disconnected. Active connections: {len(self.active_connections)}")

    async def send_message(self, message: Dict[str, Any], client_id: str):
        """
        Send a message to a specific client
        
        Args:
            message: The message to send
            client_id: The client's unique ID
        """
        if client_id in self.active_connections:
            try:
                # Simplified check and error handling
                await self.active_connections[client_id].send_json(message)
            except RuntimeError:
                # Socket already closed, remove it
                self.disconnect(client_id)
            except Exception as e:
                logger.error(f"Error sending message to client {client_id}: {str(e)}")
        else:
            # Client ID not found - no need to log a warning
            pass

    async def broadcast(self, message: Dict[str, Any]):
        """
        Broadcast a message to all connected clients
        
        Args:
            message: The message to broadcast
        """
        disconnected_clients = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_json(message)
            except RuntimeError:
                logger.error(f"Error sending message to client {client_id}. Will mark for disconnect.")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            self.disconnect(client_id)

# Initialize a global connection manager instance
manager = ConnectionManager()
