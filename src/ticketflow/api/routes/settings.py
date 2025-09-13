from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, Field, validator
import logging

from ticketflow.database.connection import db_manager
from ticketflow.database import SettingsManager
from ticketflow.database.models import SettingType, SettingCategory
from ticketflow.api.response_models import SuccessResponse, ErrorResponse
from ticketflow.config import config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/settings", tags=["settings"])

# Pydantic models for API requests/responses
class SettingResponse(BaseModel):
    """Response model for a single setting"""
    id: int
    key: str
    category: str
    name: str
    description: str
    setting_type: str
    value: Any  # Will be converted based on setting_type
    default_value: Any
    is_enabled: bool
    is_required: bool
    is_sensitive: bool
    validation_rules: Dict[str, Any]
    allowed_values: List[str]
    created_at: str
    updated_at: str
    updated_by: str

class SettingCreateRequest(BaseModel):
    """Request model for creating a new setting"""
    key: str = Field(..., min_length=1, max_length=100, description="Unique setting key")
    category: str = Field(..., min_length=1, max_length=50, description="Setting category")
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    setting_type: str = Field(..., description="Data type")
    value: str = Field(default="", description="Setting value")
    default_value: str = Field(default="", description="Default value")
    description: str = Field(default="", description="Setting description")
    is_enabled: bool = Field(default=True, description="Whether setting is enabled")
    is_required: bool = Field(default=False, description="Whether setting is required")
    is_sensitive: bool = Field(default=False, description="Whether setting contains sensitive data")
    validation_rules: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    allowed_values: Optional[List[str]] = Field(default=None, description="Allowed values")
    
    @validator('setting_type')
    def validate_setting_type(cls, v):
        valid_types = [t.value for t in SettingType]
        if v not in valid_types:
            raise ValueError(f"Invalid setting_type. Must be one of: {valid_types}")
        return v
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = [c.value for c in SettingCategory]
        if v not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        return v

class SettingUpdateRequest(BaseModel):
    """Request model for updating a setting"""
    value: Optional[str] = Field(None, description="New setting value")
    is_enabled: Optional[bool] = Field(None, description="Whether setting is enabled")

class SettingsListResponse(BaseModel):
    """Response model for settings list"""
    settings: List[SettingResponse]
    total: int
    category: Optional[str] = None

# Dependency to get settings manager
async def get_settings_manager() -> SettingsManager:
    """Get settings manager instance"""
    if not db_manager._connected:
        raise HTTPException(status_code=503, detail="Database connection not available")
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

