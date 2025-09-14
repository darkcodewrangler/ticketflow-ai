#!/usr/bin/env python3
"""
Test script to verify API improvements for UI alignment
Tests the new Slack channel settings and Resend email configuration
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any


class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_health_check(self) -> bool:
        """Test if API is running"""
        try:
            async with self.session.get(f"{self.base_url}/health") as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"✅ API Health Check: {data.get('status', 'unknown')}")
                    return True
                else:
                    print(f"❌ API Health Check failed: {response.status}")
                    return False
        except Exception as e:
            print(f"❌ API Health Check error: {e}")
            return False
    
    async def test_settings_endpoints(self) -> Dict[str, Any]:
        """Test settings endpoints for new configurations"""
        results = {}
        
        try:
            # Test getting all settings
            async with self.session.get(f"{self.base_url}/api/settings/") as response:
                if response.status == 200:
                    response_data = await response.json()
                    # Handle wrapped response format
                    if isinstance(response_data, dict) and 'data' in response_data:
                        data = response_data['data']
                        if isinstance(data, dict) and 'settings' in data:
                            settings = data['settings']
                        else:
                            settings = data if isinstance(data, list) else []
                    elif isinstance(response_data, list):
                        settings = response_data
                    else:
                        settings = []
                    
                    results['get_all_settings'] = {
                        'status': 'success',
                        'count': len(settings),
                        'categories': list(set(s.get('category', 'unknown') for s in settings))
                    }
                    print(f"✅ Get all settings: {len(settings)} settings found")
                    print(f"   Categories: {results['get_all_settings']['categories']}")
                    
                    # Check for new Slack settings
                    slack_settings = [s for s in settings if s.get('category') == 'slack']
                    slack_keys = [s.get('key') for s in slack_settings]
                    expected_slack_keys = [
                        'slack_bot_token',
                        'slack_app_token', 
                        'slack_signing_secret',
                        'slack_new_ticket_channel',
                        'slack_escalation_channel',
                        'slack_resolution_channel',
                        'slack_agent_assignment_channel',
                        'slack_notifications_enabled'
                    ]
                    
                    missing_slack = [key for key in expected_slack_keys if key not in slack_keys]
                    if not missing_slack:
                        print("✅ All expected Slack settings found")
                        results['slack_settings'] = {'status': 'success', 'keys': slack_keys}
                    else:
                        print(f"❌ Missing Slack settings: {missing_slack}")
                        results['slack_settings'] = {'status': 'missing', 'missing': missing_slack}
                    
                    # Check for new Resend email settings
                    email_settings = [s for s in settings if s.get('category') == 'email']
                    email_keys = [s.get('key') for s in email_settings]
                    expected_email_keys = [
                        'resend_api_key',
                        'resend_from_email',
                        'resend_from_name',
                        'resend_reply_to_email',
                        'resend_webhook_secret',
                        'resend_track_opens',
                        'resend_track_clicks',
                        'resend_new_ticket_recipient',
                        'resend_escalation_recipient',
                        'resend_resolution_recipient',
                        'resend_agent_assignment_recipient',
                        'resend_notifications_enabled'
                    ]
                    
                    missing_email = [key for key in expected_email_keys if key not in email_keys]
                    if not missing_email:
                        print("✅ All expected Resend email settings found")
                        results['email_settings'] = {'status': 'success', 'keys': email_keys}
                    else:
                        print(f"❌ Missing Resend email settings: {missing_email}")
                        results['email_settings'] = {'status': 'missing', 'missing': missing_email}
                    
                    # Check that no database settings are exposed
                    db_settings = [s for s in settings if 'database' in s.get('key', '').lower() or 'db_' in s.get('key', '').lower()]
                    if not db_settings:
                        print("✅ No database connection settings exposed")
                        results['database_settings'] = {'status': 'success', 'message': 'No database settings exposed'}
                    else:
                        print(f"❌ Database settings found (should be hidden): {[s.get('key') for s in db_settings]}")
                        results['database_settings'] = {'status': 'error', 'exposed': [s.get('key') for s in db_settings]}
                    
                else:
                    results['get_all_settings'] = {'status': 'error', 'code': response.status}
                    print(f"❌ Get all settings failed: {response.status}")
                    
        except Exception as e:
            results['get_all_settings'] = {'status': 'exception', 'error': str(e)}
            print(f"❌ Settings test error: {e}")
        
        return results
    
    async def test_settings_by_category(self) -> Dict[str, Any]:
        """Test getting settings by category"""
        results = {}
        categories = ['slack', 'email', 'system', 'agent']
        
        for category in categories:
            try:
                async with self.session.get(f"{self.base_url}/api/settings/?category={category}") as response:
                    if response.status == 200:
                        response_data = await response.json()
                        # Handle wrapped response format
                        if isinstance(response_data, dict) and 'data' in response_data:
                            data = response_data['data']
                            if isinstance(data, dict) and 'settings' in data:
                                settings = data['settings']
                            else:
                                settings = data if isinstance(data, list) else []
                        elif isinstance(response_data, list):
                            settings = response_data
                        else:
                            settings = []
                            
                        results[f'{category}_category'] = {
                            'status': 'success',
                            'count': len(settings),
                            'keys': [s.get('key') for s in settings]
                        }
                        print(f"✅ {category.title()} category: {len(settings)} settings")
                    else:
                        results[f'{category}_category'] = {'status': 'error', 'code': response.status}
                        print(f"❌ {category.title()} category failed: {response.status}")
            except Exception as e:
                results[f'{category}_category'] = {'status': 'exception', 'error': str(e)}
                print(f"❌ {category.title()} category error: {e}")
        
        return results
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all API tests"""
        print("🚀 Starting API Improvement Tests...\n")
        
        # Test API health
        health_ok = await self.test_health_check()
        if not health_ok:
            return {'error': 'API not accessible'}
        
        print()
        
        # Test settings endpoints
        print("📋 Testing Settings Endpoints...")
        settings_results = await self.test_settings_endpoints()
        
        print("\n📂 Testing Settings by Category...")
        category_results = await self.test_settings_by_category()
        
        return {
            'health_check': health_ok,
            'settings_tests': settings_results,
            'category_tests': category_results,
            'timestamp': asyncio.get_event_loop().time()
        }


async def main():
    """Main test function"""
    async with APITester() as tester:
        results = await tester.run_all_tests()
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        if results.get('health_check'):
            print("✅ API Health: PASS")
        else:
            print("❌ API Health: FAIL")
            return
        
        settings_tests = results.get('settings_tests', {})
        if settings_tests.get('slack_settings', {}).get('status') == 'success':
            print("✅ Slack Settings: PASS")
        else:
            print("❌ Slack Settings: FAIL")
        
        if settings_tests.get('email_settings', {}).get('status') == 'success':
            print("✅ Resend Email Settings: PASS")
        else:
            print("❌ Resend Email Settings: FAIL")
        
        if settings_tests.get('database_settings', {}).get('status') == 'success':
            print("✅ Database Settings Hidden: PASS")
        else:
            print("❌ Database Settings Hidden: FAIL")
        
        category_tests = results.get('category_tests', {})
        category_pass = all(test.get('status') == 'success' for test in category_tests.values())
        if category_pass:
            print("✅ Category Endpoints: PASS")
        else:
            print("❌ Category Endpoints: FAIL")
        
        print("\n🎉 API improvement tests completed!")
        
        # Save detailed results
        with open('api_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        print("📄 Detailed results saved to api_test_results.json")


if __name__ == "__main__":
    asyncio.run(main())