# WebSocket to REST API Migration

This project migrates non-real-time operations from WebSockets to REST APIs in the Superego LangGraph application. After this migration, WebSockets are used exclusively for real-time streaming operations, while all other operations use REST APIs.

## Changes Made

### Backend Changes

1. **Created Conversations API**
   - Created a new file `backend/app/api/conversations.py` with endpoints for:
     - Getting all conversations with pagination
     - Getting conversation history by ID with pagination
     - Creating new conversations
     - Updating conversation messages
     - Deleting conversations
   - Added the conversations router to `backend/app/api/router.py`

2. **Simplified WebSocket Endpoints**
   - Created a simplified version of the WebSocket endpoints in `backend/app/websocket_endpoints_simplified.py` that:
     - Keeps only handlers for real-time operations (user_message, rerun_message, rerun_from_constitution, run_parallel_flows)
     - Removes handlers for operations migrated to REST API (get_constitutions, get_system_prompts, get_flow_templates, etc.)
     - Uses the conversation_manager.get_conversation() function to fetch conversation history from persistent storage

3. **Created Simplified Main Application**
   - Created a simplified version of the main application in `backend/app/main_simplified.py` that:
     - Uses the simplified WebSocket endpoints directly
     - Keeps all the REST API endpoints

4. **Created Script to Run Simplified Application**
   - Created a script to run the simplified version of the application in `backend/run_simplified.py`

### Frontend Changes

1. **Updated REST Client**
   - Updated `frontend/src/api/restClient.ts` to add methods for:
     - Getting all conversations with pagination
     - Getting conversation history by ID with pagination
     - Creating new conversations
     - Updating conversations
     - Deleting conversations

2. **Added React Query Hooks**
   - Updated `frontend/src/api/queryHooks.ts` to add hooks for:
     - Fetching all conversations
     - Fetching conversation history
     - Creating conversations
     - Updating conversations
     - Deleting conversations

3. **Updated Components**
   - Modified `frontend/src/components/Chat.tsx` to:
     - Use REST API for fetching conversation history
     - Use REST API for updating conversations
     - Keep WebSockets only for real-time message streaming
   - Modified `frontend/src/components/InstanceSidebar.tsx` to:
     - Make props optional since it's using React Query hooks
     - Use React Query hooks exclusively for data fetching
   - Updated `frontend/src/App.tsx` to:
     - Remove WebSocket-based data fetching for flow instances and configs
     - Use React Query hooks for flow instances and configs
     - Remove unnecessary props passed to InstanceSidebar

4. **Simplified WebSocketClient**
   - Updated `frontend/src/api/websocketClient.ts` to:
     - Removed `requestConversationHistory` method
     - Removed `onConversationUpdate` callback
     - Removed handling of non-real-time message types
     - Focused exclusively on real-time streaming operations

## Running the Simplified Application

To run the simplified version of the application:

1. Start the backend server:
   ```bash
   cd backend
   python run_simplified.py
   ```

2. Start the frontend development server:
   ```bash
   cd frontend
   npm run dev
   ```

3. Open your browser and navigate to http://localhost:3000

## Testing

To verify that the migration was successful:

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

## Benefits of the Migration

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
   - Messages are properly persisted when switching between conversations
   - "Chat updated with rerun results" message appears correctly
