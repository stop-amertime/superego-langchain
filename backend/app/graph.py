import uuid
import os
import logging
from typing import Dict, List, Any, Optional, TypedDict, Callable, Union, Literal
from datetime import datetime

from langgraph.types import Command
from .models import Message, MessageRole, SuperegoEvaluation, SuperegoDecision, ToolInput, ToolOutput
from .tools import get_tool
from .constitution_registry import ConstitutionRegistry
from .agents.input_superego import SimpleInputSuperego
from .agents.assistant import SimpleAssistant

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to constitutions directory
CONSTITUTIONS_DIR = os.path.join(os.path.dirname(__file__), "data", "constitutions")

# Initialize the constitution registry
constitution_registry = ConstitutionRegistry(CONSTITUTIONS_DIR)

# Default constitution ID
DEFAULT_CONSTITUTION_ID = "default"

# Get all available constitutions
def get_all_constitutions() -> Dict[str, Dict[str, Any]]:
    """Get all available constitutions"""
    return constitution_registry.get_all_constitutions()

# Get a constitution by ID
def get_constitution(constitution_id: str) -> str:
    """
    Get a constitution by ID
    
    Args:
        constitution_id: The ID of the constitution to get
        
    Returns:
        The constitution content
        
    Raises:
        ValueError: If the constitution is not found
    """
    constitution = constitution_registry.get_constitution(constitution_id)
    if not constitution:
        raise ValueError(f"Constitution not found: {constitution_id}")
    return constitution["content"]

# Define the state schema
class GraphState(TypedDict):
    """State for the flow system"""
    conversation_id: str
    messages: List[Message]
    user_input: str
    constitution_id: str
    sysprompt_id: Optional[str]
    superego_evaluation: Optional[SuperegoEvaluation]
    assistant_response: Optional[str]
    tools_used: List[Dict[str, Any]]
    on_token: Optional[Callable[[str], None]]
    on_thinking: Optional[Callable[[str], None]]

# Special node names
START = "START"
END = "END"

# Create agent instances
input_superego = SimpleInputSuperego({
    "constitution": "default"
})

assistant = SimpleAssistant({
    "system_prompt": "You are a helpful AI assistant that can use tools.",
    "available_tools": ["calculator"]
})

# Define the superego node
async def superego_node(state: GraphState) -> Union[GraphState, Command]:
    """
    Superego evaluation node
    
    This node evaluates the user input against the constitution and
    returns a Command object to route the flow based on the evaluation.
    """
    logger.info("Running superego node")
    
    # Extract needed values from state
    user_input = state["user_input"]
    messages = state["messages"]
    constitution_id = state["constitution_id"]
    on_thinking = state["on_thinking"]
    
    # Get the constitution content
    try:
        constitution_content = get_constitution(constitution_id)
    except ValueError as e:
        # If the constitution is not found, raise an error
        logger.error(f"Error getting constitution: {e}")
        raise
    
    # Update the input superego's constitution
    input_superego.constitution = constitution_content
    
    # Create context for the superego
    context = {
        "messages": messages,
        "constitution_id": constitution_id,
        "on_thinking": on_thinking
    }
    
    # Process the input with the superego
    result = await input_superego.process(user_input, context)
    
    # If the result is a Command object, return it
    if isinstance(result, Command):
        # Add the superego evaluation to the state
        if "superego_evaluation" in result.update:
            state["superego_evaluation"] = result.update["superego_evaluation"]
            
            # Create a superego message
            superego_message = Message(
                id=str(uuid.uuid4()),
                role=MessageRole.SUPEREGO,
                content=result.update["superego_evaluation"].reason,
                timestamp=datetime.now().isoformat(),
                decision=result.update["superego_evaluation"].decision.value,
                thinking=result.update["superego_evaluation"].thinking,
                constitutionId=constitution_id
            )
            
            # Add the message to the state
            state["messages"] = state["messages"] + [superego_message]
        
        # Return the Command object
        return result
    
    # If the result is not a Command object, return the updated state
    return state

