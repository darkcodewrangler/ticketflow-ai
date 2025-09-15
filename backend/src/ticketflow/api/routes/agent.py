"""
Agent API routes - Simplified version
AI agent workflow management for ticket processing
"""


from ticketflow.database.models import TicketStatus, WorkflowStatus
from ticketflow.database.connection import db_manager
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from datetime import datetime
from ticketflow.utils.helpers import get_isoformat, get_value
from ticketflow.database.operations import WorkflowOperations, TicketOperations
from ticketflow.database.schemas import AgentWorkflowResponse, TicketResponse
from ticketflow.api.dependencies import verify_db_connection, get_current_user, require_permissions
from ticketflow.agent.core import TicketFlowAgent
from ticketflow.api.websocket_manager import websocket_manager
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessTicketRequest(BaseModel):
    """Request schema for processing tickets"""
    ticket_id: int
    force_reprocess: bool = False


class FeedbackRequest(BaseModel):
    """Request schema for collecting feedback on agent performance"""
    workflow_id: int
    resolution_effective: bool
    resolution_rating: int  # 1-5 scale
    feedback_text: str = ""
    user_id: str = ""


@router.post("/process")
async def process_ticket(
    request: ProcessTicketRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["process_tickets"]))
):
    """Start processing a ticket with the AI agent"""
    try:
        # Verify ticket exists
        tickets = db_manager.tickets.query(filters={"id": int(request.ticket_id)}, limit=1).to_list()
        if not tickets:
            return error_response(
                message="Ticket not found",
                error="Ticket with the specified ID does not exist",
                error_code=ErrorCodes.TICKET_NOT_FOUND
            )
        
        ticket = TicketResponse.model_validate(tickets[0]).model_dump()
    
        # # Create workflow
        workflow = WorkflowOperations.create_workflow(int(request.ticket_id))
        
        # Convert ticket to a minimal dict for processing
        ticket_dict = {
            "id": get_value(ticket, "id"),
            "title": get_value(ticket, "title"),
            "description": get_value(ticket, "description"),
            "category": get_value(ticket, "category"),    
            "priority": get_value(ticket, "priority"),
            "user_email": get_value(ticket, "user_email"),
            "user_type": get_value(ticket, "user_type"),
            "status": get_value(ticket, "status")
        }
        # Trigger AI processing in background
        background_tasks.add_task(
            _trigger_agent_processing,
            get_value(ticket_dict, "id"),
            ticket_dict,
            workflow.id
        )
        try:
            await websocket_manager.send_agent_update(
                get_value(ticket_dict, "id"), "queued", "Queued for processing", {"workflow_id": workflow.id}
            )
        except Exception:
            pass
        
        processing_data = {
            "ticket_id": request.ticket_id,
            "workflow_id": workflow.id,
            "status": TicketStatus.PROCESSING.value
        }
        
        return success_response(
            data=processing_data,
            message=f"Started processing ticket {request.ticket_id}",
            metadata={"workflow_id": workflow.id}
        )
        
    except Exception as e:
        # Check if it's already an error response
        if hasattr(e, 'get') and e.get('success') is False:
            return e
        return error_response(
            message="Failed to start ticket processing",
            error=str(e),
            error_code=ErrorCodes.AGENT_PROCESSING_FAILED
        )


@router.get("/status")
async def get_agent_status(
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get current agent status and queue information"""
    try:
   
        # Get active workflows
        active_workflows = db_manager.agent_workflows.query(
            filters={"status": WorkflowStatus.RUNNING.value},
            limit=int(100)
        ).to_list()
        
        # Get pending tickets
        pending_tickets = db_manager.tickets.query(
            filters={"status": TicketStatus.NEW.value},
            limit=int(100)
        ).to_list()
        
        status_data = {
            "status": "active",
            "queue": {
                "processing": len(active_workflows),
                "pending": len(pending_tickets)
            },
            "active_workflows": [
                {"id": getattr(w, 'id', w.get('id', 0)), "ticket_id": getattr(w, 'ticket_id', w.get('ticket_id', 0))}
                for w in active_workflows[:10]  # Limit to first 10
            ]
        }
        
        return success_response(
            data=status_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"type": "agent_status"}
        )
        
    except Exception as e:
        return error_response(
            message="Failed to retrieve agent status",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/workflows")
async def get_workflows(
    limit: int = 50,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get recent workflows"""
    try:
     
        workflows = db_manager.agent_workflows.query(
            limit=int(limit),
            order_by={"started_at": "desc"}
        ).to_list()
        
        workflow_list = [AgentWorkflowResponse.model_validate(w).model_dump() for w in workflows]
        return success_response(
            data=workflow_list,
            message=ResponseMessages.RETRIEVED,
            count=len(workflow_list),
            metadata={"limit": limit}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve workflows",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/workflows/{workflow_id}")
async def get_workflow(
    workflow_id: int,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_tickets"]))
):
    """Get a specific workflow"""
    try:

        workflows = db_manager.agent_workflows.query(
            filters={"id": int(workflow_id)},
            limit=1
        ).to_list()
        
        if not workflows:
            return error_response(
                message="Workflow not found",
                error="Workflow with the specified ID does not exist",
                error_code=ErrorCodes.WORKFLOW_NOT_FOUND
            )
        
        workflow_data = AgentWorkflowResponse.model_validate(workflows[0]).model_dump()
        return success_response(
            data=workflow_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"workflow_id": workflow_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve workflow",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.put("/workflows/{workflow_id}/complete")
async def complete_workflow(
    workflow_id: int,
    confidence: float = 0.8,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["process_tickets"]))
):
    """Mark a workflow as completed"""
    try:
        success = WorkflowOperations.complete_workflow(int(workflow_id), float(confidence))
        
        if not success:
            return error_response(
                message="Workflow not found",
                error="Cannot complete non-existent workflow",
                error_code=ErrorCodes.WORKFLOW_NOT_FOUND
            )
        
        completion_data = {
            "workflow_id": workflow_id,
            "confidence": confidence,
            "completed": True
        }
        
        return success_response(
            data=completion_data,
            message="Workflow completed successfully",
            metadata={"workflow_id": workflow_id, "confidence": confidence}
        )
        
    except Exception as e:
        return error_response(
            message="Failed to complete workflow",
            error=str(e),
            error_code=ErrorCodes.WORKFLOW_EXECUTION_FAILED
        )


