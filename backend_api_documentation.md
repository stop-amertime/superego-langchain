# Superego Agent System: API Documentation

## System Overview

The Superego Agent System is a research platform investigating "Superego" agents that monitor other agents according to defined values. The Superego acts as a value-based filter for both inputs and outputs, allowing systems to enforce ethical constraints through a defined constitution.

### Core Concept

This system represents a novel approach to AI safety and alignment research where a "Superego" agent evaluates all inputs and outputs against a set of defined values or principles. The research focuses on how such a system can enforce ethical guardrails while still allowing specialized inner agents to perform their functions.

Key research questions this system addresses:
- How can value-based filtering improve AI safety?
- What architectures enable effective agent monitoring?
- How do different constitution formulations affect agent behavior?
- Can monitoring agents effectively detect and prevent problematic outputs?

### System Architecture

- **Superego Agent**: Evaluates messages against a "constitution" of values, issuing commands to control flow
- **Inner Agents**: Process inputs after Superego approval, with specialized capabilities (research, coding, etc.)
- **Flow Control**: Agents can route messages to other agents or themselves recursively based on evaluation
- **Streaming**: All agents support streaming partial responses throughout processing
- **Hidden Communication**: Agents pass metadata in the "agent_guidance" field between each other (invisible to users)

Key design principles:
- Minimal implementation focused on research, not production
- Functional programming patterns with immutable flow records
- Explicit tracking of agent identity and decision paths

## API Endpoints

The API is built using FastAPI and provides the following endpoints:

### Health Check

```
GET /health
```

Returns the API status and version.

**Response:**
```json
{
  "status": "ok",
  "version": "0.1.0"
}
```

### List Available Flows

```
GET /flows
```

Returns a list of all available flow definitions.

**Response:**
```json
[
  {
    "id": "basic-calculator",
    "name": "Basic Calculator",
    "description": "A simple calculator flow with Superego monitoring"
  },
  {
    "id": "research-assistant",
    "name": "Research Assistant",
    "description": "Flow with research capabilities and value monitoring"
  }
]
```

### Get Flow Definition

```
GET /flow/{flow_id}
```

Returns the definition of a specific flow.

**Response:**
```json
{
  "name": "basic-calculator",
  "description": "A simple calculator flow with Superego monitoring",
  "graph": {
    "start": "input_superego",
    "nodes": {
      "input_superego": {
        "type": "superego",
        "agent_id": "input_superego",
        "constitution": "Be helpful and accurate... [truncated]",
        "transitions": {
          "BLOCK": null,
          "ACCEPT": "calculator_agent",
          "CAUTION": "calculator_agent",
          "NEEDS_CLARIFICATION": "input_superego"
        }
      },
      "calculator_agent": {
        "type": "inner_agent",
        "agent_id": "calculator",
        "system_prompt": "You are a calculator agent...",
        "transitions": {
          "COMPLETE": null
        }
      }
    }
  }
}
```

### Execute Flow

```
POST /flow/execute
```

Executes a flow with the specified input and returns a streaming response.

**Request Body:**
```json
{
  "flow_id": "basic-calculator",
  "input": "Calculate 5*10",
  "conversation_id": "optional-conversation-id",
  "metadata": {} 
}
```

**Response:**
Server-Sent Events (SSE) stream with the following event types:

- `partial_output`: Streaming chunks of the response
- `complete_step`: Complete step information when an agent completes
- `error`: Error information if something goes wrong

Example events:

