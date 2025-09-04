"""
TicketFlow AI Database Package
"""

from .connection import db_manager, get_db, Base
from .models import Ticket, KnowledgeBaseArticle, AgentWorkflow, PerformanceMetrics
from .schemas import (
    TicketCreateRequest, 
    TicketResponse, 
    KnowledgeBaseCreateRequest,
    KnowledgeBaseResponse,
    AgentWorkflowResponse,
    DashboardMetricsResponse
)

__all__ = [
    "db_manager",
    "get_db", 
    "Base",
    "Ticket",
    "KnowledgeBaseArticle", 
    "AgentWorkflow",
    "PerformanceMetrics",
    "TicketCreateRequest",
    "TicketResponse",
    "KnowledgeBaseCreateRequest",
    "KnowledgeBaseResponse",
    "AgentWorkflowResponse",
    "DashboardMetricsResponse"
]