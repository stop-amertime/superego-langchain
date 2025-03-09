import logging
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, AsyncGenerator, Tuple
from enum import Enum

from ..models import SuperegoEvaluation, SuperegoDecision, Message, ToolInput, ToolOutput

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AgentType(str, Enum):
    """Types of agents in the system"""
    INPUT_SUPEREGO = "input_superego"
    OUTPUT_SUPEREGO = "output_superego"
    GENERAL_ASSISTANT = "general_assistant"
    SHOPPING_ASSISTANT = "shopping_assistant"
    ROUTER = "router"
    RESEARCHER = "researcher"
    CUSTOM = "custom"

class BaseAgent(ABC):
    """Base abstract class for all agents"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with the given configuration
        
        Args:
            config: Configuration for the agent
        """
        self.config = config
        self.agent_type = config.get("agent_type", AgentType.CUSTOM)
        self.name = config.get("name", f"{self.agent_type}_agent")
        self._is_running = False
        logger.info(f"Initialized {self.agent_type} agent: {self.name}")
    
    @abstractmethod
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """
        Process input and return a complete response
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Returns:
            The processed response
        """
        pass
    
    @abstractmethod
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream the response token by token
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Yields:
            Tokens from the response
        """
        pass
    
    async def interrupt(self) -> bool:
        """
        Interrupt the current processing
        
        Returns:
            True if successfully interrupted, False otherwise
        """
        if self._is_running:
            logger.info(f"Interrupting {self.agent_type} agent: {self.name}")
            self._is_running = False
            return True
        return False
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about the agent
        
        Returns:
            Dictionary with agent metadata
        """
        return {
            "agent_type": self.agent_type,
            "name": self.name,
            "config": {k: v for k, v in self.config.items() if k not in ["api_key"]}
        }

class SuperegoAgent(BaseAgent):
    """Base class for superego agents that evaluate content"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the superego agent
        
        Args:
            config: Configuration for the agent, including:
                - constitution: The constitution/guidelines for evaluation
        """
        super().__init__(config)
        self.constitution = config.get("constitution", "")
        logger.info(f"Initialized SuperegoAgent with constitution: {self.constitution[:50]}...")
    
    @abstractmethod
    async def evaluate(self, content: str, context: Dict[str, Any]) -> SuperegoEvaluation:
        """
        Evaluate content against the constitution
        
        Args:
            content: The content to evaluate
            context: Additional context for evaluation
            
        Returns:
            SuperegoEvaluation with decision and reasoning
        """
        pass

