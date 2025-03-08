import logging
import json
import os
from typing import Dict, List, Any, Optional

from .models import SuperegoEvaluation, SuperegoDecision

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path to constitutions file
CONSTITUTIONS_FILE = os.path.join(os.path.dirname(__file__), "data", "constitutions.json")

def load_constitutions():
    """Load constitutions from the JSON file"""
    try:
        with open(CONSTITUTIONS_FILE, 'r') as f:
            data = json.load(f)
            return {constitution["id"]: constitution for constitution in data.get("constitutions", [])}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading constitutions: {e}")
        return {}

# Load all constitutions
ALL_CONSTITUTIONS = load_constitutions()

# Default constitution ID
DEFAULT_CONSTITUTION_ID = "default"

# Get the default constitution content
def get_default_constitution():
    """Get the default constitution content"""
    if DEFAULT_CONSTITUTION_ID in ALL_CONSTITUTIONS:
        return ALL_CONSTITUTIONS[DEFAULT_CONSTITUTION_ID]["content"]
    else:
        # Fallback if default constitution is not found
        logger.warning(f"Default constitution '{DEFAULT_CONSTITUTION_ID}' not found. Using fallback.")
        return """
# Superego Agent Guidelines

As the Superego Agent, your role is to evaluate user requests for safety, ethics, and appropriateness before they are processed by the main assistant. You act as a protective filter that ensures all interactions remain helpful, harmless, and honest.

## Evaluation Process

1. Carefully analyze the user's request for potential harmful intent or outcomes
2. Assess whether the request might:
   - Cause harm to individuals or groups
   - Facilitate illegal activities
   - Generate misleading or false information
   - Violate privacy or confidentiality
   - Create or spread harmful content

## Decision Framework

Based on your evaluation, provide ONE of the following decisions:

- ALLOW: The request is safe and can be processed normally
- CAUTION: The request may have concerning elements but can be processed with careful handling
- BLOCK: The request should not be fulfilled as it poses significant risks

## Reasoning Requirements

For each decision, provide clear reasoning that explains:
- The specific safety concerns identified (if any)
- The potential impacts of fulfilling the request
- For CAUTION or BLOCK decisions, explain exactly what makes the request problematic

Always remain balanced and fair in your evaluations, avoiding unnecessary restrictions while ensuring appropriate safeguards.
"""

# Get all available constitutions
def get_all_constitutions() -> Dict[str, Dict[str, Any]]:
    """Get all available constitutions"""
    return ALL_CONSTITUTIONS

# Save a new constitution
def save_constitution(constitution_id: str, name: str, content: str) -> bool:
    """
    Save a new constitution to the JSON file
    
    Args:
        constitution_id: Unique ID for the constitution
        name: Display name for the constitution
        content: The constitution content
        
    Returns:
        True if saved successfully, False otherwise
    """
    try:
        # Load current constitutions
        constitutions = load_constitutions()
        
        # Add or update the constitution
        constitutions[constitution_id] = {
            "id": constitution_id,
            "name": name,
            "content": content
        }
        
        # Write to file
        with open(CONSTITUTIONS_FILE, 'w') as f:
            json.dump({"constitutions": list(constitutions.values())}, f, indent=2)
        
        # Update global variable
        global ALL_CONSTITUTIONS
        ALL_CONSTITUTIONS = constitutions
        
        logger.info(f"Constitution '{constitution_id}' saved successfully")
        return True
    except Exception as e:
        logger.error(f"Error saving constitution: {e}")
        return False
