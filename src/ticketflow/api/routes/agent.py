"""
Agent API routes
AI agent interaction, workflow management, and processing control
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from ...agent.core import TicketFlowAgent, AgentConfig
from ...database.operations import TicketOperations, WorkflowOperations
from ...database.schemas import AgentWorkflowResponse
from ..dependencies import get_db_session, get_current_user

router = APIRouter()


class ProcessTicketRequest(BaseModel):
    """Request schema for processing tickets"""
    ticket_id: int
    force_reprocess: bool = False
    priority_override: Optional[str] = None


class AgentConfigUpdate(BaseModel):
    """Request schema for updating agent configuration"""
    confidence_threshold: Optional[float] = None
    max_processing_time: Optional[int] = None
    enable_auto_resolution: Optional[bool] = None
    escalation_threshold: Optional[float] = None


@router.post("/process", response_model=AgentWorkflowResponse)
async def process_ticket(
    request: ProcessTicketRequest,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Process a ticket with the AI agent"""
    try:
        # Verify ticket exists
        ticket = TicketOperations.get_ticket_by_id(session, request.ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        # Check if already processing (unless force reprocess)
        if not request.force_reprocess:
            existing_workflows = WorkflowOperations.get_active_workflows_for_ticket(
                session, request.ticket_id
            )
            if existing_workflows:
                raise HTTPException(
                    status_code=409,
                    detail="Ticket is already being processed"
                )
        
        # Create workflow
        workflow = WorkflowOperations.create_workflow(session, request.ticket_id)
        
        # Start processing in background
        background_tasks.add_task(
            process_ticket_async,
            session,
            request.ticket_id,
            workflow.id,
            request.priority_override,
            current_user["id"]
        )
        
        return AgentWorkflowResponse.from_orm(workflow)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start ticket processing: {str(e)}"
        )


async def process_ticket_async(
    session: Session,
    ticket_id: int,
    workflow_id: int,
    priority_override: Optional[str],
    user_id: str
):
    """Background task for processing tickets"""
    try:
        # Initialize agent
        agent = TicketFlowAgent()
        
        # Get ticket
        ticket = TicketOperations.get_ticket_by_id(session, ticket_id)
        if not ticket:
            WorkflowOperations.mark_workflow_failed(
                session, workflow_id, "Ticket not found"
            )
            return
        
        # Process ticket
        result = await agent.process_ticket(ticket, session)
        
        # Update workflow with results
        WorkflowOperations.complete_workflow(session, workflow_id, result)
        
    except Exception as e:
        # Mark workflow as failed
        WorkflowOperations.mark_workflow_failed(
            session, workflow_id, str(e)
        )


@router.post("/process-batch")
async def process_ticket_batch(
    ticket_ids: List[int],
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Process multiple tickets in batch"""
    try:
        if len(ticket_ids) > 50:
            raise HTTPException(
                status_code=400,
                detail="Batch size cannot exceed 50 tickets"
            )
        
        workflows = []
        for ticket_id in ticket_ids:
            # Verify ticket exists
            ticket = TicketOperations.get_ticket_by_id(session, ticket_id)
            if not ticket:
                continue  # Skip non-existent tickets
            
            # Create workflow
            workflow = WorkflowOperations.create_workflow(session, ticket_id)
            workflows.append(workflow)
            
            # Start processing
            background_tasks.add_task(
                process_ticket_async,
                session,
                ticket_id,
                workflow.id,
                None,  # No priority override for batch
                current_user["id"]
            )
        
        return {
            "message": f"Started processing {len(workflows)} tickets",
            "workflows": [AgentWorkflowResponse.from_orm(w) for w in workflows]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start batch processing: {str(e)}"
        )


@router.get("/status")
async def get_agent_status(
    session: Session = Depends(get_db_session)
):
    """Get current agent status and queue information"""
    try:
        # Get active workflows
        active_workflows = WorkflowOperations.get_active_workflows(session)
        
        # Get queue stats
        queue_stats = {
            "processing": len(active_workflows),
            "pending": TicketOperations.get_pending_ticket_count(session),
            "completed_today": WorkflowOperations.get_completed_workflows_today(session)
        }
        
        return {
            "status": "active",
            "queue": queue_stats,
            "active_workflows": [
                {"id": w.id, "ticket_id": w.ticket_id, "started_at": w.started_at}
                for w in active_workflows
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent status: {str(e)}"
        )


@router.get("/config")
async def get_agent_config():
    """Get current agent configuration"""
    try:
        config = AgentConfig.get_current_config()
        return config.dict()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent config: {str(e)}"
        )


@router.put("/config")
async def update_agent_config(
    config_update: AgentConfigUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update agent configuration"""
    try:
        # Only allow admin users to update config
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="Admin privileges required"
            )
        
        # Get current config
        current_config = AgentConfig.get_current_config()
        
        # Update only provided fields
        update_data = config_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(current_config, field, value)
        
        # Save updated config
        AgentConfig.save_config(current_config)
        
        return {
            "message": "Agent configuration updated successfully",
            "config": current_config.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update agent config: {str(e)}"
        )


@router.post("/workflow/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: int,
    session: Session = Depends(get_db_session),
    current_user: dict = Depends(get_current_user)
):
    """Cancel an active workflow"""
    try:
        workflow = WorkflowOperations.get_workflow_by_id(session, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        if workflow.status != "running":
            raise HTTPException(
                status_code=400,
                detail="Workflow is not currently running"
            )
        
        # Cancel the workflow
        WorkflowOperations.cancel_workflow(session, workflow_id, current_user["id"])
        
        return {
            "message": "Workflow cancelled successfully",
            "workflow_id": workflow_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel workflow: {str(e)}"
        )


@router.get("/workflows/active", response_model=List[AgentWorkflowResponse])
async def get_active_workflows(
    limit: int = 50,
    session: Session = Depends(get_db_session)
):
    """Get currently active workflows"""
    try:
        workflows = WorkflowOperations.get_active_workflows(session, limit)
        return [AgentWorkflowResponse.from_orm(w) for w in workflows]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get active workflows: {str(e)}"
        )


@router.get("/performance")
async def get_agent_performance_summary(
    days: int = 7,
    session: Session = Depends(get_db_session)
):
    """Get agent performance summary"""
    try:
        performance = await WorkflowOperations.get_agent_performance_summary(
            session, days
        )
        
        return {
            "period_days": days,
            "performance": performance
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent performance: {str(e)}"
        )
