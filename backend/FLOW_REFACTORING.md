# Flow System Refactoring

## Overview

This document outlines the refactoring of the flow system in the Superego LangGraph application. The refactoring removes overlapping and redundant flow management systems by standardizing everything around the `flow_engine.py` implementation, which is the most recent and robust approach.

## What Changed

### Old System (Removed)
- **flow_manager.py** - An older implementation focused on flow templates, configs, and instances with a simple JSON file-based storage model
- **flow.py** - A wrapper around graph.py that provided a CommandFlow class with basic process() and stream() methods
- **graph.py** - The original flow execution logic with hardcoded superego_node and assistant_node functions

### New System (Consolidated)
- **flow_engine.py** - The central component that now handles all flow operations:
  - Flow definition management
  - Flow instance management
  - LangGraph integration for flow execution
  - File-per-instance persistence model
  - Conditional edge routing
  - Command-based flow control

## API Changes

### REST Endpoints
- Replaced `/api/flow-configs` and `/api/flow-templates` with `/api/flow-definitions`
- Updated `/api/flow-instances` to use flow_engine.py
- Changed model structure to match the FlowDefinition and FlowInstance models in flow_engine.py

### WebSocket Interface
- Added a new FlowHandler that processes flow-related WebSocket messages
- Created a consolidated flow_engine.py message handler for all flow operations
- Updated the WebSocket endpoint to register the new handler
- Streamlined message handling for flow operations

## Migration

A script has been provided to help with the migration:
- `backend/cleanup_old_flow_system.py` - Backs up the old files and renames them with .old extension

## Using the New System

### Creating Flow Definitions

```python
from flow_engine import get_flow_engine
from models import NodeConfig, EdgeConfig, FlowDefinition

# Get the flow engine
flow_engine = get_flow_engine()

# Create a flow definition
definition = FlowDefinition(
    name="My Flow",
    description="My flow definition",
    nodes={
        "input_superego": NodeConfig(
            type="INPUT_SUPEREGO",
            config={"constitution_id": "default"}
        ),
        "assistant": NodeConfig(
            type="GENERAL_ASSISTANT",
            config={"system_prompt": "You are a helpful AI assistant."}
        )
    },
    edges=[
        EdgeConfig(from_node="START", to_node="input_superego"),
        EdgeConfig(from_node="input_superego", to_node="assistant", condition="ALLOW"),
        EdgeConfig(from_node="input_superego", to_node="END", condition="BLOCK"),
        EdgeConfig(from_node="assistant", to_node="END")
    ]
)

# Register the definition
flow_engine.create_flow_definition(definition)
```

### Creating Flow Instances

```python
# Create a flow instance
instance = flow_engine.create_flow_instance(
    definition_id="definition_id",
    name="My Instance",
    description="My flow instance",
    parameters={} # Optional parameters to override node configurations
)
```

### Processing User Input

```python
async def process_input(instance_id, user_input):
    # Process user input
    result = await flow_engine.process_user_input(
        instance_id=instance_id,
        user_input=user_input,
        on_token=on_token_callback,  # Optional
        on_thinking=on_thinking_callback  # Optional
    )
    
    return result
```

## Benefits of the Refactoring

1. **Simplicity** - One central component for all flow operations
2. **Consistency** - Standard models and APIs across the application
3. **Maintainability** - Easier to understand and extend
4. **Performance** - More efficient persistence model with file-per-instance
5. **Flexibility** - Better support for complex flows with conditional routing

## Next Steps

- Explore additional node types beyond input_superego and assistant
- Add support for more complex flow patterns
- Improve the frontend visualization of flows

## Questions?

If you have any questions about the refactoring or how to use the new system, please reach out to the development team.
