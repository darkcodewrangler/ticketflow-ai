"""
PyTiDB package for TicketFlow AI
AI-powered database operations with automatic embeddings and intelligent search
"""

from .connection import db_manager, PyTiDBManager
from .models import (
    Ticket, 
    KnowledgeBaseArticle, 
    AgentWorkflow, 
    PerformanceMetrics,
    TicketStatus,
    Priority,
    ResolutionType
)
from .operations import (
    TicketOperations,
    KnowledgeBaseOperations,
    WorkflowOperations,
    AnalyticsOperations
)

__all__ = [
    # Connection management
    "db_manager",
    "PyTiDBManager",
    
    # Models
    "Ticket",
    "KnowledgeBaseArticle",
    "AgentWorkflow", 
    "PerformanceMetrics",
    
    # Enums
    "TicketStatus",
    "Priority",
    "ResolutionType",
    
    # Operations
    "TicketOperations",
    "KnowledgeBaseOperations",
    "WorkflowOperations",
    "AnalyticsOperations"
]

# Version info
__version__ = "0.1.0"
__description__ = "PyTiDB AI-powered operations for TicketFlow AI"