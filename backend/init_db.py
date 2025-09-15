#!/usr/bin/env python3
"""
Database initialization script
"""

import asyncio
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.ticketflow.database.connection import db_manager

def init_database():
    """Initialize database tables"""
    try:
        print("Connecting to database...")
        if not db_manager.connect():
            print("Failed to connect to database")
            return False
        
        print("Initializing database tables...")
        if not db_manager.initialize_tables():
            print("Failed to initialize tables")
            return False
        
        print("Database tables initialized successfully!")
        
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False
    finally:
        db_manager.close()
    
    return True

if __name__ == "__main__":
    success = init_database()
    sys.exit(0 if success else 1)