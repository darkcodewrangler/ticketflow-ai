
import hashlib
import secrets
import logging
from datetime import datetime
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any, List

from ticketflow.database.connection import db_manager
from ticketflow.database.models import APIKey
from ticketflow.utils.helpers import get_isoformat, get_value

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)

class AuthOperations:
    """
    Authentication operations with standardized CRUD patterns
    """
    
    @staticmethod
    def create_api_key(key_data: Dict[str, Any]) -> tuple[APIKey, str]:
        """Create new API key with standardized pattern"""
        try:
            # Generate secure API key, hash, and preview
            api_key, key_hash, key_preview = AuthOperations.generate_api_key()
            
            # Create APIKey instance
            key_record = APIKey(
                key_name=get_value(key_data, "name", ""),
                api_key="",  # Never store the actual key
                key_hash=key_hash,
                key_preview=key_preview,
                organization=get_value(key_data, "organization", ""),
                can_create_tickets=get_value(key_data, "can_create_tickets", True),
                can_read_tickets=get_value(key_data, "can_read_tickets", True),
                can_process_tickets=get_value(key_data, "can_process_tickets", False),
                can_read_analytics=get_value(key_data, "can_read_analytics", False)
            )
            
            # Insert into database
            result = db_manager.api_keys.insert(key_record)
            created_key = result[0] if isinstance(result, list) else result
            
            logger.info(f"Created API key {created_key.key_name} for {created_key.organization}")
            return created_key, api_key
            
        except Exception as e:
            logger.error(f"Failed to create API key: {e}")
            raise
    
    @staticmethod
    def generate_api_key() -> tuple[str, str, str]:
        """Generate API key, its hash, and preview"""
        # Generate secure random key
        api_key = f"tk_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"
        
        # Hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        # Create preview (first 8 chars + ... + last 4 chars)
        key_preview = f"{api_key[:8]}...{api_key[-4:]}"
        
        return api_key, key_hash, key_preview
    
    @staticmethod
    def get_api_keys(filters: Dict[str, Any] = None, limit: int = 50) -> List[APIKey]:
        """Get API keys with optional filters"""
        try:
            query_filters = filters or {"is_active": True}
            results = db_manager.api_keys.query(
                filters=query_filters,
                limit=limit,
                order_by={"created_at": "desc"}
            ).to_list()
            
            # Convert dict results to APIKey objects
            keys = []
            for result in results:
                if isinstance(result, dict):
                    # Convert dict to APIKey object
                    key = APIKey(**result)
                    keys.append(key)
                else:
                    # Already an APIKey object
                    keys.append(result)
            
            logger.info(f"Retrieved {len(keys)} API keys")
            return keys
            
        except Exception as e:
            logger.error(f"Failed to get API keys: {e}")
            raise
    
    @staticmethod
    def get_api_key_by_id(key_id: int) -> Optional[APIKey]:
        """Get API key by ID"""
        try:
            results = db_manager.api_keys.query(
                filters={"id": key_id, "is_active": True},
                limit=1
            ).to_list()
            
            if not results:
                logger.warning(f"API key {key_id} not found")
                return None
            
            result = results[0]
            if isinstance(result, dict):
                # Convert dict to APIKey object
                return APIKey(**result)
            else:
                # Already an APIKey object
                return result
            
        except Exception as e:
            logger.error(f"Failed to get API key {key_id}: {e}")
            raise
    
    @staticmethod
    def update_api_key(key_id: int, update_data: Dict[str, Any]) -> Optional[APIKey]:
        """Update API key with standardized pattern - only name and organization allowed"""
        try:
            # Only allow updating name and organization for security
            allowed_fields = {"key_name", "organization"}
            
            filtered_data = {
                k: v for k, v in update_data.items() 
                if k in allowed_fields and v is not None
            }
            
            # Handle 'name' field mapping to 'key_name'
            if "name" in update_data:
                filtered_data["key_name"] = update_data["name"]
                filtered_data.pop("name", None)
            
            if not filtered_data:
                logger.warning("No valid fields to update (only name and organization allowed)")
                return None
            
            # Update the key
            updated_count = db_manager.api_keys.update(
                filters={"id": key_id, "is_active": True},
                values=filtered_data
            )
            
            if updated_count == 0:
                logger.warning(f"API key {key_id} not found for update")
                return None
            
            # Return updated key
            updated_key = AuthOperations.get_api_key_by_id(key_id)
            logger.info(f"Updated API key {key_id} (name/org only)")
            return updated_key
            
        except Exception as e:
            logger.error(f"Failed to update API key {key_id}: {e}")
            raise
    
    @staticmethod
    def delete_api_key(key_id: int) -> bool:
        """Soft delete API key (mark as inactive)"""
        try:
            updated_count = db_manager.api_keys.update(
                filters={"id": key_id, "is_active": True},
                values={"is_active": False}
            )
            
            if updated_count == 0:
                logger.warning(f"API key {key_id} not found for deletion")
                return False
            
            logger.info(f"Deleted API key {key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete API key {key_id}: {e}")
            raise
    
    @staticmethod
    def verify_api_key(api_key: str) -> Optional[dict]:
        """Verify API key and return permissions"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()
            
            # Query database for key
            keys = db_manager.api_keys.query(
                filters={"key_hash": key_hash, "is_active": True},
                limit=1
            ).to_list()
            
            if not keys:
                logger.warning("Invalid API key attempted")
                return None
            
            key_data = keys[0]
            
            # Update last used
            db_manager.api_keys.update(
                filters={"id": key_data.id},
                values={"last_used": get_isoformat()}
            )
            
            logger.info(f"API key verified for {key_data.key_name}")
            return {
                "id": key_data.id,
                "key_name": key_data.key_name,
                "organization": key_data.organization,
                "permissions": {
                    "create_tickets": key_data.can_create_tickets,
                    "read_tickets": key_data.can_read_tickets,
                    "process_tickets": key_data.can_process_tickets,
                    "read_analytics": key_data.can_read_analytics
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to verify API key: {e}")
            return None

def get_current_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """FastAPI dependency for API key authentication"""
    
    # For demo purposes, allow access without auth
    if not credentials:
        return {
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
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    return auth_data

def require_permission(permission: str):
    """Decorator factory for permission checking"""
    def permission_checker(auth_data: dict = Depends(get_current_api_key)):
        if not auth_data["permissions"].get(permission, False):
            raise HTTPException(
                status_code=403, 
                detail=f"Missing required permission: {permission}"
            )
        return auth_data
    return permission_checker


# Export operations classes
__all__ = [
    "AuthOperations",
]