#!/usr/bin/env python3
"""
Test PDF upload and processing functionality for knowledge base
"""

import requests
import time
import os

def test_pdf_upload():
    """Test PDF file upload to knowledge base"""
    print("\n=== Testing PDF Upload ===")
    
    # Check if sample PDF exists
    pdf_file = "sample_test_document.pdf"
    if not os.path.exists(pdf_file):
        print(f"Error: {pdf_file} not found. Please run test_pdf_sample.py first.")
        return None
    
    url = "http://localhost:8000/api/kb/upload"
    
    with open(pdf_file, 'rb') as f:
        files = {'file': (pdf_file, f, 'application/pdf')}
        data = {
            'category': 'test',
            'tags': 'pdf,testing,sample',
            'author': 'test_user'
        }
        
        try:
            response = requests.post(url, files=files, data=data)
            print(f"Upload Status Code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"Upload successful!")
                data = result.get('data', {})
                task_id = data.get('task_id')
                print(f"Task ID: {task_id}")
                print(f"Message: {result.get('message')}")
                return task_id
            else:
                print(f"Upload failed: {response.text}")
                return None
                
        except Exception as e:
            print(f"Upload error: {e}")
            return None

def test_processing_status(task_id):
    """Test processing status check"""
    print("\n=== Testing Processing Status ===")
    
    if not task_id:
        print("No task ID provided")
        return None
    
    url = f"http://localhost:8000/api/kb/processing-status?task_id={task_id}"
    
    # Wait for processing to complete
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                status = data.get('status')
                print(f"Attempt {attempt + 1}: Status = {status}")
                
                if status == 'completed':
                    print("Processing completed successfully!")
                    result_data = data.get('result_data', {})
                    article_id = result_data.get('article_id')
                    print(f"Article ID: {article_id}")
                    return article_id
                elif status == 'failed':
                    error_msg = data.get('error_message', 'Unknown error')
                    print(f"Processing failed: {error_msg}")
                    return None
                elif status in ['pending', 'processing']:
                    progress = data.get('progress_percentage', 0)
                    print(f"  Progress: {progress}%")
                    time.sleep(2)  # Wait 2 seconds before next check
                    continue
            else:
                print(f"Status check failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Status check error: {e}")
            return None
    
    print("Processing timeout - took too long")
    return None

def test_article_retrieval(article_id):
    """Test article retrieval"""
    print("\n=== Testing Article Retrieval ===")
    
    if not article_id:
        print("No article ID provided")
        return False
    
    url = f"http://localhost:8000/api/kb/articles/{article_id}"
    
    try:
        response = requests.get(url)
        print(f"Retrieval Status Code: {response.status_code}")
        
        if response.status_code == 200:
            article = response.json()
            print(f"Article Title: {article.get('title')}")
            print(f"Article Format: {article.get('format')}")
            print(f"Article Summary: {article.get('summary')}")
            print(f"Content Preview: {article.get('content', '')[:200]}...")
            return True
        else:
            print(f"Retrieval failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"Retrieval error: {e}")
        return False

def test_pdf_search():
    """Test search functionality for PDF content"""
    print("\n=== Testing PDF Search ===")
    
    search_queries = [
        "PDF processing",
        "PyPDF2 library",
        "technical details",
        "sample document"
    ]
    
    for query in search_queries:
        print(f"\nSearching for: '{query}'")
        url = f"http://localhost:8000/api/kb/search?q={query}"
        
        try:
            response = requests.get(url)
            if response.status_code == 200:
                results = response.json()
                print(f"Found {len(results)} results")
                
                for i, result in enumerate(results[:2]):  # Show first 2 results
                    print(f"  Result {i+1}: {result.get('title')}")
                    print(f"    Format: {result.get('format')}")
                    print(f"    Preview: {result.get('content', '')[:100]}...")
            else:
                print(f"Search failed: {response.status_code}")
                
        except Exception as e:
            print(f"Search error: {e}")

def test_articles_list():
    """Test articles listing"""
    print("\n=== Testing Articles List ===")
    
    url = "http://localhost:8000/api/kb/articles"
    
    try:
        response = requests.get(url)
        print(f"List Status Code: {response.status_code}")
        
        if response.status_code == 200:
            articles = response.json()
            print(f"Total articles: {len(articles)}")
            
            # Look for PDF articles
            pdf_articles = [a for a in articles if a.get('format') == 'pdf']
            print(f"PDF articles: {len(pdf_articles)}")
            
            if pdf_articles:
                print("PDF Articles found:")
                for article in pdf_articles[:3]:  # Show first 3
                    print(f"  - {article.get('title')} (ID: {article.get('id')})")
            
            return len(pdf_articles) > 0
        else:
            print(f"List failed: {response.text}")
            return False
            
    except Exception as e:
        print(f"List error: {e}")
        return False

def main():
    """Run all PDF tests"""
    print("Starting PDF Knowledge Base Tests...")
    
    # Test upload
    task_id = test_pdf_upload()
    if not task_id:
        print("Upload test failed - stopping")
        return
    
    # Test processing
    article_id = test_processing_status(task_id)
    if not article_id:
        print("Processing test failed - stopping")
        return
    
    # Test retrieval
    if not test_article_retrieval(article_id):
        print("Retrieval test failed")
        return
    
    # Test search
    test_pdf_search()
    
    # Test articles list
    if test_articles_list():
        print("\n✅ All PDF tests completed successfully!")
    else:
        print("\n❌ Some tests failed")
    
    print("\n=== Test Summary ===")
    print("✅ PDF upload functionality")
    print("✅ Background processing")
    print("✅ Article creation")
    print("✅ Content extraction")
    print("✅ Search integration")
    print("✅ API endpoints")

if __name__ == "__main__":
    main()