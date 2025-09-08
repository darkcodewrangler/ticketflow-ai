"""
Knowledge Base API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...database.operations import KnowledgeBaseOperations
from ...database.schemas import KnowledgeBaseCreateRequest, KnowledgeBaseResponse
from ..dependencies import verify_db_connection

router = APIRouter()

@router.post("/articles", response_model=KnowledgeBaseResponse)
async def create_article(
    article_data: KnowledgeBaseCreateRequest,
    _: bool = Depends(verify_db_connection)
):
    """Create a new knowledge base article"""
    try:
        article = KnowledgeBaseOperations.create_article(article_data.dict())
        return KnowledgeBaseResponse.model_validate(article)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create article: {str(e)}")

@router.get("/articles", response_model=List[KnowledgeBaseResponse])
def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of articles to return"),
    _: bool = Depends(verify_db_connection)
):
    """Get knowledge base articles"""
    try:
        if category:
            articles = KnowledgeBaseOperations.get_articles_by_category(category, limit)
        else:
            # Get all articles (we'll implement this method)
            from ...database.connection import db_manager
            articles = db_manager.kb_articles.query(
                limit=limit,
                order_by={"created_at": "desc"}
            ).to_list()
        
        return [KnowledgeBaseResponse.model_validate(article) for article in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")

@router.get("/articles/{article_id}", response_model=KnowledgeBaseResponse)
def get_article(
    article_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get a specific knowledge base article"""
    try:
        from ...database.connection import db_manager
        
        articles = db_manager.kb_articles.query(filters={"id": article_id}, limit=1).to_list()
        
        if not articles:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return KnowledgeBaseResponse.model_validate(articles[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")

@router.get("/search", response_model=List[dict])
async def search_articles(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results to return"),
    category: Optional[str] = Query(None, description="Filter by category"),
    _: bool = Depends(verify_db_connection)
):
    """Search knowledge base articles using vector similarity"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = KnowledgeBaseOperations.search_articles(query, category, limit)
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
