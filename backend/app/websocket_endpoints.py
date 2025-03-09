import json
import uuid
import asyncio
import logging
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

from .models import Message, WebSocketMessageType, MessageRole, ParallelFlowResult
from .connection_manager import ConnectionManager
from .graph import run_graph, rerun_from_checkpoint, filter_user_messages
from .conversation_manager import get_conversation, update_conversation
from .flow_manager import run_multiple_flows

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
                    
                    # Get conversation from persistent storage
                    messages = get_conversation(conversation_id)
                    if not messages:
                        await manager.send_message(
                            {
                                "type": WebSocketMessageType.ERROR,
                                "content": f"Conversation with ID {conversation_id} not found.",
                                "timestamp": datetime.now().isoformat()
                            }, 
                            client_id
                        )
                        continue
                    
                    # Update in-memory cache
                    conversations[conversation_id] = messages
                    
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
                        # Get conversation from persistent storage
                        messages = get_conversation(conversation_id)
                        if not messages:
                            await manager.send_message(
                                {
                                    "type": WebSocketMessageType.ERROR,
                                    "content": f"Conversation with ID {conversation_id} not found.",
                                    "timestamp": datetime.now().isoformat()
                                }, 
                                client_id
                            )
                            continue
                        
                        # Update in-memory cache
                        conversations[conversation_id] = messages
                        
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
                    
                    # Get conversation from persistent storage
                    messages = get_conversation(conversation_id)
                    
                    # Update in-memory cache
                    conversations[conversation_id] = messages
                    
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
