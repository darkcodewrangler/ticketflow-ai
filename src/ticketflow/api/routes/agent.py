"""
Agent API routes - Simplified version
AI agent workflow management for ticket processing
"""


from ticketflow.database.connection import db_manager
import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel
import logging
from ticketflow.utils.helpers import get_value
from ticketflow.database.operations import WorkflowOperations, TicketOperations
from ticketflow.database.schemas import AgentWorkflowResponse, TicketResponse
from ticketflow.api.dependencies import verify_db_connection, get_current_user
from ticketflow.agent.core import TicketFlowAgent
from ..websocket_manager import websocket_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class ProcessTicketRequest(BaseModel):
    """Request schema for processing tickets"""
    ticket_id: int
    force_reprocess: bool = False


@router.post("/process")
async def process_ticket(
    request: ProcessTicketRequest,
    background_tasks: BackgroundTasks,
    _: bool = Depends(verify_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Start processing a ticket with the AI agent"""
    try:
        # Verify ticket exists

        tickets = await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: db_manager.tickets.query(filters={"id": int(request.ticket_id)}, limit=1).to_pydantic()
        )
        # tickets = db_manager.tickets.query(filters={"id": int(request.ticket_id)}, limit=1).to_pydantic()
        
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = TicketResponse.model_dump(tickets[0])
    
        # Create workflow
        workflow = await WorkflowOperations.create_workflow(int(request.ticket_id))
        
        # Convert ticket to dict for processing
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
            get_value(ticket, "id"),
            ticket_dict,
            workflow.id
        )
        try:
            await websocket_manager.send_agent_update(
                get_value(ticket, "id"), "queued", "Queued for processing", {"workflow_id": workflow.id}
            )
        except Exception:
            pass
        
        return {
            "message": f"Started processing ticket {request.ticket_id}",
            "workflow_id": workflow.id,
            "status": "processing" 
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ticket processing: {str(e)}"
        )


@router.get("/status")
async def get_agent_status(
    _: bool = Depends(verify_db_connection)
):
    """Get current agent status and queue information"""
    try:
   
        # Get active workflows
        active_workflows = db_manager.agent_workflows.query(
            filters={"status": "running"},
            limit=int(100)
        ).to_list()
        
        # Get pending tickets
        pending_tickets = db_manager.tickets.query(
            filters={"status": "new"},
            limit=int(100)
        ).to_list()
        
        return {
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
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/workflows", response_model=List[AgentWorkflowResponse])
async def get_workflows(
    limit: int = 50,
    _: bool = Depends(verify_db_connection)
):
    """Get recent workflows"""
    try:
     
        workflows = db_manager.agent_workflows.query(
            limit=int(limit),
            order_by={"started_at": "desc"}
        ).to_list()
        
        return [AgentWorkflowResponse.model_validate(w) for w in workflows]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflows: {str(e)}"
        )


@router.get("/workflows/{workflow_id}", response_model=AgentWorkflowResponse)
async def get_workflow(
    workflow_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get a specific workflow"""
    try:

        workflows = db_manager.agent_workflows.query(
            filters={"id": int(workflow_id)},
            limit=1
        ).to_list()
        
        if not workflows:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return AgentWorkflowResponse.model_validate(workflows[0])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get workflow: {str(e)}"
        )


@router.put("/workflows/{workflow_id}/complete")
async def complete_workflow(
    workflow_id: int,
    confidence: float = 0.8,
    _: bool = Depends(verify_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Mark a workflow as completed"""
    try:
        success = await WorkflowOperations.complete_workflow(int(workflow_id), float(confidence))
        
        if not success:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return {
            "message": "Workflow completed successfully",
            "workflow_id": workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to complete workflow: {str(e)}"
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
        result = asyncio.run(agent.process_existing_ticket(ticket_id, workflow_id))

        
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
            logger.warning(f"⚠️ AI processing failed for ticket {ticket_id}: {result.get('error')}")
            try:
                asyncio.run(websocket_manager.send_agent_update(ticket_id, "error", "Processing failed", {"error": result.get('error')}))
            except Exception:
                pass
            
    except Exception as e:
        logger.error(f"❌ AI processing error for ticket {ticket_id}: {e}")
        # Update workflow with error
        try:
           asyncio.run(WorkflowOperations.update_workflow_step(workflow_id, {
                "step": "error",
                "status": "failed",
                "message": f"AI processing failed: {str(e)}",
                "error": str(e)
            }))
           try:
               asyncio.run(websocket_manager.send_agent_update(ticket_id, "error", "Processing error", {"error": str(e)}))
           except Exception:
               pass

        except Exception as update_error:
            logger.error(f"Failed to update workflow with error: {update_error}")