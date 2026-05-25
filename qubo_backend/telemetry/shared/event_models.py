"""
Qurve AI - Shared Event Models
Zero-dependency event models for telemetry system
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from enum import Enum


class EventType(str, Enum):
    """Standard event types for telemetry."""
    TASK_START = "TASK_START"
    TASK_SUCCESS = "TASK_SUCCESS"
    TASK_FAILURE = "TASK_FAILURE"
    TASK_TIMEOUT = "TASK_TIMEOUT"
    TASK_CANCELLED = "TASK_CANCELLED"
    
    BENCHMARK_START = "BENCHMARK_START"
    BENCHMARK_COMPLETE = "BENCHMARK_COMPLETE"
    BENCHMARK_FAILED = "BENCHMARK_FAILED"
    BENCHMARK_TIMEOUT = "BENCHMARK_TIMEOUT"
    
    QUEUE_ENQUEUED = "QUEUE_ENQUEUED"
    QUEUE_DEQUEUED = "QUEUE_DEQUEUED"
    QUEUE_FULL = "QUEUE_FULL"
    QUEUE_EMPTY = "QUEUE_EMPTY"
    
    WORKER_ASSIGNED = "WORKER_ASSIGNED"
    WORKER_RELEASED = "WORKER_RELEASED"
    WORKER_EXHAUSTED = "WORKER_EXHAUSTED"
    
    SYSTEM_STARTUP = "SYSTEM_STARTUP"
    SYSTEM_SHUTDOWN = "SYSTEM_SHUTDOWN"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    
    SOLVER_START = "SOLVER_START"
    SOLVER_SUCCESS = "SOLVER_SUCCESS"
    SOLVER_FAILURE = "SOLVER_FAILURE"
    SOLVER_TIMEOUT = "SOLVER_TIMEOUT"
    
    FALLBACK_TRIGGERED = "FALLBACK_TRIGGERED"
    FALLBACK_SUCCESS = "FALLBACK_SUCCESS"
    FALLBACK_FAILURE = "FALLBACK_FAILURE"


class ComponentType(str, Enum):
    """Component types for telemetry."""
    API = "api"
    QUEUE = "queue"
    WORKER = "worker"
    SOLVER = "solver"
    TELEMETRY = "telemetry"
    SYSTEM = "system"
    FRONTEND = "frontend"


class StatusType(str, Enum):
    """Status types for telemetry."""
    SUCCESS = "success"
    FAILURE = "failure"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class BaseEvent:
    """Base event model with all required telemetry fields."""
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    correlation_id: Optional[str] = None
    benchmark_session_id: Optional[str] = None
    event_type: EventType = EventType.SYSTEM_STARTUP
    component: ComponentType = ComponentType.SYSTEM
    status: StatusType = StatusType.SUCCESS
    duration_ms: Optional[float] = None
    thread_id: Optional[str] = None
    worker_id: Optional[str] = None
    queue_depth: Optional[int] = None
    solver: Optional[str] = None
    provider: Optional[str] = None
    backend: Optional[str] = None
    fallback_reason: Optional[str] = None
    memory_usage_mb: Optional[float] = None
    cpu_usage_percent: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "benchmark_session_id": self.benchmark_session_id,
            "event_type": self.event_type.value,
            "component": self.component.value,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "thread_id": self.thread_id,
            "worker_id": self.worker_id,
            "queue_depth": self.queue_depth,
            "solver": self.solver,
            "provider": self.provider,
            "backend": self.backend,
            "fallback_reason": self.fallback_reason,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "metadata": self.metadata
        }


@dataclass
class BenchmarkEvent(BaseEvent):
    """Benchmark-specific event model."""
    benchmark_id: Optional[str] = None
    num_solvers: Optional[int] = None
    problem_size: Optional[int] = None
    successful_solvers: Optional[int] = None
    total_solvers: Optional[int] = None
    
    def __post_init__(self):
        """Set component type to system for benchmark events."""
        self.component = ComponentType.SYSTEM


@dataclass
class TaskEvent(BaseEvent):
    """Task-specific event model."""
    task_id: Optional[str] = None
    task_type: Optional[str] = None
    priority: Optional[str] = None
    timeout_seconds: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    
    def __post_init__(self):
        """Set component type to worker for task events."""
        self.component = ComponentType.WORKER


@dataclass
class WorkerEvent(BaseEvent):
    """Worker-specific event model."""
    worker_pool_size: Optional[int] = None
    active_workers: Optional[int] = None
    queued_tasks: Optional[int] = None
    completed_tasks: Optional[int] = None
    failed_tasks: Optional[int] = None
    avg_task_duration_ms: Optional[float] = None
    
    def __post_init__(self):
        """Set component type to worker for worker events."""
        self.component = ComponentType.WORKER


@dataclass
class QueueEvent(BaseEvent):
    """Queue-specific event model."""
    queue_size: Optional[int] = None
    max_queue_size: Optional[int] = None
    wait_time_ms: Optional[float] = None
    priority: Optional[str] = None
    
    def __post_init__(self):
        """Set component type to queue for queue events."""
        self.component = ComponentType.QUEUE


@dataclass
class SystemEvent(BaseEvent):
    """System-specific event model."""
    system_version: Optional[str] = None
    python_version: Optional[str] = None
    environment: Optional[str] = None
    startup_time_ms: Optional[float] = None
    shutdown_time_ms: Optional[float] = None
    
    def __post_init__(self):
        """Set component type to system for system events."""
        self.component = ComponentType.SYSTEM


@dataclass
class SolverEvent(BaseEvent):
    """Solver-specific event model."""
    solver_name: Optional[str] = None
    solver_version: Optional[str] = None
    solver_config: Optional[Dict[str, Any]] = None
    execution_time_ms: Optional[float] = None
    energy: Optional[float] = None
    solution_quality: Optional[float] = None
    
    def __post_init__(self):
        """Set component type to solver for solver events."""
        self.component = ComponentType.SOLVER
        if self.solver_name:
            self.solver = self.solver_name
