import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from enum import Enum

from .agents import AgentFactory
from .models import SuperegoDecision, Message, MessageRole

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlowResult(Enum):
    """Result of a flow execution"""
    SUCCESS = "success"
    BLOCKED = "blocked"
    ERROR = "error"

class SuperegoFlow:
    """
    A flow that uses an InputSuperego agent to screen inputs before passing them to an AutoGen agent.
    This is a simple implementation of the flow architecture described in the refactoring plan.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the flow with the given configuration
        
        Args:
            config: Configuration for the flow, including:
                - input_superego_config: Configuration for the InputSuperego agent
                - autogen_config: Configuration for the AutoGen agent
        """
        self.config = config
        
        # Create the InputSuperego agent
        input_superego_config = config.get("input_superego_config", {})
        self.input_superego = AgentFactory.create("input_superego", input_superego_config)
        logger.info("Created InputSuperego agent for flow")
        
        # Create the AutoGen agent
        autogen_config = config.get("autogen_config", {})
        self.autogen = AgentFactory.create("autogen", autogen_config)
        logger.info("Created AutoGen agent for flow")
    
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
        logger.info(f"Processing input through SuperegoFlow: {input_text[:50]}...")
        
        try:
            # First, evaluate the input with the InputSuperego agent
            evaluation = await self.input_superego.evaluate_input(input_text)
            
            # If the input is blocked, return the blocked result
            if evaluation.decision == SuperegoDecision.BLOCK:
                logger.info(f"Input blocked by InputSuperego: {input_text[:50]}")
                return FlowResult.BLOCKED, f"""
                This input has been blocked by the Superego agent.
                
                Reason:
                {evaluation.reason}
                """
            
            # If the input is allowed or cautioned, process it with the AutoGen agent
            logger.info(f"Input {evaluation.decision.value} by InputSuperego, processing with AutoGen: {input_text[:50]}")
            
            # Add a note to the context if the input is cautioned
            if evaluation.decision == SuperegoDecision.CAUTION:
                context["superego_caution"] = evaluation.reason
            
            # Process the input with the AutoGen agent
            response = await self.autogen.process(input_text, context)
            
            return FlowResult.SUCCESS, response
            
        except Exception as e:
            logger.error(f"Error in SuperegoFlow.process: {str(e)}")
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
        logger.info(f"Streaming response for input through SuperegoFlow: {input_text[:50]}...")
        
        try:
            # First, evaluate the input with the InputSuperego agent
            evaluation = await self.input_superego.evaluate_input(input_text)
            
            # If the input is blocked, yield the blocked result
            if evaluation.decision == SuperegoDecision.BLOCK:
                logger.info(f"Input blocked by InputSuperego: {input_text[:50]}")
                blocked_response = f"""
                This input has been blocked by the Superego agent.
                
                Reason:
                {evaluation.reason}
                """
                for char in blocked_response:
                    yield FlowResult.BLOCKED, char
                    await asyncio.sleep(0.001)  # Small delay to simulate streaming
                return
            
            # If the input is allowed or cautioned, process it with the AutoGen agent
            logger.info(f"Input {evaluation.decision.value} by InputSuperego, streaming with AutoGen: {input_text[:50]}")
            
            # Add a note to the context if the input is cautioned
            if evaluation.decision == SuperegoDecision.CAUTION:
                context["superego_caution"] = evaluation.reason
            
            # Stream the response from the AutoGen agent
            async for token in self.autogen.stream(input_text, context):
                yield FlowResult.SUCCESS, token
                
        except Exception as e:
            logger.error(f"Error in SuperegoFlow.stream: {str(e)}")
            error_message = f"Error: {str(e)}"
            for char in error_message:
                yield FlowResult.ERROR, char
                await asyncio.sleep(0.001)  # Small delay to simulate streaming
