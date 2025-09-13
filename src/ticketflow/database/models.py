"""
PyTiDB AI-powered models for TicketFlow AI
Features automatic embeddings, vector search, and hybrid search
"""

from pytidb.schema import TableModel, Field, VectorField, FullTextField, Relationship
from sqlalchemy.schema import Index
from pytidb.datatype import TEXT, JSON
from pytidb.embeddings import EmbeddingFunction
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import numpy as np
from pydantic import field_serializer
from ticketflow.config import config


text_embed = EmbeddingFunction(model_name='jina_ai/jina-embeddings-v4',api_key=config.JINA_API_KEY)


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

class WorkflowStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class SettingType(str, Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    JSON = "json"
    ENCRYPTED = "encrypted"  # For sensitive data like tokens

class SettingCategory(str, Enum):
    SLACK = "slack"
    EMAIL = "email"
    NOTIFICATIONS = "notifications"
    SYSTEM = "system"
    AGENT = "agent"
    SECURITY = "security"

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
    title: str = FullTextField( description="Ticket title - auto-embedded",)
    description: str = FullTextField( description="Detailed description - auto-embedded",)
    title_vector: Optional[list[float]] = text_embed.VectorField(source_field='title', description="Vector embedding for title")
    description_vector: Optional[list[float]] = text_embed.VectorField(source_field='description', description="Vector embedding for description")
    
    @field_serializer('title_vector', 'description_vector')
    def serialize_vector(self, value: Any) -> Optional[List[float]]:
        """Convert numpy arrays to lists for JSON serialization"""
        if value is None:
            return None
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value
    # Categorical fields
    category: str = Field(max_length=100,default="general", description="Ticket category (account, billing, technical, etc.)")
    priority: str = Field(default=Priority.MEDIUM.value, description="Ticket priority level")
    status: str = Field(default=TicketStatus.NEW.value, description="Current ticket status")
    
    # User information
    user_id: str = Field(max_length=100,default="", description="User identifier")
    user_email: str = Field(max_length=255,default="", description="User email address")
    user_type: str = Field(max_length=50,default="customer", description="Type of user (customer, internal, partner)")
    
    # Resolution tracking
    resolution: str = Field(sa_type=TEXT,default="", description="Resolution details")
    resolved_by: str = Field(max_length=100,default="", description="Who resolved the ticket (agent name or 'ai_agent')")
    resolution_type: str = Field(default=ResolutionType.AUTOMATED.value, description="How was it resolved")
    
    # Agent processing metadata
    agent_confidence: float = Field(default=0.0, description="AI agent confidence score (0.0-1.0)")
    processing_duration_ms: int = Field(default=0, description="Time taken to process in milliseconds")
    similar_cases_found: int = Field(default=0, description="Number of similar cases found")
    kb_articles_used: int = Field(default=0, description="Number of KB articles referenced")
    
    # Workflow and metadata (JSON fields for flexibility)
    workflow_steps: List[Dict] = Field(sa_type=JSON, default_factory=list, description="Agent workflow execution steps")
    ticket_metadata: Dict = Field(sa_type=JSON, default_factory=dict, description="Additional ticket metadata")
    
    # Timestamps (ISO format for consistency)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Last update timestamp")
    resolved_at: Optional[str] = Field(default=None, description="Resolution timestamp")


    workflows = Relationship(sa_relationship="AgentWorkflow", back_populates="ticket")
    class Config:
        # Enable PyTiDB's automatic embedding generation
        auto_embed_text_fields = True  # This tells PyTiDB to create vectors for text fields
        embedding_model = "jina_ai"    # Use Jina AI's embedding model
        enable_hybrid_search = True    # Enable vector + full-text search
       
    __table_args__ = (
        Index('idx_status_priority', 'status', 'priority'),
        Index('idx_category_status', 'category', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_user_id', 'user_id'),
        Index('idx_resolution_type', 'resolution_type'),
    )

class KnowledgeBaseArticle(TableModel):
    """
    AI-Powered Knowledge Base with Automatic Embeddings
    
    Auto-embeds title and content for semantic search
    Built-in similarity search capabilities
    Usage analytics tracking
    """
    __tablename__ = "kb_articles"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Content fields - automatically embedded by PyTiDB!
    title: str = FullTextField(description="Article title - auto-embedded")
    content: str = FullTextField(description="Article content - auto-embedded for search")
    summary: str = FullTextField(default="",description="Article summary - also auto-embedded")
    title_vector: Optional[list[float]] = text_embed.VectorField(source_field='title', description="Vector embedding for title")
    content_vector: Optional[list[float]] = text_embed.VectorField(source_field='content', description="Vector embedding for content")

    @field_serializer('title_vector', 'content_vector')
    def serialize_vector(self, value: Any) -> Optional[List[float]]:
        """Convert numpy arrays to lists for JSON serialization"""
        if value is None:
            return None
        if isinstance(value, np.ndarray):
            return value.tolist()
        return value
    # Organization
    category: str = Field(description="Article category",nullable=False)
    tags: List[str] = Field(sa_type=JSON, default_factory=list, description="Article tags")
    
    # Source tracking
    source_url: str = Field(max_length=1000, default="", description="Original source URL if crawled")
    source_type: str = Field(max_length=50,default="manual", description="manual, crawled, or imported",nullable=False)  # 'manual', 'crawled', 'imported'
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
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), sa_column_kwargs={"onupdate": lambda: datetime.utcnow().isoformat()})
    last_accessed: Optional[str] = Field(default=None, description="Last time article was accessed")

    class Config:
        # Enable PyTiDB's automatic embedding generation
        auto_embed_text_fields = True  # This tells PyTiDB to create vectors for text fields
        embedding_model = "jina_ai"    # Use Jina AI's embedding model
        enable_hybrid_search = True    # Enable vector + full-text search

    __table_args__ = (
        Index('idx_kb_category', 'category'),
        Index('idx_kb_source_type', 'source_type'),
        Index('idx_kb_updated_at', 'updated_at'),
    )
