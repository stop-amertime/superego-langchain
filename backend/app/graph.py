import uuid
import logging
from typing import Dict, List, Any, Optional, TypedDict, Callable
from datetime import datetime

from langgraph.graph import StateGraph, END
from pydantic import Field

from .models import Message, MessageRole, SuperegoEvaluation, SuperegoDecision
from .llm_client import get_llm_client
from .agents import get_all_constitutions, get_default_constitution

# Set up logging
logger = logging.getLogger(__name__)

# Define the state schema
class GraphState(TypedDict):
    """State for the LangGraph agent"""
    conversation_id: str
    messages: List[Message]
    current_user_input: str
    constitution_id: str
    sysprompt_id: Optional[str]
    superego_evaluation: Optional[SuperegoEvaluation]
    assistant_response: Optional[str]
    streaming_handlers: Dict[str, Any]
    checkpoint_id: Optional[str]
    processed: bool  # Track if we've already processed this input to prevent loops

# Store checkpoints for rerunning
checkpoints: Dict[str, GraphState] = {}

# Store message to checkpoint mapping for easier rerunning
message_checkpoints: Dict[str, str] = {}

# Define the superego node
async def superego_node(state: GraphState) -> GraphState:
    """Superego evaluation node"""
    logger.info("Running superego node")
    
    # Prevent infinite loops by checking processed flag
    if state.get("processed", False):
        logger.info("Input already processed, skipping superego evaluation")
        return state
    
    # Mark as processed immediately
    state["processed"] = True
    
    # Extract needed values from state
    user_input = state["current_user_input"]
    messages = state["messages"]
    constitution_id = state["constitution_id"]
    on_thinking = state["streaming_handlers"].get("on_thinking")
    
    # Get the constitution content
    constitutions = get_all_constitutions()
    constitution_content = constitutions.get(constitution_id, {}).get("content") or get_default_constitution()
    
    # Get the superego evaluation
    llm_client = get_llm_client()
    evaluation = await llm_client.get_superego_evaluation(
        user_input=user_input,
        constitution=constitution_content,
        messages=messages,
        on_thinking=on_thinking
    )
    
    # Add the constitution ID to the evaluation
    evaluation.constitutionId = constitution_id
    
    # Handle error case
    if evaluation.decision == SuperegoDecision.ERROR:
        logger.warning("Superego evaluation failed, defaulting to ALLOW")
        evaluation = SuperegoEvaluation(
            decision=SuperegoDecision.ALLOW,
            reason="Evaluation could not be completed, defaulting to ALLOW.",
            thinking="Thinking process unavailable due to evaluation error."
        )
    
    logger.info(f"Superego evaluation complete: {evaluation.decision}")
    
    # Create a checkpoint for this state
    checkpoint_id = str(uuid.uuid4())
    checkpoints[checkpoint_id] = state.copy()
    
    # Find the user message ID to associate with this checkpoint
    for msg in state["messages"]:
        if msg.role == MessageRole.USER and msg.content == state["current_user_input"]:
            message_checkpoints[msg.id] = checkpoint_id
            logger.info(f"Associated message {msg.id} with checkpoint {checkpoint_id}")
            break
    
    # Return updated state
    return {
        **state,
        "superego_evaluation": evaluation,
        "checkpoint_id": checkpoint_id
    }

