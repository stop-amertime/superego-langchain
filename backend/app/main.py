from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import logging
import uuid
from typing import Dict, List
from dotenv import load_dotenv

from .models import Message, WebSocketMessageType, MessageRole, init_models
from .conversation_manager import get_all_conversations
from .agents import get_default_constitution
from .websocket_endpoints import handle_websocket_connection
from .api.router import api_router

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Check for API key
if not os.getenv("OPENROUTER_API_KEY"):
    logger.warning("OPENROUTER_API_KEY not set in environment variables. API calls will fail.")

# Create FastAPI app
app = FastAPI(
    title="Superego LangGraph API",
    description="API for the Superego LangGraph application",
    version="0.1.0"
)

# Configure CORS
frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the API router
app.include_router(api_router)

# Get conversations from persistent storage
conversations = get_all_conversations()

# Initialize models on startup
@app.on_event("startup")
async def startup_event():
    """Initialize models and resources on startup"""
    init_models()
    logger.info("Models and resources initialized")

# Root endpoint for health check
@app.get("/")
async def root():
    """Basic API endpoint to check if the server is running"""
    return {"status": "ok", "message": "Superego LangGraph API is running"}

# API status endpoint
@app.get("/api")
async def api_status():
    """Check API status and configuration"""
    # Check for OpenRouter API key to determine if API is usable
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    api_ready = len(api_key) > 0
    
    return {
        "status": "ok",
        "api_ready": api_ready,
        "config": {
            "has_api_key": api_ready
        }
    }

# WebSocket endpoint
@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for client connections"""
    try:
        await handle_websocket_connection(websocket, client_id, conversations)
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error handling websocket connection: {e}")
