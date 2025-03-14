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
    async def event_generator():
        """Generate SSE events from flow steps"""
        try:
            async for step in generator:
                # Filter out hidden fields
                filtered_step = filter_user_visible_fields(step)
                
                # Determine event type based on step
                event_type = "complete_step" if "complete_step" in step else "partial_output"
                
                # Create JSON payload
                json_data = json.dumps({
                    "type": event_type,
                    "data": filtered_step
                })
                
                # Yield SSE event
                yield {
                    "event": event_type,
                    "data": json_data
                }
                
                # Small delay to ensure proper event streaming
                await asyncio.sleep(0.01)
                
        except Exception as e:
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
    if "complete_step" in step:
        # Handle complete steps from the flow executor
        filtered_step = step["complete_step"].copy() if isinstance(step["complete_step"], dict) else {}
    elif "step" in step:
        # Handle steps from the flow executor
        filtered_step = step["step"].copy() if isinstance(step["step"], dict) else {}
    elif "type" in step and step["type"] == "partial_output":
        # Pass partial outputs directly
        return step
    else:
        # Default case - just use the step as is
        filtered_step = step.copy()
    
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
