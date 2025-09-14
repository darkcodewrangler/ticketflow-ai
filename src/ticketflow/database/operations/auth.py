
import hashlib
import secrets
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from ticketflow.database import db_manager

security = HTTPBearer(auto_error=False)

class AuthOperations:
    @staticmethod
    def generate_api_key() -> tuple[str, str]:
        """Generate API key and its hash"""
        # Generate secure random key
        api_key = f"tk_{''.join(secrets.choice('abcdefghijklmnopqrstuvwxyz0123456789') for _ in range(32))}"
        
        # Hash for storage
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        
        return api_key, key_hash
    
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
                return None
            
            key_data = keys[0]
            
            # Update last used
            db_manager.api_keys.update(
                filters={"id": key_data.id},
                values={"last_used": datetime.utcnow().isoformat()}
            )
            
            return {
                "key_name": key_data.key_name,
                "organization": key_data.organization,
                "permissions": {
                    "create_tickets": key_data.can_create_tickets,
                    "read_tickets": key_data.can_read_tickets,
                    "process_tickets": key_data.can_process_tickets,
                    "read_analytics": key_data.can_read_analytics
                }
            }
            
        except Exception:
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