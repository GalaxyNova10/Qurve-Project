"""
Qurve AI - Production Health Endpoints
Enterprise-grade health checks for production monitoring
"""

import asyncio
import psutil
import time
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..telemetry import get_structured_logger, get_benchmark_event_tracker
from ..tasks import get_benchmark_queue, get_async_runner

router = APIRouter(prefix="/health", tags=["health"])

logger = get_structured_logger(__name__)


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    environment: str
    uptime_seconds: float
    checks: Dict[str, Any]


class LivenessResponse(BaseModel):
    """Liveness check response model."""
    status: str
    timestamp: str
    alive: bool


class ReadinessResponse(BaseModel):
    """Readiness check response model."""
    status: str
    timestamp: str
    ready: bool
    checks: Dict[str, Any]


class TelemetryHealthResponse(BaseModel):
    """Telemetry health check response model."""
    status: str
    timestamp: str
    telemetry_operational: bool
    event_count: int
    correlation_count: int
    checks: Dict[str, Any]


class QueueHealthResponse(BaseModel):
    """Queue health check response model."""
    status: str
    timestamp: str
    queue_operational: bool
    queue_stats: Dict[str, Any]
    checks: Dict[str, Any]


class SolversHealthResponse(BaseModel):
    """Solvers health check response model."""
    status: str
    timestamp: str
    solvers_status: Dict[str, Any]
    checks: Dict[str, Any]


# Application startup time
START_TIME = time.time()


