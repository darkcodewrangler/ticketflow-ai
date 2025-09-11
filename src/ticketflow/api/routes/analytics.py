"""
Analytics API routes
Performance metrics, dashboard data, and insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ticketflow.utils.helpers import get_isoformat, get_value, utcnow

from ...database.operations import AnalyticsOperations
from ...database.schemas import DashboardMetricsResponse
from ..dependencies import verify_db_connection

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    _: bool = Depends(verify_db_connection)
):
    """Get current dashboard metrics and KPIs"""
    try:
        metrics = await AnalyticsOperations.get_dashboard_metrics()
        return DashboardMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=500,    
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


@router.get("/performance/daily")
async def get_daily_performance(
    date: Optional[str] = Query(None, description="Date (YYYY-MM-DD), defaults to today"),
    _: bool = Depends(verify_db_connection)
):
    """Get daily performance metrics"""
    try:
        target_date = date or get_isoformat(utcnow().date())
        
        # Use the existing create_daily_metrics method
        metrics = await AnalyticsOperations.create_daily_metrics(target_date)
        
        return {
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
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily performance: {str(e)}"
        )


@router.get("/performance/summary")
async def get_performance_summary(
    _: bool = Depends(verify_db_connection)
):
    """Get performance summary - simplified version"""
    try:
        dashboard_metrics = await AnalyticsOperations.get_dashboard_metrics()

        
        return {
            "summary": "Performance overview",
            "metrics": dashboard_metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance summary: {str(e)}"
        )


@router.get("/categories")
async def get_category_breakdown(
    _: bool = Depends(verify_db_connection)
):
    """Get ticket breakdown by category"""
    try:
        # Simple category breakdown using direct PyTiDB queries
        from ...database.connection import db_manager
        tickets = db_manager.tickets.query(limit=int(1000)).to_list()
        
        categories = {}
        for ticket in tickets:
            category = getattr(ticket, 'category', 'general') if hasattr(ticket, 'category') else ticket.get('category', 'general')
            categories[category] = categories.get(category, 0) + 1
        
        return {
            "categories": categories,
            "total_tickets": len(tickets)
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get category breakdown: {str(e)}"
        )


@router.get("/stats")
async def get_basic_stats(
    _: bool = Depends(verify_db_connection)
):
    """Get basic statistics from all data"""
    try:
        from ...database.connection import db_manager
        
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
        
        return {
            "totals": {
                "tickets": len(tickets),
                "kb_articles": len(articles),
                "workflows": len(workflows)
            },
            "priority_breakdown": priority_breakdown,
            "status_breakdown": status_breakdown
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get basic stats: {str(e)}"
        )
