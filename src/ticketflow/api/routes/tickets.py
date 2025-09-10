"""
Ticket API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging

from ...database.operations import TicketOperations
from ...database.schemas import TicketCreateRequest, TicketResponse
from ..dependencies import verify_db_connection
from ...config import config

logger = logging.getLogger(__name__)

router = APIRouter()

def parse_auto_process_param(auto_process_str: str) -> bool:
    """Parse auto_process query parameter string to boolean"""
    if not auto_process_str:
        return True  # Default to true if not provided
    
    # Normalize the string
    normalized = auto_process_str.lower().strip()
    
    # Parse various true/false representations
    if normalized in ["true", "1", "yes", "on", "enabled", "auto"]:
        return True
    elif normalized in ["false", "0", "no", "off", "disabled", "manual"]:
        return False
    else:
        # If unclear, default to true for better UX
        logger.warning(f"Unknown auto_process value '{auto_process_str}', defaulting to true")
        return True

def should_auto_process(ticket_data: Dict[str, Any]) -> bool:
    """Determine if ticket should be auto-processed based on business rules"""
    
    # Always auto-process for demo
    if config.DEMO_MODE:
        return True
    
    # Production rules
    priority = ticket_data.get("priority", "medium")
    category = ticket_data.get("category", "general")
    
    # Auto-process urgent tickets
    if priority == "urgent":
        return True
    
    # Auto-process common categories with good KB coverage
    if category in ["account", "billing", "password"]:
        return True
    
    # Don't auto-process complex technical issues
    if category == "technical" and priority == "low":
        return False
    
    return True  # Default to auto-processing

async def trigger_agent_processing(ticket_id: int, ticket_data: Dict[str, Any]):
    """Background task to trigger agent processing for a ticket"""
    try:
        from ...agent.core import TicketFlowAgent
        
        logger.info(f"🤖 Starting auto-processing for ticket {ticket_id}")
        
        # Initialize agent
        agent = TicketFlowAgent()
        
        # Process the ticket
        result = await agent.process_ticket(ticket_data)
        
        if result.get("success"):
            logger.info(f"✅ Auto-processing completed for ticket {ticket_id}")
        else:
            logger.warning(f"⚠️ Auto-processing failed for ticket {ticket_id}: {result.get('error')}")
            
    except Exception as e:
        logger.error(f"❌ Auto-processing error for ticket {ticket_id}: {e}")

@router.post("/")
async def create_ticket(
    ticket_data: TicketCreateRequest,
    background_tasks: BackgroundTasks,
    auto_process: str = Query("true", description="Whether to automatically process the ticket with AI agent (true/false)"),
    _: bool = Depends(verify_db_connection)
):
    """Create a new ticket with optional auto-processing"""
    try:
        # Convert to dict for processing
        ticket_dict = ticket_data.model_dump()
        
        # Parse auto_process parameter
        auto_process_bool = parse_auto_process_param(auto_process)
        
        # Determine if we should auto-process
        should_process = auto_process_bool and should_auto_process(ticket_dict)
        
        # Create the ticket
        ticket = TicketOperations.create_ticket(ticket_dict)
        
        # Trigger agent processing if enabled
        if should_process:
            background_tasks.add_task(
                trigger_agent_processing, 
                ticket.id, 
                ticket_dict
            )
            logger.info(f"🎯 Auto-processing enabled for ticket {ticket.id}")
        
        # Return response with processing info
        response_data = TicketResponse.model_validate(ticket).dict()
        response_data["auto_processing"] = should_process
        
        return response_data
        
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    status: Optional[str] = Query(None, description="Filter tickets by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of tickets to return"),
    _: bool = Depends(verify_db_connection)
):
    """Get tickets, optionally filtered by status"""
    try:
        if status:
            tickets = TicketOperations.get_tickets_by_status(status, int(limit))
        else:
            tickets = TicketOperations.get_recent_tickets(limit=int(limit))
        
        return [TicketResponse.model_validate(ticket) for ticket in tickets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tickets: {str(e)}")

@router.get("/recent", response_model=List[TicketResponse])
def get_recent_tickets(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=100, description="Number of tickets to return"),
    _: bool = Depends(verify_db_connection)
):
    """Get recent tickets"""
    try:
        tickets = TicketOperations.get_recent_tickets(int(days), int(limit))
        return [TicketResponse.model_validate(ticket) for ticket in tickets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent tickets: {str(e)}")

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get a specific ticket by ID"""
    try:
        # PyTiDB query for specific ticket
        from ...database.connection import db_manager
        tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_pydantic()
        
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponse.model_dump(tickets[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ticket: {str(e)}")

@router.get("/{ticket_id}/similar", response_model=List[dict])
async def get_similar_tickets(
    ticket_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of similar tickets to return"),
    _: bool = Depends(verify_db_connection)
):
    """Get similar tickets using vector search"""
    try:
        # Get the source ticket
        from ...database.connection import db_manager
        tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_pydantic()
        
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = TicketResponse.model_dump(tickets[0])
      
        similar_tickets = TicketOperations.find_similar_to_ticket(ticket, int(limit))
        
        return similar_tickets
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar tickets: {str(e)}")
