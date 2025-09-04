"""
Ticket API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database.operations import TicketOperations
from ...database.schemas import TicketCreateRequest, TicketResponse
from ..dependencies import get_db_session

router = APIRouter()

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket_data: TicketCreateRequest,
    session: Session = Depends(get_db_session)
):
    """Create a new ticket"""
    try:
        ticket = await TicketOperations.create_ticket(session, ticket_data)
        return TicketResponse.from_orm(ticket)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create ticket: {str(e)}")

@router.get("/", response_model=List[TicketResponse])
def get_tickets(
    status: Optional[str] = Query(None, description="Filter tickets by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of tickets to return"),
    session: Session = Depends(get_db_session)
):
    """Get tickets, optionally filtered by status"""
    try:
        if status:
            tickets = TicketOperations.get_tickets_by_status(session, status, limit)
        else:
            tickets = TicketOperations.get_recent_tickets(session, limit=limit)
        
        return [TicketResponse.from_orm(ticket) for ticket in tickets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tickets: {str(e)}")

@router.get("/recent", response_model=List[TicketResponse])
def get_recent_tickets(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=100, description="Number of tickets to return"),
    session: Session = Depends(get_db_session)
):
    """Get recent tickets"""
    try:
        tickets = TicketOperations.get_recent_tickets(session, days, limit)
        return [TicketResponse.from_orm(ticket) for ticket in tickets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recent tickets: {str(e)}")

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(
    ticket_id: int,
    session: Session = Depends(get_db_session)
):
    """Get a specific ticket by ID"""
    try:
        from ...database.models import Ticket
        ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return TicketResponse.from_orm(ticket)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ticket: {str(e)}")

@router.get("/{ticket_id}/similar", response_model=List[dict])
async def get_similar_tickets(
    ticket_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of similar tickets to return"),
    min_similarity: float = Query(0.75, ge=0.0, le=1.0, description="Minimum similarity score"),
    session: Session = Depends(get_db_session)
):
    """Get similar tickets using vector search"""
    try:
        from ...database.models import Ticket
        ticket = session.query(Ticket).filter(Ticket.id == ticket_id).first()
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        similar_tickets = await TicketOperations.find_similar_tickets(
            session, ticket, limit, min_similarity
        )
        
        return similar_tickets
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to find similar tickets: {str(e)}")
