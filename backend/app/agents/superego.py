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
) -> Tuple[str, str, str, str]:
    """Evaluate an input message against a constitution
    
    Args:
        llm: Language model for evaluation
        input_message: The user's input
        constitution: The constitution text to evaluate against
        
    Returns:
        Tuple of (decision, agent_guidance, thinking, response)
    """
    import logging
    logger = logging.getLogger("uvicorn")
    
    # Create output parser
    parser = PydanticOutputParser(pydantic_object=SuperegoOutput)
    
    # Get format instructions
    format_instructions = parser.get_format_instructions()
    
    # Create prompt without concatenating format_instructions directly
    template = SUPEREGO_PROMPT + "\n\nOutput Format Instructions:\n{format_instructions}"
    prompt = ChatPromptTemplate.from_template(template)
    
    # Format prompt with all parameters
    messages = prompt.format_messages(
        constitution=constitution,
        input_message=input_message,
        agent_id="superego",
        format_instructions=format_instructions
    )
    
    logger.info("Prompt formatted successfully")
    
    # Call LLM
    response = await llm.ainvoke(messages)
    result = parser.parse(response.content)
    
    # Validate decision
    valid_decisions = [BLOCK, ACCEPT, CAUTION, NEEDS_CLARIFICATION]
    if result.decision not in valid_decisions:
        result.decision = CAUTION
        result.agent_guidance += " (Note: Invalid decision was corrected to CAUTION)"
    
    return result.decision, result.agent_guidance, result.thinking, result.response


async def create_superego_step(
    prev_step: Dict[str, Any],
    agent_id: str,
    decision: str,
    agent_guidance: str,
    thinking: str,
    user_message: str,
    ai_response: str
) -> FlowStep:
    """Create a superego step from evaluation results
    
    Args:
        prev_step: Previous step in the flow
        agent_id: Identifier for this superego agent
        decision: Evaluation decision (BLOCK, ACCEPT, etc.)
        agent_guidance: Hidden context for next agent
        thinking: Reasoning process
        user_message: Original user message
        ai_response: Response from the LLM evaluation
        
    Returns:
        Complete FlowStep
    """
    # Determine next agent based on decision, but use AI's response text
    next_agent = None
    
    if decision == BLOCK:
        next_agent = None
    elif decision in [ACCEPT, CAUTION, NEEDS_CLARIFICATION]:
        # Keep existing logic for NEEDS_CLARIFICATION
        next_agent = "inner_agent"  # Default, will be overridden by flow router
    
    # Create step with AI response
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
        response=ai_response,  # Use the AI-generated response
        next_agent=next_agent
    )


async def create_superego_node(
    llm: BaseChatModel,
    agent_id: str = "superego",
    max_iterations: int = 3,
    constitution: Optional[str] = None
) -> callable:
    """Create a langgraph-compatible superego node function
    
    Args:
        llm: The language model to use
        agent_id: Identifier for this agent
        max_iterations: Maximum number of iterations
        constitution: Constitution text to evaluate against
        
    Returns:
        Langgraph-compatible node function
    """
    async def superego_node_fn(state):
        """Node function for LangGraph that processes the state"""
        import logging
        logger = logging.getLogger("uvicorn")
        
        logger.info(f"Superego node called with state type: {type(state).__name__}")
        
        flow_record = state.flow_record
        prev_step = flow_record[-1] if flow_record else {}
        user_message = prev_step.get("response", "")
        constitution_text = constitution or prev_step.get("constitution", "")
        
        logger.info(f"Evaluating user message: '{user_message[:50]}...' against constitution")
        
        # Stream partial outputs to show we're working
        # First, emit a message that we're processing
        initial_chunk = StreamChunk(
            partial_output="Evaluating your message...",
            complete=False
        )
        logger.debug(f"Yielding initial streaming chunk: {initial_chunk}")
        yield initial_chunk
        
        # Evaluate the input
        decision, agent_guidance, thinking, ai_response = await superego_evaluate(
            llm, user_message, constitution_text
        )
        
        logger.info(f"Superego decision: {decision}")
        logger.debug(f"AI generated response: {ai_response}")
        
        # Send the actual AI response as a stream chunk 
        response_chunk = StreamChunk(
            partial_output=ai_response,
            complete=False
        )
        logger.debug(f"Yielding response streaming chunk: {response_chunk}")
        yield response_chunk
        
        # Create the step, passing AI's response
        step = await create_superego_step(
            prev_step, agent_id, decision, agent_guidance, 
            thinking, user_message, ai_response
        )
        
        # Convert step to dictionary
        step_dict = step.dict()
        
        # Log the step being returned
        logger.info(f"Superego step created with ID: {step.step_id}, next_agent: {step.next_agent}")
        
        # Final yield with the complete flow record state
        logger.debug(f"Yielding final state update with response: {step.response}")
        yield {
            "flow_record": flow_record + [step_dict],
            "instance_id": state.instance_id  # Preserve the instance_id
        }
    
    return superego_node_fn
