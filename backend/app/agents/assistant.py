"""
Assistant agent implementation.

This module provides a concrete implementation of the AssistantAgent
that can use tools to respond to user queries.
"""

import logging
import asyncio
import json
import uuid
from datetime import datetime
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
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> Union[str, Dict[str, Any]]:
        """
        Process input and return a complete response.
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Returns:
            The processed response string or a dictionary with message and additional data
        """
        # Create response
        message_id = str(uuid.uuid4())
        
        # Generate response content
        response_content = await self._generate_response(input_text, context)
        
        # Create an assistant message
        message = {
            "id": message_id,
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Return both the response and the message object
        return {
            "message": response_content,
            "message_object": message
        }
    
    async def _generate_response(self, input_text: str, context: Dict[str, Any]) -> str:
        """Generate the actual response content"""
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
            # Create a message ID for this streaming response
            message_id = str(uuid.uuid4())
            
            # Get the token callback function if available
            on_token = context.get("on_token")
            node_id = context.get("node_id", "assistant")
            
            # Log critical information
            logger.info(f"ASSISTANT STREAMING: node_id={node_id}, message_id={message_id}")
            logger.info(f"TOKEN CALLBACK PRESENT: {on_token is not None}")
            
            # Get the full response
            response = await self._generate_response(input_text, context)
            
            # Ensure we have a non-empty response
            if not response:
                response = f"You said: {input_text}\n\nI'm a simple assistant that can use tools. Try asking me to calculate something, like '2 + 2'."
            
            accumulated_text = ""
            
            # CRITICAL: Always log the response for debugging
            logger.info(f"ASSISTANT RESPONSE TO STREAM: {response[:100]}...")
            
            # Simulate streaming by yielding one character at a time
            for char in response:
                if not self._is_running:
                    logger.info("Streaming interrupted")
                    break
                
                accumulated_text += char
                
                # Use the token callback if available - CRITICAL: always try to use it
                if on_token:
                    try:
                        # The on_token callback should handle its own async tasks
                        # Just call it directly
                        on_token(node_id, char, message_id)
                        
                        # Debug logging for every 20 characters
                        if len(accumulated_text) % 20 == 0:
                            logger.info(f"STREAMED {len(accumulated_text)} CHARS SO FAR")
                    except Exception as callback_error:
                        # If there's an error in the callback, log it but continue
                        logger.error(f"Error in token callback: {str(callback_error)}")
                else:
                    logger.warning(f"NO TOKEN CALLBACK AVAILABLE - tokens won't reach frontend!")
                
                yield char
                await asyncio.sleep(0.01)  # Small delay to simulate streaming
            
            # Debug logging for streaming completion
            logger.info(f"COMPLETED STREAMING {len(response)} CHARACTERS")
            
            # Create message completion info
            message_complete = {
                "id": message_id,
                "role": "assistant",
                "content": response,
                "timestamp": datetime.now().isoformat(),
                "node_id": node_id,
                "streaming_complete": True
            }
            
            # Log message completion
            logger.info(f"STREAM COMPLETED: message_id={message_id}")
            
            # We can't return, but we can yield one last special token
            yield "\n__STREAM_COMPLETE__"
                
        except Exception as e:
            logger.error(f"Error in SimpleAssistant.stream: {str(e)}")
            yield f"Error: {str(e)}"
        finally:
            self._is_running = False
            
    async def use_tool(self, tool_input: ToolInput, context: Dict[str, Any]) -> ToolOutput:
        """
        Use a tool and return the output.
        
        Args:
            tool_input: The input for the tool
            context: Additional context for processing
            
        Returns:
            The tool output
        """
        # Find the tool
        tool = None
        for t in self.available_tools:
            if t.name == tool_input.name:
                tool = t
                break
        
        if not tool:
            return ToolOutput(
                name=tool_input.name,
                output=f"Tool '{tool_input.name}' not found.",
                error=True
            )
        
        # Use the tool
        try:
            output = await tool.process(tool_input.arguments)
            return ToolOutput(
                name=tool_input.name,
                output=output
            )
        except Exception as e:
            return ToolOutput(
                name=tool_input.name,
                output=f"Error using tool: {str(e)}",
                error=True
            )
