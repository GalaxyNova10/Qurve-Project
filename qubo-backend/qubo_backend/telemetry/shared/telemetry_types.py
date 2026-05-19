"""
Qurve AI - Shared Telemetry Types
Zero-dependency type definitions for telemetry system
"""

from enum import Enum
from typing import Protocol, runtime_checkable


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


class PriorityType(str, Enum):
    """Priority types for tasks."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ProviderType(str, Enum):
    """Provider types for solvers."""
    NEAL = "neal"
    QISKIT = "qiskit"
    BRAKET = "braket"
    CLASSICAL = "classical"
    HYBRID = "hybrid"


class BackendType(str, Enum):
    """Backend types for quantum providers."""
    LOCAL_SIMULATOR = "local_simulator"
    CLOUD_SIMULATOR = "cloud_simulator"
    QUANTUM_HARDWARE = "quantum_hardware"
    HYBRID_SOLVER = "hybrid_solver"
    CLASSICAL_OPTIMIZER = "classical_optimizer"


@runtime_checkable
class TelemetryEmitter(Protocol):
    """Protocol for telemetry emission."""
    
    def emit_event(self, event: dict) -> None:
        """Emit a telemetry event."""
        ...
    
    def emit_error(self, error: dict) -> None:
        """Emit an error event."""
        ...
    
    def emit_metric(self, metric: dict) -> None:
        """Emit a metric event."""
        ...


@runtime_checkable
class EventTracker(Protocol):
    """Protocol for event tracking."""
    
    def add_event(self, event: dict) -> None:
        """Add an event to tracking."""
        ...
    
    def get_events(self, event_type: str = None) -> list:
        """Get events by type."""
        ...
    
    def clear_events(self) -> None:
        """Clear all tracked events."""
        ...


@runtime_checkable
class CorrelationManager(Protocol):
    """Protocol for correlation management."""
    
    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        ...
    
    def generate_benchmark_session_id(self) -> str:
        """Generate a new benchmark session ID."""
        ...
    
    def get_correlation_id(self) -> str:
        """Get current correlation ID."""
        ...
    
    def get_benchmark_session_id(self) -> str:
        """Get current benchmark session ID."""
        ...


@runtime_checkable
class TelemetryLogger(Protocol):
    """Protocol for structured logging."""
    
    def info(self, msg: str, **kwargs) -> None:
        """Log info message."""
        ...
    
    def warning(self, msg: str, **kwargs) -> None:
        """Log warning message."""
        ...
    
    def error(self, msg: str, **kwargs) -> None:
        """Log error message."""
        ...
    
    def debug(self, msg: str, **kwargs) -> None:
        """Log debug message."""
        ...


# Type aliases for common patterns
EventMetadata = dict[str, any]
TelemetryConfig = dict[str, any]
CorrelationContext = dict[str, str]
BenchmarkContext = dict[str, any]
ExecutionContext = dict[str, any]
