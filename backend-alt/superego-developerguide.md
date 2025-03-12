# Superego Agent System: Developer Reference

## Core Concept

Research system investigating "Superego" agents that monitor other agents according to defined values. The Superego acts as a value-based filter for both inputs and outputs, allowing systems to enforce ethical constraints.

## System Architecture

- **Superego Agent**: Evaluates messages against a "constitution" of values, issuing commands to control flow
- **Inner Agents**: Process inputs after Superego approval, with specialized capabilities (research, coding, etc.)
- **Flow Control**: Agents can route messages to other agents or themselves recursively based on evaluation
- **Streaming**: All agents support streaming partial responses throughout processing
- **Hidden Communication**: Agents can pass metadata in the "agent_guidance" field that's invisible to users but accessible to other agents

Key design principles:
- Minimal implementation focused on research, not production
- Functional programming patterns with immutable flow records
- Explicit tracking of agent identity and decision paths

## Step Structure

```python
{
    "step_id": str,         # Unique identifier for this step in the flow
    "agent_id": str,        # Identifier for specific agent: "superego", "research", "coding", etc.
    "timestamp": str,       # ISO timestamp when this step occurred
    "role": str,            # "user", "assistant", or "system"
    "input": str,           # Input message/content this agent received
    
    # Agent-specific fields - only one set will be present based on agent type
    # Superego-specific fields
    "constitution": str,    # For superego: the actual constitution text used
    "decision": str,        # BLOCK, ACCEPT, CAUTION, or NEEDS_CLARIFICATION
    
    # Inner agent-specific fields
    "system_prompt": str,   # Inner agent system instructions
    "tool_usage": {         # Present when tools are used
        "tool_name": str,
        "input": any,
        "output": any
    },
    
    # Common fields for all agents
    "thinking": str,        # Agent's reasoning process (not shown to user)
    "agent_guidance": str,  # Hidden inter-agent communication - passes context between agents
    "response": str,        # The agent's visible response to the user
    "next_agent": str       # The next agent to call (or null if flow ends)
}
```

The `agent_guidance` field is a critical feature for inter-agent communication. It allows agents to pass context, warnings, or guidance to subsequent agents without exposing this information to the user. For example, a Superego might accept a request but include guidance about potential concerns for the Inner Agent to consider.

## Flow Record

A flow record is an array of step records tracking the entire conversation history:

```python
[
    {
        "step_id": "1",
        "agent_id": "user",
        "timestamp": "2023-11-15T10:30:45Z",
        "role": "user",
        "input": null,
        "response": "Calculate 5*10",
        "next_agent": "input_superego"
    },
    {
        "step_id": "2",
        "agent_id": "input_superego",
        "timestamp": "2023-11-15T10:30:46Z",
        "role": "assistant",
        "input": "Calculate 5*10",
        "constitution": "Be helpful, accurate, and verify calculations before providing answers.",
        "thinking": "This appears to be a simple calculation request.",
        "decision": "CAUTION",
        "agent_guidance": "Request is acceptable but requires verification. Inner agent should double-check result.",
        "response": "I'll help you calculate that.",
        "next_agent": "calculator_agent"
    },
    {
        "step_id": "3",
        "agent_id": "calculator_agent",
        "timestamp": "2023-11-15T10:30:47Z",
        "role": "assistant",
        "input": "Calculate 5*10",
        "system_prompt": "You are a calculator agent that performs arithmetic operations.",
        "thinking": "I need to multiply 5 by 10",
        "agent_guidance": "Calculation verified using tool. Confidence: high.",
        "response": "I'll calculate 5*10 for you",
        "tool_usage": {
            "tool_name": "calculator", 
            "input": "5*10", 
            "output": "50"
        },
        "next_agent": "research_agent"
    },
    {
        "step_id": "4",
        "agent_id": "research_agent",
        "timestamp": "2023-11-15T10:30:48Z",
        "role": "assistant",
        "input": "Calculate 5*10",
        "system_prompt": "You are a research agent that provides comprehensive answers.",
        "response": "The result of 5*10 is 50.",
        "next_agent": null
    }
]
```

## Superego Commands

Superego agents use these standardized commands to control flow:

```python
BLOCK = "BLOCK"     # Reject the input entirely, conversation ends
ACCEPT = "ACCEPT"   # Allow the input without special handling
CAUTION = "CAUTION" # Allow with warning (agent_guidance passed to inner agent)
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"  # Recurse to get more info from user
```

## Flow Definition Schema

The flow definition specifies the agent graph structure and transition rules:

