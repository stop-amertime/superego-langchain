import json
import uuid
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime

from .models import FlowConfig, FlowTemplate, FlowInstance, ParallelFlowResult, Message, SuperegoEvaluation
from .graph import run_graph

# Set up logging
logger = logging.getLogger(__name__)

# In-memory storage for flow templates, configurations, and instances
# In a production system, this would be stored in a database
flow_templates: Dict[str, FlowTemplate] = {}
flow_configs: Dict[str, FlowConfig] = {}
flow_instances: Dict[str, FlowInstance] = {}

# File paths for persistent storage
FLOW_TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), "data", "flow_templates.json")
FLOW_CONFIGS_FILE = os.path.join(os.path.dirname(__file__), "data", "flow_configs.json")
FLOW_INSTANCES_FILE = os.path.join(os.path.dirname(__file__), "data", "flow_instances.json")

# Ensure the data directory exists
os.makedirs(os.path.dirname(FLOW_TEMPLATES_FILE), exist_ok=True)

# Check if essential files exist and create them if they don't
def ensure_data_files_exist():
    """Ensure that all data files exist with at least empty JSON objects."""
    files = [FLOW_TEMPLATES_FILE, FLOW_CONFIGS_FILE, FLOW_INSTANCES_FILE]
    for file_path in files:
        if not os.path.exists(file_path):
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            # Create an empty JSON file
            with open(file_path, 'w') as f:
                json.dump({}, f)
            logger.info(f"Created empty data file: {file_path}")

def init_default_flow_templates():
    """Initialize default flow templates and instances if none exist."""
    if not flow_templates:
        # Default template with superego enabled
        standard_template_id = str(uuid.uuid4())
        standard_config_id = str(uuid.uuid4())
        standard_config = FlowConfig(
            id=standard_config_id,
            name="Standard Flow",
            constitution_id="default",
            sysprompt_id="assistant_default",
            superego_enabled=True,
            description="Standard flow with superego evaluation"
        )
        standard_template = FlowTemplate(
            id=standard_template_id,
            name="Standard",
            description="Standard flow with superego evaluation",
            config=standard_config,
            is_default=True
        )
        flow_templates[standard_template_id] = standard_template
        flow_configs[standard_config_id] = standard_config

        # Template without superego
        no_superego_template_id = str(uuid.uuid4())
        no_superego_config_id = str(uuid.uuid4())
        no_superego_config = FlowConfig(
            id=no_superego_config_id,
            name="No Superego Flow",
            constitution_id="none",
            sysprompt_id="assistant_default",
            superego_enabled=False,
            description="Flow without superego evaluation"
        )
        no_superego_template = FlowTemplate(
            id=no_superego_template_id,
            name="No Superego",
            description="Flow without superego evaluation",
            config=no_superego_config,
            is_default=False
        )
        flow_templates[no_superego_template_id] = no_superego_template
        flow_configs[no_superego_config_id] = no_superego_config

        # Save to files
        save_flow_templates()
        save_flow_configs()
        
        # Create a default instance based on the standard flow
        default_instance_id = str(uuid.uuid4())
        default_message_store_id = str(uuid.uuid4())
        default_instance = FlowInstance(
            id=default_instance_id,
            flow_config_id=standard_config_id,
            message_store_id=default_message_store_id,
            name="Default Session",
            description="Automatically created default session"
        )
        flow_instances[default_instance_id] = default_instance
        save_flow_instances()
        
        logger.info(f"Created default instance with ID: {default_instance_id}")


def load_flow_templates():
    """Load flow templates from file."""
    global flow_templates
    try:
        if os.path.exists(FLOW_TEMPLATES_FILE):
            with open(FLOW_TEMPLATES_FILE, 'r') as f:
                data = json.load(f)
                flow_templates = {
                    template_id: FlowTemplate.parse_obj(template_data)
                    for template_id, template_data in data.items()
                }
        else:
            init_default_flow_templates()
    except Exception as e:
        logger.error(f"Error loading flow templates: {e}")
        init_default_flow_templates()


