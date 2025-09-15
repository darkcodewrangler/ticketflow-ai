"""
Ticket API routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
import logging

from ticketflow.database.operations import TicketOperations
from ticketflow.database.schemas import TicketCreateRequest, TicketResponse
from ticketflow.api.dependencies import verify_db_connection, get_current_api_key, require_permissions
from ticketflow.config import config
from ticketflow.api.websocket_manager import websocket_manager
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)
from ticketflow.database.connection import db_manager
from ticketflow.agent.core import TicketFlowAgent
        
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
       
        logger.info(f"🤖 Starting auto-processing for ticket {ticket_id}")
        try:
            await websocket_manager.send_agent_update(ticket_id, "start", "Started auto-processing")
        except Exception:
            pass
        
        # Initialize agent
        agent = TicketFlowAgent()
        
        # Process the ticket
        result = agent.process_ticket(ticket_data)
        
        if result.get("success"):
            logger.info(f"Auto-processing completed for ticket {ticket_id}")
            try:
                await websocket_manager.send_agent_update(ticket_id, "completed", "Auto-processing completed", {
                    "workflow_id": result.get("workflow_id"),
                    "status": result.get("final_status"),
                    "confidence": result.get("confidence")
                })
            except Exception:
                pass
        else:
            logger.warning(f"Auto-processing failed for ticket {ticket_id}: {result.get('error')}")
            try:
                await websocket_manager.send_agent_update(ticket_id, "error", "Auto-processing failed", {"error": result.get('error')})
            except Exception:
                pass
            
    except Exception as e:
        logger.error(f"Auto-processing error for ticket {ticket_id}: {e}")
        try:
            await websocket_manager.send_agent_update(ticket_id, "error", "Auto-processing error", {"error": str(e)})
        except Exception:
            pass

@router.post("/")
async def create_ticket(
    ticket_data: TicketCreateRequest,
    background_tasks: BackgroundTasks,
    auto_process: str = Query("true", description="Whether to automatically process the ticket with AI agent (true/false)"),
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["create_tickets"]))
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
        ticket_data = TicketResponse.model_validate(ticket).model_dump()
        try:
            await websocket_manager.send_ticket_created(ticket_data)
        except Exception:
            pass
        
        # Trigger agent processing if enabled
        if should_process:
            background_tasks.add_task(
                trigger_agent_processing, 
                ticket.id, 
                ticket_dict
            )
            logger.info(f"Auto-processing enabled for ticket {ticket.id}")
        
        # Return standardized response with processing info
        ticket_data["auto_processing"] = should_process
        
        return success_response(
            data=ticket_data,
            message=ResponseMessages.TICKET_CREATED,
            metadata={"auto_processing_enabled": should_process}
        )
        
    except Exception as e:
        logger.error(f"Failed to create ticket: {e}")
        return error_response(
            message="Failed to create ticket",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/")
async def get_tickets(
    status: Optional[str] = Query(None, description="Filter tickets by status"),
    limit: int = Query(50, ge=1, le=100, description="Number of tickets to return"),
    days: int = Query(None, ge=1, le=60, description="Days old tickets to return"),
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get tickets, optionally filtered by status"""
    try:
        if status:
            tickets = TicketOperations.get_tickets_by_status(status, int(limit))
        else:
            tickets = TicketOperations.get_recent_tickets(limit=int(limit),days= int(days) if days else None)
        
        ticket_list = [TicketResponse.model_validate(ticket).model_dump() for ticket in tickets]
        return success_response(
            data=ticket_list,
            message=ResponseMessages.RETRIEVED,
            count=len(ticket_list),
            metadata={"filtered_by_status": status is not None, "status_filter": status,
            "filtered_by_days": days is not None, "days_filter": days}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve tickets",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/recent")
async def get_recent_tickets(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    limit: int = Query(100, ge=1, le=100, description="Number of tickets to return"),
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get recent tickets"""
    try:
        tickets = TicketOperations.get_recent_tickets(int(days), int(limit))

        ticket_list = [TicketResponse.model_validate(ticket).model_dump() for ticket in tickets]
        return success_response(
            data=ticket_list,
            message=ResponseMessages.RETRIEVED,
            count=len(ticket_list),
            metadata={"days_back": days, "limit": limit}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve recent tickets",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get a specific ticket by ID"""
    try:
        # PyTiDB query for specific ticket
      
        tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_pydantic()
        
        if not tickets:
            return error_response(
                message=ResponseMessages.TICKET_NOT_FOUND,
                error="Ticket not found",
                error_code=ErrorCodes.TICKET_NOT_FOUND
            )
        
        ticket_data = TicketResponse.model_dump(tickets[0])
        return success_response(
            data=ticket_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"ticket_id": ticket_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve ticket",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

@router.get("/{ticket_id}/similar")
async def get_similar_tickets(
    ticket_id: int,
    limit: int = Query(10, ge=1, le=50, description="Number of similar tickets to return"),
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get similar tickets using vector search"""
    try:
        # Get the source ticket
        
        tickets = db_manager.tickets.query(filters={"id": ticket_id}, limit=1).to_pydantic()
        
        if not tickets:
            return error_response(
                message=ResponseMessages.TICKET_NOT_FOUND,
                error="Ticket not found",
                error_code=ErrorCodes.TICKET_NOT_FOUND
            )
        
        ticket = TicketResponse.model_dump(tickets[0])
      
        similar_tickets = TicketOperations.find_similar_to_ticket(ticket, int(limit))
        
        return success_response(
            data=similar_tickets,
            message="Similar tickets retrieved successfully",
            count=len(similar_tickets),
            metadata={"source_ticket_id": ticket_id, "similarity_limit": limit}
        )
    except Exception as e:
        return error_response(
            message="Failed to find similar tickets",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )
