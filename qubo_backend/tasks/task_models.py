"""
Qurve AI - Task Models
Enterprise-grade task definitions and status tracking
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """Task execution status for enterprise tracking."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority levels for enterprise scheduling."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class TaskResult:
    """
    Enterprise-grade task result with comprehensive metadata.
    
    Contains:
    - Task execution status and timing
    - Result data or error information
    - Performance metrics
    - Correlation and session tracking
    """
    task_id: str
    status: TaskStatus
    result: Optional[Any] = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    worker_id: Optional[str] = None
    correlation_id: Optional[str] = None
    benchmark_session_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_success(self) -> bool:
        """Check if task completed successfully."""
        return self.status == TaskStatus.COMPLETED and self.error is None
    
    def is_failure(self) -> bool:
        """Check if task failed."""
        return self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED]
    
    def is_finished(self) -> bool:
        """Check if task is finished (success or failure)."""
        return self.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.TIMEOUT, TaskStatus.CANCELLED]


@dataclass
class Task:
    """
    Enterprise-grade task definition with comprehensive metadata.
    
    Supports:
    - Solver execution tasks
    - Benchmark orchestration tasks
    - System maintenance tasks
    - Resource monitoring tasks
    """
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    task_type: str = ""
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    func: Optional[callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    timeout_seconds: Optional[float] = None
    max_retries: int = 0
    retry_count: int = 0
    correlation_id: Optional[str] = None
    benchmark_session_id: Optional[str] = None
    solver_name: Optional[str] = None
    provider: Optional[str] = None
    backend: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        if not self.task_id:
            self.task_id = str(uuid.uuid4())
        
        # Auto-set correlation and session IDs if not provided
        from ..telemetry.correlation import get_correlation_id, get_benchmark_session_id
        
        if not self.correlation_id:
            self.correlation_id = get_correlation_id()
        
        if not self.benchmark_session_id:
            self.benchmark_session_id = get_benchmark_session_id()
    
    def create_result(self, status: TaskStatus, result: Any = None, error: str = None) -> TaskResult:
        """Create task result with timing and metadata."""
        completed_at = time.time()
        duration_ms = None
        
        if self.created_at:
            duration_ms = (completed_at - self.created_at) * 1000
        
        return TaskResult(
            task_id=self.task_id,
            status=status,
            result=result,
            error=error,
            duration_ms=duration_ms,
            created_at=self.created_at,
            started_at=getattr(self, 'started_at', None),
            completed_at=completed_at,
            worker_id=getattr(self, 'worker_id', None),
            correlation_id=self.correlation_id,
            benchmark_session_id=self.benchmark_session_id,
            solver_name=self.solver_name,
            provider=self.provider,
            backend=self.backend,
            metadata=self.metadata
        )
    
    def mark_running(self, worker_id: str = None):
        """Mark task as running."""
        self.status = TaskStatus.RUNNING
        self.started_at = time.time()
        self.worker_id = worker_id
    
    def mark_completed(self, result: Any):
        """Mark task as completed with result."""
        self.status = TaskStatus.COMPLETED
        self.result = result
        self.error = None
    
    def mark_failed(self, error: str):
        """Mark task as failed with error."""
        self.status = TaskStatus.FAILED
        self.error = error
        self.result = None
    
    def mark_cancelled(self):
        """Mark task as cancelled."""
        self.status = TaskStatus.CANCELLED
        self.error = "Task cancelled"
        self.result = None
    
    def mark_timeout(self):
        """Mark task as timed out."""
        self.status = TaskStatus.TIMEOUT
        self.error = f"Task timed out after {self.timeout_seconds} seconds"
        self.result = None
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return (
            self.retry_count < self.max_retries and
            self.status in [TaskStatus.FAILED, TaskStatus.TIMEOUT]
        )
    
    def create_retry(self) -> 'Task':
        """Create retry task with incremented retry count."""
        retry_task = Task(
            task_type=self.task_type,
            priority=self.priority,
            func=self.func,
            args=self.args,
            kwargs=self.kwargs,
            timeout_seconds=self.timeout_seconds,
            max_retries=self.max_retries,
            retry_count=self.retry_count + 1,
            correlation_id=self.correlation_id,
            benchmark_session_id=self.benchmark_session_id,
            solver_name=self.solver_name,
            provider=self.provider,
            backend=self.backend,
            metadata=self.metadata.copy()
        )
        
        return retry_task


@dataclass
class BenchmarkTask(Task):
    """
    Specialized task for benchmark execution.
    
    Extends Task with benchmark-specific fields:
    - Solver configuration
    - Problem size tracking
    - Performance expectations
    """
    solver_name: str = ""
    provider: str = ""
    backend: str = ""
    num_assets: int = 0
    binary_bits: int = 0
    cardinality: int = 0
    risk_tolerance: float = 0.5
    max_sector_exposure: float = 0.3
    trajectories: int = 10
    time_limit_seconds: int = 30
    
    def __post_init__(self):
        """Post-initialization setup for benchmark tasks."""
        super().__post_init__()
        
        # Set task type and metadata
        self.task_type = "benchmark_execution"
        
        # Update metadata with benchmark-specific info
        self.metadata.update({
            "num_assets": self.num_assets,
            "binary_bits": self.binary_bits,
            "cardinality": self.cardinality,
            "risk_tolerance": self.risk_tolerance,
            "max_sector_exposure": self.max_sector_exposure,
            "trajectories": self.trajectories,
            "time_limit_seconds": self.time_limit_seconds
        })


@dataclass
class SystemTask(Task):
    """
    Specialized task for system operations.
    
    Extends Task with system-specific fields:
    - Health checks
    - Maintenance operations
    - Resource monitoring
    """
    operation: str = ""
    component: str = ""
    
    def __post_init__(self):
        """Post-initialization setup for system tasks."""
        super().__post_init__()
        
        # Set task type
        self.task_type = "system_operation"
        
        # Update metadata with system-specific info
        self.metadata.update({
            "operation": self.operation,
            "component": self.component
        })
