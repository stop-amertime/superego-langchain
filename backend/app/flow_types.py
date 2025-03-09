"""
Types for the flow system.

This module provides types used by the flow system, including Command for routing.
"""

from typing import Dict, Any, Optional, TypeVar, Generic, Literal

# Type variable for the goto parameter
T = TypeVar('T')

class Command(Generic[T]):
    """
    Command object for routing in the flow system.
    
    This is a simplified version of the Command object from langgraph.
    """
    
    # Special constant for parent graph
    PARENT = "__parent__"
    
    def __init__(
        self,
        goto: T,
        update: Optional[Dict[str, Any]] = None,
        graph: Optional[str] = None
    ):
        """
        Initialize a Command object.
        
        Args:
            goto: The destination node
            update: Optional state update
            graph: Optional graph to navigate to
        """
        self.goto = goto
        self.update = update or {}
        self.graph = graph
