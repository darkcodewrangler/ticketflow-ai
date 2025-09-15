"""
PyTiDB AI-powered database operations for TicketFlow AI
Leverages automatic embeddings and built-in search capabilities
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import  timedelta
import logging

from ticketflow.database.operations.utils import reranker

from ticketflow.database.models import (
    Ticket, 
    TicketStatus,
    Priority,
    ResolutionType
)
from ticketflow.database.connection import db_manager
from pytidb.filters import GTE, NE
logger = logging.getLogger(__name__)
from ticketflow.utils.helpers import get_isoformat, get_value,utcnow



class TicketOperations:
    """
    High-level ticket operations with PyTiDB's AI features
    
    Automatic embeddings, vector search, and hybrid search built-in!
    """
    @staticmethod
    def create_ticket(ticket_data: Dict[str, Any]) -> Ticket:
        """
        Create a new ticket - PyTiDB automatically generates embeddings!
        
        Args:
            ticket_data: Dictionary with ticket fields
            
        Returns:
            Created ticket with auto-generated embeddings
        """
        try:
            # Create ticket instance
            ticket = Ticket(
                title=get_value(ticket_data, "title", ""),
                description=get_value(ticket_data, "description", ""),      
                category=get_value(ticket_data, "category", "general"),
                priority=get_value(ticket_data, "priority", Priority.MEDIUM.value),
                status=get_value(ticket_data, "status", TicketStatus.NEW.value),
                user_id=get_value(ticket_data, "user_id", ""),
                user_email=get_value(ticket_data, "user_email", ""),
                user_type=get_value(ticket_data, "user_type", "customer"),
                ticket_metadata=get_value(ticket_data, "ticket_metadata", {})
            )
            
            # PyTiDB automatically generates embeddings for title and description!
            result = db_manager.tickets.insert(ticket)
            # Handle case where insert returns a list
            created_ticket = result[0] if isinstance(result, list) else result
            
            logger.info(f"Created ticket {created_ticket.id} with auto-embeddings")
            return created_ticket
            
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
            raise

    @staticmethod
    def get_tickets_by_status(status: str, limit: int = 50) -> List[Ticket]:
        """Get tickets by status using PyTiDB query"""
        try:
            return db_manager.tickets.query(
                filters={"status": status},
                limit=limit,
                order_by={"created_at": "desc"}
            ).to_list()
        except Exception as e:
            logger.error(f"Failed to get tickets by status: {e}")
            return []

    @staticmethod
    def get_recent_tickets(days: int = None, limit: int = 20) -> List[Ticket]:
        """Get recent tickets"""
        try:
            if days is not None:
               since_date = get_isoformat(utcnow() - timedelta(days=days))
            
            # PyTiDB query with date filter
               return db_manager.tickets.query(
                filters={"created_at": {GTE: since_date}},
                limit=limit,
                order_by={"created_at": "desc"}
                ).to_list()

            else:
             return db_manager.tickets.query(
                    limit=limit,
                    order_by={"created_at": "desc"}
                ).to_list()
        
        except Exception as e:
            logger.error(f"Failed to get recent tickets: {e}")
            return []

    @staticmethod
    def find_similar_tickets(query_text: str, limit: int = 10, include_filters: Dict = None) -> List[Dict]:
        """
        Find similar tickets using PyTiDB's hybrid search
        """
        try:
            # Build filters for resolved tickets
            filters = {"status": TicketStatus.RESOLVED.value}
            if include_filters:
                filters.update(include_filters)
        
            try:
                search_query = db_manager.tickets.search(
                    query=query_text,
                    search_type='hybrid',
                ).vector_column('description_vector').text_column('description')  
                
                # Set reasonable similarity thresholds
                search_query = search_query.distance_threshold(0.75)  # Allow moderately similar results
                
                search_query = search_query.filter(filters).fusion(method='rrf', k=60) 
                
                # Apply reranker on the description field (where the main content is)
                if reranker is not None:
                    search_query = search_query.rerank(reranker, 'description')
                
                
                results = search_query.limit(limit).to_list()
                
                logger.info(f"Hybrid search found {len(results)} similar tickets")
                
            except Exception as vector_error:
                # Fallback to full-text search with better configuration
                logger.warning(f"Hybrid search failed, falling back to text search: {vector_error}")
                results = db_manager.tickets.search(
                    query_text,
                    search_type="fulltext"
                ).text_column('description').filter(filters).limit(limit).to_list()
                
                logger.info(f"Text search found {len(results)} similar tickets")

            # Convert to expected format
            similar_tickets = []
            for result in results:
                description = get_value(result, 'description', '')
                if len(description) > 200:
                    description = description[:200] + "..."
           
                similar_tickets.append({
                    "ticket_id": get_value(result, 'id'),
                    "title": get_value(result, 'title', ''),
                    "description": description,
                    "resolution": get_value(result, 'resolution', ''),
                    "category": get_value(result, 'category', ''),
                    "priority": get_value(result, 'priority', ''),
                    "resolved_at": get_value(result, 'resolved_at'),
                    "resolution_type": get_value(result, 'resolution_type', ''),
                    "similarity_score": get_value(result, '_score', 0.0),
                    "distance": get_value(result, '_distance', 1.0)
                })
        
            logger.info(f"Returning {len(similar_tickets)} similar tickets for query: '{query_text[:50]}...'")
            return similar_tickets
        
        except Exception as e:
            logger.error(f"Failed to find similar tickets: {e}")
            return []

    @staticmethod
    def find_similar_to_ticket(ticket: Ticket, limit: int = 10) -> List[Dict]:

        """
        Find tickets similar to a given ticket using its content
        """
     
        # Use the ticket's title and description for search
        search_query = f"{get_value(ticket, 'title', '')} {get_value(ticket, 'description', '')}"
        
        # Exclude the source ticket from results
        filters = {"id": {NE: get_value(ticket, 'id', '')}}
        return TicketOperations.find_similar_tickets(query_text=search_query, 
            limit=limit, 
            include_filters=filters
        )

    @staticmethod
    def update_ticket(ticket_id: int, updates: Dict[str, Any]) -> Optional[Ticket]:

        """Update ticket with new data"""
        try:
            # Add update timestamp
            updates["updated_at"] = get_isoformat()
            
            # Update using PyTiDB
            db_manager.tickets.update(
                filters={"id": ticket_id},
                values=updates
            )
            
            # Fetch updated ticket to verify the update worked
            updated_tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_list()
            if updated_tickets and len(updated_tickets) > 0:
                logger.info(f"Updated ticket {ticket_id}")
                return updated_tickets[0]
            
            logger.warning(f"No ticket found with ID {ticket_id}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to update ticket {ticket_id}: {e}")
            return None

    @staticmethod
    def resolve_ticket(ticket_id: int, resolution: str, resolved_by: str = "ai_agent", confidence: float = 0.0) -> Optional[Ticket]:
        """Mark ticket as resolved"""
        updates = {
            "status": TicketStatus.RESOLVED.value,
            "resolution": resolution,
            "resolved_by": resolved_by,
            "resolution_type": ResolutionType.AUTOMATED.value,
            "agent_confidence": confidence,
            "resolved_at": get_isoformat()
        }
        
        return TicketOperations.update_ticket(ticket_id, updates)




# Export operations classes
__all__ = [
    "TicketOperations",
]