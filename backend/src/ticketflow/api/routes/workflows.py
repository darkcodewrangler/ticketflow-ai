"""
Workflow API routes
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any

from ticketflow.database.operations import WorkflowOperations
from ticketflow.database.schemas import AgentWorkflowResponse
from ticketflow.api.dependencies import verify_db_connection
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)
from ticketflow.database.connection import db_manager

router = APIRouter()

@router.post("/")
async def create_workflow(
    ticket_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Create a new agent workflow for a ticket"""
    try:
        workflow = await WorkflowOperations.create_workflow(int(ticket_id))
        workflow_data = AgentWorkflowResponse.model_validate(workflow).model_dump()
        
        return success_response(
            data=workflow_data,
            message=ResponseMessages.WORKFLOW_STARTED,
            metadata={"ticket_id": ticket_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to create workflow",
            error=str(e),
            error_code=ErrorCodes.WORKFLOW_EXECUTION_FAILED
        )

@router.get("/{workflow_id}")
def get_workflow(
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

@router.get("/ticket/{ticket_id}")
def get_workflows_for_ticket(
    ticket_id: int,
    _: bool = Depends(verify_db_connection)
):
    """Get all workflows for a specific ticket"""
    try:
     
        workflows = db_manager.agent_workflows.query(
            filters={"ticket_id": int(ticket_id)},
            order_by={"started_at": "desc"}
        ).to_list()
        
        workflow_list = [AgentWorkflowResponse.model_validate(workflow).model_dump() for workflow in workflows]
        return success_response(
            data=workflow_list,
            message=ResponseMessages.RETRIEVED,
            count=len(workflow_list),
            metadata={"ticket_id": ticket_id}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve workflows for ticket",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )

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
            return success_response(
                data={"workflow_id": workflow_id, "step_added": True},
                message="Workflow step added successfully",
                metadata={"step_data": step_data}
            )
        else:
            return error_response(
                message="Workflow not found",
                error="Cannot add step to non-existent workflow",
                error_code=ErrorCodes.WORKFLOW_NOT_FOUND
            )
    except Exception as e:
        return error_response(
            message="Failed to update workflow step",
            error=str(e),
            error_code=ErrorCodes.WORKFLOW_EXECUTION_FAILED
        )
