"""
Tools package for the Superego LangChain application.

This package contains tools that can be used by agents in the system.
"""

from .calculator import Calculator

# Registry of available tools
_tools = {}

def register_tool(tool):
    """Register a tool with the system."""
    _tools[tool.name] = tool
    return tool

def get_tool(name):
    """Get a tool by name."""
    return _tools.get(name)

def get_available_tools():
    """Get a list of all available tools."""
    return list(_tools.values())

# Register built-in tools
register_tool(Calculator())
