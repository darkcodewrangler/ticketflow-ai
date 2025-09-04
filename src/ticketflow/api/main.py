"""
FastAPI application main module
"""

from ..config import config
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
from typing import List, Optional

from ..database import db_manager
from ..database.operations import TicketOperations, KnowledgeBaseOperations, WorkflowOperations
from .routes import tickets, knowledge_base, workflows, search
from .dependencies import get_db_session

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager"""
    # Startup
    get_db_session()
    yield
    # Shutdown - cleanup if needed
  
app = FastAPI(
    title="TicketFlow AI",
    description="AI-powered ticketing system with vector search capabilities",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(knowledge_base.router, prefix="/api/v1/knowledge", tags=["knowledge"])
app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["workflows"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "TicketFlow AI API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "ticketflow-ai"}

if __name__ == "__main__":
    uvicorn.run("ticketflow.api.main:app", host="0.0.0.0", port=8000, reload=True)
