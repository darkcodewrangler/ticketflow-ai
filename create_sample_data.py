"""
Create sample data for TicketFlow AI testing and demos
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticketflow.database.connection import db_manager
from ticketflow.database.operations import TicketOperations, KnowledgeBaseOperations
from ticketflow.database.schemas import TicketCreateRequest, KnowledgeBaseCreateRequest
from ticketflow.config import config

# Sample ticket data
SAMPLE_TICKETS = [
    {
        "title": "Cannot login to my account",
        "description": "I'm trying to log into my account but it keeps saying my password is wrong. I've tried resetting it twice but still can't get in. This is urgent as I need to access my data for a presentation tomorrow.",
        "category": "account",
        "priority": "high",
        "user_email": "john.doe@example.com"
    },
    {
        "title": "Payment processing error", 
        "description": "When I try to make a payment, I get an error message saying 'Transaction failed - please try again later'. I've tried different cards and browsers but same issue.",
        "category": "billing",
        "priority": "medium",
        "user_email": "sarah.smith@example.com"
    },
    {
        "title": "API integration not working",
        "description": "I'm trying to integrate your API with our system but I'm getting 403 forbidden errors on all endpoints. My API key seems to be correct. Can you help troubleshoot this?",
        "category": "technical",
        "priority": "high",
        "user_email": "dev@techcorp.com"
    },
    {
        "title": "Mobile app crashes on startup",
        "description": "The mobile app crashes immediately after opening on my iPhone 14. I've tried restarting my phone and reinstalling the app but no luck. Other users in my team are experiencing the same issue.",
        "category": "technical",
        "priority": "urgent",
        "user_email": "mobile.user@company.com"
    },
    {
        "title": "Billing invoice question",
        "description": "I received my monthly invoice but there are charges I don't recognize. Can someone explain what 'Premium API calls - overage' means? I thought I was on unlimited plan.",
        "category": "billing",
        "priority": "low",
        "user_email": "accounting@business.com"
    }
]

# Sample knowledge base articles
SAMPLE_KB_ARTICLES = [
    {
        "title": "How to Reset Your Password",
        "content": "If you're having trouble logging into your account, you can reset your password by following these steps:\n\n1. Go to the login page\n2. Click 'Forgot Password' link\n3. Enter your email address\n4. Check your email for reset link\n5. Click the link and create a new password\n\nIf you don't receive the email, check your spam folder. The reset link expires after 24 hours for security.",
        "summary": "Step-by-step guide to reset forgotten passwords",
        "category": "account",
        "tags": ["password", "reset", "login", "account"],
        "source_type": "manual",
        "author": "Support Team"
    },
    {
        "title": "Payment Processing Troubleshooting",
        "content": "Common payment issues and solutions:\n\n**Transaction Failed Error:**\n- Verify card details are correct\n- Check if card has sufficient funds\n- Try a different payment method\n- Clear browser cache and cookies\n\n**403 Forbidden:**\n- Check if your account has payment permissions\n- Verify billing address matches card\n- Contact your bank to ensure they're not blocking the transaction\n\nIf issues persist, contact our billing team with your transaction ID.",
        "summary": "Solutions for common payment processing errors",
        "category": "billing", 
        "tags": ["payment", "billing", "transaction", "error"],
        "source_type": "manual",
        "author": "Billing Team"
    },
    {
        "title": "API Authentication Guide",
        "content": "To authenticate with our API:\n\n1. **Get your API Key:**\n   - Login to your dashboard\n   - Go to Settings > API Keys\n   - Generate a new key if needed\n\n2. **Include in requests:**\n   - Header: `Authorization: Bearer YOUR_API_KEY`\n   - Or query parameter: `?api_key=YOUR_API_KEY`\n\n**Common 403 errors:**\n- API key is invalid or expired\n- Account has insufficient permissions\n- Rate limits exceeded\n- IP not whitelisted (if applicable)\n\nAPI keys are case-sensitive and must be kept secure.",
        "summary": "How to authenticate API requests and fix 403 errors",
        "category": "technical",
        "tags": ["api", "authentication", "403", "forbidden", "key"],
        "source_type": "manual",
        "author": "Dev Team"
    }
]

async def create_sample_data():
    print("🎫 Creating Sample Data for TicketFlow AI")
    print("=" * 50)
    
    # Connect to database
    if not db_manager.connect(config.database_url):
        print("❌ Database connection failed!")
        return
    
    session = db_manager.get_session()
    
    try:
        # Create sample tickets
        print("📝 Creating sample tickets...")
        created_tickets = []
        
        for i, ticket_data in enumerate(SAMPLE_TICKETS, 1):
            print(f"Creating ticket {i}: {ticket_data['title'][:50]}...")
            
            ticket_request = TicketCreateRequest(**ticket_data)
            ticket = await TicketOperations.create_ticket(session, ticket_request)
            created_tickets.append(ticket)
            
            print(f"✅ Created ticket ID {ticket.id}")
        
        print(f"\n✅ Created {len(created_tickets)} sample tickets!")
        
        # Create sample KB articles
        print("\n📚 Creating knowledge base articles...")
        created_articles = []
        
        for i, article_data in enumerate(SAMPLE_KB_ARTICLES, 1):
            print(f"Creating article {i}: {article_data['title'][:50]}...")
            
            article_request = KnowledgeBaseCreateRequest(**article_data)
            article = await KnowledgeBaseOperations.create_article(session, article_request)
            created_articles.append(article)
            
            print(f"✅ Created article ID {article.id}")
        
        print(f"\n✅ Created {len(created_articles)} knowledge base articles!")
        
        # Test vector search
        print("\n🔍 Testing vector search...")
        test_ticket = created_tickets[0]  # Use first ticket
        similar_tickets = await TicketOperations.find_similar_tickets(session, test_ticket)
        
        print(f"Similar tickets to '{test_ticket.title}':")
        for similar in similar_tickets[:3]:
            print(f"  - {similar['title'][:50]}... (similarity: {similar['similarity_score']:.3f})")
        
        # Test KB search
        kb_results = await KnowledgeBaseOperations.search_articles(session, "password reset login")
        print(f"\nKB articles for 'password reset login':")
        for result in kb_results[:3]:
            print(f"  - {result['title']} (similarity: {result['similarity_score']:.3f})")
        
        print("\n🎉 Sample data created successfully!")
        print("\nYou can now:")
        print("- Test your vector search functionality")
        print("- Build agent workflows with real data")
        print("- Create your demo interface")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    # Check if OpenAI API key is set
    if not config.OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not set in .env file")
        print("Get your API key from: https://platform.openai.com/api-keys")
        sys.exit(1)
    
    asyncio.run(create_sample_data())