"""
Workflow API routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from ...database.operations import WorkflowOperations
from ...database.schemas import AgentWorkflowResponse
from ..dependencies import verify_db_connection

router = APIRouter()

@router.post("/", response_model=AgentWorkflowResponse)
async def create_workflow(
    ticket_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Create a new agent workflow for a ticket"""
    try:
        workflow = await WorkflowOperations.create_workflow(int(ticket_id))
        return AgentWorkflowResponse.model_validate(workflow)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")

@router.get("/{workflow_id}", response_model=AgentWorkflowResponse)
def get_workflow(
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
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")

@router.get("/ticket/{ticket_id}", response_model=List[AgentWorkflowResponse])
def get_workflows_for_ticket(
    ticket_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get all workflows for a specific ticket"""
    try:
        from ...database.connection import db_manager
        
        workflows = db_manager.agent_workflows.query(
            filters={"ticket_id": int(ticket_id)},
            order_by={"started_at": "desc"}
        ).to_list()
        
        return [AgentWorkflowResponse.model_validate(workflow) for workflow in workflows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflows: {str(e)}")

@router.put("/{workflow_id}/step")
async def update_workflow_step(
    workflow_id: int,
    step_data: Dict[str, Any],
    _: bool = Depends(verify_db_connection)
):
    """Add a step to a workflow"""
    try:
        success = await WorkflowOperations.update_workflow_step(int(workflow_id), step_data)
        if success:
            return {"message": "Step added successfully"}
        else:
            raise HTTPException(status_code=404, detail="Workflow not found")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update workflow step: {str(e)}")
