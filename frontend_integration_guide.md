# Frontend Integration Guide for Multi-Agent System

This guide explains how to integrate the frontend with the new multi-agent system. The frontend should be a thin client that instructs the backend and displays results without handling complex logic.

## API Endpoints

### 1. Process User Input

**Endpoint:** `/api/flow/process`

**Method:** POST

**Request Body:**
```json
{
  "user_input": "User message here",
  "conversation_id": "optional-conversation-id",
  "flow_instance_id": "optional-flow-instance-id"
}
```

**Response:**
```json
{
  "conversation_id": "conversation-id",
  "flow_instance_id": "flow-instance-id",
  "messages": [
    {
      "id": "message-id",
      "role": "user",
      "content": "User message",
      "timestamp": "2025-03-09T17:30:00.000Z"
    },
    {
      "id": "message-id",
      "role": "superego",
      "content": "Evaluation reason",
      "decision": "ALLOW",
      "thinking": "Evaluation thinking process",
      "timestamp": "2025-03-09T17:30:01.000Z"
    },
    {
      "id": "message-id",
      "role": "assistant",
      "content": "Assistant response",
      "timestamp": "2025-03-09T17:30:02.000Z"
    }
  ],
  "superego_evaluation": {
    "decision": "ALLOW",
    "reason": "Evaluation reason",
    "thinking": "Evaluation thinking process"
  },
  "tools_used": [
    {
      "name": "calculator",
      "arguments": {
        "expression": "2 + 2"
      },
      "output": "Result: 4"
    }
  ]
}
```

### 2. Stream User Input Processing

**Endpoint:** `/api/flow/stream`

**Method:** WebSocket

**Message Format (Client to Server):**
```json
{
  "type": "user_message",
  "content": {
    "user_input": "User message here",
    "conversation_id": "optional-conversation-id",
    "flow_instance_id": "optional-flow-instance-id"
  }
}
```

**Message Format (Server to Client):**

1. Superego Evaluation:
```json
{
  "type": "superego_evaluation",
  "content": {
    "decision": "ALLOW",
    "reason": "Evaluation reason",
    "thinking": "Evaluation thinking process"
  }
}
```

2. Assistant Token (for streaming):
```json
{
  "type": "assistant_token",
  "content": "token"
}
```

3. Tool Usage:
```json
{
  "type": "tool_usage",
  "content": {
    "name": "calculator",
    "arguments": {
      "expression": "2 + 2"
    },
    "output": "Result: 4"
  }
}
```

4. Completion:
```json
{
  "type": "flow_completed",
  "content": {
    "conversation_id": "conversation-id",
    "flow_instance_id": "flow-instance-id"
  }
}
```

## UI Components

### 1. Message Display

- Display messages from different roles with distinct styling:
  - User messages
  - Assistant messages
  - Superego evaluations (optional, can be hidden by default)

### 2. Tool Result Display

- When tools are used, display the tool results in a structured way
- For calculator results, show the expression and result

### 3. Streaming Support

- Support for streaming tokens from the assistant
- Show typing indicator while waiting for response

### 4. Error Handling

- Display appropriate error messages when:
  - The superego blocks a message
  - A tool encounters an error
  - The backend returns an error

## Example Integration

```typescript
// Example of sending a message and handling the response
async function sendMessage(userInput: string, conversationId?: string) {
  setIsLoading(true);
  
  try {
    const response = await fetch('/api/flow/process', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_input: userInput,
        conversation_id: conversationId,
      }),
    });
    
    const result = await response.json();
    
    // Update conversation with new messages
    setMessages(prevMessages => [...prevMessages, ...result.messages]);
    
    // Store conversation ID for future messages
    setConversationId(result.conversation_id);
    
    // Handle tools used
    if (result.tools_used && result.tools_used.length > 0) {
      // Display tool results
      setToolResults(result.tools_used);
    }
  } catch (error) {
    console.error('Error sending message:', error);
    setError('Failed to send message. Please try again.');
  } finally {
    setIsLoading(false);
  }
}
```

## WebSocket Example

```typescript
// Example of setting up a WebSocket connection for streaming
function setupWebSocket() {
  const ws = new WebSocket('ws://localhost:8000/ws');
  
  ws.onopen = () => {
    console.log('WebSocket connected');
  };
  
  ws.onmessage = (event) => {
    const message = JSON.parse(event.data);
    
    switch (message.type) {
      case 'superego_evaluation':
        // Handle superego evaluation
        setSuperEgoEvaluation(message.content);
        break;
        
      case 'assistant_token':
        // Append token to current message
        appendToken(message.content);
        break;
        
      case 'tool_usage':
        // Display tool usage
        addToolResult(message.content);
        break;
        
      case 'flow_completed':
        // Mark flow as completed
        setFlowCompleted(true);
        break;
        
      default:
        console.log('Unknown message type:', message.type);
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    setError('WebSocket connection error');
  };
  
  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Attempt to reconnect
    setTimeout(setupWebSocket, 3000);
  };
  
  return ws;
}
```

## Important Considerations

1. **Thin Client Approach**: The frontend should not handle complex logic. All processing should be done on the backend.

2. **Error Handling**: Display appropriate error messages to the user when things go wrong.

3. **Streaming Support**: Implement streaming support for a better user experience.

4. **Tool Results**: Display tool results in a structured and user-friendly way.

5. **Superego Evaluations**: Consider whether to show superego evaluations to the user. This might be a configurable option.

6. **Conversation History**: Store and display the conversation history, including all messages from different roles.
    setHasError(false);
