"""
Handler for flow related WebSocket messages using flow_engine.py.
This module handles flow definitions and instances.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...models import Message, WebSocketMessageType, NodeConfig, EdgeConfig, FlowInstance, SuperegoEvaluation, SuperegoDecision
from ...flow_engine import get_flow_engine
from ...conversation_manager import get_conversation, update_conversation
from ..utils import create_message, create_error_message, create_system_message

# Set up logging
logger = logging.getLogger(__name__)

async def handle_flow_message(message_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle flow-related messages using flow_engine
    
    Args:
        message_type: The message type
        context: The conversation context
        
    Returns:
        Updated context with messages and conversation ID if applicable
    """
    client_id = context["client_id"]
    conversation_id = context["conversation_id"]
    messages = context["messages"]
    manager = context["manager"]
    request_data = context["request_data"]
    
    # Get flow engine
    flow_engine = get_flow_engine()
    
    # Handle different flow-related message types
    if message_type == "get_flow_definitions":
        # Return available flow definitions
        definitions = flow_engine.flow_definitions
        # Convert to dictionaries for JSON serialization
        serialized_definitions = [definition.dict() for definition in definitions.values()]
        await manager.send_message(
            create_message(
                WebSocketMessageType.FLOW_DEFINITIONS_RESPONSE,
                serialized_definitions,
                None
            ),
            client_id
        )
    
    elif message_type == "get_flow_instances":
        # Return available flow instances
        instances = flow_engine.flow_instances
        # Convert to dictionaries for JSON serialization
        serialized_instances = [instance.dict() for instance in instances.values()]
        await manager.send_message(
            create_message(
                WebSocketMessageType.FLOW_INSTANCES_RESPONSE,
                serialized_instances,
                None
            ),
            client_id
        )
    
    elif message_type == "get_conversation_history":
        # Return conversation history for the current flow instance
        instance_id = request_data.get("flow_instance_id") or request_data.get("conversation_id")
        
        if not instance_id:
            await manager.send_message(
                create_error_message(
                    "Missing flow instance ID",
                    None
                ),
                client_id
            )
            return {}
        
        # Get the flow instance
        instance = flow_engine.get_flow_instance(instance_id)
        if not instance:
            await manager.send_message(
                create_error_message(
                    f"Flow instance not found: {instance_id}",
                    None
                ),
                client_id
            )
            return {}
        
        # Get messages from the instance
        history = instance.messages
        
        # Update the context with the retrieved messages
        context["messages"] = history
        
        # Send the conversation history as a conversation update
        await manager.send_message(
            {
                "type": WebSocketMessageType.CONVERSATION_UPDATE,
                "content": {
                    "messages": [msg.dict() for msg in history],
                    "replace": True
                },
                "conversation_id": instance_id,
                "timestamp": datetime.now().isoformat()
            },
            client_id
        )
    
    elif message_type == "get_flow_definition":
        # Return a specific flow definition by ID
        if "id" not in request_data:
            raise ValueError("Missing definition ID")
        
        definition_id = request_data.get("id")
        definition = flow_engine.get_flow_definition(definition_id)
        
        if definition:
            await manager.send_message(
                create_system_message(
                    {
                        "success": True,
                        "message": f"Found definition: {definition.name}",
                        "definition": definition.dict()
                    },
                    None
                ),
                client_id
            )
        else:
            await manager.send_message(
                create_error_message(
                    f"Flow definition with ID {definition_id} not found",
                    None
                ),
                client_id
            )
    
    elif message_type == "get_flow_instance":
        # Return a specific flow instance by ID
        if "id" not in request_data:
            raise ValueError("Missing instance ID")
        
        instance_id = request_data.get("id")
        instance = flow_engine.get_flow_instance(instance_id)
        
        if instance:
            await manager.send_message(
                create_system_message(
                    {
                        "success": True,
                        "message": f"Found instance: {instance.name}",
                        "instance": instance.dict()
                    },
                    None
                ),
                client_id
            )
        else:
            await manager.send_message(
                create_error_message(
                    f"Flow instance with ID {instance_id} not found",
                    None
                ),
                client_id
            )
    
    elif message_type == "create_flow_definition":
        # Create a new flow definition
        if not all(k in request_data for k in ["name", "nodes", "edges"]):
            raise ValueError("Missing required fields for flow definition (name, nodes, edges)")
        
        from ...models import FlowDefinition
        
        # Create the flow definition object
        definition = FlowDefinition(
            id=str(uuid.uuid4()),
            name=request_data.get("name"),
            description=request_data.get("description", ""),
            nodes=request_data.get("nodes"),
            edges=request_data.get("edges")
        )
        
        # Create the flow definition
        new_definition = flow_engine.create_flow_definition(definition)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Flow definition created: {new_definition.name}",
                    "definition": new_definition.dict()
                },
                None
            ),
            client_id
        )
    
    elif message_type == "create_flow_instance":
        # Create a new flow instance
        if not all(k in request_data for k in ["flow_definition_id", "name"]):
            raise ValueError("Missing required fields for flow instance (flow_definition_id, name)")
        
        # Create the flow instance
        new_instance = flow_engine.create_flow_instance(
            definition_id=request_data.get("flow_definition_id"),
            name=request_data.get("name"),
            description=request_data.get("description"),
            parameters=request_data.get("parameters", {})
        )
        
        if new_instance:
            await manager.send_message(
                create_system_message(
                    {
                        "success": True,
                        "message": f"Flow instance created: {new_instance.name}",
                        "instance": new_instance.dict()
                    },
                    None
                ),
                client_id
            )
        else:
            await manager.send_message(
                create_error_message(
                    f"Could not create flow instance. Flow definition not found or invalid parameters.",
                    None
                ),
                client_id
            )
    
    elif message_type == "update_flow_definition":
        # Update a flow definition
        if "id" not in request_data:
            raise ValueError("Missing definition ID")
        
        definition_id = request_data.get("id")
        definition = flow_engine.get_flow_definition(definition_id)
        
        if not definition:
            await manager.send_message(
                create_error_message(
                    f"Flow definition with ID {definition_id} not found",
                    None
                ),
                client_id
            )
            return {}
        
        # Update the definition fields
        if "name" in request_data:
            definition.name = request_data.get("name")
        if "description" in request_data:
            definition.description = request_data.get("description")
        if "nodes" in request_data:
            definition.nodes = request_data.get("nodes")
        if "edges" in request_data:
            definition.edges = request_data.get("edges")
        
        # Save the updated definition
        flow_engine.save_flow_definition(definition)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Flow definition updated: {definition.name}",
                    "definition": definition.dict()
                },
                None
            ),
            client_id
        )
    
    elif message_type == "update_flow_instance":
        # Update a flow instance
        if "id" not in request_data:
            raise ValueError("Missing instance ID")
        
        instance_id = request_data.get("id")
        instance = flow_engine.get_flow_instance(instance_id)
        
        if not instance:
            await manager.send_message(
                create_error_message(
                    f"Flow instance with ID {instance_id} not found",
                    None
                ),
                client_id
            )
            return {}
        
        # Update the instance fields
        if "name" in request_data:
            instance.name = request_data.get("name")
        if "description" in request_data:
            instance.description = request_data.get("description")
        if "parameters" in request_data:
            instance.parameters = request_data.get("parameters")
        
        # Update the instance
        flow_engine.update_flow_instance(instance)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Flow instance updated: {instance.name}",
                    "instance": instance.dict()
                },
                None
            ),
            client_id
        )
    
    elif message_type == "delete_flow_instance":
        # Delete a flow instance
        if "id" not in request_data:
            raise ValueError("Missing instance ID")
        
        instance_id = request_data.get("id")
        success = flow_engine.delete_flow_instance(instance_id)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": success,
                    "message": f"Flow instance {'deleted' if success else 'not found'}: {instance_id}"
                },
                None
            ),
            client_id
        )
    
    elif message_type == "process_user_input":
        # Process user input through a flow instance
        if not all(k in request_data for k in ["flow_instance_id", "content"]):
            raise ValueError("Missing required fields for processing user input (flow_instance_id, content)")
        
        instance_id = request_data.get("flow_instance_id")
        user_input = request_data.get("content")
        
        # Create on_token and on_thinking callbacks
        async def on_token(node_id, token, message_id):
            await manager.send_message(
                {
                    "type": WebSocketMessageType.ASSISTANT_TOKEN,
                    "content": {
                        "id": message_id,
                        "token": token,
                        "node_id": node_id,
                        "flow_instance_id": instance_id
                    },
                    "flow_instance_id": instance_id,
                    "timestamp": datetime.now().isoformat()
                },
                client_id
            )
        
        async def on_thinking(node_id, thinking, message_id):
            await manager.send_message(
                {
                    "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                    "content": {
                        "status": "thinking",
                        "id": message_id,
                        "thinking": thinking,
                        "node_id": node_id,
                        "flow_instance_id": instance_id
                    },
                    "flow_instance_id": instance_id,
                    "timestamp": datetime.now().isoformat()
                },
                client_id
            )
        
        # Notify that the flow has started
        await manager.send_message(
            {
                "type": WebSocketMessageType.FLOW_STARTED,
                "content": {
                    "flow_instance_id": instance_id
                },
                "flow_instance_id": instance_id,
                "timestamp": datetime.now().isoformat()
            },
            client_id
        )
        
        try:
            # Process the user input
            result = await flow_engine.process_user_input(
                instance_id=instance_id,
                user_input=user_input,
                on_token=on_token,
                on_thinking=on_thinking
            )
            
            # Check for errors
            if "error" in result:
                await manager.send_message(
                    {
                        "type": WebSocketMessageType.FLOW_ERROR,
                        "content": {
                            "error": result["error"],
                            "flow_instance_id": instance_id
                        },
                        "flow_instance_id": instance_id,
                        "timestamp": datetime.now().isoformat()
                    },
                    client_id
                )
                return {}
            
            # Notify that the flow has completed
            await manager.send_message(
                {
                    "type": WebSocketMessageType.FLOW_COMPLETED,
                    "content": {
                        "flow_instance_id": instance_id,
                        "result": result
                    },
                    "flow_instance_id": instance_id,
                    "timestamp": datetime.now().isoformat()
                },
                client_id
            )
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            await manager.send_message(
                {
                    "type": WebSocketMessageType.FLOW_ERROR,
                    "content": {
                        "error": str(e),
                        "flow_instance_id": instance_id
                    },
                    "flow_instance_id": instance_id,
                    "timestamp": datetime.now().isoformat()
                },
                client_id
            )
    
    # Return empty dict for message types that don't update messages
    return {}
