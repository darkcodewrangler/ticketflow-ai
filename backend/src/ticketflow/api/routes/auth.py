
from typing import Any, Dict, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, Query
from ticketflow.database.operations.auth import AuthOperations
from ticketflow.api.dependencies import verify_db_connection, get_current_api_key, require_permissions
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/keys")
async def create_api_key(
    key_data: Dict[str, Any],
    _: bool = Depends(verify_db_connection)
):
    """Create new API key"""
    try:
        # Validate required fields
        if not key_data.get("name"):
            return error_response(
                message="Key name is required",
                error_code=ErrorCodes.VALIDATION_ERROR
            )
        
        created_key, api_key = await AuthOperations.create_api_key(key_data)
        
        return success_response(
            data={
                "api_key": api_key,  # Only returned once!
                "key_preview": created_key.key_preview,
                "key_name": created_key.key_name,
                "organization": created_key.organization,
                "permissions": {
                    "create_tickets": created_key.can_create_tickets,
                    "read_tickets": created_key.can_read_tickets,
                    "process_tickets": created_key.can_process_tickets,
                    "read_analytics": created_key.can_read_analytics
                },
                "warning": "Store this key securely - it won't be shown again"
            },
            message="API key created successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to create API key",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/keys")
async def list_api_keys(
    limit: int = Query(50, ge=1, le=100, description="Number of keys to return"),
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(get_current_api_key)
):
    """List API keys (without showing actual keys)"""
    try:
        keys = await AuthOperations.get_api_keys(limit=limit)
        
        key_list = [{
            "id": key.id,
            "key_name": key.key_name,
            "key_preview": key.key_preview,
            "organization": key.organization,
            "created_at": key.created_at,
            "last_used": key.last_used,
            "permissions": {
                "create_tickets": key.can_create_tickets,
                "read_tickets": key.can_read_tickets,
                "process_tickets": key.can_process_tickets,
                "read_analytics": key.can_read_analytics
            }
        } for key in keys]
        
        return success_response(
            data=key_list,
            message=ResponseMessages.RETRIEVED,
            count=len(key_list)
        )
    except Exception as e:
        return error_response(
             message="Failed to retrieve API keys",
             error=str(e),
             error_code=ErrorCodes.INTERNAL_ERROR
         )


@router.get("/keys/{key_id}")
async def get_api_key(
    key_id: int,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(get_current_api_key)
):
    """Get API key by ID"""
    try:
        key = await AuthOperations.get_api_key_by_id(key_id)
        if not key:
            return error_response(
                message="API key not found",
                error_code=ErrorCodes.NOT_FOUND
            )
        
        return success_response(
            data={
                "id": key.id,
                "key_name": key.key_name,
                "key_preview": key.key_preview,
                "organization": key.organization,
                "created_at": key.created_at,
                "last_used": key.last_used,
                "permissions": {
                    "create_tickets": key.can_create_tickets,
                    "read_tickets": key.can_read_tickets,
                    "process_tickets": key.can_process_tickets,
                    "read_analytics": key.can_read_analytics
                }
            },
            message="API key retrieved successfully"
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve API key",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.put("/keys/{key_id}")
async def update_api_key(
    key_id: str,
    update_data: Dict[str, Any],
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(get_current_api_key)
):
    """Update API key"""
    try:
        updated_key = await AuthOperations.update_api_key(key_id, update_data)
        if not updated_key:
            return error_response(
                message="API key not found",
                error_code=ErrorCodes.NOT_FOUND
            )
        
        return success_response(
            data={
                "id": updated_key.id,
                "key_name": updated_key.key_name,
                "organization": updated_key.organization,
                "permissions": {
                    "create_tickets": updated_key.can_create_tickets,
                    "read_tickets": updated_key.can_read_tickets,
                    "process_tickets": updated_key.can_process_tickets,
                    "read_analytics": updated_key.can_read_analytics
                }
            },
            message=ResponseMessages.UPDATED
        )
    except Exception as e:
        return error_response(
            message="Failed to update API key",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.delete("/keys/{key_id}")
async def delete_api_key(
    key_id: str,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(get_current_api_key)
):
    """Delete API key"""
    try:
        success = await AuthOperations.delete_api_key(key_id)
        if not success:
            return error_response(
                message="API key not found",
                error_code=ErrorCodes.NOT_FOUND
            )
        
        return success_response(
            message=ResponseMessages.DELETED
        )
    except Exception as e:
        return error_response(
            message="Failed to delete API key",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )