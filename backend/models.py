"""
Data models for AI-Powered CRM MVP
Pydantic models for API request/response structures
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pydantic import BaseModel, Field

# Chat Models
class ChatMessage(BaseModel):
    """Chat message from owner or lead"""
    content: str = Field(..., description="Message content")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    files: Optional[List[Dict[str, str]]] = Field(None, description="Uploaded files info")
    timestamp: Optional[str] = Field(None, description="Message timestamp")

class ChatResponse(BaseModel):
    """Response from chat endpoints"""
    response: str = Field(..., description="Agent response")
    session_id: str = Field(..., description="Session ID")
    pipeline_complete: bool = Field(False, description="Whether pipeline is complete")
    pipeline_payload: Optional[Dict[str, Any]] = Field(None, description="Complete pipeline data")
    timestamp: str = Field(..., description="Response timestamp")

# Pipeline Models
class StageConfig(BaseModel):
    """Configuration for a single pipeline stage"""
    stage_name: str = Field(..., description="Name of the stage")
    stage_number: int = Field(..., description="Stage number (1-based)")
    entry_condition: str = Field(..., description="Condition to enter this stage")
    prompt: str = Field(..., description="AI prompt for this stage")
    brief_stage_goal: str = Field(..., description="Brief description of stage goal")
    fields: List[str] = Field(default_factory=list, description="Fields to collect in this stage")
    user_tags: List[str] = Field(default_factory=list, description="Tags for leads in this stage")

class PipelinePayload(BaseModel):
    """Complete pipeline configuration"""
    biz_name: str = Field(..., description="Business name")
    biz_info: str = Field(..., description="Business information")
    goal: str = Field(..., description="Business goal")
    business_id: str = Field(..., description="Unique business identifier")
    total_stages: int = Field(..., description="Total number of stages")
    stages: List[StageConfig] = Field(..., description="List of stage configurations")
    pipeline_completed: bool = Field(True, description="Pipeline completion status")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# Lead Models
class LeadData(BaseModel):
    """Lead information"""
    name: str = Field("", description="Lead name")
    type: str = Field("", description="Lead type/category")
    company: str = Field("", description="Company name")
    website: str = Field("", description="Website URL")
    phone: str = Field("", description="Phone number")
    email: str = Field("", description="Email address")
    address: str = Field("", description="Physical address")
    requirements: str = Field("", description="Lead requirements")
    notes: str = Field("", description="Additional notes")
    stage: int = Field(1, description="Current pipeline stage")
    user_tags: List[str] = Field(default_factory=list, description="Tags assigned to this lead")
    session_id: str = Field(..., description="Lead's session ID")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# Business Models
class BusinessData(BaseModel):
    """Business configuration data"""
    biz_name: str = Field("", description="Business name")
    biz_info: str = Field("", description="Business information")
    goal: str = Field("", description="Business goal")
    business_id: str = Field("", description="Unique business identifier")
    owner_session_id: Optional[str] = Field(None, description="Owner's session ID")
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# Kanban Models
class KanbanCard(BaseModel):
    """Kanban card representing a lead"""
    id: str = Field(..., description="Unique card ID")
    lead_name: str = Field(..., description="Lead name")
    lead_type: str = Field("", description="Lead type")
    user_tags: List[str] = Field(default_factory=list, description="Lead tags")
    stage: int = Field(..., description="Current stage")
    position: int = Field(0, description="Position within stage")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

class KanbanColumn(BaseModel):
    """Kanban column representing a pipeline stage"""
    stage_number: int = Field(..., description="Stage number")
    stage_name: str = Field(..., description="Stage name")
    brief_stage_goal: str = Field("", description="Stage goal description")
    cards: List[KanbanCard] = Field(default_factory=list, description="Cards in this column")

class KanbanBoard(BaseModel):
    """Complete Kanban board"""
    business_name: str = Field("", description="Business name")
    columns: List[KanbanColumn] = Field(default_factory=list, description="Board columns")
    total_leads: int = Field(0, description="Total number of leads")
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# WebSocket Models
class WebSocketMessage(BaseModel):
    """WebSocket message structure"""
    type: str = Field(..., description="Message type")
    data: Dict[str, Any] = Field(..., description="Message data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

# File Upload Models
class FileUpload(BaseModel):
    """File upload information"""
    filename: str = Field(..., description="Original filename")
    path: str = Field(..., description="Server file path")
    size: int = Field(..., description="File size in bytes")
    type: str = Field(..., description="File type/extension")
    uploaded_at: str = Field(default_factory=lambda: datetime.now().isoformat())

# State Models
class ApplicationState(BaseModel):
    """Complete application state for persistence"""
    business_data: BusinessData = Field(default_factory=BusinessData)
    pipeline_payload: Optional[PipelinePayload] = Field(None)
    leads: List[LeadData] = Field(default_factory=list)
    owner_conversations: List[Dict[str, str]] = Field(default_factory=list)
    lead_conversations: Dict[str, List[Dict[str, str]]] = Field(default_factory=dict)
    active_sessions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    kanban_board: KanbanBoard = Field(default_factory=KanbanBoard)
    session_state: Dict[str, Any] = Field(default_factory=dict, description="Complete session state for ready state preparation")
    last_updated: str = Field(default_factory=lambda: datetime.now().isoformat())

# API Response Models
class APIResponse(BaseModel):
    """Standard API response wrapper"""
    success: bool = Field(True, description="Operation success status")
    message: str = Field("", description="Response message")
    data: Optional[Any] = Field(None, description="Response data")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

class ErrorResponse(BaseModel):
    """Error response model"""
    success: bool = Field(False, description="Always false for errors")
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Additional error details")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat()) 