@router.get("/", response_model=SuccessResponse[SettingsListResponse])
async def get_all_settings(
    category: Optional[str] = None,
    include_sensitive: bool = False,
    settings_manager: SettingsManager = Depends(get_settings_manager)
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
        if category:
            # Validate category
            valid_categories = [c.value for c in SettingCategory]
            if category not in valid_categories:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid category. Must be one of: {valid_categories}"
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
        
        return SuccessResponse(
            data=response_data,
            message=f"Retrieved {len(settings_response)} settings"
        )
        
    except Exception as e:
        logger.error(f"Failed to get settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve settings"
        )
    finally:
         await settings_manager.db.close()

@router.get("/validate/required", response_model=SuccessResponse[Dict[str, Any]])
async def validate_all_required_settings(
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Validate all required settings have proper values.
    
    Returns:
        Validation results for all required settings
    """
    try:
        # Validate all required settings
        validation_errors = await settings_manager.validate_all_required_settings()
        
        is_valid = len(validation_errors) == 0
        
        return SuccessResponse(
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate required settings"
        )
    finally:
        await settings_manager.db.close()

@router.get("/{key}", response_model=SuccessResponse[SettingResponse])
async def get_setting(
    key: str,
    include_sensitive: bool = False,
    settings_manager: SettingsManager = Depends(get_settings_manager)
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
        setting = await settings_manager.get_setting(key, decrypt=include_sensitive)
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Don't include sensitive values unless explicitly requested
        if setting['is_sensitive'] and not include_sensitive:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return SuccessResponse(
            data=setting_response,
            message=f"Retrieved setting '{key}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get setting {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve setting"
        )
    finally:
        await settings_manager.db.close()

@router.post("/", response_model=SuccessResponse[SettingResponse])
async def create_setting(
    request: SettingCreateRequest,
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Create a new setting.
    
    Args:
        request: Setting creation data
        
    Returns:
        Created setting data
    """
    try:
        # Check if setting already exists
        existing = await settings_manager.get_setting(request.key)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Setting '{request.key}' already exists"
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
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create setting"
            )
        
        # Don't include sensitive values in response
        if setting['is_sensitive']:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return SuccessResponse(
            data=setting_response,
            message=f"Created setting '{request.key}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create setting {request.key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create setting"
        )
    finally:
        await settings_manager.db.close()

@router.put("/{key}", response_model=SuccessResponse[SettingResponse])
async def update_setting(
    key: str,
    request: SettingUpdateRequest,
    settings_manager: SettingsManager = Depends(get_settings_manager)
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
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Validate the new value if provided
        if request.value is not None:
            is_valid, error_msg = await settings_manager.validate_setting(key, request.value)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Validation failed: {error_msg}"
                )
        
        # Update setting
        setting = await settings_manager.update_setting(
            key=key,
            value=request.value,
            is_enabled=request.is_enabled,
            updated_by="api_user"  # TODO: Get from authentication
        )
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update setting"
            )
        
        # Don't include sensitive values in response
        if setting['is_sensitive']:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return SuccessResponse(
            data=setting_response,
            message=f"Updated setting '{key}'"
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        # Validation errors
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to update setting {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update setting"
        )
    finally:
        await settings_manager.db.close()

@router.delete("/{key}", response_model=SuccessResponse[Dict[str, str]])
async def delete_setting(
    key: str,
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Delete a setting.
    
    Args:
        key: Setting key
        
    Returns:
        Success confirmation
    """
    try:
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Check if setting is required
        if existing['is_required']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete required setting '{key}'"
            )
        
        # Delete setting
        success = await settings_manager.delete_setting(key)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete setting"
            )
        
        return SuccessResponse(
            data={"key": key, "status": "deleted"},
            message=f"Deleted setting '{key}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete setting {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete setting"
        )
    finally:
        await settings_manager.db.close()

@router.post("/initialize", response_model=SuccessResponse[Dict[str, Any]])
async def initialize_default_settings(
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Initialize default settings in the database.
    
    Returns:
        Initialization status
    """
    try:
        await settings_manager.initialize_default_settings()
        
        # Count settings by category
        category_counts = {}
        for category in SettingCategory:
            settings = await settings_manager.get_settings_by_category(category.value, decrypt=False)
            category_counts[category.value] = len(settings)
        
        return SuccessResponse(
            data={
                "status": "initialized",
                "category_counts": category_counts,
                "total_settings": sum(category_counts.values())
            },
            message="Default settings initialized successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to initialize default settings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize default settings"
        )
    finally:
        await settings_manager.db.close()

@router.get("/categories/list", response_model=SuccessResponse[List[str]])
async def get_setting_categories():
    """
    Get list of available setting categories.
    
    Returns:
        List of setting categories
    """
    categories = [category.value for category in SettingCategory]
    return SuccessResponse(
        data=categories,
        message=f"Retrieved {len(categories)} setting categories"
    )

@router.get("/types/list", response_model=SuccessResponse[List[str]])
async def get_setting_types():
    """
    Get list of available setting types.
    
    Returns:
        List of setting types
    """
    types = [setting_type.value for setting_type in SettingType]
    return SuccessResponse(
        data=types,
        message=f"Retrieved {len(types)} setting types"
    )

@router.post("/validate/{key}", response_model=SuccessResponse[Dict[str, Any]])
async def validate_setting_value(
    key: str,
    value: str,
    settings_manager: SettingsManager = Depends(get_settings_manager)
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
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Validate the value
        is_valid, error_msg = await settings_manager.validate_setting(key, value)
        
        return SuccessResponse(
            data={
                "key": key,
                "value": value,
                "is_valid": is_valid,
                "error_message": error_msg if not is_valid else None
            },
            message=f"Validation {'passed' if is_valid else 'failed'} for setting '{key}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to validate setting {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate setting"
        )
    finally:
        await settings_manager.db.close()

@router.post("/reset/{key}", response_model=SuccessResponse[SettingResponse])
async def reset_setting_to_default(
    key: str,
    settings_manager: SettingsManager = Depends(get_settings_manager)
):
    """
    Reset a setting to its default value.
    
    Args:
        key: Setting key
        
    Returns:
        Reset setting data
    """
    try:
        # Check if setting exists
        existing = await settings_manager.get_setting(key)
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{key}' not found"
            )
        
        # Reset to default value
        setting = await settings_manager.update_setting(
            key=key,
            value=existing['default_value'],
            is_enabled=None,  # Don't change enabled status
            updated_by="api_user"  # TODO: Get from authentication
        )
        
        if not setting:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reset setting"
            )
        
        # Don't include sensitive values in response
        if setting['is_sensitive']:
            setting = setting.copy()
            setting['value'] = "[ENCRYPTED]"
        
        setting_response = _convert_setting_to_response(setting)
        
        return SuccessResponse(
            data=setting_response,
            message=f"Reset setting '{key}' to default value"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reset setting {key}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset setting"
        )
    finally:
        await settings_manager.db.close()