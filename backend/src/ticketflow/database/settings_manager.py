from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import json
import logging

from ticketflow.database.connection import PyTiDBManager
from ticketflow.database.models import Settings, SettingType, SettingCategory
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
    
    def initialize_default_settings(self) -> None:
        """
        Initialize default settings in the database if they don't exist.
        """
        try:
            for setting_data in self._default_settings:
                existing = self.get_setting(setting_data['key'])
                if not existing:
                    self.create_setting(**setting_data)
            logger.info("Default settings initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize default settings: {e}")
            raise
    
    def get_setting(self, key: str, decrypt: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a setting by key.
        
        Args:
            key: Setting key
            decrypt: Whether to decrypt sensitive values (default: True)
            
        Returns:
            Setting data or None if not found
        """
        try:
            # Use the standard db.settings pattern
            results = self.db.settings.query(filters={'key': key}, limit=1).to_list()
            
            if not results:
                return None
            
            setting = results[0]
            
            # Convert to dict - assuming setting is a dict-like object from PyTiDB
            setting_dict = {
                'id': setting.get('id'),
                'key': setting.get('key'),
                'category': setting.get('category'),
                'name': setting.get('name'),
                'description': setting.get('description'),
                'setting_type': setting.get('setting_type'),
                'value': setting.get('value'),
                'default_value': setting.get('default_value'),
                'is_enabled': bool(setting.get('is_enabled', True)),
                'is_required': bool(setting.get('is_required', False)),
                'is_sensitive': bool(setting.get('is_sensitive', False)),
                'validation_rules': json.loads(setting.get('validation_rules')) if setting.get('validation_rules') else {},
                'allowed_values': json.loads(setting.get('allowed_values')) if setting.get('allowed_values') else [],
                'created_at': setting.get('created_at'),
                'updated_at': setting.get('updated_at'),
                'updated_by': setting.get('updated_by')
            }
            
            # Decrypt sensitive values if requested
            if decrypt and setting_dict['is_sensitive'] and setting_dict['value']:
                try:
                    setting_dict['value'] = self.encryption.decrypt(setting_dict['value'])
                except Exception as e:
                    logger.error(f"Failed to decrypt setting {key}: {e}")
                    setting_dict['value'] = ""
            
            return setting_dict
                
        except Exception as e:
            logger.error(f"Failed to get setting {key}: {e}")
            return None
    
    def get_setting_value(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value with type conversion.
        
        Args:
            key: Setting key
            default: Default value if setting not found or disabled
            
        Returns:
            Converted setting value or default
        """
        setting = self.get_setting(key)
        
        if not setting or not setting['is_enabled']:
            return default
        
        return self._convert_value(setting['value'], setting['setting_type'])
    
    def get_settings_by_category(self, category: str, decrypt: bool = True) -> List[Dict[str, Any]]:
        """
        Get all settings in a category.
        
        Args:
            category: Setting category
            decrypt: Whether to decrypt sensitive values
            
        Returns:
            List of settings in the category
        """
        try:
            # Use the standard db.settings pattern
            results = self.db.settings.query(filters={'category': category}).to_list()
            
            if not results:
                return []
            
            settings_list = []
            for setting in results:
                setting_dict = {
                    'id': setting.get('id'),
                    'key': setting.get('key'),
                    'category': setting.get('category'),
                    'name': setting.get('name'),
                    'description': setting.get('description'),
                    'setting_type': setting.get('setting_type'),
                    'value': setting.get('value'),
                    'default_value': setting.get('default_value'),
                    'is_enabled': bool(setting.get('is_enabled', True)),
                    'is_required': bool(setting.get('is_required', False)),
                    'is_sensitive': bool(setting.get('is_sensitive', False)),
                    'validation_rules': json.loads(setting.get('validation_rules')) if setting.get('validation_rules') else {},
                    'allowed_values': json.loads(setting.get('allowed_values')) if setting.get('allowed_values') else [],
                    'created_at': setting.get('created_at'),
                    'updated_at': setting.get('updated_at'),
                    'updated_by': setting.get('updated_by')
                }
                
                # Decrypt sensitive values if requested
                if decrypt and setting_dict['is_sensitive'] and setting_dict['value']:
                    try:
                        setting_dict['value'] = self.encryption.decrypt(setting_dict['value'])
                    except Exception as e:
                        logger.error(f"Failed to decrypt setting {setting_dict['key']}: {e}")
                        setting_dict['value'] = ""
                
                settings_list.append(setting_dict)
            
            return settings_list
                
        except Exception as e:
            logger.error(f"Failed to get settings for category {category}: {e}")
            return []
    
    def create_setting(
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
            
            # Create new setting using standard db.settings pattern
            validation_rules_json = json.dumps(validation_rules) if validation_rules else None
            allowed_values_json = json.dumps(allowed_values) if allowed_values else None
            
            setting_data = {
                'key': key,
                'category': category,
                'name': name,
                'setting_type': setting_type,
                'value': encrypted_value,
                'default_value': encrypted_default,
                'description': description,
                'is_enabled': is_enabled,
                'is_required': is_required,
                'is_sensitive': is_sensitive,
                'validation_rules': validation_rules_json,
                'allowed_values': allowed_values_json,
                'updated_by': updated_by,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            
            result = self.db.settings.insert(setting_data)
            
            logger.info(f"Created setting: {key}")
            return  self.get_setting(key)
            
        except Exception as integrity_error:
            if "Duplicate entry" in str(integrity_error) or "UNIQUE constraint" in str(integrity_error):
                logger.error(f"Setting with key {key} already exists")
                return None
            raise
        except Exception as e:
            logger.error(f"Failed to create setting {key}: {e}")
            return None
    
    def update_setting(
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
            setting = self.get_setting(key, decrypt=False)
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
                'updated_at': datetime.now(),
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
            
            # Use standard db.settings.update() pattern
            self.db.settings.update(
                filters={'key': key},
                values=update_data
            )
            
            logger.info(f"Updated setting: {key}")
            return self.get_setting(key)
            
        except Exception as e:
            logger.error(f"Failed to update setting {key}: {e}")
            return None
    
    def delete_setting(self, key: str) -> bool:
        """
        Delete a setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Use standard db.settings pattern
            result = self.db.settings.delete(filters={'key': key})
            
            logger.info(f"Deleted setting: {key}")
            return True
                    
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
    
    def validate_setting(self, key: str, value: Any) -> tuple[bool, str]:
        """
        Validate a setting value.
        
        Args:
            key: Setting key
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        setting = self.get_setting(key, decrypt=False)
        if not setting:
            return False, f"Setting '{key}' not found"
        
        return self._validate_setting_value(value, setting)
    
    def validate_all_required_settings(self) -> Dict[str, str]:
        """
        Validate all required settings have values.
        
        Returns:
            Dictionary of setting_key -> error_message for invalid settings
        """
        errors = {}
        
        try:
            # Use standard db.settings pattern
            results = self.db.settings.query(filters={'is_required': True}).to_list()
            
            if not results:
                return errors
            
            for setting in results:
                setting_dict = {
                    'key': setting.get('key'),
                    'setting_type': setting.get('setting_type'),
                    'is_required': bool(setting.get('is_required', False)),
                    'validation_rules': json.loads(setting.get('validation_rules')) if setting.get('validation_rules') else {},
                    'allowed_values': json.loads(setting.get('allowed_values')) if setting.get('allowed_values') else []
                }
                
                # Get the actual value (decrypt if needed)
                value = setting.get('value')
                is_sensitive = bool(setting.get('is_sensitive', False))
                if is_sensitive and value:
                    try:
                        value = self.encryption.decrypt(value)
                    except Exception:
                        value = None
                
                is_valid, error_msg = self._validate_setting_value(value, setting_dict)
                if not is_valid:
                    errors[setting_dict['key']] = error_msg
                
        except Exception as e:
            logger.error(f"Failed to validate required settings: {e}")
            errors['system'] = f"Validation system error: {str(e)}"
        
        return errors
    
    def get_setting_with_fallback(self, key: str, fallback_value: Any = None) -> Any:
        """
        Get setting value with fallback to default value or provided fallback.
        
        Args:
            key: Setting key
            fallback_value: Value to return if setting not found or disabled
            
        Returns:
            Setting value, default value, or fallback value
        """
        try:
            setting = self.get_setting(key)
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
                'description': 'Bot token for Slack integration',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': True
            },
            {
                'key': 'slack_app_token',
                'category': SettingCategory.SLACK,
                'name': 'Slack App Token',
                'description': 'App-level token for Slack Socket Mode',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': True
            },
            {
                'key': 'slack_signing_secret',
                'category': SettingCategory.SLACK,
                'name': 'Signing Secret',
                'description': 'Secret for validating Slack requests',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': True
            },
            {
                'key': 'slack_new_ticket_channel',
                'category': SettingCategory.SLACK,
                'name': 'New Ticket Channel',
                'description': 'Slack channel for new ticket notifications',
                'setting_type': SettingType.STRING,
                'value': '#general',
                'default_value': '#general',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'slack_escalation_channel',
                'category': SettingCategory.SLACK,
                'name': 'Escalation Channel',
                'description': 'Slack channel for escalated ticket notifications',
                'setting_type': SettingType.STRING,
                'value': '#escalations',
                'default_value': '#escalations',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'slack_resolution_channel',
                'category': SettingCategory.SLACK,
                'name': 'Resolution Channel',
                'description': 'Slack channel for ticket resolution notifications',
                'setting_type': SettingType.STRING,
                'value': '#resolutions',
                'default_value': '#resolutions',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'slack_agent_assignment_channel',
                'category': SettingCategory.SLACK,
                'name': 'Agent Assignment Channel',
                'description': 'Slack channel for agent assignment notifications',
                'setting_type': SettingType.STRING,
                'value': '#assignments',
                'default_value': '#assignments',
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
            
            # Resend Email Settings (Primary)
            {
                'key': 'resend_api_key',
                'category': SettingCategory.EMAIL,
                'name': 'Resend API Key',
                'description': 'API key for Resend email service',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': True
            },
            {
                'key': 'resend_from_email',
                'category': SettingCategory.EMAIL,
                'name': 'From Email Address',
                'description': 'Email address to send from using Resend service',
                'setting_type': SettingType.STRING,
                'value': 'victory@notif.klozbuy.com',
                'default_value': 'victory@notif.klozbuy.com',
                'is_enabled': True,
                'is_required': True,
                'is_sensitive': False
            },
            {
                'key': 'resend_from_name',
                'category': SettingCategory.EMAIL,
                'name': 'From Name',
                'description': 'Display name for emails sent via Resend',
                'setting_type': SettingType.STRING,
                'value': 'TicketFlow Support',
                'default_value': 'TicketFlow Support',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_reply_to_email',
                'category': SettingCategory.EMAIL,
                'name': 'Reply-To Email',
                'description': 'Email address for replies',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_webhook_secret',
                'category': SettingCategory.EMAIL,
                'name': 'Webhook Secret',
                'description': 'Secret key for validating Resend webhook requests',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': True
            },
            {
                'key': 'resend_track_opens',
                'category': SettingCategory.EMAIL,
                'name': 'Track Email Opens',
                'description': 'Enable email open tracking via Resend',
                'setting_type': SettingType.BOOLEAN,
                'value': 'true',
                'default_value': 'true',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_track_clicks',
                'category': SettingCategory.EMAIL,
                'name': 'Track Email Clicks',
                'description': 'Enable email click tracking via Resend',
                'setting_type': SettingType.BOOLEAN,
                'value': 'true',
                'default_value': 'true',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_new_ticket_recipient',
                'category': SettingCategory.EMAIL,
                'name': 'New Ticket Email Recipients',
                'description': 'Email addresses to notify for new tickets (comma-separated)',
                'setting_type': SettingType.STRING,
                'value': 'victory@notif.klozbuy.com',
                'default_value': 'victory@notif.klozbuy.com',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_escalation_recipient',
                'category': SettingCategory.EMAIL,
                'name': 'Escalation Email Recipients',
                'description': 'Email addresses to notify for escalated tickets (comma-separated)',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_resolution_recipient',
                'category': SettingCategory.EMAIL,
                'name': 'Resolution Email Recipients',
                'description': 'Email addresses to notify for resolved tickets (comma-separated)',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_agent_assignment_recipient',
                'category': SettingCategory.EMAIL,
                'name': 'Agent Assignment Email Recipients',
                'description': 'Email addresses to notify for agent assignments (comma-separated)',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_notifications_enabled',
                'category': SettingCategory.EMAIL,
                'name': 'Enable Email Notifications',
                'description': 'Master switch for all email notifications via Resend',
                'setting_type': SettingType.BOOLEAN,
                'value': 'true',
                'default_value': 'true',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            
            # Resend API Settings
            {
                'key': 'resend_api_key',
                'category': SettingCategory.EMAIL,
                'name': 'Resend API Key',
                'description': 'API key for Resend email service',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': True
            },
            {
                'key': 'resend_from_email',
                'category': SettingCategory.EMAIL,
                'name': 'Resend From Email',
                'description': 'Email address to send from using Resend service',
                'setting_type': SettingType.STRING,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_from_name',
                'category': SettingCategory.EMAIL,
                'name': 'Resend From Name',
                'description': 'Display name for emails sent via Resend',
                'setting_type': SettingType.STRING,
                'value': 'TicketFlow Support',
                'default_value': 'TicketFlow Support',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_enabled',
                'category': SettingCategory.EMAIL,
                'name': 'Enable Resend Service',
                'description': 'Use Resend API instead of SMTP for email delivery',
                'setting_type': SettingType.BOOLEAN,
                'value': 'false',
                'default_value': 'false',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_webhook_secret',
                'category': SettingCategory.EMAIL,
                'name': 'Resend Webhook Secret',
                'description': 'Secret key for validating Resend webhook requests',
                'setting_type': SettingType.ENCRYPTED,
                'value': '',
                'default_value': '',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': True
            },
            {
                'key': 'resend_track_opens',
                'category': SettingCategory.EMAIL,
                'name': 'Track Email Opens',
                'description': 'Enable email open tracking via Resend',
                'setting_type': SettingType.BOOLEAN,
                'value': 'true',
                'default_value': 'true',
                'is_enabled': True,
                'is_required': False,
                'is_sensitive': False
            },
            {
                'key': 'resend_track_clicks',
                'category': SettingCategory.EMAIL,
                'name': 'Track Email Clicks',
                'description': 'Enable email click tracking via Resend',
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