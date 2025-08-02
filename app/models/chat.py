from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatMessage(BaseModel):
    """Individual chat message"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class ChatRequest(BaseModel):
    """Request for chat interaction"""
    message: str
    draft_context: Optional[Dict[str, Any]] = None
    user_team: Optional[Dict[str, Any]] = None
    conversation_history: Optional[List[ChatMessage]] = []
    league_settings: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    """Response from chat system"""
    response: str
    sources: Optional[List[str]] = []
    confidence: float = 0.0
    suggested_actions: Optional[List[str]] = []
    follow_up_questions: Optional[List[str]] = []

class ChatSession(BaseModel):
    """Chat session management"""
    session_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.now)
    last_activity: datetime = Field(default_factory=datetime.now) 