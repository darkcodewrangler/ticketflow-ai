import requests
import json
import sys
from pathlib import Path

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ticketflow.config import config

def test_jina_connection():
    print("🤖 Testing Jina AI Connection")
    print("=" * 40)
    
    if not config.JINA_API_KEY:
        print("❌ JINA_API_KEY not found in .env")
        return False
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.JINA_API_KEY}"
    }
    
    payload = {
        "model": "jina-embeddings-v4",
        "input": [{"text": "Hello, this is a test!"}],
        "task": "text-matching",
        "embedding_type": "float"
    }
    
    try:
        response = requests.post(
            f"https://api.jina.ai/v1/embeddings", 
            headers=headers, 
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        embedding = result["data"][0]["embedding"]
        
        print(f"✅ Connection successful!")
        print(f"✅ Model: {result['model']}")
        print(f"✅ Embedding dimensions: {len(embedding)}")
        print(f"✅ First 5 values: {embedding[:5]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

if __name__ == "__main__":
    test_jina_connection()