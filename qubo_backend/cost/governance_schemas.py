"""
Qurve AI - Governance Schema Definitions
Version 1.0 - LOCKED SCHEMA

This file defines the frozen governance schema contracts.
Any changes require version bump and migration.

GOVERNANCE_SCHEMA_VERSION = "v1"
SCHEMA_LOCKED = True
SCHEMA_LOCK_TIMESTAMP = "2026-05-12T22:00:00Z"
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime

# Governance Schema Version
GOVERNANCE_SCHEMA_VERSION = "v1"
SCHEMA_LOCKED = True
SCHEMA_LOCK_TIMESTAMP = "2026-05-12T22:00:00Z"


class GovernanceDecisionSchema(Enum):
    """Governance decision schema - LOCKED v1."""
    ALLOW = "allow"
    THROTTLE = "throttle"
    FALLBACK = "fallback"
    REJECT = "reject"


class AlertLevelSchema(Enum):
    """Alert level schema - LOCKED v1."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CloudDeviceSchema(Enum):
    """Cloud device schema - LOCKED v1."""
    SV1_SIMULATOR = "sv1"
    TN1_SIMULATOR = "tn1"
    DM1_SIMULATOR = "dm1"


@dataclass
class CostModelSchema:
    """Cost model schema - LOCKED v1."""
    device: CloudDeviceSchema
    cost_per_task_usd: float
    cost_per_shot_usd: float
    min_cost_usd: float
    max_cost_usd: float
    description: str


@dataclass
class QuotaConfigSchema:
    """Quota configuration schema - LOCKED v1."""
    max_daily_spend_usd: float = 100.0
    max_monthly_spend_usd: float = 1000.0
    max_single_task_cost_usd: float = 10.0
    max_cloud_tasks_per_hour: int = 10
    max_cloud_tasks_per_day: int = 100


@dataclass
class CostEstimateSchema:
    """Cost estimate schema - LOCKED v1."""
    device: CloudDeviceSchema
    shots: int
    estimated_cost_usd: float
    governance_decision: GovernanceDecisionSchema
    quota_remaining_usd: Optional[float] = None
    throttle_reason: Optional[str] = None
    fallback_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CostTelemetrySchema:
    """Cost telemetry schema - LOCKED v1."""
    correlation_id: str
    estimated_cost_usd: float
    daily_spend_usd: float
    monthly_spend_usd: float
    governance_decision: GovernanceDecisionSchema
    quota_remaining_usd: float
    alert_level: AlertLevelSchema
    alert_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GovernanceEventSchema:
    """Governance event schema - LOCKED v1."""
    event_id: str
    correlation_id: str
    timestamp: datetime
    governance_decision: GovernanceDecisionSchema
    estimated_cost_usd: float
    quota_snapshot: Dict[str, Any]
    device: CloudDeviceSchema
    shots: int
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ThrottlingEventSchema:
    """Throttling event schema - LOCKED v1."""
    event_id: str
    correlation_id: str
    timestamp: datetime
    throttle_reason: str
    quota_remaining_usd: float
    hourly_tasks_used: int
    daily_tasks_used: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackEventSchema:
    """Fallback event schema - LOCKED v1."""
    event_id: str
    correlation_id: str
    timestamp: datetime
    from_solver: str
    to_solver: str
    fallback_reason: str
    governance_decision: GovernanceDecisionSchema
    cloud_cost_impact: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# Schema Validation Functions
def validate_governance_schema_version(version: str) -> bool:
    """Validate governance schema version."""
    return version == GOVERNANCE_SCHEMA_VERSION


def validate_cost_model_schema(model: Any) -> bool:
    """Validate cost model against schema."""
    required_fields = ['device', 'cost_per_task_usd', 'cost_per_shot_usd', 'min_cost_usd', 'max_cost_usd', 'description']
    return all(hasattr(model, field) for field in required_fields)


def validate_quota_config_schema(config: Any) -> bool:
    """Validate quota config against schema."""
    required_fields = ['max_daily_spend_usd', 'max_monthly_spend_usd', 'max_single_task_cost_usd', 
                       'max_cloud_tasks_per_hour', 'max_cloud_tasks_per_day']
    return all(hasattr(config, field) for field in required_fields)


def validate_cost_telemetry_schema(telemetry: Any) -> bool:
    """Validate cost telemetry against schema."""
    required_fields = ['estimated_cost_usd', 'daily_spend_usd', 'monthly_spend_usd', 
                       'governance_decision', 'quota_remaining_usd', 'alert_level', 'timestamp', 'correlation_id']
    return all(hasattr(telemetry, field) for field in required_fields)


# Schema Migration Rules
SCHEMA_MIGRATION_RULES = {
    "v1": {
        "compatible_with": ["v1"],
        "migration_required": False,
        "breaking_changes": []
    }
}


def check_schema_compatibility(version: str) -> Dict[str, Any]:
    """Check schema compatibility."""
    if version not in SCHEMA_MIGRATION_RULES:
        return {
            "compatible": False,
            "migration_required": True,
            "breaking_changes": ["Unknown schema version"]
        }
    
    return SCHEMA_MIGRATION_RULES[version]


# Schema Export for Documentation
GOVERNANCE_SCHEMA_EXPORT = {
    "version": GOVERNANCE_SCHEMA_VERSION,
    "locked": SCHEMA_LOCKED,
    "lock_timestamp": SCHEMA_LOCK_TIMESTAMP,
    "enums": {
        "GovernanceDecision": [e.value for e in GovernanceDecisionSchema],
        "AlertLevel": [e.value for e in AlertLevelSchema],
        "CloudDevice": [e.value for e in CloudDeviceSchema]
    },
    "dataclasses": {
        "CostModel": CostModelSchema.__annotations__,
        "QuotaConfig": QuotaConfigSchema.__annotations__,
        "CostEstimate": CostEstimateSchema.__annotations__,
        "CostTelemetry": CostTelemetrySchema.__annotations__,
        "GovernanceEvent": GovernanceEventSchema.__annotations__,
        "ThrottlingEvent": ThrottlingEventSchema.__annotations__,
        "FallbackEvent": FallbackEventSchema.__annotations__
    }
}

REPLAY_SCHEMA_EXPORT = {
    "version": "v1",
    "locked": True,
    "lock_timestamp": "2026-05-12T22:00:00Z",
    "enums": {
        "ReplayMode": ["mode1", "mode2"],
        "ReplayStatus": ["status1", "status2"],
        "DivergenceType": ["type1", "type2"]
    },
    "dataclasses": {
        "ReplaySnapshot": {},
        "ReplaySession": {},
        "ReplayTimelineEvent": {},
        "ReplayComparison": {},
        "ReplayTelemetry": {}
    }
}
