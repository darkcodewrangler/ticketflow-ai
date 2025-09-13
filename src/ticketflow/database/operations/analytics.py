

import logging
from typing import Any, Dict
from datetime import datetime, timezone

from pytidb.filters import GTE, NE

from ticketflow.database.connection import db_manager
from ticketflow.database.models import PerformanceMetrics, ResolutionType, TicketStatus
from ticketflow.utils.helpers import get_isoformat, get_value, utcnow
logger = logging.getLogger(__name__)
class AnalyticsOperations:
    """
    Performance analytics and metrics operations
    """

    @staticmethod
    async def get_dashboard_metrics() -> Dict[str, Any]:
        """Get real-time dashboard metrics"""
        try:
            # Get today's tickets
            today = get_isoformat(utcnow().date())
            today_tickets = db_manager.tickets.query(
                filters={"created_at": {GTE: today}},
                limit=1000  # Reasonable limit for today
            ).to_list()

            # Get all non-resolved tickets for pending count
            pending_tickets_list = db_manager.tickets.query(
                filters={"status": {NE: TicketStatus.RESOLVED.value}},
                limit=1000
            ).to_list()
            
            # Calculate metrics
            total_today = len(today_tickets)
            auto_resolved_today = 0
            processing = 0
            processing_durations = []
            resolution_hours = []
            category_breakdown = {}
            priority_breakdown = {}

            for t in today_tickets:
                status = get_value(t, 'status', None)
                category = get_value(t, 'category', 'general')
                priority = get_value(t, 'priority', 'medium')

                category_breakdown[category] = category_breakdown.get(category, 0) + 1
                priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1

                if status == TicketStatus.RESOLVED.value:
                    auto_resolved_today += 1
                    created_at = get_value(t, 'created_at')
                    resolved_at = get_value(t, 'resolved_at')
                    if created_at and resolved_at:
                        # Ensure created_at and resolved_at are datetime objects
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if isinstance(resolved_at, str):
                            resolved_at = datetime.fromisoformat(resolved_at.replace('Z', '+00:00'))
                        
                        # Make sure they are timezone-aware for correct subtraction
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        if resolved_at.tzinfo is None:
                            resolved_at = resolved_at.replace(tzinfo=timezone.utc)

                        resolution_hours.append((resolved_at - created_at).total_seconds() / 3600)

                elif status == TicketStatus.PROCESSING.value:
                    processing += 1
                    created_at = get_value(t, 'created_at')
                    updated_at = get_value(t, 'updated_at')
                    if created_at and updated_at:
                        if isinstance(created_at, str):
                            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        if isinstance(updated_at, str):
                            updated_at = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                        
                        if created_at.tzinfo is None:
                            created_at = created_at.replace(tzinfo=timezone.utc)
                        if updated_at.tzinfo is None:
                            updated_at = updated_at.replace(tzinfo=timezone.utc)

                        processing_durations.append((updated_at - created_at).total_seconds() * 1000)


            # Get recent resolved tickets for avg confidence
            resolved_tickets = db_manager.tickets.query(
                filters={"status": TicketStatus.RESOLVED.value},
                limit=100, order_by={"resolved_at": "desc"}
            ).to_list()
            
            avg_confidence = 0.0
            if resolved_tickets:
                confidences = [get_value(t, 'agent_confidence', 0) for t in resolved_tickets if get_value(t, 'agent_confidence', 0) > 0]
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
            
            avg_processing_time_ms = sum(processing_durations) / len(processing_durations) if processing_durations else 0
            avg_resolution_hours = sum(resolution_hours) / len(resolution_hours) if resolution_hours else 0
            automation_rate = (auto_resolved_today / total_today * 100) if total_today > 0 else 0
            
            # Mocked/default values for fields not easily calculable in real-time
            customer_satisfaction_avg = 4.5  # Mock value
            estimated_time_saved_hours = auto_resolved_today * 0.25 # 15 mins per ticket
            estimated_cost_saved = auto_resolved_today * 12.5 # $50/hr * 0.25

            return {
                "tickets_today": total_today,
                "tickets_auto_resolved_today": auto_resolved_today,
                "currently_processing": processing,
                "pending_tickets": len(pending_tickets_list),
                "avg_confidence": avg_confidence,
                "avg_processing_time_ms": avg_processing_time_ms,
                "avg_resolution_hours": avg_resolution_hours,
                "automation_rate": automation_rate,
                "resolution_rate": automation_rate,  # Assuming resolution_rate is same as automation_rate for now
                "customer_satisfaction_avg": customer_satisfaction_avg,
                "estimated_time_saved_hours": estimated_time_saved_hours,
                "estimated_cost_saved": estimated_cost_saved,
                "category_breakdown": category_breakdown,
                "priority_breakdown": priority_breakdown,
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard metrics: {e}")
            # Return a default structure matching the schema on error
            return {
                "tickets_today": 0,
                "tickets_auto_resolved_today": 0,
                "currently_processing": 0,
                "pending_tickets": 0,
                "avg_confidence": 0.0,
                "avg_processing_time_ms": 0.0,
                "avg_resolution_hours": 0.0,
                "automation_rate": 0.0,
                "resolution_rate": 0.0,
                "customer_satisfaction_avg": 0.0,
                "estimated_time_saved_hours": 0.0,
                "estimated_cost_saved": 0.0,
                "category_breakdown": {},
                "priority_breakdown": {},
            }

    @staticmethod
    async def create_daily_metrics(date: str = None) -> PerformanceMetrics:

        """Create daily performance metrics"""
        target_date = date or get_isoformat(utcnow().date())
        
        try:
            # Get tickets for the day
            day_tickets = db_manager.tickets.query(
                filters={"created_at": {GTE: target_date}},
                limit=10000  # Large limit for full day
            ).to_list() 
            
            # Calculate metrics - handle both objects and dicts
            total = len(day_tickets)
            auto_resolved = 0
            escalated = 0
            
            # Category breakdown
            categories = {}
            for ticket in day_tickets:
                # Handle both object attributes and dictionary keys
                resolution_type = get_value(ticket, 'resolution_type', None) 
                status = get_value(ticket, 'status', None) 
                category = get_value(ticket, 'category', 'general') 
                
                if resolution_type == ResolutionType.AUTOMATED.value:
                    auto_resolved += 1
                if status == TicketStatus.ESCALATED.value:
                    escalated += 1
                    
                categories[category] = categories.get(category, 0) + 1
            
            # Create metrics record
            metrics = PerformanceMetrics(
                metric_date=target_date,
                tickets_processed=total,
                tickets_auto_resolved=auto_resolved,
                tickets_escalated=escalated,
                category_breakdown=categories,
                estimated_time_saved_hours=auto_resolved * 0.25,  # 15 min per ticket
                estimated_cost_saved=auto_resolved * 12.5  # $50/hour * 0.25 hours
            )
            
            result = db_manager.performance_metrics.insert(metrics)
            # Handle case where insert returns a list
            created_metrics = result[0] if isinstance(result, list) else result
            logger.info(f"📊 Created daily metrics for {target_date}")
            return created_metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to create daily metrics: {e}")
            raise


__all__ = [
    "AnalyticsOperations"
]
