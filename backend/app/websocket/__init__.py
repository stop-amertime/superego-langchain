"""
WebSocket package for the Superego LangGraph application.

This package provides a stateless, event-based WebSocket interface with standardized
message formats and clear separation of concerns.
"""

from .core import manager, registry
from .events import emitter, WebSocketEvents
from .response import WebSocketResponse
from .handlers import MessageHandler, UserMessageHandler

# Export the public API
__all__ = [
    "manager",
    "registry",
    "emitter",
    "WebSocketEvents",
    "WebSocketResponse",
    "MessageHandler",
    "UserMessageHandler"
]
