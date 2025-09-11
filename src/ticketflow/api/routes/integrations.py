"""
Integration API routes for external platform webhooks
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from typing import Dict, Any
import logging

from ...database.operations import TicketOperations
from ...database.schemas import WebhookTicketRequest, TicketResponse
from ..dependencies import verify_db_connection
from ..routes.tickets import should_auto_process, trigger_agent_processing, parse_auto_process_param

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/webhook")
async def receive_external_ticket(
    ticket_data: WebhookTicketRequest,
    background_tasks: BackgroundTasks,
    auto_process: str = Query("true", description="Whether to automatically process the ticket with AI agent (true/false)"),
    _: bool = Depends(verify_db_connection)
):
    """
    Webhook endpoint for external platform integrations
    
    Accepts tickets from various external platforms and normalizes them
    to the internal TicketFlow format. Supports flexible field mapping
    for different platforms (Zendesk, Freshdesk, Jira, etc.).
    
    Example payloads:
    - Zendesk: `{"subject": "...", "description": "...", "priority": "high"}`
    - Freshdesk: `{"title": "...", "body": "...", "customer_email": "..."}`
    - Jira: `{"title": "...", "description": "...", "platform": "jira"}`
    """
    try:
        # Normalize external data to internal format
        normalized_data = ticket_data.normalize_to_ticket_data()
        
        # Validate required fields
        if not normalized_data.get("title") or normalized_data["title"] == "No title provided":
            raise HTTPException(
                status_code=400, 
                detail="Title or subject is required"
            )
        
        if not normalized_data.get("description") or normalized_data["description"] == "No description provided":
            raise HTTPException(
                status_code=400, 
                detail="Description or body is required"
            )
        
        # Parse auto_process parameter
        auto_process_bool = parse_auto_process_param(auto_process)
        
        # Determine if we should auto-process
        should_process = auto_process_bool and should_auto_process(normalized_data)
        
        # Create ticket using existing operations
        ticket =await TicketOperations.create_ticket(normalized_data)
        
        # Trigger agent processing if enabled
        if should_process:
            background_tasks.add_task(
                trigger_agent_processing, 
                ticket.id, 
                normalized_data
            )
            logger.info(f"🎯 Auto-processing enabled for webhook ticket {ticket.id}")
        
        # Log webhook receipt
        logger.info(
            f"✅ Webhook ticket created: {ticket.id} from {normalized_data['ticket_metadata'].get('platform', 'unknown')} platform"
        )
        
        # Return created ticket with processing info
        response_data = TicketResponse.model_validate(ticket).model_dump()
        response_data["auto_processing"] = should_process
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Webhook ticket creation failed: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to process webhook ticket: {str(e)}"
        )

@router.post("/webhook/batch", response_model=Dict[str, Any])
async def receive_external_tickets_batch(
    tickets_data: list[WebhookTicketRequest],
    background_tasks: BackgroundTasks,
    auto_process: str = Query("true", description="Whether to automatically process the tickets with AI agent (true/false)"),
    _: bool = Depends(verify_db_connection)
):
    """
    Batch webhook endpoint for processing multiple tickets at once
    
    Useful for bulk imports or platforms that send multiple tickets
    in a single webhook call.
    """
    try:
        created_tickets = []
        failed_tickets = []
        
        for i, ticket_data in enumerate(tickets_data):
            try:
                # Normalize external data to internal format
                normalized_data = ticket_data.normalize_to_ticket_data()
                
                # Validate required fields
                if not normalized_data.get("title") or normalized_data["title"] == "No title provided":
                    failed_tickets.append({
                        "index": i,
                        "error": "Title or subject is required",
                        "data": ticket_data.model_dump()
                    })
                    continue
                
                if not normalized_data.get("description") or normalized_data["description"] == "No description provided":
                    failed_tickets.append({
                        "index": i,
                        "error": "Description or body is required", 
                        "data": ticket_data.model_dump()
                    })
                    continue
                
                # Parse auto_process parameter
                auto_process_bool = parse_auto_process_param(auto_process)
                
                # Determine if we should auto-process this ticket
                should_process = auto_process_bool and should_auto_process(normalized_data)
                
                # Create ticket
                ticket = await TicketOperations.create_ticket(normalized_data)
                
                # Trigger agent processing if enabled
                if should_process:
                    background_tasks.add_task(
                        trigger_agent_processing, 
                        ticket.id, 
                        normalized_data
                    )
                
                created_tickets.append({
                    "index": i,
                    "ticket_id": ticket.id,
                    "title": ticket.title,
                    "auto_processing": should_process
                })
                
            except Exception as e:
                failed_tickets.append({
                    "index": i,
                    "error": str(e),
                    "data": ticket_data.dict()
                })
        
        logger.info(
            f"✅ Batch webhook processed: {len(created_tickets)} created, {len(failed_tickets)} failed"
        )
        
        return {
            "status": "completed",
            "created_count": len(created_tickets),
            "failed_count": len(failed_tickets),
            "created_tickets": created_tickets,
            "failed_tickets": failed_tickets
        }
        
    except Exception as e:
        logger.error(f"❌ Batch webhook processing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process batch webhook: {str(e)}"
        )

@router.get("/webhook/health")
async def webhook_health_check():
    """
    Health check endpoint for webhook integrations
    
    External platforms can use this to verify the webhook endpoint
    is available and responsive.
    """
    return {
        "status": "healthy",
        "endpoint": "webhook",
        "supported_platforms": ["zendesk", "freshdesk", "jira", "servicenow", "custom"],
        "features": [
            "flexible_field_mapping",
            "automatic_validation", 
            "batch_processing",
            "metadata_preservation"
        ]
    }