```python
{
    "name": str,
    "description": str,
    "graph": {
        "start": str,  # Starting node name
        "nodes": {
            "node_name": {
                "type": str,      # "superego" or "inner_agent"
                "agent_id": str,  # Unique identifier for the agent
                "max_iterations": int,  # Maximum self-recursion count
                
                # Agent-specific configuration
                "constitution": str,  # For superego: full constitution text
                "system_prompt": str,  # For inner agents: system instructions
                "tools": [str],        # For inner agents: available tools
                
                # Flow control - defines where to go next based on agent decision
                "transitions": {
                    "condition": str  # Next node name, null (end), or self (recursion)
                }
            }
        }
    }
}
```

## Transition Rules

Transition conditions map directly to agent decision values:

```python
# Superego transitions
"transitions": {
    "BLOCK": null,              # End flow
    "ACCEPT": "inner_agent",    # Go to inner agent 
    "CAUTION": "inner_agent",   # Go to inner agent with warning
    "NEEDS_CLARIFICATION": "self"  # Loop back to self
}

# Inner Agent transitions
"transitions": {
    "COMPLETE": null,          # End flow
    "NEEDS_TOOL": "self",      # Self-loop for tool usage
    "ERROR": "error_handler"   # Go to error handler
}
```

## Component Interfaces

### agents/superego.py ✅
- **Purpose**: Evaluate messages against constitution values
- **Function**: `superego_evaluate(llm, input_message, constitution) -> decision, agent_guidance, thinking`
- **Imports**: `langchain_core`, `pydantic`
- **Returns**: Decision, agent_guidance, and thinking process
- **Input**: LLM instance, input message, constitution text
- **Output**: Stream of `StreamChunk` objects with partial and complete outputs
- **Hidden Communication**: Uses `agent_guidance` field to pass context to inner agents
- **Implementation Notes**:
  - Uses LangChain's structured output parsing with Pydantic for reliable decision extraction
  - Leverages async/await for non-blocking LLM calls and streaming
  - Validates decision values and applies fallback to CAUTION if invalid
  - Creates properly formatted FlowStep objects for graph execution
  - Factory function `create_superego_node` generates compatible LangGraph nodes

### agents/inner_agent.py ✅
- **Purpose**: Process inputs after Superego approval
- **Function**: `process_with_tools(llm, input_message, system_prompt, agent_guidance, agent_id, available_tools) -> response, tool_usage, agent_guidance, next_agent`
- **Imports**: `langchain_core`, `pydantic`, `asyncio`
- **Returns**: Response, tool usage records, agent guidance, and next agent
- **Input**: LLM instance, input message, system prompt, agent guidance, agent ID, and available tools dictionary
- **Output**: Stream of `StreamChunk` objects with partial and complete outputs
- **Tool Usage**: Records tool calls and results in the flow step
- **Implementation Notes**:
  - Uses structured output parsing with Pydantic to ensure consistent format
  - Supports both synchronous and asynchronous tools with unified interface
  - Maintains streaming during tool execution with intermediate updates
  - Dynamically handles self-transitions and recursive tool use
  - Automatically validates and normalizes next_agent field for routing
  - Creates organized FlowStep objects using functional composition pattern

### agents/prompts.py ✅
- **Purpose**: Store prompt templates for agents
- **Constants**:
  - `SUPEREGO_PROMPT`: Template for superego evaluation
  - `INNER_AGENT_PROMPT`: Template for inner agent
  - `STREAMING_RESPONSE_TEMPLATE`: Simplified template for streaming responses
- **Agent_Guidance Field Usage**: Templates include detailed instructions on proper use of agent_guidance field
- **Implementation Notes**:
  - Prompt templates use clear sections to guide agent responses
  - SUPEREGO_PROMPT focuses on constitutional evaluation with explicit decision structure
  - INNER_AGENT_PROMPT emphasizes processing inputs based on superego approval
  - Added specific fields needed for template formatting: agent_id, constitution, etc.
  - Included explicit instructions for formatting thinking, decisions, and next steps

### agents/commands.py ✅
- **Purpose**: Define superego command constants
- **Constants**: 
  - **Superego decisions**: `BLOCK`, `ACCEPT`, `CAUTION`, `NEEDS_CLARIFICATION`
  - **Inner agent decisions**: `COMPLETE`, `NEEDS_TOOL`, `NEEDS_RESEARCH`, `NEEDS_REVIEW`, `ERROR`
- **No function calls or returns**
- **Implementation Notes**: 
  - Added inner agent decision constants beyond the basic superego commands
  - Each constant has a descriptive comment explaining its purpose
  - The implementation follows the ruthless minimalism principle with no unnecessary code

