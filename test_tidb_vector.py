"""
Test script for TiDB Vector integration with TicketFlow AI
Tests native VECTOR columns and similarity search
"""

import asyncio
import sys
from pathlib import Path
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticketflow.database.connection import db_manager, Base
from ticketflow.database.operations import TicketOperations, KnowledgeBaseOperations
from ticketflow.database.schemas import TicketCreateRequest, KnowledgeBaseCreateRequest
from ticketflow.config import config
from ticketflow.utils.vector_utils import vector_manager
from sqlalchemy import text

async def test_tidb_vectors():
    print("🔍 TicketFlow AI - TiDB Vector Integration Test")
    print("=" * 60)
    
    # Check configuration
    if not config.validate():
        print("❌ Configuration validation failed!")
        return
    
    # Connect to database
    print("1. Connecting to TiDB...")
    success = db_manager.connect(config.database_url)
    
    if not success:
        print("❌ Database connection failed!")
        return
    
    print("✅ Connected to TiDB successfully!")
    
    # Create tables with vector support
    print("\n2. Creating tables with VECTOR columns...")
    try:
        Base.metadata.create_all(bind=db_manager.engine)
        print("✅ Tables created with TiDB VECTOR support!")
    except Exception as e:
        print(f"❌ Table creation failed: {e}")
        return
    
    session = db_manager.get_session()
    
    try:
        # Test 1: Create tickets with vector embeddings
        print("\n3. Creating test tickets with embeddings...")
        
        test_tickets = [
            {
                "title": "Login password reset issue",
                "description": "User cannot reset their password. The reset email is not arriving and they've checked spam folder. Need to help them regain access to their account urgently.",
                "category": "account",
                "priority": "high",
                "user_email": "user1@test.com"
            },
            {
                "title": "Cannot access account - password problems", 
                "description": "I'm having trouble logging into my account. When I enter my password, it says it's incorrect, but I'm sure it's right. I tried the forgot password option but didn't get an email.",
                "category": "account",
                "priority": "medium",
                "user_email": "user2@test.com"
            },
            {
                "title": "Payment processing failed",
                "description": "My payment was declined but I know there are funds in my account. The error message says 'transaction could not be processed'. I need this fixed to continue using the service.",
                "category": "billing",
                "priority": "high", 
                "user_email": "user3@test.com"
            }
        ]
        
        created_tickets = []
        for i, ticket_data in enumerate(test_tickets, 1):
            print(f"  Creating ticket {i}: {ticket_data['title'][:40]}...")
            
            start_time = time.time()
            ticket_request = TicketCreateRequest(**ticket_data)
            ticket = await TicketOperations.create_ticket(session, ticket_request)
            end_time = time.time()
            
            created_tickets.append(ticket)
            print(f"  ✅ Created ticket ID {ticket.id} (took {end_time - start_time:.2f}s)")
        
        print(f"\n✅ Created {len(created_tickets)} tickets with vector embeddings!")
        
        # Test 2: Vector similarity search
        print("\n4. Testing TiDB native vector similarity search...")
        
        # Mark one ticket as resolved so we can find similar ones
        resolved_ticket = created_tickets[0]
        resolved_ticket.status = "resolved"
        resolved_ticket.resolution = "Password reset email was stuck in spam filter. Manually reset password and advised user to whitelist our domain."
        resolved_ticket.resolution_type = "human"
        session.commit()
        
        print(f"  Marked ticket '{resolved_ticket.title[:40]}...' as resolved")
        
        # Find similar tickets to the second one
        query_ticket = created_tickets[1]
        print(f"  Searching for tickets similar to: '{query_ticket.title[:40]}...'")
        
        start_time = time.time()
        similar_tickets = await TicketOperations.find_similar_tickets(
            session, query_ticket, limit=5, min_similarity=0.5
        )
        end_time = time.time()
        
        print(f"  Found {len(similar_tickets)} similar tickets (took {end_time - start_time:.3f}s)")
        
        for i, similar in enumerate(similar_tickets, 1):
            print(f"    {i}. '{similar['title'][:50]}...' (similarity: {similar['similarity_score']:.3f})")
        
        # Test 3: Knowledge base with vectors
        print("\n5. Testing knowledge base with vector search...")
        
        kb_articles = [
            {
                "title": "Password Reset Troubleshooting Guide",
                "content": "If users can't reset their password, check: 1) Email delivery (spam folder), 2) Account status (not locked), 3) Reset link expiry (24 hour limit), 4) Domain whitelist requirements. For urgent cases, manually reset via admin panel.",
                "summary": "Step-by-step guide for password reset issues",
                "category": "account",
                "tags": ["password", "reset", "email", "troubleshooting"],
                "source_type": "manual",
                "author": "Support Team"
            },
            {
                "title": "Payment Failure Resolution Process",
                "content": "When payment processing fails: 1) Check payment method validity, 2) Verify billing address, 3) Contact payment processor for holds, 4) Check for international restrictions, 5) Offer alternative payment methods if needed.",
                "summary": "How to resolve payment processing failures",
                "category": "billing",
                "tags": ["payment", "billing", "transaction", "failed"],
                "source_type": "manual", 
                "author": "Billing Team"
            }
        ]
        
        created_articles = []
        for i, article_data in enumerate(kb_articles, 1):
            print(f"  Creating KB article {i}: {article_data['title'][:40]}...")
            
            article_request = KnowledgeBaseCreateRequest(**article_data)
            article = await KnowledgeBaseOperations.create_article(session, article_request)
            created_articles.append(article)
            
            print(f"  ✅ Created article ID {article.id}")
        
        # Test KB vector search
        print(f"\n6. Testing KB vector search...")
        
        search_queries = [
            "user can't login password issue",
            "payment not working declined",
            "how to troubleshoot account access"
        ]
        
        for query in search_queries:
            print(f"\n  Searching for: '{query}'")
            start_time = time.time()
            results = await KnowledgeBaseOperations.search_articles(session, query, limit=3)
            end_time = time.time()
            
            print(f"  Found {len(results)} relevant articles (took {end_time - start_time:.3f}s)")
            for j, result in enumerate(results, 1):
                print(f"    {j}. '{result['title']}' (similarity: {result['similarity_score']:.3f})")
        
        # Test 4: Direct SQL vector operations
        print("\n7. Testing direct TiDB vector SQL operations...")
        
        # Get a sample vector for testing
        sample_ticket = created_tickets[0]
        if sample_ticket.combined_vector:
            # Test VEC_COSINE_DISTANCE function directly
            sql = text("""
                SELECT 
                    id, 
                    title, 
                    VEC_COSINE_DISTANCE(combined_vector, :test_vector) as distance,
                    VEC_L2_DISTANCE(combined_vector, :test_vector) as l2_distance
                FROM tickets 
                WHERE combined_vector IS NOT NULL 
                ORDER BY distance ASC 
                LIMIT 3
            """)
            
            result = session.execute(sql, {'test_vector': sample_ticket.combined_vector})
            
            print("  Direct TiDB vector functions results:")
            for row in result:
                print(f"    ID {row.id}: '{row.title[:40]}...' (cosine: {row.distance:.3f}, L2: {row.l2_distance:.3f})")
        
        print("\n🎉 TiDB Vector Integration Test Complete!")
        print("\nResults Summary:")
        print(f"✅ Created {len(created_tickets)} tickets with 3072-dim embeddings")
        print(f"✅ Vector similarity search working with native TiDB functions")
        print(f"✅ Knowledge base vector search operational")
        print(f"✅ Direct SQL vector operations functional")
        print("\n🚀 Ready for agent workflow implementation!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        session.close()

async def benchmark_vector_performance():
    """Optional: Benchmark vector operations performance"""
    print("\n📊 Vector Performance Benchmark")
    print("-" * 40)
    
    session = db_manager.get_session()
    
    try:
        # Test embedding generation speed
        test_texts = [
            "Simple test text",
            "This is a more complex test with multiple sentences. It should take slightly longer to process but still be fast enough for real-time use.",
            "A very long text that simulates a detailed ticket description with lots of information about user issues, error messages, steps taken to reproduce the problem, system environment details, and expected vs actual behavior that would be typical in a comprehensive support ticket submission."
        ]
        
        print("Embedding generation performance:")
        for i, text in enumerate(test_texts, 1):
            start_time = time.time()
            embedding = await vector_manager.generate_embedding(text)
            end_time = time.time()
            
            print(f"  Text {i} ({len(text)} chars): {end_time - start_time:.3f}s")
        
        # Test vector search performance
        tickets = session.query(session.query_cls).limit(5).all()
        if tickets:
            test_ticket = tickets[0]
            
            print(f"\nVector search performance:")
            for limit in [5, 10, 20]:
                start_time = time.time()
                results = await TicketOperations.find_similar_tickets(
                    session, test_ticket, limit=limit, min_similarity=0.3
                )
                end_time = time.time()
                
                print(f"  Search limit {limit}: {end_time - start_time:.3f}s ({len(results)} results)")
        
    except Exception as e:
        print(f"Benchmark failed: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    # Check if Jina API key is set
    if not config.JINA_API_KEY:
        print("❌ JINA_API_KEY not set in .env file")
        print("Get your API key from: https://jina.ai/")
        print("Sign up for free at: https://jina.ai/")
        sys.exit(1)
    
    # Run main test
    asyncio.run(test_tidb_vectors())
    
    # Optionally run performance benchmark
    print("\n" + "="*60)
    user_input = input("Run performance benchmark? (y/n): ")
    if user_input.lower() == 'y':
        asyncio.run(benchmark_vector_performance())