"""
Test script for the webhook endpoint
"""

import requests
import json

# Test data for different platforms
test_cases = [
    {
        "name": "Zendesk-style webhook",
        "data": {
            "subject": "Password reset not working",
            "description": "I've tried resetting my password multiple times but never receive the email. Checked spam folder.",
            "priority": "high",
            "customer_email": "user@example.com",
            "platform": "zendesk"
        }
    },
    {
        "name": "Freshdesk-style webhook", 
        "data": {
            "title": "API integration failing",
            "body": "Our API calls are returning 500 errors since this morning. No changes on our end.",
            "category": "technical",
            "priority": "urgent",
            "user_email": "dev@company.com",
            "platform": "freshdesk"
        }
    },
    {
        "name": "Jira-style webhook",
        "data": {
            "title": "Feature request: Dark mode",
            "description": "Users are requesting a dark mode option for the dashboard interface.",
            "category": "feature_request",
            "priority": "medium",
            "user_id": "jira-12345",
            "platform": "jira"
        }
    },
    {
        "name": "Custom platform webhook",
        "data": {
            "title": "Billing inquiry",
            "description": "Question about our monthly subscription charges",
            "category": "billing",
            "priority": "low",
            "customer_email": "billing@customer.com",
            "id": "ext-789",
            "platform": "custom_system",
            "metadata": {
                "source_url": "https://custom-system.com/ticket/789",
                "department": "finance"
            }
        }
    }
]

def test_webhook_endpoint():
    """Test the webhook endpoint with various payload formats"""
    base_url = "http://localhost:8000"
    webhook_url = f"{base_url}/api/integrations/webhook"
    
    print("🧪 Testing webhook endpoint...")
    print(f"URL: {webhook_url}")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Data: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            response = requests.post(
                webhook_url,
                json=test_case['data'],
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                ticket = response.json()
                print(f"   ✅ Success! Created ticket ID: {ticket['id']}")
                print(f"   Title: {ticket['title']}")
                print(f"   Category: {ticket['category']}")
                print(f"   Priority: {ticket['priority']}")
                print(f"   Platform: {ticket['ticket_metadata'].get('platform', 'unknown')}")
            else:
                print(f"   ❌ Failed! Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed! Make sure the API server is running on {base_url}")
            break
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "=" * 50)
    print("🏁 Webhook testing completed!")

def test_health_check():
    """Test the webhook health check endpoint"""
    base_url = "http://localhost:8000"
    health_url = f"{base_url}/api/integrations/webhook/health"
    
    print("\n🏥 Testing webhook health check...")
    print(f"URL: {health_url}")
    
    try:
        response = requests.get(health_url)
        if response.status_code == 200:
            health_data = response.json()
            print("✅ Health check passed!")
            print(f"Status: {health_data['status']}")
            print(f"Supported platforms: {', '.join(health_data['supported_platforms'])}")
        else:
            print(f"❌ Health check failed! Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Health check error: {e}")

if __name__ == "__main__":
    test_webhook_endpoint()
    test_health_check()
