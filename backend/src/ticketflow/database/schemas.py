"""
Pydantic schemas for API request/response models
These define the structure of data going in and out of the API
Updated to match current PyTiDB models
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from .models import ResolutionType, Priority, TicketStatus
# Enums (matching database models)




# Request schemas (data coming into API)
class TicketCreateRequest(BaseModel):
    """Schema for creating a new ticket"""
    title: str = Field(..., min_length=1, max_length=500, description="Ticket title")
    description: str = Field(..., min_length=1, description="Detailed ticket description")
    category: str = Field(..., min_length=1, max_length=100, description="Ticket category")
    priority: Priority = Field(default=Priority.MEDIUM, description="Ticket priority level")
    user_id: Optional[str] = Field(None, max_length=100, description="User identifier")
    user_email: Optional[EmailStr] = Field(None, description="User email address")
    user_type: str = Field(default="customer", max_length=50, description="Type of user")
    ticket_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('description')
    def description_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Description cannot be empty')
        return v.strip()
    
    @validator('category')
    def category_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Category cannot be empty')
        return v.strip().lower()

class TicketUpdateRequest(BaseModel):
    """Schema for updating an existing ticket"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    priority: Optional[Priority] = None
    status: Optional[TicketStatus] = None
    resolution: Optional[str] = None
    ticket_metadata: Optional[Dict[str, Any]] = None

class KnowledgeBaseCreateRequest(BaseModel):
    """Schema for creating knowledge base articles"""
    title: str = Field(..., min_length=1, max_length=500, description="Article title")
    content: str = Field(..., min_length=1, description="Article content")
    summary: Optional[str] = Field(None, max_length=1000, description="Article summary")
    category: str = Field(..., min_length=1, max_length=100, description="Article category")
    tags: Optional[List[str]] = Field(default_factory=list, description="Article tags")
    source_url: Optional[str] = Field(None, max_length=1000, description="Source URL")
    source_type: str = Field(default="manual", max_length=50, description="Source type")
    author: Optional[str] = Field(None, max_length=255, description="Article author")
    
    @validator('title')
    def title_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()
    
    @validator('category')
    def category_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Category cannot be empty')
        return v.strip().lower()

