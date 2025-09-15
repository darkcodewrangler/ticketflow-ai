"""
Learning Metrics Operations

Handles operations for agent learning metrics using PyTiDB pattern

"""

from typing import Dict, Optional
import logging

from ticketflow.database.models import LearningMetrics
from ticketflow.database.connection import db_manager
from ticketflow.utils.helpers import utcnow

logger = logging.getLogger(__name__)


class LearningMetricsManager:
    """Manages learning metrics in the database using PyTiDB"""
    
    @staticmethod
    def get_current_metrics() -> Optional[LearningMetrics]:
        """Get the current active learning metrics"""
        try:
            # Query for active metrics, ordered by updated_at descending
            results = db_manager.learning_metrics.query(
                filters={"is_active": True},
                order_by={"updated_at": "desc"},
                limit=1
            ).to_list()
            
            if results:
                # Convert dict result to LearningMetrics object
                data = results[0]
                return LearningMetrics(**data)
            return None
        except Exception as e:
            logger.error(f"Failed to get current metrics: {e}")
            return None
    
    @staticmethod
    def create_or_update_metrics(
        total_tickets_processed: int = 0,
        successful_resolutions: int = 0,
        escalations: int = 0,
        verification_failures: int = 0,
        average_confidence: float = 0.0,
        feedback_count: int = 0,
        positive_feedback: int = 0,
        resolution_patterns: Optional[Dict] = None,
        common_failures: Optional[Dict] = None,
        agent_version: str = "1.0"
    ) -> LearningMetrics:
        """Create new or update existing learning metrics"""
        try:
            # Get current metrics or create new
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Update existing metrics
                updated_data = {
                    "total_tickets_processed": total_tickets_processed,
                    "successful_resolutions": successful_resolutions,
                    "escalations": escalations,
                    "verification_failures": verification_failures,
                    "average_confidence": average_confidence,
                    "feedback_count": feedback_count,
                    "positive_feedback": positive_feedback,
                    "resolution_patterns": resolution_patterns or {},
                    "common_failures": common_failures or {},
                    "agent_version": agent_version,
                    "updated_at": utcnow().isoformat()
                }
                
                # Update the record
                updated_count = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                
                if updated_count and updated_count > 0:
                    # Return the updated record
                    updated_metrics = LearningMetricsManager.get_current_metrics()
                    logger.info(f"Updated learning metrics record {current.id}")
                    return updated_metrics
                else:
                    logger.error("Failed to update learning metrics - no rows affected")
                    return current
            else:
                # Create new metrics
                new_metrics = LearningMetrics(
                    total_tickets_processed=total_tickets_processed,
                    successful_resolutions=successful_resolutions,
                    escalations=escalations,
                    verification_failures=verification_failures,
                    average_confidence=average_confidence,
                    feedback_count=feedback_count,
                    positive_feedback=positive_feedback,
                    resolution_patterns=resolution_patterns or {},
                    common_failures=common_failures or {},
                    agent_version=agent_version,
                    is_active=True
                )
                
                result = db_manager.learning_metrics.insert(new_metrics)
                created_metrics = result[0] if isinstance(result, list) else result
                logger.info(f"Created new learning metrics record {created_metrics.id}")
                return created_metrics
                
        except Exception as e:
            logger.error(f"Failed to create/update learning metrics: {e}")
            raise
    
    @staticmethod
    def increment_ticket_processed() -> LearningMetrics:
        """Increment the total tickets processed counter"""
        try:
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Update existing metrics
                updated_data = {
                    "total_tickets_processed": current.total_tickets_processed + 1,
                    "updated_at": utcnow().isoformat()
                }
                
                result = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                logger.info(f"Incremented tickets processed to {current.total_tickets_processed + 1}")
                return result[0] if isinstance(result, list) else result
            else:
                # Create new metrics with 1 ticket processed
                return LearningMetricsManager.create_or_update_metrics(total_tickets_processed=1)
                
        except Exception as e:
            logger.error(f"Failed to increment ticket processed: {e}")
            raise
    
    @staticmethod
    def increment_successful_resolution() -> LearningMetrics:
        """Increment the successful resolutions counter"""
        try:
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Update existing metrics
                updated_data = {
                    "successful_resolutions": current.successful_resolutions + 1,
                    "updated_at": utcnow().isoformat()
                }
                
                result = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                logger.info(f"Incremented successful resolutions to {current.successful_resolutions + 1}")
                return result[0] if isinstance(result, list) else result
            else:
                # Create new metrics with 1 successful resolution
                return LearningMetricsManager.create_or_update_metrics(successful_resolutions=1)
                
        except Exception as e:
            logger.error(f"Failed to increment successful resolution: {e}")
            raise
    
    @staticmethod
    def increment_escalation() -> LearningMetrics:
        """Increment the escalations counter"""
        try:
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Update existing metrics
                updated_data = {
                    "escalations": current.escalations + 1,
                    "updated_at": utcnow().isoformat()
                }
                
                result = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                logger.info(f"Incremented escalations to {current.escalations + 1}")
                return result[0] if isinstance(result, list) else result
            else:
                # Create new metrics with 1 escalation
                return LearningMetricsManager.create_or_update_metrics(escalations=1)
                
        except Exception as e:
            logger.error(f"Failed to increment escalation: {e}")
            raise
    
    @staticmethod
    def process_feedback(is_positive: bool) -> LearningMetrics:
        """Process user feedback and update metrics"""
        try:
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Update existing metrics
                updated_data = {
                    "feedback_count": current.feedback_count + 1,
                    "positive_feedback": current.positive_feedback + (1 if is_positive else 0),
                    "updated_at": utcnow().isoformat()
                }
                
                result = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                feedback_type = "positive" if is_positive else "negative"
                logger.info(f"Processed {feedback_type} feedback - Total: {current.feedback_count + 1}")
                return result[0] if isinstance(result, list) else result
            else:
                # Create new metrics with feedback
                return LearningMetricsManager.create_or_update_metrics(
                    feedback_count=1,
                    positive_feedback=1 if is_positive else 0
                )
                
        except Exception as e:
            logger.error(f"Failed to process feedback: {e}")
            raise
    
    @staticmethod
    def update_confidence(new_confidence: float) -> LearningMetrics:
        """Update the average confidence score"""
        try:
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Calculate new average confidence
                total_tickets = current.total_tickets_processed
                if total_tickets > 0:
                    # Weighted average calculation
                    current_total = current.average_confidence * total_tickets
                    new_average = (current_total + new_confidence) / (total_tickets + 1)
                else:
                    new_average = new_confidence
                
                # Update existing metrics
                updated_data = {
                    "average_confidence": round(new_average, 3),
                    "updated_at": utcnow().isoformat()
                }
                
                result = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                logger.info(f"Updated confidence score to {new_average:.3f}")
                return result[0] if isinstance(result, list) else result
            else:
                # Create new metrics with confidence
                return LearningMetricsManager.create_or_update_metrics(
                    average_confidence=new_confidence
                )
                
        except Exception as e:
            logger.error(f"Failed to update confidence: {e}")
            raise
    
    @staticmethod
    def update_patterns(
        resolution_patterns: Optional[Dict] = None,
        common_failures: Optional[Dict] = None
    ) -> LearningMetrics:
        """Update resolution patterns and common failures"""
        try:
            current = LearningMetricsManager.get_current_metrics()
            
            if current:
                # Merge with existing patterns
                updated_data = {}
                
                if resolution_patterns:
                    existing_patterns = current.resolution_patterns or {}
                    merged_patterns = {**existing_patterns, **resolution_patterns}
                    updated_data["resolution_patterns"] = merged_patterns
                
                if common_failures:
                    existing_failures = current.common_failures or {}
                    merged_failures = {**existing_failures, **common_failures}
                    updated_data["common_failures"] = merged_failures
                
                if updated_data:
                    updated_data["updated_at"] = utcnow().isoformat()
                    
                    result = db_manager.learning_metrics.update(
                    filters={"id": current.id},
                    values=updated_data
                )
                    logger.info("Updated learning patterns and failures")
                    return result[0] if isinstance(result, list) else result
                else:
                    return current
            else:
                # Create new metrics with patterns
                return LearningMetricsManager.create_or_update_metrics(
                    resolution_patterns=resolution_patterns or {},
                    common_failures=common_failures or {}
                )
                
        except Exception as e:
            logger.error(f"Failed to update patterns: {e}")
            raise