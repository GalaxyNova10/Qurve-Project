"""
Qurve AI - Monitoring API Routes
READ-ONLY operational observability endpoints.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List, Any, Optional
import logging

from .monitoring_service import (
    get_monitoring_service, 
    SystemHealth, 
    SystemMetrics, 
    SolverMetrics, 
    CloudMetrics
)

logger = logging.getLogger(__name__)

# Create monitoring router
monitoring_router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])

@monitoring_router.get("/overview", response_model=Dict[str, Any])
async def get_monitoring_overview():
    """
    Get system overview with key operational metrics.
    READ-ONLY endpoint for operational visibility.
    """
    try:
        monitoring = get_monitoring_service()
        
        # Get all metrics
        system_metrics = monitoring.get_system_metrics()
        system_health = monitoring.get_system_health()
        memory_usage = monitoring.get_memory_usage()
        
        # Calculate derived overview metrics
        total_executions = sum(
            solver.success_count + solver.failure_count 
            for solver in monitoring.get_solver_metrics().values()
        )
        
        cloud_metrics = monitoring.get_cloud_metrics()
        
        return {
            "system_health": system_health.value,
            "active_executions": system_metrics.active_executions,
            "total_executions": total_executions,
            "success_rate": 100.0 - system_metrics.failure_rate,
            "avg_latency_ms": system_metrics.avg_execution_latency_ms,
            "throughput_per_min": system_metrics.execution_throughput_per_min,
            "fallback_frequency": system_metrics.fallback_frequency,
            "timeout_count": system_metrics.timeout_count,
            "cloud_active_tasks": cloud_metrics.active_aws_tasks,
            "cloud_queue_latency_ms": cloud_metrics.cloud_queue_latency_ms,
            "cloud_execution_latency_ms": cloud_metrics.cloud_execution_latency_ms,
            "estimated_cloud_cost": cloud_metrics.estimated_cloud_cost,
            "memory_usage_mb": memory_usage["estimated_memory_mb"],
            "events_buffer_size": memory_usage["events_buffer_size"],
            "last_updated": monitoring._last_update
        }
        
    except Exception as e:
        logger.error("Failed to get monitoring overview", error=str(e))
        raise HTTPException(status_code=500, detail="Monitoring overview unavailable")

@monitoring_router.get("/solvers", response_model=Dict[str, Any])
async def get_solver_metrics():
    """
    Get per-solver operational metrics.
    READ-ONLY endpoint for solver performance visibility.
    """
    try:
        monitoring = get_monitoring_service()
        solver_metrics = monitoring.get_solver_metrics()
        
        # Convert to response format
        solver_data = {}
        for solver_name, metrics in solver_metrics.items():
            total_executions = metrics.success_count + metrics.failure_count
            success_rate = (
                (metrics.success_count / total_executions * 100) 
                if total_executions > 0 else 0.0
            )
            
            solver_data[solver_name] = {
                "status": metrics.status,
                "avg_latency_ms": metrics.avg_latency_ms,
                "total_executions": total_executions,
                "success_count": metrics.success_count,
                "failure_count": metrics.failure_count,
                "success_rate": success_rate,
                "fallback_count": metrics.fallback_count,
                "feasibility_rate": metrics.feasibility_rate,
                "cloud_usage_count": metrics.cloud_usage_count,
                "local_usage_count": metrics.local_usage_count,
                "cloud_usage_percentage": (
                    (metrics.cloud_usage_count / total_executions * 100)
                    if total_executions > 0 else 0.0
                )
            }
        
        return {
            "solvers": solver_data,
            "total_solvers": len(solver_data),
            "healthy_solvers": len([
                s for s in solver_data.values() 
                if s["status"] == "healthy"
            ])
        }
        
    except Exception as e:
        logger.error("Failed to get solver metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Solver metrics unavailable")

@monitoring_router.get("/cloud", response_model=Dict[str, Any])
async def get_cloud_metrics():
    """
    Get cloud-specific operational metrics.
    READ-ONLY endpoint for cloud execution visibility.
    """
    try:
        monitoring = get_monitoring_service()
        cloud_metrics = monitoring.get_cloud_metrics()
        
        return {
            "active_aws_tasks": cloud_metrics.active_aws_tasks,
            "cloud_queue_latency_ms": cloud_metrics.cloud_queue_latency_ms,
            "cloud_execution_latency_ms": cloud_metrics.cloud_execution_latency_ms,
            "aws_region_usage": cloud_metrics.aws_region_usage,
            "task_state_distribution": cloud_metrics.task_state_distribution,
            "estimated_cloud_cost": cloud_metrics.estimated_cloud_cost,
            "supported_regions": list(cloud_metrics.aws_region_usage.keys()),
            "primary_region": max(
                cloud_metrics.aws_region_usage.items(), 
                key=lambda x: x[1], 
                default=("unknown", 0)
            )[0] if cloud_metrics.aws_region_usage else "unknown"
        }
        
    except Exception as e:
        logger.error("Failed to get cloud metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Cloud metrics unavailable")

@monitoring_router.get("/recent-events", response_model=Dict[str, Any])
async def get_recent_events(limit: int = 100):
    """
    Get recent execution events.
    READ-ONLY endpoint for execution stream visibility.
    """
    try:
        if limit < 1 or limit > 1000:
            raise HTTPException(
                status_code=400, 
                detail="Limit must be between 1 and 1000"
            )
        
        monitoring = get_monitoring_service()
        events = monitoring.get_recent_events(limit)
        
        # Convert events to response format
        event_data = []
        for event in events:
            event_data.append({
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "solver": event.solver,
                "execution_mode": event.execution_mode,
                "correlation_id": event.correlation_id,
                "latency_ms": event.latency_ms,
                "cloud_task_arn": event.cloud_task_arn,
                "error_message": event.error_message
            })
        
        return {
            "events": event_data,
            "total_events": len(event_data),
            "limit": limit,
            "events_buffer_size": monitoring.events_buffer.maxlen
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get recent events", error=str(e))
        raise HTTPException(status_code=500, detail="Recent events unavailable")

@monitoring_router.get("/health", response_model=Dict[str, Any])
async def get_monitoring_health():
    """
    Get monitoring service health status.
    READ-ONLY endpoint for monitoring system visibility.
    """
    try:
        monitoring = get_monitoring_service()
        system_health = monitoring.get_system_health()
        memory_usage = monitoring.get_memory_usage()
        
        # Determine monitoring service health
        monitoring_health = "healthy"
        if memory_usage["estimated_memory_mb"] > 100:
            monitoring_health = "degraded"
        if memory_usage["events_buffer_size"] >= memory_usage["events_buffer_max"] * 0.9:
            monitoring_health = "degraded"
        
        return {
            "monitoring_service_health": monitoring_health,
            "system_health": system_health.value,
            "events_buffer_size": memory_usage["events_buffer_size"],
            "events_buffer_max": memory_usage["events_buffer_max"],
            "estimated_memory_mb": memory_usage["estimated_memory_mb"],
            "last_update": monitoring._last_update,
            "uptime_seconds": time.time() - monitoring._last_update if hasattr(monitoring, '_start_time') else 0
        }
        
    except Exception as e:
        logger.error("Failed to get monitoring health", error=str(e))
        raise HTTPException(status_code=500, detail="Monitoring health unavailable")

@monitoring_router.get("/system", response_model=Dict[str, Any])
async def get_system_detailed_metrics():
    """
    Get detailed system metrics.
    READ-ONLY endpoint for deep operational visibility.
    """
    try:
        monitoring = get_monitoring_service()
        system_metrics = monitoring.get_system_metrics()
        
        return {
            "active_executions": system_metrics.active_executions,
            "queued_cloud_tasks": system_metrics.queued_cloud_tasks,
            "avg_execution_latency_ms": system_metrics.avg_execution_latency_ms,
            "execution_throughput_per_min": system_metrics.execution_throughput_per_min,
            "fallback_frequency": system_metrics.fallback_frequency,
            "timeout_count": system_metrics.timeout_count,
            "failure_rate": system_metrics.failure_rate,
            "retry_rate": system_metrics.retry_rate
        }
        
    except Exception as e:
        logger.error("Failed to get system metrics", error=str(e))
        raise HTTPException(status_code=500, detail="System metrics unavailable")

@monitoring_router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics():
    """
    Get monitoring service performance metrics.
    READ-ONLY endpoint for performance visibility.
    """
    try:
        monitoring = get_monitoring_service()
        memory_usage = monitoring.get_memory_usage()
        
        # Calculate performance indicators
        buffer_utilization = (
            memory_usage["events_buffer_size"] / memory_usage["events_buffer_max"] * 100
        )
        
        return {
            "memory_usage_mb": memory_usage["estimated_memory_mb"],
            "events_buffer_utilization": buffer_utilization,
            "events_buffer_size": memory_usage["events_buffer_size"],
            "events_buffer_max": memory_usage["events_buffer_max"],
            "solver_metrics_count": memory_usage["solver_metrics_count"],
            "update_interval_seconds": monitoring._update_interval,
            "last_update": monitoring._last_update,
            "performance_status": (
                "optimal" if buffer_utilization < 80 and memory_usage["estimated_memory_mb"] < 100
                else "degraded"
            )
        }
        
    except Exception as e:
        logger.error("Failed to get performance metrics", error=str(e))
        raise HTTPException(status_code=500, detail="Performance metrics unavailable")
