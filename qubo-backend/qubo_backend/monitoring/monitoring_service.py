"""
Qurve AI - Production Monitoring Service
Operational observability layer for quantum execution platform.

Purpose: READ telemetry, NOT control execution.
This service aggregates metrics and provides operational summaries
without interfering with solver architecture.
"""

import asyncio
import time
import threading
from collections import deque, defaultdict
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from ..telemetry.structured_telemetry import get_benchmark_telemetry, get_telemetry_state

logger = logging.getLogger(__name__)


class SystemHealth(Enum):
    """System health states derived from operational metrics."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNSTABLE = "unstable"
    CRITICAL = "critical"


@dataclass
class SystemMetrics:
    """System-level operational metrics."""
    active_executions: int = 0
    queued_cloud_tasks: int = 0
    avg_execution_latency_ms: float = 0.0
    execution_throughput_per_min: float = 0.0
    fallback_frequency: float = 0.0  # percentage
    timeout_count: int = 0
    failure_rate: float = 0.0  # percentage
    retry_rate: float = 0.0  # percentage


@dataclass
class SolverMetrics:
    """Per-solver operational metrics."""
    solver_name: str
    success_count: int = 0
    failure_count: int = 0
    avg_latency_ms: float = 0.0
    fallback_count: int = 0
    feasibility_rate: float = 0.0  # percentage
    cloud_usage_count: int = 0
    local_usage_count: int = 0
    status: str = "unknown"


@dataclass
class CloudMetrics:
    """Cloud-specific operational metrics."""
    active_aws_tasks: int = 0
    cloud_queue_latency_ms: float = 0.0
    cloud_execution_latency_ms: float = 0.0
    aws_region_usage: Dict[str, int] = field(default_factory=dict)
    task_state_distribution: Dict[str, int] = field(default_factory=dict)
    estimated_cloud_cost: float = 0.0


@dataclass
class ExecutionEvent:
    """Runtime execution event for monitoring."""
    timestamp: float
    event_type: str  # started, completed, failed, timeout, fallback
    solver: str
    execution_mode: str
    correlation_id: str
    latency_ms: Optional[float] = None
    cloud_task_arn: Optional[str] = None
    error_message: Optional[str] = None


class MonitoringService:
    """
    Production monitoring service for operational observability.
    
    READ-ONLY telemetry aggregation with bounded memory usage.
    Never interferes with execution flows.
    """
    
    def __init__(self, max_events: int = 5000):
        self.max_events = max_events
        self.events_buffer = deque(maxlen=max_events)
        self._lock = threading.RLock()
        
        # Metrics storage
        self.system_metrics = SystemMetrics()
        self.solver_metrics: Dict[str, SolverMetrics] = {}
        self.cloud_metrics = CloudMetrics()
        
        # Telemetry integration
        self.telemetry = get_benchmark_telemetry()
        
        # Runtime state
        self._last_update = time.time()
        self._update_interval = 30.0  # seconds
        
        logger.info(f"Monitoring service initialized with max_events={max_events}, update_interval={self._update_interval}")
    
    def add_execution_event(self, event: ExecutionEvent) -> None:
        """
        Add execution event to monitoring buffer.
        Thread-safe and bounded by maxlen.
        """
        with self._lock:
            self.events_buffer.append(event)
            self._update_realtime_metrics(event)
    
    def _update_realtime_metrics(self, event: ExecutionEvent) -> None:
        """Update metrics in real-time as events arrive."""
        # Update solver metrics
        if event.solver not in self.solver_metrics:
            self.solver_metrics[event.solver] = SolverMetrics(solver_name=event.solver)
        
        solver_metric = self.solver_metrics[event.solver]
        
        if event.event_type == "completed":
            solver_metric.success_count += 1
            if event.latency_ms:
                solver_metric.avg_latency_ms = (
                    (solver_metric.avg_latency_ms * (solver_metric.success_count - 1) + event.latency_ms) /
                    solver_metric.success_count
                )
            solver_metric.status = "healthy"
            
            # Track cloud vs local usage
            if event.execution_mode == "cloud_simulator":
                solver_metric.cloud_usage_count += 1
            else:
                solver_metric.local_usage_count += 1
                
        elif event.event_type == "failed":
            solver_metric.failure_count += 1
            solver_metric.status = "degraded"
        elif event.event_type == "fallback":
            solver_metric.fallback_count += 1
            solver_metric.status = "degraded"
        elif event.event_type == "timeout":
            self.system_metrics.timeout_count += 1
            solver_metric.status = "unstable"
        
        # Update system metrics
        if event.event_type == "started":
            self.system_metrics.active_executions += 1
        elif event.event_type in ["completed", "failed", "timeout"]:
            self.system_metrics.active_executions = max(0, self.system_metrics.active_executions - 1)
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        with self._lock:
            self._calculate_derived_metrics()
            return self.system_metrics
    
    def get_solver_metrics(self) -> Dict[str, SolverMetrics]:
        """Get per-solver metrics."""
        with self._lock:
            self._calculate_derived_metrics()
            return dict(self.solver_metrics)
    
    def get_cloud_metrics(self) -> CloudMetrics:
        """Get cloud-specific metrics."""
        with self._lock:
            self._update_cloud_metrics()
            return self.cloud_metrics
    
    def get_recent_events(self, limit: int = 100) -> List[ExecutionEvent]:
        """Get recent execution events."""
        with self._lock:
            events = list(self.events_buffer)
            return events[-limit:] if limit > 0 else events
    
    def get_system_health(self) -> SystemHealth:
        """
        Derive system health from operational metrics.
        
        Health determination logic:
        - HEALTHY: <5% failure rate, <2% timeout rate, <10% fallback rate
        - DEGRADED: 5-15% failure rate OR 2-5% timeout rate OR 10-20% fallback rate
        - UNSTABLE: 15-30% failure rate OR 5-10% timeout rate OR 20-40% fallback rate
        - CRITICAL: >30% failure rate OR >10% timeout rate OR >40% fallback rate
        """
        with self._lock:
            self._calculate_derived_metrics()
            
            failure_rate = self.system_metrics.failure_rate
            timeout_rate = self._calculate_timeout_rate()
            fallback_rate = self.system_metrics.fallback_frequency
            
            # Determine health state
            if (failure_rate < 5.0 and timeout_rate < 2.0 and fallback_rate < 10.0):
                return SystemHealth.HEALTHY
            elif (failure_rate < 15.0 and timeout_rate < 5.0 and fallback_rate < 20.0):
                return SystemHealth.DEGRADED
            elif (failure_rate < 30.0 and timeout_rate < 10.0 and fallback_rate < 40.0):
                return SystemHealth.UNSTABLE
            else:
                return SystemHealth.CRITICAL
    
    def _calculate_derived_metrics(self) -> None:
        """Calculate derived metrics from event buffer."""
        if not self.events_buffer:
            return
        
        now = time.time()
        recent_events = [e for e in self.events_buffer if now - e.timestamp < 300]  # Last 5 minutes
        
        if not recent_events:
            return
        
        # Calculate failure rate
        total_executions = len([e for e in recent_events if e.event_type in ["completed", "failed"]])
        failed_executions = len([e for e in recent_events if e.event_type == "failed"])
        
        if total_executions > 0:
            self.system_metrics.failure_rate = (failed_executions / total_executions) * 100
        
        # Calculate fallback frequency
        total_cloud_attempts = len([e for e in recent_events if e.execution_mode.startswith("cloud")])
        fallback_events = len([e for e in recent_events if e.event_type == "fallback"])
        
        if total_cloud_attempts > 0:
            self.system_metrics.fallback_frequency = (fallback_events / total_cloud_attempts) * 100
        
        # Calculate average execution latency
        completed_events = [e for e in recent_events if e.event_type == "completed" and e.latency_ms]
        if completed_events:
            self.system_metrics.avg_execution_latency_ms = sum(e.latency_ms for e in completed_events) / len(completed_events)
        
        # Calculate throughput (executions per minute)
        self.system_metrics.execution_throughput_per_min = len(recent_events) / 5.0
    
    def _calculate_timeout_rate(self) -> float:
        """Calculate timeout rate as percentage."""
        now = time.time()
        recent_events = [e for e in self.events_buffer if now - e.timestamp < 300]
        
        total_executions = len([e for e in recent_events if e.event_type in ["completed", "failed", "timeout"]])
        timeout_events = len([e for e in recent_events if e.event_type == "timeout"])
        
        return (timeout_events / total_executions * 100) if total_executions > 0 else 0.0
    
    def _update_cloud_metrics(self) -> None:
        """Update cloud-specific metrics from telemetry state."""
        try:
            # Simple cloud availability check
            availability = {"available": True, "region": "us-east-1"}
            
            # Update cloud metrics based on recent cloud events
            now = time.time()
            recent_cloud_events = [
                e for e in self.events_buffer 
                if e.execution_mode.startswith("cloud") and now - e.timestamp < 300
            ]
            
            # Count active cloud tasks (recently started, not completed)
            started_tasks = len([e for e in recent_cloud_events if e.event_type == "started"])
            completed_tasks = len([e for e in recent_cloud_events if e.event_type == "completed"])
            self.cloud_metrics.active_aws_tasks = started_tasks - completed_tasks
            
            # Calculate cloud latencies
            cloud_completed = [
                e for e in recent_cloud_events 
                if e.event_type == "completed" and e.latency_ms
            ]
            if cloud_completed:
                total_latency = sum(e.latency_ms for e in cloud_completed)
                self.cloud_metrics.cloud_execution_latency_ms = total_latency / len(cloud_completed)
            
            # Update region usage
            self.cloud_metrics.aws_region_usage = availability.get("supported_regions", {})
            
            # Update task state distribution
            self.cloud_metrics.task_state_distribution = {
                "QUEUED": len([e for e in recent_cloud_events if "queued" in str(e.error_message).lower()]),
                "RUNNING": len([e for e in recent_cloud_events if e.event_type == "started"]),
                "COMPLETED": len([e for e in recent_cloud_events if e.event_type == "completed"]),
                "FAILED": len([e for e in recent_cloud_events if e.event_type == "failed"])
            }
            
        except Exception as e:
            logger.error("Failed to update cloud metrics", error=str(e))
    
    def get_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics."""
        with self._lock:
            return {
                "events_buffer_size": len(self.events_buffer),
                "events_buffer_max": self.max_events,
                "solver_metrics_count": len(self.solver_metrics),
                "estimated_memory_mb": (
                    len(self.events_buffer) * 200 +  # ~200 bytes per event
                    len(self.solver_metrics) * 100     # ~100 bytes per solver metric
                ) / (1024 * 1024)
            }
    
    def start_background_updates(self) -> None:
        """Start background thread for periodic metric updates."""
        def update_loop():
            while True:
                try:
                    time.sleep(self._update_interval)
                    self._calculate_derived_metrics()
                except Exception as e:
                    logger.error("Background update failed", error=str(e))
        
        thread = threading.Thread(target=update_loop, daemon=True)
        thread.start()
        logger.info("Background monitoring updates started")


# Global monitoring service instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get the global monitoring service instance."""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
        _monitoring_service.start_background_updates()
    return _monitoring_service


def create_execution_event(
    event_type: str,
    solver: str,
    execution_mode: str,
    correlation_id: str,
    latency_ms: Optional[float] = None,
    cloud_task_arn: Optional[str] = None,
    error_message: Optional[str] = None
) -> ExecutionEvent:
    """Create an execution event for monitoring."""
    return ExecutionEvent(
        timestamp=time.time(),
        event_type=event_type,
        solver=solver,
        execution_mode=execution_mode,
        correlation_id=correlation_id,
        latency_ms=latency_ms,
        cloud_task_arn=cloud_task_arn,
        error_message=error_message
    )
