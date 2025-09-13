"""
PyTiDB package for TicketFlow AI
AI-powered database operations with automatic embeddings and intelligent search
"""

from ticketflow.database.connection import db_manager, PyTiDBManager
from ticketflow.database.models import (
    Ticket, 
    KnowledgeBaseArticle, 
    AgentWorkflow, 
    PerformanceMetrics,
    TicketStatus,
    Priority,
    ResolutionType,WorkflowStatus
)
from ticketflow.database.operations import (
    TicketOperations,
    KnowledgeBaseOperations,
    WorkflowOperations,
    AnalyticsOperations
)
from ticketflow.database.settings_manager import SettingsManager

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
    "WorkflowStatus",

    
    # Operations
    "TicketOperations",
    "KnowledgeBaseOperations",
    "WorkflowOperations",
    "AnalyticsOperations",
    
    # Settings
    "SettingsManager"
]

# Version info
__version__ = "0.1.0"
__description__ = "PyTiDB AI-powered operations for TicketFlow AI"