"""
Workflow API routes
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ...database.operations import WorkflowOperations
from ...database.schemas import AgentWorkflowResponse
from ..dependencies import get_db_session

router = APIRouter()

@router.post("/", response_model=AgentWorkflowResponse)
def create_workflow(
    ticket_id: int,
    session: Session = Depends(get_db_session)
):
    """Create a new agent workflow for a ticket"""
    try:
        workflow = WorkflowOperations.create_workflow(session, ticket_id)
        return AgentWorkflowResponse.from_orm(workflow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@router.get("/{workflow_id}", response_model=AgentWorkflowResponse)
def get_workflow(
    workflow_id: int,
    session: Session = Depends(get_db_session)
):
    """Get a specific workflow"""
    try:
        from ...database.models import AgentWorkflow
        
        workflow = session.query(AgentWorkflow).filter(
            AgentWorkflow.id == workflow_id
        ).first()
        
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")
        
        return AgentWorkflowResponse.from_orm(workflow)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")

@router.get("/ticket/{ticket_id}", response_model=List[AgentWorkflowResponse])
def get_workflows_for_ticket(
    ticket_id: int,
    session: Session = Depends(get_db_session)
):
    """Get all workflows for a specific ticket"""
    try:
        from ...database.models import AgentWorkflow
        
        workflows = session.query(AgentWorkflow).filter(
            AgentWorkflow.ticket_id == ticket_id
        ).order_by(AgentWorkflow.started_at.desc()).all()
        
        return [AgentWorkflowResponse.from_orm(workflow) for workflow in workflows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")

@router.put("/{workflow_id}/step")
def update_workflow_step(
    workflow_id: int,
    step_data: Dict[str, Any],
    session: Session = Depends(get_db_session)
):
    """Add a step to a workflow"""
    try:
        WorkflowOperations.update_workflow_step(session, workflow_id, step_data)
        return {"message": "Step added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow step: {str(e)}")
