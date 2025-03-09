import json
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from .models import Message, WebSocketMessageType, MessageRole, FlowConfig, FlowTemplate, FlowInstance, ParallelFlowResult
from .agents import get_all_constitutions, save_constitution
from .llm_client import get_all_sysprompts, save_sysprompt
from .connection_manager import ConnectionManager
from .graph import run_graph, rerun_from_checkpoint, filter_user_messages
from .conversation_manager import get_conversation, update_conversation
from .flow_manager import (
    get_all_flow_templates, get_all_flow_configs, get_all_flow_instances,
    get_flow_template, get_flow_config, get_flow_instance,
    create_flow_template, create_flow_config, create_flow_instance,
    update_flow_template, update_flow_config, update_flow_instance,
    delete_flow_template, delete_flow_config, delete_flow_instance,
    run_multiple_flows, update_flow_instance_last_message
)

# Set up logging
logger = logging.getLogger(__name__)

# Initialize connection manager
manager = ConnectionManager()

# Helper functions for websocket message handling
async def create_callbacks(client_id: str, conversation_id: str) -> Dict[str, Callable]:
    """Create token and thinking callbacks for streaming responses"""
    assistant_message_id = str(uuid.uuid4())
    superego_message_id = str(uuid.uuid4())
    
    async def on_token(token: str):
        await manager.send_message(
            {
                "type": WebSocketMessageType.ASSISTANT_TOKEN,
                "content": {
                    "id": assistant_message_id,
                    "token": token
                },
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            },
            client_id
        )
    
    async def on_thinking(thinking: str):
        await manager.send_message(
            {
                "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                "content": {
                    "status": "thinking",
                    "id": superego_message_id,
                    "thinking": thinking
                },
                "conversation_id": conversation_id,
                "timestamp": datetime.now().isoformat()
            },
            client_id
        )
    
    return {
        "on_token": on_token,
        "on_thinking": on_thinking,
        "assistant_id": assistant_message_id,
        "superego_id": superego_message_id
    }