def save_flow_templates():
    """Save flow templates to file."""
    try:
        with open(FLOW_TEMPLATES_FILE, 'w') as f:
            data = {
                template_id: template.dict()
                for template_id, template in flow_templates.items()
            }
            json.dump(data, f, indent=2, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o))
    except Exception as e:
        logger.error(f"Error saving flow templates: {e}")


def load_flow_configs():
    """Load flow configurations from file."""
    global flow_configs
    try:
        if os.path.exists(FLOW_CONFIGS_FILE):
            with open(FLOW_CONFIGS_FILE, 'r') as f:
                data = json.load(f)
                flow_configs = {
                    config_id: FlowConfig.parse_obj(config_data)
                    for config_id, config_data in data.items()
                }
    except Exception as e:
        logger.error(f"Error loading flow configs: {e}")


def save_flow_configs():
    """Save flow configurations to file."""
    try:
        with open(FLOW_CONFIGS_FILE, 'w') as f:
            data = {
                config_id: config.dict()
                for config_id, config in flow_configs.items()
            }
            json.dump(data, f, indent=2, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o))
    except Exception as e:
        logger.error(f"Error saving flow configs: {e}")


def load_flow_instances():
    """Load flow instances from file."""
    global flow_instances
    try:
        if os.path.exists(FLOW_INSTANCES_FILE):
            with open(FLOW_INSTANCES_FILE, 'r') as f:
                data = json.load(f)
                flow_instances = {
                    instance_id: FlowInstance.parse_obj(instance_data)
                    for instance_id, instance_data in data.items()
                }
    except Exception as e:
        logger.error(f"Error loading flow instances: {e}")


def save_flow_instances():
    """Save flow instances to file."""
    try:
        with open(FLOW_INSTANCES_FILE, 'w') as f:
            data = {
                instance_id: instance.dict()
                for instance_id, instance in flow_instances.items()
            }
            json.dump(data, f, indent=2, default=lambda o: o.dict() if hasattr(o, 'dict') else str(o))
    except Exception as e:
        logger.error(f"Error saving flow instances: {e}")


def get_all_flow_templates() -> Dict[str, FlowTemplate]:
    """Get all flow templates."""
    if not flow_templates:
        load_flow_templates()
    return flow_templates


def get_all_flow_configs() -> Dict[str, FlowConfig]:
    """Get all flow configurations."""
    if not flow_configs:
        load_flow_configs()
    return flow_configs


def get_all_flow_instances() -> Dict[str, FlowInstance]:
    """Get all flow instances."""
    if not flow_instances:
        load_flow_instances()
    return flow_instances


def get_flow_template(template_id: str) -> Optional[FlowTemplate]:
    """Get a flow template by ID."""
    templates = get_all_flow_templates()
    return templates.get(template_id)


def get_flow_config(config_id: str) -> Optional[FlowConfig]:
    """Get a flow configuration by ID."""
    configs = get_all_flow_configs()
    return configs.get(config_id)


def get_flow_instance(instance_id: str) -> Optional[FlowInstance]:
    """Get a flow instance by ID."""
    instances = get_all_flow_instances()
    return instances.get(instance_id)


def create_flow_template(
    name: str,
    description: str,
    config: FlowConfig,
    is_default: bool = False
) -> FlowTemplate:
    """Create a new flow template."""
    template_id = str(uuid.uuid4())
    template = FlowTemplate(
        id=template_id,
        name=name,
        description=description,
        config=config,
        is_default=is_default
    )
    flow_templates[template_id] = template
    flow_configs[config.id] = config
    save_flow_templates()
    save_flow_configs()
    return template


