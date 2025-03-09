# Flow-Based Chat Interface Implementation Plan

## Project Overview
We're redesigning the frontend of a multi-agent system to better represent the flow-based architecture while maintaining a chat-style interface. The backend has been rewritten with a flow-based architecture using LangGraph's Command-based flow control.

## Requirements

### Core Requirements
1. Create a more visual representation of the flow process
2. Maintain the vertical chat-like arrangement
3. Encapsulate each flow step in a unified box/card
4. Add visual connections between flow steps (vertical lines)
5. Show more details about each step in the flow (system prompts, constitution, tools used, etc.)

### Technical Requirements
1. Maintain compatibility with existing backend API
2. Support streaming responses
3. Support tool usage display
4. Support error handling
5. Maintain existing functionality (constitution selection, system prompt selection, etc.)

## System Architecture

### Backend Components
- Input Superego agent: Evaluates user inputs against a constitution
- Assistant agent: Can use tools (like a calculator)
- Flow system: Routes between agents based on evaluation results

### Frontend Components to Create
1. **FlowStep**: Core component that encapsulates everything related to a single step in the flow
2. **FlowConnector**: Visual connector between flow steps
3. **FlowStepHeader**: Header for each flow step with metadata and controls
4. **FlowStepContent**: Content area for each flow step
5. **FlowStepDetails**: Expandable details section for each flow step
6. **FlowStepToolUsage**: Display for tool usage within a flow step

## Implementation Log

### Completed Tasks
- Analyzed existing codebase
- Identified key components to modify
- Developed high-level design approach
- Created implementation plan
- Created new component files:
  - FlowStep.tsx and FlowStep.css
  - FlowConnector.tsx and FlowConnector.css
  - FlowStreamingMessage.tsx
  - FlowProcessingIndicator.tsx and FlowProcessingIndicator.css
  - FlowSuperEgoEvaluation.tsx
  - FlowChat.tsx and FlowChat.css
- Updated App.tsx to use the new FlowChat component
- Fixed WebSocket connection issues
- Fixed message store API errors
- Added better error handling for API calls
- Added retry mechanism for creating message stores
- Fixed infinite loop in message store creation

### In Progress
- Testing and debugging the new components

### Pending Tasks

1. Continue testing the components:
   - Verify that the flow-based interface works correctly
   - Ensure that all functionality from the original Chat component is preserved
   - Check that the visual flow connections display correctly

2. Refine CSS styling:
   - Design card-like containers for flow steps
   - Create vertical connector styling
   - Implement expandable/collapsible sections
   - Design visual status indicators

3. Enhance message display:
   - Group related messages by flow step
   - Show more context about each step
   - Provide visual cues about flow progression
   - Include tool usage information

4. Testing and refinement:
   - Test with various flow scenarios
   - Ensure compatibility with existing backend
   - Optimize for performance
   - Refine based on feedback

## Design Decisions

### Visual Design
1. **Card-Based Layout**: Each flow step will be contained in a card-like container with rounded corners, subtle shadows, and a clear visual hierarchy.

2. **Vertical Flow Line**: A vertical line will connect the steps, positioned to the left of the cards. The line will be styled differently based on the flow status:
   - Solid line for completed steps
   - Dashed line for in-progress steps
   - Red line for blocked steps

3. **Color Scheme**:
   - User messages: Light blue background (existing)
   - Superego evaluations: Light gray with colored borders based on decision (green for ALLOW, yellow for CAUTION, red for BLOCK)
   - Assistant responses: White background with blue border (existing)
   - Tool usage: Light yellow background within assistant cards

4. **Expandable Sections**: Each card will have expandable sections indicated by subtle icons (chevrons) that reveal additional details when clicked.

### Layout Decisions
1. **Vertical Arrangement**: Messages will still flow vertically down the page, maintaining the chat-like interface.

2. **Left-Aligned Flow Line**: The vertical flow line will be positioned on the left side of the chat container, with cards connected to it via horizontal lines.

3. **Card Width**: Cards will take up most of the available width (85% like current messages) but will be visually connected to the flow line.

4. **Responsive Design**: The layout will adapt to different screen sizes, with the flow line and connections remaining visible on smaller screens.

### Interaction Design
1. **Expandable Details**: Each card will have expandable sections for:
   - Constitution text (for superego evaluations)
   - System prompt (for assistant responses)
   - Thinking process (for both)
   - Tool usage details (for assistant responses)

2. **Visual Feedback**: Cards will provide visual feedback on hover and when expanded/collapsed.

3. **Progressive Disclosure**: Complex details will be hidden by default and revealed only when needed, keeping the interface clean.

4. **Status Indicators**: Clear visual indicators will show the status of each step in the flow (completed, in progress, blocked).

### Technical Decisions
1. **Component Structure**: We'll create reusable components that can be composed together, rather than a monolithic approach.

2. **State Management**: We'll maintain the existing state management approach, adding new state for expanded/collapsed sections.

3. **CSS Approach**: We'll use CSS modules to avoid style conflicts and maintain component encapsulation.

4. **Animation**: We'll use CSS transitions for smooth expansion/collapse animations and flow progression.

5. **Accessibility**: We'll ensure the new components are accessible, with proper ARIA attributes and keyboard navigation.