class AgentWorkflow(TableModel):
    """
    Agent Workflow Execution Tracking
    
    Tracks AI agent decision-making process
    Performance analytics and debugging
    Searchable workflow history
    """
    __tablename__ = "agent_workflows"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Link to ticket
    ticket_id: int = Field(description="ID of the ticket being processed", foreign_key="tickets.id", index=True,nullable=False)

    # Workflow execution data
    workflow_steps: List[Dict] = Field(sa_type=JSON, description="Detailed step-by-step execution log",nullable=False)
    total_duration_ms: int = Field(description="Total workflow execution time",nullable=False)
    final_confidence: float = Field(default=0.0, description="Final confidence score")
    
    # Search and analysis results
    similar_cases_found: List[Dict] = Field(sa_type=JSON, default_factory=list, description="Similar tickets found")
    kb_articles_used: List[Dict] = Field(sa_type=JSON, default_factory=list, description="KB articles referenced")
    actions_executed: List[Dict] = Field(sa_type=JSON, default_factory=list, description="Actions taken by agent")
    
    # LLM interaction logs
    llm_calls: List[Dict] = Field(sa_type=JSON, default_factory=list, description="LLM API calls and responses")
    
    # Status tracking
    status: str = Field(default="running", description="running, completed, failed, cancelled",nullable=False)
    error_message: str = Field(sa_type=TEXT,default="", description="Error details if failed")
    
    # Performance metrics
    embedding_time_ms: int = Field(default=0, description="Time spent generating embeddings")
    search_time_ms: int = Field(default=0, description="Time spent on similarity search")
    llm_time_ms: int = Field(default=0, description="Time spent on LLM calls")
    
    # Timestamps
    started_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = Field(default=None)

    # Relationship to Ticket
    ticket = Relationship(sa_relationship="Ticket", back_populates="workflows")
    class Config:
        # Don't auto-embed workflow data (it's operational, not content)
        auto_embed_text_fields = False

    __table_args__ = (
        Index('idx_workflow_ticket_id', 'ticket_id'),
        Index('idx_workflow_status', 'status'),
        Index('idx_workflow_started_at', 'started_at'),
        Index('idx_workflow_completed_at', 'completed_at'),
    )

class PerformanceMetrics(TableModel):
    """
    Pre-computed Performance Analytics (pre-computed for dashboard)
    
    Dashboard metrics and KPIs
    Trend analysis over time
    ROI and cost savings tracking
    """
    __tablename__ = "performance_metrics"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Time period
    metric_date: str = Field(description="Date for this metric period (YYYY-MM-DD)",nullable=False)
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
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), sa_column_kwargs={"onupdate": lambda: datetime.utcnow().isoformat()})
    class Config:
        # Don't auto-embed workflow data (it's operational, not content)
        auto_embed_text_fields = False

    __table_args__ = (
        Index('unique_metric_period', 'metric_date', 'metric_hour', unique=True),
        Index('idx_metric_date', 'metric_date'),
    )
