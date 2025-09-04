"""
Search API routes
Unified search across tickets, knowledge base, and other content
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ...database.operations import TicketOperations, KnowledgeBaseOperations
from ..dependencies import get_db_session

router = APIRouter()

@router.get("/tickets")
async def search_tickets(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    min_similarity: float = Query(0.7, ge=0.0, le=1.0, description="Minimum similarity"),
    session: Session = Depends(get_db_session)
):
    """Search tickets using vector similarity"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Create a temporary ticket-like object for search
        from ...utils.vector_utils import vector_manager
        embeddings = await vector_manager.generate_ticket_embeddings("", query)
        
        # Create a simple object to hold the vector for search
        class SearchQuery:
            def __init__(self, combined_vector):
                self.id = -1  # Dummy ID
                self.combined_vector = combined_vector
        
        search_obj = SearchQuery(embeddings["combined_vector"])
        similar_tickets = await TicketOperations.find_similar_tickets(
            session, search_obj, limit, min_similarity
        )
        
        return {
            "query": query,
            "results": similar_tickets,
            "count": len(similar_tickets)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/knowledge")
async def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity"),
    session: Session = Depends(get_db_session)
):
    """Search knowledge base articles"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = await KnowledgeBaseOperations.search_articles(
            session, query, limit, min_similarity
        )
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/unified")
async def unified_search(
    query: str = Query(..., description="Search query"),
    ticket_limit: int = Query(5, ge=1, le=20, description="Max ticket results"),
    kb_limit: int = Query(3, ge=1, le=10, description="Max knowledge base results"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity"),
    session: Session = Depends(get_db_session)
):
    """Unified search across tickets and knowledge base"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Search tickets
        from ...utils.vector_utils import vector_manager
        embeddings = await vector_manager.generate_ticket_embeddings("", query)
        
        class SearchQuery:
            def __init__(self, combined_vector):
                self.id = -1
                self.combined_vector = combined_vector
        
        search_obj = SearchQuery(embeddings["combined_vector"])
        similar_tickets = await TicketOperations.find_similar_tickets(
            session, search_obj, ticket_limit, min_similarity
        )
        
        # Search knowledge base
        kb_results = await KnowledgeBaseOperations.search_articles(
            session, query, kb_limit, min_similarity
        )
        
        return {
            "query": query,
            "tickets": {
                "results": similar_tickets,
                "count": len(similar_tickets)
            },
            "knowledge_base": {
                "results": kb_results,
                "count": len(kb_results)
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unified search failed: {str(e)}")
