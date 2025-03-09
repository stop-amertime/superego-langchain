"""
Agents package for the Superego LangChain application.

This package contains the agent implementations for the multi-agent system,
including superego agents for input and output evaluation, and specialized
assistant agents for different tasks.
"""

from .base import (
    BaseAgent,
    SuperegoAgent,
    InputSuperego,
    OutputSuperego,
    AssistantAgent,
    AgentFactory,
    AgentType
)
from .input_superego import SimpleInputSuperego
from .assistant import SimpleAssistant

# Register agent implementations with the factory
AgentFactory.register(AgentType.INPUT_SUPEREGO, SimpleInputSuperego)
AgentFactory.register(AgentType.GENERAL_ASSISTANT, SimpleAssistant)

__all__ = [
    'BaseAgent',
    'SuperegoAgent',
    'InputSuperego',
    'OutputSuperego',
    'AssistantAgent',
    'AgentFactory',
    'AgentType',
    'SimpleInputSuperego',
    'SimpleAssistant'
]
