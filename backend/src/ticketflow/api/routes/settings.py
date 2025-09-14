from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
import logging

from ticketflow.database.connection import db_manager
from ticketflow.database import SettingsManager
from ticketflow.database.models import SettingType, SettingCategory
from ticketflow.api.response_models import (
    success_response, error_response,
    ResponseMessages, ErrorCodes
)
from ticketflow.api.dependencies import verify_db_connection
from ticketflow.config import config
from ticketflow.database.schemas import SettingCreateRequest, SettingResponse, SettingUpdateRequest, SettingsListResponse

logger = logging.getLogger(__name__)
router = APIRouter()

# Helper function to get settings manager
def get_settings_manager() -> SettingsManager:
    """Get settings manager instance"""
    return SettingsManager(db_manager, config.ENCRYPTION_KEY)

def _convert_setting_to_response(setting: Dict[str, Any]) -> SettingResponse:
    """Convert setting dict to response model with proper type conversion"""
    # Convert value based on setting type
    converted_value = setting['value']
    if setting['setting_type'] == SettingType.INTEGER and converted_value:
        try:
            converted_value = int(converted_value)
        except ValueError:
            pass
    elif setting['setting_type'] == SettingType.FLOAT and converted_value:
        try:
            converted_value = float(converted_value)
        except ValueError:
            pass
    elif setting['setting_type'] == SettingType.BOOLEAN and converted_value:
        converted_value = converted_value.lower() in ('true', '1', 'yes', 'on')
    
    # Convert default value
    converted_default = setting['default_value']
    if setting['setting_type'] == SettingType.INTEGER and converted_default:
        try:
            converted_default = int(converted_default)
        except ValueError:
            pass
    elif setting['setting_type'] == SettingType.FLOAT and converted_default:
        try:
            converted_default = float(converted_default)
        except ValueError:
            pass
    elif setting['setting_type'] == SettingType.BOOLEAN and converted_default:
        converted_default = converted_default.lower() in ('true', '1', 'yes', 'on')
    
    return SettingResponse(
        id=setting['id'],
        key=setting['key'],
        category=setting['category'],
        name=setting['name'],
        description=setting['description'],
        setting_type=setting['setting_type'],
        value=converted_value,
        default_value=converted_default,
        is_enabled=setting['is_enabled'],
        is_required=setting['is_required'],
        is_sensitive=setting['is_sensitive'],
        validation_rules=setting['validation_rules'],
        allowed_values=setting['allowed_values'],
        created_at=setting['created_at'],
        updated_at=setting['updated_at'],
        updated_by=setting['updated_by']
    )

@router.get("/")
async def get_all_settings(
    category: Optional[str] = None,
    include_sensitive: bool = False,
    _: bool = Depends(verify_db_connection)
):
    """
    Get all settings, optionally filtered by category.
    
    Args:
        category: Filter by setting category
        include_sensitive: Whether to include decrypted sensitive values (admin only)
        
    Returns:
        List of settings
    """
    try:
        settings_manager = get_settings_manager()
        
        if category:
            # Validate category
            valid_categories = [c.value for c in SettingCategory]
            if category not in valid_categories:
                return error_response(
                    message=f"Invalid category. Must be one of: {valid_categories}",
                    error_code=ErrorCodes.BAD_REQUEST,
                    status_code=400
                )
            
            settings_data = await settings_manager.get_settings_by_category(
                category, decrypt=include_sensitive
            )
        else:
            # Get all settings (we'll need to implement this method)
            settings_data = []
            for cat in SettingCategory:
                cat_settings = await settings_manager.get_settings_by_category(
                    cat.value, decrypt=include_sensitive
                )
                settings_data.extend(cat_settings)
        
        # Convert to response models
        settings_response = []
        for setting in settings_data:
            # Don't include sensitive values in response unless explicitly requested
            if setting['is_sensitive'] and not include_sensitive:
                setting = setting.copy()
                setting['value'] = "[ENCRYPTED]"
            
            settings_response.append(_convert_setting_to_response(setting))
        
        response_data = SettingsListResponse(
            settings=settings_response,
            total=len(settings_response),
            category=category
        )
        
        return success_response(
            data=response_data,
            message=f"Retrieved {len(settings_response)} settings"
        )
        
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        return error_response(
            message="Failed to retrieve settings",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )
   