@router.post("/feedback")
async def collect_feedback(
    request: FeedbackRequest,
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["process_tickets"]))
):
    """Collect feedback on agent performance for learning and improvement"""
    try:
        # Verify workflow exists
        workflow = WorkflowOperations.get_workflow(request.workflow_id)
        if not workflow:
            return error_response(
                message="Workflow not found",
                error="Workflow with the specified ID does not exist",
                error_code=ErrorCodes.RESOURCE_NOT_FOUND
            )
        
        # Initialize agent to process feedback
        agent = TicketFlowAgent()
        
        # Process the feedback
        feedback_result = agent.process_feedback({
            "workflow_id": request.workflow_id,
            "resolution_effective": request.resolution_effective,
            "resolution_rating": request.resolution_rating,
            "feedback_text": request.feedback_text,
            "user_id": request.user_id,
            "timestamp": get_isoformat()
        })
        
        if feedback_result.get("success"):
            return success_response(
                data={"feedback_processed": True, "learning_updated": feedback_result.get("learning_updated", False)},
                message="Feedback collected successfully",
                metadata={"workflow_id": request.workflow_id}
            )
        else:
            return error_response(
                message="Failed to process feedback",
                error=feedback_result.get("error", "Unknown error"),
                error_code=ErrorCodes.PROCESSING_FAILED
            )
            
    except Exception as e:
        logger.error(f"Error collecting feedback: {e}")
        return error_response(
            message="Failed to collect feedback",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_SERVER_ERROR
        )


def _trigger_agent_processing(ticket_id: int, ticket_data: Dict[str, Any], workflow_id: int):
    """Background task to trigger agent processing for a ticket"""
    try:
        
        
        logger.info(f"🤖 Starting AI processing for ticket {ticket_id} (workflow {workflow_id})")
        try:
            asyncio.run(websocket_manager.send_agent_update(ticket_id, "start", "Processing started", {"workflow_id": workflow_id}))
        except Exception:
            pass
        
        # Initialize agent
        agent = TicketFlowAgent()
        
        # Process the existing ticket (don't create a new one)
        result = agent.process_existing_ticket(ticket_id, workflow_id)

        print(f"""result from _trigger_agent_processing: {result}""")
        if result.get("success"):
            logger.info(f"✅ AI processing completed for ticket {ticket_id}")
            try:
                asyncio.run(websocket_manager.send_agent_update(ticket_id, "completed", "Processing completed", {
                    "workflow_id": result.get("workflow_id"),
                    "status": result.get("final_status"),
                    "confidence": result.get("confidence")
                }))
            except Exception:
                pass
        else:
            logger.warning(f"⚠️ Agent processing failed for ticket {ticket_id}: {result.get('error')}")
            try:
                asyncio.run(websocket_manager.send_agent_update(ticket_id, "error", "Processing failed", {"error": result.get('error')}))
            except Exception:
                pass
            
    except Exception as e:
        logger.error(f"❌ AI processing error for ticket {ticket_id}: {e}")
        # Update workflow with error
        try:
           WorkflowOperations.update_workflow_step(workflow_id, {
                "step": "error",
                "status": "failed",
                "message": f"AI processing failed: {str(e)}",
                "error": str(e)
            })
           try:
               asyncio.run(websocket_manager.send_agent_update(ticket_id, "error", "Processing error", {"error": str(e)}))
           except Exception:
               pass

        except Exception as update_error:
            logger.error(f"Failed to update workflow with error: {update_error}")