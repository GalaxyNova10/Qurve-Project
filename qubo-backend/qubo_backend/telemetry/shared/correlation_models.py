"""
Qurve AI - Shared Correlation Models
Zero-dependency correlation ID models for telemetry system
"""

from dataclasses import dataclass, field
from typing import Optional
import uuid


@dataclass
class CorrelationId:
    """Correlation ID for request tracking."""
    value: str = field(default_factory=lambda: f"qurve-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"CorrelationId({self.value})"


@dataclass
class BenchmarkSessionId:
    """Benchmark session ID for tracking."""
    value: str = field(default_factory=lambda: f"bench-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"BenchmarkSessionId({self.value})"


@dataclass
class WorkerId:
    """Worker ID for tracking."""
    value: str = field(default_factory=lambda: f"worker-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"WorkerId({self.value})"


@dataclass
class TaskId:
    """Task ID for tracking."""
    value: str = field(default_factory=lambda: f"task-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TaskId({self.value})"


@dataclass
class TraceId:
    """Trace ID for distributed tracing."""
    value: str = field(default_factory=lambda: f"trace-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TraceId({self.value})"


@dataclass
class SpanId:
    """Span ID for distributed tracing."""
    value: str = field(default_factory=lambda: f"span-{uuid.uuid4()}")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"SpanId({self.value})"


# Factory functions for creating IDs
def create_correlation_id() -> CorrelationId:
    """Create a new correlation ID."""
    return CorrelationId()


def create_benchmark_session_id() -> BenchmarkSessionId:
    """Create a new benchmark session ID."""
    return BenchmarkSessionId()


def create_worker_id() -> WorkerId:
    """Create a new worker ID."""
    return WorkerId()


def create_task_id() -> TaskId:
    """Create a new task ID."""
    return TaskId()


def create_trace_id() -> TraceId:
    """Create a new trace ID."""
    return TraceId()


def create_span_id() -> SpanId:
    """Create a new span ID."""
    return SpanId()


# Validation functions
def is_valid_correlation_id(correlation_id: str) -> bool:
    """Validate correlation ID format."""
    return correlation_id.startswith("qurve-") and len(correlation_id) > 10


def is_valid_benchmark_session_id(session_id: str) -> bool:
    """Validate benchmark session ID format."""
    return session_id.startswith("bench-") and len(session_id) > 10


def is_valid_worker_id(worker_id: str) -> bool:
    """Validate worker ID format."""
    return worker_id.startswith("worker-") and len(worker_id) > 10


def is_valid_task_id(task_id: str) -> bool:
    """Validate task ID format."""
    return task_id.startswith("task-") and len(task_id) > 10


def is_valid_trace_id(trace_id: str) -> bool:
    """Validate trace ID format."""
    return trace_id.startswith("trace-") and len(trace_id) > 10


def is_valid_span_id(span_id: str) -> bool:
    """Validate span ID format."""
    return span_id.startswith("span-") and len(span_id) > 10
