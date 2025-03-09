"""
Flow engine for the multi-agent system.

This module provides the central component for managing flow execution,
routing between agents, and handling state persistence.
"""

import json
import os
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, AsyncGenerator, Union, TypeVar, Generic
from datetime import datetime
from pydantic import BaseModel

from langgraph.graph import StateGraph, END
from langgraph.types import Command

from .models import (
    FlowDefinition, 
    FlowInstance, 
    FlowStatus, 
    NodeConfig, 
    EdgeConfig, 
    Message, 
    MessageRole, 
    NodeExecution,
    ToolUsage,
    SuperegoEvaluation,
    SuperegoDecision
)
from .agents import AgentFactory, BaseAgent, AgentType

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Directory paths for flow data
FLOW_DEFINITIONS_DIR = os.path.join(os.path.dirname(__file__), "data", "flow_definitions")
FLOW_INSTANCES_DIR = os.path.join(os.path.dirname(__file__), "data", "flow_instances")

# Special node names
START_NODE = "START"
END_NODE = "END"

class FlowEngine:
    """
    Central component for managing flow execution, routing between agents,
    and handling state persistence.
    """
    
    def __init__(self):
        """Initialize the flow engine."""
        self.flow_definitions: Dict[str, FlowDefinition] = {}
        self.flow_instances: Dict[str, FlowInstance] = {}
        self.graphs: Dict[str, StateGraph] = {}
        self.agents: Dict[str, Dict[str, BaseAgent]] = {}
        
        # Ensure data directories exist
        os.makedirs(FLOW_DEFINITIONS_DIR, exist_ok=True)
        os.makedirs(FLOW_INSTANCES_DIR, exist_ok=True)
        
        # Load flow definitions and instances
        self.load_flow_definitions()
        self.load_flow_instances()
        
        logger.info(f"Initialized FlowEngine with {len(self.flow_definitions)} definitions and {len(self.flow_instances)} instances")
    
    def load_flow_definitions(self) -> None:
        """Load flow definitions from individual files."""
        try:
            # Ensure the directory exists
            os.makedirs(FLOW_DEFINITIONS_DIR, exist_ok=True)
            
            # Clear existing definitions
            self.flow_definitions = {}
            
            # Load each definition file
            for filename in os.listdir(FLOW_DEFINITIONS_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(FLOW_DEFINITIONS_DIR, filename)
                    try:
                        with open(file_path, 'r') as f:
                            definition_data = json.load(f)
                            definition = FlowDefinition.parse_obj(definition_data)
                            self.flow_definitions[definition.id] = definition
                    except Exception as e:
                        logger.error(f"Error loading flow definition from {file_path}: {e}")
            
            logger.info(f"Loaded {len(self.flow_definitions)} flow definitions from directory")
            
            # If no definitions were loaded, create a default one
            if not self.flow_definitions:
                self.create_default_flow_definition()
                
        except Exception as e:
            logger.error(f"Error loading flow definitions: {e}")
            # Ensure the directory exists
            os.makedirs(FLOW_DEFINITIONS_DIR, exist_ok=True)
    
    def save_flow_definition(self, definition: FlowDefinition) -> None:
        """
        Save a single flow definition to file.
        
        Args:
            definition: The flow definition to save
        """
        try:
            # Ensure the directory exists
            os.makedirs(FLOW_DEFINITIONS_DIR, exist_ok=True)
            
            # Save the definition to a file named after its ID
            file_path = os.path.join(FLOW_DEFINITIONS_DIR, f"{definition.id}.json")
            with open(file_path, 'w') as f:
                json.dump(definition.dict(), f, indent=2)
            
            logger.info(f"Saved flow definition {definition.id} to file")
        except Exception as e:
            logger.error(f"Error saving flow definition {definition.id}: {e}")
    
    def save_flow_definitions(self) -> None:
        """Save all flow definitions to individual files."""
        for definition in self.flow_definitions.values():
            self.save_flow_definition(definition)
    
    def load_flow_instances(self) -> None:
        """Load flow instances from individual files."""
        try:
            # Ensure the directory exists
            os.makedirs(FLOW_INSTANCES_DIR, exist_ok=True)
            
            # Clear existing instances
            self.flow_instances = {}
            
            # Load each instance file
            for filename in os.listdir(FLOW_INSTANCES_DIR):
                if filename.endswith('.json'):
                    file_path = os.path.join(FLOW_INSTANCES_DIR, filename)
                    try:
                        with open(file_path, 'r') as f:
                            instance_data = json.load(f)
                            instance = FlowInstance.parse_obj(instance_data)
                            self.flow_instances[instance.id] = instance
                    except Exception as e:
                        logger.error(f"Error loading flow instance from {file_path}: {e}")
            
            logger.info(f"Loaded {len(self.flow_instances)} flow instances from directory")
        except Exception as e:
            logger.error(f"Error loading flow instances: {e}")
            # Ensure the directory exists
            os.makedirs(FLOW_INSTANCES_DIR, exist_ok=True)
    
    def save_flow_instance(self, instance: FlowInstance) -> None:
        """
        Save a single flow instance to file.
        
        Args:
            instance: The flow instance to save
        """
        try:
            # Ensure the directory exists
            os.makedirs(FLOW_INSTANCES_DIR, exist_ok=True)
            
            # Save the instance to a file named after its ID
            file_path = os.path.join(FLOW_INSTANCES_DIR, f"{instance.id}.json")
            with open(file_path, 'w') as f:
                json.dump(instance.dict(), f, indent=2)
            
            logger.info(f"Saved flow instance {instance.id} to file")
        except Exception as e:
            logger.error(f"Error saving flow instance {instance.id}: {e}")
    
    def save_flow_instances(self) -> None:
        """Save all flow instances to individual files."""
        for instance in self.flow_instances.values():
            self.save_flow_instance(instance)
    
    def get_flow_definition(self, definition_id: str) -> Optional[FlowDefinition]:
        """
        Get a flow definition by ID.
        
        Args:
            definition_id: ID of the flow definition
            
        Returns:
            The flow definition, or None if not found
        """
        return self.flow_definitions.get(definition_id)
    
    def get_flow_instance(self, instance_id: str) -> Optional[FlowInstance]:
        """
        Get a flow instance by ID.
        
        Args:
            instance_id: ID of the flow instance
            
        Returns:
            The flow instance, or None if not found
        """
        return self.flow_instances.get(instance_id)
    
    def create_flow_definition(self, definition: FlowDefinition) -> FlowDefinition:
        """
        Create a new flow definition.
        
        Args:
            definition: The flow definition to create
            
        Returns:
            The created flow definition
        """
        # Ensure the definition has an ID
        if not definition.id:
            definition.id = str(uuid.uuid4())
        
        # Store the definition
        self.flow_definitions[definition.id] = definition
        
        # Save to file
        self.save_flow_definitions()
        
        logger.info(f"Created flow definition: {definition.id}")
        return definition
    
    def create_flow_instance(
        self, 
        definition_id: str, 
        name: str, 
        description: Optional[str] = None,
        parameters: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[FlowInstance]:
        """
        Create a new flow instance from a definition.
        
        Args:
            definition_id: ID of the flow definition
            name: Name for the flow instance
            description: Optional description for the flow instance
            parameters: Optional parameters to override node configurations
            
        Returns:
            The created flow instance, or None if the definition is not found
        """
        # Get the flow definition
        definition = self.get_flow_definition(definition_id)
        if not definition:
            logger.error(f"Flow definition not found: {definition_id}")
            return None
        
        # Create the flow instance
        instance_id = str(uuid.uuid4())
        instance = FlowInstance(
            id=instance_id,
            flow_definition_id=definition_id,
            name=name,
            description=description,
            parameters=parameters or {},
            status=FlowStatus.CREATED
        )
        
        # Store the instance
        self.flow_instances[instance_id] = instance
        
        # Save to file
        self.save_flow_instances()
        
        logger.info(f"Created flow instance: {instance_id}")
        return instance
    
    def update_flow_instance(self, instance: FlowInstance) -> None:
        """
        Update a flow instance.
        
        Args:
            instance: The updated flow instance
        """
        # Update the instance
        self.flow_instances[instance.id] = instance
        
        # Update the timestamp
        instance.updated_at = datetime.now().isoformat()
        
        # Save to file
        self.save_flow_instances()
        
        logger.info(f"Updated flow instance: {instance.id}")
    
    def delete_flow_instance(self, instance_id: str) -> bool:
        """
        Delete a flow instance.
        
        Args:
            instance_id: ID of the flow instance to delete
            
        Returns:
            True if the instance was deleted, False otherwise
        """
        if instance_id in self.flow_instances:
            del self.flow_instances[instance_id]
            self.save_flow_instances()
            logger.info(f"Deleted flow instance: {instance_id}")
            return True
        
        logger.warning(f"Flow instance not found for deletion: {instance_id}")
        return False
    
    def build_graph(self, definition: FlowDefinition) -> StateGraph:
        """
        Build a LangGraph StateGraph from a flow definition.
        
        Args:
            definition: The flow definition
            
        Returns:
            The built StateGraph
        """
        # Create a new StateGraph
        builder = StateGraph(Dict)
        
        # Add nodes
        for node_id, node_config in definition.nodes.items():
            # Create a node function that will call the appropriate agent
            node_func = self._create_node_function(node_id, node_config)
            builder.add_node(node_id, node_func)
        
        # Add edges
        for edge in definition.edges:
            if edge.from_node == START_NODE:
                builder.set_entry_point(edge.to_node)
            elif edge.to_node == END_NODE:
                builder.add_edge(edge.from_node, END)
            else:
                if edge.condition:
                    # Add conditional edge
                    builder.add_conditional_edges(
                        edge.from_node,
                        self._create_condition_function(edge.condition),
                        {
                            True: edge.to_node,
                            False: END
                        }
                    )
                else:
                    # Add normal edge
                    builder.add_edge(edge.from_node, edge.to_node)
        
        # Compile the graph
        return builder.compile()
    
    def _create_node_function(self, node_id: str, node_config: NodeConfig):
        """
        Create a node function for a LangGraph StateGraph.
        
        Args:
            node_id: ID of the node
            node_config: Configuration for the node
            
        Returns:
            A function that can be used as a node in a LangGraph StateGraph
        """
        async def node_function(state: Dict[str, Any]) -> Union[Dict[str, Any], Command]:
            """
            Node function for a LangGraph StateGraph.
            
            Args:
                state: The current state of the graph
                
            Returns:
                Updated state or a Command object
            """
            # Get the flow instance
            instance_id = state.get("instance_id")
            instance = self.get_flow_instance(instance_id)
            if not instance:
                logger.error(f"Flow instance not found: {instance_id}")
                return Command(goto=END, update={"error": f"Flow instance not found: {instance_id}"})
            
            # Update the instance with the current node
            instance.current_node = node_id
            instance.status = FlowStatus.RUNNING
            self.update_flow_instance(instance)
            
            # Get the agent for this node
            agent = self._get_agent_for_node(instance, node_id, node_config)
            if not agent:
                logger.error(f"Agent not found for node: {node_id}")
                return Command(goto=END, update={"error": f"Agent not found for node: {node_id}"})
            
            try:
                # Get the input for the agent
                input_text = state.get("user_input", "")
                
                # Get the context for the agent
                context = {
                    "instance_id": instance_id,
                    "node_id": node_id,
                    "messages": instance.messages,
                    "agent_state": instance.agent_states.get(node_id, {}),
                    "parameters": instance.parameters.get(node_id, {})
                }
                
                # Process the input with the agent
                output = await agent.process(input_text, context)
                
                # Record the node execution
                node_execution = NodeExecution(
                    node_id=node_id,
                    input=input_text,
                    output=output
                )
                instance.history.append(node_execution)
                
                # Update the instance
                self.update_flow_instance(instance)
                
                # Check if the output is a Command object
                if isinstance(output, dict) and "goto" in output:
                    # Convert to a Command object
                    return Command(
                        goto=output["goto"],
                        update=output.get("update", {})
                    )
                
                # Return the updated state
                return {
                    **state,
                    "output": output,
                    "last_node": node_id
                }
                
            except Exception as e:
                logger.error(f"Error in node {node_id}: {e}")
                instance.status = FlowStatus.ERROR
                self.update_flow_instance(instance)
                return Command(goto=END, update={"error": str(e)})
        
        return node_function
    
    def _create_condition_function(self, condition: str):
        """
        Create a condition function for a LangGraph StateGraph.
        
        Args:
            condition: The condition expression
            
        Returns:
            A function that evaluates the condition
        """
        def condition_function(state: Dict[str, Any]) -> bool:
            """
            Condition function for a LangGraph StateGraph.
            
            Args:
                state: The current state of the graph
                
            Returns:
                True if the condition is met, False otherwise
            """
            try:
                # Simple conditions for now
                if condition == "ALLOW":
                    # Check if the superego decision is ALLOW
                    superego_evaluation = state.get("superego_evaluation")
                    if superego_evaluation and superego_evaluation.decision == SuperegoDecision.ALLOW:
                        return True
                elif condition == "BLOCK":
                    # Check if the superego decision is BLOCK
                    superego_evaluation = state.get("superego_evaluation")
                    if superego_evaluation and superego_evaluation.decision == SuperegoDecision.BLOCK:
                        return True
                elif condition == "CAUTION":
                    # Check if the superego decision is CAUTION
                    superego_evaluation = state.get("superego_evaluation")
                    if superego_evaluation and superego_evaluation.decision == SuperegoDecision.CAUTION:
                        return True
                
                # Default to False
                return False
                
            except Exception as e:
                logger.error(f"Error evaluating condition {condition}: {e}")
                return False
        
        return condition_function
    
    def _get_agent_for_node(
        self, 
        instance: FlowInstance, 
        node_id: str, 
        node_config: NodeConfig
    ) -> Optional[BaseAgent]:
        """
        Get the agent for a node.
        
        Args:
            instance: The flow instance
            node_id: ID of the node
            node_config: Configuration for the node
            
        Returns:
            The agent for the node, or None if not found
        """
        # Check if we already have an agent for this node in this instance
        if instance.id in self.agents and node_id in self.agents[instance.id]:
            return self.agents[instance.id][node_id]
        
        # Create a new agent
        try:
            # Get the agent type
            agent_type = node_config.type
            
            # Get the agent configuration
            agent_config = node_config.config.copy()
            
            # Apply any instance-specific parameters
            if node_id in instance.parameters:
                agent_config.update(instance.parameters[node_id])
            
            # Create the agent
            agent = AgentFactory.create(agent_type, agent_config)
            
            # Store the agent
            if instance.id not in self.agents:
                self.agents[instance.id] = {}
            self.agents[instance.id][node_id] = agent
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating agent for node {node_id}: {e}")
            return None
    
    async def process_user_input(
        self, 
        instance_id: str, 
        user_input: str,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """
        Process user input for a flow instance.
        
        Args:
            instance_id: ID of the flow instance
            user_input: The user input to process
            on_token: Optional callback for tokens
            on_thinking: Optional callback for thinking
            
        Returns:
            The result of processing the input
        """
        # Get the flow instance
        instance = self.get_flow_instance(instance_id)
        if not instance:
            logger.error(f"Flow instance not found: {instance_id}")
            return {"error": f"Flow instance not found: {instance_id}"}
        
        # Get the flow definition
        definition = self.get_flow_definition(instance.flow_definition_id)
        if not definition:
            logger.error(f"Flow definition not found: {instance.flow_definition_id}")
            return {"error": f"Flow definition not found: {instance.flow_definition_id}"}
        
        # Create a user message
        user_message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=user_input,
            timestamp=datetime.now().isoformat()
        )
        
        # Add the message to the instance
        instance.messages.append(user_message)
        instance.last_message_at = user_message.timestamp
        self.update_flow_instance(instance)
        
        # Get or build the graph
        if definition.id not in self.graphs:
            self.graphs[definition.id] = self.build_graph(definition)
        graph = self.graphs[definition.id]
        
        # Set up the initial state
        state = {
            "instance_id": instance_id,
            "user_input": user_input,
            "messages": instance.messages,
            "on_token": on_token,
            "on_thinking": on_thinking
        }
        
        try:
            # Run the graph
            instance.status = FlowStatus.RUNNING
            self.update_flow_instance(instance)
            
            result = await graph.ainvoke(state)
            
            # Update the instance status
            if "error" in result:
                instance.status = FlowStatus.ERROR
            else:
                instance.status = FlowStatus.COMPLETED
            
            self.update_flow_instance(instance)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing user input: {e}")
            instance.status = FlowStatus.ERROR
            self.update_flow_instance(instance)
            return {"error": str(e)}
    
    async def stream_user_input(
        self, 
        instance_id: str, 
        user_input: str,
        on_token: Optional[Callable[[str], None]] = None,
        on_thinking: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream the processing of user input for a flow instance.
        
        Args:
            instance_id: ID of the flow instance
            user_input: The user input to process
            on_token: Optional callback for tokens
            on_thinking: Optional callback for thinking
            
        Yields:
            Updates from the processing
        """
        # Get the flow instance
        instance = self.get_flow_instance(instance_id)
        if not instance:
            logger.error(f"Flow instance not found: {instance_id}")
            yield {"error": f"Flow instance not found: {instance_id}"}
            return
        
        # Get the flow definition
        definition = self.get_flow_definition(instance.flow_definition_id)
        if not definition:
            logger.error(f"Flow definition not found: {instance.flow_definition_id}")
            yield {"error": f"Flow definition not found: {instance.flow_definition_id}"}
            return
        
        # Create a user message
        user_message = Message(
            id=str(uuid.uuid4()),
            role=MessageRole.USER,
            content=user_input,
            timestamp=datetime.now().isoformat()
        )
        
        # Add the message to the instance
        instance.messages.append(user_message)
        instance.last_message_at = user_message.timestamp
        self.update_flow_instance(instance)
        
        # Get or build the graph
        if definition.id not in self.graphs:
            self.graphs[definition.id] = self.build_graph(definition)
        graph = self.graphs[definition.id]
        
        # Set up the initial state
        state = {
            "instance_id": instance_id,
            "user_input": user_input,
            "messages": instance.messages,
            "on_token": on_token,
            "on_thinking": on_thinking
        }
        
        try:
            # Run the graph
            instance.status = FlowStatus.RUNNING
            self.update_flow_instance(instance)
            
            # Stream the result
            async for event_type, event_data in graph.astream(state):
                # Yield the event
                yield {
                    "event_type": event_type,
                    "event_data": event_data
                }
                
                # Update the instance based on the event
                if event_type == "node":
                    # Update the current node
                    instance.current_node = event_data
                    self.update_flow_instance(instance)
                elif event_type == "output":
                    # Check for errors
                    if "error" in event_data:
                        instance.status = FlowStatus.ERROR
                        self.update_flow_instance(instance)
            
            # Update the instance status
            instance.status = FlowStatus.COMPLETED
            self.update_flow_instance(instance)
            
        except Exception as e:
            logger.error(f"Error streaming user input: {e}")
            instance.status = FlowStatus.ERROR
            self.update_flow_instance(instance)
            yield {"error": str(e)}
    
    def create_default_flow_definition(self) -> FlowDefinition:
        """
        Create a default flow definition with input superego and assistant.
        
        Returns:
            The created flow definition
        """
        # Create the flow definition
        definition_id = str(uuid.uuid4())
        definition = FlowDefinition(
            id=definition_id,
            name="Default Flow",
            description="Default flow with input superego and assistant",
            nodes={
                "input_superego": NodeConfig(
                    type=AgentType.INPUT_SUPEREGO,
                    config={
                        "constitution": "default"
                    }
                ),
                "assistant": NodeConfig(
                    type=AgentType.GENERAL_ASSISTANT,
                    config={
                        "system_prompt": "You are a helpful AI assistant."
                    }
                )
            },
            edges=[
                EdgeConfig(from_node=START_NODE, to_node="input_superego"),
                EdgeConfig(from_node="input_superego", to_node="assistant", condition="ALLOW"),
                EdgeConfig(from_node="input_superego", to_node=END_NODE, condition="BLOCK"),
                EdgeConfig(from_node="assistant", to_node=END_NODE)
            ]
        )
        
        # Store the definition
        self.flow_definitions[definition_id] = definition
        
        # Save to file
        self.save_flow_definitions()
        
        logger.info(f"Created default flow definition: {definition_id}")
        return definition
    
    def migrate_from_old_format(self) -> None:
        """
        Migrate from the old format to the new format.
        
        This will:
        1. Create flow definitions from flow templates
        2. Update flow instances to use the new format
        3. Migrate messages from the message store to flow instances
        """
        # TODO: Implement migration from old format
        pass

# Singleton instance
_instance = None

def get_flow_engine() -> FlowEngine:
    """
    Get the singleton instance of the flow engine.
    
    Returns:
        The flow engine instance
    """
    global _instance
    if _instance is None:
        _instance = FlowEngine()
    return _instance
