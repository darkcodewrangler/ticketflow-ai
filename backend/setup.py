#!/usr/bin/env python3
"""
TicketFlow AI Setup Script

This script sets up the entire TicketFlow AI project by:
1. Validating environment configuration
2. Initializing database and creating tables
3. Setting up default settings
4. Creating sample data for testing/demo
5. Verifying the setup

Run this script once before starting the API server with run_api.py
"""

import asyncio
import sys
import os
from pathlib import Path
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ticketflow.config import config
from ticketflow.database.connection import db_manager
from ticketflow.database.settings_manager import SettingsManager
from ticketflow.database.operations import TicketOperations, KnowledgeBaseOperations
from ticketflow.database.schemas import TicketCreateRequest, KnowledgeBaseCreateRequest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("🎫 TicketFlow AI - Project Setup")
    print("=" * 60)
    print()

def validate_environment():
    """Validate environment configuration"""
    logger.info("🔍 Validating environment configuration...")
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        logger.error(".env file not found!")
        logger.info("📝 Please create a .env file with the required environment variables.")
        logger.info("   See .env.example or README.md for required variables.")
        return False
    
    # Validate configuration
    if not config.validate():
        logger.error(" Environment configuration validation failed!")
        logger.info("📝 Please check your .env file and ensure all required variables are set.")
        return False
    
    logger.info("✅ Environment configuration is valid")
    return True