async def handle_websocket_connection(websocket: WebSocket, client_id: str, conversations: Dict[str, List[Message]]):
    """
    Handle a WebSocket connection
    
    Args:
        websocket: The WebSocket connection
        client_id: The client's unique ID
        conversations: Dictionary of conversations (used only as in-memory cache)
    """
    if not client_id:
        client_id = str(uuid.uuid4())
    
    await manager.connect(websocket, client_id)
    
    try:
        # Small delay to ensure connection is stable
        await asyncio.sleep(0.2)
        
        conversation_id = None
        messages: List[Message] = []
        
        while True:
            data = await websocket.receive_text()
            
            try:
                request_data = json.loads(data)
                logger.info(f"Received message from client {client_id}: {request_data}")
                
                # Extract the message type
                if "type" not in request_data:
                    raise ValueError("Missing message type")
                
                message_type = request_data.get("type")
                logger.info(f"Processing message type: {message_type}")
                
                # Extract and normalize message content
                # This handles cases where a client sends a nested message (type inside content)
                message_content = request_data.get("content", "")
                conversation_id = request_data.get("conversation_id") 
                
                # Special case handling for nested JSON in content (common in some client implementations)
                if isinstance(message_content, str) and message_content.startswith("{"):
                    try:
                        # Try to parse the content as JSON
                        content_json = json.loads(message_content)
                        
                        # If content has a 'type' field, it might be a command message nested in content
                        if isinstance(content_json, dict) and "type" in content_json:
                            nested_type = content_json.get("type")
                            logger.info(f"Found nested message of type {nested_type} in content")
                            
                            # Use the conversation_id from the nested content if available
                            if content_json.get("conversation_id"):
                                conversation_id = content_json.get("conversation_id")
                                logger.info(f"Using conversation_id from nested content: {conversation_id}")
                            
                            # Update the message type and request data to use the nested values
                            message_type = nested_type
                            
                            # Merge the outer message fields with the inner ones, prioritizing inner values
                            merged_data = request_data.copy()
                            merged_data.update(content_json)
                            # Restore the conversation_id if it was present
                            if conversation_id:
                                merged_data["conversation_id"] = conversation_id
                            request_data = merged_data
                            
                            logger.info(f"Updated message to type {message_type}")
                    except json.JSONDecodeError:
                        # Not valid JSON, continue with original message
                        pass
                
                # Handle different message types
                if message_type == "user_message":
                    if "content" not in request_data:
                        raise ValueError("Missing message content")
                    
                    user_input = request_data.get("content")
                    conversation_id = request_data.get("conversation_id", conversation_id)
                    constitution_id = request_data.get("constitution_id")
                    sysprompt_id = request_data.get("sysprompt_id")
                    
                    # Initialize conversation if needed
                    if not conversation_id:
                        conversation_id = str(uuid.uuid4())
                        conversations[conversation_id] = []
                        messages = []
                    else:
                        messages = conversations.get(conversation_id, [])
                    
                    # Notify that superego is evaluating
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                            "content": {
                                "status": "started", 
                                "message": "Superego is evaluating your message...",
                                "constitutionId": constitution_id
                            },
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                    
                    # Create callbacks for streaming responses
                    callbacks = await create_callbacks(client_id, conversation_id)
                    
                    # Get user messages only to prevent loops
                    user_messages = filter_user_messages(messages)
                    
                    # Process with LangGraph
                    result = await run_graph(
                        user_input=user_input,
                        conversation_id=conversation_id,
                        messages=user_messages,
                        constitution_id=constitution_id,
                        sysprompt_id=sysprompt_id,
                        on_token=callbacks["on_token"],
                        on_thinking=callbacks["on_thinking"]
                    )
                    
                    # Extract messages from result
                    updated_messages = result["messages"]
                    
                    # Find the new superego and assistant messages
                    superego_message = None
                    assistant_message = None
                    
                    for msg in updated_messages:
                        if msg.role == MessageRole.SUPEREGO:
                            superego_message = msg
                        elif msg.role == MessageRole.ASSISTANT:
                            assistant_message = msg
                    
                    # Update conversation storage in memory and on disk
                    conversations[conversation_id] = updated_messages
                    messages = updated_messages
                    update_conversation(conversation_id, updated_messages)
                    
                    # Send the superego evaluation result
                    if superego_message:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                                "content": {
                                    "status": "completed",
                                    "decision": superego_message.decision,
                                    "reason": superego_message.content,
                                    "thinking": superego_message.thinking,
                                    "id": superego_message.id,
                                    "constitutionId": constitution_id,
                                    "checkpoint_id": result.get("checkpoint_id")
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    
                    # Send the complete assistant response
                    if assistant_message:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ASSISTANT_MESSAGE,
                                "content": {
                                    "id": assistant_message.id,
                                    "content": assistant_message.content
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    
                    logger.info(f"Updated conversation with {len(updated_messages)} messages")
                    
                elif message_type == "get_constitutions":
                    # Return available constitutions
                    constitutions = get_all_constitutions()
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.CONSTITUTIONS_RESPONSE,
                            "content": list(constitutions.values()),
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "rerun_message":
                    # Rerun a message with potentially different constitution/sysprompt
                    if "message_id" not in request_data:
                        raise ValueError("Missing message_id")
                    
                    message_id = request_data.get("message_id")
                    constitution_id = request_data.get("constitution_id")
                    sysprompt_id = request_data.get("sysprompt_id")
                    conversation_id = request_data.get("conversation_id", conversation_id)
                    
                    # Conversation ID must be provided for reruns and must exist
                    if not conversation_id:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": "Conversation ID is required for rerunning messages",
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    if conversation_id not in conversations:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": f"Conversation with ID {conversation_id} not found. The session may have expired or the server was restarted.",
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    messages = conversations.get(conversation_id, [])
                    
                    # Get the messages
                    messages = conversations.get(conversation_id, [])
                    
                    # Try to find a checkpoint associated with this message
                    from .graph import message_checkpoints
                    
                    checkpoint_id = None
                    
                    # First, check if we have a direct mapping from message ID to checkpoint
                    if message_id in message_checkpoints:
                        checkpoint_id = message_checkpoints[message_id]
                        logger.info(f"Found checkpoint {checkpoint_id} for message {message_id}")
                    else:
                        # Find the message to rerun
                        original_message = None
                        message_index = -1
                        for i, msg in enumerate(messages):
                            if msg.id == message_id:
                                original_message = msg
                                message_index = i
                                break
                        
                        if not original_message:
                            await manager.send_message(
                                {
                                    "type": WebSocketMessageType.ERROR,
                                    "content": f"Message with ID {message_id} not found",
                                    "timestamp": datetime.now().isoformat()
                                }, 
                                client_id
                            )
                            continue
                        
                        # If rerunning an assistant or superego message, find the preceding user message
                        user_message = None
                        if original_message.role in [MessageRole.ASSISTANT, MessageRole.SUPEREGO]:
                            # Look backward from the original message to find the user message
                            for i in range(message_index, -1, -1):
                                if messages[i].role == MessageRole.USER:
                                    user_message = messages[i]
                                    # Check if this user message has a checkpoint
                                    if user_message.id in message_checkpoints:
                                        checkpoint_id = message_checkpoints[user_message.id]
                                        logger.info(f"Found checkpoint {checkpoint_id} for preceding user message {user_message.id}")
                                    break
                        elif original_message.role == MessageRole.USER:
                            user_message = original_message
                        
                        if not user_message:
                            await manager.send_message(
                                {
                                    "type": WebSocketMessageType.ERROR,
                                    "content": "Could not find user message to rerun",
                                    "timestamp": datetime.now().isoformat()
                                }, 
                                client_id
                            )
                            continue
                    
                    # Notify that processing is starting
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                            "content": {
                                "status": "started", 
                                "message": "Rerunning message...",
                                "constitutionId": constitution_id
                            },
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                    
                    # Create callbacks for streaming responses
                    callbacks = await create_callbacks(client_id, conversation_id)
                    
                    # Get user messages only up to the current one
                    user_messages = []
                    for msg in messages:
                        if msg.role == MessageRole.USER:
                            user_messages.append(msg)
                            if msg.id == user_message.id:
                                break
                    
                    # If we have a checkpoint, use rerun_from_checkpoint instead of run_graph
                    if checkpoint_id:
                        try:
                            logger.info(f"Rerunning from checkpoint {checkpoint_id} with constitution {constitution_id} and sysprompt {sysprompt_id}")
                            result = await rerun_from_checkpoint(
                                checkpoint_id=checkpoint_id,
                                constitution_id=constitution_id,
                                sysprompt_id=sysprompt_id,
                                on_token=callbacks["on_token"],
                                on_thinking=callbacks["on_thinking"]
                            )
                        except ValueError as e:
                            # Fallback to run_graph if checkpoint not found
                            logger.warning(f"Checkpoint {checkpoint_id} not found, falling back to run_graph: {str(e)}")
                            await manager.send_message(
                                {
                                    "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                    "content": "Session checkpoints not found. Running a fresh evaluation.",
                                    "timestamp": datetime.now().isoformat()
                                }, 
                                client_id
                            )
                            result = await run_graph(
                                user_input=user_message.content,
                                conversation_id=conversation_id,
                                messages=user_messages,
                                constitution_id=constitution_id,
                                sysprompt_id=sysprompt_id,
                                on_token=callbacks["on_token"],
                                on_thinking=callbacks["on_thinking"]
                            )
                    else:
                        # No checkpoint, just run the graph
                        result = await run_graph(
                            user_input=user_message.content,
                            conversation_id=conversation_id,
                            messages=user_messages,
                            constitution_id=constitution_id,
                            sysprompt_id=sysprompt_id,
                            on_token=callbacks["on_token"],
                            on_thinking=callbacks["on_thinking"]
                        )
                    
                    # For reruns, we need to handle replacing existing messages properly
                    updated_messages = result["messages"]
                    
                    # Find the user message that was rerun
                    user_message_index = -1
                    for i, msg in enumerate(messages):
                        if msg.id == user_message.id:
                            user_message_index = i
                            break
                    
                    # If we found the user message, we want to keep everything up to and including it,
                    # and then append the new superego and assistant messages
                    if user_message_index >= 0:
                        # Keep all messages up to and including the user message
                        preserved_messages = messages[:user_message_index + 1]
                        
                        # Find the new superego and assistant messages from the result
                        new_superego_message = None
                        new_assistant_message = None
                        
                        for msg in updated_messages:
                            if msg.role == MessageRole.SUPEREGO:
                                new_superego_message = msg
                            elif msg.role == MessageRole.ASSISTANT:
                                new_assistant_message = msg
                        
                        # Combine preserved messages with new responses
                        final_messages = preserved_messages.copy()
                        if new_superego_message:
                            final_messages.append(new_superego_message)
                        if new_assistant_message:
                            final_messages.append(new_assistant_message)
                        
                        # Update conversation storage with the combined messages in memory and on disk
                        conversations[conversation_id] = final_messages
                        messages = final_messages
                        update_conversation(conversation_id, final_messages)
                        
                        # Send a message to replace the entire conversation in the frontend
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.CONVERSATION_UPDATE,
                                "content": {
                                    "messages": [msg.dict() for msg in final_messages],
                                    "replace": True
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            },
                            client_id
                        )
                        
                        # Set these for the individual notifications
                        superego_message = new_superego_message
                        assistant_message = new_assistant_message
                    else:
                        # If we couldn't find the user message, just use the standard approach
                        superego_message = None
                        assistant_message = None
                        
                        for msg in updated_messages:
                            if msg.role == MessageRole.SUPEREGO:
                                superego_message = msg
                            elif msg.role == MessageRole.ASSISTANT:
                                assistant_message = msg
                        
                    # Update conversation storage in memory and on disk
                    conversations[conversation_id] = updated_messages
                    messages = updated_messages
                    update_conversation(conversation_id, updated_messages)
                    
                    # Send the superego evaluation result
                    if superego_message:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                                "content": {
                                    "status": "completed",
                                    "decision": superego_message.decision,
                                    "reason": superego_message.content,
                                    "thinking": superego_message.thinking,
                                    "id": superego_message.id,
                                    "constitutionId": constitution_id,
                                    "checkpoint_id": result.get("checkpoint_id")
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    
                    # Send the complete assistant response
                    if assistant_message:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ASSISTANT_MESSAGE,
                                "content": {
                                    "id": assistant_message.id,
                                    "content": assistant_message.content
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    
                    logger.info(f"Updated conversation with {len(updated_messages)} messages")
                
                elif message_type == "rerun_from_constitution":
                    # Rerun with a different constitution
                    if "constitution_id" not in request_data:
                        raise ValueError("Missing constitution_id")
                    
                    constitution_id = request_data.get("constitution_id")
                    checkpoint_id = request_data.get("checkpoint_id")
                    
                    # Notify that superego is evaluating with new constitution
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                            "content": {
                                "status": "started", 
                                "message": "Superego is evaluating with new constitution...",
                                "constitutionId": constitution_id
                            },
                            "conversation_id": conversation_id,
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                    
                    # Create callbacks for streaming responses
                    callbacks = await create_callbacks(client_id, conversation_id)
                    
                    if checkpoint_id:
                        # Rerun from checkpoint
                        result = await rerun_from_checkpoint(
                            checkpoint_id=checkpoint_id,
                            constitution_id=constitution_id,
                            sysprompt_id=request_data.get("sysprompt_id"),
                            on_token=callbacks["on_token"],
                            on_thinking=callbacks["on_thinking"]
                        )
                    else:
                        # Find last user message and rerun
                        last_user_message = None
                        for message in reversed(messages):
                            if message.role == MessageRole.USER:
                                last_user_message = message
                                break
                        
                        if not last_user_message:
                            await manager.send_message(
                                {
                                    "type": WebSocketMessageType.ERROR,
                                    "content": "No user message found to rerun",
                                    "timestamp": datetime.now().isoformat()
                                }, 
                                client_id
                            )
                            continue
                        
                        # Get user messages only
                        user_messages = filter_user_messages(messages)
                        
                        # Process with LangGraph
                        result = await run_graph(
                            user_input=last_user_message.content,
                            conversation_id=conversation_id,
                            messages=user_messages,
                            constitution_id=constitution_id,
                            on_token=callbacks["on_token"],
                            on_thinking=callbacks["on_thinking"]
                        )
                    
                    # Extract messages from result
                    updated_messages = result["messages"]
                    
                    # Find the new superego and assistant messages
                    superego_message = None
                    assistant_message = None
                    
                    for msg in updated_messages:
                        if msg.role == MessageRole.SUPEREGO:
                            superego_message = msg
                        elif msg.role == MessageRole.ASSISTANT:
                            assistant_message = msg
                    
                    # Send the superego evaluation result
                    if superego_message:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SUPEREGO_EVALUATION,
                                "content": {
                                    "status": "completed",
                                    "decision": superego_message.decision,
                                    "reason": superego_message.content,
                                    "thinking": superego_message.thinking,
                                    "id": superego_message.id,
                                    "constitutionId": constitution_id,
                                    "checkpoint_id": result.get("checkpoint_id")
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    
                    # Send the complete assistant response
                    if assistant_message:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ASSISTANT_MESSAGE,
                                "content": {
                                    "id": assistant_message.id,
                                    "content": assistant_message.content
                                },
                                "conversation_id": conversation_id,
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    
                    # Update conversation storage in memory and on disk
                    conversations[conversation_id] = updated_messages
                    messages = updated_messages
                    update_conversation(conversation_id, updated_messages)
                    
                    logger.info(f"Updated conversation with {len(updated_messages)} messages")
                    
                elif message_type == "get_system_prompts" or message_type == "get_sysprompts":
                    # Return available system prompts
                    sysprompts = get_all_sysprompts()
                    
                    if message_type == "get_sysprompts":
                        # Return in format for dropdown
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SYSPROMPTS_RESPONSE,
                                "content": list(sysprompts.values()),
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    else:
                        # Backward compatibility format
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "sysprompts": list(sysprompts.values())
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                
                elif message_type == "get_flow_templates":
                    # Return available flow templates
                    templates = get_all_flow_templates()
                    # Convert templates to dictionaries for JSON serialization
                    serialized_templates = [template.dict() for template in templates.values()]
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.FLOW_TEMPLATES_RESPONSE,
                            "content": serialized_templates,
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "get_flow_configs":
                    # Return available flow configurations
                    configs = get_all_flow_configs()
                    # Convert configs to dictionaries for JSON serialization
                    serialized_configs = [config.dict() for config in configs.values()]
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.FLOW_CONFIGS_RESPONSE,
                            "content": serialized_configs,
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "get_flow_instances":
                    # Return available flow instances
                    instances = get_all_flow_instances()
                    # Convert instances to dictionaries for JSON serialization
                    serialized_instances = [instance.dict() for instance in instances.values()]
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.FLOW_INSTANCES_RESPONSE,
                            "content": serialized_instances,
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "get_conversation_history":
                    # Return conversation history for the current flow instance
                    conversation_id = request_data.get("flow_instance_id") or request_data.get("conversation_id")
                    
                    if not conversation_id:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": "Missing flow instance ID or conversation ID",
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    # Get the conversation history from persistent storage
                    history = get_conversation(conversation_id)
                    
                    # Update the in-memory cache
                    conversations[conversation_id] = history
                    messages = history  # Update the current messages variable too
                    
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
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": True,
                                    "message": f"Found instance: {instance.name}",
                                    "instance": instance.dict()
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    else:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": f"Flow instance with ID {instance_id} not found",
                                "timestamp": datetime.now().isoformat()
                            }, 
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
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": True,
                                "message": f"Flow template created: {template.name}",
                                "template": template.dict()
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
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
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": True,
                                "message": f"Flow instance created: {instance.name}",
                                "instance": instance.dict()
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
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
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": True,
                                    "message": f"Flow template updated: {template.name}",
                                    "template": template.dict()
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    else:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": f"Flow template with ID {template_id} not found",
                                "timestamp": datetime.now().isoformat()
                            }, 
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
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": True,
                                    "message": f"Flow configuration updated: {config.name}",
                                    "config": config.dict()
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    else:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": f"Flow configuration with ID {config_id} not found",
                                "timestamp": datetime.now().isoformat()
                            }, 
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
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": True,
                                    "message": f"Flow instance updated: {instance.name}",
                                    "instance": instance.dict()
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                    else:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": f"Flow instance with ID {instance_id} not found",
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                
                elif message_type == "delete_flow_template":
                    # Delete a flow template
                    if "id" not in request_data:
                        raise ValueError("Missing template ID")
                    
                    template_id = request_data.get("id")
                    success = delete_flow_template(template_id)
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"Flow template {'deleted' if success else 'not found'}: {template_id}"
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "delete_flow_config":
                    # Delete a flow configuration
                    if "id" not in request_data:
                        raise ValueError("Missing config ID")
                    
                    config_id = request_data.get("id")
                    success = delete_flow_config(config_id)
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"Flow configuration {'deleted' if success else 'not found or in use'}: {config_id}"
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "delete_flow_instance":
                    # Delete a flow instance
                    if "id" not in request_data:
                        raise ValueError("Missing instance ID")
                    
                    instance_id = request_data.get("id")
                    success = delete_flow_instance(instance_id)
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"Flow instance {'deleted' if success else 'not found'}: {instance_id}"
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
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
                        conversations[conversation_id] = []
                    
                    messages = conversations.get(conversation_id, [])
                    
                    # Get user messages only to prevent loops
                    user_messages = filter_user_messages(messages)
                    
                    # Create on_token and on_thinking callbacks for each flow
                    on_token = {}
                    on_thinking = {}
                    
                    for config_id in flow_config_ids:
                        flow_assistant_id = str(uuid.uuid4())
                        flow_superego_id = str(uuid.uuid4())
                        
                        async def create_token_callback(id):
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
                        
                        async def create_thinking_callback(id):
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
                        
                        on_token[config_id] = await create_token_callback(flow_assistant_id)
                        on_thinking[config_id] = await create_thinking_callback(flow_superego_id)
                    
                    # Run flows in parallel
                    results = await run_multiple_flows(
                        flow_config_ids=flow_config_ids,
                        user_input=user_input,
                        conversation_id=conversation_id,
                        messages=user_messages,
                        on_token=on_token,
                        on_thinking=on_thinking
                    )
                    
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
                
                elif message_type == "save_constitution" or message_type == "create_constitution":
                    # Save a new constitution
                    if not all(k in request_data for k in ["id", "name", "content"]):
                        raise ValueError("Missing required fields for constitution (id, name, content)")
                    
                    constitution_id = request_data.get("id")
                    name = request_data.get("name")
                    content = request_data.get("content")
                    
                    success = save_constitution(constitution_id, name, content)
                    
                    # Get the saved constitution to return to the client
                    saved_constitution = None
                    if success:
                        constitutions = get_all_constitutions()
                        saved_constitution = constitutions.get(constitution_id)
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"Constitution {'saved' if success else 'failed to save'}: {name}",
                                "constitution": saved_constitution
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                    
                elif message_type == "update_constitution":
                    # Update an existing constitution
                    if "id" not in request_data:
                        raise ValueError("Missing constitution ID")
                    
                    constitution_id = request_data.get("id")
                    name = request_data.get("name")
                    content = request_data.get("content")
                    
                    # Get the existing constitution
                    constitutions = get_all_constitutions()
                    existing_constitution = constitutions.get(constitution_id)
                    
                    if not existing_constitution:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": False,
                                    "message": f"Constitution with ID {constitution_id} not found"
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    # Update with new values or keep existing ones
                    updated_name = name if name is not None else existing_constitution["name"]
                    updated_content = content if content is not None else existing_constitution["content"]
                    
                    success = save_constitution(constitution_id, updated_name, updated_content)
                    
                    # Get the updated constitution to return to the client
                    updated_constitution = None
                    if success:
                        constitutions = get_all_constitutions()
                        updated_constitution = constitutions.get(constitution_id)
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"Constitution {'updated' if success else 'failed to update'}: {updated_name}",
                                "constitution": updated_constitution
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                    
                elif message_type == "delete_constitution":
                    # Delete a constitution
                    if "id" not in request_data:
                        raise ValueError("Missing constitution ID")
                    
                    constitution_id = request_data.get("id")
                    
                    # Check if this is a protected constitution
                    protected_ids = ["default", "none"]
                    if constitution_id in protected_ids:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": False,
                                    "message": f"Cannot delete protected constitution: {constitution_id}"
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    # Get the constitution name before deleting
                    constitutions = get_all_constitutions()
                    constitution = constitutions.get(constitution_id)
                    
                    if not constitution:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.SYSTEM_MESSAGE,
                                "content": {
                                    "success": False,
                                    "message": f"Constitution with ID {constitution_id} not found"
                                },
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    constitution_name = constitution["name"]
                    
                    # Delete the constitution file
                    import os
                    from .constitution_registry import CONSTITUTIONS_DIR
                    
                    file_path = os.path.join(CONSTITUTIONS_DIR, f"{constitution_id}.md")
                    
                    try:
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            success = True
                        else:
                            success = False
                    except Exception as e:
                        logger.error(f"Error deleting constitution file: {str(e)}")
                        success = False
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"Constitution {'deleted' if success else 'failed to delete'}: {constitution_name}"
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                elif message_type == "save_system_prompt":
                    # Save a new system prompt
                    if not all(k in request_data for k in ["id", "name", "content"]):
                        raise ValueError("Missing required fields for system prompt (id, name, content)")
                    
                    success = save_sysprompt(
                        request_data.get("id"),
                        request_data.get("name"),
                        request_data.get("content")
                    )
                    
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.SYSTEM_MESSAGE,
                            "content": {
                                "success": success,
                                "message": f"System prompt {'saved' if success else 'failed to save'}: {request_data.get('name')}"
                            },
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
                else:
                    # Unhandled message type
                    logger.warning(f"Unhandled message type: {message_type}")
                    await manager.send_message(
                        {
                            "type": WebSocketMessageType.ERROR,
                            "content": f"Unhandled message type: {message_type}",
                            "timestamp": datetime.now().isoformat()
                        }, 
                        client_id
                    )
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON received: {data}")
                await manager.send_message(
                    {
                        "type": WebSocketMessageType.ERROR,
                        "content": "Invalid JSON format",
                        "timestamp": datetime.now().isoformat()
                    },
                    client_id
                )
            except ValueError as e:
                logger.error(f"Value error: {str(e)}")
                await manager.send_message(
                    {
                        "type": WebSocketMessageType.ERROR,
                        "content": str(e),
                        "timestamp": datetime.now().isoformat()
                    },
                    client_id
                )
            except Exception as e:
                logger.error(f"Error processing message: {str(e)}")
                await manager.send_message(
                    {
                        "type": WebSocketMessageType.ERROR,
                        "content": f"Error processing message: {str(e)}",
                        "timestamp": datetime.now().isoformat()
                    },
                    client_id
                )
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket connection: {str(e)}")
        manager.disconnect(client_id)
