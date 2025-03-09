# WebSocket to REST API Migration Plan

## Overview

This plan outlines the steps to migrate all non-real-time operations from WebSockets to REST APIs in the Superego LangGraph application. After this migration, WebSockets will be used exclusively for real-time streaming operations, while all other operations will use REST APIs.

## Current Architecture Analysis

### Operations that should use WebSockets (real-time streaming):
- Streaming message tokens during generation
- Receiving real-time superego evaluations
- Sending user messages and receiving immediate responses

### Operations to migrate to REST APIs (non-real-time):
- Getting conversation history
- Getting/creating/updating/deleting flow instances
- Getting/creating/updating/deleting flow configs
- Getting/creating/updating/deleting flow templates
- Getting/creating/updating/deleting constitutions
- Getting/creating/updating/deleting system prompts
- Running parallel flows

## Migration Plan

### Phase 1: Backend REST API Development

1. **Create Conversations API**
   - Create a new file `backend/app/api/conversations.py`
   - Implement endpoints for:
     - Getting conversation history by ID
     - Updating conversation messages
     - Deleting conversations
   - These endpoints will use the existing conversation_manager.py functions

2. **Update API Router**
   - Add the new conversations router to `backend/app/api/router.py`

3. **Ensure Existing REST APIs are Complete**
   - Review existing REST APIs for flow instances, flow configs, flow templates, constitutions, and system prompts
   - Add any missing endpoints or functionality

### Phase 2: Frontend REST Client Updates

1. **Add Conversations API Client**
   - Update `frontend/src/api/restClient.ts` to add methods for:
     - Getting conversation history
     - Updating conversations
     - Deleting conversations

2. **Add React Query Hooks for Conversations**
   - Update `frontend/src/api/queryHooks.ts` to add hooks for:
     - Fetching conversation history
     - Updating conversations
     - Deleting conversations

### Phase 3: Component Updates

1. **Update Chat Component**
   - Modify `frontend/src/components/Chat.tsx` to:
     - Use REST API for fetching conversation history
     - Use REST API for updating conversations
     - Keep WebSockets only for real-time message streaming

2. **Update InstanceSidebar Component**
   - Ensure `frontend/src/components/InstanceSidebar.tsx` uses REST API for:
     - Fetching flow instances
     - Creating/updating/deleting flow instances

3. **Update ConstitutionManager Component**
   - Ensure `frontend/src/components/ConstitutionManager.tsx` uses REST API for:
     - Fetching constitutions
     - Creating/updating/deleting constitutions

4. **Update SyspromptSelector Component**
   - Ensure `frontend/src/components/SyspromptSelector.tsx` uses REST API for:
     - Fetching system prompts
     - Creating/updating/deleting system prompts

5. **Update ParallelFlowsView Component**
   - Modify `frontend/src/components/ParallelFlowsView.tsx` to:
     - Use REST API for fetching flow configs
     - Keep WebSockets only for real-time message streaming

### Phase 4: WebSocket Client Simplification

1. **Simplify WebSocketClient**
   - Update `frontend/src/api/websocketClient.ts` to:
     - Remove methods for non-real-time operations
     - Focus exclusively on real-time streaming operations

2. **Update WebSocket Message Handlers**
   - Remove handlers for operations migrated to REST API from:
     - `backend/app/websocket_endpoints.py`
     - `backend/app/websocket/message_handlers/flow.py`
     - `backend/app/websocket/message_handlers/user_messages.py`

### Phase 5: Testing and Validation

1. **Test REST API Endpoints**
   - Test each new and existing REST endpoint
   - Verify correct data retrieval, updates, and error handling

2. **Test Frontend Components**
   - Test each updated component
   - Verify they correctly use REST APIs for non-real-time operations
   - Verify they still use WebSockets for real-time operations

3. **Test End-to-End Functionality**
   - Test switching between conversations
   - Verify messages are properly persisted
   - Test rerunning messages with different constitutions

## Implementation Approach

1. **Incremental Migration**
   - Implement and test one feature at a time
   - Start with conversation history, then move to other features
   - Keep both WebSocket and REST implementations working in parallel during migration

2. **Feature Flags**
   - Use feature flags to gradually roll out REST API implementations
   - This allows for easy rollback if issues are discovered

3. **Comprehensive Testing**
   - Test each feature thoroughly after migration
   - Ensure no functionality is lost during the migration

## Expected Benefits

1. **Improved Code Organization**
   - Clear separation between real-time and non-real-time operations
   - More maintainable codebase

2. **Better Performance**
   - Reduced WebSocket traffic
   - Ability to leverage browser caching for static or semi-static data

3. **Enhanced Reliability**
   - Fewer potential points of failure
   - More robust error handling

4. **Fixed Issues**
   - Messages will be properly persisted when switching between conversations
   - "Chat updated with rerun results" message will appear correctly
