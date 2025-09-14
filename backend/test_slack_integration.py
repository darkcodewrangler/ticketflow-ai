#!/usr/bin/env python3
"""
Test script for Slack integration functionality
"""

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ticketflow.external_tools_manager import ExternalToolsManager
from ticketflow.config import config

async def test_slack_integration():
    """Test the Slack notification functionality"""
    print("🧪 Testing Slack Integration...")
    
    # Initialize the external tools manager
    tools_manager = ExternalToolsManager()
    
    # Check if Slack is enabled
    if not tools_manager.slack_enabled:
        print("⚠️  Slack integration is not enabled (SLACK_BOT_TOKEN not configured)")
        print("   To test Slack integration, add SLACK_BOT_TOKEN to your .env file")
        return
    
    print(f"✅ Slack integration is enabled")
    print(f"   Bot token configured: {config.SLACK_BOT_TOKEN[:10]}...")
    
    # Test cases
    test_cases = [
        {
            "name": "Simple notification",
            "channel": "#general",
            "message": "Hello from TicketFlow AI! This is a test notification.",
            "ticket_id": None
        },
        {
            "name": "Ticket notification with rich formatting",
            "channel": "#general",
            "message": "Ticket has been updated with new information from the customer.",
            "ticket_id": 12345
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test_case['name']}")
        
        try:
            result = await tools_manager.send_slack_notification(
                channel=test_case['channel'],
                message=test_case['message'],
                ticket_id=test_case['ticket_id']
            )
            
            print(f"   Status: {result['status']}")
            
            if result['status'] == 'sent':
                print(f"   ✅ Message sent successfully")
                print(f"   Channel: {result['channel']}")
                print(f"   Message ID: {result['message_id']}")
            elif result['status'] == 'failed':
                print(f"   ❌ Message failed to send")
                print(f"   Error: {result['error']}")
                if 'error_code' in result:
                    print(f"   Error Code: {result['error_code']}")
            else:
                print(f"   ⚠️  Unexpected status: {result['status']}")
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
    
    print("\n🏁 Slack integration testing completed!")

if __name__ == "__main__":
    asyncio.run(test_slack_integration())