class KnowledgeBaseUpdateRequest(BaseModel):
    """Schema for updating knowledge base articles"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    content: Optional[str] = Field(None, min_length=1)
    summary: Optional[str] = Field(None, max_length=1000)
    category: Optional[str] = Field(None, min_length=1, max_length=100)
    tags: Optional[List[str]] = None
    source_url: Optional[str] = Field(None, max_length=1000)
    author: Optional[str] = Field(None, max_length=255)

# Response schemas (data going out from API)
class TicketResponse(BaseModel):
    """Schema for ticket responses"""
    id: int
    title: str
    description: str
    category: str
    priority: str
    status: str
    user_id: str
    user_email: str
    user_type: str
    resolution: str
    resolved_by: str
    resolution_type: str
    agent_confidence: float
    processing_duration_ms: int
    similar_cases_found: int
    kb_articles_used: int
    workflow_steps: List[Dict[str, Any]]
    ticket_metadata: Dict[str, Any]
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]
    resolved_at: Optional[Union[str, datetime]]
    
    class Config:
        from_attributes = True  # Allows conversion from SQLAlchemy models
        
    @validator('created_at', 'updated_at', 'resolved_at', pre=True)
    def parse_datetime(cls, v):
        """Handle both string and datetime inputs"""
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return v

class AgentWorkflowResponse(BaseModel):
    """Schema for agent workflow responses"""
    id: int
    ticket_id: int
    status: str
    workflow_steps: List[Dict[str, Any]]
    total_duration_ms: int
    final_confidence: float
    similar_cases_found: List[Dict[str, Any]]
    kb_articles_used: List[Dict[str, Any]]
    actions_executed: List[Dict[str, Any]]
    llm_calls: List[Dict[str, Any]]
    embedding_time_ms: int
    search_time_ms: int
    llm_time_ms: int
    started_at: Union[str, datetime]
    completed_at: Optional[Union[str, datetime]]
    error_message: str
    
    class Config:
        from_attributes = True
        
    @validator('started_at', 'completed_at', pre=True)
    def parse_datetime(cls, v):
        """Handle both string and datetime inputs"""
        if v is None:
            return v
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return v

class KnowledgeBaseResponse(BaseModel):
    """Schema for knowledge base article responses"""
    id: int
    title: str
    content: str
    summary: str
    category: str
    tags: List[str]
    source_url: str
    source_type: str
    author: str
    view_count: int
    helpful_votes: int
    unhelpful_votes: int
    usage_in_resolutions: int
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]
    last_accessed: Optional[Union[str, datetime]]
    
    # Computed properties
    helpfulness_score: Optional[float] = Field(None, description="Calculated helpfulness percentage")
    
    class Config:
        from_attributes = True
        
    @validator('created_at', 'updated_at', 'last_accessed', pre=True)
    def parse_datetime(cls, v):
        """Handle both string and datetime inputs"""
        if v is None:
            return v
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return v

class DashboardMetricsResponse(BaseModel):
    """Schema for dashboard metrics"""
    tickets_today: int
    tickets_auto_resolved_today: int
    currently_processing: int
    pending_tickets: int
    avg_confidence: float
    avg_processing_time_ms: float
    avg_resolution_hours: float
    automation_rate: float
    resolution_rate: float
    customer_satisfaction_avg: float
    estimated_time_saved_hours: float
    estimated_cost_saved: float
    category_breakdown: Dict[str, int]
    priority_breakdown: Dict[str, int]

class PerformanceMetricsResponse(BaseModel):
    """Schema for performance metrics responses"""
    id: int
    metric_date: str
    metric_hour: Optional[int]
    tickets_processed: int
    tickets_auto_resolved: int
    tickets_escalated: int
    avg_confidence_score: float
    avg_processing_time_ms: int
    avg_resolution_time_hours: float
    customer_satisfaction_avg: float
    resolution_accuracy_rate: float
    category_breakdown: Dict[str, Any]
    priority_breakdown: Dict[str, Any]
    estimated_time_saved_hours: float
    estimated_cost_saved: float
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]
    
    class Config:
        from_attributes = True
        
    @validator('created_at', 'updated_at', pre=True)
    def parse_datetime(cls, v):
        """Handle both string and datetime inputs"""
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return v
    
class SearchResultResponse(BaseModel):
    """Schema for search results"""
    ticket_id: int
    title: str
    description: str
    resolution: str
    similarity_score: float
    category: str
    priority: str
    status: str
    resolved_at: Optional[Union[str, datetime]]
    
    @validator('resolved_at', pre=True)
    def parse_datetime(cls, v):
        """Handle both string and datetime inputs"""
        if v is None:
            return v
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return v

class KnowledgeBaseSearchResult(BaseModel):
    """Schema for KB search results"""
    id: int
    title: str
    content: str
    summary: str
    category: str
    similarity_score: float
    helpfulness_score: float
    usage_count: int

class AgentConfigResponse(BaseModel):
    """Schema for agent configuration"""
    confidence_threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    max_processing_time: int = Field(default=300000, ge=1000)  # milliseconds
    enable_auto_resolution: bool = Field(default=True)
    escalation_threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    max_similar_tickets: int = Field(default=10, ge=1, le=50)
    max_kb_articles: int = Field(default=5, ge=1, le=20)
    llm_temperature: float = Field(default=0.3, ge=0.0, le=1.0)
    
class WorkflowStepResponse(BaseModel):
    """Schema for individual workflow steps"""
    step_name: str
    step_type: str
    started_at: Union[str, datetime]
    completed_at: Optional[Union[str, datetime]]
    duration_ms: int
    status: str
    input_data: Dict[str, Any]
    output_data: Dict[str, Any]
    error_message: str
    
    @validator('started_at', 'completed_at', pre=True)
    def parse_datetime(cls, v):
        """Handle both string and datetime inputs"""
        if v is None:
            return v
        if isinstance(v, str):
            return v
        elif isinstance(v, datetime):
            return v.isoformat()
        return v

class WebhookTicketRequest(BaseModel):
    """Schema for webhook ticket creation from external platforms"""
    # Flexible field mapping for different external platforms
    subject: Optional[str] = Field(None, description="Ticket subject (alternative to title)")
    title: Optional[str] = Field(None, description="Ticket title")
    description: Optional[str] = Field(None, description="Ticket description")
    body: Optional[str] = Field(None, description="Ticket body (alternative to description)")
    category: Optional[str] = Field(default="general", description="Ticket category")
    priority: Optional[str] = Field(default="medium", description="Ticket priority")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email address")
    user_email: Optional[EmailStr] = Field(None, description="User email address")
    user_id: Optional[str] = Field(None, description="User identifier")
    id: Optional[str] = Field(None, description="External ticket ID")
    platform: Optional[str] = Field(default="external", description="Source platform")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    
    @validator('priority')
    def validate_priority(cls, v):
        """Validate priority value"""
        if v and v.lower() not in ['low', 'medium', 'high', 'urgent']:
            return 'medium'
        return v.lower() if v else 'medium'
    
    @validator('category')
    def validate_category(cls, v):
        """Validate and normalize category"""
        if not v or not v.strip():
            return 'general'
        return v.strip().lower()
    
    def normalize_to_ticket_data(self) -> Dict[str, Any]:
        """Convert webhook data to internal ticket format"""
        return {
            "title": self.title or self.subject or "No title provided",
            "description": self.description or self.body or "No description provided",
            "category": self.category,
            "priority": self.priority,
            "user_email": str(self.customer_email or self.user_email or ""),
            "user_id": self.user_id or "",
            "user_type": "customer",
            "ticket_metadata": {
                **self.metadata,
                "external_id": self.id,
                "platform": self.platform,
                "source": "webhook"
            }
        }

# Pydantic models for API requests/responses
class SettingResponse(BaseModel):
    """Response model for a single setting"""
    id: int
    key: str
    category: str
    name: str
    description: str
    setting_type: str
    value: Any  # Will be converted based on setting_type
    default_value: Any
    is_enabled: bool
    is_required: bool
    is_sensitive: bool
    validation_rules: Dict[str, Any]
    allowed_values: List[str]
    created_at: str
    updated_at: str
    updated_by: str

class SettingCreateRequest(BaseModel):
    """Request model for creating a new setting"""
    key: str = Field(..., min_length=1, max_length=100, description="Unique setting key")
    category: str = Field(..., min_length=1, max_length=50, description="Setting category")
    name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    setting_type: str = Field(..., description="Data type")
    value: str = Field(default="", description="Setting value")
    default_value: str = Field(default="", description="Default value")
    description: str = Field(default="", description="Setting description")
    is_enabled: bool = Field(default=True, description="Whether setting is enabled")
    is_required: bool = Field(default=False, description="Whether setting is required")
    is_sensitive: bool = Field(default=False, description="Whether setting contains sensitive data")
    validation_rules: Optional[Dict[str, Any]] = Field(default=None, description="Validation rules")
    allowed_values: Optional[List[str]] = Field(default=None, description="Allowed values")
    
    @validator('setting_type')
    def validate_setting_type(cls, v):
        valid_types = [t.value for t in SettingType]
        if v not in valid_types:
            raise ValueError(f"Invalid setting_type. Must be one of: {valid_types}")
        return v
    
    @validator('category')
    def validate_category(cls, v):
        valid_categories = [c.value for c in SettingCategory]
        if v not in valid_categories:
            raise ValueError(f"Invalid category. Must be one of: {valid_categories}")
        return v

class SettingUpdateRequest(BaseModel):
    """Request model for updating a setting"""
    value: Optional[str] = Field(None, description="New setting value")
    is_enabled: Optional[bool] = Field(None, description="Whether setting is enabled")

class SettingsListResponse(BaseModel):
    """Response model for settings list"""
    settings: List[SettingResponse]
    total: int
    category: Optional[str] = None


# Export all schemas for easy imports
__all__ = [
    # Enums
    "TicketStatusEnum",
    "PriorityEnum", 
    "ResolutionTypeEnum",
    "WorkflowStatusEnum",
    
    # Request schemas
    "TicketCreateRequest",
    "TicketUpdateRequest",
    "KnowledgeBaseCreateRequest",
    "KnowledgeBaseUpdateRequest",
    "WebhookTicketRequest",
    "SettingCreateRequest",
    "SettingUpdateRequest",

    
    # Response schemas
    "SettingsListResponse",
    "SettingResponse",
    "TicketResponse",
    "AgentWorkflowResponse",
    "KnowledgeBaseResponse",
    "DashboardMetricsResponse",
    "PerformanceMetricsResponse",
    "SearchResultResponse",
    "KnowledgeBaseSearchResult",
    "AgentConfigResponse",
    "WorkflowStepResponse"

]