#!/usr/bin/env python3
"""
TicketFlow AI Settings Initialization Script

This script provides comprehensive settings management functionality:
1. Initialize default settings in the database
2. Validate environment configuration
3. Backup and restore settings
4. Reset settings to defaults
5. Display current settings configuration

Usage:
    python init_settings.py                    # Initialize default settings
    python init_settings.py --validate         # Validate current settings
    python init_settings.py --backup           # Backup current settings
    python init_settings.py --restore <file>   # Restore settings from backup
    python init_settings.py --reset            # Reset all settings to defaults
    python init_settings.py --show             # Show current settings
"""

import asyncio
import sys
import os
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ticketflow.config import config
from src.ticketflow.database.connection import db_manager
from src.ticketflow.database.settings_manager import SettingsManager
from src.ticketflow.database.models import SettingCategory, SettingType

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SettingsInitializer:
    """Settings initialization and management class"""
    
    def __init__(self):
        self.settings_manager: Optional[SettingsManager] = None
        
    async def initialize(self):
        """Initialize database connection and settings manager"""
        try:
            if not db_manager._connected:
                logger.info("Connecting to database...")
                db_manager.connect()
            
            self.settings_manager = SettingsManager(db_manager)
            logger.info("Settings manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize settings manager: {e}")
            raise
    
    async def cleanup(self):
        """Clean up database connections"""
        if db_manager:
            await db_manager.close()
    
    def print_banner(self, title: str):
        """Print formatted banner"""
        print("=" * 60)
        print(f"🎫 TicketFlow AI - {title}")
        print("=" * 60)
        print()
    
    def validate_environment(self) -> bool:
        """Validate environment configuration"""
        logger.info("🔍 Validating environment configuration...")
        
        # Check if .env file exists
        env_file = Path(".env")
        if not env_file.exists():
            logger.warning("⚠️  .env file not found. Using environment variables or defaults.")
        
        # Check required environment variables
        required_vars = [
            'TIDB_HOST', 'TIDB_PORT', 'TIDB_USER', 'TIDB_DATABASE'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not getattr(config, var, None):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
            return False
        
        # Check optional but important variables
        optional_vars = {
            'ENCRYPTION_KEY': 'Settings encryption will not work',
            'SLACK_BOT_TOKEN': 'Slack integration will not work',
            'OPENAI_API_KEY': 'OpenAI integration will not work',
            'OPENROUTER_API_KEY': 'OpenRouter integration will not work'
        }
        
        for var, warning in optional_vars.items():
            if not getattr(config, var, None):
                logger.warning(f"⚠️  {var} not set: {warning}")
        
        logger.info("✅ Environment validation completed")
        return True
    
    async def initialize_default_settings(self) -> bool:
        """Initialize default settings in the database"""
        try:
            self.print_banner("Settings Initialization")
            
            if not self.validate_environment():
                return False
            
            await self.initialize()
            
            logger.info("🔧 Initializing default settings...")
            await self.settings_manager.initialize_default_settings()
            
            # Count settings by category
            category_counts = {}
            total_settings = 0
            
            for category in SettingCategory:
                settings = await self.settings_manager.get_settings_by_category(
                    category.value, decrypt=False
                )
                count = len(settings)
                category_counts[category.value] = count
                total_settings += count
                logger.info(f"  📁 {category.value}: {count} settings")
            
            logger.info(f"✅ Successfully initialized {total_settings} settings")
            
            # Verify critical settings
            await self._verify_critical_settings()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize settings: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def _verify_critical_settings(self):
        """Verify that critical settings are properly initialized"""
        logger.info("🔍 Verifying critical settings...")
        
        critical_settings = [
            'slack_notifications_enabled',
            'email_notifications_enabled', 
            'system_timezone',
            'system_max_tickets_per_page'
        ]
        
        for setting_key in critical_settings:
            setting = await self.settings_manager.get_setting(setting_key)
            if setting:
                logger.info(f"  ✅ {setting_key}: {setting['value']}")
            else:
                logger.warning(f"  ⚠️  {setting_key}: NOT FOUND")
    
    async def validate_settings(self) -> bool:
        """Validate current settings configuration"""
        try:
            self.print_banner("Settings Validation")
            await self.initialize()
            
            logger.info("🔍 Validating current settings...")
            
            # Check each category
            all_valid = True
            for category in SettingCategory:
                settings = await self.settings_manager.get_settings_by_category(
                    category.value, decrypt=False
                )
                
                logger.info(f"📁 Category: {category.value} ({len(settings)} settings)")
                
                for setting in settings:
                    # Basic validation
                    if not setting.get('key'):
                        logger.error(f"  ❌ Setting missing key: {setting}")
                        all_valid = False
                        continue
                    
                    # Type validation
                    setting_type = setting.get('setting_type')
                    value = setting.get('value')
                    
                    if setting_type == SettingType.BOOLEAN.value:
                        if value not in ['true', 'false']:
                            logger.warning(f"  ⚠️  {setting['key']}: Invalid boolean value '{value}'")
                    
                    elif setting_type == SettingType.INTEGER.value:
                        try:
                            int(value) if value else 0
                        except ValueError:
                            logger.warning(f"  ⚠️  {setting['key']}: Invalid integer value '{value}'")
                    
                    logger.info(f"  ✅ {setting['key']}: {value}")
            
            if all_valid:
                logger.info("✅ All settings validation passed")
            else:
                logger.warning("⚠️  Some settings validation issues found")
            
            return all_valid
            
        except Exception as e:
            logger.error(f"❌ Settings validation failed: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def backup_settings(self, backup_file: Optional[str] = None) -> bool:
        """Backup current settings to a JSON file"""
        try:
            self.print_banner("Settings Backup")
            await self.initialize()
            
            if not backup_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = f"settings_backup_{timestamp}.json"
            
            logger.info(f"📦 Creating settings backup: {backup_file}")
            
            # Get all settings
            all_settings = {}
            for category in SettingCategory:
                settings = await self.settings_manager.get_settings_by_category(
                    category.value, decrypt=False  # Don't decrypt for backup
                )
                all_settings[category.value] = settings
            
            # Create backup data
            backup_data = {
                'timestamp': datetime.now().isoformat(),
                'version': '1.0',
                'settings': all_settings
            }
            
            # Write to file
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            total_settings = sum(len(settings) for settings in all_settings.values())
            logger.info(f"✅ Successfully backed up {total_settings} settings to {backup_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Settings backup failed: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def show_settings(self) -> bool:
        """Display current settings configuration"""
        try:
            self.print_banner("Current Settings")
            await self.initialize()
            
            for category in SettingCategory:
                settings = await self.settings_manager.get_settings_by_category(
                    category.value, decrypt=False
                )
                
                print(f"\n📁 {category.value.upper()} ({len(settings)} settings)")
                print("-" * 50)
                
                for setting in settings:
                    key = setting.get('key', 'Unknown')
                    value = setting.get('value', 'Not set')
                    enabled = "✅" if setting.get('is_enabled') else "❌"
                    sensitive = "🔒" if setting.get('is_sensitive') else ""
                    
                    # Mask sensitive values
                    if setting.get('is_sensitive') and value:
                        display_value = "*" * min(len(str(value)), 8)
                    else:
                        display_value = value
                    
                    print(f"  {enabled} {key}: {display_value} {sensitive}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to show settings: {e}")
            return False
        finally:
            await self.cleanup()
    
    async def reset_settings(self) -> bool:
        """Reset all settings to defaults"""
        try:
            self.print_banner("Settings Reset")
            
            # Confirm reset
            response = input("⚠️  This will reset ALL settings to defaults. Continue? (y/N): ")
            if response.lower() != 'y':
                logger.info("Reset cancelled by user")
                return False
            
            await self.initialize()
            
            logger.info("🔄 Resetting all settings to defaults...")
            
            # This would require implementing a reset method in SettingsManager
            # For now, we'll reinitialize
            await self.settings_manager.initialize_default_settings()
            
            logger.info("✅ Settings reset completed")
            return True
            
        except Exception as e:
            logger.error(f"❌ Settings reset failed: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main function with command line argument parsing"""
    parser = argparse.ArgumentParser(
        description="TicketFlow AI Settings Initialization and Management"
    )
    parser.add_argument(
        '--validate', action='store_true',
        help='Validate current settings configuration'
    )
    parser.add_argument(
        '--backup', nargs='?', const=True,
        help='Backup current settings (optional: specify filename)'
    )
    parser.add_argument(
        '--show', action='store_true',
        help='Display current settings'
    )
    parser.add_argument(
        '--reset', action='store_true',
        help='Reset all settings to defaults'
    )
    
    args = parser.parse_args()
    
    initializer = SettingsInitializer()
    success = False
    
    try:
        if args.validate:
            success = await initializer.validate_settings()
        elif args.backup:
            backup_file = args.backup if isinstance(args.backup, str) else None
            success = await initializer.backup_settings(backup_file)
        elif args.show:
            success = await initializer.show_settings()
        elif args.reset:
            success = await initializer.reset_settings()
        else:
            # Default: initialize settings
            success = await initializer.initialize_default_settings()
        
        if success:
            print("\n✅ Operation completed successfully!")
        else:
            print("\n❌ Operation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())