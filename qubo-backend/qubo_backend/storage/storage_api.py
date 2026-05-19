"""
Qurve AI - Storage API Routes
READ-ONLY endpoints for execution persistence data.
"""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Dict, List, Any, Optional
import logging

from .execution_storage import (
    get_execution_storage,
    BenchmarkRun,
    SolverExecution,
    CloudTask,
    TelemetryEvent
)

logger = logging.getLogger(__name__)

# Create storage router
storage_router = APIRouter(prefix="/api/v1/storage", tags=["storage"])

@storage_router.get("/benchmarks", response_model=Dict[str, Any])
async def get_benchmarks(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> Dict[str, Any]:
    """
    Get benchmark runs with pagination.
    READ-ONLY endpoint for execution history.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        # Get benchmark runs
        benchmarks = await storage.get_benchmark_runs(limit=limit, offset=offset)
        
        return {
            "benchmarks": [
                {
                    "benchmark_id": b.benchmark_id,
                    "correlation_id": b.correlation_id,
                    "started_at": b.started_at.isoformat() if b.started_at else None,
                    "completed_at": b.completed_at.isoformat() if b.completed_at else None,
                    "duration_ms": b.duration_ms,
                    "status": b.status.value,
                    "selected_solver": b.selected_solver,
                    "fallback_chain": b.fallback_chain,
                    "num_assets": b.num_assets,
                    "execution_mode": b.execution_mode,
                    "metadata": b.metadata
                }
                for b in benchmarks
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(benchmarks) == limit
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get benchmarks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve benchmarks")

@storage_router.get("/benchmark/{benchmark_id}", response_model=Dict[str, Any])
async def get_benchmark_details(
    benchmark_id: str = Path(..., description="Benchmark ID")
) -> Dict[str, Any]:
    """
    Get detailed benchmark information including solver executions.
    READ-ONLY endpoint for benchmark replay metadata.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        # Get benchmark and solver executions
        benchmarks = await storage.get_benchmark_runs(limit=1, offset=0)
        benchmark = next((b for b in benchmarks if b.benchmark_id == benchmark_id), None)
        
        if not benchmark:
            raise HTTPException(status_code=404, detail="Benchmark not found")
        
        solver_executions = await storage.get_solver_executions(benchmark_id)
        
        return {
            "benchmark": {
                "benchmark_id": benchmark.benchmark_id,
                "correlation_id": benchmark.correlation_id,
                "started_at": benchmark.started_at.isoformat() if benchmark.started_at else None,
                "completed_at": benchmark.completed_at.isoformat() if benchmark.completed_at else None,
                "duration_ms": benchmark.duration_ms,
                "status": benchmark.status.value,
                "selected_solver": benchmark.selected_solver,
                "fallback_chain": benchmark.fallback_chain,
                "num_assets": benchmark.num_assets,
                "execution_mode": benchmark.execution_mode,
                "metadata": benchmark.metadata
            },
            "solver_executions": [
                {
                    "execution_id": e.execution_id,
                    "solver_name": e.solver_name,
                    "provider": e.provider,
                    "backend": e.backend,
                    "latency_ms": e.latency_ms,
                    "feasibility": e.feasibility,
                    "fallback_used": e.fallback_used,
                    "energy": e.energy,
                    "status": e.status.value,
                    "metadata": e.metadata
                }
                for e in solver_executions
            ],
            "replay_metadata": {
                "original_request": benchmark.metadata.get("request_payload"),
                "solver_selection": benchmark.selected_solver,
                "execution_mode": benchmark.execution_mode,
                "fallback_chain": benchmark.fallback_chain,
                "supports_replay": True
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get benchmark details", benchmark_id=benchmark_id, error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve benchmark details")

@storage_router.get("/executions", response_model=Dict[str, Any])
async def get_executions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    benchmark_id: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get solver executions with optional benchmark filter.
    READ-ONLY endpoint for execution analytics.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        executions = []
        if benchmark_id:
            executions = await storage.get_solver_executions(benchmark_id)
        else:
            # Get all executions (would need to implement this method)
            executions = []
        
        return {
            "executions": [
                {
                    "execution_id": e.execution_id,
                    "benchmark_id": e.benchmark_id,
                    "solver_name": e.solver_name,
                    "provider": e.provider,
                    "backend": e.backend,
                    "latency_ms": e.latency_ms,
                    "feasibility": e.feasibility,
                    "fallback_used": e.fallback_used,
                    "energy": e.energy,
                    "status": e.status.value,
                    "metadata": e.metadata
                }
                for e in executions
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(executions) == limit
            },
            "filter": {
                "benchmark_id": benchmark_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get executions", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve executions")

@storage_router.get("/cloud-tasks", response_model=Dict[str, Any])
async def get_cloud_tasks(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    status: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get cloud tasks with optional status filter.
    READ-ONLY endpoint for cloud execution monitoring.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        tasks = await storage.get_cloud_tasks(limit=limit, status=status)
        
        return {
            "cloud_tasks": [
                {
                    "task_arn": t.task_arn,
                    "device_arn": t.device_arn,
                    "region": t.region,
                    "shots": t.shots,
                    "queue_latency_ms": t.queue_latency_ms,
                    "execution_latency_ms": t.execution_latency_ms,
                    "total_latency_ms": t.total_latency_ms,
                    "task_status": t.task_status.value,
                    "failure_reason": t.failure_reason,
                    "metadata": t.metadata
                }
                for t in tasks
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(tasks) == limit
            },
            "filter": {
                "status": status
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get cloud tasks", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve cloud tasks")

@storage_router.get("/telemetry", response_model=Dict[str, Any])
async def get_telemetry_events(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    event_type: Optional[str] = Query(None),
    severity: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """
    Get telemetry events with optional filtering.
    READ-ONLY endpoint for analytics and debugging.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        # Note: This would need to be implemented in execution_storage
        events = []
        
        return {
            "events": [
                {
                    "event_id": e.event_id,
                    "correlation_id": e.correlation_id,
                    "timestamp": e.timestamp.isoformat(),
                    "event_type": e.event_type,
                    "severity": e.severity,
                    "payload": e.payload_json
                }
                for e in events
            ],
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": len(events) == limit
            },
            "filters": {
                "event_type": event_type,
                "severity": severity
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get telemetry events", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve telemetry events")

@storage_router.get("/health", response_model=Dict[str, Any])
async def get_storage_health() -> Dict[str, Any]:
    """
    Get storage system health metrics.
    READ-ONLY endpoint for storage monitoring.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            return {
                "status": "unavailable",
                "error": "Storage service not initialized"
            }
        
        health = await storage.get_storage_health()
        
        return {
            "status": "healthy",
            "storage_health": health,
            "database_connected": storage._db_available,
            "background_worker_running": health["worker_running"],
            "retention_policies": health["retention_policies"],
            "last_cleanup": health["time_since_cleanup_seconds"]
        }
        
    except Exception as e:
        logger.error("Failed to get storage health", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve storage health")

@storage_router.get("/stats", response_model=Dict[str, Any])
async def get_storage_statistics() -> Dict[str, Any]:
    """
    Get storage statistics and usage metrics.
    READ-ONLY endpoint for analytics.
    """
    try:
        storage = get_execution_storage()
        
        if not storage:
            raise HTTPException(status_code=503, detail="Storage service unavailable")
        
        # Get basic statistics (would need to implement count queries)
        stats = {
            "total_benchmarks": 0,
            "total_executions": 0,
            "total_cloud_tasks": 0,
            "total_telemetry_events": 0,
            "storage_health": await storage.get_storage_health()
        }
        
        return {
            "statistics": stats,
            "retention_info": {
                "telemetry_events_days": 30,
                "cloud_tasks_days": 90,
                "benchmark_runs_days": 365
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get storage statistics", error=str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve storage statistics")