# Define the assistant node
async def assistant_node(state: GraphState) -> GraphState:
    """Assistant response node"""
    logger.info("Running assistant node")
    
    # Extract needed values from state
    user_input = state["current_user_input"]
    messages = state["messages"]
    superego_evaluation = state["superego_evaluation"]
    sysprompt_id = state["sysprompt_id"]
    on_token = state["streaming_handlers"].get("on_token")
    
    # Determine the response based on superego decision
    if superego_evaluation.decision == SuperegoDecision.BLOCK:
        # For BLOCK decisions, create a blocked response without calling the LLM
        logger.info("Superego BLOCKED the message. Generating blocked response.")
        assistant_content = (
            "I apologize, but I cannot provide a response to that message. " +
            "Our content review system has determined that it may not be appropriate. " +
            f"Reason: {superego_evaluation.reason or 'Not specified'}"
        )
    else:
        # For ALLOW or CAUTION, get the LLM response
        llm_client = get_llm_client()
        content = ""
        async for token in llm_client.stream_llm_response(
            user_input=user_input,
            messages=messages,
            superego_evaluation=superego_evaluation,
            sysprompt_id=sysprompt_id
        ):
            content += token
            
            # Call the token callback if provided
            if on_token:
                await on_token(token)
        
        # For CAUTION, add a prefix to the LLM response
        if superego_evaluation.decision == SuperegoDecision.CAUTION:
            assistant_content = (
                "**Note:** I'm providing this information with caution.\n" +
                f"The content review system flagged potential concerns: {superego_evaluation.reason or 'Unspecified'}\n\n" +
                content
            )
        else:  # ALLOW
            assistant_content = content
    
    # Return updated state
    return {
        **state,
        "assistant_response": assistant_content
    }

# Create and initialize the graph
def create_graph():
    """Create the LangGraph for the superego flow"""
    builder = StateGraph(GraphState)
    builder.add_node("superego", superego_node)
    builder.add_node("assistant", assistant_node)
    builder.add_edge("superego", "assistant")
    builder.add_edge("assistant", END)
    builder.set_entry_point("superego")
    return builder.compile()

agent_graph = create_graph()

# Helper function to filter messages
def filter_user_messages(messages: List[Message]) -> List[Message]:
    """Filter to keep only user messages to prevent loops"""
    return [msg for msg in messages if msg.role == MessageRole.USER]

# Function to run the graph
async def run_graph(
    user_input: str,
    conversation_id: Optional[str] = None,
    messages: Optional[List[Message]] = None,
    constitution_id: Optional[str] = None,
    sysprompt_id: Optional[str] = None,
    on_token: Optional[Callable[[str], None]] = None,
    on_thinking: Optional[Callable[[str], None]] = None,
    checkpoint_node: Optional[str] = None,
    skip_superego: bool = False
) -> Dict[str, Any]:
    """Run the graph with the given inputs"""
    # Initialize parameters with defaults if not provided
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    if messages is None:
        messages = []
    
    # Filter out superego/assistant messages to prevent loops
    user_messages = filter_user_messages(messages)
    
    # Add current user input as a message if not already present
    if not any(msg.content == user_input for msg in user_messages):
        user_message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=user_input,
            timestamp=datetime.now().isoformat()
        )
        user_messages.append(user_message)
    
    # Set up streaming handlers
    streaming_handlers = {}
    if on_token:
        streaming_handlers["on_token"] = on_token
    if on_thinking:
        streaming_handlers["on_thinking"] = on_thinking
    
    # Initialize the state
    state: GraphState = {
        "conversation_id": conversation_id,
        "messages": user_messages,
        "current_user_input": user_input,
        "constitution_id": constitution_id or "default",
        "sysprompt_id": sysprompt_id,
        "superego_evaluation": None,
        "assistant_response": None,
        "streaming_handlers": streaming_handlers,
        "checkpoint_id": None,
        "processed": False
    }
    
    # Run the graph
    config = {}
    if checkpoint_node:
        config = {"configurable": {"checkpoint_node": checkpoint_node}}
    
    # If skipping superego, set entry point to assistant node directly
    if skip_superego:
        # Create a "fake" superego evaluation that always allows
        state["superego_evaluation"] = SuperegoEvaluation(
            decision=SuperegoDecision.ALLOW,
            reason="Superego evaluation skipped",
            thinking="Superego evaluation was explicitly skipped for this flow.",
            constitutionId=constitution_id
        )
        # Start from assistant node
        config["configurable"] = config.get("configurable", {})
        config["configurable"]["entry_point"] = "assistant"
    
    result = await agent_graph.ainvoke(state, config)
    
    # Create output messages
    superego_message = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.SUPEREGO,
        content=result["superego_evaluation"].reason,
        timestamp=datetime.now().isoformat(),
        decision=result["superego_evaluation"].decision.value,
        thinking=result["superego_evaluation"].thinking,
        constitutionId=result["superego_evaluation"].constitutionId
    )
    
    assistant_message = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.ASSISTANT,
        content=result["assistant_response"],
        timestamp=datetime.now().isoformat()
    )
    
    # Combine messages
    updated_messages = user_messages.copy()
    updated_messages.append(superego_message)
    updated_messages.append(assistant_message)
    
    # Return the result
    return {
        "conversation_id": conversation_id,
        "messages": updated_messages,
        "superego_evaluation": result["superego_evaluation"],
        "assistant_message": assistant_message,
        "checkpoint_id": result["checkpoint_id"]
    }

