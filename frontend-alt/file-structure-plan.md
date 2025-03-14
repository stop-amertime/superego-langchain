# Superego Frontend - File Structure Plan

This document provides a detailed file structure plan for the Svelte-based frontend application. It outlines the organization of files and directories, ensuring a clear separation of concerns and maintainable codebase.

## Root Structure

```
frontend-alt/
├── public/                 # Static assets
│   ├── favicon.ico
│   └── index.html
├── src/                    # Source code
│   ├── api/                # API services
│   ├── components/         # UI components
│   ├── stores/             # Svelte stores
│   ├── types/              # TypeScript type definitions
│   ├── utils/              # Utility functions
│   ├── App.svelte          # Main application component
│   ├── global.css          # Global styles
│   └── main.ts             # Application entry point
├── tests/                  # Test files
├── .gitignore
├── package.json
├── svelte.config.js
├── tsconfig.json
└── vite.config.ts
```

## API Services

```
src/api/
├── constants.ts            # API URLs and constants
├── flowService.ts          # Flow-related API calls
├── toolService.ts          # Tool confirmation API calls 
├── streamService.ts        # Server-Sent Events handling
└── types.ts                # API-specific type definitions
```

## Components

```
src/components/
├── agent/                  # Agent-related components
│   ├── AgentCard.svelte    # Base card component for all agents
│   ├── SuperegoCard.svelte # Card for superego agent steps
│   ├── InnerAgentCard.svelte # Card for inner agent steps
│   ├── UserMessageCard.svelte # Card for user messages
│   ├── ConnectionLine.svelte # Visual connector between cards
│   └── ToolUsage.svelte    # Tool usage display component
│
├── chat/                   # Chat-related components
│   ├── ChatInput.svelte    # Message input component
│   ├── ConversationView.svelte # Main conversation container
│   └── StreamingText.svelte # Streaming text display
│
├── flow/                   # Flow management components
│   ├── FlowInstanceList.svelte # List of flow instances
│   ├── FlowSelectionModal.svelte # Modal for selecting flow definitions
│   ├── NewFlowButton.svelte # Button to create new flow
│   └── FlowControl.svelte  # Flow control panel
│
├── layout/                 # Layout components
│   ├── AppLayout.svelte    # Main application layout
│   ├── NavigatorPanel.svelte # Left panel component
│   ├── ConversationPanel.svelte # Middle panel component
│   └── DetailsPanel.svelte # Right panel component
│
├── shared/                 # Shared/common components
│   ├── Button.svelte       # Reusable button component
│   ├── Card.svelte         # Base card component
│   ├── Modal.svelte        # Reusable modal component
│   ├── Spinner.svelte      # Loading spinner
│   └── ErrorDisplay.svelte # Error message display
│
└── tool/                   # Tool-related components
    ├── ToolConfirmationModal.svelte # Modal for confirming tool executions
    └── ToolSettingsPanel.svelte # Panel for tool settings
```

## Stores

```
src/stores/
├── flowInstancesStore.ts   # Store for managing flow instances
├── currentFlowStore.ts     # Store for current flow state
├── uiStateStore.ts         # Store for UI state (modals, expandable sections)
└── toolConfirmationStore.ts # Store for tool confirmation state
```

## Types

```
src/types/
├── agent.ts                # Agent-related types
├── flow.ts                 # Flow-related types
├── tool.ts                 # Tool-related types
└── index.ts                # Type exports
```

## Utils

```
src/utils/
├── dateFormatter.ts        # Date and time formatting utilities
├── eventUtils.ts           # Event handling utilities
├── stringUtils.ts          # String manipulation utilities
└── colorUtils.ts           # Color manipulation for agent cards
```

## Component Responsibilities

### Layout Components

- **AppLayout.svelte**: Main layout component that arranges the three panels
- **NavigatorPanel.svelte**: Container for flow navigation components
- **ConversationPanel.svelte**: Container for conversation components
- **DetailsPanel.svelte**: Container for detail/configuration components (future use)

### Agent Components

- **AgentCard.svelte**: Base component for all agent cards with common functionality
- **SuperegoCard.svelte**: Extends AgentCard for superego-specific display (constitution, decision)
- **InnerAgentCard.svelte**: Extends AgentCard for inner agent-specific display (tools, system prompt)
- **UserMessageCard.svelte**: Card for user messages
- **ConnectionLine.svelte**: Visual line connecting sequential agent cards
- **ToolUsage.svelte**: Displays tool usage details (name, input, output)

### Chat Components

- **ChatInput.svelte**: Text input for user messages with submit button
- **ConversationView.svelte**: Main container that manages the conversation flow
- **StreamingText.svelte**: Handles incremental text rendering for streaming responses

### Flow Components

- **FlowInstanceList.svelte**: Lists recent flow instances with selection capability
- **FlowSelectionModal.svelte**: Modal for selecting flow definitions when creating new flow
- **NewFlowButton.svelte**: Button that opens the flow selection modal
- **FlowControl.svelte**: Controls for managing the current flow (future expansion)

### Tool Components

- **ToolConfirmationModal.svelte**: Modal for confirming tool executions
- **ToolSettingsPanel.svelte**: Panel for configuring tool confirmation settings

### Shared Components

- **Button.svelte**: Reusable button component with consistent styling
- **Card.svelte**: Base card component for consistent styling
- **Modal.svelte**: Reusable modal component
- **Spinner.svelte**: Loading indicator
- **ErrorDisplay.svelte**: Error message display component

## Store Responsibilities

- **flowInstancesStore.ts**: Manages the list of available flow instances, loading/fetching
- **currentFlowStore.ts**: Manages the current flow state, execution, and history
- **uiStateStore.ts**: Manages UI state like modal visibility, expanded cards, etc.
- **toolConfirmationStore.ts**: Manages tool confirmation state and settings

## Implementation Dependencies

This diagram shows the dependencies between key components:

```
AppLayout
├── NavigatorPanel
│   └── FlowInstanceList
│       ├── flowInstancesStore
│       └── NewFlowButton
│           └── FlowSelectionModal
│               └── flowService
│
├── ConversationPanel
│   ├── ConversationView
│   │   ├── AgentCard/SuperegoCard/InnerAgentCard
│   │   │   └── StreamingText
│   │   ├── ConnectionLine
│   │   └── currentFlowStore
│   │
│   └── ChatInput
│       └── streamService
│
└── DetailsPanel (future)
    └── ToolSettingsPanel
        └── toolService
```

## Implementation Order

For efficient development, components should be implemented in this order:

1. **Core Structure**: AppLayout, NavigatorPanel, ConversationPanel, DetailsPanel
2. **Stores**: flowInstancesStore, currentFlowStore, uiStateStore
3. **API Services**: flowService, streamService, toolService
4. **Base Components**: AgentCard, StreamingText, ChatInput
5. **Specialized Components**: SuperegoCard, InnerAgentCard, ConnectionLine
6. **Flow Management**: FlowInstanceList, FlowSelectionModal, NewFlowButton
7. **Tool Components**: ToolConfirmationModal, ToolSettingsPanel

This order allows for incremental development and testing of the system from core to specialized components.
