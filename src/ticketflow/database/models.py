"""
PyTiDB AI-powered models for TicketFlow AI
Features automatic embeddings, vector search, and hybrid search
"""

from pytidb.schema import TableModel, Field, VectorField, FullTextField
from pytidb.datatype import TEXT, JSON
from pytidb.embeddings import EmbeddingFunction
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

from ..config import config

text_embed = EmbeddingFunction(model_name='jina_ai/jina-embeddings-v4', api_key=config.JINA_API_KEY)

# Enums for data consistency
class TicketStatus(str, Enum):
    NEW = "new"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class Priority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ResolutionType(str, Enum):
    AUTOMATED = "automated"
    HUMAN = "human"
    ESCALATED = "escalated"

class Ticket(TableModel):
    """
    AI-Powered Ticket Model with Automatic Embeddings
    
    PyTiDB automatically creates embeddings for title and description!
    Built-in vector similarity search
    Hybrid search (vector + full-text) support
    """
    __tablename__ = "tickets"
    
    # Primary key (auto-increment)
    id: int = Field(primary_key=True)
    
    # Core ticket data - PyTiDB will auto-embed these text fields!
    title: str = FullTextField(sa_type=TEXT, description="Ticket title - auto-embedded")
    description: str = FullTextField(sa_type=TEXT, description="Detailed description - auto-embedded")
    title_vector: list[float] = text_embed.VectorField(source_field='title',description="Vector embedding for title")
    description_vector: list[float] = text_embed.VectorField(source_field='description',description="Vector embedding for description")
    # Categorical fields
    category: str = Field(default="general", description="Ticket category (account, billing, technical, etc.)")
    priority: str = Field(default=Priority.MEDIUM.value, description="Ticket priority level")
    status: str = Field(default=TicketStatus.NEW.value, description="Current ticket status")
    
    # User information
    user_id: str = Field(default="", description="User identifier")
    user_email: str = Field(default="", description="User email address")
    user_type: str = Field(default="customer", description="Type of user (customer, internal, partner)")
    
    # Resolution tracking
    resolution: str = Field(sa_type=TEXT, default="", description="Resolution details")
    resolved_by: str = Field(default="", description="Who resolved the ticket (agent name or 'ai_agent')")
    resolution_type: str = Field(default=ResolutionType.AUTOMATED.value, description="How was it resolved")
    
    # Agent processing metadata
    agent_confidence: float = Field(default=0.0, description="AI agent confidence score (0.0-1.0)")
    processing_duration_ms: int = Field(default=0, description="Time taken to process in milliseconds")
    similar_cases_found: int = Field(default=0, description="Number of similar cases found")
    kb_articles_used: int = Field(default=0, description="Number of KB articles referenced")
    
    # Workflow and metadata (JSON fields for flexibility)
    workflow_steps: List[Dict] = Field(sa_type=JSON, default_factory=list, description="Agent workflow execution steps")
    metadata: Dict = Field(sa_type=JSON, default_factory=dict, description="Additional metadata")
    
    # Timestamps (ISO format for consistency)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Last update timestamp")
    resolved_at: Optional[str] = Field(default=None, description="Resolution timestamp")


class KnowledgeBaseArticle(TableModel):
    """
    AI-Powered Knowledge Base with Automatic Embeddings
    
    🤖 Auto-embeds title and content for semantic search
    🔍 Built-in similarity search capabilities
    📊 Usage analytics tracking
    """
    __tablename__ = "kb_articles"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Content fields - automatically embedded by PyTiDB!
    title: str = Field(sa_type=TEXT, description="Article title - auto-embedded")
    content: str = Field(sa_type=TEXT, description="Article content - auto-embedded for search")
    summary: str = Field(sa_type=TEXT, default="", description="Article summary - also auto-embedded")
    title_vector:list[float]= VectorField(description="Vector embedding for title")
    # Organization
    category: str = Field(description="Article category")
    tags: List[str] = Field(sa_type=JSON, default_factory=list, description="Article tags")
    
    # Source tracking
    source_url: str = Field(default="", description="Original source URL if crawled")
    source_type: str = Field(default="manual", description="manual, crawled, or imported")
    author: str = Field(default="", description="Article author")
    
    # Analytics - track article effectiveness
    view_count: int = Field(default=0, description="Number of times viewed")
    helpful_votes: int = Field(default=0, description="Number of helpful votes")
    unhelpful_votes: int = Field(default=0, description="Number of unhelpful votes")
    usage_in_resolutions: int = Field(default=0, description="Times used to resolve tickets")
    
    # Computed helpfulness score
    @property
    def helpfulness_score(self) -> float:
        """Calculate helpfulness percentage"""
        total_votes = self.helpful_votes + self.unhelpful_votes
        if total_votes == 0:
            return 0.0
        return self.helpful_votes / total_votes
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    last_accessed: Optional[str] = Field(default=None, description="Last time article was accessed")