def create_flow_config(
    name: str,
    constitution_id: str = "default",
    sysprompt_id: Optional[str] = "assistant_default",
    superego_enabled: bool = True,
    description: Optional[str] = None
) -> FlowConfig:
    """Create a new flow configuration."""
    config_id = str(uuid.uuid4())
    config = FlowConfig(
        id=config_id,
        name=name,
        constitution_id=constitution_id,
        sysprompt_id=sysprompt_id,
        superego_enabled=superego_enabled,
        description=description
    )
    flow_configs[config_id] = config
    save_flow_configs()
    return config


def create_flow_instance(
    flow_config_id: str,
    name: str,
    description: Optional[str] = None
) -> FlowInstance:
    """Create a new flow instance."""
    instance_id = str(uuid.uuid4())
    # Use the instance's own ID as the message store ID
    message_store_id = instance_id
    instance = FlowInstance(
        id=instance_id,
        flow_config_id=flow_config_id,
        message_store_id=message_store_id,
        name=name,
        description=description
    )
    flow_instances[instance_id] = instance
    save_flow_instances()
    return instance


def update_flow_template(
    template_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None,
    config: Optional[FlowConfig] = None,
    is_default: Optional[bool] = None
) -> Optional[FlowTemplate]:
    """Update a flow template."""
    template = get_flow_template(template_id)
    if not template:
        return None

    if name is not None:
        template.name = name
    if description is not None:
        template.description = description
    if config is not None:
        template.config = config
        flow_configs[config.id] = config
    if is_default is not None:
        template.is_default = is_default
    
    template.updated_at = datetime.now().isoformat()
    flow_templates[template_id] = template
    save_flow_templates()
    save_flow_configs()
    return template


def update_flow_config(
    config_id: str,
    name: Optional[str] = None,
    constitution_id: Optional[str] = None,
    sysprompt_id: Optional[str] = None,
    superego_enabled: Optional[bool] = None,
    description: Optional[str] = None
) -> Optional[FlowConfig]:
    """Update a flow configuration."""
    config = get_flow_config(config_id)
    if not config:
        return None

    if name is not None:
        config.name = name
    if constitution_id is not None:
        config.constitution_id = constitution_id
    if sysprompt_id is not None:
        config.sysprompt_id = sysprompt_id
    if superego_enabled is not None:
        config.superego_enabled = superego_enabled
    if description is not None:
        config.description = description
    
    config.updated_at = datetime.now().isoformat()
    flow_configs[config_id] = config
    save_flow_configs()
    return config


def update_flow_instance(
    instance_id: str,
    name: Optional[str] = None,
    description: Optional[str] = None
) -> Optional[FlowInstance]:
    """Update a flow instance."""
    instance = get_flow_instance(instance_id)
    if not instance:
        return None

    if name is not None:
        instance.name = name
    if description is not None:
        instance.description = description
    
    instance.updated_at = datetime.now().isoformat()
    flow_instances[instance_id] = instance
    save_flow_instances()
    return instance


def delete_flow_template(template_id: str) -> bool:
    """Delete a flow template."""
    if template_id in flow_templates:
        del flow_templates[template_id]
        save_flow_templates()
        return True
    return False


def delete_flow_config(config_id: str) -> bool:
    """Delete a flow configuration."""
    if config_id in flow_configs:
        # Check if any templates are using this config
        for template in flow_templates.values():
            if template.config.id == config_id:
                return False
        
        del flow_configs[config_id]
        save_flow_configs()
        return True
    return False


def delete_flow_instance(instance_id: str) -> bool:
    """Delete a flow instance."""
    if instance_id in flow_instances:
        del flow_instances[instance_id]
        save_flow_instances()
        return True
    return False

def update_flow_instance_last_message(instance_id: str) -> bool:
    """Update the last_message_at timestamp for a flow instance."""
    instance = get_flow_instance(instance_id)
    if not instance:
        return False
    
    instance.last_message_at = datetime.now().isoformat()
    instance.updated_at = instance.last_message_at
    flow_instances[instance_id] = instance
    save_flow_instances()
    return True