### flow/builder.py ✅
- **Purpose**: Construct LangGraph from flow definition
- **Function**: `build_flow(flow_def: dict, llm) -> StateGraph`
- **Imports**: `langgraph`, `agents.superego`, `agents.inner_agent`
- **Returns**: Compiled StateGraph with cycle support
- **Key Feature**: Handles agent transitions and recursion limits
- **Implementation Notes**:
  - Uses a dictionary-based approach to map node types to creator functions
  - Creates a unified router that handles both superego and inner agent decisions
  - Automatically handles self-transitions and recursion with flexible routing
  - Passes only required parameters to node creation functions
  - Implements error checking for invalid flow definitions
  - Follows minimalist approach with flat structure and functional programming patterns

### flow/executor.py ✅
- **Purpose**: Execute flows and handle streaming
- **Function**: `execute_flow(flow: StateGraph, input: str) -> AsyncGenerator[dict, None]`
- **Imports**: `langgraph`, `anyio`
- **Returns**: Stream of flow record steps with agent attribution
- **User Visibility**: Filters out hidden fields (`thinking`, `agent_guidance`) from user-visible output
- **Implementation Notes**:
  - Uses async generator for efficient streaming without buffering
  - Filters sensitive fields using dictionary comprehension
  - Maintains flow state using LangGraph's native streaming
  - Extracts latest step from state for incremental updates
  - Follows minimalist approach with no unnecessary abstractions

### flow/engine.py ✅
- **Purpose**: Orchestrate flow execution and manage flow state
- **Functions**: 
  - `initialize_engine(constitutions_dir: str, flow_defs_dir: str) -> FlowEngine` - Initialize engine with constitutions and flows
  - `FlowEngine.create_flow(flow_id: str, llm: Any) -> str` - Create a flow instance from a definition
  - `FlowEngine.execute(instance_id: str, input_message: str) -> AsyncGenerator[Dict, None]` - Execute a flow with input
  - `FlowEngine.get_flow_history(instance_id: str) -> List[Dict]` - Get history of a flow instance
  - `FlowEngine.get_available_flows() -> List[Dict]` - Get list of available flow definitions
- **Imports**: `uuid`, `datetime`, `asyncio`, `flow.builder`, `flow.executor`, `flow.loader`
- **Returns**: Various - flow instance IDs, flow state, streaming execution results
- **Key Feature**: Singleton pattern for global access with initialization function
- **Implementation Notes**:
  - Uses a singleton instance to avoid redundant engine instantiation
  - Maintains flow state with dictionaries rather than classes
  - Tracks flow history with immutable append-only arrays
  - Creates user steps with proper agent routing information
  - Bridges between flow definition loading and execution
  - Manages both flow definitions (templates) and flow instances (executions)
  - Provides a unified API for the entire flow system without abstracting away details

### flow/loader.py ✅
- **Purpose**: Load flow definitions
- **Functions**: 
  - `load_flow(path: str) -> dict` - Load a single flow definition
  - `load_flows_from_directory(directory: str) -> List[dict]` - Load all flows from a directory
  - `get_constitutions_map(directory: str) -> Dict[str, str]` - Load all constitutions
  - `embed_constitutions(flow_def: dict, constitutions: Dict[str, str]) -> dict` - Embed constitutions into flow
- **Imports**: `json`, `pathlib`
- **Returns**: Loaded flow definitions with embedded constitutions
- **Implementation Notes**:
  - Uses standard library json module instead of orjson for simplicity
  - Implements validation to ensure flow definitions have required structure
  - Handles loading constitutions as markdown files and embedding them in flows
  - Robust error handling with informative error messages
  - Uses pathlib for cleaner file path operations

### api/routes.py ✅
- **Purpose**: Define FastAPI endpoints
- **Routes**:
  - `POST /flow/execute`: Execute flow with user input
  - `GET /flows`: List available flows
  - `GET /flow/{flow_id}`: Get specific flow definition
- **Imports**: `fastapi`, `pydantic`, `flow.loader`
- **Returns**: FastAPI route handlers and SSE responses
- **Implementation Notes**:
  - Uses Pydantic models for request/response validation
  - Creates a flow registry using the loader module
  - Handles flow discovery and execution
  - Uses dependency injection for sharing the flow registry
  - Implements error handling for missing flows
  - Sanitizes sensitive data from API responses

### api/stream.py ✅
- **Purpose**: Handle SSE streaming
- **Function**: `stream_response(generator: AsyncGenerator) -> EventSourceResponse`
- **Imports**: `sse_starlette`, `asyncio`, `json`
- **Returns**: EventSourceResponse with filtered flow steps
- **Implementation Notes**:
  - Implements Server-Sent Events (SSE) for streaming partial outputs
  - Filters out sensitive fields like thinking, agent_guidance
  - Handles different event types (partial_output vs complete_step)
  - Includes error handling for streaming exceptions
  - Sets proper headers for streaming compatibility with various clients

