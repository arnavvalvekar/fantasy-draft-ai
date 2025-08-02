from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
import logging

from app.models.chat import ChatRequest, ChatResponse, ChatMessage
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get RAG service
def get_rag_service() -> RAGService:
    return RAGService()

@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Chat with the fantasy football draft assistant using RAG capabilities
    """
    try:
        logger.info(f"Chat request received: {request.message[:100]}...")
        
        # Get response from RAG service
        response = rag_service.chat(request)
        
        logger.info("Chat response generated successfully")
        return response
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

@router.post("/chat/session/{session_id}", response_model=ChatResponse)
async def chat_with_session(
    session_id: str,
    request: ChatRequest,
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Chat with session management for conversation history
    """
    try:
        logger.info(f"Chat session request: {session_id}")
        
        # In a real implementation, you would:
        # 1. Load session history from database
        # 2. Add current message to history
        # 3. Pass full history to RAG service
        # 4. Save updated history
        
        # For now, just use the basic chat functionality
        response = rag_service.chat(request)
        
        return response
        
    except Exception as e:
        logger.error(f"Error in chat session endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Chat session error: {str(e)}")

@router.get("/chat/sessions", response_model=List[Dict[str, Any]])
async def get_chat_sessions():
    """
    Get list of chat sessions (placeholder)
    """
    # In a real implementation, you would return actual session data
    return [
        {
            "session_id": "session_1",
            "created_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T01:00:00Z",
            "message_count": 5
        }
    ]

@router.delete("/chat/session/{session_id}")
async def delete_chat_session(session_id: str):
    """
    Delete a chat session
    """
    try:
        logger.info(f"Deleting chat session: {session_id}")
        
        # In a real implementation, you would delete from database
        # For now, just return success
        
        return {"message": f"Session {session_id} deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail=f"Delete session error: {str(e)}")

@router.post("/chat/clear")
async def clear_chat_cache(
    rag_service: RAGService = Depends(get_rag_service)
):
    """
    Clear the chat cache in the backend
    """
    try:
        logger.info("Clearing chat cache...")
        
        # Clear the chat cache in the RAG service
        rag_service.clear_chat_cache()
        
        logger.info("Chat cache cleared successfully")
        return {
            "message": "Chat cache cleared successfully",
            "cache_size": 0
        }
        
    except Exception as e:
        logger.error(f"Error clearing chat cache: {e}")
        raise HTTPException(status_code=500, detail=f"Clear cache error: {str(e)}")

@router.get("/chat/health")
async def chat_health():
    """
    Health check for chat service
    """
    return {
        "status": "healthy",
        "service": "chat",
        "rag_available": True
    } 