#!/usr/bin/env python3
"""
Test script for Knowledge Base API functionality
"""

import requests
import json
import time
from pathlib import Path

# API base URL
BASE_URL = "http://localhost:8000"

def test_file_upload():
    """Test file upload functionality"""
    print("\n=== Testing File Upload ===")
    
    # Create a test markdown file
    test_content = """# Test Knowledge Base Article

This is a test article for the knowledge base.

## Features
- File processing
- AI metadata generation
- Background task processing

## Conclusion
This demonstrates the knowledge base functionality.
"""
    
    test_file_path = Path("test_article.md")
    test_file_path.write_text(test_content, encoding='utf-8')
    
    try:
        # Upload the file
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_article.md', f, 'text/markdown')}
            data = {
                'category': 'Testing',
                'tags': 'test,knowledge-base,api',
                'author': 'Test User'
            }
            
            response = requests.post(f"{BASE_URL}/api/kb/upload", files=files, data=data)
            
        if response.status_code == 200:
            result = response.json()
            print(f"✅ File upload successful!")
            if 'data' in result and 'task_id' in result['data']:
                print(f"Task ID: {result['data']['task_id']}")
                return result['data']['task_id']
            else:
                print(f"Response: {result}")
                return None
        else:
            print(f"❌ File upload failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during file upload: {e}")
        return None
    finally:
        # Clean up test file
        if test_file_path.exists():
            test_file_path.unlink()

def test_url_processing():
    """Test URL processing functionality"""
    print("\n=== Testing URL Processing ===")
    
    try:
        data = {
            'url': 'https://blog.geltechng.com/web-development/how-nigerian-businesses-can-benefit-from-custom-web-development',  # Simple test URL
            'follow_links':True,
            'max_depth': 3,
            'category': 'Web Content',
            'tags': 'test,web-scraping',
            'author': 'Test User'
        }
        
        response = requests.post(f"{BASE_URL}/api/kb/url", data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ URL processing started successfully!")
            if 'data' in result and 'task_id' in result['data']:
                print(f"Task ID: {result['data']['task_id']}")
                return result['data']['task_id']
            else:
                print(f"Response: {result}")
                return None
        else:
            print(f"❌ URL processing failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during URL processing: {e}")
        return None

def test_processing_status(task_id):
    """Test processing status endpoint"""
    print(f"\n=== Testing Processing Status for Task {task_id} ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/kb/processing-status?task_id={task_id}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Status check successful!")
            if 'data' in result:
                print(f"Status: {result['data'].get('status', 'unknown')}")
                print(f"Progress: {result['data'].get('progress', 0)}%")
                return result['data']
            else:
                print(f"Response: {result}")
                return result
        else:
            print(f"❌ Status check failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during status check: {e}")
        return None

def test_articles_list():
    """Test articles listing endpoint"""
    print("\n=== Testing Articles List ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/kb/articles?limit=5")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Articles list retrieved successfully!")
            if 'data' in result:
                print(f"Found {len(result['data'])} articles")
                return result['data']
            else:
                print(f"Response: {result}")
                return result
        else:
            print(f"❌ Articles list failed: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error during articles list: {e}")
        return None

def main():
    """Main test function"""
    print("🚀 Starting Knowledge Base API Tests")
    print(f"Testing against: {BASE_URL}")
    
    # Test file upload
    # file_task_id = test_file_upload()
    
    # Test URL processing
    url_task_id = test_url_processing()
    
    # Wait a bit for processing to start
    time.sleep(2)
    
    # Test status checking
    # if file_task_id:
    #     test_processing_status(file_task_id)
    
    if url_task_id:
        test_processing_status(url_task_id)
    
    # Test articles listing
    test_articles_list()
    
    print("\n✨ Knowledge Base API tests completed!")
    print("\n📝 Note: Background processing may still be running.")
    print("   Check the processing status endpoints to monitor progress.")

if __name__ == "__main__":
    main()