class AgentWorkflow(TableModel):
    """
    Agent Workflow Execution Tracking
    
    🤖 Tracks AI agent decision-making process
    📊 Performance analytics and debugging
    🔍 Searchable workflow history
    """
    __tablename__ = "agent_workflows"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Link to ticket
    ticket_id: int = Field(description="ID of the ticket being processed")
    
    # Workflow execution data
    workflow_steps: List[Dict] = Field(sa_type=JSON, description="Detailed step-by-step execution log")
    total_duration_ms: int = Field(description="Total workflow execution time")
    final_confidence: float = Field(default=0.0, description="Final confidence score")
    
    # Search and analysis results
    similar_cases_found: List[Dict] = Field(sa_type=JSON, default_factory=list, description="Similar tickets found")
    kb_articles_used: List[Dict] = Field(sa_type=JSON, default_factory=list, description="KB articles referenced")
    actions_executed: List[Dict] = Field(sa_type=JSON, default_factory=list, description="Actions taken by agent")
    
    # LLM interaction logs
    llm_calls: List[Dict] = Field(sa_type=JSON, default_factory=list, description="LLM API calls and responses")
    
    # Status tracking
    status: str = Field(default="running", description="running, completed, failed, cancelled")
    error_message: str = Field(default="", description="Error details if failed")
    
    # Performance metrics
    embedding_time_ms: int = Field(default=0, description="Time spent generating embeddings")
    search_time_ms: int = Field(default=0, description="Time spent on similarity search")
    llm_time_ms: int = Field(default=0, description="Time spent on LLM calls")
    
    # Timestamps
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = Field(default=None)

    class Config:
        # Don't auto-embed workflow data (it's operational, not content)
        auto_embed_text_fields = False

class PerformanceMetrics(TableModel):
    """
    Pre-computed Performance Analytics
    
    📊 Dashboard metrics and KPIs
    📈 Trend analysis over time
    💰 ROI and cost savings tracking
    """
    __tablename__ = "performance_metrics"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Time period
    metric_date: str = Field(description="Date for this metric period (YYYY-MM-DD)")
    metric_hour: Optional[int] = Field(default=None, description="Hour (0-23) for hourly metrics, null for daily")
    
    # Core performance metrics
    tickets_processed: int = Field(default=0)
    tickets_auto_resolved: int = Field(default=0) 
    tickets_escalated: int = Field(default=0)
    avg_confidence_score: float = Field(default=0.0)
    avg_processing_time_ms: int = Field(default=0)
    avg_resolution_time_hours: float = Field(default=0.0)
    
    # Quality metrics
    customer_satisfaction_avg: float = Field(default=0.0, description="Average satisfaction score (1-5)")
    resolution_accuracy_rate: float = Field(default=0.0, description="Percentage of accurate auto-resolutions")
    
    # Category and priority breakdowns
    category_breakdown: Dict = Field(sa_type=JSON, default_factory=dict, description="Tickets by category")
    priority_breakdown: Dict = Field(sa_type=JSON, default_factory=dict, description="Tickets by priority")
    
    # Business impact
    estimated_time_saved_hours: float = Field(default=0.0, description="Estimated human time saved")
    estimated_cost_saved: float = Field(default=0.0, description="Estimated cost savings in dollars")
    
    # Timestamps
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    class Config:
        auto_embed_text_fields = False  # Metrics don't need embedding

# Export all models
__all__ = [
    "Ticket",
    "KnowledgeBaseArticle", 
    "AgentWorkflow",
    "PerformanceMetrics",
    "TicketStatus",
    "Priority", 
    "ResolutionType"
]