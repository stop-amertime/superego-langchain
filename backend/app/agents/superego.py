"""
Superego Agent Implementation

Core functionality for evaluating messages against constitution values,
making decisions, and providing guidance to inner agents.
"""

import asyncio
from typing import AsyncGenerator, Dict, List, Tuple, Any, Optional
from datetime import datetime
import uuid

from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from ..models import FlowStep, StreamChunk
from .commands import BLOCK, ACCEPT, CAUTION, NEEDS_CLARIFICATION
from .prompts import SUPEREGO_PROMPT


class SuperegoOutput(BaseModel):
    """Structured output from superego evaluation"""
    thinking: str = Field(description="Detailed reasoning process (not shown to user)")
    decision: str = Field(description="One of ACCEPT, BLOCK, CAUTION, NEEDS_CLARIFICATION")
    agent_guidance: str = Field(description="Hidden context for the next agent")
    response: str = Field(description="Brief user-facing explanation of the decision")


async def superego_evaluate(
    llm: BaseChatModel,
    input_message: str, 
    constitution: str
) -> Tuple[str, str, str]:
    """Evaluate an input message against a constitution
    
    Args:
        llm: Language model for evaluation
        input_message: The user's input
        constitution: The constitution text to evaluate against
        
    Returns:
        Tuple of (decision, agent_guidance, thinking)
    """
    # Create output parser
    parser = PydanticOutputParser(pydantic_object=SuperegoOutput)
    
    # Create prompt
    prompt = ChatPromptTemplate.from_template(
        SUPEREGO_PROMPT + "\n\n" + parser.get_format_instructions()
    )
    
    # Format prompt
    messages = prompt.format_messages(
        constitution=constitution,
        input_message=input_message,
        agent_id="superego"
    )
    
    # Call LLM
    response = await llm.ainvoke(messages)
    result = parser.parse(response.content)
    
    # Validate decision
    valid_decisions = [BLOCK, ACCEPT, CAUTION, NEEDS_CLARIFICATION]
    if result.decision not in valid_decisions:
        result.decision = CAUTION
        result.agent_guidance += " (Note: Invalid decision was corrected to CAUTION)"
    
    return result.decision, result.agent_guidance, result.thinking


async def create_superego_step(
    prev_step: Dict[str, Any],
    agent_id: str,
    decision: str,
    agent_guidance: str,
    thinking: str,
    user_message: str
) -> FlowStep:
    """Create a superego step from evaluation results
    
    Args:
        prev_step: Previous step in the flow
        agent_id: Identifier for this superego agent
        decision: Evaluation decision (BLOCK, ACCEPT, etc.)
        agent_guidance: Hidden context for next agent
        thinking: Reasoning process
        user_message: Original user message
        
    Returns:
        Complete FlowStep
    """
    # Determine next agent based on decision
    next_agent = None
    response = ""
    
    if decision == BLOCK:
        response = "I'm unable to help with that request."
        next_agent = None
    elif decision in [ACCEPT, CAUTION]:
        response = "I'll help with that."
        # Next agent will be determined by the flow definition
        next_agent = "inner_agent"  # Default, will be overridden by flow router
    elif decision == NEEDS_CLARIFICATION:
        response = "Could you provide more information?"
        next_agent = agent_id  # Loop back to self for clarification
    
    # Create step
    return FlowStep(
        step_id=str(uuid.uuid4()),
        agent_id=agent_id,
        timestamp=datetime.now().isoformat(),
        role="assistant",
        input=user_message,
        constitution=prev_step.get("constitution", ""),
        thinking=thinking,
        decision=decision,
        agent_guidance=agent_guidance,
        response=response,
        next_agent=next_agent
    )


async def create_superego_node(
    llm: BaseChatModel,
    agent_id: str = "superego"
) -> callable:
    """Create a langgraph-compatible superego node function
    
    Args:
        llm: The language model to use
        agent_id: Identifier for this agent
        
    Returns:
        Async generator function that streams results
    """
    async def superego_node(
        state: Dict[str, Any]
    ) -> AsyncGenerator[StreamChunk, None]:
        """Superego node function that evaluates inputs and streams results"""
        # Get the most recent user message
        steps = state.get("steps", [])
        prev_step = steps[-1] if steps else {}
        user_message = prev_step.get("response", "")
        constitution = prev_step.get("constitution", "")
        
        # Early yield of processing message
        yield StreamChunk(
            partial_output="Evaluating input against constitution...",
            complete=False
        )
        
        # Evaluate the input
        decision, agent_guidance, thinking = await superego_evaluate(
            llm, user_message, constitution
        )
        
        # Create the step
        step = await create_superego_step(
            prev_step, agent_id, decision, agent_guidance, 
            thinking, user_message
        )
        
        # Create final streaming chunk with complete step
        yield StreamChunk(
            partial_output=step.response,
            complete=True,
            flow_step=step
        )
    
    return superego_node
