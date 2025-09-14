"""
TicketFlow AI API Server
Run this script to start the FastAPI development server
"""

import uvicorn
import sys
import os

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

if __name__ == "__main__":
    print("Starting TicketFlow AI API Server...")
    print("API will be available at: http://localhost:8000")
    print("Interactive API docs at: http://localhost:8000/docs")
    print("Alternative docs at: http://localhost:8000/redoc")
    
    uvicorn.run(
        "ticketflow.api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
