import os
import json
import logging
import re
from typing import List, Dict, Any, Optional, Callable, AsyncGenerator
from openai import AsyncOpenAI
from dotenv import load_dotenv

from .models import Message, MessageRole, SuperegoDecision, SuperegoEvaluation

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get OpenRouter API key from environment
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    logger.warning("OPENROUTER_API_KEY not set in environment variables")

# Get model names from environment
BASE_MODEL = os.getenv("BASE_MODEL", "anthropic/claude-3.7-sonnet")
SUPEREGO_MODEL = os.getenv("SUPEREGO_MODEL", "anthropic/claude-3.7-sonnet:thinking")

# Path to system prompts file
SYSPROMPTS_FILE = os.path.join(os.path.dirname(__file__), "data", "sysprompts.json")

# Load system prompts from JSON file
def load_sysprompts():
    """Load system prompts from the JSON file"""
    try:
        with open(SYSPROMPTS_FILE, 'r') as f:
            data = json.load(f)
            return {prompt["id"]: prompt for prompt in data.get("prompts", [])}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading system prompts: {e}")
        return {}

# Load all system prompts
ALL_SYSPROMPTS = load_sysprompts()

# Default system prompt ID
DEFAULT_SYSPROMPT_ID = "assistant_default"

# Get the default system prompt content
def get_default_sysprompt():
    """Get the default system prompt content"""
    if DEFAULT_SYSPROMPT_ID in ALL_SYSPROMPTS:
        return ALL_SYSPROMPTS[DEFAULT_SYSPROMPT_ID]["content"]
    else:
        # Fallback if default system prompt is not found
        logger.warning(f"Default system prompt '{DEFAULT_SYSPROMPT_ID}' not found. Using fallback.")
        return "You are a helpful AI assistant with a Superego mechanism that evaluates user requests."

