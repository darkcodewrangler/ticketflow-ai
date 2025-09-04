"""
Test script to verify database setup
"""

import asyncio
import sys
from pathlib import Path

# Add src to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticketflow.database.connection import db_manager, Base
from ticketflow.database.models import Ticket, KnowledgeBaseArticle, AgentWorkflow
from ticketflow.database.schemas import TicketCreateRequest
from ticketflow.config import config

async def test_database():
    print("🎫 TicketFlow AI - Database Test")
    print("=" * 50)
    
    # Test connection
    print("1. Testing database connection...")
    success = db_manager.connect(config.database_url)
    
    if not success:
        print("❌ Database connection failed!")
        print("Check your .env file and TiDB credentials")
        return
    
    print("✅ Database connected successfully!")
    
    # Test table creation
    print("\n2. Creating database tables...")
    try:
        Base.metadata.create_all(bind=db_manager.engine)
        print("✅ Tables created successfully!")
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return
    
    # Test basic operations
    print("\n3. Testing basic database operations...")
    session = db_manager.get_session()
    
    try:
        # Create a test ticket
        test_ticket = Ticket(
            title="Database Test Ticket",
            description="This is a test ticket to verify database operations work correctly.",
            category="technical",
            priority="medium",
            user_id="test_user",
            user_email="test@example.com"
        )
        
        session.add(test_ticket)
        session.commit()
        session.refresh(test_ticket)
        
        print(f"✅ Created ticket with ID: {test_ticket.id}")
        
        # Query the ticket back
        retrieved_ticket = session.query(Ticket).filter(Ticket.id == test_ticket.id).first()
        
        if retrieved_ticket:
            print(f"✅ Retrieved ticket: '{retrieved_ticket.title}'")
        else:
            print("❌ Failed to retrieve ticket")
            
        # Clean up test data
        session.delete(retrieved_ticket)
        session.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Database operation failed: {e}")
        session.rollback()
    finally:
        session.close()
    
    print("\n🎉 Database setup complete and working!")

if __name__ == "__main__":
    asyncio.run(test_database())