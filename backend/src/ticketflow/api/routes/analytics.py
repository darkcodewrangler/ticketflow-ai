"""
Analytics API routes
Performance metrics, dashboard data, and insights
"""

from ticketflow.database.connection import db_manager
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import  Optional
from ticketflow.utils.helpers import get_isoformat, get_value, utcnow
from ticketflow.database.operations import AnalyticsOperations
from ticketflow.database.schemas import DashboardMetricsResponse
from ticketflow.api.dependencies import verify_db_connection, require_permissions
from ticketflow.api.response_models import (
    success_response, error_response, paginated_response,
    ResponseMessages, ErrorCodes
)

router = APIRouter()


@router.get("/dashboard")
async def get_dashboard_metrics(
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_analytics"]))
):
    """Get current dashboard metrics and KPIs"""
    try:
        metrics = await AnalyticsOperations.get_dashboard_metrics()
        dashboard_data = DashboardMetricsResponse(**metrics).model_dump()
        
        return success_response(
            data=dashboard_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"type": "dashboard_metrics"}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve dashboard metrics",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/performance/daily")
async def get_daily_performance(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_analytics"]))
):
    """Get daily performance metrics"""
    try:
        target_date = date or get_isoformat(utcnow().date())
        
        # Use the existing create_daily_metrics method
        metrics = await AnalyticsOperations.create_daily_metrics(target_date)
        
        performance_data = {
            "date": target_date,
            "metrics": {
                "tickets_processed": metrics.tickets_processed,
                "tickets_auto_resolved": metrics.tickets_auto_resolved,
                "tickets_escalated": metrics.tickets_escalated,
                "category_breakdown": metrics.category_breakdown,
                "estimated_time_saved_hours": metrics.estimated_time_saved_hours,
                "estimated_cost_saved": metrics.estimated_cost_saved
            }
        }
        
        return success_response(
            data=performance_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"date": target_date, "type": "daily_performance"}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve daily performance metrics",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/performance/summary")
async def get_performance_summary(
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_analytics"]))
):
    """Get performance summary - simplified version"""
    try:
        dashboard_metrics = await AnalyticsOperations.get_dashboard_metrics()
        
        summary_data = {
            "summary": "Performance overview",
            "metrics": dashboard_metrics
        }
        
        return success_response(
            data=summary_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"type": "performance_summary"}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve performance summary",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/categories")
async def get_category_breakdown(
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_analytics"]))
):
    """Get ticket breakdown by category"""
    try:
        # Simple category breakdown using direct PyTiDB queries
        tickets = db_manager.tickets.query(limit=int(1000)).to_list()
        
        categories = {}
        for ticket in tickets:
            category = getattr(ticket, 'category', 'general') if hasattr(ticket, 'category') else ticket.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        
        category_data = {
            "categories": categories,
            "total_tickets": len(tickets)
        }
        
        return success_response(
            data=category_data,
            message=ResponseMessages.RETRIEVED,
            count=len(categories),
            metadata={"type": "category_breakdown", "total_tickets": len(tickets)}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve category breakdown",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )


@router.get("/stats")
async def get_basic_stats(
    _: bool = Depends(verify_db_connection),
    api_key_data: dict = Depends(require_permissions(["read_analytics"]))
):
    """Get basic statistics from all data"""
    try:
        
        # Get basic counts
        tickets = db_manager.tickets.query(limit=int(1000)).to_list()
        articles = db_manager.kb_articles.query(limit=int(1000)).to_list()
        workflows = db_manager.agent_workflows.query(limit=int(1000)).to_list()

        # Calculate basic stats
        priority_breakdown = {}
        status_breakdown = {}
        
        for ticket in tickets:
            priority = get_value(ticket, 'priority', 'medium')
            status = get_value(ticket, 'status', 'new')
            
            priority_breakdown[priority] = priority_breakdown.get(priority, 0) + 1
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        stats_data = {
            "totals": {
                "tickets": len(tickets),
                "kb_articles": len(articles),
                "workflows": len(workflows)
            },
            "priority_breakdown": priority_breakdown,
            "status_breakdown": status_breakdown
        }
        
        return success_response(
            data=stats_data,
            message=ResponseMessages.RETRIEVED,
            metadata={"type": "basic_statistics"}
        )
    except Exception as e:
        return error_response(
            message="Failed to retrieve basic statistics",
            error=str(e),
            error_code=ErrorCodes.INTERNAL_ERROR
        )
