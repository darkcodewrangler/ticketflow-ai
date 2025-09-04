"""
SQLAlchemy models for TicketFlow AI database
These represent database tables as Python classes
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, DECIMAL, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .connection import Base
import enum
from tidb_vector.sqlalchemy import VectorType

# Enums for consistent values
class TicketStatus(str, enum.Enum):
    NEW = "new"
    PROCESSING = "processing"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class ResolutionType(str, enum.Enum):
    AUTOMATED = "automated"
    HUMAN = "human"
    ESCALATED = "escalated"

# Main Models
class Ticket(Base):
    """Main tickets table with vector support"""
    __tablename__ = "tickets"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Basic ticket information
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(Enum(Priority), nullable=False, default=Priority.MEDIUM)
    status = Column(Enum(TicketStatus), nullable=False, default=TicketStatus.NEW)
    
    # User information
    user_id = Column(String(100))
    user_email = Column(String(255))
    user_type = Column(String(50), default="customer")
    
    # Resolution information
    resolution = Column(Text)
    resolved_by = Column(String(100))  # agent name or 'smartsupport_agent'
    resolution_type = Column(Enum(ResolutionType), default=ResolutionType.AUTOMATED)
    
    # Agent processing metadata
    agent_confidence = Column(DECIMAL(5, 4))  # 0.0000 to 1.0000
    processing_duration_ms = Column(Integer)
    similar_cases_found = Column(Integer, default=0)
    kb_articles_used = Column(Integer, default=0)
    
    # TiDB native VECTOR columns (2048 dimensions for text-embeddings)
    title_vector = Column(VectorType(2048))
    description_vector = Column(VectorType(2048))
    combined_vector = Column(VectorType(2048))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    
    # Relationships
    workflows = relationship("AgentWorkflow", back_populates="ticket")
    
    # Indexes (SQLAlchemy will create these)
    __table_args__ = (
        Index('idx_status_priority', 'status', 'priority'),
        Index('idx_category_status', 'category', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_user_id', 'user_id'),
        Index('idx_resolution_type', 'resolution_type'),
    )

class KnowledgeBaseArticle(Base):
    """Knowledge base articles with vector embeddings"""
    __tablename__ = "kb_articles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Article content
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    category = Column(String(100), nullable=False)
    tags = Column(JSON)  # Array of tags for flexible categorization
    
    # Source information
    source_url = Column(String(1000))
    source_type = Column(String(50), nullable=False)  # 'manual', 'crawled', 'imported'
    author = Column(String(255))
    
    # Usage analytics
    view_count = Column(Integer, default=0)
    helpful_votes = Column(Integer, default=0)
    unhelpful_votes = Column(Integer, default=0)
    last_accessed = Column(DateTime(timezone=True))
    
    # Vector embeddings (2048 dimensions for text-embeddings)
    title_vector = Column(VectorType(2048))
    content_vector = Column(VectorType(2048))
    summary_vector = Column(VectorType(2048))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes
    __table_args__ = (
        Index('idx_kb_category', 'category'),
        Index('idx_kb_source_type', 'source_type'),
        Index('idx_kb_updated_at', 'updated_at'),
    )

class AgentWorkflow(Base):
    """Agent workflow execution logs"""
    __tablename__ = "agent_workflows"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ticket_id = Column(Integer, ForeignKey('tickets.id'), nullable=False)
    
    # Workflow execution data
    workflow_steps = Column(JSON, nullable=False)  # Array of step objects
    total_duration_ms = Column(Integer, nullable=False)
    final_confidence = Column(DECIMAL(5, 4))
    
    # Results
    similar_cases_found = Column(JSON)  # Array of similar case IDs and scores
    kb_articles_used = Column(JSON)  # Array of KB article IDs and relevance
    actions_executed = Column(JSON)  # Array of executed actions and results
    
    # Status
    status = Column(String(50), nullable=False, default="running")  # 'running', 'completed', 'failed', 'cancelled'
    error_message = Column(Text)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    ticket = relationship("Ticket", back_populates="workflows")
    
    # Indexes
    __table_args__ = (
        Index('idx_workflow_ticket_id', 'ticket_id'),
        Index('idx_workflow_status', 'status'),
        Index('idx_workflow_started_at', 'started_at'),
        Index('idx_workflow_completed_at', 'completed_at'),
    )

class PerformanceMetrics(Base):
    """Performance metrics and analytics (pre-computed for dashboard)"""
    __tablename__ = "performance_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time period
    metric_date = Column(DateTime(timezone=True), nullable=False)
    metric_hour = Column(Integer)  # NULL for daily metrics, 0-23 for hourly
    
    # Core metrics
    tickets_processed = Column(Integer, default=0)
    tickets_auto_resolved = Column(Integer, default=0)
    tickets_escalated = Column(Integer, default=0)
    avg_confidence_score = Column(DECIMAL(5, 4))
    avg_processing_time_ms = Column(Integer)
    avg_resolution_time_hours = Column(DECIMAL(8, 2))
    
    # Quality metrics
    customer_satisfaction_avg = Column(DECIMAL(3, 2))  # 1.00 to 5.00
    resolution_accuracy_rate = Column(DECIMAL(5, 4))  # Percentage
    
    # Category breakdown (JSON for flexibility)
    category_breakdown = Column(JSON)  # {"technical": 45, "billing": 23}
    priority_breakdown = Column(JSON)  # {"high": 5, "medium": 30, "low": 65}
    
    # Cost savings estimates
    estimated_time_saved_hours = Column(DECIMAL(8, 2))
    estimated_cost_saved = Column(DECIMAL(10, 2))
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Unique constraint to prevent duplicates
    __table_args__ = (
        Index('unique_metric_period', 'metric_date', 'metric_hour', unique=True),
        Index('idx_metric_date', 'metric_date'),
    )