@router.get("/live", response_model=LivenessResponse)
async def liveness_check():
    """
    Liveness check - indicates if the service is alive.
    
    This endpoint should return 200 if the service is alive,
    regardless of its readiness to serve traffic.
    """
    try:
        return LivenessResponse(
            status="healthy",
            timestamp=datetime.now(timezone.utc).isoformat(),
            alive=True
        )
    except Exception as e:
        logger.error(msg="Liveness check failed", error=str(e))
        raise HTTPException(status_code=503, detail="Service not alive")


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check():
    """
    Readiness check - indicates if the service is ready to serve traffic.
    
    This endpoint should return 200 only if the service is ready
    to serve traffic (all dependencies are available).
    """
    checks = {}
    all_ready = True
    
    # Check telemetry system
    try:
        event_tracker = get_benchmark_event_tracker()
        events = event_tracker.get_events()
        checks["telemetry"] = {
            "status": "healthy",
            "event_count": len(events),
            "message": "Telemetry system operational"
        }
    except Exception as e:
        all_ready = False
        checks["telemetry"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Telemetry system not operational"
        }
    
    # Check queue system
    try:
        queue = get_benchmark_queue()
        stats = queue.get_queue_stats()
        checks["queue"] = {
            "status": "healthy",
            "pending_tasks": stats.pending_tasks,
            "running_tasks": stats.running_tasks,
            "message": "Queue system operational"
        }
    except Exception as e:
        all_ready = False
        checks["queue"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Queue system not operational"
        }
    
    # Check async runner
    try:
        async_runner = get_async_runner()
        checks["async_runner"] = {
            "status": "healthy",
            "message": "Async runner operational"
        }
    except Exception as e:
        all_ready = False
        checks["async_runner"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Async runner not operational"
        }
    
    status = "ready" if all_ready else "not_ready"
    
    return ReadinessResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        ready=all_ready,
        checks=checks
    )


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Comprehensive health check - indicates overall system health.
    
    This endpoint provides detailed health information about all
    system components and their current status.
    """
    uptime = time.time() - START_TIME
    
    checks = {}
    overall_healthy = True
    
    # System resources check
    try:
        memory = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=1)
        
        checks["system"] = {
            "status": "healthy",
            "memory_usage_percent": memory.percent,
            "cpu_usage_percent": cpu,
            "available_memory_gb": memory.available / (1024**3),
            "message": "System resources within limits"
        }
        
        # Check for resource issues
        if memory.percent > 90:
            overall_healthy = False
            checks["system"]["status"] = "warning"
            checks["system"]["message"] = "High memory usage"
        
        if cpu > 80:
            overall_healthy = False
            checks["system"]["status"] = "warning"
            checks["system"]["message"] = "High CPU usage"
            
    except Exception as e:
        overall_healthy = False
        checks["system"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "System monitoring not available"
        }
    
    # Telemetry check
    try:
        event_tracker = get_benchmark_event_tracker()
        events = event_tracker.get_events()
        checks["telemetry"] = {
            "status": "healthy",
            "event_count": len(events),
            "message": "Telemetry system operational"
        }
    except Exception as e:
        overall_healthy = False
        checks["telemetry"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Telemetry system not operational"
        }
    
    # Queue check
    try:
        queue = get_benchmark_queue()
        stats = queue.get_queue_stats()
        checks["queue"] = {
            "status": "healthy",
            "pending_tasks": stats.pending_tasks,
            "running_tasks": stats.running_tasks,
            "completed_tasks": stats.completed_tasks,
            "message": "Queue system operational"
        }
    except Exception as e:
        overall_healthy = False
        checks["queue"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Queue system not operational"
        }
    
    # Async runner check
    try:
        async_runner = get_async_runner()
        perf_stats = async_runner.get_performance_stats()
        checks["async_runner"] = {
            "status": "healthy",
            "performance_stats": perf_stats,
            "message": "Async runner operational"
        }
    except Exception as e:
        overall_healthy = False
        checks["async_runner"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Async runner not operational"
        }
    
    status = "healthy" if overall_healthy else "unhealthy"
    
    return HealthResponse(
        status=status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        version="1.0.0",
        environment="production",
        uptime_seconds=uptime,
        checks=checks
    )


@router.get("/health/telemetry", response_model=TelemetryHealthResponse)
async def telemetry_health():
    """Detailed telemetry health check."""
    checks = {}
    telemetry_operational = True
    
    # Check event tracker
    try:
        event_tracker = get_benchmark_event_tracker()
        events = event_tracker.get_events()
        perf_summary = event_tracker.get_performance_summary()
        fallback_analysis = event_tracker.get_fallback_analysis()
        
        checks["event_tracker"] = {
            "status": "healthy",
            "total_events": len(events),
            "performance_summary_available": perf_summary is not None,
            "fallback_analysis_available": fallback_analysis is not None,
            "message": "Event tracker operational"
        }
        
    except Exception as e:
        telemetry_operational = False
        checks["event_tracker"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Event tracker not operational"
        }
    
    # Check correlation management
    try:
        from ..telemetry import get_correlation_id, get_benchmark_session_id
        correlation_id = get_correlation_id()
        session_id = get_benchmark_session_id()
        
        checks["correlation_management"] = {
            "status": "healthy",
            "correlation_id_available": correlation_id is not None,
            "session_id_available": session_id is not None,
            "message": "Correlation management operational"
        }
        
    except Exception as e:
        telemetry_operational = False
        checks["correlation_management"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Correlation management not operational"
        }
    
    # Check structured logger
    try:
        structured_logger = get_structured_logger("health_check")
        
        checks["structured_logger"] = {
            "status": "healthy",
            "logger_available": structured_logger is not None,
            "message": "Structured logger operational"
        }
        
    except Exception as e:
        telemetry_operational = False
        checks["structured_logger"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Structured logger not operational"
        }
    
    # Get event count
    event_tracker = get_benchmark_event_tracker()
    events = event_tracker.get_events()
    
    return TelemetryHealthResponse(
        status="healthy" if telemetry_operational else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        telemetry_operational=telemetry_operational,
        event_count=len(events),
        correlation_count=len(set(e.correlation_id for e in events if e.correlation_id)),
        checks=checks
    )


@router.get("/health/queue", response_model=QueueHealthResponse)
async def queue_health():
    """Detailed queue health check."""
    checks = {}
    queue_operational = True
    
    try:
        queue = get_benchmark_queue()
        stats = queue.get_queue_stats()
        
        # Check queue health indicators
        queue_health = "healthy"
        health_message = "Queue system operational"
        
        # Check for queue overload
        if stats.pending_tasks > 80:
            queue_health = "warning"
            health_message = "Queue approaching capacity"
        
        if stats.pending_tasks >= 100:
            queue_health = "unhealthy"
            health_message = "Queue at maximum capacity"
        
        # Check for worker exhaustion
        if stats.running_tasks >= 3:
            queue_health = "warning"
            health_message = "High worker utilization"
        
        checks["queue_stats"] = {
            "status": queue_health,
            "pending_tasks": stats.pending_tasks,
            "running_tasks": stats.running_tasks,
            "completed_tasks": stats.completed_tasks,
            "failed_tasks": stats.failed_tasks,
            "avg_execution_time_ms": stats.avg_execution_time_ms,
            "message": health_message
        }
        
        # Check queue capacity
        checks["capacity"] = {
            "status": "healthy" if stats.pending_tasks < 90 else "warning",
            "utilization_percent": (stats.pending_tasks / 100) * 100,
            "max_capacity": 100,
            "message": "Queue capacity within limits"
        }
        
        # Check worker pool
        try:
            from ..tasks import get_worker_pool
            worker_pool = get_worker_pool()
            worker_stats = worker_pool.get_stats()
            
            checks["worker_pool"] = {
                "status": "healthy",
                "active_workers": worker_stats.active_workers,
                "total_tasks": worker_stats.total_tasks,
                "completed_tasks": worker_stats.completed_tasks,
                "failed_tasks": worker_stats.failed_tasks,
                "message": "Worker pool operational"
            }
            
        except Exception as e:
            queue_operational = False
            checks["worker_pool"] = {
                "status": "unhealthy",
                "error": str(e),
                "message": "Worker pool not operational"
            }
        
    except Exception as e:
        queue_operational = False
        checks["queue"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Queue system not operational"
        }
    
    return QueueHealthResponse(
        status="healthy" if queue_operational else "unhealthy",
        timestamp=datetime.now(timezone.utc).isoformat(),
        queue_operational=queue_operational,
        queue_stats=stats if 'stats' in locals() else {},
        checks=checks
    )


@router.get("/health/solvers", response_model=SolversHealthResponse)
async def solvers_health():
    """Detailed solvers health check."""
    checks = {}
    solvers_status = {}
    
    # Check Neal SA solver
    try:
        from ..optimization.neal_solver import NealSAOptimizer
        neal_solver = NealSAOptimizer()
        
        # Test Neal solver availability
        neal_available = True
        neal_message = "Neal SA solver operational"
        
        solvers_status["neal_sa"] = {
            "status": "healthy",
            "available": neal_available,
            "message": neal_message
        }
        
    except Exception as e:
        solvers_status["neal_sa"] = {
            "status": "unhealthy",
            "available": False,
            "error": str(e),
            "message": "Neal SA solver not operational"
        }
    
    # Check Qiskit solver
    try:
        from ..optimization.qiskit_solver import QiskitQAOAOptimizer
        qiskit_solver = QiskitQAOAOptimizer()
        
        qiskit_available = True
        qiskit_message = "Qiskit QAOA solver operational"
        
        solvers_status["qiskit_qaoa"] = {
            "status": "healthy",
            "available": qiskit_available,
            "message": qiskit_message
        }
        
    except Exception as e:
        solvers_status["qiskit_qaoa"] = {
            "status": "unhealthy",
            "available": False,
            "error": str(e),
            "message": "Qiskit QAOA solver not operational"
        }
    
    # Check Braket solver
    try:
        from ..optimization.braket_adapter import get_braket_adapter
        braket_adapter = get_braket_adapter()
        status = braket_adapter.check_availability()
        
        braket_available = status.available
        braket_message = "Braket LocalSimulator operational" if braket_available else "Braket LocalSimulator not available"
        
        solvers_status["braket_local"] = {
            "status": "healthy" if braket_available else "warning",
            "available": braket_available,
            "pydantic_compatible": status.pydantic_compatible,
            "simulator_available": status.simulator_available,
            "message": braket_message
        }
        
        if status.error:
            solvers_status["braket_local"]["error"] = status.error
        
    except Exception as e:
        solvers_status["braket_local"] = {
            "status": "unhealthy",
            "available": False,
            "error": str(e),
            "message": "Braket LocalSimulator not operational"
        }
    
    # Calculate overall solver health
    healthy_solvers = sum(1 for s in solvers_status.values() if s["status"] == "healthy")
    total_solvers = len(solvers_status)
    solver_health = healthy_solvers / total_solvers if total_solvers > 0 else 0
    
    overall_status = "healthy" if solver_health >= 0.8 else "degraded" if solver_health >= 0.5 else "unhealthy"
    
    return SolversHealthResponse(
        status=overall_status,
        timestamp=datetime.now(timezone.utc).isoformat(),
        solvers_status=solvers_status,
        checks={
            "healthy_solvers": healthy_solvers,
            "total_solvers": total_solvers,
            "health_percentage": solver_health * 100
        }
    )
