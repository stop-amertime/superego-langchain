"""
Conversation manager for persistent storage of conversation messages.
This module provides functions for storing and retrieving conversation messages.
"""

import json
import os
import logging
from typing import Dict, List, Optional
from datetime import datetime

from .models import Message

# Set up logging
logger = logging.getLogger(__name__)

# File path for persistent storage
CONVERSATIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "conversations.json")

# In-memory cache of conversations
conversations: Dict[str, List[Dict]] = {}

def ensure_conversations_file_exists():
    """Ensure that the conversations file exists with at least an empty JSON object."""
    if not os.path.exists(CONVERSATIONS_FILE):
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(CONVERSATIONS_FILE), exist_ok=True)
        # Create an empty JSON file
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump({}, f)
        logger.info(f"Created empty conversations file: {CONVERSATIONS_FILE}")

def load_conversations():
    """Load conversations from file."""
    global conversations
    try:
        if os.path.exists(CONVERSATIONS_FILE):
            with open(CONVERSATIONS_FILE, 'r') as f:
                data = json.load(f)
                conversations = data
        else:
            ensure_conversations_file_exists()
    except Exception as e:
        logger.error(f"Error loading conversations: {e}")
        ensure_conversations_file_exists()

def save_conversations():
    """Save conversations to file."""
    try:
        with open(CONVERSATIONS_FILE, 'w') as f:
            json.dump(conversations, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving conversations: {e}")

def get_conversation(conversation_id: str) -> List[Message]:
    """
    Get a conversation by ID.
    
    Args:
        conversation_id: The conversation ID
        
    Returns:
        List of messages in the conversation
    """
    if not conversations:
        load_conversations()
    
    # Convert the stored dictionaries to Message objects
    message_dicts = conversations.get(conversation_id, [])
    return [Message.parse_obj(msg) for msg in message_dicts]

def update_conversation(conversation_id: str, messages: List[Message]):
    """
    Update a conversation with new messages.
    
    Args:
        conversation_id: The conversation ID
        messages: The updated list of messages
    """
    if not conversations:
        load_conversations()
    
    # Convert Message objects to dictionaries for storage
    conversations[conversation_id] = [msg.dict() for msg in messages]
    save_conversations()

def delete_conversation(conversation_id: str) -> bool:
    """
    Delete a conversation.
    
    Args:
        conversation_id: The conversation ID
        
    Returns:
        True if the conversation was deleted, False otherwise
    """
    if not conversations:
        load_conversations()
    
    if conversation_id in conversations:
        del conversations[conversation_id]
        save_conversations()
        return True
    return False

def get_all_conversations() -> Dict[str, List[Message]]:
    """
    Get all conversations.
    
    Returns:
        Dictionary of conversation IDs to lists of messages
    """
    if not conversations:
        load_conversations()
    
    # Convert the stored dictionaries to Message objects
    return {
        conv_id: [Message.parse_obj(msg) for msg in msgs]
        for conv_id, msgs in conversations.items()
    }

# Initialize on module import
ensure_conversations_file_exists()
load_conversations()
