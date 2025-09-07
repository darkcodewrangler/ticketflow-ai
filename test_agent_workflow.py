"""
Test the complete AI Agent workflow
Demonstrates multi-step intelligent ticket processing
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_agent_workflow():
    print("🤖 TicketFlow AI - Agent Workflow Test")
    print("=" * 50)
    
    try:
        from ticketflow.database import db_manager
        from ticketflow.agent.core import TicketFlowAgent, AgentConfig
        from ticketflow.config import config
        
        # Validate setup
        if not config.validate():
            print("❌ Configuration validation failed!")
            return False
        
        # Connect to database
        if not db_manager.connect():
            print("❌ Database connection failed!")
            return False
        if not db_manager.initialize_tables(drop_existing=False):
            print("❌ Table initialization failed!")
            return False
        
        print("✅ Database ready")
        
        # Initialize agent
        agent_config = AgentConfig(
            confidence_threshold=0.8,
            max_similar_tickets=5,
            max_kb_articles=3,
            enable_auto_resolution=True
        )
        
        agent = TicketFlowAgent(agent_config)
        print("✅ AI Agent initialized")
        
        # Test tickets for processing
        test_tickets = [
            {
                "title": "Cannot reset password - email not received",
                "description": "I clicked forgot password but never got the reset email. Checked spam folder multiple times. Need urgent access to account for work presentation tomorrow.",
                "category": "account",
                "priority": "high",
                "user_email": "urgent.user@company.com",
                "user_type": "customer"
            },
            {
                "title": "API integration suddenly returning 403 errors",
                "description": "Our production API integration started failing this morning with 403 forbidden errors on all endpoints. No changes made to our code or API keys.",
                "category": "technical", 
                "priority": "urgent",
                "user_email": "devops@startup.com",
                "user_type": "customer"
            }
        ]
        
        print(f"\n🎯 Processing {len(test_tickets)} tickets through AI Agent...")
        
        results = []
        for i, ticket_data in enumerate(test_tickets, 1):
            print(f"\n--- Processing Ticket {i}: {ticket_data['title'][:40]}... ---")
            
            # Process ticket through agent workflow
            result = await agent.process_ticket(ticket_data)
            results.append(result)
            
            if result["success"]:
                print(f"✅ Ticket {result['ticket_id']} processed successfully")
                print(f"   Status: {result['final_status']}")
                print(f"   Confidence: {result['confidence']:.2f}")
                print(f"   Processing Time: {result['processing_time_ms']}ms")
                print(f"   Actions: {len(result['actions_taken'])}")
                
                if result.get('resolution'):
                    print(f"   Resolution: {result['resolution'][:100]}...")
            else:
                print(f"❌ Ticket processing failed: {result['error']}")
        
        # Summary
        successful = len([r for r in results if r["success"]])
        print(f"\n📊 Agent Processing Summary:")
        print(f"   Successfully processed: {successful}/{len(test_tickets)}")
        print(f"   Average confidence: {sum(r['confidence'] for r in results if r['success']) / max(successful, 1):.2f}")
        print(f"   Total processing time: {sum(r['processing_time_ms'] for r in results if r['success'])}ms")
        
        print(f"\n🎉 AI Agent workflow test completed!")
        print(f"🚀 Ready for demo and frontend integration!")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_agent_workflow())