# Export all models
class ProcessingTask(TableModel):
    """
    Background Processing Task Tracking
    
    Tracks status of file uploads, URL processing, and other async operations
    Provides real-time status updates for knowledge base operations
    """
    __tablename__ = "processing_tasks"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Task identification
    task_type: str = Field(max_length=50, description="Type of task: file_upload, url_scrape, etc.", nullable=False)
    task_id: str = Field(max_length=100, description="Unique task identifier", nullable=False, index=True)
    
    # Task details
    source_name: str = Field(max_length=500, description="Original filename or URL", nullable=False)
    status: str = Field(max_length=20, default="pending", description="pending, processing, completed, failed", nullable=False)
    progress_percentage: int = Field(default=0, description="Progress from 0-100")
    
    # Results
    result_data: Dict = Field(sa_type=JSON, default_factory=dict, description="Task results and metadata")
    error_message: str = Field(sa_type=TEXT, default="", description="Error details if failed")
    
    # Timing
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    started_at: Optional[str] = Field(default=None, description="When processing actually started")
    completed_at: Optional[str] = Field(default=None, description="When task finished")
    
    # Optional metadata
    user_metadata: Dict = Field(sa_type=JSON, default_factory=dict, description="User-provided metadata")
    
    class Config:
        auto_embed_text_fields = False  # No need to embed task data
    
    __table_args__ = (
        Index('idx_task_id', 'task_id'),
        Index('idx_task_status', 'status'),
        Index('idx_task_type', 'task_type'),
        Index('idx_created_at', 'created_at'),
    )

class Settings(TableModel):
    """
    Application Settings Model
    
    Stores all application configuration settings with support for:
    - Different data types (string, int, float, boolean, json, encrypted)
    - Categorization (slack, email, notifications, system, etc.)
    - Encryption for sensitive data (API tokens, passwords)
    - Enable/disable functionality
    - Default values and validation
    """
    __tablename__ = "settings"
    
    # Primary key
    id: int = Field(primary_key=True)
    
    # Setting identification
    key: str = Field(max_length=100, description="Unique setting key (e.g., 'slack_bot_token')", nullable=False, index=True)
    category: str = Field(max_length=50, description="Setting category for organization", nullable=False, index=True)
    
    # Setting metadata
    name: str = Field(max_length=200, description="Human-readable setting name", nullable=False)
    description: str = Field(sa_type=TEXT, description="Detailed description of the setting", default="")
    setting_type: str = Field(max_length=20, description="Data type: string, integer, float, boolean, json, encrypted", nullable=False)
    
    # Setting value and state
    value: str = Field(sa_type=TEXT, description="Setting value (encrypted if sensitive)", default="")
    default_value: str = Field(sa_type=TEXT, description="Default value for the setting", default="")
    is_enabled: bool = Field(default=True, description="Whether this setting is enabled/active")
    is_required: bool = Field(default=False, description="Whether this setting is required for functionality")
    is_sensitive: bool = Field(default=False, description="Whether this setting contains sensitive data (will be encrypted)")
    
    # Validation and constraints
    validation_rules: Dict = Field(sa_type=JSON, default_factory=dict, description="Validation rules (min, max, regex, etc.)")
    allowed_values: List[str] = Field(sa_type=JSON, default_factory=list, description="List of allowed values (for enum-like settings)")
    
    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Creation timestamp")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="Last update timestamp")
    updated_by: str = Field(max_length=100, default="system", description="Who last updated this setting")
    
    class Config:
        auto_embed_text_fields = False  # No need to embed settings data
    
    __table_args__ = (
        Index('idx_settings_key', 'key'),
        Index('idx_settings_category', 'category'),
        Index('idx_settings_enabled', 'is_enabled'),
        Index('idx_settings_required', 'is_required'),
    )

__all__ = [
    "Ticket",
    "KnowledgeBaseArticle", 
    "AgentWorkflow",
    "PerformanceMetrics",
    "ProcessingTask",
    "Settings",
    "TicketStatus",
    "Priority", 
    "ResolutionType",
    "WorkflowStatus",
    "SettingType",
    "SettingCategory"
]