"""
Event emitter for WebSocket communication.

This module provides an event-based system for WebSocket communication,
allowing components to communicate without direct references to each other.
"""

import asyncio
import logging
from typing import Dict, List, Any, Callable, Awaitable, Optional

# Set up logging
logger = logging.getLogger(__name__)

class EventEmitter:
    """
    Event emitter for asynchronous event-based communication.
    
    This class provides a simple event emitter that allows components to
    subscribe to events and emit events to subscribers.
    """
    
    def __init__(self):
        """Initialize the event emitter with an empty dictionary of listeners."""
        self.listeners: Dict[str, List[Callable[..., Awaitable[None]]]] = {}
    
    def on(self, event: str, listener: Callable[..., Awaitable[None]]) -> None:
        """
        Register a listener for an event.
        
        Args:
            event: The event to listen for
            listener: The async function to call when the event is emitted
        """
        if event not in self.listeners:
            self.listeners[event] = []
        
        self.listeners[event].append(listener)
        logger.debug(f"Registered listener for event: {event}")
    
    def off(self, event: str, listener: Optional[Callable[..., Awaitable[None]]] = None) -> None:
        """
        Remove a listener for an event.
        
        Args:
            event: The event to remove the listener from
            listener: The listener to remove. If None, all listeners for the event are removed.
        """
        if event not in self.listeners:
            return
        
        if listener is None:
            self.listeners[event] = []
            logger.debug(f"Removed all listeners for event: {event}")
        else:
            self.listeners[event] = [l for l in self.listeners[event] if l != listener]
            logger.debug(f"Removed listener for event: {event}")
    
    async def emit(self, event: str, *args: Any, **kwargs: Any) -> None:
        """
        Emit an event to all registered listeners.
        
        Args:
            event: The event to emit
            *args: Positional arguments to pass to the listeners
            **kwargs: Keyword arguments to pass to the listeners
        """
        if event not in self.listeners:
            logger.debug(f"No listeners for event: {event}")
            return
        
        logger.debug(f"Emitting event: {event} to {len(self.listeners[event])} listeners")
        
        # Create tasks for all listeners
        tasks = []
        for listener in self.listeners[event]:
            task = asyncio.create_task(listener(*args, **kwargs))
            tasks.append(task)
        
        # Wait for all tasks to complete
        if tasks:
            await asyncio.gather(*tasks)

# Global event emitter instance
emitter = EventEmitter()

# Event types
class WebSocketEvents:
    """Event types for WebSocket communication."""
    
    # Connection events
    CONNECTION_ESTABLISHED = "connection:established"
    CONNECTION_CLOSED = "connection:closed"
    
    # Message events
    MESSAGE_RECEIVED = "message:received"
    MESSAGE_SENT = "message:sent"
    
    # Node events (node-centric approach)
    NODE_STATE_CHANGED = "node:state_changed"  # When a node changes state (started, processing, completed)
    NODE_OUTPUT = "node:output"                # When a node produces output
    NODE_ERROR = "node:error"                  # When a node encounters an error
    NODE_TOKEN = "node:token"                  # When a node produces a token (for streaming)
    NODE_THINKING = "node:thinking"            # When a node is thinking (for streaming thinking)
    
    # Flow events
    FLOW_STARTED = "flow:started"              # When a flow starts
    FLOW_COMPLETED = "flow:completed"          # When a flow completes
    FLOW_ERROR = "flow:error"                  # When a flow encounters an error
    
    # System events
    SYSTEM_MESSAGE = "system:message"          # System messages
    ERROR = "error"                            # Error messages
