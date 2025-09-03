from typing import List, Dict
import openai
import numpy as np
from tidb_vector import TiDBVectorClient

## TiDB Vector Search Implementation

### **Vector Search Strategy**

class VectorSearchEngine:
    def __init__(self):
        self.tidb_client = TiDBVectorClient()
        self.embedding_model = "text-embedding-3-large"  # 3072 dimensions
        
    async def generate_embedding(self, text: str) -> np.ndarray:
        """Generate embeddings using OpenAI's latest model"""
        response = await openai.Embedding.acreate(
            model=self.embedding_model,
            input=text
        )
        return np.array(response['data'][0]['embedding'])
    
    async def hybrid_search(self, query: str, limit: int = 10) -> List[SearchResult]:
        """Combine vector similarity with full-text search"""
        
        # Generate query embedding
        query_vector = await self.generate_embedding(query)
        
        # Hybrid search SQL query
        sql = """
        SELECT 
            t.id,
            t.title,
            t.description,
            t.resolution,
            t.category,
            t.priority,
            -- Vector similarity score
            VEC_COSINE_DISTANCE(t.description_vector, %s) as vector_similarity,
            -- Full-text search score  
            MATCH(t.title, t.description) AGAINST(%s IN NATURAL LANGUAGE MODE) as text_score,
            -- Combined score (weighted)
            (0.7 * VEC_COSINE_DISTANCE(t.description_vector, %s) + 
             0.3 * MATCH(t.title, t.description) AGAINST(%s IN NATURAL LANGUAGE MODE)) as combined_score
        FROM tickets t
        WHERE t.status = 'resolved' 
          AND (
            VEC_COSINE_DISTANCE(t.description_vector, %s) > 0.75 OR
            MATCH(t.title, t.description) AGAINST(%s IN NATURAL LANGUAGE MODE) > 0
          )
        ORDER BY combined_score DESC
        LIMIT %s
        """
        
        params = [query_vector, query, query_vector, query, query_vector, query, limit]
        results = await self.tidb_client.execute(sql, params)
        
        return [SearchResult.from_row(row) for row in results]
    
    async def semantic_clustering(self, tickets: List[Ticket]) -> Dict[str, List[Ticket]]:
        """Group tickets by semantic similarity"""
        
        if not tickets:
            return {}
            
        # Get all embeddings
        embeddings = [ticket.description_vector for ticket in tickets]
        
        # Use TiDB's vector clustering capabilities
        sql = """
        WITH ticket_clusters AS (
            SELECT 
                id,
                title,
                description,
                -- Use vector similarity to create clusters
                ROW_NUMBER() OVER (
                    PARTITION BY FLOOR(
                        VEC_COSINE_DISTANCE(description_vector, 
                            (SELECT description_vector FROM tickets WHERE id = %s)
                        ) * 10
                    ) 
                    ORDER BY created_at
                ) as cluster_rank
            FROM tickets
            WHERE id IN (%s)
        )
        SELECT * FROM ticket_clusters
        ORDER BY cluster_rank, id
        """
        
        # Implementation for semantic clustering
        return clusters
