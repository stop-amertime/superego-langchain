"""
Assistant agent implementation.

This module provides a concrete implementation of the AssistantAgent
that can use tools to respond to user queries.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

from ..models import ToolInput, ToolOutput
from ..tools import get_tool
from .base import AssistantAgent, AgentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleAssistant(AssistantAgent):
    """
    Simple implementation of the Assistant agent.
    
    This agent can use tools to respond to user queries.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simple assistant agent.
        
        Args:
            config: Configuration for the agent, including:
                - system_prompt: The system prompt for the assistant
                - available_tools: Optional list of available tools
        """
        super().__init__(config)
        
        # Get the available tools
        self.tool_names = config.get("available_tools", ["calculator"])
        self.available_tools = [get_tool(name) for name in self.tool_names if get_tool(name)]
        
        logger.info(f"Initialized SimpleAssistant with {len(self.available_tools)} tools")
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """
        Process input and return a complete response.
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Returns:
            The processed response
        """
        # Check if there's a caution message
        caution_message = context.get("caution_message")
        if caution_message:
            response = f"[CAUTION: {caution_message}]\n\n"
        else:
            response = ""
        
        # Check if the input is a tool request
        if "calculate" in input_text.lower() or "calculator" in input_text.lower():
            # Extract the expression from the input
            # This is a simple implementation that assumes the expression is everything after "calculate"
            expression = input_text.lower().split("calculate", 1)[-1].strip()
            if not expression:
                expression = input_text.lower().split("calculator", 1)[-1].strip()
            
            # Use the calculator tool
            calculator = get_tool("calculator")
            if calculator:
                tool_input = ToolInput(name="calculator", arguments={"expression": expression})
                tool_output = await self.use_tool(tool_input, context)
                
                response += f"I'll calculate that for you.\n\nExpression: {expression}\n{tool_output.output}"
            else:
                response += "I'm sorry, but the calculator tool is not available."
        else:
            # Simple response for non-tool requests
            response += f"You said: {input_text}\n\nI'm a simple assistant that can use tools. Try asking me to calculate something, like '2 + 2'."
        
        return response
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream the response token by token.
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Yields:
            Tokens from the response
        """
        # Set running flag
        self._is_running = True
        
        try:
            # Get the full response
            response = await self.process(input_text, context)
            
            # Simulate streaming by yielding one character at a time
            for char in response:
                if not self._is_running:
                    logger.info("Streaming interrupted")
                    break
                yield char
                await asyncio.sleep(0.001)  # Small delay to simulate streaming
                
        except Exception as e:
            logger.error(f"Error in SimpleAssistant.stream: {str(e)}")
            yield f"Error: {str(e)}"
        finally:
            self._is_running = False
