"""
API Dependencies
Database session management and other shared dependencies
"""

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException
from typing import Generator

from ..database.connection import db_manager


def get_db_session() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session for API endpoints.
    Automatically handles session cleanup.
    """
    if not db_manager._connected():
        raise HTTPException(
            status_code=503, 
            detail="Database connection is not available"
        )
    
    session = db_manager.get_session()
    if not session:
        raise HTTPException(
            status_code=503,
            detail="Unable to create database session"
        )
    
    try:
        yield session
    finally:
        session.close()


def get_current_user():
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


def require_admin(current_user: dict = Depends(get_current_user)):
    """
    Dependency that requires admin privileges.
    """
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin privileges required"
        )
    return current_user
