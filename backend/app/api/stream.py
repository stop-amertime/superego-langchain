"""
SSE Streaming for Superego Agent System

Handles streaming of flow execution steps using Server-Sent Events (SSE).
Filters sensitive fields and formats output for clients.
"""

from typing import AsyncGenerator, Dict, Any
import json
import asyncio

from fastapi import Request
from sse_starlette.sse import EventSourceResponse


async def stream_response(
    generator: AsyncGenerator[Dict[str, Any], None]
) -> EventSourceResponse:
    """Stream flow execution steps as Server-Sent Events
    
    Args:
        generator: Async generator yielding flow steps
        
    Returns:
        SSE response with filtered and formatted flow steps
    """
    import logging
    logger = logging.getLogger("uvicorn")
    logger.info("Starting stream_response")
    
    async def event_generator():
        """Generate SSE events from flow steps"""
        try:
            logger.info("Begin processing generator items")
            
            async for step in generator:
                logger.info(f"Received step: {type(step).__name__}, Keys: {list(step.keys() if isinstance(step, dict) else [])}")
                
                # Handle StreamChunk instances directly
                if isinstance(step, dict) and hasattr(step, 'get') and step.get('partial_output') is not None:
                    # It's already a partial_output
                    event_type = "partial_output"
                    filtered_step = step
                    logger.info(f"Handling direct partial output: {step}")
                elif hasattr(step, 'partial_output'):  # It's a StreamChunk
                    event_type = "partial_output"
                    filtered_step = {
                        "partial_output": step.partial_output,
                        "complete": step.complete
                    }
                    # We don't have access to state here, so we can't add instance_id
                    logger.info(f"Handling StreamChunk: {filtered_step}")
                    
                    # Debug all attributes of the StreamChunk
                    logger.debug(f"StreamChunk attributes: {dir(step)}")
                    if hasattr(step, 'dict'):
                        logger.debug(f"StreamChunk as dict: {step.dict()}")
                    
                    # Add debugging for flow_step if present
                    if hasattr(step, 'flow_step') and step.flow_step:
                        logger.debug(f"StreamChunk contains flow_step: {step.flow_step}")
                    
                    # Log complete status and partial output
                    logger.debug(f"StreamChunk complete status: {step.complete}")
                    logger.debug(f"StreamChunk partial output: '{step.partial_output}'")
                    
                    # Make sure we include instance_id if available
                    if 'instance_id' in step.__dict__:
                        filtered_step['instance_id'] = step.instance_id
                    elif 'instance_id' in step.dict() if hasattr(step, 'dict') else {}:
                        filtered_step['instance_id'] = step.dict()['instance_id']
                else:
                    # Regular step processing
                    # Filter out hidden fields
                    filtered_step = filter_user_visible_fields(step)
                    
                    # Determine event type based on step
                    is_complete = "flow_step" in step or "complete_step" in step
                    event_type = "complete_step" if is_complete else "partial_output"
                    logger.info(f"Determined event type: {event_type}, is_complete={is_complete}")
                    
                    # Ensure that partial_output is a string, not an object
                    if event_type == "partial_output" and isinstance(filtered_step, dict) and "response" in filtered_step:
                        # Extract just the response as the partial output
                        filtered_step = {
                            "partial_output": filtered_step.get("response", ""),
                            "instance_id": filtered_step.get("instance_id")
                        }
                
                # Create JSON payload
                json_data = json.dumps({
                    "type": event_type,
                    "data": filtered_step
                })
                
                # Yield SSE event
                logger.info(f"Yielding event: {event_type}")
                yield {
                    "event": event_type,
                    "data": json_data
                }
                
                # Small delay to ensure proper event streaming
                await asyncio.sleep(0.01)
                
        except Exception as e:
            # Log the error with traceback
            import traceback
            logger.error(f"Error in event_generator: {str(e)}")
            logger.error(traceback.format_exc())
            
            # Send error as a special event
            error_data = json.dumps({
                "type": "error",
                "data": {"message": str(e)}
            })
            
            yield {
                "event": "error",
                "data": error_data
            }
    
    # Create SSE response
    return EventSourceResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable Nginx buffering
        }
    )


def filter_user_visible_fields(step: Dict[str, Any]) -> Dict[str, Any]:
    """Filter out fields that should not be visible to the user
    
    Args:
        step: Flow step with all fields
        
    Returns:
        Flow step with hidden fields removed
    """
    if not step:
        return {}
    
    # Copy the step to avoid modifying the original
    # Always preserve instance_id
    instance_id = step.get("instance_id")
    
    # Check for flow_step which is what inner_agent.py actually provides
    if "flow_step" in step:
        # Handle flow steps from inner_agent.py
        filtered_step = step["flow_step"].copy() if isinstance(step["flow_step"], dict) else {}
    elif "complete_step" in step:
        # Handle complete steps from the flow executor
        filtered_step = step["complete_step"].copy() if isinstance(step["complete_step"], dict) else {}
    elif "step" in step:
        # Handle steps from the flow executor
        filtered_step = step["step"].copy() if isinstance(step["step"], dict) else {}
    elif "type" in step and step["type"] == "partial_output":
        # Pass partial outputs directly and ensure instance_id is included
        partial_step = step.copy()
        if instance_id:
            partial_step["instance_id"] = instance_id
        return partial_step
    else:
        # Default case - just use the step as is
        filtered_step = step.copy()
    
    # Always include the instance_id in the filtered step
    if instance_id:
        filtered_step["instance_id"] = instance_id
    
    # Fields to hide from users
    hidden_fields = [
        "thinking",
        "agent_guidance",
        "raw_llm_output",
        "internal_metadata"
    ]
    
    # Remove hidden fields
    for field in hidden_fields:
        if field in filtered_step:
            filtered_step.pop(field)
    
    return filtered_step
