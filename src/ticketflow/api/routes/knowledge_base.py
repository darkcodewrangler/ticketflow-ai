"""
Knowledge Base API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ticketflow.database.operations import KnowledgeBaseOperations
from ticketflow.database.schemas import KnowledgeBaseCreateRequest, KnowledgeBaseResponse
from ticketflow.api.dependencies import verify_db_connection
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)
from ticketflow.database.connection import db_manager
router = APIRouter()

@router.post("/articles")
async def create_article(
    article_data: KnowledgeBaseCreateRequest,
    _: bool = Depends(verify_db_connection)
):
    """Create a new knowledge base article"""
    try:
        article = await KnowledgeBaseOperations.create_article(article_data.model_dump())
        article_data = KnowledgeBaseResponse.model_validate(article).model_dump()
        
        return success_response(
            data=article_data,
            message=ResponseMessages.KB_ARTICLE_CREATED
        )
    except Exception as e:
        return error_response(
            message="Failed to create knowledge base article",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/articles")
async def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of articles to return"),
    _: bool = Depends(verify_db_connection)
):
    """Get knowledge base articles"""
    try:
        if category:
            articles = await KnowledgeBaseOperations.get_articles_by_category(category, int(limit))
        else:
            
            articles = db_manager.kb_articles.query(
                limit=int(limit),
                order_by={"created_at": "desc"}
            ).to_list()
        
        article_list = [KnowledgeBaseResponse.model_validate(article).model_dump() for article in articles]
        return success_response(
            data=article_list,
            message=ResponseMessages.RETRIEVED,
            count=len(article_list),
            metadata={"filtered_by_category": category is not None, "category_filter": category}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve knowledge base articles",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/articles/{article_id}")
async def get_article(
    article_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get a specific knowledge base article"""
    try:
      
        articles = db_manager.kb_articles.query(filters={"id": int(article_id)}, limit=1).to_list()
        
        if not articles:
            return error_response(
                message=ResponseMessages.KB_ARTICLE_NOT_FOUND,
                error="Knowledge base article not found",
                error_code=ErrorCodes.KB_ARTICLE_NOT_FOUND
            )
        
        article_data = KnowledgeBaseResponse.model_validate(articles[0]).model_dump()
        return success_response(
            data=article_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"article_id": article_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve knowledge base article",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/search")
async def search_articles(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    _: bool = Depends(verify_db_connection)
):
    """Search knowledge base articles using vector similarity"""
    try:
        if not query.strip():
            return error_response(
                message="Search query cannot be empty",
                error="Query parameter is required and cannot be empty",
                error_code=ErrorCodes.BAD_REQUEST
            )
        
        results = await KnowledgeBaseOperations.search_articles(query, category, int(limit))
        
        return success_response(
            data=results,
            message="Knowledge base search completed successfully",
            count=len(results),
            metadata={"query": query, "category_filter": category, "search_limit": limit}
        )
    except Exception as e:
        return error_response(
            message="Knowledge base search failed",
            error=str(e),
            error_code=ErrorCodes.KB_SEARCH_FAILED
        )
