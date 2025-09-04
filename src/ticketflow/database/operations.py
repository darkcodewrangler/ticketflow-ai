"""
Database operations for TicketFlow AI
High-level functions for CRUD operations with vector support
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, text
from datetime import datetime, timedelta
import json

from .models import Ticket, KnowledgeBaseArticle, AgentWorkflow, PerformanceMetrics
from .schemas import TicketCreateRequest, KnowledgeBaseCreateRequest
from ..utils.vector_utils import vector_manager

class TicketOperations:
    """High-level ticket operations with TiDB vector search"""
    
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
        
        # Create ticket with embeddings (TiDB native vectors)
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
    async def find_similar_tickets(session: Session, ticket: Ticket, limit: int = 10, min_similarity: float = 0.75) -> List[Dict]:
        """
        Find similar tickets using TiDB native vector similarity search
        """
        if not ticket.combined_vector:
            return []
        
        # Use TiDB's native vector search with VEC_COSINE_DISTANCE
        # VEC_COSINE_DISTANCE returns distance (0 = identical, higher = more different)
        # We convert to similarity score: similarity = 1 - distance
        sql = text("""
            SELECT 
                id, title, description, resolution, category, priority, resolved_at, resolution_type,
                VEC_COSINE_DISTANCE(combined_vector, :query_vector) as distance,
                (1 - VEC_COSINE_DISTANCE(combined_vector, :query_vector)) as similarity_score
            FROM tickets 
            WHERE status = 'resolved' 
              AND id != :ticket_id
              AND combined_vector IS NOT NULL
              AND VEC_COSINE_DISTANCE(combined_vector, :query_vector) <= :max_distance
            ORDER BY distance ASC
            LIMIT :limit_count
        """)
        
        max_distance = 1 - min_similarity  # Convert similarity to distance threshold
        
        result = session.execute(sql, {
            'query_vector': ticket.combined_vector,
            'ticket_id': ticket.id,
            'max_distance': max_distance,
            'limit_count': limit
        })
        
        similar_tickets = []
        for row in result:
            similar_tickets.append({
                "ticket_id": row.id,
                "title": row.title,
                "description": row.description,
                "resolution": row.resolution,
                "category": row.category,
                "priority": row.priority,
                "resolved_at": row.resolved_at,
                "resolution_type": row.resolution_type,
                "similarity_score": float(row.similarity_score),
                "distance": float(row.distance)
            })
        
        return similar_tickets

class KnowledgeBaseOperations:
    """Knowledge base operations with TiDB vector search"""
    
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
            title_vector=title_embedding,
            content_vector=content_embedding,
            summary_vector=summary_embedding
        )
        
        session.add(article)
        session.commit()
        session.refresh(article)
        
        return article
    
    @staticmethod
    async def search_articles(session: Session, query: str, limit: int = 5, min_similarity: float = 0.6) -> List[Dict]:
        """Search knowledge base articles using TiDB native vector similarity"""
        
        # Generate query embedding
        query_embedding = await vector_manager.generate_embedding(query)
        
        # Use TiDB's native vector search
        sql = text("""
            SELECT 
                id, title, content, category, tags, source_url,
                VEC_COSINE_DISTANCE(content_vector, :query_vector) as distance,
                (1 - VEC_COSINE_DISTANCE(content_vector, :query_vector)) as similarity_score
            FROM kb_articles 
            WHERE content_vector IS NOT NULL
              AND VEC_COSINE_DISTANCE(content_vector, :query_vector) <= :max_distance
            ORDER BY distance ASC
            LIMIT :limit_count
        """)
        
        max_distance = 1 - min_similarity
        
        result = session.execute(sql, {
            'query_vector': query_embedding,
            'max_distance': max_distance,
            'limit_count': limit
        })
        
        similar_articles = []
        for row in result:
            similar_articles.append({
                "article_id": row.id,
                "title": row.title,
                "content": row.content[:200] + "..." if len(row.content) > 200 else row.content,
                "category": row.category,
                "tags": row.tags,
                "source_url": row.source_url,
                "similarity_score": float(row.similarity_score),
                "distance": float(row.distance)
            })
        
        return similar_articles

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