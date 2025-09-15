"""
Search API routes
Unified search across tickets, knowledge base, and other content
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any

from ticketflow.database.operations import TicketOperations, KnowledgeBaseOperations
from ticketflow.api.dependencies import verify_db_connection
from ticketflow.api.response_models import success_response, error_response

router = APIRouter()

@router.get("/tickets")
def search_tickets(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results"),
    _: bool = Depends(verify_db_connection)
):
    """Search tickets using vector similarity"""
    try:
        if not query.strip():
            return error_response(
                message="Query cannot be empty",
                status_code=400
            )
        
        # Use the existing similar tickets search
        similar_tickets = TicketOperations.find_similar_tickets(query, int(limit))
        
        return success_response(
            message="Ticket search completed successfully",
            data=similar_tickets,
            count=len(similar_tickets),
            metadata={"query": query, "limit": limit}
        )
    except Exception as e:
        return error_response(
            message=f"Search failed: {str(e)}",
            status_code=500
        )

@router.get("/knowledge")
def search_knowledge(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results"),
    category: str = Query(None, description="Filter by category"),
    _: bool = Depends(verify_db_connection)
):
    """Search knowledge base articles"""
    try:
        if not query.strip():
            return error_response(
                message="Query cannot be empty",
                status_code=400
            )
        
        results =  KnowledgeBaseOperations.search_articles(query, category, int(limit))
        
        return success_response(
            message="Knowledge base search completed successfully",
            data=results,
            count=len(results),
            metadata={"query": query, "category": category, "limit": limit}
        )
    except Exception as e:
        return error_response(
            message=f"Search failed: {str(e)}",
            status_code=500
        )

@router.get("/unified")
def unified_search(
    query: str = Query(..., description="Search query"),
    ticket_limit: int = Query(5, ge=1, le=20, description="Max ticket results"),
    kb_limit: int = Query(3, ge=1, le=10, description="Max knowledge base results"),
    _: bool = Depends(verify_db_connection)
):
    """Unified search across tickets and knowledge base"""
    try:
        if not query.strip():
            return error_response(
                message="Query cannot be empty",
                status_code=400
            )
        
        # Search tickets
        similar_tickets = TicketOperations.find_similar_tickets(query, int(ticket_limit))
        
        # Search knowledge base
        kb_results =  KnowledgeBaseOperations.search_articles(query, None, int(kb_limit))
        
        return success_response(
            message="Unified search completed successfully",
            data={
                "tickets": {
                    "results": similar_tickets,
                    "count": len(similar_tickets)
                },
                "knowledge_base": {
                    "results": kb_results,
                    "count": len(kb_results)
                }
            },
            count=len(similar_tickets) + len(kb_results),
            metadata={"query": query, "ticket_limit": ticket_limit, "kb_limit": kb_limit}
        )
    except Exception as e:
        return error_response(
            message=f"Unified search failed: {str(e)}",
            status_code=500
        )
