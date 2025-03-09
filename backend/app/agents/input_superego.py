"""
Input Superego agent implementation.

This module provides a concrete implementation of the InputSuperego agent
that evaluates user inputs against a constitution.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, AsyncGenerator, Union

from langgraph.types import Command

from ..models import SuperegoEvaluation, SuperegoDecision
from .base import InputSuperego, AgentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleInputSuperego(InputSuperego):
    """
    Simple implementation of the Input Superego agent.
    
    This agent evaluates user inputs against a constitution and returns
    a Command object to route the flow based on the evaluation result.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the simple input superego agent.
        
        Args:
            config: Configuration for the agent, including:
                - constitution: The constitution/guidelines for evaluation
        """
        super().__init__(config)
    
    async def evaluate(self, content: str, context: Dict[str, Any]) -> SuperegoEvaluation:
        """
        Evaluate user input against the constitution.
        
        Args:
            content: The user input to evaluate
            context: Additional context for evaluation
            
        Returns:
            SuperegoEvaluation with decision and reasoning
        """
        # This is a simple implementation that just checks for keywords
        # In a real implementation, this would use an LLM to evaluate the input
        
        # Check for harmful content
        harmful_keywords = ["bomb", "kill", "murder", "suicide", "terrorist", "hack", "steal"]
        for keyword in harmful_keywords:
            if keyword in content.lower():
                return SuperegoEvaluation(
                    decision=SuperegoDecision.BLOCK,
                    reason=f"Your request contains potentially harmful content ({keyword})."
                )
        
        # Check for sensitive content
        sensitive_keywords = ["sex", "nude", "porn", "drug", "illegal"]
        for keyword in sensitive_keywords:
            if keyword in content.lower():
                return SuperegoEvaluation(
                    decision=SuperegoDecision.CAUTION,
                    reason=f"Your request contains sensitive content ({keyword}). I'll proceed with caution."
                )
        
        # Default to allowing the request
        return SuperegoEvaluation(
            decision=SuperegoDecision.ALLOW,
            reason="Your request appears to be safe and appropriate."
        )
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> Union[str, Command]:
        """
        Process input and return a Command object for routing.
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Returns:
            A Command object for routing the flow
        """
        # Evaluate the input
        evaluation = await self.evaluate(input_text, context)
        
        # Create a Command object based on the evaluation
        if evaluation.decision == SuperegoDecision.BLOCK:
            # If blocked, go to END
            return Command(
                goto="END",
                update={
                    "superego_evaluation": evaluation,
                    "blocked_reason": evaluation.reason
                }
            )
        elif evaluation.decision == SuperegoDecision.CAUTION:
            # If caution, go to assistant with caution message
            return Command(
                goto="assistant",
                update={
                    "superego_evaluation": evaluation,
                    "caution_message": evaluation.reason
                }
            )
        else:
            # If allowed, go to assistant
            return Command(
                goto="assistant",
                update={
                    "superego_evaluation": evaluation
                }
            )
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream the response token by token.
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Yields:
            Tokens from the response
        """
        # This is not typically used for InputSuperego in the flow system
        # as it returns a Command object instead
        evaluation = await self.evaluate(input_text, context)
        result = f"Decision: {evaluation.decision.value}\nReason: {evaluation.reason}"
        
        for char in result:
            yield char
            await asyncio.sleep(0.001)
