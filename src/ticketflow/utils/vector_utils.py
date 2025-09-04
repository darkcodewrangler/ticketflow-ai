"""
Vector embedding utilities for TicketFlow AI
Handles Jina embeddings and TiDB vector storage
"""

import json
import numpy as np
from typing import List, Optional, Union
import requests
from ..config import config

class VectorManager:
    """Manages vector embeddings and TiDB vector operations"""
    
    def __init__(self):
        self.embedding_model = "jina-embeddings-v4"  # 2048 dimensions
        self.embedding_dimensions = 2048
        self.embedding_task='text-matching'
        self.jina_api_key = config.JINA_API_KEY
        self.jina_api_url = "https://api.jina.ai/v1/embeddings"
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate Jina embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jina_api_key}"
            }
            
            payload = {
                "model": self.embedding_model,
                "task": self.embedding_task,
                "input": [{
                    "text":text.strip()
                }],
                "encoding_format": "float"
            }
            
            response = requests.post(self.jina_api_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            embedding = result["data"][0]["embedding"]
            
            # Ensure we have the right number of dimensions
            if len(embedding) != self.embedding_dimensions:
                print(f"⚠️ Warning: Expected {self.embedding_dimensions} dimensions, got {len(embedding)}")
            
            return embedding
            
        except Exception as e:
            print(f"❌ Error generating Jina embedding: {e}")
            # Return zero vector as fallback
            return [0.0] * self.embedding_dimensions
    
    def generate_embedding_sync(self, text: str) -> List[float]:
        """
        Synchronous version for cases where async isn't available
        """
        try:
            headers = {
                "Content-Type": "application/json", 
                "Authorization": f"Bearer {self.jina_api_key}"
            }
            
            payload = {
               "model": self.embedding_model,
                "task": self.embedding_task,
                "input": [{
                    "text":text.strip()
                }],
                "encoding_format": "float"
            }
            
            response = requests.post(self.jina_api_url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            return result["data"][0]["embedding"]
            
        except Exception as e:
            print(f"❌ Error generating Jina embedding (sync): {e}")
            return [0.0] * self.embedding_dimensions
    def embedding_to_string(self, embedding: List[float]) -> str:
        """
        Convert embedding list to string format for database storage
        For now, we'll store as JSON string, later migrate to TiDB VECTOR
        """
        return json.dumps(embedding)
    
    def string_to_embedding(self, embedding_str: Optional[str]) -> Optional[List[float]]:
        """
        Convert string back to embedding list
        """
        if not embedding_str:
            return None
        try:
            return json.loads(embedding_str)
        except json.JSONDecodeError:
            return None
    
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """
        Calculate cosine similarity between two vectors
        """
        if not vec1 or not vec2:
            return 0.0
            
        # Convert to numpy arrays for efficient computation
        a = np.array(vec1)
        b = np.array(vec2)
        
        # Calculate cosine similarity
        dot_product = np.dot(a, b)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        
        if norm_a == 0 or norm_b == 0:
            return 0.0
            
        return dot_product / (norm_a * norm_b)
    
    async def generate_ticket_embeddings(self, title: str, description: str) -> dict:
        """
        Generate all embeddings for a ticket
        
        Returns:
            Dict with title_vector, description_vector, and combined_vector
        """
        # Generate individual embeddings
        title_embedding = await self.generate_embedding(title)
        description_embedding = await self.generate_embedding(description)
        
        # Combined text for better search results
        combined_text = f"{title}\n\n{description}"
        combined_embedding = await self.generate_embedding(combined_text)
        
        return {
            "title_vector": title_embedding,
            "description_vector": description_embedding,
            "combined_vector": combined_embedding
        }

# Global vector manager instance
vector_manager = VectorManager()