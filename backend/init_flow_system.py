#!/usr/bin/env python3
"""
Script to initialize the flow system.

This script will:
1. Create the flow definitions and instances directories
2. Create a default flow definition
"""

import os
import sys
import logging
import shutil

# Add the app directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Initialize the flow system."""
    logger.info("Initializing flow system...")
    
    try:
        # Import the flow engine
        from app.flow_engine import get_flow_engine, FLOW_DEFINITIONS_DIR, FLOW_INSTANCES_DIR
        
        # Clean up old data
        if os.path.exists(FLOW_DEFINITIONS_DIR):
            logger.info(f"Removing old flow definitions directory: {FLOW_DEFINITIONS_DIR}")
            shutil.rmtree(FLOW_DEFINITIONS_DIR)
        
        if os.path.exists(FLOW_INSTANCES_DIR):
            logger.info(f"Removing old flow instances directory: {FLOW_INSTANCES_DIR}")
            shutil.rmtree(FLOW_INSTANCES_DIR)
        
        # Create the directories
        os.makedirs(FLOW_DEFINITIONS_DIR, exist_ok=True)
        os.makedirs(FLOW_INSTANCES_DIR, exist_ok=True)
        
        logger.info(f"Created flow directories: {FLOW_DEFINITIONS_DIR}, {FLOW_INSTANCES_DIR}")
        
        # Get the flow engine
        flow_engine = get_flow_engine()
        
        # Create a default flow definition
        default_definition = flow_engine.create_default_flow_definition()
        
        logger.info(f"Created default flow definition: {default_definition.id}")
        
        # Create a research flow definition
        from app.models import FlowDefinition, NodeConfig, EdgeConfig
        from app.flow_engine import START_NODE, END_NODE
        from app.agents import AgentType
        
        research_definition = FlowDefinition(
            id=None,  # Will be generated
            name="Research Flow",
            description="Flow with input superego, router, researcher, and assistant",
            nodes={
                "input_superego": NodeConfig(
                    type=AgentType.INPUT_SUPEREGO,
                    config={
                        "constitution": "default"
                    }
                ),
                "router": NodeConfig(
                    type=AgentType.ROUTER,
                    config={
                        "system_prompt": "You are a router that decides which agent to call next based on the user's input."
                    }
                ),
                "researcher": NodeConfig(
                    type=AgentType.RESEARCHER,
                    config={
                        "system_prompt": "You are a researcher that searches for information to answer the user's question."
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
                EdgeConfig(from_node="input_superego", to_node="router", condition="ALLOW"),
                EdgeConfig(from_node="input_superego", to_node=END_NODE, condition="BLOCK"),
                EdgeConfig(from_node="router", to_node="researcher"),
                EdgeConfig(from_node="router", to_node="assistant"),
                EdgeConfig(from_node="researcher", to_node="assistant"),
                EdgeConfig(from_node="assistant", to_node=END_NODE)
            ]
        )
        
        research_definition = flow_engine.create_flow_definition(research_definition)
        
        logger.info(f"Created research flow definition: {research_definition.id}")
        
        logger.info("Flow system initialization completed successfully")
    except Exception as e:
        logger.error(f"Error during flow system initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
