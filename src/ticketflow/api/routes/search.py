"""
Search API routes
Unified search across tickets, knowledge base, and other content
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any

from ...database.operations import TicketOperations, KnowledgeBaseOperations
from ..dependencies import verify_db_connection

router = APIRouter()

@router.get("/tickets")
async def search_tickets(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    _: bool = Depends(verify_db_connection)
):
    """Search tickets using vector similarity"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Use the existing similar tickets search
        similar_tickets = TicketOperations.find_similar_tickets(query, limit)
        
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
    category: str = Query(None, description="Filter by category"),
    _: bool = Depends(verify_db_connection)
):
    """Search knowledge base articles"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = KnowledgeBaseOperations.search_articles(query, category, limit)
        
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
    _: bool = Depends(verify_db_connection)
):
    """Unified search across tickets and knowledge base"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Search tickets
        similar_tickets = TicketOperations.find_similar_tickets(query, ticket_limit)
        
        # Search knowledge base
        kb_results = KnowledgeBaseOperations.search_articles(query, None, kb_limit)
        
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