class LLMClient:
    """Client for interacting with LLMs through OpenRouter API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the LLM client with the OpenRouter API key"""
        self.api_key = api_key or OPENROUTER_API_KEY
        if not self.api_key:
            raise ValueError("OpenRouter API key is required")
        
        # Initialize OpenAI client with OpenRouter base URL
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        logger.info(f"LLMClient initialized with models: BASE={BASE_MODEL}, SUPEREGO={SUPEREGO_MODEL}")
    
    async def get_superego_evaluation(
        self, 
        user_input: str,
        constitution: str,
        messages: Optional[List[Message]] = None,
        on_thinking: Optional[Callable[[str], None]] = None
    ) -> SuperegoEvaluation:
        """
        Evaluate user input with the superego agent
        
        Args:
            user_input: The user input to evaluate
            constitution: The constitution/guidelines for the superego
            messages: Optional conversation history
            on_thinking: Optional callback for thinking content
            
        Returns:
            SuperegoEvaluation with decision and reasoning
        """
        logger.info(f"Evaluating user input with superego: {user_input[:50]}...")
        logger.info(f"Using constitution: {constitution[:100]}...")
        
        # Load the superego instructions
        from .agent_instructions import load_instructions
        instructions_content = load_instructions("input_superego")
        
        # Combine instructions and constitution into a single system prompt
        system_prompt = f"{instructions_content}\n\n## CONSTITUTION:\n\n{constitution}"
        
        # Prepare messages for OpenAI format
        openai_messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided - only include user messages to prevent loops
        if messages:
            user_messages = [msg for msg in messages if msg.role == MessageRole.USER]
            for msg in user_messages:
                openai_messages.append({"role": "user", "content": msg.content})
            logger.info(f"Added {len(user_messages)} user messages from conversation history")
        
        # Add the current user message - format it according to the instructions
        evaluation_prompt = f"""
USER INPUT: {user_input}

Evaluate this input according to your instructions and constitution.
"""
        openai_messages.append({"role": "user", "content": evaluation_prompt})
        
        # Log the full messages being sent to the API in a nicely formatted way
        logger.info("=" * 80)
        logger.info("OPENROUTER API CALL - SUPEREGO EVALUATION")
        logger.info("=" * 80)
        logger.info("SYSTEM PROMPT (INSTRUCTIONS + CONSTITUTION):")
        logger.info("-" * 80)
        logger.info(system_prompt)
        logger.info("-" * 80)
        logger.info("FULL CONVERSATION CONTEXT:")
        logger.info("-" * 80)
        for i, msg in enumerate(openai_messages):
            role = msg["role"].upper()
            content = msg["content"]
            logger.info(f"[{i+1}] {role}: {content}")
        logger.info("-" * 80)
        logger.info("=" * 80)
        
        # Thinking storage
        thinking_content = ""
        
        try:
            # Stream the superego response
            logger.info(f"Making API request to model: {SUPEREGO_MODEL}")
            stream = await self.client.chat.completions.create(
                model=SUPEREGO_MODEL,
                messages=openai_messages,
                stream=True,
                extra_body={"reasoning": {"max_tokens": 2000}},
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Superego LangGraph"
                }
            )
            logger.info("API request sent, awaiting response stream")
            
            full_response = ""
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta:
                    delta = chunk.choices[0].delta
                    
                    # Extract thinking content from various possible delta formats
                    delta_thinking = None
                    if hasattr(delta, "thinking") and delta.thinking:
                        delta_thinking = delta.thinking
                    elif hasattr(delta, "thinking_delta") and delta.thinking_delta:
                        delta_thinking = delta.thinking_delta
                    elif hasattr(delta, "redacted_thinking") and delta.redacted_thinking:
                        delta_thinking = f"[REDACTED: {delta.redacted_thinking}]"
                    
                    # Process thinking content if present
                    if delta_thinking:
                        thinking_content += delta_thinking
                        if on_thinking:
                            await on_thinking(delta_thinking)
                    
                    # Process regular content
                    if hasattr(delta, "content") and delta.content:
                        full_response += delta.content
                        # For some models, content can also be used for thinking
                        if not delta_thinking and on_thinking:
                            await on_thinking(delta.content)
            
            # Parse the evaluation response to determine the decision
            decision = SuperegoDecision.ALLOW  # Default decision
            
            # First look for explicit decision markers
            decision_match = re.search(r'decision:\s*(ALLOW|BLOCK|CAUTION)', full_response, re.IGNORECASE)
            if decision_match:
                decision_text = decision_match.group(1).upper()
                if decision_text == "BLOCK":
                    decision = SuperegoDecision.BLOCK
                elif decision_text == "CAUTION":
                    decision = SuperegoDecision.CAUTION
            # Then check for decision keywords in the text
            elif re.search(r'\bBLOCK\b', full_response, re.IGNORECASE):
                decision = SuperegoDecision.BLOCK
            elif re.search(r'\bCAUTION\b', full_response, re.IGNORECASE):
                decision = SuperegoDecision.CAUTION
            
            return SuperegoEvaluation(
                decision=decision,
                reason=full_response,
                thinking=thinking_content
            )
            
        except Exception as e:
            logger.error(f"Error in superego evaluation: {str(e)}")
            return SuperegoEvaluation(
                decision=SuperegoDecision.ERROR,
                reason=f"Error evaluating input: {str(e)}",
                thinking=thinking_content
            )
    
    async def stream_llm_response(
        self,
        user_input: str,
        messages: List[Message],
        superego_evaluation: Optional[SuperegoEvaluation] = None,
        sysprompt_id: str = DEFAULT_SYSPROMPT_ID
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the base LLM
        
        Args:
            user_input: The current user message
            messages: Conversation history
            superego_evaluation: Optional superego evaluation to include
            sysprompt_id: ID of the system prompt to use
            
        Yields:
            Tokens from the LLM response
        """
        logger.info(f"Streaming LLM response for: {user_input[:50]}...")
        logger.info(f"Using sysprompt_id: {sysprompt_id}")
        
        # Get the system prompt content
        if sysprompt_id and sysprompt_id in ALL_SYSPROMPTS:
            system_message = ALL_SYSPROMPTS[sysprompt_id]["content"]
            logger.info(f"Found system prompt with ID {sysprompt_id}: {system_message[:100]}...")
        else:
            system_message = get_default_sysprompt()
            logger.info(f"Using default system prompt: {system_message[:100]}...")
            
        # If we have a superego evaluation, include it in the system message
        if superego_evaluation:
            logger.info(f"Including superego evaluation with decision: {superego_evaluation.decision.value}")
            system_message += f"\n\nThe Superego has evaluated the current user request with this decision: {superego_evaluation.decision.value}."
            system_message += f"\n\nSuperego reasoning: {superego_evaluation.reason}"
            
            # Add specific instructions based on superego decision
            if superego_evaluation.decision == SuperegoDecision.BLOCK:
                system_message += "\n\nThis request has been BLOCKED. You must politely decline to fulfill this request and explain why it cannot be fulfilled."
                logger.info("Added BLOCK instructions to system message")
            elif superego_evaluation.decision == SuperegoDecision.CAUTION:
                system_message += "\n\nThis request has been CAUTIONED. You may fulfill this request, but take extra care to ensure your response is safe, ethical, and helpful."
                logger.info("Added CAUTION instructions to system message")
        else:
            logger.info("No superego evaluation provided")
        
        # Prepare messages for OpenAI format
        openai_messages = [{"role": "system", "content": system_message}]
        
        # Add conversation history - only include user messages to prevent loops
        user_messages = [msg for msg in messages if msg.role == MessageRole.USER]
        for msg in user_messages:
            openai_messages.append({"role": "user", "content": msg.content})
        logger.info(f"Added {len(user_messages)} user messages from conversation history")
        
        # Log the full messages being sent to the API in a nicely formatted way
        logger.info("=" * 80)
        logger.info("OPENROUTER API CALL - LLM RESPONSE")
        logger.info("=" * 80)
        logger.info("SYSTEM PROMPT:")
        logger.info("-" * 80)
        logger.info(system_message)
        logger.info("-" * 80)
        logger.info("FULL CONVERSATION CONTEXT:")
        logger.info("-" * 80)
        for i, msg in enumerate(openai_messages):
            role = msg["role"].upper()
            content = msg["content"]
            logger.info(f"[{i+1}] {role}: {content}")
        logger.info("-" * 80)
        logger.info("=" * 80)
        
        try:
            # Stream the LLM response
            logger.info(f"Making API request to model: {BASE_MODEL}")
            stream = await self.client.chat.completions.create(
                model=BASE_MODEL,
                messages=openai_messages,
                stream=True,
                extra_headers={
                    "HTTP-Referer": "http://localhost:3000",
                    "X-Title": "Superego LangGraph"
                }
            )
            logger.info("API request sent, awaiting response stream")
            
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            logger.error(f"Error streaming LLM response: {str(e)}")
            yield f"Error: {str(e)}"

# Default LLM client instance
default_client = None

def get_llm_client() -> LLMClient:
    """Get the default LLM client, initializing it if necessary"""
    global default_client
    
    if default_client is None:
        default_client = LLMClient()
    
    return default_client

# Get all available system prompts
def get_all_sysprompts() -> Dict[str, Dict[str, Any]]:
    """Get all available system prompts"""
    return ALL_SYSPROMPTS

# Save a new system prompt
def save_sysprompt(prompt_id: str, name: str, content: str) -> bool:
    """
    Save a new system prompt to the JSON file
    
    Args:
        prompt_id: Unique ID for the system prompt
        name: Display name for the system prompt
        content: The system prompt content
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Load current system prompts
        sysprompts = load_sysprompts()
        
        # Add or update the system prompt
        sysprompts[prompt_id] = {
            "id": prompt_id,
            "name": name,
            "content": content
        }
        
        # Write to file
        with open(SYSPROMPTS_FILE, 'w') as f:
            json.dump({"prompts": list(sysprompts.values())}, f, indent=2)
        
        # Update global variable
        global ALL_SYSPROMPTS
        ALL_SYSPROMPTS = sysprompts
        
        logger.info(f"System prompt '{prompt_id}' saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving system prompt: {e}")
        return False
