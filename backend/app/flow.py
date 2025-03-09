import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple, Union
from enum import Enum

from .graph import run_flow
from .models import SuperegoDecision, Message, MessageRole, SuperegoEvaluation
from langgraph.types import Command

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowResult(Enum):
    """Result of a flow execution"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    ERROR = "error"

class CommandFlow:
    """
    A flow that uses a Command-based system for routing between agents.
    
    This flow uses an InputSuperego agent to screen inputs before passing
    them to an Assistant agent that can use tools.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the flow with the given configuration
        
        Args:
            config: Configuration for the flow, including:
                - constitution_id: ID of the constitution to use
                - sysprompt_id: ID of the system prompt to use
                - skip_superego: Whether to skip the superego evaluation
        """
        self.config = config
        self.constitution_id = config.get("constitution_id", "default")
        self.sysprompt_id = config.get("sysprompt_id")
        self.skip_superego = config.get("skip_superego", False)
        
        logger.info(f"Created CommandFlow with constitution: {self.constitution_id}")
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> Tuple[FlowResult, str]:
        """
        Process the input through the flow
        
        Args:
            input_text: The user input to process
            context: Additional context for the processing
            
        Returns:
            A tuple of (result, response) where:
                - result: The result of the flow execution (SUCCESS, BLOCKED, ERROR)
                - response: The response from the flow
        """
        logger.info(f"Processing input through CommandFlow: {input_text[:50]}...")
        
        try:
            # Extract needed values from context
            conversation_id = context.get("conversation_id")
            messages = context.get("messages", [])
            on_token = context.get("on_token")
            on_thinking = context.get("on_thinking")
            
            # Run the flow
            result = await run_flow(
                user_input=input_text,
                conversation_id=conversation_id,
                messages=messages,
                constitution_id=self.constitution_id,
                sysprompt_id=self.sysprompt_id,
                on_token=on_token,
                on_thinking=on_thinking,
                skip_superego=self.skip_superego
            )
            
            # Determine the result type
            superego_evaluation = result.get("superego_evaluation")
            if superego_evaluation and superego_evaluation.decision == SuperegoDecision.BLOCK:
                return FlowResult.BLOCKED, superego_evaluation.reason
            
            # Get the assistant response
            assistant_response = result.get("assistant_response", "")
            
            return FlowResult.SUCCESS, assistant_response
            
        except Exception as e:
            logger.error(f"Error in CommandFlow.process: {str(e)}")
            return FlowResult.ERROR, f"Error: {str(e)}"
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[Tuple[FlowResult, str], None]:
        """
        Stream the response from the flow
        
        Args:
            input_text: The user input to process
            context: Additional context for the processing
            
        Yields:
            Tuples of (result, token) where:
                - result: The result of the flow execution (SUCCESS, BLOCKED, ERROR)
                - token: A token from the response
        """
        logger.info(f"Streaming response for input through CommandFlow: {input_text[:50]}...")
        
        # For now, we'll just process the input and stream the result character by character
        # In a real implementation, we would use the streaming capabilities of the agents
        
        try:
            # Process the input
            result, response = await self.process(input_text, context)
            
            # Stream the response
            for char in response:
                yield result, char
                await asyncio.sleep(0.001)  # Small delay to simulate streaming
                
        except Exception as e:
            logger.error(f"Error in CommandFlow.stream: {str(e)}")
            error_message = f"Error: {str(e)}"
            for char in error_message:
                yield FlowResult.ERROR, char
                await asyncio.sleep(0.001)  # Small delay to simulate streaming
