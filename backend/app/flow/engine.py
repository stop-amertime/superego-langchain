#!/usr/bin/env python
"""
Core flow engine module for Superego Agent System.
Provides a unified interface for managing flow state and execution.
"""
from typing import Dict, List, Optional, Any, AsyncGenerator
import uuid
from datetime import datetime
import asyncio
import json
import os
import pathlib

from app.flow.builder import build_flow
from app.flow.executor import execute_flow
from app.flow.loader import load_flow, embed_constitutions, get_constitutions_map
from app.models import FlowStep, StreamChunk


class FlowEngine:
    """Minimalist flow orchestration engine. Provides a unified interface for 
    creating, executing, and managing flows without unnecessary abstractions.
    """
    
    def __init__(self):
        """Initialize the flow engine with empty registries."""
        self.flow_definitions = {}
        self.active_flows = {}
        self.constitutions = {}
        
        # Path for storing flow instances
        self.instances_dir = pathlib.Path("app/data/flow_instances")
        # Ensure directory exists
        self.instances_dir.mkdir(parents=True, exist_ok=True)
    
    async def load_constitutions(self, directory: str) -> None:
        """Load constitutions from directory."""
        self.constitutions = await get_constitutions_map(directory)
    
    async def load_flow_definitions(self, directory: str) -> List[str]:
        """Load flow definitions from directory."""
        from pathlib import Path
        
        flow_ids = []
        for file_path in Path(directory).glob("*.json"):
            flow_def = await load_flow(str(file_path))
            
            # Embed constitutions
            flow_def = await embed_constitutions(flow_def, self.constitutions)
            
            # Store with ID
            flow_id = flow_def.get("id", file_path.stem)
            self.flow_definitions[flow_id] = flow_def
            flow_ids.append(flow_id)
            
        return flow_ids
        
    async def load_flow_instances(self) -> None:
        """Load all flow instances from the instances directory."""
        # Clear current instances
        self.active_flows = {}
        
        # Load from files without rebuilding graphs - we'll build them on demand
        for file_path in self.instances_dir.glob("*.json"):
            try:
                with open(file_path, "r") as f:
                    instance_data = json.load(f)
                    
                # Extract instance ID from filename
                instance_id = file_path.stem
                
                # Get flow definition from the instance data
                flow_def = instance_data.get("definition")
                if not flow_def:
                    print(f"Warning: Flow instance {instance_id} is missing flow definition, skipping.")
                    continue
                
                # Don't rebuild the flow graph now - we'll do it on demand when needed
                # This prevents excessive rebuilding at startup
                instance_data["graph"] = None  # Will be built when needed
                
                # Store in memory
                self.active_flows[instance_id] = instance_data
            except Exception as e:
                # Log error but continue loading other instances
                print(f"Error loading flow instance {file_path}: {e}")
                
    def save_flow_instance(self, instance_id: str) -> None:
        """Save a flow instance to disk.
        
        Args:
            instance_id: ID of the flow instance to save
            
        Raises:
            ValueError: If the instance is not found
        """
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
            
        # Get instance data
        instance_data = self.active_flows[instance_id]
        
        # Create a JSON-serializable copy
        serializable_data = {}
        for key, value in instance_data.items():
            # Skip the graph object which may contain unserializable elements
            if key == "graph":
                continue
            serializable_data[key] = value
            
        # Save to file
        file_path = self.instances_dir / f"{instance_id}.json"
        with open(file_path, "w") as f:
            json.dump(serializable_data, f, indent=2)
    
    async def create_flow(self, flow_id: str, llm: Any) -> str:
        if flow_id not in self.flow_definitions:
            raise ValueError(f"Flow definition {flow_id} not found")
        
        instance_id = str(uuid.uuid4())
        flow_def = self.flow_definitions[flow_id]
        
        # Properly await the async build_flow function
        flow_graph = await build_flow(flow_def, llm)
        
        self.active_flows[instance_id] = {
            "graph": flow_graph,
            "definition": flow_def,
            "history": [],
            "tool_confirmation_settings": {"confirm_all": True, "exempted_tools": []},
            "pending_tool_executions": {},
            "created_at": datetime.now().isoformat()
        }
        
        self.save_flow_instance(instance_id)
        return instance_id
    
    async def execute(self, instance_id: str, input_message: str) -> AsyncGenerator[Dict, None]:
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
        
        flow_data = self.active_flows[instance_id]
        flow_graph = flow_data["graph"]
        
        # Build flow graph on demand if it doesn't exist
        if flow_graph is None:
            import logging
            logger = logging.getLogger("uvicorn")
            logger.info(f"Building flow graph on demand for instance {instance_id}")
            
            # Get OpenRouter API key and model from .env
            api_key = os.environ.get("OPENROUTER_API_KEY")
            base_model = os.environ.get("BASE_MODEL", "anthropic/claude-3.5-sonnet")
            
            if not api_key:
                raise ValueError("OPENROUTER_API_KEY not found in environment")
            
            # Configure LLM for OpenRouter
            from langchain_openai import ChatOpenAI
            llm = ChatOpenAI(
                temperature=0,
                model=base_model,
                openai_api_key=api_key,
                openai_api_base="https://openrouter.ai/api/v1"
            )
            
            # Build flow graph
            flow_def = flow_data["definition"]
            flow_graph = await build_flow(flow_def, llm)
            
            # Update instance data with the new graph
            flow_data["graph"] = flow_graph
        
        user_step = {
            "step_id": str(uuid.uuid4()),
            "agent_id": "user",
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "input": None,
            "response": input_message,
            "next_agent": flow_data["definition"]["graph"]["start"],
            "instance_id": instance_id  # Add instance_id to user_step
        }
        
        flow_data["history"].append(user_step)
        self.save_flow_instance(instance_id)
        
        # Create a flow_def with instance_id to pass to execute_flow
        flow_def = flow_data["definition"].copy()
        flow_def["instance_id"] = instance_id
        
        async for step in execute_flow(flow_graph, input_message, flow_def):
            if step.get("complete", False) and "flow_step" in step:
                flow_data["history"].append(step["flow_step"])
                self.save_flow_instance(instance_id)
            
            yield step
    
    def get_flow_history(self, instance_id: str) -> List[Dict]:
        """Get the history of a flow instance."""
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
        
        return self.active_flows[instance_id]["history"]
    
    def get_flow_definition(self, flow_id: str) -> Dict:
        """Get a flow definition by ID."""
        if flow_id not in self.flow_definitions:
            raise ValueError(f"Flow definition {flow_id} not found")
        
        return self.flow_definitions[flow_id]
    
    def get_available_flows(self) -> List[Dict]:
        """Get a list of available flow definitions."""
        return [
            {
                "id": flow_id,
                "name": flow_def.get("name", "Unnamed Flow"),
                "description": flow_def.get("description", "")
            }
            for flow_id, flow_def in self.flow_definitions.items()
        ]
        
    async def execute_pending_tool(self, instance_id: str, tool_execution_id: str) -> Dict:
        if instance_id not in self.active_flows:
            raise ValueError(f"Flow instance {instance_id} not found")
            
        flow_instance = self.active_flows[instance_id]
        
        if tool_execution_id not in flow_instance["pending_tool_executions"]:
            raise ValueError(f"Tool execution {tool_execution_id} not found")
            
        pending_execution = flow_instance["pending_tool_executions"][tool_execution_id]
        tool_name = pending_execution["tool_name"]
        tool_input = pending_execution["tool_input"]
        
        from ..agents.inner_agent import execute_tool
        from ..tools.calculator import register_tools
        available_tools = register_tools()
        
        result = await execute_tool(tool_name, tool_input, available_tools)
        pending_execution["result"] = result
        
        del flow_instance["pending_tool_executions"][tool_execution_id]
        self.save_flow_instance(instance_id)
        
        return {
            "tool_name": tool_name,
            "input": tool_input,
            "result": result
        }


# Singleton instance for global access
# This avoids unnecessary class instantiation while maintaining a clear API
flow_engine = FlowEngine()


async def initialize_engine(constitutions_dir: str, flow_defs_dir: str) -> FlowEngine:
    """Initialize the flow engine with constitutions and flow definitions."""
    # Load environment variables first to ensure they're available
    from dotenv import load_dotenv
    import os
    
    # Get the absolute path to the .env file
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env")
    print(f"Loading environment from: {env_path}")
    load_dotenv(dotenv_path=env_path)
    
    # Now initialize the engine components
    await flow_engine.load_constitutions(constitutions_dir)
    await flow_engine.load_flow_definitions(flow_defs_dir)
    # Load existing flow instances
    await flow_engine.load_flow_instances()
    return flow_engine