class InputSuperego(SuperegoAgent):
    """
    Input Superego agent that evaluates user inputs before they're processed.
    It screens inputs against a constitution to ensure compliance with guidelines.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the input superego agent
        
        Args:
            config: Configuration for the agent
        """
        config["agent_type"] = AgentType.INPUT_SUPEREGO
        super().__init__(config)
    
    async def evaluate(self, content: str, context: Dict[str, Any]) -> SuperegoEvaluation:
        """
        Evaluate user input against the constitution
        
        Args:
            content: The user input to evaluate
            context: Additional context for evaluation
            
        Returns:
            SuperegoEvaluation with decision and reasoning
        """
        # This method should be implemented by concrete subclasses
        raise NotImplementedError("Subclasses must implement evaluate()")
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """
        Process input and return a complete response
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Returns:
            The processed response
        """
        # Evaluate the input
        evaluation = await self.evaluate(input_text, context)
        
        # Return the evaluation as a formatted string
        return f"""
        DECISION: {evaluation.decision.value}
        
        REASON:
        {evaluation.reason}
        """
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream the response token by token
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Yields:
            Tokens from the response
        """
        # Set running flag
        self._is_running = True
        
        try:
            # Evaluate the input
            evaluation = await self.evaluate(input_text, context)
            
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

class OutputSuperego(SuperegoAgent):
    """
    Output Superego agent that evaluates assistant outputs as they're streamed.
    It screens outputs against a constitution to ensure compliance with guidelines.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the output superego agent
        
        Args:
            config: Configuration for the agent
        """
        config["agent_type"] = AgentType.OUTPUT_SUPEREGO
        super().__init__(config)
        self.buffer_size = config.get("buffer_size", 100)  # Number of tokens to buffer before evaluation
        self.buffer = ""
        self.previous_chunks = []
    
    async def evaluate_chunk(self, chunk: str, context: Dict[str, Any]) -> Tuple[SuperegoDecision, Optional[str]]:
        """
        Evaluate a chunk of output against the constitution
        
        Args:
            chunk: The chunk of output to evaluate
            context: Additional context for evaluation
            
        Returns:
            Tuple of (decision, modified_chunk)
        """
        # Combine with previous chunks for context
        full_content = "".join(self.previous_chunks) + chunk
        
        # Evaluate the full content
        evaluation = await self.evaluate(full_content, context)
        
        # Return the decision and potentially modified chunk
        if evaluation.decision == SuperegoDecision.BLOCK:
            # Replace the chunk with a blocked message
            return SuperegoDecision.BLOCK, f"[BLOCKED: {evaluation.reason}]"
        elif evaluation.decision == SuperegoDecision.CAUTION:
            # Add a caution note if this is the first chunk
            if not self.previous_chunks:
                return SuperegoDecision.CAUTION, f"[CAUTION: {evaluation.reason}]\n\n{chunk}"
            return SuperegoDecision.CAUTION, chunk
        else:
            # Allow the chunk unchanged
            return SuperegoDecision.ALLOW, chunk
    
    async def process_stream(self, token_stream: AsyncGenerator[str, None], context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Process a stream of tokens, evaluating chunks and yielding processed tokens
        
        Args:
            token_stream: Stream of tokens from the assistant
            context: Additional context for evaluation
            
        Yields:
            Processed tokens
        """
        self._is_running = True
        self.buffer = ""
        self.previous_chunks = []
        
        try:
            async for token in token_stream:
                if not self._is_running:
                    logger.info("Processing interrupted")
                    break
                
                # Add token to buffer
                self.buffer += token
                
                # If buffer reaches threshold, evaluate and yield
                if len(self.buffer) >= self.buffer_size:
                    decision, processed_chunk = await self.evaluate_chunk(self.buffer, context)
                    
                    # Store the original chunk for context
                    self.previous_chunks.append(self.buffer)
                    
                    # Reset buffer
                    self.buffer = ""
                    
                    # Yield the processed chunk
                    if processed_chunk:
                        yield processed_chunk
            
            # Process any remaining buffer
            if self.buffer:
                decision, processed_chunk = await self.evaluate_chunk(self.buffer, context)
                if processed_chunk:
                    yield processed_chunk
                
        except Exception as e:
            logger.error(f"Error in OutputSuperego.process_stream: {str(e)}")
            yield f"Error: {str(e)}"
        finally:
            self._is_running = False
    
    async def evaluate(self, content: str, context: Dict[str, Any]) -> SuperegoEvaluation:
        """
        Evaluate content against the constitution
        
        Args:
            content: The content to evaluate
            context: Additional context for evaluation
            
        Returns:
            SuperegoEvaluation with decision and reasoning
        """
        # This method should be implemented by concrete subclasses
        raise NotImplementedError("Subclasses must implement evaluate()")
    
    async def process(self, input_text: str, context: Dict[str, Any]) -> str:
        """
        Process input and return a complete response
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Returns:
            The processed response
        """
        # This is not typically used for OutputSuperego as it processes streams
        evaluation = await self.evaluate(input_text, context)
        return f"Output evaluation: {evaluation.decision.value} - {evaluation.reason}"
    
    async def stream(self, input_text: str, context: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """
        Stream the response token by token
        
        Args:
            input_text: The input text to process
            context: Additional context for processing
            
        Yields:
            Tokens from the response
        """
        # This is not typically used for OutputSuperego as it processes streams
        evaluation = await self.evaluate(input_text, context)
        result = f"Output evaluation: {evaluation.decision.value} - {evaluation.reason}"
        
        for char in result:
            if not self._is_running:
                break
            yield char
            await asyncio.sleep(0.001)

class AssistantAgent(BaseAgent):
    """Base class for assistant agents that respond to user queries and can use tools"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the assistant agent
        
        Args:
            config: Configuration for the agent, including:
                - system_prompt: The system prompt for the assistant
                - available_tools: Optional list of available tools
        """
        super().__init__(config)
        self.system_prompt = config.get("system_prompt", "You are a helpful AI assistant.")
        self.available_tools = config.get("available_tools", [])
        logger.info(f"Initialized AssistantAgent with system prompt: {self.system_prompt[:50]}...")
        logger.info(f"AssistantAgent has {len(self.available_tools)} available tools")
    
    async def use_tool(self, tool_input: ToolInput, context: Dict[str, Any]) -> ToolOutput:
        """
        Use a tool with the given input
        
        Args:
            tool_input: The input for the tool
            context: Additional context for tool usage
            
        Returns:
            The output from the tool
        """
        tool_name = tool_input.name
        
        # Find the tool by name
        tool = next((t for t in self.available_tools if t.name == tool_name), None)
        
        if not tool:
            logger.error(f"Tool not found: {tool_name}")
            return ToolOutput(
                name=tool_name,
                output=f"Error: Tool '{tool_name}' not found"
            )
        
        try:
            # Use the tool
            logger.info(f"Using tool: {tool_name} with arguments: {tool_input.arguments}")
            result = await tool.execute(tool_input.arguments, context)
            
            return ToolOutput(
                name=tool_name,
                output=result
            )
        except Exception as e:
            logger.error(f"Error using tool {tool_name}: {str(e)}")
            return ToolOutput(
                name=tool_name,
                output=f"Error using tool: {str(e)}"
            )

# Agent factory
class AgentFactory:
    """Factory for creating agents of different types"""
    
    _registry = {}
    
    @classmethod
    def register(cls, agent_type: str, agent_class):
        """Register an agent class for a specific type"""
        cls._registry[agent_type] = agent_class
        logger.info(f"Registered agent type: {agent_type}")
    
    @classmethod
    def create(cls, agent_type: str, config: Dict[str, Any]) -> BaseAgent:
        """Create an agent of the specified type"""
        if agent_type not in cls._registry:
            raise ValueError(f"Unknown agent type: {agent_type}")
        
        logger.info(f"Creating agent of type: {agent_type}")
        return cls._registry[agent_type](config)
    
    @classmethod
    def get_available_agent_types(cls) -> List[str]:
        """Get a list of available agent types"""
        return list(cls._registry.keys())
