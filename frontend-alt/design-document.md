# Superego Agent System - Frontend Design Document

This document outlines the design and implementation plan for the Svelte-based thin client that will interact with the Superego Agent System backend.

## Overview

The frontend will be a research-focused application that visualizes the Superego agent system as a chat-like interface with detailed agent action cards. It will support streaming responses and maintain a history of flow instances.

## User Interface Layout

The application will have a three-panel layout:

1. **Left Panel (Flow Navigator)**: Lists recently run flow instances and provides a way to create new ones
2. **Main Panel (Flow Conversation)**: Displays the agent actions as a vertical sequence of cards
3. **Right Panel (Optional Details/Configuration)**: Available for future expansion to show detailed information or configuration options

```
+-------------------+-------------------------------+------------------+
| Flow Navigator    | Flow Conversation             | Details Panel    |
|                   |                               | (Future)         |
| [New Flow]        | +-------------------------+   |                  |
|                   | | User Message            |   |                  |
| Recent Flows:     | +-------------------------+   |                  |
| - Flow #123       | | Superego Agent          |   |                  |
| - Flow #122       | | Decision: ACCEPT        |   |                  |
| - Flow #121       | | + Extra Details         |   |                  |
|                   | +-------------------------+   |                  |
|                   | |         |               |   |                  |
|                   | |         V               |   |                  |
|                   | +-------------------------+   |                  |
|                   | | Inner Agent             |   |                  |
|                   | | Tool Usage: Calculator  |   |                  |
|                   | | + Extra Details         |   |                  |
|                   | +-------------------------+   |                  |
|                   | |                         |   |                  |
|                   | | [User Input Field]      |   |                  |
|                   | |                         |   |                  |
+-------------------+-------------------------------+------------------+
```

## Components Architecture

### 1. Flow Navigator Panel

#### Components:
- **FlowInstanceList.svelte**
  - Displays list of recent flow instances
  - Each item shows flow ID and timestamp
  - Clicking an item loads that flow instance

- **NewFlowButton.svelte**
  - Creates a new flow instance
  - Opens a modal to select flow definition

- **FlowSelectionModal.svelte**
  - Lists available flow definitions
  - Shows name and description
  - Allows selection and initialization

### 2. Flow Conversation Panel

#### Components:
- **ConversationView.svelte**
  - Main container for the conversation
  - Manages vertical layout of agent cards
  - Handles scroll behavior

- **AgentCard.svelte**
  - Base component for all agent actions
  - Different visual treatments based on agent type
  - Expandable/collapsible for detailed information

- **SuperegoCard.svelte (extends AgentCard)**
  - Shows constitution and decision
  - Includes expandable section for agent_guidance
  - Visual cues for different decision types (ACCEPT, BLOCK, CAUTION)

- **InnerAgentCard.svelte (extends AgentCard)**
  - Shows agent ID and response
  - Displays tool usage details when applicable
  - Includes expandable section for agent_guidance

- **UserMessageCard.svelte**
  - Displays user messages
  - Visually distinct from agent cards

- **ConnectionLine.svelte**
  - Visual connector between cards
  - Simple vertical line showing flow direction

- **ChatInput.svelte**
  - Text input for user messages
  - Send button
  - Displays loading/processing state

### 3. Streaming Support

#### Components:
- **StreamingText.svelte**
  - Renders text as it streams from the backend
  - Updates in real-time
  - Supports basic formatting

### 4. State Management

#### Stores:
- **flowInstancesStore.ts**
  - Maintains list of recent flow instances
  - Handles loading/fetching instances

- **currentFlowStore.ts**
  - Current flow instance data
  - Flow execution state
  - Agent actions history

- **uiStateStore.ts**
  - UI state (modal visibility, expanded cards, etc.)
  - Loading/error states

## API Integration

### Services:
- **flowService.ts**
  - Fetches available flow definitions
  - Manages flow instance execution
  - Handles Server-Sent Events (SSE) for streaming

- **toolService.ts**
  - Handles tool confirmation
  - Updates tool confirmation settings

## Component Details

### AgentCard.svelte

The agent card is the core visual component that will display each step in the flow. It needs to show different information based on the agent type:

```svelte
<!-- AgentCard.svelte (simplified example) -->
<script>
  import { slide } from 'svelte/transition';
  
  export let step; // FlowStep object
  
  let expanded = false;
  
  function toggleExpanded() {
    expanded = !expanded;
  }
</script>

<div class="agent-card {step.agent_id}">
  <div class="header">
    <span class="agent-id">{step.agent_id}</span>
    <span class="timestamp">{formatTimestamp(step.timestamp)}</span>
    <button on:click={toggleExpanded}>
      {expanded ? 'Hide Details' : 'Show Details'}
    </button>
  </div>
  
  <div class="response">
    {step.response}
  </div>
  
  {#if expanded}
    <div class="details" transition:slide>
      {#if step.decision} <!-- Superego agent -->
        <div class="decision {step.decision.toLowerCase()}">
          Decision: {step.decision}
        </div>
        {#if step.constitution}
          <div class="constitution">
            <h4>Constitution:</h4>
            <pre>{step.constitution}</pre>
          </div>
        {/if}
      {/if}
      
      {#if step.tool_usage} <!-- Inner agent with tool -->
        <div class="tool-usage">
          <h4>Tool Usage:</h4>
          <div>Tool: {step.tool_usage.tool_name}</div>
          <div>Input: <pre>{JSON.stringify(step.tool_usage.input, null, 2)}</pre></div>
          <div>Output: <pre>{JSON.stringify(step.tool_usage.output, null, 2)}</pre></div>
        </div>
      {/if}
      
      {#if step.agent_guidance}
        <div class="agent-guidance">
          <h4>Agent Guidance:</h4>
          <pre>{step.agent_guidance}</pre>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .agent-card {
    border: 1px solid #ccc;
    border-radius: 8px;
    margin: 12px 0;
    padding: 12px;
    background: white;
  }
  
  .superego {
    border-left: 4px solid #3498db;
  }
  
  .inner-agent {
    border-left: 4px solid #2ecc71;
  }
  
  .user {
    border-left: 4px solid #e67e22;
    align-self: flex-end;
  }
  
  .header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 8px;
    font-size: 0.9em;
    color: #666;
  }
  
  .response {
    white-space: pre-wrap;
  }
  
  .details {
    margin-top: 12px;
    padding-top: 12px;
    border-top: 1px solid #eee;
  }
  
  .decision {
    padding: 4px 8px;
    border-radius: 4px;
    display: inline-block;
    margin-bottom: 8px;
  }
  
  .accept {
    background: #e6ffed;
    color: #22863a;
  }
  
  .block {
    background: #ffeef0;
    color: #cb2431;
  }
  
  .caution {
    background: #fff5b1;
    color: #735c0f;
  }
  
  .needs_clarification {
    background: #f1f8ff;
    color: #0366d6;
  }
  
  pre {
    background: #f6f8fa;
    padding: 8px;
    border-radius: 4px;
    overflow: auto;
    font-size: 0.9em;
  }
</style>
```

### StreamingText.svelte

This component will handle the streaming text from the backend:

```svelte
<!-- StreamingText.svelte (simplified example) -->
<script>
  export let text = '';
  export let done = false;
  
  // Additional styling/animation logic can be added here
</script>

<div class="streaming-text {done ? 'done' : 'streaming'}">
  {text}
  {#if !done}
    <span class="cursor"></span>
  {/if}
</div>

<style>
  .streaming-text {
    white-space: pre-wrap;
    word-break: break-word;
  }
  
  .cursor {
    display: inline-block;
    width: 10px;
    height: 18px;
    background: #666;
    animation: blink 1s infinite;
  }
  
  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }
</style>
```

### FlowInstanceList.svelte

For managing flow instances in the left panel:

