"""
Migration script for converting existing flow instances and messages to the new format.

This script will:
1. Load existing flow templates and create flow definitions
2. Load existing flow instances and update them to the new format
3. Load messages from the message store and add them to flow instances
"""

import json
import os
import uuid
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .models import (
    FlowDefinition, 
    FlowInstance, 
    FlowStatus, 
    NodeConfig, 
    EdgeConfig, 
    Message,
    MessageRole
)
from .flow_engine import get_flow_engine, START_NODE, END_NODE
from .agents import AgentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# File paths for old data
FLOW_TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), "data", "flow_templates.json")
FLOW_CONFIGS_FILE = os.path.join(os.path.dirname(__file__), "data", "flow_configs.json")
FLOW_INSTANCES_FILE = os.path.join(os.path.dirname(__file__), "data", "flow_instances.json")
MESSAGES_FILE = os.path.join(os.path.dirname(__file__), "data", "messages.json")

def load_old_flow_templates() -> Dict[str, Any]:
    """Load old flow templates from file."""
    try:
        if os.path.exists(FLOW_TEMPLATES_FILE):
            with open(FLOW_TEMPLATES_FILE, 'r') as f:
                data = json.load(f)
                return data
        else:
            logger.warning(f"Flow templates file not found: {FLOW_TEMPLATES_FILE}")
            return {}
    except Exception as e:
        logger.error(f"Error loading flow templates: {e}")
        return {}

def load_old_flow_configs() -> Dict[str, Any]:
    """Load old flow configurations from file."""
    try:
        if os.path.exists(FLOW_CONFIGS_FILE):
            with open(FLOW_CONFIGS_FILE, 'r') as f:
                data = json.load(f)
                return data
        else:
            logger.warning(f"Flow configs file not found: {FLOW_CONFIGS_FILE}")
            return {}
    except Exception as e:
        logger.error(f"Error loading flow configs: {e}")
        return {}

def load_old_flow_instances() -> Dict[str, Any]:
    """Load old flow instances from file."""
    try:
        if os.path.exists(FLOW_INSTANCES_FILE):
            with open(FLOW_INSTANCES_FILE, 'r') as f:
                data = json.load(f)
                return data
        else:
            logger.warning(f"Flow instances file not found: {FLOW_INSTANCES_FILE}")
            return {}
    except Exception as e:
        logger.error(f"Error loading flow instances: {e}")
        return {}

def load_old_messages() -> Dict[str, List[Dict[str, Any]]]:
    """Load old messages from file."""
    try:
        if os.path.exists(MESSAGES_FILE):
            with open(MESSAGES_FILE, 'r') as f:
                data = json.load(f)
                return data
        else:
            logger.warning(f"Messages file not found: {MESSAGES_FILE}")
            return {}
    except Exception as e:
        logger.error(f"Error loading messages: {e}")
        return {}

def create_flow_definition_from_template(template: Dict[str, Any], config: Dict[str, Any]) -> FlowDefinition:
    """
    Create a flow definition from an old flow template and config.
    
    Args:
        template: The old flow template
        config: The old flow configuration
        
    Returns:
        The new flow definition
    """
    # Create a unique ID for the flow definition
    definition_id = str(uuid.uuid4())
    
    # Create nodes for the flow definition
    nodes = {
        "input_superego": NodeConfig(
            type=AgentType.INPUT_SUPEREGO,
            config={
                "constitution": config.get("constitution_id", "default")
            }
        ),
        "assistant": NodeConfig(
            type=AgentType.GENERAL_ASSISTANT,
            config={
                "system_prompt": "You are a helpful AI assistant.",
                "sysprompt_id": config.get("sysprompt_id", "assistant_default")
            }
        )
    }
    
    # Create edges for the flow definition
    edges = [
        EdgeConfig(from_node=START_NODE, to_node="input_superego"),
        EdgeConfig(from_node="input_superego", to_node="assistant", condition="ALLOW"),
        EdgeConfig(from_node="input_superego", to_node=END_NODE, condition="BLOCK"),
        EdgeConfig(from_node="assistant", to_node=END_NODE)
    ]
    
    # Create the flow definition
    definition = FlowDefinition(
        id=definition_id,
        name=template.get("name", "Migrated Flow"),
        description=template.get("description", "Migrated from old flow template"),
        nodes=nodes,
        edges=edges
    )
    
    return definition

def create_flow_instance_from_old(
    old_instance: Dict[str, Any], 
    definition_id: str,
    messages: List[Dict[str, Any]]
) -> FlowInstance:
    """
    Create a flow instance from an old flow instance.
    
    Args:
        old_instance: The old flow instance
        definition_id: ID of the new flow definition
        messages: Messages for this instance
        
    Returns:
        The new flow instance
    """
    # Parse messages
    parsed_messages = [Message.parse_obj(msg) for msg in messages]
    
    # Create the flow instance
    instance = FlowInstance(
        id=old_instance.get("id", str(uuid.uuid4())),
        flow_definition_id=definition_id,
        name=old_instance.get("name", "Migrated Instance"),
        description=old_instance.get("description"),
        messages=parsed_messages,
        status=FlowStatus.COMPLETED if parsed_messages else FlowStatus.CREATED,
        created_at=old_instance.get("created_at", datetime.now().isoformat()),
        updated_at=old_instance.get("updated_at", datetime.now().isoformat()),
        last_message_at=old_instance.get("last_message_at")
    )
    
    return instance

def migrate_data():
    """Migrate data from the old format to the new format."""
    logger.info("Starting data migration...")
    
    # Get the flow engine
    flow_engine = get_flow_engine()
    
    # Load old data
    old_templates = load_old_flow_templates()
    old_configs = load_old_flow_configs()
    old_instances = load_old_flow_instances()
    old_messages = load_old_messages()
    
    logger.info(f"Loaded {len(old_templates)} templates, {len(old_configs)} configs, {len(old_instances)} instances, and {len(old_messages)} message stores")
    
    # Create flow definitions from templates
    template_to_definition = {}
    for template_id, template in old_templates.items():
        # Get the config for this template
        config_id = template.get("config", {}).get("id")
        if not config_id or config_id not in old_configs:
            logger.warning(f"Config not found for template {template_id}")
            continue
        
        config = old_configs[config_id]
        
        # Create a flow definition
        definition = create_flow_definition_from_template(template, config)
        
        # Store the definition
        flow_engine.create_flow_definition(definition)
        
        # Remember the mapping from template to definition
        template_to_definition[template_id] = definition.id
        
        logger.info(f"Created flow definition {definition.id} from template {template_id}")
    
    # Create flow instances from old instances
    for instance_id, old_instance in old_instances.items():
        # Get the template for this instance
        template_id = old_instance.get("flow_template_id")
        if not template_id or template_id not in template_to_definition:
            logger.warning(f"Template not found for instance {instance_id}")
            continue
        
        # Get the definition ID
        definition_id = template_to_definition[template_id]
        
        # Get the messages for this instance
        message_store_id = old_instance.get("message_store_id")
        messages = old_messages.get(message_store_id, []) if message_store_id else []
        
        # Create a flow instance
        instance = create_flow_instance_from_old(old_instance, definition_id, messages)
        
        # Store the instance
        flow_engine.flow_instances[instance.id] = instance
        
        logger.info(f"Created flow instance {instance.id} from old instance {instance_id} with {len(messages)} messages")
    
    # Save the flow instances
    flow_engine.save_flow_instances()
    
    logger.info("Data migration completed successfully")

if __name__ == "__main__":
    migrate_data()