# Function to rerun from a checkpoint
async def rerun_from_checkpoint(
    checkpoint_id: str,
    constitution_id: str,
    sysprompt_id: Optional[str] = None,
    on_token: Optional[Callable[[str], None]] = None,
    on_thinking: Optional[Callable[[str], None]] = None
) -> Dict[str, Any]:
    """Rerun the graph from a checkpoint with a different constitution and/or system prompt"""
    original_checkpoint_id = checkpoint_id
    
    # Check if the ID is a message ID first
    if checkpoint_id in message_checkpoints:
        logger.info(f"Found message checkpoint mapping: {checkpoint_id} -> {message_checkpoints[checkpoint_id]}")
        checkpoint_id = message_checkpoints[checkpoint_id]
    
    # Validate checkpoint exists
    if checkpoint_id not in checkpoints:
        logger.error(f"Checkpoint {checkpoint_id} not found (original ID: {original_checkpoint_id})")
        # Check if any checkpoints exist at all
        if len(checkpoints) == 0:
            logger.error("No checkpoints exist in the system")
        else:
            logger.info(f"Available checkpoint IDs: {list(checkpoints.keys())}")
        
        raise ValueError(f"Checkpoint {checkpoint_id} not found. The session may have expired or the server was restarted.")
    
    # Get the checkpoint and create a fresh state
    checkpoint = checkpoints[checkpoint_id].copy()
    
    # Create a fresh state with the new constitution
    fresh_state: GraphState = {
        "conversation_id": checkpoint["conversation_id"],
        "messages": checkpoint["messages"].copy(),
        "current_user_input": checkpoint["current_user_input"],
        "constitution_id": constitution_id,  # Use the new constitution ID
        "sysprompt_id": checkpoint["sysprompt_id"],
        "superego_evaluation": None,  # Reset to force re-evaluation
        "assistant_response": None,  # Reset to force re-generation
        "streaming_handlers": {},  # Will update below
        "checkpoint_id": None,
        "processed": False  # Reset to ensure processing
    }
    
    # Set up streaming handlers
    if on_token:
        fresh_state["streaming_handlers"]["on_token"] = on_token
    if on_thinking:
        fresh_state["streaming_handlers"]["on_thinking"] = on_thinking
    
    # Copy any other handlers from original checkpoint
    for key, handler in checkpoint["streaming_handlers"].items():
        if key not in fresh_state["streaming_handlers"]:
            fresh_state["streaming_handlers"][key] = handler
    
    # Run the graph with the fresh state
    result = await agent_graph.ainvoke(fresh_state)
    
    # Create output messages
    superego_message = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.SUPEREGO,
        content=result["superego_evaluation"].reason,
        timestamp=datetime.now().isoformat(),
        decision=result["superego_evaluation"].decision.value,
        thinking=result["superego_evaluation"].thinking,
        constitutionId=result["superego_evaluation"].constitutionId
    )
    
    assistant_message = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.ASSISTANT,
        content=result["assistant_response"],
        timestamp=datetime.now().isoformat()
    )
    
    # Get user messages from original checkpoint
    user_messages = filter_user_messages(checkpoint["messages"])
    
    # Create updated message list
    updated_messages = user_messages.copy()
    updated_messages.append(superego_message)
    updated_messages.append(assistant_message)
    
    # Return the result
    return {
        "conversation_id": checkpoint["conversation_id"],
        "messages": updated_messages,
        "superego_evaluation": result["superego_evaluation"],
        "assistant_message": assistant_message,
        "checkpoint_id": result["checkpoint_id"]
    }