```svelte
<!-- FlowInstanceList.svelte (simplified example) -->
<script>
  import { onMount } from 'svelte';
  import { flowInstancesStore, currentFlowStore } from '../stores';
  
  let instances = [];
  
  onMount(async () => {
    // Load recent instances
    // In a real implementation, this would be populated from the API
    instances = [
      { id: 'flow-123', name: 'Example Flow', timestamp: new Date() },
      { id: 'flow-122', name: 'Another Flow', timestamp: new Date(Date.now() - 3600000) }
    ];
  });
  
  function selectInstance(instance) {
    // Load the flow instance
    currentFlowStore.loadInstance(instance.id);
  }
</script>

<div class="flow-instances">
  <h3>Recent Flows</h3>
  
  <ul>
    {#each instances as instance}
      <li on:click={() => selectInstance(instance)}>
        <span class="name">{instance.name}</span>
        <span class="time">{formatRelativeTime(instance.timestamp)}</span>
      </li>
    {/each}
  </ul>
</div>

<style>
  .flow-instances {
    padding: 12px;
  }
  
  ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }
  
  li {
    padding: 8px 12px;
    border-radius: 4px;
    cursor: pointer;
    margin-bottom: 4px;
  }
  
  li:hover {
    background: #f0f0f0;
  }
  
  .name {
    display: block;
    font-weight: 500;
  }
  
  .time {
    font-size: 0.8em;
    color: #666;
  }
</style>
```

## API Integration

### Fetching Flow Definitions

```typescript
// src/api/flowService.ts
const API_BASE_URL = '/api';

export async function getFlowDefinitions() {
  const response = await fetch(`${API_BASE_URL}/flows`);
  if (!response.ok) {
    throw new Error(`Failed to fetch flows: ${response.status}`);
  }
  return response.json();
}

export async function getFlowDefinition(flowId) {
  const response = await fetch(`${API_BASE_URL}/flow/${flowId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch flow definition: ${response.status}`);
  }
  return response.json();
}
```

### Handling SSE for Streaming

```typescript
// src/api/streamService.ts
import { currentFlowStore } from '../stores';

export function executeFlow(flowId, input) {
  const eventSource = new EventSource(
    `/api/flow/execute?flow_id=${flowId}&input=${encodeURIComponent(input)}`
  );
  
  eventSource.addEventListener('partial_output', (event) => {
    const data = JSON.parse(event.data);
    currentFlowStore.updatePartialOutput(data.data);
  });
  
  eventSource.addEventListener('complete_step', (event) => {
    const data = JSON.parse(event.data);
    currentFlowStore.addCompleteStep(data.data);
  });
  
  eventSource.addEventListener('error', (event) => {
    let data;
    try {
      data = JSON.parse(event.data);
    } catch (e) {
      data = { message: 'Unknown error occurred' };
    }
    currentFlowStore.setError(data.message);
    eventSource.close();
  });
  
  return () => {
    eventSource.close();
  };
}
```

## Data Flow

1. User selects or creates a new flow instance
2. System fetches flow definition if needed
3. User sends a message
4. Backend processes through agents
5. Frontend receives streaming updates:
   - Partial outputs update the current step text
   - Complete steps add new cards to the conversation
6. Flow instance is stored for later retrieval

## Implementation Plan

### Phase 1: Basic Structure and Layout
- Setup project structure
- Implement core layout components
- Create state management stores

### Phase 2: Flow Instance Management
- Implement flow instance list
- Build flow selection and creation
- Setup flow instance loading

### Phase 3: Conversation View and Agent Cards
- Build agent card components
- Implement conversation view
- Create connection lines

### Phase 4: API Integration and Streaming
- Set up API services
- Implement SSE handling
- Connect UI components to data flow

### Phase 5: Styling and Polish
- Refine visual design
- Add animations and transitions
- Implement responsive design

### Phase 6: Tool Confirmation (Future)
- Add tool confirmation UI
- Implement confirmation settings

## Development Guidelines

1. **Component Isolation**: Each component should be self-contained with minimal dependencies
2. **TypeScript Usage**: Use TypeScript for type safety, especially for API interfaces
3. **CSS Approach**: Use component-scoped CSS
4. **Minimalist Dependencies**: Only add libraries when absolutely necessary
5. **Progressive Enhancement**: Build core functionality first, then enhance

## Future Enhancements

1. **Flow Configuration UI**: Interface for creating and editing flows
2. **Constitution Editor**: UI for editing agent constitutions
3. **Advanced Visualization**: More sophisticated visualization of agent transitions
4. **Performance Metrics**: Display agent performance and timing information
5. **Export/Import**: Allow exporting and importing flow instances
