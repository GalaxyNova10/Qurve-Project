"""
Qurve AI - Replay Schema Definitions
Version 1.0 - LOCKED REPLAY SCHEMA

This file defines the frozen replay schema contracts.
Any changes require version bump and migration.

REPLAY_SCHEMA_VERSION = "v1"
REPLAY_SCHEMA_LOCKED = True
REPLAY_SCHEMA_LOCK_TIMESTAMP = "2026-05-12T22:45:00Z"
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

# Replay Schema Version
REPLAY_SCHEMA_VERSION = "v1"
REPLAY_SCHEMA_LOCKED = True
REPLAY_SCHEMA_LOCK_TIMESTAMP = "2026-05-12T22:45:00Z"


class ReplayModeSchema(Enum):
    """Replay mode schema - LOCKED v1."""
    METADATA_ONLY = "metadata_only"
    LOCAL_REPLAY = "local_replay"
    SIMULATION_REPLAY = "simulation_replay"


class ReplayStatusSchema(Enum):
    """Replay status schema - LOCKED v1."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DivergenceTypeSchema(Enum):
    """Divergence type schema - LOCKED v1."""
    TIMING = "timing"
    SOLVER = "solver"
    FALLBACK = "fallback"
    TELEMETRY = "telemetry"
    GOVERNANCE = "governance"


@dataclass
class ReplaySnapshotSchema:
    """Replay snapshot schema - LOCKED v1."""
    replay_id: str
    original_execution_id: str
    correlation_id: str
    timestamp: datetime
    original_request: Dict[str, Any]
    solver_selection: str
    execution_mode: str
    fallback_chain: List[str]
    cloud_task_references: List[str]
    governance_decisions: List[Dict[str, Any]]
    cost_decisions: List[Dict[str, Any]]
    telemetry_traces: List[Dict[str, Any]]
    credential_state_metadata: Dict[str, Any]
    solver_outputs: Dict[str, Any]
    timing_breakdowns: Dict[str, float]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    immutable: bool = True


@dataclass
class ReplaySessionSchema:
    """Replay session schema - LOCKED v1."""
    session_id: str
    replay_id: str
    mode: ReplayModeSchema
    status: ReplayStatusSchema
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    divergence_score: Optional[float] = None
    timeline_reconstruction_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ReplayTimelineEventSchema:
    """Replay timeline event schema - LOCKED v1."""
    event_id: str
    session_id: str
    timestamp: datetime
    event_type: str
    phase: str
    solver: str
    governance_decision: Optional[str] = None
    cloud_decision: Optional[str] = None
    fallback_decision: Optional[str] = None
    timing_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplayComparisonSchema:
    """Replay comparison schema - LOCKED v1."""
    comparison_id: str
    original_session_id: str
    replay_session_id: str
    timestamp: datetime
    timing_drift_ms: Optional[float] = None
    solver_divergence: Optional[Dict[str, Any]] = None
    fallback_divergence: Optional[Dict[str, Any]] = None
    telemetry_divergence: Optional[Dict[str, Any]] = None
    governance_divergence: Optional[Dict[str, Any]] = None
    overall_divergence_score: Optional[float] = None
    divergence_breakdown: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplayTelemetrySchema:
    """Replay telemetry schema - LOCKED v1."""
    replay_id: str
    replay_mode: ReplayModeSchema
    replay_source_execution_id: str
    timeline_reconstruction_ms: float
    replay_divergence_score: Optional[float] = None
    timestamp: datetime
    correlation_id: str
    metadata: Dict[str, Any] = field(default_factory=dict)


# Schema Validation Functions
def validate_replay_schema_version(version: str) -> bool:
    """Validate replay schema version."""
    return version == REPLAY_SCHEMA_VERSION


def validate_replay_snapshot_schema(snapshot: Any) -> bool:
    """Validate replay snapshot against schema."""
    required_fields = [
        'replay_id', 'original_execution_id', 'correlation_id', 'timestamp',
        'original_request', 'solver_selection', 'execution_mode', 'fallback_chain',
        'cloud_task_references', 'governance_decisions', 'cost_decisions',
        'telemetry_traces', 'credential_state_metadata', 'solver_outputs',
        'timing_breakdowns'
    ]
    return all(hasattr(snapshot, field) for field in required_fields)


def validate_replay_session_schema(session: Any) -> bool:
    """Validate replay session against schema."""
    required_fields = [
        'session_id', 'replay_id', 'mode', 'status', 'started_at',
        'divergence_score', 'timeline_reconstruction_ms'
    ]
    return all(hasattr(session, field) for field in required_fields)


# Schema Validation Functions
def validate_replay_schema_version(version: str) -> bool:
    """Validate replay schema version."""
    return version == REPLAY_SCHEMA_VERSION


# Schema Migration Rules
REPLAY_SCHEMA_MIGRATION_RULES = {
    "v1": {
        "compatible_with": ["v1"],
        "migration_required": False,
        "breaking_changes": []
    }
}


def check_replay_schema_compatibility(version: str) -> Dict[str, Any]:
    """Check replay schema compatibility."""
    if version not in REPLAY_SCHEMA_MIGRATION_RULES:
        return {
            "compatible": False,
            "migration_required": True,
            "breaking_changes": ["Unknown schema version"]
        }
    
    return REPLAY_SCHEMA_MIGRATION_RULES[version]


# Schema Export for Documentation
REPLAY_SCHEMA_EXPORT = {
    "version": REPLAY_SCHEMA_VERSION,
    "locked": REPLAY_SCHEMA_LOCKED,
    "lock_timestamp": REPLAY_SCHEMA_LOCK_TIMESTAMP,
    "enums": {
        "ReplayMode": [e.value for e in ReplayModeSchema],
        "ReplayStatus": [e.value for e in ReplayStatusSchema],
        "DivergenceType": [e.value for e in DivergenceTypeSchema]
    },
    "dataclasses": {
        "ReplaySnapshot": ReplaySnapshotSchema.__annotations__,
        "ReplaySession": ReplaySessionSchema.__annotations__,
        "ReplayTimelineEvent": ReplayTimelineEventSchema.__annotations__,
        "ReplayComparison": ReplayComparisonSchema.__annotations__,
        "ReplayTelemetry": ReplayTelemetrySchema.__annotations__
    }
}
