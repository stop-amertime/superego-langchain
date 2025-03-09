"""
Message store for persistent storage of flow instance messages.
This module provides functions for storing and retrieving messages for flow instances.
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
MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "data", "messages.json")

# In-memory cache of messages
messages: Dict[str, List[Dict]] = {}

def ensure_messages_file_exists():
    """Ensure that the messages file exists with at least an empty JSON object."""
    if not os.path.exists(MESSAGES_FILE):
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(MESSAGES_FILE), exist_ok=True)
        # Create an empty JSON file
        with open(MESSAGES_FILE, 'w') as f:
            json.dump({}, f)
        logger.info(f"Created empty messages file: {MESSAGES_FILE}")

def load_messages():
    """Load messages from file."""
    global messages
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r') as f:
                data = json.load(f)
                messages = data
        else:
            ensure_messages_file_exists()
    except Exception as e:
        logger.error(f"Error loading messages: {e}")
        ensure_messages_file_exists()

def save_messages():
    """Save messages to file."""
    try:
        with open(MESSAGES_FILE, 'w') as f:
            json.dump(messages, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving messages: {e}")

def get_messages(message_store_id: str) -> List[Message]:
    """
    Get messages for a flow instance by message store ID.
    
    Args:
        message_store_id: The message store ID
        
    Returns:
        List of messages in the store
    """
    if not messages:
        load_messages()
    
    # Convert the stored dictionaries to Message objects
    message_dicts = messages.get(message_store_id, [])
    return [Message.parse_obj(msg) for msg in message_dicts]

def update_messages(message_store_id: str, messages_list: List[Message]):
    """
    Update messages for a flow instance.
    
    Args:
        message_store_id: The message store ID
        messages_list: The updated list of messages
    """
    if not messages:
        load_messages()
    
    # Convert Message objects to dictionaries for storage
    messages[message_store_id] = [msg.dict() for msg in messages_list]
    save_messages()

def delete_message_store(message_store_id: str) -> bool:
    """
    Delete a message store.
    
    Args:
        message_store_id: The message store ID
        
    Returns:
        True if the message store was deleted, False otherwise
    """
    if not messages:
        load_messages()
    
    if message_store_id in messages:
        del messages[message_store_id]
        save_messages()
        return True
    return False

def get_all_message_stores() -> Dict[str, List[Message]]:
    """
    Get all message stores.
    
    Returns:
        Dictionary of message store IDs to lists of messages
    """
    if not messages:
        load_messages()
    
    # Convert the stored dictionaries to Message objects
    return {
        store_id: [Message.parse_obj(msg) for msg in msgs]
        for store_id, msgs in messages.items()
    }

# Initialize on module import
ensure_messages_file_exists()
load_messages()