async def run_multiple_flows(
    flow_config_ids: List[str],
    user_input: str,
    conversation_id: Optional[str] = None,
    messages: Optional[List[Message]] = None,
    on_token: Optional[Dict[str, Any]] = None,
    on_thinking: Optional[Dict[str, Any]] = None
) -> List[ParallelFlowResult]:
    """Run multiple flows in parallel with different configurations."""
    results = []
    
    for config_id in flow_config_ids:
        config = get_flow_config(config_id)
        if not config:
            continue
        
        # Run the flow with this configuration
        try:
            # Create a flow instance with this configuration
            flow_config = {
                "constitution_id": config.constitution_id,
                "sysprompt_id": config.sysprompt_id,
                "skip_superego": not config.superego_enabled
            }
            
            from .flow import CommandFlow
            flow = CommandFlow(flow_config)
            
            # Create context for the flow
            flow_context = {
                "conversation_id": conversation_id,
                "messages": messages or [],
                "on_token": on_token.get(config_id) if on_token else None,
                "on_thinking": on_thinking.get(config_id) if on_thinking else None
            }
            
            # Process the input
            flow_result_type, flow_response = await flow.process(user_input, flow_context)
            
            # Get the last messages from the flow context
            # This assumes the flow adds the messages to the context
            updated_messages = flow_context.get("messages", [])
            
            # Extract superego evaluation and assistant message
            superego_evaluation = None
            assistant_message = None
            
            for msg in updated_messages:
                if msg.role == "superego":
                    superego_evaluation = SuperegoEvaluation(
                        decision=SuperegoDecision(msg.decision) if hasattr(msg, "decision") else SuperegoDecision.ALLOW,
                        reason=msg.content,
                        thinking=msg.thinking if hasattr(msg, "thinking") else "",
                        constitutionId=msg.constitutionId if hasattr(msg, "constitutionId") else config.constitution_id
                    )
                elif msg.role == "assistant" and msg.content == flow_response:
                    assistant_message = msg
            
            # If we didn't find the assistant message, create one
            if not assistant_message and flow_result_type == "success":
                assistant_message = Message(
                    id=str(uuid.uuid4()),
                    role=MessageRole.ASSISTANT,
                    content=flow_response,
                    timestamp=datetime.now().isoformat()
                )
            
            # Create result
            result = ParallelFlowResult(
                flow_config_id=config_id,
                flow_name=config.name,
                superego_evaluation=superego_evaluation,
                assistant_message=assistant_message,
                constitution_id=config.constitution_id,
                sysprompt_id=config.sysprompt_id,
                superego_enabled=config.superego_enabled
            )
            
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error running flow {config_id}: {e}")
            # Continue with other flows
    
    return results


# Initialize on module import
# First ensure the data files exist
ensure_data_files_exist()
# Then load the data
load_flow_templates()  # This will also create default templates and instance if needed
load_flow_configs()
load_flow_instances()

# If we still don't have any instances, create a default one
if not flow_instances:
    logger.info("No instances found after initialization, creating a default instance")
    # Find a suitable config
    configs = get_all_flow_configs()
    if configs:
        # Prefer a config with superego enabled, but take any if none have it
        standard_config = next((c for c in configs.values() if c.superego_enabled), 
                               next(iter(configs.values()), None))
        
        if standard_config:
            # Create the default instance
            default_instance_id = str(uuid.uuid4())
            default_message_store_id = str(uuid.uuid4())
            default_instance = FlowInstance(
                id=default_instance_id,
                flow_config_id=standard_config.id,
                message_store_id=default_message_store_id,
                name="Default Session",
                description="Automatically created default session"
            )
            flow_instances[default_instance_id] = default_instance
            save_flow_instances()
            logger.info(f"Created default instance with ID: {default_instance_id}")
