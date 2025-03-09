"""
Handler for user message related WebSocket messages.
This module handles processing user messages and rerunning messages.
"""

import logging
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime

from ...models import Message, WebSocketMessageType, MessageRole
from ...graph import run_graph, rerun_from_checkpoint, filter_user_messages, message_checkpoints
from ..utils import create_message
from ...conversation_manager import get_conversation, update_conversation

# Set up logging
logger = logging.getLogger(__name__)

async def create_callbacks(manager, client_id: str, conversation_id: str) -> Dict[str, Any]:
    """
    Create token and thinking callbacks for streaming responses
    
    Args:
        manager: The connection manager
        client_id: The client's unique ID
        conversation_id: The conversation ID
        
    Returns:
        Dictionary of callbacks and message IDs
    """
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

async def handle_user_message(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle a user message
    
    Args:
        context: The conversation context
        
    Returns:
        Updated context with messages and conversation ID
    """
    client_id = context["client_id"]
    conversation_id = context["conversation_id"]
    conversations = context["conversations"]
    messages = context["messages"]
    manager = context["manager"]
    request_data = context["request_data"]
    
    if "content" not in request_data:
        raise ValueError("Missing message content")
    
    user_input = request_data.get("content")
    conversation_id = request_data.get("conversation_id", conversation_id)
    constitution_id = request_data.get("constitution_id")
    sysprompt_id = request_data.get("sysprompt_id")
    
    # Initialize conversation if needed
    if not conversation_id:
        conversation_id = str(uuid.uuid4())
        messages = []
    else:
        # Get messages from persistent storage
        messages = get_conversation(conversation_id)
    
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
    callbacks = await create_callbacks(manager, client_id, conversation_id)
    
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
    
    # Update conversation in persistent storage
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
    
    return {
        "messages": updated_messages,
        "conversation_id": conversation_id
    }

async def handle_rerun_message(message_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle rerunning a message with potentially different constitution/sysprompt
    
    Args:
        message_type: The message type (rerun_message or rerun_from_constitution)
        context: The conversation context
        
    Returns:
        Updated context with messages
    """
    client_id = context["client_id"]
    conversation_id = context["conversation_id"]
    conversations = context["conversations"]
    messages = context["messages"]
    manager = context["manager"]
    request_data = context["request_data"]
    
    if message_type == "rerun_message":
        if "message_id" not in request_data:
            raise ValueError("Missing message_id")
        
        message_id = request_data.get("message_id")
        constitution_id = request_data.get("constitution_id")
        sysprompt_id = request_data.get("sysprompt_id")
        conversation_id = request_data.get("conversation_id", conversation_id)
        
        # Conversation ID must be provided for reruns and must exist
        if not conversation_id:
            await manager.send_message(
                create_message(
                    WebSocketMessageType.ERROR,
                    "Conversation ID is required for rerunning messages",
                    None
                ),
                client_id
            )
            return {}
        
        if conversation_id not in conversations:
            await manager.send_message(
                create_message(
                    WebSocketMessageType.ERROR,
                    f"Conversation with ID {conversation_id} not found. The session may have expired or the server was restarted.",
                    None
                ),
                client_id
            )
            return {}
        
        messages = conversations.get(conversation_id, [])
        
        # Try to find a checkpoint associated with this message
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
                    create_message(
                        WebSocketMessageType.ERROR,
                        f"Message with ID {message_id} not found",
                        None
                    ),
                    client_id
                )
                return {}
            
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
                    create_message(
                        WebSocketMessageType.ERROR,
                        "Could not find user message to rerun",
                        None
                    ),
                    client_id
                )
                return {}
    
    elif message_type == "rerun_from_constitution":
        # Rerun with a different constitution
        if "constitution_id" not in request_data:
            raise ValueError("Missing constitution_id")
        
        constitution_id = request_data.get("constitution_id")
        checkpoint_id = request_data.get("checkpoint_id")
        sysprompt_id = request_data.get("sysprompt_id")
        
        # Find last user message if no checkpoint provided
        if not checkpoint_id:
            last_user_message = None
            for message in reversed(messages):
                if message.role == MessageRole.USER:
                    last_user_message = message
                    break
            
            if not last_user_message:
                await manager.send_message(
                    create_message(
                        WebSocketMessageType.ERROR,
                        "No user message found to rerun",
                        None
                    ),
                    client_id
                )
                return {}
            
            user_message = last_user_message
    
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
    callbacks = await create_callbacks(manager, client_id, conversation_id)
    
    # Get user messages only up to the current one if rerunning a specific message
    if message_type == "rerun_message":
        user_messages = []
        for msg in messages:
            if msg.role == MessageRole.USER:
                user_messages.append(msg)
                if msg.id == user_message.id:
                    break
    else:
        # For rerun_from_constitution, get all user messages
        user_messages = filter_user_messages(messages)
    
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
                create_message(
                    WebSocketMessageType.SYSTEM_MESSAGE,
                    "Session checkpoints not found. Running a fresh evaluation.",
                    None
                ),
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
    
    if message_type == "rerun_message":
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
            
            # Update conversation in persistent storage
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
            
            # Update the messages in the context
            messages = final_messages
        else:
            # If we couldn't find the user message, just use the standard approach
            superego_message = None
            assistant_message = None
            
            for msg in updated_messages:
                if msg.role == MessageRole.SUPEREGO:
                    superego_message = msg
                elif msg.role == MessageRole.ASSISTANT:
                    assistant_message = msg
            
            # Update conversation in persistent storage
            update_conversation(conversation_id, updated_messages)
            messages = updated_messages
    else:
        # For rerun_from_constitution, just use the updated messages
        superego_message = None
        assistant_message = None
        
        for msg in updated_messages:
            if msg.role == MessageRole.SUPEREGO:
                superego_message = msg
            elif msg.role == MessageRole.ASSISTANT:
                assistant_message = msg
        
        # Update conversation in persistent storage
        update_conversation(conversation_id, updated_messages)
        messages = updated_messages
    
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
    
    logger.info(f"Updated conversation with {len(messages)} messages")
    
    return {
        "messages": messages
    }
