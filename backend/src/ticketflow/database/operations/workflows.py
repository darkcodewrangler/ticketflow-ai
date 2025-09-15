
import datetime
from typing import Any, Dict, List
from ticketflow.database.connection import db_manager
from ticketflow.database.models import AgentWorkflow, WorkflowStatus
from ticketflow.utils.helpers import get_isoformat, get_value
import logging
logger = logging.getLogger(__name__)

class WorkflowOperations:
    """
    Agent workflow operations
    """

    @staticmethod
    def create_workflow(ticket_id: int, initial_steps: List[Dict] = None) -> AgentWorkflow:

        """Create new agent workflow"""
        try:
            workflow = AgentWorkflow(
                ticket_id=ticket_id,
                workflow_steps=initial_steps or [],
                total_duration_ms=0,
                status=WorkflowStatus.RUNNING.value
            )
            
            result = db_manager.agent_workflows.insert(workflow)
            # Handle case where insert returns a list
            created_workflow = result[0] if isinstance(result, list) else result
            logger.info(f"Created workflow {created_workflow.id} for ticket {ticket_id}")
            return created_workflow
            
        except Exception as e:
            logger.error(f"Failed to create workflow: {e}")
            raise

    @staticmethod
    def update_workflow_step(workflow_id: int, step_data: Dict[str, Any]) -> bool:

        """Add step to workflow"""
        try:
            # Get current workflow
            workflows = db_manager.agent_workflows.query(filters={"id": workflow_id}, limit=1).to_list()
            if not workflows:
                logger.warning(f"Workflow {workflow_id} not found")
                return False
            
            workflow = workflows[0]
            
            # Add timestamp to step
            step_data["timestamp"] = get_isoformat()

            
            # Update workflow steps - handle both objects and dicts
            current_steps = get_value(workflow, 'workflow_steps', [])
            
            current_steps.append(step_data)
            
            db_manager.agent_workflows.update(
                filters={"id": workflow_id},
                values={"workflow_steps": current_steps}
            )
            
            logger.info(f"Added step to workflow {workflow_id}: {step_data.get('step', 'unknown')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update workflow step: {e}")

            return False

    @staticmethod
    def complete_workflow(workflow_id: int, final_confidence: float = 0.0, total_duration_ms: int = 0) -> bool:
        """Mark workflow as completed"""
        try:
            updates = {
                "status":WorkflowStatus.COMPLETED.value,
                "completed_at": get_isoformat(),
                "final_confidence": final_confidence,
                "total_duration_ms": total_duration_ms
            }
            
            db_manager.agent_workflows.update(
                filters={"id": workflow_id},
                values=updates
            )
            
            logger.info(f"Completed workflow {workflow_id} with confidence {final_confidence} and duration {total_duration_ms}ms")

            return True
            
        except Exception as e:
            logger.error(f"Failed to complete workflow: {e}")
            
            return False


__all__ = [
    "WorkflowOperations"
]