### tools/calculator.py ✅
- **Purpose**: Implement simple calculator tool
- **Function**: `calculate(expression) -> result`
- **Imports**: `re`, `math`, `operator` (all standard library)
- **Returns**: Calculated result or error message
- **Implementation Notes**:
  - Includes robust error handling for various calculation scenarios
  - Implements security checks to prevent code injection
  - Uses a restricted execution environment with only safe operations
  - Added `register_tools()` function for simple integration with the agent system
  - Supports basic arithmetic, exponentiation, and common math functions
  - Following the minimalism principle with focused functionality

## Implementation Guidelines

### Streaming Protocol
- All agents must yield partial outputs as they're generated
- Streaming format: `{"partial_output": str, "complete": bool, "flow_step": dict}`
- Partial outputs contain incomplete responses during generation
- Complete=True indicates the final chunk with the full flow step

### Inter-Agent Communication
- The `agent_guidance` field is the primary channel for hidden communication between agents
- Agent_guidance should be detailed enough to provide context but concise
- Agent_guidance is never shown to users but is crucial for agent coordination
- Examples of effective agent_guidance:
  - "Request appears benign but contains ambiguous elements. Monitor for potential escalation."
  - "Mathematical verification needed. Previous agent uncertain about calculation."
  - "User seems frustrated. Consider acknowledging difficulty before answering."

### State Management
- All flow steps must be treated as immutable
- Append new steps rather than modifying existing ones
- Use functional patterns for state updates
- Include all necessary context in each step

### Recursion and Cycles
- Agents can call themselves or other agents
- Track iteration counts per node to prevent infinite loops
- Self-transitions need explicit termination conditions
- Each agent must determine when recursion is complete

## Dependencies
- `langgraph` - For agent orchestration with cycle support
- `langchain` - For pre-built agent structures and tool interfaces
- `fastapi` - For API endpoints
- `sse-starlette` - For streaming
- `anyio` - For simplified async operations
- `pydantic` - For validation and serialization
- `orjson` - For JSON handling

## Working Example

```python
from langgraph.graph import StateGraph
from langchain_openai import ChatOpenAI

# Create LLM
llm = ChatOpenAI()

# Define superego evaluation function
def superego_evaluate(input_message, constitution):
    """Evaluate input against constitution"""
    # Use LLM to evaluate the input against the constitution
    # In practice, this would use LangChain to prompt the LLM
    
    # For this example, assume it's a simple calculation request
    decision = "ACCEPT"
    agent_guidance = "Simple calculation request. Verify result before responding."
    thinking = "User is asking for a calculation that seems straightforward."
    
    return decision, agent_guidance, thinking

# Create superego node function
def create_superego_node(llm, agent_id="superego"):
    """Creates a superego node"""
    async def superego_node(input_step, constitution):
        # Evaluate the input against the constitution
        decision, agent_guidance, thinking = superego_evaluate(input_step["response"], constitution)
        
        # Create the superego step
        step = {
            "step_id": str(uuid.uuid4()),
            "agent_id": agent_id,
            "timestamp": datetime.now().isoformat(),
            "role": "assistant",
            "input": input_step["response"],
            "constitution": constitution,
            "thinking": thinking,
            "decision": decision,
            "agent_guidance": agent_guidance,
            "response": f"I'll help with that." if decision in ["ACCEPT", "CAUTION"] else "I can't help with that.",
            "next_agent": "inner_agent" if decision in ["ACCEPT", "CAUTION"] else None
        }
        
        # Stream the response (simplified for example)
        yield {"partial_output": step["response"], "complete": True, "flow_step": step}
    
    return superego_node

# Define flow building function
def build_simple_flow():
    """Build a simple superego → inner agent flow"""
    flow_def = {
        "name": "basic_calculator",
        "graph": {
            "start": "superego",
            "nodes": {
                "superego": {
                    "type": "superego",
                    "agent_id": "superego",
                    "constitution": "Be helpful and verify calculations.",
                    "transitions": {
                        "ACCEPT": "calculator",
                        "CAUTION": "calculator",
                        "BLOCK": None
                    }
                },
                "calculator": {
                    "type": "inner_agent",
                    "agent_id": "calculator",
                    "system_prompt": "You are a calculator agent.",
                    "tools": ["calculator"],
                    "transitions": {
                        "*": None
                    }
                }
            }
        }
    }
    
    # In a real implementation, this would use LangGraph to build the flow
    # return build_flow(flow_def, llm)
    return "StateGraph object would be returned"

# Example execution
def execute_example():
    # Create a user input step
    user_step = {
        "step_id": "1",
        "agent_id": "user",
        "timestamp": "2023-11-15T10:30:45Z",
        "role": "user",
        "response": "Calculate 5*10",
        "next_agent": "superego"
    }
    
    # Evaluate with superego
    decision, agent_guidance, thinking = superego_evaluate(
        user_step["response"], 
        "Be helpful and verify calculations."
    )
    
    # Create superego step
    superego_step = {
        "step_id": "2",
        "agent_id": "superego",
        "timestamp": "2023-11-15T10:30:46Z",
        "role": "assistant",
        "input": user_step["response"],
        "constitution": "Be helpful and verify calculations.",
        "thinking": thinking,
        "decision": decision,
        "agent_guidance": agent_guidance,
        "response": "I'll help with that calculation.",
        "next_agent": "calculator" if decision in ["ACCEPT", "CAUTION"] else None
    }
    
    # Create flow record
    flow_record = [user_step, superego_step]
    
    # In a real implementation, this would continue to the calculator agent
    return flow_record

# Example output
print(execute_example())
```

