"""
PyTiDB package for TicketFlow AI
AI-powered database operations with automatic embeddings
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

__all__ = [
    "db_manager",
    "PyTiDBManager", 
    "Ticket",
    "KnowledgeBaseArticle",
    "AgentWorkflow", 
    "PerformanceMetrics",
    "TicketStatus",
    "Priority",
    "ResolutionType"
]