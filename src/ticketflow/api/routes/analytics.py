"""
Analytics API routes
Performance metrics, dashboard data, and insights
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ...database.operations import AnalyticsOperations
from ...database.schemas import DashboardMetricsResponse
from ..dependencies import get_db_session

router = APIRouter()


@router.get("/dashboard", response_model=DashboardMetricsResponse)
async def get_dashboard_metrics(
    session: Session = Depends(get_db_session)
):
    """Get current dashboard metrics and KPIs"""
    try:
        metrics = await AnalyticsOperations.get_dashboard_metrics(session)
        return DashboardMetricsResponse(**metrics)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get dashboard metrics: {str(e)}"
        )


@router.get("/performance/daily")
async def get_daily_performance(
    days: int = Query(30, ge=1, le=90, description="Number of days to retrieve"),
    session: Session = Depends(get_db_session)
):
    """Get daily performance metrics over time"""
    try:
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)
        
        metrics = await AnalyticsOperations.get_performance_trends(
            session, start_date, end_date, "daily"
        )
        
        return {
            "period": f"{start_date} to {end_date}",
            "granularity": "daily",
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get daily performance: {str(e)}"
        )


@router.get("/performance/hourly")
async def get_hourly_performance(
    hours: int = Query(24, ge=1, le=168, description="Number of hours to retrieve"),
    session: Session = Depends(get_db_session)
):
    """Get hourly performance metrics"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        metrics = await AnalyticsOperations.get_performance_trends(
            session, start_time.date(), end_time.date(), "hourly"
        )
        
        return {
            "period": f"{start_time} to {end_time}",
            "granularity": "hourly", 
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get hourly performance: {str(e)}"
        )


@router.get("/categories")
async def get_category_breakdown(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    session: Session = Depends(get_db_session)
):
    """Get ticket breakdown by category"""
    try:
        breakdown = await AnalyticsOperations.get_category_breakdown(session, days)
        return {
            "period_days": days,
            "categories": breakdown
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get category breakdown: {str(e)}"
        )


@router.get("/priorities")
async def get_priority_breakdown(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    session: Session = Depends(get_db_session)
):
    """Get ticket breakdown by priority"""
    try:
        breakdown = await AnalyticsOperations.get_priority_breakdown(session, days)
        return {
            "period_days": days,
            "priorities": breakdown
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get priority breakdown: {str(e)}"
        )


@router.get("/resolution-times")
async def get_resolution_time_analysis(
    days: int = Query(30, ge=1, le=90, description="Number of days to analyze"),
    session: Session = Depends(get_db_session)
):
    """Get resolution time analysis"""
    try:
        analysis = await AnalyticsOperations.get_resolution_time_analysis(session, days)
        return {
            "period_days": days,
            "analysis": analysis
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get resolution time analysis: {str(e)}"
        )


@router.get("/agent-performance")
async def get_agent_performance(
    days: int = Query(7, ge=1, le=30, description="Number of days to analyze"),
    session: Session = Depends(get_db_session)
):
    """Get AI agent performance metrics"""
    try:
        performance = await AnalyticsOperations.get_agent_performance(session, days)
        return {
            "period_days": days,
            "performance": performance
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent performance: {str(e)}"
        )


@router.get("/knowledge-base/stats")
async def get_knowledge_base_stats(
    session: Session = Depends(get_db_session)
):
    """Get knowledge base usage and effectiveness statistics"""
    try:
        stats = await AnalyticsOperations.get_kb_statistics(session)
        return {
            "statistics": stats
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get KB statistics: {str(e)}"
        )


@router.post("/export")
async def export_analytics_data(
    start_date: str = Query(..., description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., description="End date (YYYY-MM-DD)"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    session: Session = Depends(get_db_session)
):
    """Export analytics data for the specified date range"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        
        if end < start:
            raise HTTPException(
                status_code=400,
                detail="End date must be after start date"
            )
        
        if (end - start).days > 365:
            raise HTTPException(
                status_code=400,
                detail="Date range cannot exceed 365 days"
            )
        
        data = await AnalyticsOperations.export_analytics_data(
            session, start, end, format
        )
        
        return {
            "start_date": start_date,
            "end_date": end_date,
            "format": format,
            "data": data
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export analytics data: {str(e)}"
        )
