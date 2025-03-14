"""
Calculator Tool

Simple calculator tool for performing basic arithmetic operations.
"""

import re
import math
import operator
from typing import Union, Dict, Any


def calculate(expression: str) -> Union[float, str]:
    """Calculate the result of a mathematical expression
    
    Args:
        expression: A string containing a mathematical expression
        
    Returns:
        The calculated result or an error message
    """
    try:
        # Clean the expression
        cleaned = expression.strip()
        
        # Check for empty input
        if not cleaned:
            return "Error: Empty expression"
        
        # Basic security check - only allow safe characters
        if not re.match(r'^[0-9\s\.\+\-\*\/\(\)\^\%\,]+$', cleaned):
            return "Error: Invalid characters in expression"
        
        # Define safe operations
        safe_operators = {
            '+': operator.add,
            '-': operator.sub,
            '*': operator.mul,
            '/': operator.truediv,
            '^': operator.pow,
            '%': operator.mod
        }
        
        safe_functions = {
            'abs': abs,
            'round': round,
            'min': min,
            'max': max,
            'sqrt': math.sqrt,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan
        }
        
        # Create safe evaluation environment
        safe_dict = {**safe_operators, **safe_functions}
        
        # Replace ^ with ** for exponentiation
        cleaned = cleaned.replace('^', '**')
        
        # Evaluate using safe operations
        result = eval(cleaned, {"__builtins__": None}, safe_dict)
        
        # Format the result
        if isinstance(result, int) or (isinstance(result, float) and result.is_integer()):
            return int(result)
        else:
            return round(result, 10)  # Round to 10 decimal places to avoid float precision issues
    
    except ZeroDivisionError:
        return "Error: Division by zero"
    except ValueError as e:
        return f"Error: {str(e)}"
    except SyntaxError:
        return "Error: Invalid syntax in expression"
    except Exception as e:
        return f"Error: {str(e)}"


def register_tools() -> Dict[str, Any]:
    """Register the calculator tool for use in the agent system
    
    Returns:
        Dictionary mapping tool name to function
    """
    return {
        "calculator": calculate
    }
