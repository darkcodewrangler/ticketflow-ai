#!/usr/bin/env python3
"""
Database Settings Initialization Script

This script initializes the settings table and populates it with default settings.
Run this script after setting up the database to ensure all required settings are available.
"""

import asyncio
import logging
from typing import Optional

from ticketflow.database.connection import db_manager
from ticketflow.database.settings_manager import SettingsManager
from ticketflow.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def initialize_settings_table(encryption_key: Optional[str] = None) -> bool:
    """
    Initialize the settings table and populate with default settings.
    
    Args:
        encryption_key: Optional encryption key for sensitive settings
        
    Returns:
        True if initialization successful, False otherwise
    """
    try:
        # Ensure database connection
        if not db_manager._connected:
            logger.info("Connecting to database...")
            db_manager.connect()
        
        # Initialize database tables (this will create the settings table)
        logger.info("Initializing database tables...")
        await db_manager.initialize_tables()
        
        # Initialize settings manager
        logger.info("Initializing settings manager...")
        settings_manager = SettingsManager(db_manager, encryption_key)
        
        # Initialize default settings
        logger.info("Populating default settings...")
        await settings_manager.initialize_default_settings()
        
        logger.info("Settings initialization completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize settings: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close()

async def verify_settings_initialization() -> bool:
    """
    Verify that settings have been initialized correctly.
    
    Returns:
        True if verification successful, False otherwise
    """
    try:
        # Ensure database connection
        if not db_manager._connected:
            logger.info("Connecting to database for verification...")
            db_manager.connect()
        
        settings_manager = SettingsManager(db_manager)
        
        # Check critical settings
        critical_settings = [
            'slack_notifications_enabled',
            'email_notifications_enabled',
            'slack_new_ticket_channel',
            'system_timezone'
        ]
        
        logger.info("Verifying critical settings...")
        for setting_key in critical_settings:
            setting = await settings_manager.get_setting(setting_key)
            if setting:
                logger.info(f"{setting_key}: {setting['value']} (enabled: {setting['is_enabled']})")
            else:
                logger.error(f"{setting_key}: NOT FOUND")
                return False
        
        # Check settings by category
        categories = ['slack', 'email', 'system', 'agent']
        for category in categories:
            settings = await settings_manager.get_settings_by_category(category, decrypt=False)
            logger.info(f"Category '{category}': {len(settings)} settings")
        
        logger.info("Settings verification completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Failed to verify settings: {e}")
        return False
    finally:
        if db_manager:
            await db_manager.close()

async def main():
    """
    Main function to run settings initialization.
    """
    logger.info("Starting settings initialization...")
    
    # Initialize settings
    success = await initialize_settings_table()
    if not success:
        logger.error("Settings initialization failed!")
        return
    
    # Verify initialization
    success = await verify_settings_initialization()
    if not success:
        logger.error("Settings verification failed!")
        return
    
    logger.info("Settings initialization and verification completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())