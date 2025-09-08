"""
Ticket API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional

from ...database.operations import TicketOperations
from ...database.schemas import TicketCreateRequest, TicketResponse
from ..dependencies import verify_db_connection

router = APIRouter()

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    _: bool = Depends(verify_db_connection)
):
    """Create a new ticket"""
    try:
        ticket = TicketOperations.create_ticket(ticket_data.dict())
        return TicketResponse.model_validate(ticket)
    except Exception as e:
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
        tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_list()
        
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponse.from_attributes(tickets[0])
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
        tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_list()
        
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = tickets[0]
        similar_tickets = TicketOperations.find_similar_to_ticket(ticket, int(limit))
        
        return similar_tickets
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar tickets: {str(e)}")