```
event: partial_output
data: {"type":"partial_output","data":{"partial_output":"I'll help"}}

event: partial_output
data: {"type":"partial_output","data":{"partial_output":"I'll help you calculate that."}}

event: complete_step
data: {"type":"complete_step","data":{"step_id":"1","agent_id":"input_superego","timestamp":"2023-11-15T10:30:46Z","role":"assistant","input":"Calculate 5*10","decision":"ACCEPT","response":"I'll help you calculate that."}}

event: partial_output
data: {"type":"partial_output","data":{"partial_output":"The result of 5*10 is "}}

event: partial_output
data: {"type":"partial_output","data":{"partial_output":"The result of 5*10 is 50."}}

event: complete_step
data: {"type":"complete_step","data":{"step_id":"2","agent_id":"calculator","timestamp":"2023-11-15T10:30:47Z","role":"assistant","input":"Calculate 5*10","response":"The result of 5*10 is 50.","tool_usage":{"tool_name":"calculator","input":"5*10","output":"50"}}}
```

### Tool Execution Confirmation

```
POST /flow/{instance_id}/confirm_tool
```

Confirms or denies a pending tool execution.

**Request Body:**
```json
{
  "tool_execution_id": "execution-id",
  "confirmed": true
}
```

**Response:**
```json
{
  "status": "success",
  "result": {
    "tool_name": "calculator",
    "input": "5*10",
    "output": "50"
  },
  "message": "Tool calculator executed successfully"
}
```

### Update Tool Confirmation Settings

```
POST /flow/{instance_id}/confirmation_settings
```

Updates tool confirmation settings for a flow instance.

**Request Body:**
```json
{
  "confirm_all": false,
  "exempted_tools": ["calculator", "search"]
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Tool confirmation settings updated",
  "settings": {
    "confirm_all": false,
    "exempted_tools": ["calculator", "search"]
  }
}
```

### Get Tool Confirmation Settings

```
GET /flow/{instance_id}/confirmation_settings
```

Gets current tool confirmation settings for a flow instance.

**Response:**
```json
{
  "confirm_all": true,
  "exempted_tools": []
}
```

## Data Models

### Complete Flow Step Structure

Each step in the flow represents an operation by a specific agent. The complete structure includes:

```json
{
  "step_id": str,         // Unique identifier for this step in the flow
  "agent_id": str,        // Identifier for specific agent: "superego", "research", "coding", etc.
  "timestamp": str,       // ISO timestamp when this step occurred
  "role": str,            // "user", "assistant", or "system"
  "input": str,           // Input message/content this agent received
  
  // Agent-specific fields - only one set will be present based on agent type
  // Superego-specific fields
  "constitution": str,    // For superego: the actual constitution text used
  "decision": str,        // BLOCK, ACCEPT, CAUTION, or NEEDS_CLARIFICATION
  
  // Inner agent-specific fields
  "system_prompt": str,   // Inner agent system instructions
  "tool_usage": {         // Present when tools are used
      "tool_name": str,
      "input": any,
      "output": any
  },
  
  // Common fields for all agents
  "thinking": str,        // Agent's reasoning process (not shown to user)
  "agent_guidance": str,  // Hidden inter-agent communication - passes context between agents
  "response": str,        // The agent's visible response to the user
  "next_agent": str       // The next agent to call (or null if flow ends)
}
```

**Important Notes for Frontend Developers:**
1. The fields `thinking` and `agent_guidance` are internal and not exposed in client-facing APIs
2. The complete structure is shown here for understanding, but client APIs will only receive a filtered subset
3. Different agent types will have different fields present (Superego vs Inner Agent)

### Flow Record

A flow record is an array of step records tracking the entire conversation history. This is crucial for frontend developers to understand the full conversation flow:

