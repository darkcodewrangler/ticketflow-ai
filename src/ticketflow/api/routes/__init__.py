"""
API routes package
Exports all route modules for the TicketFlow AI API
"""

# Import all route modules for easy access
from . import tickets
from . import knowledge_base
from . import workflows
from . import search
from . import analytics
from . import agent

# Export all route modules
__all__ = [
    "tickets",
    "knowledge_base", 
    "workflows",
    "search",
    "analytics",
    "agent"
]
