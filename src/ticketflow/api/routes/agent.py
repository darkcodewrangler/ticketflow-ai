"""
Agent API routes - Simplified version
AI agent workflow management for ticket processing
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from pydantic import BaseModel

from ...database.operations import WorkflowOperations, TicketOperations
from ...database.schemas import AgentWorkflowResponse
from ..dependencies import verify_db_connection, get_current_user

router = APIRouter()


class ProcessTicketRequest(BaseModel):
    """Request schema for processing tickets"""
    ticket_id: int
    force_reprocess: bool = False


@router.post("/process")
async def process_ticket(
    request: ProcessTicketRequest,
    _: bool = Depends(verify_db_connection),
    current_user: dict = Depends(get_current_user)
):
    """Start processing a ticket with the AI agent"""
    try:
        # Verify ticket exists
        from ...database.connection import db_manager
        tickets = db_manager.tickets.query(filters={"id": int(request.ticket_id)}, limit=1).to_list()
        
        if not tickets:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Create workflow
        workflow = WorkflowOperations.create_workflow(int(request.ticket_id))
        
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
        from ...database.connection import db_manager
        
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
        from ...database.connection import db_manager
        
        workflows = db_manager.agent_workflows.query(
            limit=int(limit),
            order_by=[("started_at", "desc")]
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
        from ...database.connection import db_manager
        
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
        success = WorkflowOperations.complete_workflow(int(workflow_id), float(confidence))
        
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