"""
Flow Loader for Superego Agent System

Load flow definitions from files or directories and validate them.
Focuses on efficient, minimal implementation.
"""

import os
import json
from typing import Dict, Any, List, Optional
from pathlib import Path


async def load_flow(path: str) -> Dict[str, Any]:
    """Load a flow definition from a file
    
    Args:
        path: Path to the flow definition JSON file
        
    Returns:
        Flow definition as a dictionary
    
    Raises:
        FileNotFoundError: If the file doesn't exist
        JSONDecodeError: If the file isn't valid JSON
    """
    with open(path, 'r') as f:
        flow_def = json.load(f)
    
    # Validate minimal required structure
    if not _validate_flow_definition(flow_def):
        raise ValueError(f"Invalid flow definition in {path}")
        
    return flow_def


async def load_flows_from_directory(directory: str) -> List[Dict[str, Any]]:
    """Load all flow definitions from a directory
    
    Args:
        directory: Path to directory containing flow definition JSON files
        
    Returns:
        List of flow definitions
    """
    flows = []
    directory_path = Path(directory)
    
    # Ensure directory exists
    if not directory_path.exists() or not directory_path.is_dir():
        return []
    
    # Load all JSON files
    for file_path in directory_path.glob("*.json"):
        try:
            flow = await load_flow(str(file_path))
            # Add file path for reference
            flow["file_path"] = str(file_path)
            flows.append(flow)
        except (ValueError, json.JSONDecodeError) as e:
            # Skip invalid files but don't crash
            continue
    
    return flows


def _validate_flow_definition(flow_def: Dict[str, Any]) -> bool:
    """Validate a flow definition has the required structure
    
    Args:
        flow_def: Flow definition to validate
        
    Returns:
        True if valid, False otherwise
    """
    # Check required top-level keys
    if not all(key in flow_def for key in ["name", "graph"]):
        return False
    
    # Check graph structure
    graph = flow_def.get("graph", {})
    if not all(key in graph for key in ["start", "nodes"]):
        return False
    
    # Check that start node exists in nodes
    start_node = graph.get("start")
    nodes = graph.get("nodes", {})
    if start_node not in nodes:
        return False
    
    # Check each node has a type and transitions
    for node_name, node in nodes.items():
        if "type" not in node or "transitions" not in node:
            return False
        
        # Validate node type
        if node.get("type") not in ["superego", "inner_agent"]:
            return False
            
        # Check specific fields based on type
        if node.get("type") == "superego" and "constitution" not in node:
            return False
        if node.get("type") == "inner_agent" and "system_prompt" not in node:
            return False
    
    return True


async def get_constitutions_map(directory: str) -> Dict[str, str]:
    """Load all constitution files from a directory
    
    Args:
        directory: Path to directory containing constitution markdown files
        
    Returns:
        Dictionary mapping constitution names to their content
    """
    constitutions = {}
    directory_path = Path(directory)
    
    # Ensure directory exists
    if not directory_path.exists() or not directory_path.is_dir():
        return {}
    
    # Load all markdown files
    for file_path in directory_path.glob("*.md"):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Use filename without extension as the constitution name
            name = file_path.stem
            constitutions[name] = content
        except Exception:
            # Skip files with errors
            continue
    
    return constitutions


async def embed_constitutions(
    flow_def: Dict[str, Any], 
    constitutions: Dict[str, str]
) -> Dict[str, Any]:
    """Embed constitution content into a flow definition
    
    Args:
        flow_def: Flow definition to update
        constitutions: Map of constitution names to their content
        
    Returns:
        Updated flow definition with embedded constitutions
    """
    # Create a deep copy to avoid modifying the original
    updated_flow = json.loads(json.dumps(flow_def))
    
    # Process all nodes
    for node_name, node in updated_flow.get("graph", {}).get("nodes", {}).items():
        if node.get("type") == "superego":
            # Check if node references a constitution by name
            constitution_name = node.get("constitution")
            if constitution_name in constitutions:
                # Replace name with actual content
                node["constitution"] = constitutions[constitution_name]
    
    return updated_flow
