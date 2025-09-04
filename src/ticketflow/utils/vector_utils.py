"""
Vector embedding utilities for TicketFlow AI
Handles OpenAI embeddings and TiDB vector storage
"""

import json
import numpy as np
from typing import List, Optional, Union
import openai
from ..config import config

# Initialize OpenAI client
openai.api_key = config.OPENAI_API_KEY

class VectorManager:
    """Manages vector embeddings and TiDB vector operations"""
    
    def __init__(self):
        self.embedding_model = "text-embedding-3-large"  # 3072 dimensions
        self.embedding_dimensions = 3072
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate OpenAI embedding for text
        
        Args:
            text: Text to embed
            
        Returns:
            List of floats representing the embedding vector
        """
        try:
            response = await openai.embeddings.acreate(
                model=self.embedding_model,
                input=text.strip()
            )
            embedding = response.data[0].embedding
            return embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            # Return zero vector as fallback
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
            "title_vector": self.embedding_to_string(title_embedding),
            "description_vector": self.embedding_to_string(description_embedding),
            "combined_vector": self.embedding_to_string(combined_embedding)
        }

# Global vector manager instance
vector_manager = VectorManager()