```json
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

### Superego Commands

Superego agents use these standardized commands to control flow. Frontend developers should be aware of these as they directly impact conversation flow and UI state:

```
BLOCK = "BLOCK"     # Reject the input entirely, conversation ends
ACCEPT = "ACCEPT"   # Allow the input without special handling
CAUTION = "CAUTION" # Allow with warning (agent_guidance passed to inner agent)
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"  # Recurse to get more info from user
```

### Inner Agent Commands

Inner agents use these commands to control their flow:

```
COMPLETE = "COMPLETE"           # End flow execution
NEEDS_TOOL = "NEEDS_TOOL"       # Self-loop for tool usage
NEEDS_RESEARCH = "NEEDS_RESEARCH"  # Transition to research agent
NEEDS_REVIEW = "NEEDS_REVIEW"   # Transition to review agent
ERROR = "ERROR"                 # Transition to error handler
```

## Flow Definition Schema

Flow definitions specify the agent graph structure and transition rules. This is crucial for frontend developers to understand the possible conversation paths:

```json
{
  "name": str,
  "description": str,
  "graph": {
    "start": str,  // Starting node name
    "nodes": {
      "node_name": {
        "type": str,      // "superego" or "inner_agent"
        "agent_id": str,  // Unique identifier for the agent
        "max_iterations": int,  // Maximum self-recursion count
        
        // Agent-specific configuration
        "constitution": str,  // For superego: full constitution text
        "system_prompt": str,  // For inner agents: system instructions
        "tools": [str],        // For inner agents: available tools
        
        // Flow control - defines where to go next based on agent decision
        "transitions": {
          "condition": str  // Next node name, null (end), or self (recursion)
        }
      }
    }
  }
}
```

### Transition Rules

Transition conditions map directly to agent decision values. These determine the flow of the conversation:

```
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

## Streaming Protocol

All agents in the system yield partial outputs as they're generated, which is crucial for frontend developers to implement a responsive UI:

- Streaming format: `{"partial_output": str, "complete": bool, "flow_step": dict}`
- Partial outputs contain incomplete responses during generation
- Complete=True indicates the final chunk with the full flow step

The API uses Server-Sent Events (SSE) for streaming results back to the client. The client should handle these event types:

1. `partial_output`: Contains incremental content updates during agent processing
2. `complete_step`: Contains a complete step record when an agent finishes
3. `error`: Contains error information if something goes wrong

Example client-side code for handling the stream:

```javascript
const eventSource = new EventSource('/flow/execute');

eventSource.addEventListener('partial_output', (event) => {
  const data = JSON.parse(event.data);
  // Update UI with streaming content
  appendToOutput(data.data.partial_output);
});

eventSource.addEventListener('complete_step', (event) => {
  const data = JSON.parse(event.data);
  // Handle complete step data
  processCompleteStep(data.data);
});

eventSource.addEventListener('error', (event) => {
  const data = JSON.parse(event.data);
  // Handle error
  showError(data.data.message);
  eventSource.close();
});
```

## Inter-Agent Communication

The `agent_guidance` field is a critical feature for inter-agent communication, though it's not directly exposed to frontend clients. Understanding this concept helps frontend developers visualize the agent interactions in their UI:

- Agent_guidance is never shown to users but is crucial for agent coordination
- It allows agents to pass context, warnings, or guidance to subsequent agents
- The Superego might accept a request but include guidance about potential concerns

Examples of effective agent_guidance messages that might influence the flow (not shown to users):
- "Request appears benign but contains ambiguous elements. Monitor for potential escalation."
- "Mathematical verification needed. Previous agent uncertain about calculation."
- "User seems frustrated. Consider acknowledging difficulty before answering."

## State Management

For frontend developers implementing conversation history and state:

- All flow steps are treated as immutable
- New steps are appended rather than modifying existing ones
- The system uses functional patterns for state updates
- Each step includes all necessary context

## Recursion and Cycles

Agents can call themselves or other agents. This is important to understand for implementing UI that can represent these complex flows:

- Track iteration counts per node to prevent infinite loops
- Self-transitions have explicit termination conditions
- Each agent determines when recursion is complete

## Creating Custom Flows

To create a custom flow (useful for frontend developers building flow editors or visualizers):

1. Define your flow in a JSON file in the `app/data/flow_definitions/` directory
2. Add any constitutions needed in the `app/data/constitutions/` directory
3. Follow the Flow Definition Schema shown above

