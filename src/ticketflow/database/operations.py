"""
PyTiDB AI-powered database operations for TicketFlow AI
Leverages automatic embeddings and built-in search capabilities
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import logging

from .models import (
    Ticket, 
    KnowledgeBaseArticle, 
    AgentWorkflow, 
    PerformanceMetrics,
    TicketStatus,
    Priority,
    ResolutionType
)
from .connection import db_manager
from pytidb.filters import GTE, NE
logger = logging.getLogger(__name__)

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
                title=ticket_data.get("title", ""),
                description=ticket_data.get("description", ""),
                category=ticket_data.get("category", "general"),
                priority=ticket_data.get("priority", Priority.MEDIUM.value),
                status=ticket_data.get("status", TicketStatus.NEW.value),
                user_id=ticket_data.get("user_id", ""),
                user_email=ticket_data.get("user_email", ""),
                user_type=ticket_data.get("user_type", "customer"),
                ticket_metadata=ticket_data.get("metadata", {})
            )
            
            # PyTiDB automatically generates embeddings for title and description!
            created_ticket = db_manager.tickets.insert(ticket)
            
            logger.info(f"✅ Created ticket {created_ticket.id} with auto-embeddings")
            return created_ticket
            
        except Exception as e:
            logger.error(f"❌ Failed to create ticket: {e}")
            raise

    @staticmethod
    def get_tickets_by_status(status: str, limit: int = 50) -> List[Ticket]:
        """Get tickets by status using PyTiDB query"""
        try:
            return db_manager.tickets.query(
                filters={"status": status},
                limit=limit,
                order_by=[("created_at", "desc")]
            )
        except Exception as e:
            logger.error(f"❌ Failed to get tickets by status: {e}")
            return []

    @staticmethod
    def get_recent_tickets(days: int = 7, limit: int = 100) -> List[Ticket]:
        """Get recent tickets"""
        try:
            since_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            # PyTiDB query with date filter
            return db_manager.tickets.query(
                filters={"created_at": {GTE: since_date}},
                limit=limit,
                order_by=[("created_at", "desc")]
            )
        except Exception as e:
            logger.error(f"❌ Failed to get recent tickets: {e}")
            return []

    @staticmethod
    def find_similar_tickets(query_text: str, limit: int = 10, include_filters: Dict = None) -> List[Dict]:
        """
        Find similar tickets using PyTiDB's built-in hybrid search
        
        This is the magic of PyTiDB - one line for intelligent search!
        """
        try:
            # Build filters for resolved tickets
            filters = {"status": TicketStatus.RESOLVED.value}
            if include_filters:
                filters.update(include_filters)
            
            # PyTiDB's built-in hybrid search (vector + full-text + reranking)
            results = db_manager.tickets.search(
                query_text,
                search_type='hybrid',  # AI-powered result reranking
            ).vector_column('description_vector').text_column('description').limit(limit).filter(filters).to_list()
            
            # Convert to our expected format - handle both objects and dicts
            similar_tickets = []
            for result in results:
                # Handle both object attributes and dictionary keys
                def get_value(obj, key, default=None):
                    if hasattr(obj, key):
                        return getattr(obj, key, default)
                    elif isinstance(obj, dict):
                        return obj.get(key, default)
                    return default
                
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
            
            logger.info(f"🔍 Found {len(similar_tickets)} similar tickets for query: '{query_text[:50]}...'")
            return similar_tickets
            
        except Exception as e:
            logger.error(f"❌ Failed to find similar tickets: {e}")
            return []

    @staticmethod
    def find_similar_to_ticket(ticket: Ticket, limit: int = 10) -> List[Dict]:
        """
        Find tickets similar to a given ticket using its content
        """
        # Use the ticket's title and description for search
        search_query = f"{ticket.title} {ticket.description}"
        
        # Exclude the source ticket from results
        filters = {"id": {NE: ticket.id}}
        
        return TicketOperations.find_similar_tickets(
            search_query, 
            limit=limit, 
            include_filters=filters
        )

    @staticmethod
    def update_ticket(ticket_id: int, updates: Dict[str, Any]) -> Optional[Ticket]:
        """Update ticket with new data"""
        try:
            # Add update timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            # Update using PyTiDB
            db_manager.tickets.update(
                filters={"id": ticket_id},
                values=updates
            )
            
            # Fetch updated ticket to verify the update worked
            updated_tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_list()
            if updated_tickets and len(updated_tickets) > 0:
                logger.info(f"✅ Updated ticket {ticket_id}")
                return updated_tickets[0]
            
            logger.warning(f"⚠️ No ticket found with ID {ticket_id}")
            return None
            
        except Exception as e:
            logger.error(f"❌ Failed to update ticket {ticket_id}: {e}")
            return None

    @staticmethod
    def resolve_ticket(ticket_id: int, resolution: str, resolved_by: str = "ai_agent", 
                      confidence: float = 0.0) -> Optional[Ticket]:
        """Mark ticket as resolved"""
        updates = {
            "status": TicketStatus.RESOLVED.value,
            "resolution": resolution,
            "resolved_by": resolved_by,
            "resolution_type": ResolutionType.AUTOMATED.value,
            "agent_confidence": confidence,
            "resolved_at": datetime.utcnow().isoformat()
        }
        
        return TicketOperations.update_ticket(ticket_id, updates)

class KnowledgeBaseOperations:
    """
    Knowledge base operations with PyTiDB AI features
    """

    @staticmethod
    def create_article(article_data: Dict[str, Any]) -> KnowledgeBaseArticle:
        """Create KB article - PyTiDB auto-generates embeddings!"""
        try:
            article = KnowledgeBaseArticle(
                title=article_data.get("title", ""),
                content=article_data.get("content", ""),
                summary=article_data.get("summary", ""),
                category=article_data.get("category", "general"),
                tags=article_data.get("tags", []),
                source_url=article_data.get("source_url", ""),
                source_type=article_data.get("source_type", "manual"),
                author=article_data.get("author", "")
            )
            
            # PyTiDB automatically generates embeddings for title, content, and summary!
            created_article = db_manager.kb_articles.insert(article)
            
            logger.info(f"📚 Created KB article {created_article.id} with auto-embeddings")
            return created_article
            
        except Exception as e:
            logger.error(f"❌ Failed to create KB article: {e}")
            raise

    @staticmethod
    def search_articles(query: str, category: str = None, limit: int = 5) -> List[Dict]:
        """
        Search knowledge base using PyTiDB's intelligent search
        """
        try:
            filters = {}
            if category:
                filters["category"] = category
            
            # PyTiDB's built-in hybrid search on KB articles
            results = db_manager.kb_articles.search(
                query,
                search_type='hybrid'      
            ).vector_column('content_vector').text_column('content').limit(limit).filter(filters).to_list()
            
            # Convert to our format - handle both objects and dicts
            articles = []
            for result in results:
                # Handle both object attributes and dictionary keys
                def get_value(obj, key, default=None):
                    if hasattr(obj, key):
                        return getattr(obj, key, default)
                    elif isinstance(obj, dict):
                        return obj.get(key, default)
                    return default
                
                content = get_value(result, 'content', '')
                if len(content) > 300:
                    content = content[:300] + "..."
                
                # Calculate helpfulness score if it's not available
                helpful_votes = get_value(result, 'helpful_votes', 0)
                unhelpful_votes = get_value(result, 'unhelpful_votes', 0)
                total_votes = helpful_votes + unhelpful_votes
                helpfulness_score = (helpful_votes / total_votes) if total_votes > 0 else 0.0
                
                articles.append({
                    "article_id": get_value(result, 'id'),
                    "title": get_value(result, 'title', ''),
                    "content": content,
                    "summary": get_value(result, 'summary', ''),
                    "category": get_value(result, 'category', ''),
                    "tags": get_value(result, 'tags', []),
                    "source_url": get_value(result, 'source_url', ''),
                    "author": get_value(result, 'author', ''),
                    "helpfulness_score": helpfulness_score,
                    "similarity_score": get_value(result, '_score', 0.0),
                    "usage_count": get_value(result, 'usage_in_resolutions', 0)
                })
            
            logger.info(f"📖 Found {len(articles)} relevant articles for: '{query[:50]}...'")
            return articles
            
        except Exception as e:
            logger.error(f"❌ Failed to search articles: {e}")
            return []

    @staticmethod
    def get_articles_by_category(category: str, limit: int = 20) -> List[KnowledgeBaseArticle]:
        """Get articles by category"""
        try:
            return db_manager.kb_articles.query(
                filters={"category": category},
                limit=limit,
                order_by=[("created_at", "desc")]
            )
        except Exception as e:
            logger.error(f"❌ Failed to get articles by category: {e}")
            return []

    @staticmethod
    def update_article_usage(article_id: int, was_helpful: bool = True):
        """Track article usage and helpfulness"""
        try:
            # Get current article
            articles = db_manager.kb_articles.query(filters={"id": article_id}, limit=1).to_list()
            if not articles:
                return
            
            article = articles[0]
            # Handle the case where attributes might be dict keys instead of attributes
            usage_count = getattr(article, 'usage_in_resolutions', 0) if hasattr(article, 'usage_in_resolutions') else article.get('usage_in_resolutions', 0)
            view_count = getattr(article, 'view_count', 0) if hasattr(article, 'view_count') else article.get('view_count', 0)
            helpful_votes = getattr(article, 'helpful_votes', 0) if hasattr(article, 'helpful_votes') else article.get('helpful_votes', 0)
            unhelpful_votes = getattr(article, 'unhelpful_votes', 0) if hasattr(article, 'unhelpful_votes') else article.get('unhelpful_votes', 0)
            
            # Update usage stats
            updates = {
                "usage_in_resolutions": usage_count + 1,
                "view_count": view_count + 1,
                "last_accessed": datetime.utcnow().isoformat()
            }
            
            if was_helpful:
                updates["helpful_votes"] = helpful_votes + 1
            else:
                updates["unhelpful_votes"] = unhelpful_votes + 1
            
            db_manager.kb_articles.update(
                filters={"id": article_id},
                values=updates
            )
            
            logger.info(f"📊 Updated usage stats for article {article_id}")
            
        except Exception as e:
            logger.error(f"❌ Failed to update article usage: {e}")

class WorkflowOperations:
    """
    Agent workflow operations
    """

    @staticmethod
    def create_workflow(ticket_id: int, initial_steps: List[Dict] = None) -> AgentWorkflow:
        """Create new agent workflow"""
        try:
            workflow = AgentWorkflow(
                ticket_id=ticket_id,
                workflow_steps=initial_steps or [],
                total_duration_ms=0,
                status="running"
            )
            
            created_workflow = db_manager.agent_workflows.insert(workflow)
            logger.info(f"🔄 Created workflow {created_workflow.id} for ticket {ticket_id}")
            return created_workflow
            
        except Exception as e:
            logger.error(f"❌ Failed to create workflow: {e}")
            raise

    @staticmethod
    def update_workflow_step(workflow_id: int, step_data: Dict[str, Any]) -> bool:
        """Add step to workflow"""
        try:
            # Get current workflow
            workflows = db_manager.agent_workflows.query(filters={"id": workflow_id}, limit=1).to_list()
            if not workflows:
                logger.warning(f"⚠️ Workflow {workflow_id} not found")
                return False
            
            workflow = workflows[0]
            
            # Add timestamp to step
            step_data["timestamp"] = datetime.utcnow().isoformat()
            
            # Update workflow steps - handle both objects and dicts
            if hasattr(workflow, 'workflow_steps'):
                current_steps = workflow.workflow_steps or []
            else:
                current_steps = workflow.get('workflow_steps', [])
            
            current_steps.append(step_data)
            
            db_manager.agent_workflows.update(
                filters={"id": workflow_id},
                values={"workflow_steps": current_steps}
            )
            
            logger.info(f"🔄 Added step to workflow {workflow_id}: {step_data.get('step', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update workflow step: {e}")
            return False

    @staticmethod
    def complete_workflow(workflow_id: int, final_confidence: float = 0.0, 
                         total_duration_ms: int = 0) -> bool:
        """Mark workflow as completed"""
        try:
            updates = {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
                "final_confidence": final_confidence,
                "total_duration_ms": total_duration_ms
            }
            
            db_manager.agent_workflows.update(
                filters={"id": workflow_id},
                values=updates
            )
            
            logger.info(f"✅ Completed workflow {workflow_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to complete workflow: {e}")
            return False

class AnalyticsOperations:
    """
    Performance analytics and metrics operations
    """

    @staticmethod
    def get_dashboard_metrics() -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        try:
            # Get today's tickets
            today = datetime.utcnow().date().isoformat()
            today_tickets = db_manager.tickets.query(
                filters={"created_at": {GTE: today}},
                limit=1000  # Reasonable limit for today
            ).to_list()
            
            # Calculate metrics - handle both objects and dicts
            total_today = len(today_tickets)
            auto_resolved_today = 0
            processing = 0
            
            for t in today_tickets:
                status = getattr(t, 'status', None) if hasattr(t, 'status') else t.get('status')
                if status == TicketStatus.RESOLVED.value:
                    auto_resolved_today += 1
                elif status == TicketStatus.PROCESSING.value:
                    processing += 1
            
            # Get recent resolved tickets for avg confidence
            resolved_tickets = db_manager.tickets.query(
                filters={"status": TicketStatus.RESOLVED.value},
                limit=100, order_by={"resolved_at": "desc"}
            ).to_list()
            
            avg_confidence = 0.0
            if resolved_tickets:
                confidences = []
                for t in resolved_tickets:
                    confidence = getattr(t, 'agent_confidence', 0) if hasattr(t, 'agent_confidence') else t.get('agent_confidence', 0)
                    if confidence > 0:
                        confidences.append(confidence)
                
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
            
            return {
                "tickets_today": total_today,
                "tickets_auto_resolved_today": auto_resolved_today,
                "currently_processing": processing,
                "avg_confidence": avg_confidence,
                "automation_rate": (auto_resolved_today / total_today * 100) if total_today > 0 else 0,
                "resolution_rate": (auto_resolved_today / total_today * 100) if total_today > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard metrics: {e}")
            return {
                "tickets_today": 0,
                "tickets_auto_resolved_today": 0,
                "currently_processing": 0,
                "avg_confidence": 0.0,
                "automation_rate": 0.0,
                "resolution_rate": 0.0
            }

    @staticmethod
    def create_daily_metrics(date: str = None) -> PerformanceMetrics:
        """Create daily performance metrics"""
        target_date = date or datetime.utcnow().date().isoformat()
        
        try:
            # Get tickets for the day
            day_tickets = db_manager.tickets.query(
                filters={"created_at": {GTE: target_date}},
                limit=10000  # Large limit for full day
            ).to_list() 
            
            # Calculate metrics - handle both objects and dicts
            total = len(day_tickets)
            auto_resolved = 0
            escalated = 0
            
            # Category breakdown
            categories = {}
            for ticket in day_tickets:
                # Handle both object attributes and dictionary keys
                resolution_type = getattr(ticket, 'resolution_type', None) if hasattr(ticket, 'resolution_type') else ticket.get('resolution_type')
                status = getattr(ticket, 'status', None) if hasattr(ticket, 'status') else ticket.get('status')
                category = getattr(ticket, 'category', 'general') if hasattr(ticket, 'category') else ticket.get('category', 'general')
                
                if resolution_type == ResolutionType.AUTOMATED.value:
                    auto_resolved += 1
                if status == TicketStatus.ESCALATED.value:
                    escalated += 1
                    
                categories[category] = categories.get(category, 0) + 1
            
            # Create metrics record
            metrics = PerformanceMetrics(
                metric_date=target_date,
                tickets_processed=total,
                tickets_auto_resolved=auto_resolved,
                tickets_escalated=escalated,
                category_breakdown=categories,
                estimated_time_saved_hours=auto_resolved * 0.25,  # 15 min per ticket
                estimated_cost_saved=auto_resolved * 12.5  # $50/hour * 0.25 hours
            )
            
            created_metrics = db_manager.performance_metrics.insert(metrics)
            logger.info(f"📊 Created daily metrics for {target_date}")
            return created_metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to create daily metrics: {e}")
            raise

# Export operations classes
__all__ = [
    "TicketOperations",
    "KnowledgeBaseOperations", 
    "WorkflowOperations",
    "AnalyticsOperations"
]