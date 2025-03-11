# Superego LangGraph API Documentation

This document provides comprehensive documentation for the Superego LangGraph backend API, intended for frontend developers to integrate with the backend.

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [REST API Endpoints](#rest-api-endpoints)
   - [Health Check](#health-check)
   - [Constitutions API](#constitutions-api)
   - [System Prompts API](#system-prompts-api)
   - [Flow Definitions API](#flow-definitions-api)
   - [Flow Instances API](#flow-instances-api)
   - [Messages API](#messages-api)
4. [WebSocket API](#websocket-api)
   - [Connection](#connection)
   - [Message Types](#message-types)
   - [User Message Flow](#user-message-flow)
   - [Flow Operations](#flow-operations)
5. [Data Models](#data-models)
   - [Message Models](#message-models)
   - [Flow Models](#flow-models)
   - [Agent Models](#agent-models)
6. [Flow Engine](#flow-engine)
   - [Concepts](#concepts)
   - [Flow Configuration](#flow-configuration)
   - [Node Types](#node-types)
7. [Error Handling](#error-handling)
8. [Best Practices](#best-practices)

## Overview

The Superego LangGraph API provides both REST and WebSocket interfaces for interacting with the SuperEgo language model system. The API allows you to:

- Create and manage constitutions (rule sets for message governance)
- Configure and manage system prompts
- Define and execute flows (sequences of AI operations)
- Send messages and receive responses with SuperEgo evaluation
- Process streaming responses in real-time

The API is built with FastAPI and provides both synchronous REST endpoints and asynchronous WebSocket communication.

## Authentication

Currently, the API does not implement authentication. All endpoints are publicly accessible. However, the API requires a valid OpenRouter API key to be set in the environment variables for AI model calls to function correctly.

Required environment variable:
- `OPENROUTER_API_KEY`: Your OpenRouter API key for accessing language models

## REST API Endpoints

### Health Check

#### `GET /`

Check if the API server is running.

**Response:**
```json
{
  "status": "ok",
  "message": "Superego LangGraph API is running"
}
```

#### `GET /api`

Check API status and configuration.

**Response:**
```json
{
  "status": "ok",
  "api_ready": true,
  "config": {
    "has_api_key": true
  }
}
```

### Constitutions API

Constitutions define rules for message governance and are used by the SuperEgo to evaluate messages.

#### `GET /api/constitutions/`

Get all available constitutions.

**Response:**
```json
{
  "success": true,
  "data": {
    "default": {
      "id": "default",
      "name": "Default Constitution",
      "content": "..."
    },
    "strict": {
      "id": "strict",
      "name": "Strict Constitution",
      "content": "..."
    }
  }
}
```

#### `GET /api/constitutions/{constitution_id}`

Get a specific constitution by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "default",
    "name": "Default Constitution",
    "content": "..."
  }
}
```

#### `POST /api/constitutions/`

Create a new constitution.

**Request:**
```json
{
  "id": "custom",
  "name": "Custom Constitution",
  "content": "# Custom rules\n1. Be helpful\n2. Be respectful"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "custom",
    "name": "Custom Constitution",
    "content": "# Custom rules\n1. Be helpful\n2. Be respectful"
  },
  "message": "Constitution 'Custom Constitution' created successfully"
}
```

#### `PUT /api/constitutions/{constitution_id}`

Update an existing constitution.

**Request:**
```json
{
  "name": "Updated Constitution",
  "content": "# Updated rules\n1. Be helpful\n2. Be respectful\n3. Be accurate"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "custom",
    "name": "Updated Constitution",
    "content": "# Updated rules\n1. Be helpful\n2. Be respectful\n3. Be accurate"
  },
  "message": "Constitution 'Updated Constitution' updated successfully"
}
```

#### `DELETE /api/constitutions/{constitution_id}`

Delete a constitution. Protected constitutions (e.g., "default", "none") cannot be deleted.

**Response:**
```json
{
  "success": true,
  "message": "Constitution 'Custom Constitution' deleted successfully"
}
```

### System Prompts API

System Prompts provide initial instructions to the assistant model.

**Note:** The system prompts API endpoints follow the same pattern as the constitutions API. You can use similar endpoints to get, create, update, and delete system prompts.

### Flow Definitions API

Flow definitions describe the structure and behavior of AI processing flows.

#### `GET /api/flow-definitions/`

Get all flow definitions.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "default-flow",
      "name": "Default Flow",
      "description": "Standard processing flow with SuperEgo evaluation",
      "nodes": {
        "user_input": {
          "type": "input",
          "config": {}
        },
        "superego": {
          "type": "superego",
          "config": {
            "constitution_id": "default"
          }
        },
        "assistant": {
          "type": "assistant",
          "config": {
            "model": "anthropic/claude-3-opus-20240229"
          }
        }
      },
      "edges": [
        {
          "from_node": "user_input",
          "to_node": "superego"
        },
        {
          "from_node": "superego",
          "to_node": "assistant"
        }
      ],
      "created_at": "2024-03-09T12:00:00.000Z",
      "updated_at": "2024-03-09T12:00:00.000Z"
    }
  ]
}
```

#### `GET /api/flow-definitions/{definition_id}`

Get a specific flow definition by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "default-flow",
    "name": "Default Flow",
    "description": "Standard processing flow with SuperEgo evaluation",
    "nodes": {
      "user_input": {
        "type": "input",
        "config": {}
      },
      "superego": {
        "type": "superego",
        "config": {
          "constitution_id": "default"
        }
      },
      "assistant": {
        "type": "assistant",
        "config": {
          "model": "anthropic/claude-3-opus-20240229"
        }
      }
    },
    "edges": [
      {
        "from_node": "user_input",
        "to_node": "superego"
      },
      {
        "from_node": "superego",
        "to_node": "assistant"
      }
    ],
    "created_at": "2024-03-09T12:00:00.000Z",
    "updated_at": "2024-03-09T12:00:00.000Z"
  }
}
```

#### `POST /api/flow-definitions/`

Create a new flow definition.

**Request:**
```json
{
  "name": "Custom Flow",
  "description": "Custom processing flow with multiple assistants",
  "nodes": {
    "user_input": {
      "type": "input",
      "config": {}
    },
    "superego": {
      "type": "superego",
      "config": {
        "constitution_id": "strict"
      }
    },
    "assistant_1": {
      "type": "assistant",
      "config": {
        "model": "anthropic/claude-3-haiku-20240307"
      }
    },
    "assistant_2": {
      "type": "assistant",
      "config": {
        "model": "anthropic/claude-3-opus-20240229"
      }
    }
  },
  "edges": [
    {
      "from_node": "user_input",
      "to_node": "superego"
    },
    {
      "from_node": "superego",
      "to_node": "assistant_1",
      "condition": "decision == 'ALLOW'"
    },
    {
      "from_node": "superego",
      "to_node": "assistant_2",
      "condition": "decision == 'CAUTION'"
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "flow-12345",
    "name": "Custom Flow",
    "description": "Custom processing flow with multiple assistants",
    "nodes": {
      /* nodes from request */
    },
    "edges": [
      /* edges from request */
    ],
    "created_at": "2024-03-09T15:30:00.000Z",
    "updated_at": "2024-03-09T15:30:00.000Z"
  },
  "message": "Flow definition 'Custom Flow' created successfully"
}
```

#### `PUT /api/flow-definitions/{definition_id}`

Update an existing flow definition.

**Request:**
```json
{
  "name": "Updated Flow",
  "description": "Updated flow description"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "flow-12345",
    "name": "Updated Flow",
    "description": "Updated flow description",
    /* remaining fields unchanged */
  },
  "message": "Flow definition 'Updated Flow' updated successfully"
}
```

#### `POST /api/flow-definitions/default`

Create a default flow definition.

**Response:**
```json
{
  "success": true,
  "data": {
    /* default flow definition */
  },
  "message": "Default flow definition created successfully"
}
```

### Flow Instances API

Flow instances are running instances of flow definitions.

#### `GET /api/flow-instances/`

Get all flow instances.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "instance-12345",
      "flow_definition_id": "default-flow",
      "name": "Chat Session 1",
      "description": "User conversation with default flow",
      "current_node": "assistant",
      "status": "running",
      "created_at": "2024-03-09T14:00:00.000Z",
      "updated_at": "2024-03-09T14:10:00.000Z",
      "last_message_at": "2024-03-09T14:10:00.000Z"
    }
  ]
}
```

#### `GET /api/flow-instances/{instance_id}`

Get a specific flow instance by ID.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "instance-12345",
    "flow_definition_id": "default-flow",
    "name": "Chat Session 1",
    "description": "User conversation with default flow",
    "current_node": "assistant",
    "status": "running",
    "messages": [
      /* list of messages in this flow instance */
    ],
    "history": [
      /* list of node executions */
    ],
    "agent_states": {
      /* states of agents in this flow */
    },
    "tool_usages": [
      /* list of tool usages */
    ],
    "parameters": {
      /* flow parameters */
    },
    "created_at": "2024-03-09T14:00:00.000Z",
    "updated_at": "2024-03-09T14:10:00.000Z",
    "last_message_at": "2024-03-09T14:10:00.000Z"
  }
}
```

#### `POST /api/flow-instances/`

Create a new flow instance from a flow definition.

**Request:**
```json
{
  "flow_definition_id": "default-flow",
  "name": "New Chat Session",
  "description": "User conversation with default flow",
  "parameters": {
    "assistant": {
      "model": "anthropic/claude-3-opus-20240229"
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "instance-67890",
    "flow_definition_id": "default-flow",
    "name": "New Chat Session",
    "description": "User conversation with default flow",
    "current_node": null,
    "status": "created",
    "messages": [],
    "history": [],
    "agent_states": {},
    "tool_usages": [],
    "parameters": {
      "assistant": {
        "model": "anthropic/claude-3-opus-20240229"
      }
    },
    "created_at": "2024-03-09T15:30:00.000Z",
    "updated_at": "2024-03-09T15:30:00.000Z",
    "last_message_at": null
  },
  "message": "Flow instance 'New Chat Session' created successfully"
}
```

#### `PUT /api/flow-instances/{instance_id}`

Update an existing flow instance.

**Request:**
```json
{
  "name": "Updated Chat Session",
  "description": "Updated description"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "instance-67890",
    "name": "Updated Chat Session",
    "description": "Updated description",
    /* remaining fields unchanged */
  },
  "message": "Flow instance 'Updated Chat Session' updated successfully"
}
```

#### `DELETE /api/flow-instances/{instance_id}`

Delete a flow instance.

**Response:**
```json
{
  "success": true,
  "message": "Flow instance 'Updated Chat Session' deleted successfully"
}
```

### Messages API

The Messages API allows you to manage message stores, which contain conversations.

#### `GET /api/messages/`

Get all message stores with optional pagination.

**Query Parameters:**
- `limit` (optional): Limit the number of message stores
- `offset` (optional): Offset for pagination

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "store-12345",
      "messages": [
        /* list of messages */
      ],
      "message_count": 10,
      "last_updated": "2024-03-09T14:10:00.000Z"
    }
  ]
}
```

#### `GET /api/messages/{message_store_id}`

Get a specific message store by ID with optional pagination.

**Query Parameters:**
- `limit` (optional): Limit the number of messages
- `offset` (optional): Offset for pagination

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "store-12345",
    "messages": [
      {
        "id": "msg-1",
        "role": "user",
        "content": "Hello, world!",
        "timestamp": "2024-03-09T14:00:00.000Z"
      },
      {
        "id": "msg-2",
        "role": "superego",
        "content": "This message is allowed",
        "timestamp": "2024-03-09T14:00:05.000Z",
        "decision": "ALLOW",
        "constitutionId": "default",
        "thinking": "The message is harmless and friendly"
      },
      {
        "id": "msg-3",
        "role": "assistant",
        "content": "Hello! How can I help you today?",
        "timestamp": "2024-03-09T14:00:10.000Z"
      }
    ],
    "total_messages": 3
  }
}
```

#### `POST /api/messages/`

Create a new empty message store.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "store-67890",
    "messages": []
  }
}
```

#### `PUT /api/messages/{message_store_id}`

Update a message store with new messages.

**Request:**
```json
[
  {
    "id": "msg-1",
    "role": "user",
    "content": "Hello, world!",
    "timestamp": "2024-03-09T14:00:00.000Z"
  },
  {
    "id": "msg-2",
    "role": "assistant",
    "content": "Hello! How can I help you today?",
    "timestamp": "2024-03-09T14:00:10.000Z"
  }
]
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "store-67890",
    "messages": [
      /* messages from request */
    ],
    "message_count": 2
  }
}
```

#### `DELETE /api/messages/{message_store_id}`

Delete a message store.

**Response:**
```json
{
  "success": true,
  "message": "Message store store-67890 deleted successfully"
}
```

## WebSocket API

The WebSocket API provides real-time, bidirectional communication for streaming responses, SuperEgo evaluations, and flow state updates.

### Connection

Connect to the WebSocket endpoint:

```
ws://your-server/ws/{client_id}
```

Where `client_id` is a unique identifier for the client. This can be any string, but using a UUID is recommended.

### Message Types

All WebSocket messages follow this format:

```json
{
  "type": "message_type",
  "content": { /* message-specific content */ },
  "timestamp": "2024-03-09T14:00:00.000Z"
}
```

#### Incoming Message Types (Client to Server)

- `user_message`: Send a user message
- `flow`: Perform flow operations

#### Outgoing Message Types (Server to Client)

- `user_message`: User message received
- `superego_evaluation`: SuperEgo evaluation result
- `assistant_message`: Complete assistant message
- `assistant_token`: Single token from an assistant message (for streaming)
- `tool_usage`: Tool usage information
- `superego_intervention`: SuperEgo intervention
- `error`: Error information
- `system_message`: System message
- `constitutions_response`: List of available constitutions
- `rerun_from_constitution`: Response to a rerun request with a different constitution
- `sysprompts_response`: List of available system prompts
- `conversation_update`: Full conversation update
- `flow_templates_response`: List of available flow templates
- `flow_configs_response`: List of flow configurations
- `flow_instances_response`: List of flow instances
- `parallel_flows_result`: Result from running multiple flows
- `flow_state_update`: Update on flow state changes
- `flow_node_transition`: When flow transitions between nodes
- `flow_node_thinking`: Thinking output from a node
- `flow_node_output`: Output from a node
- `flow_definition_response`: Response with flow definitions
- `flow_completed`: When a flow completes
- `flow_error`: When a flow encounters an error

### User Message Flow

To send a user message:

```json
{
  "type": "user_message",
  "content": {
    "message": "Hello, world!",
    "conversationId": "optional-conversation-id"
  }
}
```

The server will respond with a series of messages:

1. First, a `user_message` acknowledgment
2. Then, a `superego_evaluation` with the evaluation result
3. If the message is allowed, streaming `assistant_token` messages
4. Finally, a complete `assistant_message`

Example responses:

```json
{
  "type": "user_message",
  "content": {
    "id": "msg-1",
    "role": "user",
    "content": "Hello, world!",
    "timestamp": "2024-03-09T14:00:00.000Z"
  },
  "timestamp": "2024-03-09T14:00:00.000Z"
}
```

```json
{
  "type": "superego_evaluation",
  "content": {
    "decision": "ALLOW",
    "reason": "The message is harmless and friendly",
    "thinking": "Detailed thinking process...",
    "timestamp": "2024-03-09T14:00:05.000Z",
    "constitutionId": "default"
  },
  "timestamp": "2024-03-09T14:00:05.000Z"
}
```

```json
{
  "type": "assistant_token",
  "content": {
    "token": "Hello",
    "conversationId": "conv-12345"
  },
  "timestamp": "2024-03-09T14:00:06.000Z"
}
```

```json
{
  "type": "assistant_message",
  "content": {
    "id": "msg-3",
    "role": "assistant",
    "content": "Hello! How can I help you today?",
    "timestamp": "2024-03-09T14:00:10.000Z"
  },
  "timestamp": "2024-03-09T14:00:10.000Z"
}
```

### Flow Operations

To perform flow operations:

```json
{
  "type": "flow",
  "content": {
    "operation": "start",
    "flow_instance_id": "instance-12345",
    "user_input": "Hello, world!"
  }
}
```

Available operations:
- `start`: Start a flow instance with user input
- `pause`: Pause a running flow instance
- `resume`: Resume a paused flow instance
- `stop`: Stop a running flow instance
- `get_instance`: Get a flow instance by ID
- `list_instances`: List all flow instances
- `create_instance`: Create a new flow instance
- `update_instance`: Update a flow instance
- `delete_instance`: Delete a flow instance

## Data Models

### Message Models

#### Message
```typescript
{
  id: string;
  role: 'user' | 'assistant' | 'superego' | 'system';
  content: string;
  timestamp: string;
  decision?: 'ALLOW' | 'BLOCK' | 'CAUTION' | 'ANALYZING' | 'ERROR';
  constitutionId?: string;
  thinking?: string;
  thinkingTime?: string;
  withoutSuperego?: string;
}
```

#### SuperegoEvaluation
```typescript
{
  decision: 'ALLOW' | 'BLOCK' | 'CAUTION' | 'ANALYZING' | 'ERROR';
  reason: string;
  thinking?: string;
  timestamp?: string;
  constitutionId?: string;
  status?: string;
  id?: string;
}
```

### Flow Models

#### NodeConfig
```typescript
{
  type: string;
  config: Record<string, any>;
}
```

#### EdgeConfig
```typescript
{
  from_node: string;
  to_node: string;
  condition?: string;
}
```

#### FlowDefinition
```typescript
{
  id: string;
  name: string;
  description?: string;
  nodes: Record<string, NodeConfig>;
  edges: EdgeConfig[];
  created_at: string;
  updated_at: string;
}
```

#### FlowConfig
```typescript
{
  id: string;
  name: string;
  constitution_id: string;
  sysprompt_id?: string;
  superego_enabled: boolean;
  description?: string;
  created_at: string;
  updated_at: string;
}
```

#### FlowInstance
```typescript
{
  id: string;
  flow_definition_id: string;
  current_node?: string;
  status: 'created' | 'running' | 'paused' | 'completed' | 'error';
  name: string;
  description?: string;
  messages: Message[];
  history: NodeExecution[];
  agent_states: Record<string, Record<string, any>>;
  tool_usages: ToolUsage[];
  parameters: Record<string, Record<string, any>>;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
}
```

### Agent Models

#### AgentState
```typescript
{
  conversation_id: string;
  messages: Message[];
  user_input: string;
  superego_evaluation?: SuperegoEvaluation;
  current_output: string;
  interrupted: boolean;
  tools_used: Array<Record<string, any>>;
}
```

#### ToolUsage
```typescript
{
  tool_name: string;
  input_data: Record<string, any>;
  output: any;
  timestamp: string;
}
```

## Flow Engine

The Flow Engine manages the execution of flows, which are sequences of operations performed on messages.

### Concepts

- **Flow Definition**: A blueprint that defines the structure of a flow, including nodes and edges.
- **Flow Instance**: A running instance of a flow definition with its own state and history.
- **Node**: A processing unit in a flow (e.g., user input, SuperEgo evaluation, assistant response).
- **Edge**: A connection between nodes that defines the flow of data.
- **Node Execution**: A record of a node's execution, including input and output.

### Flow Configuration

Flow configurations define how a flow should be executed, including which constitution and system prompt to use.

```json
{
  "id": "config-12345",
  "name": "Default Configuration",
  "constitution_id": "default",
  "sysprompt_id": "assistant_default",
  "superego_enabled": true,
  "description": "Default configuration with SuperEgo"
}
```

### Node Types

- **input**: Represents user input
- **superego**: Performs SuperEgo evaluation
- **assistant**: Generates assistant responses
- **tool**: Executes a tool or function

Example node configuration:

```json
{
  "type": "assistant",
  "config": {
    "model": "anthropic/claude-3-opus-20240229",
    "temperature": 0.7,
    "max_tokens": 1000
  }
}
```

## Error Handling

The API returns standard HTTP error codes:

- `400 Bad Request`: Invalid request format or parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

WebSocket errors are sent with the `error` message type:

```json
{
  "type": "error",
  "content": {
    "message": "Error description",
    "error_code": "ERROR_CODE"
  },
  "timestamp": "2024-03-09T14:00:00.000Z"
}
```

Common error codes:
- `INVALID_JSON`: Invalid JSON received
- `UNKNOWN_MESSAGE_TYPE`: Unknown WebSocket message type
- `INTERNAL_ERROR`: Server-side error
- `FLOW_NOT_FOUND`: Flow instance not found
- `FLOW_EXECUTION_ERROR`: Error executing flow

## Best Practices

1. **Use WebSockets for Interactive Features**
   - WebSockets provide real-time updates and streaming responses
   - Ideal for chat interfaces and live updates

2. **Manage Flow Instances**
   - Create a new flow instance for each conversation
   - Use flow parameters to customize behavior
   - Delete unused flow instances to save resources

3. **Handle SuperEgo Decisions**
   - Always check the SuperEgo decision before displaying assistant responses
   - Provide appropriate UI for different decisions (ALLOW, BLOCK, CAUTION)

4. **Error Handling**
   - Implement robust error handling for both REST and WebSocket APIs
   - Display user-friendly error messages
   - Retry operations when appropriate

5. **Performance Considerations**
   - WebSocket connections should be established once and reused
   - Use pagination for large data sets
   - Consider caching frequent requests like constitutions and system prompts
