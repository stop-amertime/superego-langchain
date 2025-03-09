"""
Standardized error handling for the application.
This module defines standard error types, codes, and utility functions
for consistent error handling across the codebase.
"""

import logging
from enum import Enum
from typing import Dict, Any, Optional, Union
from datetime import datetime

from .models import WebSocketMessageType

# Set up logging
logger = logging.getLogger(__name__)

class ErrorCode(str, Enum):
    """Standard error codes for the application"""
    
    # General errors
    UNKNOWN_ERROR = "unknown_error"
    INVALID_REQUEST = "invalid_request"
    MISSING_PARAMETER = "missing_parameter"
    INVALID_PARAMETER = "invalid_parameter"
    
    # Authentication/authorization errors
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    
    # Resource errors
    NOT_FOUND = "not_found"
    ALREADY_EXISTS = "already_exists"
    CONFLICT = "conflict"
    
    # External service errors
    EXTERNAL_SERVICE_ERROR = "external_service_error"
    LLM_API_ERROR = "llm_api_error"
    
    # WebSocket errors
    WEBSOCKET_ERROR = "websocket_error"
    CONNECTION_ERROR = "connection_error"
    
    # Flow errors
    FLOW_ERROR = "flow_error"
    CHECKPOINT_ERROR = "checkpoint_error"
    
    # Constitution errors
    CONSTITUTION_ERROR = "constitution_error"
    PROTECTED_CONSTITUTION = "protected_constitution"

class AppError(Exception):
    """Base exception class for application errors"""
    
    def __init__(
        self, 
        code: Union[ErrorCode, str], 
        message: str, 
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the error
        
        Args:
            code: The error code
            message: The error message
            details: Additional error details
        """
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(message)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary
        
        Returns:
            A dictionary representation of the error
        """
        return {
            "code": self.code if isinstance(self.code, str) else self.code.value,
            "message": self.message,
            "details": self.details,
            "timestamp": datetime.now().isoformat()
        }
    
    def log(self, level: int = logging.ERROR):
        """
        Log the error
        
        Args:
            level: The logging level
        """
        logger.log(level, f"Error {self.code}: {self.message} - {self.details}")

# Specific error classes
class InvalidRequestError(AppError):
    """Error for invalid requests"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.INVALID_REQUEST, message, details)

class MissingParameterError(AppError):
    """Error for missing parameters"""
    
    def __init__(self, parameter: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.MISSING_PARAMETER, 
            f"Missing required parameter: {parameter}", 
            details
        )

class InvalidParameterError(AppError):
    """Error for invalid parameters"""
    
    def __init__(self, parameter: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.INVALID_PARAMETER, 
            f"Invalid parameter '{parameter}': {message}", 
            details
        )

class NotFoundError(AppError):
    """Error for resources not found"""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.NOT_FOUND, 
            f"{resource_type} with ID {resource_id} not found", 
            details
        )

class ExternalServiceError(AppError):
    """Error for external service failures"""
    
    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.EXTERNAL_SERVICE_ERROR, 
            f"Error from external service '{service}': {message}", 
            details
        )

class LLMApiError(AppError):
    """Error for LLM API failures"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.LLM_API_ERROR, message, details)

class WebSocketError(AppError):
    """Error for WebSocket failures"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.WEBSOCKET_ERROR, message, details)

class FlowError(AppError):
    """Error for flow failures"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.FLOW_ERROR, message, details)

class CheckpointError(AppError):
    """Error for checkpoint failures"""
    
    def __init__(self, checkpoint_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.CHECKPOINT_ERROR, 
            f"Error with checkpoint {checkpoint_id}: {message}", 
            details
        )

class ConstitutionError(AppError):
    """Error for constitution failures"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(ErrorCode.CONSTITUTION_ERROR, message, details)

class ProtectedConstitutionError(AppError):
    """Error for attempting to modify protected constitutions"""
    
    def __init__(self, constitution_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            ErrorCode.PROTECTED_CONSTITUTION, 
            f"Cannot modify protected constitution: {constitution_id}", 
            details
        )

# Utility functions
def format_error_response(error: AppError) -> Dict[str, Any]:
    """
    Format an error for API responses
    
    Args:
        error: The error to format
        
    Returns:
        A formatted error response
    """
    return {
        "success": False,
        "error": error.to_dict()
    }

def format_websocket_error(error: AppError, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Format an error for WebSocket responses
    
    Args:
        error: The error to format
        conversation_id: Optional conversation ID
        
    Returns:
        A formatted WebSocket error message
    """
    message = {
        "type": WebSocketMessageType.ERROR,
        "content": error.to_dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    if conversation_id:
        message["conversation_id"] = conversation_id
    
    return message

def handle_exception(e: Exception, context: Optional[Dict[str, Any]] = None) -> AppError:
    """
    Convert an exception to an AppError
    
    Args:
        e: The exception to convert
        context: Optional context information
        
    Returns:
        An AppError instance
    """
    if isinstance(e, AppError):
        return e
    
    # Add context to the error details
    details = {"exception_type": type(e).__name__}
    if context:
        details["context"] = context
    
    # Log the exception
    logger.exception(f"Unhandled exception: {str(e)}")
    
    # Convert to AppError
    return AppError(ErrorCode.UNKNOWN_ERROR, str(e), details)
