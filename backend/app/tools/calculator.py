"""
Simple calculator tool for the assistant agent.
"""

import logging
import math
from typing import Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Calculator:
    """Simple calculator tool that can perform basic arithmetic operations."""
    
    def __init__(self):
        """Initialize the calculator."""
        self.name = "calculator"
        self.description = "A calculator that can perform basic arithmetic operations."
        logger.info("Initialized Calculator tool")
    
    async def execute(self, arguments: Dict[str, Any], context: Dict[str, Any] = None) -> str:
        """
        Execute the calculator with the given arguments.
        
        Args:
            arguments: The arguments for the calculator, including:
                - expression: The expression to evaluate
            context: Additional context (not used)
            
        Returns:
            The result of the calculation as a string
        """
        expression = arguments.get("expression", "")
        
        if not expression:
            logger.warning("No expression provided to calculator")
            return "Error: No expression provided"
        
        logger.info(f"Calculating expression: {expression}")
        
        try:
            # Create a safe environment for eval
            safe_env = {
                "abs": abs,
                "round": round,
                "max": max,
                "min": min,
                "sum": sum,
                "len": len,
                "pow": pow,
                "math": math
            }
            
            # Evaluate the expression
            result = eval(expression, {"__builtins__": {}}, safe_env)
            
            logger.info(f"Calculation result: {result}")
            return f"Result: {result}"
            
        except Exception as e:
            logger.error(f"Error calculating expression: {e}")
            return f"Error: {str(e)}"
