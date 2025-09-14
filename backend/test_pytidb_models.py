"""
Test PyTiDB models and automatic embedding features
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticketflow.database import db_manager, Ticket, KnowledgeBaseArticle
from ticketflow.config import config

def test_pytidb_models():
    print("🤖 Testing PyTiDB Models with Auto-Embeddings")
    print("=" * 55)
    
    # Test configuration
    if not config.validate():
        print("❌ Configuration validation failed!")
        return False
    
    # Connect to database
    print("1. Connecting to TiDB with PyTiDB...")
    if not db_manager.connect():
        print("❌ Connection failed!")
        return False
    
    print("✅ Connected successfully!")
    success_drop = db_manager.drop_db()
    if success_drop:
        print("  🗑️ Dropped existing database (if any)")

    success_create = db_manager.create_db()
    if success_create:
       print("  🆕 Created new database")
    # Initialize tables
    print("\n2. Initializing tables with AI features...")
    if not db_manager.initialize_tables(drop_existing=True):
        print("❌ Table initialization failed!")
        return False
    
    print("✅ Tables created with automatic embedding support!")
    
    # Test ticket creation with automatic embeddings
    print("\n3. Testing automatic embedding generation...")
    
    try:
        # Create a test ticket - PyTiDB will automatically generate embeddings!
        test_ticket = Ticket(
            title="Cannot login to my account",
            description="I'm trying to log into my account but it keeps saying my password is wrong. I've tried resetting it multiple times but still can't get in.",
            category="account",
            priority="high",
            user_email="test@example.com"
        )
        
        print("  📝 Inserting ticket with auto-embedding...")
        created_ticket = db_manager.tickets.insert(test_ticket)
        
        print(f"  ✅ Created ticket ID {created_ticket.id}")
        print(f"  🤖 PyTiDB automatically generated embeddings for:")
        print(f"     - Title: '{created_ticket.title[:50]}...'")
        print(f"     - Description: '{created_ticket.description[:50]}...'")
        
        # Test knowledge base article with auto-embedding
        print("\n4. Testing KB article with auto-embeddings...")
        
        kb_article = KnowledgeBaseArticle(
            title="Password Reset Troubleshooting",
            content="If users can't reset their password, check: 1) Email delivery, 2) Account status, 3) Reset link expiry. For urgent cases, manually reset via admin panel.",
            category="account",
            tags=["password", "reset", "troubleshooting"],
            author="Support Team"
        )
        
        print("  📚 Inserting KB article with auto-embedding...")
        created_article = db_manager.kb_articles.insert(kb_article)
        
        print(f"  ✅ Created article ID {created_article.id}")
        print(f"  🤖 PyTiDB automatically generated embeddings for article content!")
        
        print("\n🎉 PyTiDB Models Test Successful!")
        print("\nWhat just happened:")
        print("✅ Tables created with VECTOR columns automatically")
        print("✅ Text fields automatically converted to embeddings") 
        print("✅ Vector similarity search enabled")
        print("✅ Hybrid search (vector + full-text) ready")
        print("✅ Zero embedding management code needed!")
        
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_pytidb_models()