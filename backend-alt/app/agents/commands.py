"""
Superego Command Constants

Simple module defining standard command constants for superego agents
to control flow execution. No function calls or complex logic - 
just constants as specified in the developer guide.
"""

# Superego evaluation decisions
BLOCK = "BLOCK"                       # Reject input entirely, conversation ends
ACCEPT = "ACCEPT"                     # Allow input without special handling
CAUTION = "CAUTION"                   # Allow with warning (agent_guidance passed to inner agent)
NEEDS_CLARIFICATION = "NEEDS_CLARIFICATION"  # Recurse to get more info from user

# Inner agent decisions
COMPLETE = "COMPLETE"                 # Task complete, flow can end or proceed
NEEDS_TOOL = "NEEDS_TOOL"             # Agent needs to use a tool, self-transition
NEEDS_RESEARCH = "NEEDS_RESEARCH"     # Insufficient information, transition to research
NEEDS_REVIEW = "NEEDS_REVIEW"         # Needs superego to review output
ERROR = "ERROR"                       # Error occurred, transition to error handler
AWAITING_TOOL_CONFIRMATION = "AWAITING_TOOL_CONFIRMATION"  # Waiting for user to confirm tool execution