Example minimal flow definition:

```json
{
  "name": "Simple Calculator",
  "description": "A basic calculator with value monitoring",
  "graph": {
    "start": "input_superego",
    "nodes": {
      "input_superego": {
        "type": "superego",
        "agent_id": "input_superego",
        "constitution": "default",
        "transitions": {
          "ACCEPT": "calculator",
          "CAUTION": "calculator",
          "BLOCK": null,
          "NEEDS_CLARIFICATION": "input_superego"
        }
      },
      "calculator": {
        "type": "inner_agent",
        "agent_id": "calculator",
        "system_prompt": "You are a helpful calculator that solves math problems.",
        "tools": ["calculator"],
        "transitions": {
          "COMPLETE": null,
          "NEEDS_TOOL": "calculator"
        }
      }
    }
  }
}
```

## Enhanced Multi-Agent Flow Example

For more complex applications, here's an example of a multi-agent flow that demonstrates how different specialized agents can work together:

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

Understanding the overall flow execution process is essential for frontend developers:

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

## Environment Configuration

The API server can be configured using these environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | HTTP server port | 8000 |
| `HOST` | HTTP server host | 0.0.0.0 |
| `BASE_MODEL` | Default LLM model | anthropic/claude-3.5-sonnet |
| `SUPEREGO_MODEL` | Model for superego agents | anthropic/claude-3.5-sonnet:thinking |
| `FRONTEND_URL` | CORS allowed origin | http://localhost:3000 |
| `OPENROUTER_API_KEY` | API key for OpenRouter | None |
| `FLOWS_DIRECTORY` | Path to flow definitions | app/data/flow_definitions |
| `CONSTITUTIONS_DIRECTORY` | Path to constitutions | app/data/constitutions |

## Dependencies

Understanding the system dependencies helps frontend developers set appropriate expectations:

- `langgraph` - For agent orchestration with cycle support
- `langchain` - For pre-built agent structures and tool interfaces
- `fastapi` - For API endpoints
- `sse-starlette` - For streaming
- `anyio` - For simplified async operations
- `pydantic` - For validation and serialization
- `orjson` - For JSON handling

## Frontend Integration Guidelines

When building a frontend for this API, consider these guidelines:

### 1. Streaming UI Design

Create a streaming-first interface:
- Show typing indicators during partial outputs
- Update progressively as content arrives
- Distinguish between different agent types visually
- Use animations or transitions for a fluid experience
- Implement buffering for smoother display of rapid stream chunks

### 2. Agent Identification

Help users understand which agent is responding:
- Color-code or visually distinguish different agent types (Superego vs Inner agents)
- Show appropriate icons for different agent types (shield for Superego, tools for specific agents)
- Clearly label which agent is currently responding
- Consider tooltips explaining agent roles and capabilities
- Use consistent visual language across the interface

### 3. Superego Visibility

Make the evaluation process transparent to users:
- Make Superego evaluation results visible to users when appropriate
- Show decision type (ACCEPT, BLOCK, CAUTION) with distinct visual treatments
- Consider collapsible sections for Superego evaluations
- Use color-coding for different decision types (green for ACCEPT, yellow for CAUTION, red for BLOCK)
- Allow users to view or hide this information based on preference

### 4. Tool Usage Visualization

Represent tool usage clearly:
- Show tool usage in a structured way
- Display tool inputs and outputs clearly
- Consider syntax highlighting for code outputs
- Use expandable/collapsible sections for tool calls
- Implement visualizations for numerical or data-heavy tool results
- Show loading states during tool execution

### 5. Flow Visualization

Consider visualizing the flow structure:
- Show which agents were involved in processing a request
- Highlight the current position in the flow
- Consider a simplified flowchart visualization
- Use breadcrumbs to show the path through different agents
- Implement transitions between agent states
- Visualize recursion and cycling in intuitive ways

### 6. Conversation History

