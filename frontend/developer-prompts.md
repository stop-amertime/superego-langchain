# Development Prompts for Superego Frontend Components

These prompts outline specific tasks for individual developers to implement components of the Superego Agent System frontend. Each prompt focuses on a specific area of functionality while referring to the shared design document and API documentation.

## Prompt 1: Project Setup and Core Structure

**Task**: Set up the initial Svelte project structure and implement the core layout components.

**Reference Documents**:
- `frontend-alt/design-document.md` for overall architecture
- `backend_api_documentation.md` for API endpoints

**Deliverables**:
1. Initialize a new Svelte project with TypeScript support
2. Configure Vite for development with API proxying to backend
3. Implement the main layout with three-panel structure (Flow Navigator, Conversation View, Details Panel)
4. Create placeholder components for each panel
5. Set up routing (if needed) and basic navigation

**Implementation Notes**:
- Use a minimal set of dependencies
- Follow the component structure outlined in the design document
- Implement responsive design considerations for different screen sizes
- Create a consistent theme/styling foundation for other developers to build on - specify this in a separate MD file so that other workers do not need to reference the rest of the code base and can work in parallel. 

## Prompt 2: Flow Navigator Panel

**Task**: Implement the Flow Navigator panel with flow instance management functionality.

**Reference Documents**:
- `frontend-alt/design-document.md` (Flow Navigator Panel section)
- `backend_api_documentation.md` (List Available Flows endpoint)

**Deliverables**:
1. `FlowInstanceList.svelte` for displaying and selecting flow instances
2. `NewFlowButton.svelte` for creating new flow instances
3. `FlowSelectionModal.svelte` for selecting flow definitions
4. Required stores for managing flow instance state

**Implementation Notes**:
- Focus on clean, accessible UI for the flow instance list
- Implement proper loading states and error handling
- Consider empty states (no flow instances available)
- Add proper timestamp formatting for recent flows

## Prompt 3: Agent Cards and Conversation View

**Task**: Implement the conversation view with agent cards that display flow steps.

**Reference Documents**:
- `frontend-alt/design-document.md` (Flow Conversation Panel section)
- `backend_api_documentation.md` (Complete Flow Step Structure section)

**Deliverables**:
1. `AgentCard.svelte` base component
2. `SuperegoCard.svelte` for Superego agent steps
3. `InnerAgentCard.svelte` for inner agent steps
4. `UserMessageCard.svelte` for user messages
5. `ConnectionLine.svelte` for visual flow connections
6. `ConversationView.svelte` container component

**Implementation Notes**:
- Ensure proper styling for different agent types
- Implement expandable/collapsible sections for detailed information
- Use appropriate transitions for smooth UI experience
- Handle edge cases (missing data, long content)
- Ensure accessibility with proper ARIA attributes

## Prompt 4: Streaming Text and Chat Input

**Task**: Implement streaming text display and user input components.

**Reference Documents**:
- `frontend-alt/design-document.md` (Streaming Support and ChatInput sections)
- `backend_api_documentation.md` (Streaming Protocol section)

**Deliverables**:
1. `StreamingText.svelte` for displaying streaming text content
2. `ChatInput.svelte` for user message entry
3. Helper utilities for text formatting (if needed)

**Implementation Notes**:
- Ensure smooth rendering of streaming text updates
- Implement typing indicator for active streaming
- Handle edge cases (interrupted streams, errors)
- Make chat input accessible and responsive
- Consider UX for long inputs and mobile devices

## Prompt 5: API Services Integration

**Task**: Implement API services for backend communication.

**Reference Documents**:
- `frontend-alt/design-document.md` (API Integration section)
- `backend_api_documentation.md` (API Endpoints section)

**Deliverables**:
1. `flowService.ts` for flow-related API calls
2. `toolService.ts` for tool confirmation functionality
3. `streamService.ts` for handling SSE connections
4. Types definition file for API responses

**Implementation Notes**:
- Implement robust error handling
- Use TypeScript for type safety
- Follow consistent patterns for all API calls
- Handle reconnection logic for SSE streams
- Consider rate limiting and request debouncing

## Prompt 6: State Management

**Task**: Implement Svelte stores for application state management.

**Reference Documents**:
- `frontend-alt/design-document.md` (State Management section)
- `backend_api_documentation.md` (Data Models section)

**Deliverables**:
1. `flowInstancesStore.ts` for managing flow instances
2. `currentFlowStore.ts` for current flow state
3. `uiStateStore.ts` for UI state

**Implementation Notes**:
- Use derived stores where appropriate
- Keep stores focused on specific concerns
- Implement proper initialization and cleanup
- Document store APIs for other developers
- Consider performance for large flow records
- Consdier whether a store is STRICTLY necessary! 

## Prompt 7: Tool Confirmation UI

**Task**: Implement UI for tool confirmation functionality.

**Reference Documents**:
- `frontend-alt/design-document.md` (Tool Confirmation section)
- `backend_api_documentation.md` (Tool Execution Confirmation endpoint)

**Deliverables**:
1. `ToolConfirmationModal.svelte` for confirming tool executions
2. `ToolSettingsPanel.svelte` for managing tool confirmation settings
3. Integration with relevant stores and services

**Implementation Notes**:
- Create clear, usable UI for confirming or rejecting tool executions
- Implement settings management for tools that require confirmation
- Handle edge cases (timeouts, multiple pending confirmations)
- Consider UX flow for frequent tool usage scenarios

## Prompt 8: Testing and Documentation

**Task**: Set up testing infrastructure and create component documentation.

**Reference Documents**:
- `frontend-alt/design-document.md`
- Existing component implementations

**Deliverables**:
1. Test setup with testing library
2. Basic tests for core components
3. Component documentation using appropriate format
4. Usage examples for key components

**Implementation Notes**:
- Focus on functional tests for critical components
- Document component APIs, props, and events
- Create usage examples for complex components
- Set up consistent documentation format
