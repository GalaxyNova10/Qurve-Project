"""
Qurve AI - Shared Context Models
Zero-dependency context models for telemetry system
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone


@dataclass
class TelemetryContext:
    """Base telemetry context with minimal dependencies."""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    benchmark_session_id: Optional[str] = None
    thread_id: Optional[str] = None
    process_id: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "benchmark_session_id": self.benchmark_session_id,
            "thread_id": self.thread_id,
            "process_id": self.process_id
        }


@dataclass
class CorrelationContext:
    """Context for correlation tracking."""
    correlation_id: Optional[str] = None
    benchmark_session_id: Optional[str] = None
    trace_id: Optional[str] = None
    parent_span_id: Optional[str] = None
    span_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert correlation context to dictionary."""
        return {
            "correlation_id": self.correlation_id,
            "benchmark_session_id": self.benchmark_session_id,
            "trace_id": self.trace_id,
            "parent_span_id": self.parent_span_id,
            "span_id": self.span_id
        }


@dataclass
class BenchmarkContext:
    """Context for benchmark execution."""
    benchmark_id: Optional[str] = None
    solver_name: Optional[str] = None
    provider: Optional[str] = None
    backend: Optional[str] = None
    problem_size: Optional[int] = None
    num_solvers: Optional[int] = None
    cardinality: Optional[int] = None
    risk_tolerance: Optional[float] = None
    trajectories: Optional[int] = None
    time_limit_seconds: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert benchmark context to dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "solver_name": self.solver_name,
            "provider": self.provider,
            "backend": self.backend,
            "problem_size": self.problem_size,
            "num_solvers": self.num_solvers,
            "cardinality": self.cardinality,
            "risk_tolerance": self.risk_tolerance,
            "trajectories": self.trajectories,
            "time_limit_seconds": self.time_limit_seconds
        }


@dataclass
class ExecutionContext:
    """Context for execution tracking."""
    task_id: Optional[str] = None
    worker_id: Optional[str] = None
    queue_depth: Optional[int] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_ms: Optional[float] = None
    timeout_seconds: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert execution context to dictionary."""
        return {
            "task_id": self.task_id,
            "worker_id": self.worker_id,
            "queue_depth": self.queue_depth,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "timeout_seconds": self.timeout_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent
        }


@dataclass
class SystemContext:
    """Context for system-level tracking."""
    system_version: Optional[str] = None
    python_version: Optional[str] = None
    environment: Optional[str] = None
    hostname: Optional[str] = None
    region: Optional[str] = None
    availability_zone: Optional[str] = None
    instance_type: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert system context to dictionary."""
        return {
            "system_version": self.system_version,
            "python_version": self.python_version,
            "environment": self.environment,
            "hostname": self.hostname,
            "region": self.region,
            "availability_zone": self.availability_zone,
            "instance_type": self.instance_type
        }


@dataclass
class ErrorContext:
    """Context for error tracking."""
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None
    error_code: Optional[str] = None
    retry_count: Optional[int] = None
    last_retry_time: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert error context to dictionary."""
        return {
            "error_type": self.error_type,
            "error_message": self.error_message,
            "stack_trace": self.stack_trace,
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "last_retry_time": self.last_retry_time
        }


@dataclass
class PerformanceContext:
    """Context for performance tracking."""
    latency_ms: Optional[float] = None
    throughput_qps: Optional[float] = None
    p95_latency_ms: Optional[float] = None
    p99_latency_ms: Optional[float] = None
    error_rate: Optional[float] = None
    success_rate: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert performance context to dictionary."""
        return {
            "latency_ms": self.latency_ms,
            "throughput_qps": self.throughput_qps,
            "p95_latency_ms": self.p95_latency_ms,
            "p99_latency_ms": self.p99_latency_ms,
            "error_rate": self.error_rate,
            "success_rate": self.success_rate
        }
