from typing import Dict, List, Optional, Any
import uuid
from datetime import datetime
from ticketflow.database.connection import db_manager
from ticketflow.database.models import ProcessingTask
from ticketflow.utils.helpers import get_isoformat
import logging

logger = logging.getLogger(__name__)

class ProcessingTaskOperations:
    """Operations for managing background processing tasks"""
    
    @staticmethod
    def create_task(
        task_type: str,
        source_name: str,
        user_metadata: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Create a new processing task"""
        try:
            task_id = str(uuid.uuid4())
            
            # Create ProcessingTask object
            task = ProcessingTask(
                task_type=task_type,
                task_id=task_id,
                source_name=source_name,
                status="pending",
                progress_percentage=0,
                result_data={},
                error_message="",
                created_at=get_isoformat(),
                user_metadata=user_metadata or {}
            )
            
            # Insert the task
            result = db_manager.processing_tasks.insert(task)
            # Handle case where insert returns a list
            created_task = result[0] if isinstance(result, list) else result
            logger.info(f"✅ Created processing task {task_id} for {source_name}")
            
            return {
                "task_id": task_id,
                "status": "pending",
                "created_at": created_task.created_at
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to create processing task: {e}")
            raise
    
    @staticmethod
    def update_task_status(
        task_id: str,
        status: str,
        progress_percentage: Optional[int] = None,
        result_data: Optional[Dict] = None,
        error_message: Optional[str] = None
    ) -> bool:
        """Update task status and progress"""
        try:
            updates = {"status": status}
            
            if progress_percentage is not None:
                updates["progress_percentage"] = progress_percentage
            
            if result_data is not None:
                updates["result_data"] = result_data
            
            if error_message is not None:
                updates["error_message"] = error_message
            
            if status == "processing" and not updates.get("started_at"):
                updates["started_at"] = get_isoformat()
            
            if status in ["completed", "failed"]:
                updates["completed_at"] = get_isoformat()
                if progress_percentage is None:
                    updates["progress_percentage"] = 100 if status == "completed" else 0
            
            db_manager.processing_tasks.update(
                filters={"task_id": task_id},
                values=updates
            )
            
            logger.info(f"✅ Updated task {task_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update task {task_id}: {e}")
            return False
    
    @staticmethod
    def get_task_status(task_id: str) -> Optional[Dict[str, Any]]:
        """Get current task status"""
        try:
            tasks = db_manager.processing_tasks.query(
                filters={"task_id": task_id},
                limit=1
            ).to_pydantic()
            
            if not tasks:
                return None
            
            task = tasks[0]
            return {
                "task_id": task.task_id,
                "task_type": task.task_type,
                "source_name": task.source_name,
                "status": task.status,
                "progress_percentage": task.progress_percentage,
                "result_data": task.result_data,
                "error_message": task.error_message,
                "created_at": task.created_at,
                "started_at": task.started_at,
                "completed_at": task.completed_at
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get task status {task_id}: {e}")
            return None
    
    @staticmethod
    def get_recent_tasks(limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent processing tasks"""
        try:
            tasks = db_manager.processing_tasks.query(
                order_by="created_at DESC",
                limit=limit
            ).to_pydantic()
            
            return [
                {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "source_name": task.source_name,
                    "status": task.status,
                    "progress_percentage": task.progress_percentage,
                    "created_at": task.created_at,
                    "completed_at": task.completed_at
                }
                for task in tasks
            ]
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent tasks: {e}")
            return []
    
    @staticmethod
    def cleanup_old_tasks(days_old: int = 7) -> int:
        """Clean up old completed/failed tasks"""
        try:
            # This would need a proper date comparison in a real implementation
            # For now, just return 0 as cleanup count
            logger.info(f"Task cleanup would remove tasks older than {days_old} days")
            return 0
            
        except Exception as e:
            logger.error(f"❌ Failed to cleanup old tasks: {e}")
            return 0

__all__ = ["ProcessingTaskOperations"]