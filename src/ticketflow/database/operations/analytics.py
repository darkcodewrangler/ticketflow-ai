

import logging
from typing import Any, Dict
from datetime import datetime, timezone

from pytidb.filters import GTE

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
            
            # Calculate metrics - handle both objects and dicts
            total_today = len(today_tickets)
            auto_resolved_today = 0
            processing = 0
            
            for t in today_tickets:
                status = get_value(t, 'status', None) 
                if status == TicketStatus.RESOLVED.value:
                    auto_resolved_today += 1
                elif status == TicketStatus.PROCESSING.value:
                    processing += 1
            
            # Get recent resolved tickets for avg confidence
            resolved_tickets = db_manager.tickets.query(
                filters={"status": TicketStatus.RESOLVED.value},
                limit=100, order_by={"resolved_at": "desc"}
            ).to_list()
            
            avg_confidence = 0.0
            if resolved_tickets:
                confidences = []
                for t in resolved_tickets:
                    confidence = get_value(t, 'agent_confidence', 0) 
                    if confidence > 0:
                        confidences.append(confidence)
                
                if confidences:
                    avg_confidence = sum(confidences) / len(confidences)
            
            return {
                "tickets_today": total_today,
                "tickets_auto_resolved_today": auto_resolved_today,
                "currently_processing": processing,
                "avg_confidence": avg_confidence,
                "automation_rate": (auto_resolved_today / total_today * 100) if total_today > 0 else 0,
                "resolution_rate": (auto_resolved_today / total_today * 100) if total_today > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get dashboard metrics: {e}")
            return {
                "tickets_today": 0,
                "tickets_auto_resolved_today": 0,
                "currently_processing": 0,
                "avg_confidence": 0.0,
                "automation_rate": 0.0,
                "resolution_rate": 0.0
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
            
            created_metrics = db_manager.performance_metrics.insert(metrics)
            logger.info(f"📊 Created daily metrics for {target_date}")
            return created_metrics
            
        except Exception as e:
            logger.error(f"❌ Failed to create daily metrics: {e}")
            raise


__all__ = [
    "AnalyticsOperations"
]
