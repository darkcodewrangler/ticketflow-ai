"""
Database operations for TicketFlow AI
High-level functions for CRUD operations with vector support
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
import json

from .models import Ticket, KnowledgeBaseArticle, AgentWorkflow, PerformanceMetrics
from .schemas import TicketCreateRequest, KnowledgeBaseCreateRequest
from ..utils.vector_utils import vector_manager

class TicketOperations:
    """High-level ticket operations"""
    
    @staticmethod
    async def create_ticket(session: Session, ticket_data: TicketCreateRequest) -> Ticket:
        """
        Create a new ticket with vector embeddings
        """
        # Generate embeddings
        embeddings = await vector_manager.generate_ticket_embeddings(
            ticket_data.title, 
            ticket_data.description
        )
        
        # Create ticket with embeddings
        ticket = Ticket(
            title=ticket_data.title,
            description=ticket_data.description,
            category=ticket_data.category,
            priority=ticket_data.priority,
            user_id=ticket_data.user_id,
            user_email=ticket_data.user_email,
            user_type=ticket_data.user_type,
            title_vector=embeddings["title_vector"],
            description_vector=embeddings["description_vector"],
            combined_vector=embeddings["combined_vector"]
        )
        
        session.add(ticket)
        session.commit()
        session.refresh(ticket)
        
        return ticket
    
    @staticmethod
    def get_tickets_by_status(session: Session, status: str, limit: int = 50) -> List[Ticket]:
        """Get tickets by status"""
        return session.query(Ticket).filter(
            Ticket.status == status
        ).order_by(desc(Ticket.created_at)).limit(limit).all()
    
    @staticmethod
    def get_recent_tickets(session: Session, days: int = 7, limit: int = 100) -> List[Ticket]:
        """Get recent tickets"""
        since_date = datetime.utcnow() - timedelta(days=days)
        return session.query(Ticket).filter(
            Ticket.created_at >= since_date
        ).order_by(desc(Ticket.created_at)).limit(limit).all()
    
    @staticmethod
    async def find_similar_tickets(session: Session, ticket: Ticket, limit: int = 10, min_similarity: float = 0.7) -> List[Dict]:
        """
        Find similar tickets using vector similarity
        For now, we'll use Python-based similarity calculation
        Later, this will use TiDB's native vector search
        """
        if not ticket.combined_vector:
            return []
        
        # Get query vector
        query_vector = vector_manager.string_to_embedding(ticket.combined_vector)
        if not query_vector:
            return []
        
        # Get resolved tickets to compare against
        resolved_tickets = session.query(Ticket).filter(
            and_(
                Ticket.status == "resolved",
                Ticket.id != ticket.id,
                Ticket.combined_vector.isnot(None)
            )
        ).limit(100).all()  # Limit for performance
        
        similar_tickets = []
        
        for candidate in resolved_tickets:
            candidate_vector = vector_manager.string_to_embedding(candidate.combined_vector)
            if not candidate_vector:
                continue
            
            similarity = vector_manager.cosine_similarity(query_vector, candidate_vector)
            
            if similarity >= min_similarity:
                similar_tickets.append({
                    "ticket": candidate,
                    "similarity_score": similarity,
                    "title": candidate.title,
                    "description": candidate.description,
                    "resolution": candidate.resolution,
                    "category": candidate.category,
                    "resolved_at": candidate.resolved_at
                })
        
        # Sort by similarity score (highest first)
        similar_tickets.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_tickets[:limit]

class KnowledgeBaseOperations:
    """Knowledge base operations"""
    
    @staticmethod
    async def create_article(session: Session, article_data: KnowledgeBaseCreateRequest) -> KnowledgeBaseArticle:
        """Create knowledge base article with embeddings"""
        
        # Generate embeddings
        title_embedding = await vector_manager.generate_embedding(article_data.title)
        content_embedding = await vector_manager.generate_embedding(article_data.content)
        
        summary_embedding = None
        if article_data.summary:
            summary_embedding = await vector_manager.generate_embedding(article_data.summary)
        
        article = KnowledgeBaseArticle(
            title=article_data.title,
            content=article_data.content,
            summary=article_data.summary,
            category=article_data.category,
            tags=article_data.tags,
            source_url=article_data.source_url,
            source_type=article_data.source_type,
            author=article_data.author,
            title_vector=vector_manager.embedding_to_string(title_embedding),
            content_vector=vector_manager.embedding_to_string(content_embedding),
            summary_vector=vector_manager.embedding_to_string(summary_embedding) if summary_embedding else None
        )
        
        session.add(article)
        session.commit()
        session.refresh(article)
        
        return article
    
    @staticmethod
    async def search_articles(session: Session, query: str, limit: int = 5, min_similarity: float = 0.6) -> List[Dict]:
        """Search knowledge base articles using vector similarity"""
        
        # Generate query embedding
        query_embedding = await vector_manager.generate_embedding(query)
        
        # Get all articles
        articles = session.query(KnowledgeBaseArticle).filter(
            KnowledgeBaseArticle.content_vector.isnot(None)
        ).limit(50).all()  # Limit for performance
        
        similar_articles = []
        
        for article in articles:
            article_vector = vector_manager.string_to_embedding(article.content_vector)
            if not article_vector:
                continue
            
            similarity = vector_manager.cosine_similarity(query_embedding, article_vector)
            
            if similarity >= min_similarity:
                similar_articles.append({
                    "article": article,
                    "similarity_score": similarity,
                    "title": article.title,
                    "content": article.content[:200] + "...",  # Truncated for display
                    "category": article.category
                })
        
        # Sort by similarity
        similar_articles.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return similar_articles[:limit]

class WorkflowOperations:
    """Agent workflow operations"""
    
    @staticmethod
    def create_workflow(session: Session, ticket_id: int) -> AgentWorkflow:
        """Create a new agent workflow"""
        workflow = AgentWorkflow(
            ticket_id=ticket_id,
            workflow_steps=[],
            total_duration_ms=0,
            status="running"
        )
        
        session.add(workflow)
        session.commit()
        session.refresh(workflow)
        
        return workflow
    
    @staticmethod
    def update_workflow_step(session: Session, workflow_id: int, step_data: Dict[str, Any]):
        """Add a step to the workflow"""
        workflow = session.query(AgentWorkflow).filter(AgentWorkflow.id == workflow_id).first()
        if not workflow:
            return
        
        # Add the step to workflow_steps
        current_steps = workflow.workflow_steps if workflow.workflow_steps else []
        current_steps.append(step_data)
        
        workflow.workflow_steps = current_steps
        session.commit()