# Define the assistant node
async def assistant_node(state: GraphState) -> Union[GraphState, Command]:
    """
    Assistant node
    
    This node processes the user input and returns a response.
    It can use tools to help generate the response.
    """
    logger.info("Running assistant node")
    
    # Extract needed values from state
    user_input = state["user_input"]
    messages = state["messages"]
    superego_evaluation = state["superego_evaluation"]
    on_token = state["on_token"]
    
    # Create context for the assistant
    context = {
        "messages": messages,
        "superego_evaluation": superego_evaluation,
        "on_token": on_token
    }
    
    # Check if there's a caution message
    if superego_evaluation and superego_evaluation.decision == SuperegoDecision.CAUTION:
        context["caution_message"] = superego_evaluation.reason
    
    # Process the input with the assistant
    response = await assistant.process(user_input, context)
    
    # Create an assistant message
    assistant_message = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.ASSISTANT,
        content=response,
        timestamp=datetime.now().isoformat()
    )
    
    # Add the message to the state
    state["messages"] = state["messages"] + [assistant_message]
    state["assistant_response"] = response
    
    # Return a Command to end the flow
    return Command(
        goto=END,
        update=state
    )

# Function to run the flow
async def run_flow(
    user_input: str,
    conversation_id: Optional[str] = None,
    messages: Optional[List[Message]] = None,
    constitution_id: Optional[str] = None,
    sysprompt_id: Optional[str] = None,
    on_token: Optional[Callable[[str], None]] = None,
    on_thinking: Optional[Callable[[str], None]] = None,
    skip_superego: bool = False
) -> Dict[str, Any]:
    """
    Run the flow with the given inputs
    
    Args:
        user_input: The user input to process
        conversation_id: Optional conversation ID
        messages: Optional list of messages
        constitution_id: Optional constitution ID
        sysprompt_id: Optional system prompt ID
        on_token: Optional callback for tokens
        on_thinking: Optional callback for thinking
        skip_superego: Whether to skip the superego evaluation
        
    Returns:
        The result of the flow
    """
    # Initialize parameters with defaults if not provided
    if conversation_id is None:
        conversation_id = str(uuid.uuid4())
    if messages is None:
        messages = []
    
    # Add current user input as a message if not already present
    user_message = Message(
        id=str(uuid.uuid4()),
        role=MessageRole.USER,
        content=user_input,
        timestamp=datetime.now().isoformat()
    )
    messages = messages + [user_message]
    
    # Initialize the state
    state: GraphState = {
        "conversation_id": conversation_id,
        "messages": messages,
        "user_input": user_input,
        "constitution_id": constitution_id or DEFAULT_CONSTITUTION_ID,
        "sysprompt_id": sysprompt_id,
        "superego_evaluation": None,
        "assistant_response": None,
        "tools_used": [],
        "on_token": on_token,
        "on_thinking": on_thinking
    }
    
    # Run the flow
    if skip_superego:
        # Create a superego evaluation that always allows
        state["superego_evaluation"] = SuperegoEvaluation(
            decision=SuperegoDecision.ALLOW,
            reason="Superego evaluation skipped",
            thinking="Superego evaluation was explicitly skipped for this flow.",
            constitutionId=constitution_id
        )
        
        # Run the assistant node directly
        result = await assistant_node(state)
    else:
        # Run the superego node
        result = await superego_node(state)
        
        # If the result is a Command object, follow it
        if isinstance(result, Command):
            if result.goto == "assistant":
                # Update the state with the Command's updates
                for key, value in result.update.items():
                    state[key] = value
                
                # Run the assistant node
                result = await assistant_node(state)
            elif result.goto == END:
                # End the flow
                pass
        
    # Return the final state
    return {
        "conversation_id": state["conversation_id"],
        "messages": state["messages"],
        "superego_evaluation": state["superego_evaluation"],
        "assistant_response": state["assistant_response"],
        "tools_used": state["tools_used"]
    }

# Function to process a calculator request
async def process_calculator_request(expression: str) -> str:
    """
    Process a calculator request
    
    Args:
        expression: The expression to calculate
        
    Returns:
        The result of the calculation
    """
    calculator = get_tool("calculator")
    if not calculator:
        return "Calculator tool not available"
    
    tool_input = ToolInput(name="calculator", arguments={"expression": expression})
    result = await calculator.execute(tool_input.arguments)
    
    return result
