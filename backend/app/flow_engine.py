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
        
        # First, add the entry point
        entry_edges = [edge for edge in definition.edges if edge.from_node == START_NODE]
        if entry_edges:
            builder.set_entry_point(entry_edges[0].to_node)
        else:
            logger.error("No entry point defined in flow definition")
            # Default to first node if no entry point is defined
            if definition.nodes:
                first_node = next(iter(definition.nodes.keys()))
                logger.warning(f"Using {first_node} as default entry point")
                builder.set_entry_point(first_node)
            else:
                logger.error("No nodes defined in flow definition")
                return builder.compile()  # Return an empty graph
        
        # Process conditional edges first
        conditional_edges = {}
        for edge in definition.edges:
            if edge.from_node != START_NODE and edge.condition:
                # Group conditional edges by from_node
                if edge.from_node not in conditional_edges:
                    conditional_edges[edge.from_node] = []
                conditional_edges[edge.from_node].append(edge)
        
        # Add conditional edges
        for from_node, edges in conditional_edges.items():
            # Create a router function that will handle all conditions for this node
            condition_routes = {}
            
            for edge in edges:
                condition_key = edge.condition
                to_node = END if edge.to_node == END_NODE else edge.to_node
                condition_routes[condition_key] = to_node
            
            # Add a default "else" route to END if not specified
            if "default" not in condition_routes and "else" not in condition_routes:
                condition_routes["default"] = END
            
            # Add the conditional router
            builder.add_conditional_edges(
                from_node,
                self._create_multi_condition_router(from_node, condition_routes),
                condition_routes
            )
        
        # Then add all regular non-conditional edges that aren't already handled
        for edge in definition.edges:
            # Skip START node edges (already handled as entry point)
            if edge.from_node == START_NODE:
                continue
            
            # Skip conditional edges (already processed above)
            if edge.condition:
                continue
            
            # Skip nodes that have conditional routing (handled by the router)
            if edge.from_node in conditional_edges:
                continue
            
            # Handle END node special case
            if edge.to_node == END_NODE:
                try:
                    # Different versions of LangGraph handle END differently
                    builder.add_edge(edge.from_node, END)
                except (TypeError, ValueError) as e:
                    logger.warning(f"Could not add edge to END using standard method: {e}")
                    # Alternative method for older LangGraph versions
                    try:
                        builder.add_edge(edge.from_node, "__end__")
                    except Exception as e2:
                        logger.error(f"Could not add edge to END using alternate method: {e2}")
                        # Last resort - try setting the end attribute dynamically
                        try:
                            end_value = getattr(builder, "END", "__end__")
                            builder.add_edge(edge.from_node, end_value)
                        except Exception as e3:
                            logger.error(f"All methods to add END edge failed: {e3}")
            else:
                # Regular edge
                builder.add_edge(edge.from_node, edge.to_node)
        
        # Log the graph structure for debugging
        self._log_graph_structure(definition, conditional_edges)
        
        # Compile the graph
        return builder.compile()
    
    def _log_graph_structure(self, definition: FlowDefinition, conditional_edges: Dict):
        """Log the graph structure for debugging."""
        logger.info(f"Graph structure for flow '{definition.name}':")
        logger.info(f"Nodes: {list(definition.nodes.keys())}")
        
        # Log entry point
        entry_edges = [edge for edge in definition.edges if edge.from_node == START_NODE]
        if entry_edges:
            logger.info(f"Entry point: {entry_edges[0].to_node}")
        else:
            logger.info("No entry point defined")
        
        # Log conditional edges
        if conditional_edges:
            logger.info("Conditional edges:")
            for from_node, edges in conditional_edges.items():
                conditions = [f"{edge.condition} → {edge.to_node}" for edge in edges]
                logger.info(f"  {from_node}: {', '.join(conditions)}")
        
        # Log regular edges
        regular_edges = [edge for edge in definition.edges 
                        if edge.from_node != START_NODE 
                        and not edge.condition 
                        and edge.from_node not in conditional_edges]
        if regular_edges:
            logger.info("Regular edges:")
            for edge in regular_edges:
                to_node = "END" if edge.to_node == END_NODE else edge.to_node
                logger.info(f"  {edge.from_node} → {to_node}")
    
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
                
                # Log important details before node execution
                logger.info(f"EXECUTING NODE {node_id} with input: {input_text}")
                logger.info(f"Agent type: {agent.__class__.__name__}")
                logger.info(f"Token callback present: {state.get('on_token') is not None}")
                logger.info(f"Thinking callback present: {state.get('on_thinking') is not None}")
                
                # Get the context for the agent
                context = {
                    "instance_id": instance_id,
                    "node_id": node_id,
                    "messages": instance.messages,
                    "agent_state": instance.agent_states.get(node_id, {}),
                    "parameters": instance.parameters.get(node_id, {}),
                    # Pass the token and thinking callbacks
                    "on_token": state.get("on_token"),
                    "on_thinking": state.get("on_thinking")
                }
                
                # Process the input with the agent
                logger.info(f"Starting {node_id} agent processing")
                try:
                    output = await agent.process(input_text, context)
                    logger.info(f"Agent {node_id} process() completed successfully")
                except Exception as agent_error:
                    logger.error(f"ERROR in agent {node_id}.process(): {str(agent_error)}")
                    raise
                
                # Log detailed information about the node execution
                logger.info(f"Node {node_id} executed with output: {output}")
                
                # If the output is a dict with a message object, add it to the instance messages
                if isinstance(output, dict) and "message_object" in output:
                    message_obj = output["message_object"]
                    # Add to instance messages if not already there
                    if not any(
                        (hasattr(msg, "id") and msg.id == message_obj.get("id")) or 
                        (isinstance(msg, dict) and msg.get("id") == message_obj.get("id")) 
                        for msg in instance.messages
                    ):
                        instance.messages.append(message_obj)
                    # Use the message as the output for history
                    output_for_history = output.get("message", output)
                else:
                    output_for_history = output
                
                # Record in traditional node execution history (for backward compatibility)
                node_execution = NodeExecution(
                    node_id=node_id,
                    input=input_text,
                    output=output_for_history
                )
                instance.history.append(node_execution)
                
                # Record in conversational history in agent_states
                conversation_turn_id = state.get("conversation_turn_id")
                if conversation_turn_id and "conversation_history" in instance.agent_states:
                    try:
                        # Find the current conversation turn in the agent_states
                        turns = instance.agent_states["conversation_history"]["turns"]
                        for turn in turns:
                            if turn.get("id") == conversation_turn_id:
                                # Create a record of this agent's response
                                agent_response = {
                                    "node_id": node_id,
                                    "content": output_for_history,
                                    "timestamp": datetime.now().isoformat()
                                }
                                
                                # Add metadata if this is the superego
                                if node_id == "input_superego" and isinstance(output, dict) and "update" in output:
                                    if "superego_evaluation" in output["update"]:
                                        se = output["update"]["superego_evaluation"]
                                        agent_response["metadata"] = {
                                            "decision": se.get("decision") if isinstance(se, dict) else se.decision,
                                            "reason": se.get("reason") if isinstance(se, dict) else se.reason
                                        }
                                
                                # Add to the conversation turn
                                turn["agent_responses"].append(agent_response)
                                
                                # Update conversation metadata
                                turn["metadata"]["last_node"] = node_id
                                
                                # Save the current flow state
                                turn["flow_state"] = {
                                    "current_node": node_id,
                                    "next_node": output.get("goto") if isinstance(output, dict) else None
                                }
                                
                                logger.info(f"Updated conversation turn {conversation_turn_id} with response from {node_id}")
                                break
                    except Exception as conv_error:
                        logger.error(f"Error updating conversation structure: {str(conv_error)}")
                        logger.exception(conv_error)
                
                # Update the instance
                self.update_flow_instance(instance)
                
                # Check if the output is a Command object
                if isinstance(output, dict) and "goto" in output:
                    # Convert to a Command object
                    logger.info(f"Node {node_id} returning Command goto={output['goto']}")
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
    
    def _create_multi_condition_router(self, node_id: str, condition_routes: Dict[str, str]):
        """
        Create a condition router function that handles multiple conditions for a node.
        
        Args:
            node_id: The ID of the node this router is for
            condition_routes: Dict mapping condition names to target nodes
            
        Returns:
            A router function that selects the next node
        """
        def router_function(state: Dict[str, Any]) -> str:
            """
            Router function for a LangGraph StateGraph.
            
            Args:
                state: The current state of the graph
                
            Returns:
                The name of the next node to route to
            """
            try:
                logger.info(f"ROUTER FOR NODE {node_id}: Evaluating with state keys: {list(state.keys())}")
                
                # Handle explicit routing with Command objects
                output = state.get('output', {})
                if isinstance(output, dict) and 'goto' in output:
                    next_node = output['goto']
                    logger.info(f"Using explicit goto={next_node} from Command")
                    if next_node in condition_routes.values():
                        return next_node
                
                # First check if Command routing was added to state by the node
                if "command_goto" in state:
                    next_node = state["command_goto"]
                    logger.info(f"Using command_goto={next_node} from state")
                    if next_node in condition_routes.values():
                        return next_node
                
                # Check if we have node-specific condition logic
                if node_id == "input_superego":
                    # Check for superego decision in various places
                    se_decision = None
                    
                    # 1. In state.superego_evaluation
                    if "superego_evaluation" in state:
                        se = state["superego_evaluation"]
                        se_decision = se.decision if hasattr(se, "decision") else se.get("decision")
                        if se_decision:
                            logger.info(f"Found superego decision {se_decision} in state.superego_evaluation")
                    
                    # 2. In state.output.update.superego_evaluation
                    if not se_decision and isinstance(output, dict) and "update" in output:
                        update = output["update"]
                        if isinstance(update, dict) and "superego_evaluation" in update:
                            se = update["superego_evaluation"]
                            se_decision = se.decision if hasattr(se, "decision") else se.get("decision")
                            if se_decision:
                                logger.info(f"Found superego decision {se_decision} in output.update.superego_evaluation")
                    
                    # If we found a decision, use it for routing
                    if se_decision:
                        # Map decision to condition keys
                        if se_decision == SuperegoDecision.ALLOW or se_decision == "ALLOW":
                            if "ALLOW" in condition_routes:
                                logger.info(f"Routing to {condition_routes['ALLOW']} based on ALLOW decision")
                                return condition_routes["ALLOW"]
                        elif se_decision == SuperegoDecision.BLOCK or se_decision == "BLOCK":
                            if "BLOCK" in condition_routes:
                                logger.info(f"Routing to {condition_routes['BLOCK']} based on BLOCK decision")
                                return condition_routes["BLOCK"]
                        elif se_decision == SuperegoDecision.CAUTION or se_decision == "CAUTION":
                            if "CAUTION" in condition_routes:
                                logger.info(f"Routing to {condition_routes['CAUTION']} based on CAUTION decision")
                                return condition_routes["CAUTION"]
                
                # Check for a default route
                if "default" in condition_routes:
                    logger.info(f"Using default route to {condition_routes['default']}")
                    return condition_routes["default"]
                elif "else" in condition_routes:
                    logger.info(f"Using else route to {condition_routes['else']}")
                    return condition_routes["else"]
                
                # If we've exhausted all options, route to END
                logger.warning(f"No suitable route found for {node_id}, routing to END")
                return END
                
            except Exception as e:
                logger.error(f"Error in router for node {node_id}: {str(e)}")
                logger.exception(e)
                return END
        
        return router_function
    
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
        on_token: Optional[Callable[[str, str, str], None]] = None,
        on_thinking: Optional[Callable[[str, str, str], None]] = None
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
        
        # Create or update conversation tracking structure in agent_states
        # This implements a more conversational approach for history
        conversation_turn_id = str(uuid.uuid4())
        conversation_turn = {
            "id": conversation_turn_id,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_responses": [],
            "metadata": {},
            "flow_state": {}
        }
        
        # Store conversation in agent_states.conversation_history
        if "conversation_history" not in instance.agent_states:
            instance.agent_states["conversation_history"] = {"turns": []}
        
        instance.agent_states["conversation_history"]["turns"].append(conversation_turn)
        self.update_flow_instance(instance)
        
        # Set up the initial state with the conversation turn ID
        state = {
            "instance_id": instance_id,
            "user_input": user_input,
            "messages": instance.messages,
            "conversation_turn_id": conversation_turn_id,
            "on_token": on_token,
            "on_thinking": on_thinking
        }
        
        try:
            # Run the graph
            instance.status = FlowStatus.RUNNING
            self.update_flow_instance(instance)
            
            # Critical fix: Explicitly reinitialize the graph to ensure proper traversal
            # This forces LangGraph to rebuild the graph to ensure it traverses correctly
            logger.critical("REINITIALIZING graph to ensure complete traversal")
            self.graphs[definition.id] = self.build_graph(definition)
            graph = self.graphs[definition.id]
            
            # Add detailed logging
            logger.critical(f"Starting flow execution with arun, nodes: {list(definition.nodes.keys())}")
            logger.critical(f"Graph state keys: {list(state.keys())}")
            
            # Use the appropriate async method to process the flow
            try:
                # Try different method names based on LangGraph version
                if hasattr(graph, 'arun'):
                    logger.info("Using graph.arun() method")
                    result_state = await graph.arun(state)
                elif hasattr(graph, 'ainvoke'):
                    logger.info("Using graph.ainvoke() method")
                    result_state = await graph.ainvoke(state)  
                elif hasattr(graph, 'acall'):
                    logger.info("Using graph.acall() method")
                    result_state = await graph.acall(state)
                else:
                    # Fallback to invoke with asyncio.to_thread if no async methods exist
                    logger.info("No async methods found, using graph.invoke() in a thread")
                    result_state = await asyncio.to_thread(graph.invoke, state)
                    
                logger.critical(f"Flow execution COMPLETED with nodes: {list(definition.nodes.keys())}")
                logger.critical(f"Final state keys: {list(result_state.keys())}")
            except Exception as exc:
                logger.error(f"Error during graph execution: {exc}")
                logger.exception(exc)
                raise
            
            # Create a result with the final state
            result = {
                "output": result_state.get("output", {}),
                "last_node": result_state.get("last_node", "unknown"),
                "messages": instance.messages  # Include the updated messages
            }
            
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
        on_token: Optional[Callable[[str, str, str], None]] = None,
        on_thinking: Optional[Callable[[str, str, str], None]] = None
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
        
        # Create or update conversation tracking structure in agent_states
        # This implements a more conversational approach for streaming
        conversation_turn_id = str(uuid.uuid4())
        conversation_turn = {
            "id": conversation_turn_id,
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "agent_responses": [],
            "metadata": {},
            "flow_state": {}
        }
        
        # Store conversation in agent_states.conversation_history
        if "conversation_history" not in instance.agent_states:
            instance.agent_states["conversation_history"] = {"turns": []}
        
        instance.agent_states["conversation_history"]["turns"].append(conversation_turn)
        self.update_flow_instance(instance)
        
        # Set up the initial state with the conversation turn ID
        state = {
            "instance_id": instance_id,
            "user_input": user_input,
            "messages": instance.messages,
            "conversation_turn_id": conversation_turn_id,
            "on_token": on_token,
            "on_thinking": on_thinking
        }
        
        try:
            # Run the graph
            instance.status = FlowStatus.RUNNING
            self.update_flow_instance(instance)
            
            # Critical fix: Explicitly reinitialize the graph to ensure proper traversal
            logger.critical("REINITIALIZING graph to ensure complete streaming traversal")
            self.graphs[definition.id] = self.build_graph(definition)
            graph = self.graphs[definition.id]
            
            logger.critical(f"Starting STREAMING flow execution with nodes: {list(definition.nodes.keys())}")
            
            # Stream the result using the appropriate method
            stream_method = None
            if hasattr(graph, 'astream'):
                stream_method = graph.astream
            elif hasattr(graph, 'astream_events'):
                stream_method = graph.astream_events
            elif hasattr(graph, 'stream_events'):
                # Wrap sync method in async generator
                async def async_stream_wrapper(state):
                    for event in graph.stream_events(state):
                        yield event
                stream_method = async_stream_wrapper
            else:
                logger.error("No streaming method found on graph object")
                yield {"error": "No streaming method available"}
                return
            
            # Use the identified streaming method
            async for event_type, event_data in stream_method(state):
                # Yield the event
                yield {
                    "event_type": event_type,
                    "event_data": event_data
                }
                
                # Update the instance based on the event
                if event_type == "node":
                    # Update the current node and log it
                    logger.info(f"PROCESSING NODE: {event_data}")
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
            
            # Log completion
            logger.info(f"FLOW COMPLETED: final node was {instance.current_node}")
            
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
