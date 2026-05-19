"""
Qurve AI - Shared Telemetry Models
Zero-dependency shared models for telemetry system
"""

from .event_models import (
    BaseEvent,
    BenchmarkEvent,
    TaskEvent,
    WorkerEvent,
    QueueEvent,
    SystemEvent
)

from .telemetry_types import (
    EventType,
    ComponentType,
    StatusType,
    PriorityType,
    ProviderType,
    BackendType
)

from .context_models import (
    TelemetryContext,
    CorrelationContext,
    BenchmarkContext,
    ExecutionContext
)

from .correlation_models import (
    CorrelationId,
    BenchmarkSessionId,
    WorkerId,
    TaskId,
    TraceId
)

__all__ = [
    # Event models
    'BaseEvent',
    'BenchmarkEvent', 
    'TaskEvent',
    'WorkerEvent',
    'QueueEvent',
    'SystemEvent',
    
    # Type definitions
    'EventType',
    'ComponentType',
    'StatusType',
    'PriorityType',
    'ProviderType',
    'BackendType',
    
    # Context models
    'TelemetryContext',
    'CorrelationContext',
    'BenchmarkContext',
    'ExecutionContext',
    
    # ID models
    'CorrelationId',
    'BenchmarkSessionId',
    'WorkerId',
    'TaskId',
    'TraceId'
]