@router.get("/validate/required")
async def validate_all_required_settings(
    _: bool = Depends(verify_db_connection)
):
    """
    Validate all required settings have proper values.
    
    Returns:
        Validation results for all required settings
    """
    try:
        settings_manager = get_settings_manager()
        
        # Validate all required settings
        validation_errors = await settings_manager.validate_all_required_settings()
        
        is_valid = len(validation_errors) == 0
        
        return success_response(
            data={
                "is_valid": is_valid,
                "errors": validation_errors,
                "error_count": len(validation_errors),
                "validated_at": datetime.utcnow().isoformat()
            },
            message=f"Validation {'passed' if is_valid else 'failed'} - {len(validation_errors)} errors found"
        )
        
    except Exception as e:
        logger.error(f"Failed to validate required settings: {e}")
        return error_response(
            message="Failed to validate required settings",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.get("/{key}")
async def get_setting(
    key: str,
    include_sensitive: bool = False,
    _: bool = Depends(verify_db_connection)
):
    """
    Get a specific setting by key.
    
    Args:
        key: Setting key
        include_sensitive: Whether to include decrypted sensitive values
        
    Returns:
        Setting data
    """
    try:
        settings_manager = get_settings_manager()
        
        setting = await settings_manager.get_setting(key, decrypt=include_sensitive)
        
        if not setting:
            return error_response(
                message=f"Setting '{key}' not found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=404
            )
        
        # Don't include sensitive values unless explicitly requested
        if setting['is_sensitive'] and not include_sensitive:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return success_response(
            data=setting_response,
            message=f"Retrieved setting '{key}'"
        )
        
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {e}")
        return error_response(
            message="Failed to retrieve setting",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.post("/")
async def create_setting(
    request: SettingCreateRequest,
    _: bool = Depends(verify_db_connection)
):
    """
    Create a new setting.
    
    Args:
        request: Setting creation data
        
    Returns:
        Created setting data
    """
    try:
        settings_manager = get_settings_manager()
        
        # Check if setting already exists
        existing = await settings_manager.get_setting(request.key)
        if existing:
            return error_response(
                message=f"Setting '{request.key}' already exists",
                error_code=ErrorCodes.CONFLICT,
                status_code=409
            )
        
        # Create setting
        setting = await settings_manager.create_setting(
            key=request.key,
            category=request.category,
            name=request.name,
            setting_type=request.setting_type,
            value=request.value,
            default_value=request.default_value,
            description=request.description,
            is_enabled=request.is_enabled,
            is_required=request.is_required,
            is_sensitive=request.is_sensitive,
            validation_rules=request.validation_rules,
            allowed_values=request.allowed_values,
            updated_by="api_user"  # TODO: Get from authentication
        )
        
        if not setting:
            return error_response(
                message="Failed to create setting",
                error_code=ErrorCodes.INTERNAL_ERROR,
                status_code=500
            )
        
        # Don't include sensitive values in response
        if setting['is_sensitive']:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return success_response(
            data=setting_response,
            message=f"Created setting '{request.key}'"
        )
        
    except Exception as e:
        logger.error(f"Failed to create setting {request.key}: {e}")
        return error_response(
            message="Failed to create setting",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.put("/{key}")
async def update_setting(
    key: str,
    request: SettingUpdateRequest,
    _: bool = Depends(verify_db_connection)
):
    """
    Update a setting value and/or enabled status.
    
    Args:
        key: Setting key
        request: Update data
        
    Returns:
        Updated setting data
    """
    try:
        settings_manager = get_settings_manager()
        
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            return error_response(
                message=f"Setting '{key}' not found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=404
            )
        
        # Validate the new value if provided
        if request.value is not None:
            is_valid, error_msg = await settings_manager.validate_setting(key, request.value)
            if not is_valid:
                return error_response(
                    message=f"Validation failed: {error_msg}",
                    error_code=ErrorCodes.VALIDATION_ERROR,
                    status_code=400
                )
        
        # Update setting
        setting = await settings_manager.update_setting(
            key=key,
            value=request.value,
            is_enabled=request.is_enabled,
            updated_by="api_user"  # TODO: Get from authentication
        )
        
        if not setting:
            return error_response(
                message="Failed to update setting",
                error_code=ErrorCodes.INTERNAL_ERROR,
                status_code=500
            )
        
        # Don't include sensitive values in response
        if setting['is_sensitive']:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return success_response(
            data=setting_response,
            message=f"Updated setting '{key}'"
        )
        
    except ValueError as e:
        # Validation errors
        return error_response(
            message=str(e),
            error_code=ErrorCodes.VALIDATION_ERROR,
            status_code=400
        )
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {e}")
        return error_response(
            message="Failed to update setting",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.delete("/{key}")
async def delete_setting(
    key: str,
    _: bool = Depends(verify_db_connection)
):
    """
    Delete a setting.
    
    Args:
        key: Setting key
        
    Returns:
        Success confirmation
    """
    try:
        settings_manager = get_settings_manager()
        
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            return error_response(
                message=f"Setting '{key}' not found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=404
            )
        
        # Check if setting is required
        if existing['is_required']:
            return error_response(
                message=f"Cannot delete required setting '{key}'",
                error_code=ErrorCodes.BAD_REQUEST,
                status_code=400
            )
        
        # Delete setting
        success = await settings_manager.delete_setting(key)
        
        if not success:
            return error_response(
                message="Failed to delete setting",
                error_code=ErrorCodes.INTERNAL_ERROR,
                status_code=500
            )
        
        return success_response(
            data={"key": key, "status": "deleted"},
            message=f"Deleted setting '{key}'"
        )
        
    except Exception as e:
        logger.error(f"Failed to delete setting {key}: {e}")
        return error_response(
            message="Failed to delete setting",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.post("/initialize")
async def initialize_default_settings(
    _: bool = Depends(verify_db_connection)
):
    """
    Initialize default settings in the database.
    
    Returns:
        Initialization status
    """
    try:
        settings_manager = get_settings_manager()
        
        await settings_manager.initialize_default_settings()
        
        # Count settings by category
        category_counts = {}
        for category in SettingCategory:
            settings = await settings_manager.get_settings_by_category(category.value, decrypt=False)
            category_counts[category.value] = len(settings)
        
        return success_response(
            data={
                "status": "initialized",
                "category_counts": category_counts,
                "total_settings": sum(category_counts.values())
            },
            message="Default settings initialized successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize default settings: {e}")
        return error_response(
            message="Failed to initialize default settings",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.get("/categories/list")
async def get_setting_categories():
    """
    Get list of available setting categories.
    
    Returns:
        List of setting categories
    """
    try:
        categories = [category.value for category in SettingCategory]
        return success_response(
            data=categories,
            message=f"Retrieved {len(categories)} setting categories"
        )
        
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        return error_response(
            message="Failed to retrieve categories",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.get("/types/list")
async def get_setting_types():
    """
    Get list of available setting types.
    
    Returns:
        List of setting types
    """
    try:
        types = [setting_type.value for setting_type in SettingType]
        return success_response(
            data=types,
            message=f"Retrieved {len(types)} setting types"
        )
        
    except Exception as e:
        logger.error(f"Failed to get types: {e}")
        return error_response(
            message="Failed to retrieve types",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.post("/validate/{key}")
async def validate_setting_value(
    key: str,
    value: str,
    _: bool = Depends(verify_db_connection)
):
    """
    Validate a setting value without updating it.
    
    Args:
        key: Setting key
        value: Value to validate
        
    Returns:
        Validation result
    """
    try:
        settings_manager = get_settings_manager()
        
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            return error_response(
                message=f"Setting '{key}' not found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=404
            )
        
        # Validate the value
        is_valid, error_msg = await settings_manager.validate_setting(key, request.value)
        
        return success_response(
            data={
                "key": key,
                "value": request.value,
                "is_valid": is_valid,
                "error_message": error_msg if not is_valid else None
            },
            message=f"Validation {'passed' if is_valid else 'failed'} for setting '{key}'"
        )
        
    except Exception as e:
        logger.error(f"Failed to validate setting {key}: {e}")
        return error_response(
            message="Failed to validate setting",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )

@router.post("/reset/{key}")
async def reset_setting_to_default(
    key: str,
    _: bool = Depends(verify_db_connection)
):
    """
    Reset a setting to its default value.
    
    Args:
        key: Setting key
        
    Returns:
        Reset setting data
    """
    try:
        settings_manager = get_settings_manager()
        
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            return error_response(
                message=f"Setting '{key}' not found",
                error_code=ErrorCodes.NOT_FOUND,
                status_code=404
            )
        
        # Reset to default value
        setting = await settings_manager.update_setting(
            key=key,
            value=existing['default_value'],
            is_enabled=None,  # Don't change enabled status
            updated_by="api_user"  # TODO: Get from authentication
        )
        
        if not setting:
            return error_response(
                message="Failed to reset setting",
                error_code=ErrorCodes.INTERNAL_ERROR,
                status_code=500
            )
        
        # Don't include sensitive values in response
        if setting['is_sensitive']:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return success_response(
            data=setting_response,
            message=f"Reset setting '{key}' to default value"
        )
        
    except Exception as e:
        logger.error(f"Failed to reset setting {key}: {e}")
        return error_response(
            message="Failed to reset setting",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR,
            status_code=500
        )