Implement robust conversation tracking:
- Store and display the complete flow record
- Allow users to review previous exchanges
- Implement search and filtering by agent type
- Consider exporting/saving functionality
- Group related steps (like Superego evaluation + Inner agent response)

### 7. Error Handling

Design for graceful error recovery:
- Create clear error states that don't disrupt the conversation flow
- Implement retry mechanisms where appropriate
- Provide helpful context when errors occur
- Consider fallback options for failed requests

### 8. Responsive Design

Create an interface that works across devices:
- Ensure layouts adapt to different screen sizes
- Consider touch interfaces for tool interactions
- Implement responsive typography and UI elements
- Test across different browsers and platforms

## API Limitations

Frontend developers should be aware of these limitations:

- **No Authentication**: This research system doesn't include authentication - add your own if needed
- **No Rate Limiting**: Implement rate limiting at the reverse proxy level if required
- **Single User Mode**: The system isn't designed for concurrent multi-user operation
- **Limited Error Handling**: Error handling is minimal, consider adding more robust error handling in production
- **Research Focus**: The system prioritizes research capabilities over production-ready features
- **Minimal Abstraction**: The system uses a minimalist approach with few abstractions
- **No Built-in Metrics**: There's no built-in performance or usage monitoring

## Example Flow Execution

Here's a complete example of a flow execution that shows the entire process:

1. User sends: "Calculate 5*10"
2. System creates a user step with next_agent=input_superego
3. Superego evaluates input against its constitution
4. Superego streams thinking process (not visible to user)
5. Superego makes decision: ACCEPT
6. Superego creates agent_guidance: "Simple calculation request. Verify result."
7. Superego response streams to user: "I'll help you calculate that."
8. System routes to calculator agent based on transition rules
9. Calculator receives input and agent_guidance
10. Calculator uses calculator tool: input="5*10", output="50"
11. Calculator streams response: "The result of 5*10 is 50."
12. Flow completes (next_agent=null)
13. Complete flow record is available through API

## Extension Points

The API can be extended in several ways that frontend developers might want to support:

1. **New Agent Types**: Support for additional specialized agents
2. **Custom Tools**: Additional tools for agent use
3. **Custom Flow Patterns**: More complex agent interaction patterns
4. **Enhanced Constitutions**: More sophisticated value systems
5. **Visual Customization**: Theming and branding options
6. **Integration Hooks**: Connecting to external systems

## Development Philosophy and Implementation Principles

The system follows a set of core development principles that should be understood by frontend developers to maintain consistency across the project:

### Ruthless Minimalism

The codebase adheres to a philosophy of ruthless minimalism:
- **Code as Liability, Not Asset**: Every line must justify its existence
- **Library Over Custom Code**: Use existing libraries rather than reimplementing functionality
- **Avoid OOP Boilerplate**: No classes when maps/arrays suffice; no getters/setters for direct access
- **Functional Over Object-Oriented**: Favor pure functions over stateful objects
- **Flat Data Over Deep Hierarchies**: Prefer simple data structures over complex object hierarchies
- **No Unnecessary Abstraction**: Don't create wrapper functions, middleware, or transformation layers that add little value
- **Composition Over Inheritance**: Choose functional composition patterns instead of inheritance hierarchies

### Implementation Focus

- **Minimal Implementation**: Focused on research, not production
- **Functional Programming Patterns**: Using immutable flow records and pure functions
- **Explicit Tracking**: Clear tracking of agent identity and decision paths
- **Stream Directly**: Stream without unnecessary buffering
- **Comments Only for Non-Obvious Logic**: No documentation that restates what code already shows

These principles should guide frontend implementation as well. Prefer using library tools over custom implementations, avoid unnecessary abstractions, use functional patterns where possible, and maintain flat, simple data structures that mirror the backend's approach.

The mark of good system design in this project isn't how much you add - it's how much you remove while preserving capabilities.
