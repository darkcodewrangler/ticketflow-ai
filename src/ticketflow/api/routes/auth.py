
from typing import Any, Dict

from fastapi import APIRouter
from ticketflow.database.connection import db_manager
from ticketflow.database.models import APIKey
from ticketflow.database.operations.auth import AuthOperations

router = APIRouter()


@router.post("/keys")
async def create_api_key(key_data: Dict[str, Any]):
    """Create new API key (admin only for demo)"""
    api_key, key_hash = AuthOperations.generate_api_key()
    
    key_record = APIKey(
        key_name=key_data["name"],
        api_key="",  # Never store the actual key
        key_hash=key_hash,
        organization=key_data.get("organization", ""),
        can_create_tickets=key_data.get("can_create_tickets", True),
        can_read_tickets=key_data.get("can_read_tickets", True),
        can_process_tickets=key_data.get("can_process_tickets", False),
        can_read_analytics=key_data.get("can_read_analytics", False)
    )
    
    created_key = db_manager.api_keys.insert(key_record)
    
    return {
        "api_key": api_key,  # Only returned once!
        "key_name": created_key.key_name,
        "permissions": {
            "create_tickets": created_key.can_create_tickets,
            "read_tickets": created_key.can_read_tickets,
            "process_tickets": created_key.can_process_tickets,
            "read_analytics": created_key.can_read_analytics
        },
        "warning": "Store this key securely - it won't be shown again"
    }

@router.get("/keys")
async def list_api_keys():
    """List API keys (without showing actual keys)"""
    keys = db_manager.api_keys.query(filters={"is_active": True}).to_list()
    
    return {
        "keys": [{
            "id": key.id,
            "key_name": key.key_name,
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
    }