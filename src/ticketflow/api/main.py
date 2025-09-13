"""
FastAPI main application for TicketFlow AI
Provides REST API and WebSocket support for real-time demos
"""

import uvicorn
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, List, Any

from ticketflow.database import (
    db_manager, 
    TicketOperations, 
    KnowledgeBaseOperations,
    AnalyticsOperations
)
from ticketflow.agent.core import TicketFlowAgent, AgentConfig
from .websocket_manager import websocket_manager
from .routes import (
    tickets, 
    knowledge_base, 
    workflows, 
    search, 
    analytics, 
    agent, 
    integrations, 
    settings
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    # Startup
    logger.info("Starting TicketFlow AI API...")
    
    # Initialize database connection
    if not db_manager.connect():
        logger.error("Database connection failed!")
        raise Exception("Database connection failed")
    
    # # Initialize tables
    # if not db_manager.initialize_tables(drop_existing=False):
    #     logger.warning("Table initialization had issues")
    
    logger.info("TicketFlow AI API started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down TicketFlow AI API...")
    db_manager.close()

# Create FastAPI application
app = FastAPI(
    title="TicketFlow AI",
    description="AI-Powered Support Ticket Automation System",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(tickets.router, prefix="/api/tickets", tags=["tickets"])
app.include_router(knowledge_base.router, prefix="/api/kb", tags=["knowledge-base"])
app.include_router(workflows.router, prefix="/api/workflows", tags=["workflows"])
app.include_router(search.router, prefix="/api/search", tags=["search"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(agent.router, prefix="/api/agent", tags=["agent"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["integrations"])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])

# WebSocket endpoint for real-time updates
app.include_router(websocket_manager.router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db_manager._connected else "disconnected",
        "version": "1.0.0"
    }

# Root endpoint with basic info
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "TicketFlow AI",
        "description": "AI-Powered Support Ticket Automation",
        "version": "1.0.0",
        "endpoints": {
            "tickets": "/api/tickets",
            "knowledge_base": "/api/kb",
            "workflows": "/api/workflows", 
            "search": "/api/search",
            "analytics": "/api/analytics",
            "agent": "/api/agent",
            "integrations": "/api/integrations",
            "settings": "/api/settings",
            "websocket": "/ws",
            "docs": "/docs"
        }
    }

# Demo data endpoint for quick setup
@app.post("/api/demo/setup")
async def setup_demo_data(background_tasks: BackgroundTasks):
    """Set up demo data for presentations"""
    background_tasks.add_task(create_demo_data)
    return {"message": "Demo data creation started", "status": "processing"}

async def create_demo_data():
    """Create comprehensive demo data"""
    try:
        # Demo tickets
        demo_tickets = [
            {
                "title": "Password reset email not received",
                "description": "Clicked forgot password multiple times but no email arrives. Checked spam folder thoroughly. Need access urgently for client presentation.",
                "category": "account",
                "priority": "high",
                "user_email": "john.manager@company.com"
            },
            {
                "title": "Payment declined despite sufficient funds",
                "description": "My company credit card is being declined during checkout. Card works elsewhere and has sufficient credit limit. Blocking our service upgrade.",
                "category": "billing",
                "priority": "medium", 
                "user_email": "finance@business.com"
            },
            {
                "title": "API returning 503 service unavailable",
                "description": "Our production integration started receiving 503 errors this morning. Affecting customer-facing features. No changes made on our end.",
                "category": "technical",
                "priority": "urgent",
                "user_email": "devops@saas.com"
            }
        ]
        
        # Create tickets
        for ticket_data in demo_tickets:
            TicketOperations.create_ticket(ticket_data)
        
        # Demo KB articles
        demo_articles = [
            {
                "title": "Password Reset Troubleshooting",
                "content": "Complete guide for password reset issues: 1) Check spam/junk folders, 2) Verify email address spelling, 3) Whitelist sender domain, 4) Clear browser cache, 5) Try different browser, 6) Contact admin for manual reset if urgent.",
                "category": "account",
                "tags": ["password", "reset", "email"],
                "author": "Support Team"
            },
            {
                "title": "Payment Processing Issues",
                "content": "Common payment problems and solutions: Card validation, bank holds, international restrictions, billing address mismatches, and system gateway issues. Includes escalation procedures.",
                "category": "billing",
                "tags": ["payment", "billing", "card"],
                "author": "Billing Team"
            }
        ]
        
        # Create KB articles
        for article_data in demo_articles:
            KnowledgeBaseOperations.create_article(article_data)
        
        logger.info("Demo data created successfully")
        
    except Exception as e:
        logger.error(f"Demo data creation failed: {e}")
if __name__ == "__main__":
    uvicorn.run("ticketflow.api.main:app", host="0.0.0.0", port=8000, reload=True)
