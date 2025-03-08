import logging
import json
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator
from autogen_agentchat.agents import AssistantAgent
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .models import SuperegoEvaluation, SuperegoDecision

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Agent interface
class Agent(ABC):
    """Base interface for all agents"""
    
    @abstractmethod
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """Process input and return a complete response"""
        pass
    
    @abstractmethod
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream the response token by token"""
        pass
    
    @abstractmethod
    async def interrupt(self) -> bool:
        """Interrupt the current processing"""
        pass

# Agent factory
class AgentFactory:
    """Factory for creating agents of different types"""
    
    _registry = {}
    
    @classmethod
    def register(cls, agent_type: str, agent_class):
        """Register an agent class for a specific type"""
        cls._registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")
    
    @classmethod
    def create(cls, agent_type: str, config: Dict[str, Any]) -> Agent:
        """Create an agent of the specified type"""
        if agent_type not in cls._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        logger.info(f"Creating agent of type: {agent_type}")
        return cls._registry[agent_type](config)

# AutoGen agent implementation
class AutoGenAgent(Agent):
    """Agent implementation using AutoGen"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "anthropic/claude-3.7-sonnet")
        self.system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        
        # Create the model client
        # When using a non-OpenAI model with OpenRouter, we need to provide model_info
        self.model_client = OpenAIChatCompletionClient(
            model=self.model,
            api_key=self.api_key,
            base_url=self.base_url,
            model_info={
                "name": self.model,
                "context_length": 100000,  # Claude 3.7 Sonnet context length
                "max_tokens": 4096,  # Max output tokens
                "is_chat_model": True,
                "vision": False,  # Required field in v0.4.7+
                "function_calling": True,  # Required field in v0.4.7+
                "json_output": True,  # Required field for OpenAI-compatible APIs
                "family": "anthropic"  # Specify the model family
            }
        )
        
        # Create the AutoGen agent
        self.agent = AssistantAgent(
            name="assistant",
            model_client=self.model_client,
            system_message=self.system_prompt,
            model_client_stream=True
        )
        
        self._is_running = False
        logger.info(f"Initialized AutoGenAgent with model: {self.model}")
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """Process input and return a complete response"""
        logger.info(f"Processing input with AutoGenAgent: {input_text[:50]}...")
        
        try:
            # Use the AutoGen agent to process the input
            response = await self.agent.run(task=input_text)
            return response
        except Exception as e:
            logger.error(f"Error in AutoGenAgent.process: {str(e)}")
            return f"Error: {str(e)}"
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream the response token by token"""
        logger.info(f"Streaming response for input: {input_text[:50]}...")
        
        # Set running flag
        self._is_running = True
        
        try:
            # Use the AutoGen agent to stream the response
            async for message in self.agent.run_stream(task=input_text):
                if not self._is_running:
                    logger.info("Streaming interrupted")
                    break
                
                # Handle different types of messages
                from autogen_agentchat.messages import ModelClientStreamingChunkEvent, TextMessage
                from autogen_agentchat.base import TaskResult
                
                if isinstance(message, ModelClientStreamingChunkEvent):
                    # This is a token from the model
                    yield message.content
                elif isinstance(message, TextMessage) and message.source == "assistant":
                    # This is a complete message from the assistant
                    # We don't need to yield this as we've already yielded the tokens
                    pass
                elif isinstance(message, TaskResult):
                    # This is the final result, we don't need to yield it
                    pass
                elif isinstance(message, str):
                    # For backward compatibility
                    yield message
                else:
                    # Log unknown message types for debugging
                    logger.debug(f"Unknown message type in stream: {type(message)}")
        except Exception as e:
            logger.error(f"Error in AutoGenAgent.stream: {str(e)}")
            yield f"Error: {str(e)}"
        finally:
            self._is_running = False
    
    async def interrupt(self) -> bool:
        """Interrupt the current processing"""
        if self._is_running:
            logger.info("Interrupting AutoGenAgent")
            self._is_running = False
            return True
        return False

# Register the AutoGenAgent with the factory
AgentFactory.register("autogen", AutoGenAgent)

# Import the constitution registry
from .constitution_registry import ConstitutionRegistry

# Path to constitutions directory
CONSTITUTIONS_DIR = os.path.join(os.path.dirname(__file__), "data", "constitutions")

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
