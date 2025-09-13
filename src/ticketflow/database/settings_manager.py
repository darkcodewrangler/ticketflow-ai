from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import logging
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError

from ticketflow.database.models import Settings, SettingType, SettingCategory
from ticketflow.database.connection import PyTiDBManager
from ticketflow.utils.encryption import EncryptionManager
from ticketflow.config import config

logger = logging.getLogger(__name__)

class SettingsManager:
    """
    Manages application settings with encryption support for sensitive data.
    
    Features:
    - CRUD operations for settings
    - Automatic encryption/decryption for sensitive settings
    - Type conversion and validation
    - Default settings initialization
    - Category-based organization
    - Enable/disable functionality
    """
    
    def __init__(self, db_manager: PyTiDBManager, encryption_key: Optional[str] = None):
        self.db = db_manager
        self.encryption = EncryptionManager(encryption_key or config.ENCRYPTION_KEY)
        self._default_settings = self._get_default_settings()
    
    async def initialize_default_settings(self) -> None:
        """
        Initialize default settings in the database if they don't exist.
        """
        try:
            for setting_data in self._default_settings:
                existing = await self.get_setting(setting_data['key'])
                if not existing:
                    await self.create_setting(**setting_data)
            logger.info("Default settings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize default settings: {e}")
            raise
    
    async def get_setting(self, key: str, decrypt: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a setting by key.
        
        Args:
            key: Setting key
            decrypt: Whether to decrypt sensitive values (default: True)
            
        Returns:
            Setting data or None if not found
        """
        try:
            async with self.db.get_session() as session:
                result = await session.execute(
                    select(Settings).where(Settings.key == key)
                )
                setting = result.scalar_one_or_none()
                
                if not setting:
                    return None
                
                setting_dict = {
                    'id': setting.id,
                    'key': setting.key,
                    'category': setting.category,
                    'name': setting.name,
                    'description': setting.description,
                    'setting_type': setting.setting_type,
                    'value': setting.value,
                    'default_value': setting.default_value,
                    'is_enabled': setting.is_enabled,
                    'is_required': setting.is_required,
                    'is_sensitive': setting.is_sensitive,
                    'validation_rules': setting.validation_rules,
                    'allowed_values': setting.allowed_values,
                    'created_at': setting.created_at,
                    'updated_at': setting.updated_at,
                    'updated_by': setting.updated_by
                }
                
                # Decrypt sensitive values if requested
                if decrypt and setting.is_sensitive and setting.value:
                    try:
                        setting_dict['value'] = self.encryption.decrypt(setting.value)
                    except Exception as e:
                        logger.error(f"Failed to decrypt setting {key}: {e}")
                        setting_dict['value'] = ""
                
                return setting_dict
                
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            return None
    
    async def get_setting_value(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value with type conversion.
        
        Args:
            key: Setting key
            default: Default value if setting not found or disabled
            
        Returns:
            Converted setting value or default
        """
        setting = await self.get_setting(key)
        
        if not setting or not setting['is_enabled']:
            return default
        
        return self._convert_value(setting['value'], setting['setting_type'])
    
    async def get_settings_by_category(self, category: str, decrypt: bool = True) -> List[Dict[str, Any]]:
        """
        Get all settings in a category.
        
        Args:
            category: Setting category
            decrypt: Whether to decrypt sensitive values
            
        Returns:
            List of settings in the category
        """
        try:
            async with self.db.get_session() as session:
                result = await session.execute(
                    select(Settings).where(Settings.category == category)
                )
                settings = result.scalars().all()
                
                settings_list = []
                for setting in settings:
                    setting_dict = {
                        'id': setting.id,
                        'key': setting.key,
                        'category': setting.category,
                        'name': setting.name,
                        'description': setting.description,
                        'setting_type': setting.setting_type,
                        'value': setting.value,
                        'default_value': setting.default_value,
                        'is_enabled': setting.is_enabled,
                        'is_required': setting.is_required,
                        'is_sensitive': setting.is_sensitive,
                        'validation_rules': setting.validation_rules,
                        'allowed_values': setting.allowed_values,
                        'created_at': setting.created_at,
                        'updated_at': setting.updated_at,
                        'updated_by': setting.updated_by
                    }
                    
                    # Decrypt sensitive values if requested
                    if decrypt and setting.is_sensitive and setting.value:
                        try:
                            setting_dict['value'] = self.encryption.decrypt(setting.value)
                        except Exception as e:
                            logger.error(f"Failed to decrypt setting {setting.key}: {e}")
                            setting_dict['value'] = ""
                    
                    settings_list.append(setting_dict)
                
                return settings_list
                
        except Exception as e:
            logger.error(f"Failed to get settings for category {category}: {e}")
            return []
    
    async def create_setting(
        self,
        key: str,
        category: str,
        name: str,
        setting_type: str,
        value: str = "",
        default_value: str = "",
        description: str = "",
        is_enabled: bool = True,
        is_required: bool = False,
        is_sensitive: bool = False,
        validation_rules: Optional[Dict] = None,
        allowed_values: Optional[List[str]] = None,
        updated_by: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Create a new setting.
        
        Args:
            key: Unique setting key
            category: Setting category
            name: Human-readable name
            setting_type: Data type (string, integer, float, boolean, json, encrypted)
            value: Setting value
            default_value: Default value
            description: Setting description
            is_enabled: Whether setting is enabled
            is_required: Whether setting is required
            is_sensitive: Whether setting contains sensitive data
            validation_rules: Validation rules
            allowed_values: List of allowed values
            updated_by: Who created the setting
            
        Returns:
            Created setting data or None if failed
        """
        try:
            # Encrypt sensitive values
            encrypted_value = value
            if is_sensitive and value:
                encrypted_value = self.encryption.encrypt(value)
            
            # Encrypt sensitive default values
            encrypted_default = default_value
            if is_sensitive and default_value:
                encrypted_default = self.encryption.encrypt(default_value)
            
            async with self.db.get_session() as session:
                setting = Settings(
                    key=key,
                    category=category,
                    name=name,
                    description=description,
                    setting_type=setting_type,
                    value=encrypted_value,
                    default_value=encrypted_default,
                    is_enabled=is_enabled,
                    is_required=is_required,
                    is_sensitive=is_sensitive,
                    validation_rules=validation_rules or {},
                    allowed_values=allowed_values or [],
                    updated_by=updated_by
                )
                
                session.add(setting)
                await session.commit()
                await session.refresh(setting)
                
                logger.info(f"Created setting: {key}")
                return await self.get_setting(key)
                
        except IntegrityError:
            logger.error(f"Setting with key {key} already exists")
            return None
        except Exception as e:
            logger.error(f"Failed to create setting {key}: {e}")
            return None
    
    async def update_setting(
        self,
        key: str,
        value: Optional[str] = None,
        is_enabled: Optional[bool] = None,
        updated_by: str = "system"
    ) -> Optional[Dict[str, Any]]:
        """
        Update a setting value and/or enabled status.
        
        Args:
            key: Setting key
            value: New value (optional)
            is_enabled: New enabled status (optional)
            updated_by: Who updated the setting
            
        Returns:
            Updated setting data or None if failed
        """
        try:
            setting = await self.get_setting(key, decrypt=False)
            if not setting:
                logger.error(f"Setting {key} not found")
                return None
            
            # Validate new value if provided
            if value is not None:
                is_valid, error_msg = self._validate_setting_value(value, setting)
                if not is_valid:
                    logger.error(f"Validation failed for setting {key}: {error_msg}")
                    raise ValueError(error_msg)
            
            update_data = {
                'updated_at': datetime.utcnow().isoformat(),
                'updated_by': updated_by
            }
            
            if value is not None:
                # Encrypt sensitive values
                if setting['is_sensitive']:
                    update_data['value'] = self.encryption.encrypt(value)
                else:
                    update_data['value'] = value
            
            if is_enabled is not None:
                update_data['is_enabled'] = is_enabled
            
            async with self.db.get_session() as session:
                await session.execute(
                    update(Settings)
                    .where(Settings.key == key)
                    .values(**update_data)
                )
                await session.commit()
            
            logger.info(f"Updated setting: {key}")
            return await self.get_setting(key)
            
        except Exception as e:
            logger.error(f"Failed to update setting {key}: {e}")
            return None
    
    async def delete_setting(self, key: str) -> bool:
        """
        Delete a setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            async with self.db.get_session() as session:
                result = await session.execute(
                    delete(Settings).where(Settings.key == key)
                )
                await session.commit()
                
                if result.rowcount > 0:
                    logger.info(f"Deleted setting: {key}")
                    return True
                else:
                    logger.warning(f"Setting {key} not found for deletion")
                    return False
                    
        except Exception as e:
            logger.error(f"Failed to delete setting {key}: {e}")
            return False
    
    def _convert_value(self, value: str, setting_type: str) -> Any:
        """
        Convert string value to appropriate type based on setting_type.
        
        Args:
            value: String value to convert
            setting_type: Target type
            
        Returns:
            Converted value
        """
        if not value:
            return None
            
        try:
            if setting_type == SettingType.INTEGER:
                return int(value)
            elif setting_type == SettingType.FLOAT:
                return float(value)
            elif setting_type == SettingType.BOOLEAN:
                return value.lower() in ('true', '1', 'yes', 'on')
            elif setting_type == SettingType.JSON:
                return json.loads(value)
            else:  # STRING or ENCRYPTED
                return value
        except (ValueError, json.JSONDecodeError) as e:
            logger.error(f"Failed to convert value '{value}' to type {setting_type}: {e}")
            return value  # Return original value if conversion fails
    
    def _validate_setting_value(self, value: Any, setting: Dict[str, Any]) -> tuple[bool, str]:
        """
        Validate a setting value against its validation rules.
        
        Args:
            value: Value to validate
            setting: Setting configuration with validation rules
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check if required setting has a value
            if setting.get('is_required', False) and (value is None or value == ""):
                return False, f"Setting '{setting['key']}' is required but no value provided"
            
            # Skip validation if no value provided for optional setting
            if value is None or value == "":
                return True, ""
            
            # Type validation
            setting_type = setting.get('setting_type', SettingType.STRING.value)
            try:
                converted_value = self._convert_value(str(value), setting_type)
                if converted_value is None and value != "":
                    return False, f"Invalid type for setting '{setting['key']}': expected {setting_type}"
            except Exception as e:
                return False, f"Type conversion failed for setting '{setting['key']}': {str(e)}"
            
            # Allowed values validation
            allowed_values = setting.get('allowed_values', [])
            if allowed_values and str(value) not in allowed_values:
                return False, f"Value '{value}' not allowed for setting '{setting['key']}'. Allowed values: {allowed_values}"
            
            # Custom validation rules
            validation_rules = setting.get('validation_rules', {})
            if validation_rules:
                # Min/Max length for strings
                if 'min_length' in validation_rules and len(str(value)) < validation_rules['min_length']:
                    return False, f"Value for '{setting['key']}' is too short (minimum {validation_rules['min_length']} characters)"
                
                if 'max_length' in validation_rules and len(str(value)) > validation_rules['max_length']:
                    return False, f"Value for '{setting['key']}' is too long (maximum {validation_rules['max_length']} characters)"
                
                # Min/Max value for numbers
                if setting_type in [SettingType.INTEGER.value, SettingType.FLOAT.value]:
                    numeric_value = float(converted_value) if converted_value is not None else 0
                    
                    if 'min_value' in validation_rules and numeric_value < validation_rules['min_value']:
                        return False, f"Value for '{setting['key']}' is too small (minimum {validation_rules['min_value']})"
                    
                    if 'max_value' in validation_rules and numeric_value > validation_rules['max_value']:
                        return False, f"Value for '{setting['key']}' is too large (maximum {validation_rules['max_value']})"
                
                # Pattern validation for strings
                if 'pattern' in validation_rules and setting_type == SettingType.STRING.value:
                    import re
                    if not re.match(validation_rules['pattern'], str(value)):
                        return False, f"Value for '{setting['key']}' does not match required pattern"
                
                # Email validation
                if validation_rules.get('format') == 'email':
                    import re
                    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                    if not re.match(email_pattern, str(value)):
                        return False, f"Value for '{setting['key']}' is not a valid email address"
                
                # URL validation
                if validation_rules.get('format') == 'url':
                    import re
                    url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
                    if not re.match(url_pattern, str(value)):
                        return False, f"Value for '{setting['key']}' is not a valid URL"
                
                # Slack channel validation
                if validation_rules.get('format') == 'slack_channel':
                    if not str(value).startswith('#') and not str(value).startswith('@'):
                        return False, f"Slack channel '{setting['key']}' must start with # or @"
            
            return True, ""
            
        except Exception as e:
            logger.error(f"Validation error for setting '{setting.get('key', 'unknown')}': {e}")
            return False, f"Validation failed: {str(e)}"
    
    async def validate_setting(self, key: str, value: Any) -> tuple[bool, str]:
        """
        Validate a setting value.
        
        Args:
            key: Setting key
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        setting = await self.get_setting(key, decrypt=False)
        if not setting:
            return False, f"Setting '{key}' not found"
        
        return self._validate_setting_value(value, setting)
    
    async def validate_all_required_settings(self) -> Dict[str, str]:
        """
        Validate all required settings have values.
        
        Returns:
            Dictionary of setting_key -> error_message for invalid settings
        """
        errors = {}
        
        try:
            async with self.db.get_session() as session:
                result = await session.execute(
                    select(Settings).where(Settings.is_required == True)
                )
                required_settings = result.scalars().all()
                
                for setting in required_settings:
                    setting_dict = {
                        'key': setting.key,
                        'setting_type': setting.setting_type,
                        'is_required': setting.is_required,
                        'validation_rules': setting.validation_rules or {},
                        'allowed_values': setting.allowed_values or []
                    }
                    
                    # Get the actual value (decrypt if needed)
                    value = setting.value
                    if setting.is_sensitive and value:
                        try:
                            value = self.encryption.decrypt(value)
                        except Exception:
                            value = None
                    
                    is_valid, error_msg = self._validate_setting_value(value, setting_dict)
                    if not is_valid:
                        errors[setting.key] = error_msg
                
        except Exception as e:
            logger.error(f"Failed to validate required settings: {e}")
            errors['system'] = f"Validation system error: {str(e)}"
        
        return errors
    
    async def get_setting_with_fallback(self, key: str, fallback_value: Any = None) -> Any:
        """
        Get setting value with fallback to default value or provided fallback.
        
        Args:
            key: Setting key
            fallback_value: Value to return if setting not found or disabled
            
        Returns:
            Setting value, default value, or fallback value
        """
        try:
            setting = await self.get_setting(key)
            if not setting:
                logger.warning(f"Setting '{key}' not found, using fallback")
                return fallback_value
            
            if not setting.get('is_enabled', True):
                logger.info(f"Setting '{key}' is disabled, using default or fallback")
                default_value = setting.get('default_value')
                if default_value is not None:
                    return self._convert_value(default_value, setting.get('setting_type', SettingType.STRING.value))
                return fallback_value
            
            value = setting.get('value')
            if value is not None and value != "":
                return self._convert_value(value, setting.get('setting_type', SettingType.STRING.value))
            
            # Use default value if no value set
            default_value = setting.get('default_value')
            if default_value is not None:
                return self._convert_value(default_value, setting.get('setting_type', SettingType.STRING.value))
            
            return fallback_value
            
        except Exception as e:
            logger.error(f"Error getting setting '{key}' with fallback: {e}")
            return fallback_value
    
    def _get_default_settings(self) -> List[Dict[str, Any]]:
        """
        Get default settings configuration.
        
        Returns:
            List of default settings
        """
        return [
            # Slack Settings
            {
                'key': 'slack_bot_token',
                'category': SettingCategory.SLACK,
                'name': 'Slack Bot Token',
                'description': 'Bot token for Slack API authentication',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': True
            },
            {
                'key': 'slack_new_ticket_channel',
                'category': SettingCategory.SLACK,
                'name': 'New Ticket Alert Channel',
                'description': 'Slack channel for new ticket notifications',
                'setting_type': SettingType.STRING,
                'value': '#general',
                'default_value': '#general',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'slack_escalated_ticket_channel',
                'category': SettingCategory.SLACK,
                'name': 'Escalated Ticket Alert Channel',
                'description': 'Slack channel for escalated ticket notifications',
                'setting_type': SettingType.STRING,
                'value': '#general',
                'default_value': '#general',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'slack_resolved_ticket_channel',
                'category': SettingCategory.SLACK,
                'name': 'Resolved Ticket Alert Channel',
                'description': 'Slack channel for resolved ticket notifications',
                'setting_type': SettingType.STRING,
                'value': '#general',
                'default_value': '#general',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'slack_notifications_enabled',
                'category': SettingCategory.SLACK,
                'name': 'Enable Slack Notifications',
                'description': 'Master switch for all Slack notifications',
                'setting_type': SettingType.BOOLEAN,
                'value': 'true',
                'default_value': 'true',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            
            # Email Settings
            {
                'key': 'email_smtp_server',
                'category': SettingCategory.EMAIL,
                'name': 'SMTP Server',
                'description': 'SMTP server for sending emails',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': 'smtp.gmail.com',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': False
            },
            {
                'key': 'email_smtp_port',
                'category': SettingCategory.EMAIL,
                'name': 'SMTP Port',
                'description': 'SMTP server port',
                'setting_type': SettingType.INTEGER,
                'value': '587',
                'default_value': '587',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': False
            },
            {
                'key': 'email_username',
                'category': SettingCategory.EMAIL,
                'name': 'Email Username',
                'description': 'Username for email authentication',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': False
            },
            {
                'key': 'email_password',
                'category': SettingCategory.EMAIL,
                'name': 'Email Password',
                'description': 'Password for email authentication',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': True
            },
            {
                'key': 'email_from_address',
                'category': SettingCategory.EMAIL,
                'name': 'From Email Address',
                'description': 'Email address to send notifications from',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': False
            },
            {
                'key': 'email_new_ticket_recipients',
                'category': SettingCategory.EMAIL,
                'name': 'New Ticket Email Recipients',
                'description': 'Email addresses to notify for new tickets (JSON array)',
                'setting_type': SettingType.JSON,
                'value': '[]',
                'default_value': '[]',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'email_escalated_ticket_recipients',
                'category': SettingCategory.EMAIL,
                'name': 'Escalated Ticket Email Recipients',
                'description': 'Email addresses to notify for escalated tickets (JSON array)',
                'setting_type': SettingType.JSON,
                'value': '[]',
                'default_value': '[]',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'email_resolved_ticket_recipients',
                'category': SettingCategory.EMAIL,
                'name': 'Resolved Ticket Email Recipients',
                'description': 'Email addresses to notify for resolved tickets (JSON array)',
                'setting_type': SettingType.JSON,
                'value': '[]',
                'default_value': '[]',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'email_notifications_enabled',
                'category': SettingCategory.EMAIL,
                'name': 'Enable Email Notifications',
                'description': 'Master switch for all email notifications',
                'setting_type': SettingType.BOOLEAN,
                'value': 'true',
                'default_value': 'true',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            
            # System Settings
            {
                'key': 'system_timezone',
                'category': SettingCategory.SYSTEM,
                'name': 'System Timezone',
                'description': 'Default timezone for the application',
                'setting_type': SettingType.STRING,
                'value': 'UTC',
                'default_value': 'UTC',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'system_max_tickets_per_page',
                'category': SettingCategory.SYSTEM,
                'name': 'Max Tickets Per Page',
                'description': 'Maximum number of tickets to display per page',
                'setting_type': SettingType.INTEGER,
                'value': '50',
                'default_value': '50',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'system_auto_assign_tickets',
                'category': SettingCategory.SYSTEM,
                'name': 'Auto-assign Tickets',
                'description': 'Automatically assign tickets to available agents',
                'setting_type': SettingType.BOOLEAN,
                'value': 'false',
                'default_value': 'false',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            
            # Agent Settings
            {
                'key': 'agent_max_concurrent_tickets',
                'category': SettingCategory.AGENT,
                'name': 'Max Concurrent Tickets per Agent',
                'description': 'Maximum number of tickets an agent can handle simultaneously',
                'setting_type': SettingType.INTEGER,
                'value': '10',
                'default_value': '10',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'agent_response_timeout',
                'category': SettingCategory.AGENT,
                'name': 'Agent Response Timeout (seconds)',
                'description': 'Maximum time to wait for agent response',
                'setting_type': SettingType.INTEGER,
                'value': '300',
                'default_value': '300',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            }
        ]