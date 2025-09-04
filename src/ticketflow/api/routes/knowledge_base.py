"""
Knowledge Base API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database.operations import KnowledgeBaseOperations
from ...database.schemas import KnowledgeBaseCreateRequest, KnowledgeBaseResponse
from ..dependencies import get_db_session

router = APIRouter()

@router.post("/articles", response_model=KnowledgeBaseResponse)
async def create_article(
    article_data: KnowledgeBaseCreateRequest,
    session: Session = Depends(get_db_session)
):
    """Create a new knowledge base article"""
    try:
        article = await KnowledgeBaseOperations.create_article(session, article_data)
        return KnowledgeBaseResponse.from_orm(article)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create article: {str(e)}")

@router.get("/articles", response_model=List[KnowledgeBaseResponse])
def get_articles(
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, ge=1, le=100, description="Number of articles to return"),
    session: Session = Depends(get_db_session)
):
    """Get knowledge base articles"""
    try:
        from ...database.models import KnowledgeBaseArticle
        
        query = session.query(KnowledgeBaseArticle)
        if category:
            query = query.filter(KnowledgeBaseArticle.category == category)
        
        articles = query.order_by(KnowledgeBaseArticle.created_at.desc()).limit(limit).all()
        return [KnowledgeBaseResponse.from_orm(article) for article in articles]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")

@router.get("/articles/{article_id}", response_model=KnowledgeBaseResponse)
def get_article(
    article_id: int,
    session: Session = Depends(get_db_session)
):
    """Get a specific knowledge base article"""
    try:
        from ...database.models import KnowledgeBaseArticle
        
        article = session.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.id == article_id
        ).first()
        
        if not article:
            raise HTTPException(status_code=404, detail="Article not found")
        
        return KnowledgeBaseResponse.from_orm(article)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get article: {str(e)}")

@router.get("/search", response_model=List[dict])
async def search_articles(
    query: str = Query(..., description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Number of results to return"),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0, description="Minimum similarity score"),
    session: Session = Depends(get_db_session)
):
    """Search knowledge base articles using vector similarity"""
    try:
        if not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        results = await KnowledgeBaseOperations.search_articles(
            session, query, limit, min_similarity
        )
        
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