async def initialize_database():
    """Initialize database and create tables"""
    logger.info("🗄️  Initializing database...")
    
    try:
        # Connect to database
        logger.info("   Connecting to database...")
        if not db_manager.connect():
            logger.error("❌ Failed to connect to database")
            return False
        # Drop existing database (if any)
        if db_manager.drop_db():
            print("  Dropped existing database (if any)")
    
        # Create new database
        if db_manager.create_db():
            print("  Created new database")
        
        # Initialize tables
        logger.info("   Creating database tables...")
        if not db_manager.initialize_tables(drop_existing=True):
            logger.error("❌ Failed to initialize database tables")
            return False
        
        logger.info("✅ Database initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        return False

async def initialize_settings():
    """Initialize default settings"""
    logger.info("⚙️  Initializing default settings...")
    
    try:
        # Initialize settings manager
        settings_manager = SettingsManager(db_manager, config.ENCRYPTION_KEY)
        
        # Initialize default settings
        logger.info("   Creating default settings...")
        settings_manager.initialize_default_settings()
        
        # Verify critical settings
        critical_settings = [
            'slack_notifications_enabled',
            'email_notifications_enabled', 
            'system_timezone'
        ]
        
        logger.info("   Verifying critical settings...")
        for setting_key in critical_settings:
            setting = settings_manager.get_setting(setting_key)
            if setting:
                logger.info(f"     ✓ {setting_key}: {setting['value']}")
            else:
                logger.warning(f"     ⚠️  {setting_key}: not found")
        
        logger.info("✅ Settings initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Settings initialization failed: {e}")
        return False

async def create_sample_data():
    """Create sample tickets and knowledge base articles"""
    logger.info("📝 Creating sample data...")
    
    try:
        # Sample tickets
        sample_tickets = [
            {
                "title": "Cannot login to my account",
                "description": "I'm trying to log into my account but it keeps saying my password is wrong. I've tried resetting it twice but still can't get in.",
                "category": "account",
                "priority": "high",
                "user_email": "john.doe@example.com"
            },
            {
                "title": "Payment processing error",
                "description": "When I try to make a payment, I get an error message saying 'Transaction failed - please try again later'.",
                "category": "billing", 
                "priority": "medium",
                "user_email": "sarah.smith@example.com"
            },
            {
                "title": "API integration not working",
                "description": "I'm trying to integrate your API with our system but I'm getting 403 forbidden errors on all endpoints.",
                "category": "technical",
                "priority": "high", 
                "user_email": "dev@techcorp.com"
            }
        ]
        
        # Sample knowledge base articles
        sample_kb_articles = [
            {
                "title": "How to Reset Your Password",
                "content": "If you're having trouble logging into your account, you can reset your password by following these steps:\n\n1. Go to the login page\n2. Click 'Forgot Password' link\n3. Enter your email address\n4. Check your email for reset link\n5. Click the link and create a new password",
                "summary": "Step-by-step guide to reset forgotten passwords",
                "category": "account",
                "tags": ["password", "reset", "login", "account"],
                "source_type": "manual",
                "author": "Support Team"
            },
            {
                "title": "Payment Processing Troubleshooting", 
                "content": "Common payment issues and solutions:\n\n**Transaction Failed Error:**\n- Verify card details are correct\n- Check if card has sufficient funds\n- Try a different payment method\n- Clear browser cache and cookies",
                "summary": "Solutions for common payment processing errors",
                "category": "billing",
                "tags": ["payment", "billing", "transaction", "error"],
                "source_type": "manual",
                "author": "Billing Team"
            }
        ]
        
        # Create tickets
        ticket_ops = TicketOperations()
        logger.info(f"   Creating {len(sample_tickets)} sample tickets...")
        
        for ticket_data in sample_tickets:
            ticket_request = TicketCreateRequest(**ticket_data)
            ticket =  ticket_ops.create_ticket(ticket_request)
            if ticket:
                logger.info(f"     ✓ Created ticket: {ticket['title']}")
            else:
                logger.warning(f"     ⚠️  Failed to create ticket: {ticket_data['title']}")
        
        # Create knowledge base articles
        kb_ops = KnowledgeBaseOperations()
        logger.info(f"   Creating {len(sample_kb_articles)} sample KB articles...")
        
        for kb_data in sample_kb_articles:
            kb_request = KnowledgeBaseCreateRequest(**kb_data)
            article = kb_ops.create_article(kb_request)
            if article:
                logger.info(f"     ✓ Created KB article: {article['title']}")
            else:
                logger.warning(f"     ⚠️  Failed to create KB article: {kb_data['title']}")
        
        logger.info("✅ Sample data created successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Sample data creation failed: {e}")
        return False

async def verify_setup():
    """Verify that setup completed successfully"""
    logger.info("🔍 Verifying setup...")
    
    try:
        # Check database connection
        if not db_manager._connected:
            logger.error("❌ Database not connected")
            return False
        
        # Check settings
        settings_manager = SettingsManager(db_manager, config.ENCRYPTION_KEY)
        settings = await settings_manager.get_settings_by_category('system', decrypt=False)
        logger.info(f"   ✓ Found {len(settings)} system settings")
        
        # Check tickets
        ticket_ops = TicketOperations(db_manager)
        tickets = await ticket_ops.get_tickets(limit=10)
        logger.info(f"   ✓ Found {len(tickets)} sample tickets")
        
        # Check knowledge base
        kb_ops = KnowledgeBaseOperations(db_manager)
        articles = await kb_ops.get_articles(limit=10)
        logger.info(f"   ✓ Found {len(articles)} KB articles")
        
        logger.info("✅ Setup verification completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"❌ Setup verification failed: {e}")
        return False

def print_success_message():
    """Print success message with next steps"""
    print()
    print("=" * 60)
    print("🎉 TicketFlow AI Setup Complete!")
    print("=" * 60)
    print()
    print("✅ Database initialized")
    print("✅ Settings configured")
    print("✅ Sample data created")
    print("✅ Setup verified")
    print()
    print("🚀 Next Steps:")
    print("   1. Run the API server: python run_api.py")
    print("   2. Open your browser to: http://localhost:8000")
    print("   3. View API docs at: http://localhost:8000/docs")
    print()
    print("📚 For more information, see README.md")
    print("=" * 60)

async def main():
    """Main setup function"""
    print_banner()
    
    try:
        # Step 1: Validate environment
        if not validate_environment():
            sys.exit(1)
        
        # Step 2: Initialize database
        if not await initialize_database():
            sys.exit(1)
        
        # Step 3: Initialize settings
        if not await initialize_settings():
            sys.exit(1)
        
        # Step 4: Create sample data
        if not await create_sample_data():
            sys.exit(1)
        
        # Step 5: Verify setup
        if not await verify_setup():
            sys.exit(1)
        
        # Success!
        print_success_message()
        
    except KeyboardInterrupt:
        logger.info("\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Setup failed with unexpected error: {e}")
        sys.exit(1)
    finally:
        # Clean up database connection
        if db_manager and db_manager._connected:
            await db_manager.close()

if __name__ == "__main__":
    asyncio.run(main())