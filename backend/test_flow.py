"""
Simple test script to check if the flow engine is working correctly.
"""

from app.flow_engine import get_flow_engine
import asyncio
import logging
import os

# Set up logging to file
LOG_FILE = os.path.join(os.path.dirname(__file__), "flow_test_output.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Helper to log to file
def log_to_file(message):
    with open(LOG_FILE, 'a') as f:
        f.write(f"{message}\n")

async def test_flow_execution():
    """Test the flow execution by processing a user input."""
    flow_engine = get_flow_engine()
    
    # Get the test instance
    instance_id = '40146f2c-1d4e-4eb5-8646-e67d3479124b'
    instance = flow_engine.get_flow_instance(instance_id)
    
    if not instance:
        print(f"Flow instance not found: {instance_id}")
        return
    
    print(f"Testing flow execution for instance: {instance.name} (ID: {instance.id})")
    print(f"Current node: {instance.current_node}")
    print(f"Current status: {instance.status}")
    
    # Process a test message
    print("\nProcessing test message...")
    result = await flow_engine.process_user_input(
        instance_id=instance.id,
        user_input="This is a test message",
        on_token=None,
        on_thinking=None
    )
    
    # Print the result
    print("\nResult:")
    print(f"Last node: {result.get('last_node')}")
    print(f"Output type: {type(result.get('output'))}")
    
    # Log to file
    log_to_file(f"\nRESULT:")
    log_to_file(f"Last node: {result.get('last_node')}")
    log_to_file(f"Output keys: {list(result.get('output', {}).keys())}")
    
    # Get the updated instance
    instance = flow_engine.get_flow_instance(instance_id)
    print(f"\nUpdated instance state:")
    print(f"Current node: {instance.current_node}")
    print(f"Current status: {instance.status}")
    
    # Log to file
    log_to_file(f"\nUPDATED INSTANCE STATE:")
    log_to_file(f"Current node: {instance.current_node}")
    log_to_file(f"Current status: {instance.status}")
    
    # Check if we have a conversation attribute
    if hasattr(instance, "conversation"):
        print("\nConversation history:")
        log_to_file("\nCONVERSATION HISTORY:")
        
        for i, turn in enumerate(instance.conversation):
            print(f"  Turn {i+1}:")
            print(f"    User input: {turn.get('user_input')}")
            print(f"    Agent responses: {len(turn.get('agent_responses', []))}")
            print(f"    Flow state: {turn.get('flow_state', {})}")
            
            log_to_file(f"  Turn {i+1}:")
            log_to_file(f"    User input: {turn.get('user_input')}")
            log_to_file(f"    Agent responses: {len(turn.get('agent_responses', []))}")
            log_to_file(f"    Flow state: {turn.get('flow_state', {})}")
            
            for j, response in enumerate(turn.get('agent_responses', [])):
                print(f"      Response {j+1}: {response.get('node_id')} - {type(response.get('content'))}")
                log_to_file(f"      Response {j+1}: {response.get('node_id')} - Content Type: {type(response.get('content'))}")
                if response.get('metadata'):
                    log_to_file(f"        Metadata: {response.get('metadata')}")

if __name__ == "__main__":
    asyncio.run(test_flow_execution())
