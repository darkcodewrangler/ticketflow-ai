"""
API Dependencies
Database connection validation and user authentication
PyTiDB doesn't need session management - operations work directly with tables!
"""

from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, Any, List
from functools import wraps
import logging

from ticketflow.database.connection import db_manager
from ticketflow.database.operations.auth import AuthOperations

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


def verify_db_connection():
    """
    Dependency that verifies database connection is available.
    PyTiDB operations work directly with the client, no sessions needed!
    """
    if not db_manager._connected:
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not available"
        )
    return True


def get_current_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict[str, Any]:
    """
    Dependency for API key authentication.
    Validates API key from Authorization header and returns key info with permissions.
    """
    if not credentials:
        # Demo mode - allow access without authentication for testing
        logger.info("🔓 Demo mode: No authentication required")
        return {
            "id": "demo",
            "key_name": "demo",
            "organization": "demo",
            "permissions": {
                "create_tickets": True,
                "read_tickets": True,
                "process_tickets": True,
                "read_analytics": True
            }
        }
    
    api_key = credentials.credentials
    auth_data = AuthOperations.verify_api_key(api_key)
    
    if not auth_data:
        logger.warning(f"Invalid API key attempted: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired API key"
        )
    
    logger.info(f"✅ Authenticated: {auth_data['key_name']} ({auth_data['organization']})")
    return auth_data


def get_current_user() -> Dict[str, Any]:
    """
    Legacy dependency - kept for backward compatibility.
    Use get_current_api_key for new endpoints.
    """
    return {
        "id": "system",
        "username": "system",
        "role": "admin"
    }


def require_admin(current_user: dict = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency that requires admin privileges.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user


def require_permissions(required_permissions: List[str]):
    """
    Dependency factory that creates a permission checker.
    
    Args:
        required_permissions: List of required permissions like ['create_tickets', 'read_tickets']
    
    Returns:
        Dependency function that validates API key has required permissions
    """
    def permission_checker(api_key_data: Dict[str, Any] = Depends(get_current_api_key)) -> Dict[str, Any]:
        user_permissions = api_key_data.get('permissions', {})
        
        missing_permissions = []
        for permission in required_permissions:
            if not user_permissions.get(permission, False):
                missing_permissions.append(permission)
        
        if missing_permissions:
            logger.warning(
                f"Access denied for {api_key_data['key_name']}: "
                f"Missing permissions: {missing_permissions}"
            )
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Required: {required_permissions}, Missing: {missing_permissions}"
            )
        
        logger.info(
            f"✅ Permission check passed for {api_key_data['key_name']}: {required_permissions}"
        )
        return api_key_data
    
    return permission_checker


def get_db_manager():
    """
    Dependency that provides access to the PyTiDB manager.
    Verifies connection and returns the manager instance.
    """
    if not db_manager._connected:
        raise HTTPException(
            status_code=503,
            detail="Database connection is not available"
        )
    return db_manager
