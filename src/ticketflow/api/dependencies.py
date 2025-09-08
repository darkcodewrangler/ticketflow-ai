"""
API Dependencies
Database connection validation and user authentication
PyTiDB doesn't need session management - operations work directly with tables!
"""

from fastapi import Depends, HTTPException
from typing import Dict, Any

from ..database.connection import db_manager


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


def get_current_user() -> Dict[str, Any]:
    """
    Placeholder for user authentication.
    In a real application, this would validate JWT tokens, API keys, etc.
    """
    # For now, return a default user
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
