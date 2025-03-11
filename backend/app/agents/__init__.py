"""
Agents package for the Superego LangChain application.

This package contains the agent implementations for the multi-agent system,
including superego agents for input and output evaluation, and specialized
assistant agents for different tasks.
"""

import os
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# Import the constitution registry
from ..constitution_registry import ConstitutionRegistry

# Register agent implementations with the factory
AgentFactory.register(AgentType.INPUT_SUPEREGO, SimpleInputSuperego)
AgentFactory.register(AgentType.GENERAL_ASSISTANT, SimpleAssistant)

# Path to constitutions directory
CONSTITUTIONS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "constitutions")

# Initialize the constitution registry
constitution_registry = ConstitutionRegistry(CONSTITUTIONS_DIR)

# Default constitution ID
DEFAULT_CONSTITUTION_ID = "default"

# Get the default constitution content
def get_default_constitution():
    """Get the default constitution content"""
    constitution = constitution_registry.get_constitution(DEFAULT_CONSTITUTION_ID)
    if constitution:
        return constitution["content"]
    else:
        # Fallback if default constitution is not found
        logger.warning(f"Default constitution '{DEFAULT_CONSTITUTION_ID}' not found. Using fallback.")
        return """
# Superego Agent Guidelines

As the Superego Agent, your role is to evaluate user requests for safety, ethics, and appropriateness before they are processed by the main assistant. You act as a protective filter that ensures all interactions remain helpful, harmless, and honest.

## Evaluation Process

1. Carefully analyze the user's request for potential harmful intent or outcomes
2. Assess whether the request might:
   - Cause harm to individuals or groups
   - Facilitate illegal activities
   - Generate misleading or false information
   - Violate privacy or confidentiality
   - Create or spread harmful content

## Decision Framework

Based on your evaluation, provide ONE of the following decisions:

- ALLOW: The request is safe and can be processed normally
- CAUTION: The request may have concerning elements but can be processed with careful handling
- BLOCK: The request should not be fulfilled as it poses significant risks

## Reasoning Requirements

For each decision, provide clear reasoning that explains:
- The specific safety concerns identified (if any)
- The potential impacts of fulfilling the request
- For CAUTION or BLOCK decisions, explain exactly what makes the request problematic

Always remain balanced and fair in your evaluations, avoiding unnecessary restrictions while ensuring appropriate safeguards.
"""

# Get all available constitutions
def get_all_constitutions() -> Dict[str, Dict[str, Any]]:
    """Get all available constitutions"""
    return constitution_registry.get_all_constitutions()

# Save a new constitution
def save_constitution(constitution_id: str, name: str, content: str) -> bool:
    """
    Save a new constitution to a markdown file
    
    Args:
        constitution_id: Unique ID for the constitution
        name: Display name for the constitution
        content: The constitution content
        
    Returns:
        True if saved successfully, False otherwise
    """
    return constitution_registry.save_constitution(constitution_id, name, content)

__all__ = [
    'BaseAgent',
    'SuperegoAgent',
    'InputSuperego',
    'OutputSuperego',
    'AssistantAgent',
    'AgentFactory',
    'AgentType',
    'SimpleInputSuperego',
    'SimpleAssistant',
    'get_default_constitution',
    'get_all_constitutions',
    'save_constitution'
]
