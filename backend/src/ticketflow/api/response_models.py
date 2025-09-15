"""Standardized API Response Models

This module provides standardized response wrappers for all API endpoints
to ensure consistent response patterns for client-side applications.
"""

from pydantic import BaseModel, Field
from typing import Any, Optional, Dict, List, Union, Generic, TypeVar
from datetime import datetime

# Generic type for data payload
T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper
    
    This class provides a consistent structure for all API responses,
    making it easier for client applications to handle responses uniformly.
    """
    success: bool = Field(description="Indicates if the request was successful")
    message: str = Field(description="Human-readable message describing the result")
    data: Optional[T] = Field(default=None, description="The main response data/payload")
    count: Optional[int] = Field(default=None, description="Number of items in data (for lists)")
    total: Optional[int] = Field(default=None, description="Total number of items available (for pagination)")
    page: Optional[int] = Field(default=None, description="Current page number (for pagination)")
    page_size: Optional[int] = Field(default=None, description="Number of items per page (for pagination)")
    error: Optional[str] = Field(default=None, description="Error message if success is false")
    error_code: Optional[str] = Field(default=None, description="Machine-readable error code")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Response timestamp")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier for tracking")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Additional metadata")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class SuccessResponse(APIResponse[T]):
    """Success response wrapper"""
    success: bool = Field(default=True)
    
    def __init__(self, 
                 data: T = None, 
                 message: str = "Success",
                 count: Optional[int] = None,
                 total: Optional[int] = None,
                 page: Optional[int] = None,
                 page_size: Optional[int] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 request_id: Optional[str] = None,
                 **kwargs):
        super().__init__(
            success=True,
            message=message,
            data=data,
            count=count,
            total=total,
            page=page,
            page_size=page_size,
            metadata=metadata,
            request_id=request_id,
            **kwargs
        )

class ErrorResponse(APIResponse[None]):
    """Error response wrapper"""
    success: bool = Field(default=False)
    data: None = Field(default=None)
    
    def __init__(self, 
                 message: str = "An error occurred",
                 error: Optional[str] = None,
                 error_code: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None,
                 request_id: Optional[str] = None,
                 **kwargs):
        super().__init__(
            success=False,
            message=message,
            data=None,
            error=error or message,
            error_code=error_code,
            metadata=metadata,
            request_id=request_id,
            **kwargs
        )

class PaginatedResponse(SuccessResponse[List[T]]):
    """Paginated response wrapper for list endpoints"""
    
    def __init__(self,
                 data: List[T],
                 count: int,
                 total: int,
                 page: int = 1,
                 page_size: int = 50,
                 message: str = "Data retrieved successfully",
                 metadata: Optional[Dict[str, Any]] = None,
                 request_id: Optional[str] = None,
                 **kwargs):
        super().__init__(
            data=data,
            message=message,
            count=count,
            total=total,
            page=page,
            page_size=page_size,
            metadata=metadata,
            request_id=request_id,
            **kwargs
        )

# Convenience functions for creating responses
def success_response(data: Any = None, 
                    message: str = "Success", 
                    count: Optional[int] = None,
                    **kwargs) -> Dict[str, Any]:
    """Create a success response"""
    # Auto-calculate count for lists
    if count is None and isinstance(data, list):
        count = len(data)
    
    response = SuccessResponse(
        data=data,
        message=message,
        count=count,
        **kwargs
    )
    return response.model_dump(exclude_none=True)

def error_response(message: str = "An error occurred",
                  error: Optional[str] = None,
                  error_code: Optional[str] = None,
                  **kwargs) -> Dict[str, Any]:
    """Create an error response"""
    response = ErrorResponse(
        message=message,
        error=error,
        error_code=error_code,
        **kwargs
    )
    return response.model_dump(exclude_none=True)

def paginated_response(data: List[Any],
                      total: int,
                      page: int = 1,
                      page_size: int = 50,
                      message: str = "Data retrieved successfully",
                      **kwargs) -> Dict[str, Any]:
    """Create a paginated response"""
    response = PaginatedResponse(
        data=data,
        count=len(data),
        total=total,
        page=page,
        page_size=page_size,
        message=message,
        **kwargs
    )
    return response.model_dump(exclude_none=True)

# Common response messages
class ResponseMessages:
    """Common response messages for consistency"""
    
    # Success messages
    CREATED = "Resource created successfully"
    UPDATED = "Resource updated successfully"
    DELETED = "Resource deleted successfully"
    RETRIEVED = "Data retrieved successfully"
    PROCESSED = "Request processed successfully"
    
    # Error messages
    NOT_FOUND = "Resource not found"
    VALIDATION_ERROR = "Validation error"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Access forbidden"
    INTERNAL_ERROR = "Internal server error"
    BAD_REQUEST = "Bad request"
    CONFLICT = "Resource conflict"
    
    # Specific messages
    TICKET_CREATED = "Ticket created successfully"
    TICKET_UPDATED = "Ticket updated successfully"
    TICKET_NOT_FOUND = "Ticket not found"
    TICKET_WORKFLOW_NOT_FOUND = "Ticket workflow not found"

    PROCESSING_STARTED = "Ticket processing started"
    PROCESSING_COMPLETED = "Ticket processing completed"
    
    KB_ARTICLE_CREATED = "Knowledge base article created successfully"
    KB_ARTICLE_UPDATED = "Knowledge base article updated successfully"
    KB_ARTICLE_NOT_FOUND = "Knowledge base article not found"
    
    WORKFLOW_STARTED = "Workflow started successfully"
    WORKFLOW_COMPLETED = "Workflow completed successfully"
    WORKFLOW_FAILED = "Workflow execution failed"

# Error codes for machine-readable error handling
class ErrorCodes:
    """Standard error codes"""
    
    # General errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    BAD_REQUEST = "BAD_REQUEST"
    CONFLICT = "CONFLICT"
    
    # Ticket-specific errors
    TICKET_NOT_FOUND = "TICKET_NOT_FOUND"
    TICKET_PROCESSING_FAILED = "TICKET_PROCESSING_FAILED"
    INVALID_TICKET_STATUS = "INVALID_TICKET_STATUS"
    
    # Knowledge base errors
    KB_ARTICLE_NOT_FOUND = "KB_ARTICLE_NOT_FOUND"
    KB_SEARCH_FAILED = "KB_SEARCH_FAILED"
    
    # Workflow errors
    WORKFLOW_NOT_FOUND = "WORKFLOW_NOT_FOUND"
    WORKFLOW_EXECUTION_FAILED = "WORKFLOW_EXECUTION_FAILED"
    
    # Agent errors
    AGENT_PROCESSING_FAILED = "AGENT_PROCESSING_FAILED"
    AGENT_TIMEOUT = "AGENT_TIMEOUT"
    
    # Integration errors
    WEBHOOK_VALIDATION_FAILED = "WEBHOOK_VALIDATION_FAILED"
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"
    
    # Additional error codes used in the codebase
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    PROCESSING_FAILED = "PROCESSING_FAILED"
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"