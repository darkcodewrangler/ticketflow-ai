"""
Pydantic schemas for API request/response models
These define the structure of data going in and out of your API
"""

from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# Enums (matching database models)
class TicketStatusEnum(str, Enum):
    NEW = "new"
    PROCESSING = "processing" 
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"

class PriorityEnum(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

# Request schemas (data coming into API)
class TicketCreateRequest(BaseModel):
    """Schema for creating a new ticket"""
    title: str
    description: str
    category: str
    priority: PriorityEnum = PriorityEnum.MEDIUM
    user_id: Optional[str] = None
    user_email: Optional[EmailStr] = None
    user_type: str = "customer"
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v

class KnowledgeBaseCreateRequest(BaseModel):
    """Schema for creating knowledge base articles"""
    title: str
    content: str
    summary: Optional[str] = None
    category: str
    tags: Optional[List[str]] = []
    source_url: Optional[str] = None
    source_type: str = "manual"
    author: Optional[str] = None

# Response schemas (data going out from API)
class TicketResponse(BaseModel):
    """Schema for ticket responses"""
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    user_id: Optional[str]
    user_email: Optional[str]
    resolution: Optional[str]
    resolved_by: Optional[str]
    agent_confidence: Optional[float]
    processing_duration_ms: Optional[int]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models

class AgentWorkflowResponse(BaseModel):
    """Schema for agent workflow responses"""
    id: int
    ticket_id: int
    status: str
    workflow_steps: List[Dict[str, Any]]
    total_duration_ms: int
    final_confidence: Optional[float]
    similar_cases_found: Optional[List[Dict[str, Any]]]
    kb_articles_used: Optional[List[Dict[str, Any]]]
    actions_executed: Optional[List[Dict[str, Any]]]
    started_at: datetime
    completed_at: Optional[datetime]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True

class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base article responses"""
    id: int
    title: str
    content: str
    summary: Optional[str]
    category: str
    tags: Optional[List[str]]
    source_url: Optional[str]
    source_type: str
    author: Optional[str]
    view_count: int
    helpful_votes: int
    unhelpful_votes: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class DashboardMetricsResponse(BaseModel):
    """Schema for dashboard metrics"""
    tickets_today: int
    tickets_auto_resolved_today: int
    currently_processing: int
    avg_confidence: Optional[float]
    avg_processing_time_ms: Optional[float]
    avg_resolution_hours: Optional[float]
    automation_rate: float
    resolution_rate: float
    
class SearchResultResponse(BaseModel):
    """Schema for search results"""
    ticket_id: int
    title: str
    description: str
    resolution: Optional[str]
    similarity_score: float
    category: str
    priority: str
    resolved_at: Optional[datetime]