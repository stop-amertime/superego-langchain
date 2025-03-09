"""
Handler for flow related WebSocket messages.
This module handles flow templates, configs, instances, and parallel flows.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...models import Message, WebSocketMessageType, FlowConfig, FlowTemplate, FlowInstance, ParallelFlowResult
from ...graph import filter_user_messages
from ...conversation_manager import get_conversation, update_conversation
from ...flow_manager import (
    get_all_flow_templates, get_all_flow_configs, get_all_flow_instances,
    get_flow_template, get_flow_config, get_flow_instance,
    create_flow_template, create_flow_config, create_flow_instance,
    update_flow_template, update_flow_config, update_flow_instance,
    delete_flow_template, delete_flow_config, delete_flow_instance,
    run_multiple_flows, update_flow_instance_last_message
)
from ..utils import create_message, create_error_message, create_system_message

# Set up logging
logger = logging.getLogger(__name__)

async def handle_flow_message(message_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle flow-related messages
    
    Args:
        message_type: The message type
        context: The conversation context
        
    Returns:
        Updated context with messages and conversation ID if applicable
    """
    client_id = context["client_id"]
    conversation_id = context["conversation_id"]
    conversations = context["conversations"]
    messages = context["messages"]
    manager = context["manager"]
    request_data = context["request_data"]
    
    # Handle different flow-related message types
    if message_type == "get_flow_templates":
        # Return available flow templates
        templates = get_all_flow_templates()
        # Convert templates to dictionaries for JSON serialization
        serialized_templates = [template.dict() for template in templates.values()]
        await manager.send_message(
            create_message(
                WebSocketMessageType.FLOW_TEMPLATES_RESPONSE,
                serialized_templates,
                None
            ),
            client_id
        )
    
    elif message_type == "get_flow_configs":
        # Return available flow configurations
        configs = get_all_flow_configs()
        # Convert configs to dictionaries for JSON serialization
        serialized_configs = [config.dict() for config in configs.values()]
        await manager.send_message(
            create_message(
                WebSocketMessageType.FLOW_CONFIGS_RESPONSE,
                serialized_configs,
                None
            ),
            client_id
        )
    
    elif message_type == "get_flow_instances":
        # Return available flow instances
        instances = get_all_flow_instances()
        # Convert instances to dictionaries for JSON serialization
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
        conversation_id = request_data.get("flow_instance_id") or request_data.get("conversation_id")
        
        if not conversation_id:
            await manager.send_message(
                create_error_message(
                    "Missing flow instance ID or conversation ID",
                    None
                ),
                client_id
            )
            return {}
        
        # Get the conversation history from persistent storage
        history = get_conversation(conversation_id)
        
        # Update the context with the retrieved messages
        context["messages"] = history
        
        # Update the in-memory cache in the main websocket handler
        if "conversations" in context:
            context["conversations"][conversation_id] = history
        
        # Send the conversation history as a conversation update
        await manager.send_message(
            {
                "type": WebSocketMessageType.CONVERSATION_UPDATE,
                "content": {
                    "messages": [msg.dict() for msg in history],
                    "replace": True
                },
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            },
            client_id
        )
    
    elif message_type == "get_flow_instance":
        # Return a specific flow instance by ID
        if "id" not in request_data:
            raise ValueError("Missing instance ID")
        
        instance_id = request_data.get("id")
        instance = get_flow_instance(instance_id)
        
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
    
    elif message_type == "create_flow_template":
        # Create a new flow template
        if not all(k in request_data for k in ["name", "description", "config"]):
            raise ValueError("Missing required fields for flow template (name, description, config)")
        
        config_data = request_data.get("config")
        config = FlowConfig(
            id=str(uuid.uuid4()),
            name=config_data.get("name", request_data.get("name")),
            constitution_id=config_data.get("constitution_id", "default"),
            sysprompt_id=config_data.get("sysprompt_id", "assistant_default"),
            superego_enabled=config_data.get("superego_enabled", True),
            description=config_data.get("description", "")
        )
        
        template = create_flow_template(
            name=request_data.get("name"),
            description=request_data.get("description"),
            config=config,
            is_default=request_data.get("is_default", False)
        )
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Flow template created: {template.name}",
                    "template": template.dict()
                },
                None
            ),
            client_id
        )
    
    elif message_type == "create_flow_config":
        # Create a new flow configuration
        if not all(k in request_data for k in ["name"]):
            raise ValueError("Missing required fields for flow config (name)")
        
        config = create_flow_config(
            name=request_data.get("name"),
            constitution_id=request_data.get("constitution_id", "default"),
            sysprompt_id=request_data.get("sysprompt_id", "assistant_default"),
            superego_enabled=request_data.get("superego_enabled", True),
            description=request_data.get("description")
        )
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Flow configuration created: {config.name}",
                    "config": config.dict()
                },
                None
            ),
            client_id
        )
    
    elif message_type == "create_flow_instance":
        # Create a new flow instance
        if not all(k in request_data for k in ["flow_config_id", "name"]):
            raise ValueError("Missing required fields for flow instance (flow_config_id, name)")
        
        instance = create_flow_instance(
            flow_config_id=request_data.get("flow_config_id"),
            name=request_data.get("name"),
            description=request_data.get("description")
        )
        
        await manager.send_message(
            create_system_message(
                {
                    "success": True,
                    "message": f"Flow instance created: {instance.name}",
                    "instance": instance.dict()
                },
                None
            ),
            client_id
        )
    
    elif message_type == "update_flow_template":
        # Update a flow template
        if "id" not in request_data:
            raise ValueError("Missing template ID")
        
        template_id = request_data.get("id")
        name = request_data.get("name")
        description = request_data.get("description")
        is_default = request_data.get("is_default")
        config_data = request_data.get("config")
        
        config = None
        if config_data:
            config = FlowConfig(
                id=config_data.get("id", str(uuid.uuid4())),
                name=config_data.get("name", name if name else ""),
                constitution_id=config_data.get("constitution_id", "default"),
                sysprompt_id=config_data.get("sysprompt_id", "assistant_default"),
                superego_enabled=config_data.get("superego_enabled", True),
                description=config_data.get("description", "")
            )
        
        template = update_flow_template(
            template_id=template_id,
            name=name,
            description=description,
            config=config,
            is_default=is_default
        )
        
        if template:
            await manager.send_message(
                create_system_message(
                    {
                        "success": True,
                        "message": f"Flow template updated: {template.name}",
                        "template": template.dict()
                    },
                    None
                ),
                client_id
            )
        else:
            await manager.send_message(
                create_error_message(
                    f"Flow template with ID {template_id} not found",
                    None
                ),
                client_id
            )
    
    elif message_type == "update_flow_config":
        # Update a flow configuration
        if "id" not in request_data:
            raise ValueError("Missing config ID")
        
        config_id = request_data.get("id")
        name = request_data.get("name")
        constitution_id = request_data.get("constitution_id")
        sysprompt_id = request_data.get("sysprompt_id")
        superego_enabled = request_data.get("superego_enabled")
        description = request_data.get("description")
        
        config = update_flow_config(
            config_id=config_id,
            name=name,
            constitution_id=constitution_id,
            sysprompt_id=sysprompt_id,
            superego_enabled=superego_enabled,
            description=description
        )
        
        if config:
            await manager.send_message(
                create_system_message(
                    {
                        "success": True,
                        "message": f"Flow configuration updated: {config.name}",
                        "config": config.dict()
                    },
                    None
                ),
                client_id
            )
        else:
            await manager.send_message(
                create_error_message(
                    f"Flow configuration with ID {config_id} not found",
                    None
                ),
                client_id
            )
    
    elif message_type == "update_flow_instance":
        # Update a flow instance
        if "id" not in request_data:
            raise ValueError("Missing instance ID")
        
        instance_id = request_data.get("id")
        name = request_data.get("name")
        description = request_data.get("description")
        
        instance = update_flow_instance(
            instance_id=instance_id,
            name=name,
            description=description
        )
        
        if instance:
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
        else:
            await manager.send_message(
                create_error_message(
                    f"Flow instance with ID {instance_id} not found",
                    None
                ),
                client_id
            )
    
    elif message_type == "delete_flow_template":
        # Delete a flow template
        if "id" not in request_data:
            raise ValueError("Missing template ID")
        
        template_id = request_data.get("id")
        success = delete_flow_template(template_id)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": success,
                    "message": f"Flow template {'deleted' if success else 'not found'}: {template_id}"
                },
                None
            ),
            client_id
        )
    
    elif message_type == "delete_flow_config":
        # Delete a flow configuration
        if "id" not in request_data:
            raise ValueError("Missing config ID")
        
        config_id = request_data.get("id")
        success = delete_flow_config(config_id)
        
        await manager.send_message(
            create_system_message(
                {
                    "success": success,
                    "message": f"Flow configuration {'deleted' if success else 'not found or in use'}: {config_id}"
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
        success = delete_flow_instance(instance_id)
        
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
    
    elif message_type == "run_parallel_flows":
        # Run multiple flows in parallel
        if not all(k in request_data for k in ["flow_config_ids", "content"]):
            raise ValueError("Missing required fields for parallel flows (flow_config_ids, content)")
        
        flow_config_ids = request_data.get("flow_config_ids")
        user_input = request_data.get("content")
        conversation_id = request_data.get("conversation_id")
        
        # Initialize conversation if needed
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
            messages = []
        else:
            # Get messages from persistent storage
            messages = get_conversation(conversation_id)
        
        # Get user messages only to prevent loops
        user_messages = filter_user_messages(messages)
        
        # Create on_token and on_thinking callbacks for each flow
        on_token = {}
        on_thinking = {}
        
        for config_id in flow_config_ids:
            flow_assistant_id = str(uuid.uuid4())
            flow_superego_id = str(uuid.uuid4())
            
            async def create_token_callback(id, config_id):
                async def callback(token):
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.ASSISTANT_TOKEN,
                            "content": {
                                "id": id,
                                "token": token,
                                "flow_config_id": config_id
                            },
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat()
                        },
                        client_id
                    )
                return callback
            
            async def create_thinking_callback(id, config_id):
                async def callback(thinking):
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                            "content": {
                                "status": "thinking",
                                "id": id,
                                "thinking": thinking,
                                "flow_config_id": config_id
                            },
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat()
                        },
                        client_id
                    )
                return callback
            
            on_token[config_id] = await create_token_callback(flow_assistant_id, config_id)
            on_thinking[config_id] = await create_thinking_callback(flow_superego_id, config_id)
        
        # Run flows in parallel
        results = await run_multiple_flows(
            flow_config_ids=flow_config_ids,
            user_input=user_input,
            conversation_id=conversation_id,
            messages=user_messages,
            on_token=on_token,
            on_thinking=on_thinking
        )
        
        # Update conversation in persistent storage
        if messages:
            updated_messages = messages.copy()
            # Add any new messages from the results if needed
            # This depends on how run_multiple_flows updates the messages
            update_conversation(conversation_id, updated_messages)
        
        # Send the results back to the client
        await manager.send_message(
            {
                "type": WebSocketMessageType.PARALLEL_FLOWS_RESULT,
                "content": [result.dict() for result in results],
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            }, 
            client_id
        )
        
        return {
            "conversation_id": conversation_id
        }
    
    # Return empty dict for message types that don't update messages
    return {}
