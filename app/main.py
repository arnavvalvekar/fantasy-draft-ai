from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

from app.api import chat, recommendations, players
from app.services.rag_service import RAGService
from app.services.player_service import PlayerService

# Load environment variables
load_dotenv()

# Create FastAPI app
app = FastAPI(
    title="Fantasy Football Draft Assistant API",
    description="AI-powered fantasy football draft assistant with RAG capabilities",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
rag_service = RAGService()
player_service = PlayerService()

# Include API routes
app.include_router(chat.router, prefix="/api", tags=["chat"])
app.include_router(recommendations.router, prefix="/api", tags=["recommendations"])
app.include_router(players.router, prefix="/api", tags=["players"])

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Fantasy Football Draft Assistant API",
        "version": "1.0.0",
        "status": "healthy"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "services": {
            "rag_service": "initialized",
            "player_service": "initialized"
        }
    }

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "False").lower() == "true"
    ) 