## Enhanced Multi-Agent Flow

```json
{
  "name": "multi_agent_flow",
  "description": "Flow with multiple agent types",
  "graph": {
    "start": "input_superego",
    "nodes": {
      "input_superego": {
        "type": "superego",
        "agent_id": "input_superego",
        "constitution": "Be helpful and accurate. Verify calculations before providing answers. Reject harmful requests.",
        "max_iterations": 3,
        "transitions": {
          "BLOCK": null,
          "ACCEPT": "research_agent",
          "CAUTION": "research_agent",
          "NEEDS_CLARIFICATION": "input_superego"
        }
      },
      "research_agent": {
        "type": "inner_agent",
        "agent_id": "research_agent",
        "system_prompt": "You are a helpful research assistant that provides accurate information.",
        "tools": ["calculator", "search"],
        "max_iterations": 5,
        "transitions": {
          "COMPLETE": "code_agent",
          "NEEDS_TOOL": "research_agent",
          "NEEDS_REVIEW": "input_superego"
        }
      },
      "code_agent": {
        "type": "inner_agent",
        "agent_id": "code_agent",
        "system_prompt": "You are a coding assistant that writes clean, efficient code.",
        "tools": ["code_analyzer"],
        "max_iterations": 3,
        "transitions": {
          "COMPLETE": "output_superego",
          "NEEDS_REFINEMENT": "code_agent",
          "NEEDS_RESEARCH": "research_agent"
        }
      },
      "output_superego": {
        "type": "superego",
        "agent_id": "output_superego",
        "constitution": "Ensure all outputs are accurate, helpful, and free from harmful content.",
        "max_iterations": 2,
        "transitions": {
          "BLOCK": "code_agent",
          "ACCEPT": null,
          "CAUTION": null
        }
      }
    }
  }
}
```

## Flow Execution Process

1. User input → API
2. API passes input to Flow Controller
3. Flow begins execution at Superego
4. Superego streams thinking and evaluation process
   - Constitution is embedded directly in the flow step
5. Superego issues command
   - If BLOCK: return explanation to user
   - If ACCEPT/CAUTION: pass to Inner Agent with optional agent_guidance
   - If NEEDS_CLARIFICATION: recurse to itself (with iteration limit)
6. Inner Agent streams thinking process and tool usage
   - Tool calls and results are embedded directly in the flow step
   - Each agent identifies itself with a unique agent_id
   - Can recurse to itself for multi-step tool use
   - Can transition to other specialized agents as needed
7. All responses streamed back to user via SSE with complete flow steps

And finally: ruthless minimalism is essential. Every token matters. Reject unnecessary abstractions, wrapper functions, and boilerplate. Never create a function that just transforms simple data or returns a single value from an array - use the data structure directly. 

Remember: code is liability, not asset. Each line must justify its existence. No seven-step handlers where three will do. No classes when maps/arrays suffice. No getters/setters for what could be direct access. No multi-layered middleware for what could be a pure function.

Comments should be sparse and focused only on explaining non-obvious logic. No documentation bloat that restates what code already shows. No endless TODOs. No line-by-line explanations of basic operations.

Always prefer flat data over deep hierarchies. Choose composition over inheritance. Favor pure functions over stateful objects. Stream directly rather than buffering unnecessarily. Cut every corner that doesn't compromise core functionality.

The mark of good system design isn't how much you add - it's how much you remove while preserving capability.
