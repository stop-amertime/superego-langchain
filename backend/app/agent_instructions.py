import os
import logging
from typing import Dict, Any, Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to agent instructions directory
INSTRUCTIONS_DIR = os.path.join(os.path.dirname(__file__), "data", "agent_instructions")

def load_instructions(agent_type: str) -> str:
    """
    Load instructions for a specific agent type from a markdown file
    
    Args:
        agent_type: The type of agent (e.g., "input_superego")
        
    Returns:
        The instructions content as a string
    """
    file_path = os.path.join(INSTRUCTIONS_DIR, f"{agent_type}.md")
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
            logger.info(f"Loaded instructions for {agent_type} agent")
            return content
    except FileNotFoundError:
        logger.warning(f"Instructions file for {agent_type} not found: {file_path}")
        return f"You are a {agent_type.replace('_', ' ')} agent."
    except Exception as e:
        logger.error(f"Error loading instructions for {agent_type}: {e}")
        return f"You are a {agent_type.replace('_', ' ')} agent."

def get_all_instructions() -> Dict[str, str]:
    """
    Get all available agent instructions
    
    Returns:
        A dictionary mapping agent types to their instructions
    """
    instructions = {}
    
    # Create directory if it doesn't exist
    os.makedirs(INSTRUCTIONS_DIR, exist_ok=True)
    
    # Load all markdown files in the directory
    for filename in os.listdir(INSTRUCTIONS_DIR):
        if filename.endswith(".md"):
            agent_type = filename[:-3]  # Remove .md extension
            instructions[agent_type] = load_instructions(agent_type)
    
    return instructions
