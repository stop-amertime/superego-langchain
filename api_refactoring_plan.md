# API Refactoring Plan: Moving from WebSockets to Hybrid REST/WebSocket Architecture

## Current Issues

1. The WebSocket endpoint (`websocket_endpoints.py`) has grown too large and complex
2. Many operations don't require real-time bidirectional communication
3. Message type dispatching logic is becoming unwieldy
4. Error handling is complex
5. JSON serialization issues with Pydantic models (e.g., FlowConfig)

## Proposed Solution

Implement a hybrid architecture:

1. **REST API** for CRUD operations and non-streaming data
2. **WebSockets** only for real-time streaming operations

## Benefits

1. Clearer separation of concerns
2. More maintainable codebase
3. Standard REST patterns for data operations
4. Simplified WebSocket handler focused only on streaming
5. Easier testing and debugging
6. Better error handling

## Implementation Plan

### 1. Create REST API Router Structure

Create a new file `backend/app/api/router.py` with FastAPI routers for:

- Constitutions
- System Prompts
- Flow Templates
- Flow Configs
- Flow Instances

### 2. Implement JSON Serialization Fix

Update the Pydantic models to ensure proper JSON serialization:

1. Add a custom JSON encoder for Pydantic models
2. Implement model methods for proper serialization

### 3. Create REST API Endpoints

For each resource type, implement:

- GET (list all)
- GET /{id} (get one)
- POST (create)
- PUT /{id} (update)
- DELETE /{id} (delete)

### 4. Simplify WebSocket Handler

Refactor `websocket_endpoints.py` to focus only on:

- User message processing
- Streaming LLM responses
- Streaming superego thinking
- Real-time notifications

### 5. Update Frontend API Client

Create a new REST API client in the frontend and update the WebSocket client to handle only streaming operations.

### 6. Update Frontend Components

Update components to use the appropriate API client based on the operation.

## Detailed Implementation Steps

### Phase 1: Backend Restructuring

1. **Create API Package Structure**
   ```
   backend/app/api/
   ├── __init__.py
   ├── router.py              # Main router that combines all sub-routers
   ├── constitutions.py       # Constitution endpoints
   ├── sysprompts.py          # System prompt endpoints
   ├── flow_templates.py      # Flow template endpoints
   ├── flow_configs.py        # Flow config endpoints
   ├── flow_instances.py      # Flow instance endpoints
   └── utils.py               # Shared utilities
   ```

2. **Fix JSON Serialization**
   - Update Pydantic models to ensure proper JSON serialization
   - Add custom JSON encoder if needed

3. **Implement REST Endpoints**
   - Move CRUD operations from WebSocket handler to REST endpoints
   - Ensure proper error handling and status codes

4. **Simplify WebSocket Handler**
   - Remove all non-streaming operations
   - Focus on real-time communication only

### Phase 2: Frontend Updates

1. **Create REST API Client**
   ```
   frontend/src/api/
   ├── restClient.ts          # New REST API client
   ├── websocketClient.ts     # Simplified WebSocket client
   └── apiTypes.ts            # Shared API types
   ```

2. **Update Components**
   - Modify components to use the appropriate client
   - Update error handling

### Phase 3: Testing and Deployment

1. **Test REST Endpoints**
   - Verify all CRUD operations work correctly
   - Test error handling

2. **Test WebSocket Streaming**
   - Verify streaming still works correctly
   - Test reconnection logic

3. **Deploy and Monitor**
   - Deploy the updated application
   - Monitor for any issues

## Specific API Endpoints to Implement

### Constitutions API

```
GET    /api/constitutions          # List all constitutions
GET    /api/constitutions/{id}     # Get a specific constitution
POST   /api/constitutions          # Create a new constitution
PUT    /api/constitutions/{id}     # Update a constitution
DELETE /api/constitutions/{id}     # Delete a constitution
```

### System Prompts API

```
GET    /api/sysprompts             # List all system prompts
GET    /api/sysprompts/{id}        # Get a specific system prompt
POST   /api/sysprompts             # Create a new system prompt
PUT    /api/sysprompts/{id}        # Update a system prompt
DELETE /api/sysprompts/{id}        # Delete a system prompt
```

### Flow Templates API

```
GET    /api/flow-templates         # List all flow templates
GET    /api/flow-templates/{id}    # Get a specific flow template
POST   /api/flow-templates         # Create a new flow template
PUT    /api/flow-templates/{id}    # Update a flow template
DELETE /api/flow-templates/{id}    # Delete a flow template
```

### Flow Configs API

```
GET    /api/flow-configs           # List all flow configs
GET    /api/flow-configs/{id}      # Get a specific flow config
POST   /api/flow-configs           # Create a new flow config
PUT    /api/flow-configs/{id}      # Update a flow config
DELETE /api/flow-configs/{id}      # Delete a flow config
```

### Flow Instances API

```
GET    /api/flow-instances         # List all flow instances
GET    /api/flow-instances/{id}    # Get a specific flow instance
POST   /api/flow-instances         # Create a new flow instance
PUT    /api/flow-instances/{id}    # Update a flow instance
DELETE /api/flow-instances/{id}    # Delete a flow instance
```

## WebSocket Operations to Keep

1. User message processing
2. Streaming LLM responses (token by token)
3. Streaming superego thinking
4. Real-time notifications
5. Parallel flow execution (which requires streaming)

## Timeline

1. **Phase 1 (Backend Restructuring)**: 2-3 days
2. **Phase 2 (Frontend Updates)**: 1-2 days
3. **Phase 3 (Testing and Deployment)**: 1 day

Total estimated time: 4-6 days
