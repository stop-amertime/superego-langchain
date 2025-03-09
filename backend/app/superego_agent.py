import logging
import asyncio
import os
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.messages import TextMessage
from autogen_core import CancellationToken
from autogen_ext.models.openai import OpenAIChatCompletionClient

from .models import SuperegoEvaluation, SuperegoDecision
from .agents import Agent
from .agent_instructions import load_instructions

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InputSuperego(Agent):
    """
    Input Superego agent that evaluates user inputs before they're processed.
    It screens inputs against a constitution to ensure compliance with guidelines.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.model = config.get("model", "anthropic/claude-3.7-sonnet:thinking")
        
        # Load the constitution content
        constitution_content = config.get("constitution", "")
        
        # Load the agent instructions
        instructions_content = load_instructions("input_superego")
        
        # Combine instructions and constitution into a single system prompt
        self.system_prompt = f"{instructions_content}\n\n## CONSTITUTION:\n\n{constitution_content}"
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        
        # Create the model client
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
            name="input_superego",
            model_client=self.model_client,
            system_message=self.system_prompt,
            model_client_stream=True
        )
        
        self._is_running = False
        logger.info(f"Initialized InputSuperego with model: {self.model}")
    
    async def evaluate_input(self, input_text: str) -> SuperegoEvaluation:
        """
        Evaluate user input for safety and ethics
        
        Args:
            input_text: The user input to evaluate
            
        Returns:
            SuperegoEvaluation with decision and reasoning
        """
        logger.info(f"Evaluating input with InputSuperego: {input_text[:50]}...")
        
        # Log the system prompt being used in a nicely formatted way
        logger.info("=" * 80)
        logger.info("SUPEREGO AGENT - EVALUATION REQUEST")
        logger.info("=" * 80)
        logger.info("FULL SYSTEM PROMPT (INSTRUCTIONS + CONSTITUTION):")
        logger.info("-" * 80)
        logger.info(self.system_prompt)
        logger.info("-" * 80)
        
        # Create a message to evaluate the input - keep it simple since instructions are in system prompt
        evaluation_prompt = f"""
        USER INPUT: {input_text}
        
        Evaluate this input according to your instructions and constitution.
        """
        
        logger.info("EVALUATION PROMPT:")
        logger.info("-" * 80)
        logger.info(evaluation_prompt)
        logger.info("-" * 80)
        logger.info("=" * 80)
        
        try:
            # Use the AutoGen agent to process the evaluation
            logger.info("Sending request to AutoGen agent...")
            response = await self.agent.on_messages(
                [TextMessage(content=evaluation_prompt, source="system")],
                CancellationToken()
            )
            
            # Parse the response to extract decision and reasoning
            response_text = response.chat_message.content
            logger.info("=" * 80)
            logger.info("SUPEREGO AGENT - EVALUATION RESPONSE")
            logger.info("=" * 80)
            logger.info(response_text)
            logger.info("=" * 80)
            
            # Default decision
            decision = SuperegoDecision.ALLOW
            reason = response_text
            
            # Try to parse the decision from the response
            if "DECISION: BLOCK" in response_text.upper():
                decision = SuperegoDecision.BLOCK
                logger.info("Parsed decision: BLOCK")
            elif "DECISION: CAUTION" in response_text.upper():
                decision = SuperegoDecision.CAUTION
                logger.info("Parsed decision: CAUTION")
            else:
                logger.info("Parsed decision: ALLOW")
            
            return SuperegoEvaluation(
                decision=decision,
                reason=reason,
                thinking=""  # We don't have access to thinking in this implementation
            )
            
        except Exception as e:
            logger.error(f"Error in InputSuperego evaluation: {str(e)}")
            return SuperegoEvaluation(
                decision=SuperegoDecision.ERROR,
                reason=f"Error evaluating input: {str(e)}",
                thinking=""
            )
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """Process input and return a complete response"""
        logger.info(f"Processing input with InputSuperego: {input_text[:50]}...")
        
        # Evaluate the input
        evaluation = await self.evaluate_input(input_text)
        
        # Return the evaluation as a formatted string
        return f"""
        DECISION: {evaluation.decision.value}
        
        REASON:
        {evaluation.reason}
        """
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """Stream the response token by token"""
        logger.info(f"Streaming response for input: {input_text[:50]}...")
        
        # Set running flag
        self._is_running = True
        
        try:
            # Evaluate the input
            evaluation = await self.evaluate_input(input_text)
            
            # Yield the evaluation as a formatted string
            result = f"""
            DECISION: {evaluation.decision.value}
            
            REASON:
            {evaluation.reason}
            """
            
            # Simulate streaming by yielding one character at a time
            for char in result:
                if not self._is_running:
                    logger.info("Streaming interrupted")
                    break
                yield char
                await asyncio.sleep(0.001)  # Small delay to simulate streaming
                
        except Exception as e:
            logger.error(f"Error in InputSuperego.stream: {str(e)}")
            yield f"Error: {str(e)}"
        finally:
            self._is_running = False
    
    async def interrupt(self) -> bool:
        """Interrupt the current processing"""
        if self._is_running:
            logger.info("Interrupting InputSuperego")
            self._is_running = False
            return True
        return False

# Register the InputSuperego with the factory
from .agents import AgentFactory
AgentFactory.register("input_superego", InputSuperego)
