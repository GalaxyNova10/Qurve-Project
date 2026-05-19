"""
Qurve AI - Replay Artifact Classification
Enforces strict separation between operational truth and replay artifacts.

This module defines the immutable boundary between:
- Operational Truth: Real execution records
- Replay Artifacts: Derived analytical reconstructions

PRINCIPLE: "Execution records reality. Replay reconstructs reality. Replay must NEVER overwrite reality."
"""

from enum import Enum
from typing import Dict, Any, List
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class ArtifactType(Enum):
    """Artifact type classification."""
    OPERATIONAL_TRUTH = "operational_truth"
    REPLAY_ARTIFACT = "replay_artifact"


class DataSource(Enum):
    """Data source classification."""
    EXECUTION_TELEMETRY = "execution_telemetry"
    GOVERNANCE_DECISIONS = "governance_decisions"
    BENCHMARK_RESULTS = "benchmark_results"
    CLOUD_TASK_RECORDS = "cloud_task_records"
    REPLAY_SESSIONS = "replay_sessions"
    REPLAY_TIMELINES = "replay_timelines"
    REPLAY_COMPARISONS = "replay_comparisons"
    REPLAY_DIVERGENCE = "replay_divergence"


@dataclass
class ArtifactClassification:
    """Artifact classification metadata."""
    artifact_type: ArtifactType
    data_source: DataSource
    table_name: str
    namespace: str
    is_authoritative: bool
    is_derived: bool
    created_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ArtifactClassificationRules:
    """
    Enforces strict separation between operational truth and replay artifacts.
    
    Rules:
    - Operational truth tables are READ-ONLY and immutable
    - Replay artifact tables are WRITE-ONLY and derived
    - Cross-contamination is forbidden
    - Clear labeling required for all APIs
    - Dashboard separation enforced
    """
    
    def __init__(self):
        self.classifications = self._define_classifications()
        logger.info("Artifact classification rules initialized", 
                  operational_tables=len([c for c in self.classifications if c.artifact_type == ArtifactType.OPERATIONAL_TRUTH]),
                  replay_tables=len([c for c in self.classifications if c.artifact_type == ArtifactType.REPLAY_ARTIFACT]))
    
    def _define_classifications(self) -> List[ArtifactClassification]:
        """Define all artifact classifications."""
        return [
            # Operational Truth Classifications
            ArtifactClassification(
                artifact_type=ArtifactType.OPERATIONAL_TRUTH,
                data_source=DataSource.EXECUTION_TELEMETRY,
                table_name="telemetry_events",
                namespace="execution",
                is_authoritative=True,
                is_derived=False,
                created_at="2026-05-12T22:30:00Z",
                metadata={
                    "description": "Live execution telemetry from structured telemetry",
                    "access_pattern": "READ-ONLY",
                    "retention": "30 days",
                    "source": "live_execution"
                }
            ),
            ArtifactClassification(
                artifact_type=ArtifactType.OPERATIONAL_TRUTH,
                data_source=DataSource.GOVERNANCE_DECISIONS,
                table_name="governance_events",
                namespace="governance",
                is_authoritative=True,
                is_derived=False,
                created_at="2026-05-12T22:30:00Z",
                metadata={
                    "description": "Governance decisions from cost governance system",
                    "access_pattern": "READ-ONLY",
                    "retention": "90 days",
                    "source": "cost_governance"
                }
            ),
            ArtifactClassification(
                artifact_type=ArtifactType.OPERATIONAL_TRUTH,
                data_source=DataSource.BENCHMARK_RESULTS,
                table_name="benchmark_runs",
                namespace="execution",
                is_authoritative=True,
                is_derived=False,
                created_at="2026-05-12T22:30:00Z",
                metadata={
                    "description": "Benchmark execution results and metadata",
                    "access_pattern": "READ-ONLY",
                    "retention": "1 year",
                    "source": "benchmark_execution"
                }
            ),
            ArtifactClassification(
                artifact_type=ArtifactType.OPERATIONAL_TRUTH,
                data_source=DataSource.CLOUD_TASK_RECORDS,
                table_name="cloud_tasks",
                namespace="cloud",
                is_authoritative=True,
                is_derived=False,
                created_at="2026-05-12T22:30:00Z",
                metadata={
                    "description": "AWS Braket cloud task execution records",
                    "access_pattern": "READ-ONLY",
                    "retention": "90 days",
                    "source": "cloud_execution"
                }
            ),
            
            # Replay Artifact Classifications
            ArtifactClassification(
                artifact_type=ArtifactType.REPLAY_ARTIFACT,
                data_source=DataSource.REPLAY_SESSIONS,
                table_name="replay_sessions",
                namespace="replay",
                is_authoritative=False,
                is_derived=True,
                created_at="2026-05-12T22:45:00Z",
                metadata={
                    "description": "Replay session metadata and results",
                    "access_pattern": "WRITE-ONLY",
                    "retention": "1 year",
                    "source": "replay_system"
                }
            ),
            ArtifactClassification(
                artifact_type=ArtifactType.REPLAY_ARTIFACT,
                data_source=DataSource.REPLAY_TIMELINES,
                table_name="replay_timelines",
                namespace="replay",
                is_authoritative=False,
                is_derived=True,
                created_at="2026-05-12T22:45:00Z",
                metadata={
                    "description": "Reconstructed execution timelines for analysis",
                    "access_pattern": "WRITE-ONLY",
                    "retention": "1 year",
                    "source": "replay_system"
                }
            ),
            ArtifactClassification(
                artifact_type=ArtifactType.REPLAY_ARTIFACT,
                data_source=DataSource.REPLAY_COMPARISONS,
                table_name="replay_comparisons",
                namespace="replay",
                is_authoritative=False,
                is_derived=True,
                created_at="2026-05-12T22:45:00Z",
                metadata={
                    "description": "Comparison between original and replayed executions",
                    "access_pattern": "WRITE-ONLY",
                    "retention": "1 year",
                    "source": "replay_system"
                }
            ),
            ArtifactClassification(
                artifact_type=ArtifactType.REPLAY_ARTIFACT,
                data_source=DataSource.REPLAY_DIVERGENCE,
                table_name="replay_divergence_reports",
                namespace="replay",
                is_authoritative=False,
                is_derived=True,
                created_at="2026-05-12T22:45:00Z",
                metadata={
                    "description": "Divergence analysis between original and replayed executions",
                    "access_pattern": "WRITE-ONLY",
                    "retention": "1 year",
                    "source": "replay_system"
                }
            )
        ]
    
    def classify_table(self, table_name: str) -> ArtifactClassification:
        """Classify a table by name."""
        for classification in self.classifications:
            if classification.table_name == table_name:
                return classification
        raise ValueError(f"Unknown table: {table_name}")
    
    def is_operational_table(self, table_name: str) -> bool:
        """Check if table is operational truth."""
        try:
            classification = self.classify_table(table_name)
            return classification.artifact_type == ArtifactType.OPERATIONAL_TRUTH
        except ValueError:
            return False
    
    def is_replay_table(self, table_name: str) -> bool:
        """Check if table is replay artifact."""
        try:
            classification = self.classify_table(table_name)
            return classification.artifact_type == ArtifactType.REPLAY_ARTIFACT
        except ValueError:
            return False
    
    def validate_access_pattern(self, table_name: str, is_write_operation: bool) -> bool:
        """
        Validate access pattern matches classification.
        
        Args:
            table_name: Name of table being accessed
            is_write_operation: Whether this is a write operation
            
        Returns:
            True if access pattern is valid
        """
        try:
            classification = self.classify_table(table_name)
            
            # Operational tables are READ-ONLY
            if classification.artifact_type == ArtifactType.OPERATIONAL_TRUTH:
                return not is_write_operation
            
            # Replay tables are WRITE-ONLY
            if classification.artifact_type == ArtifactType.REPLAY_ARTIFACT:
                return is_write_operation
            
            return False
            
        except ValueError:
            return False
    
    def get_operational_tables(self) -> List[str]:
        """Get list of operational table names."""
        return [c.table_name for c in self.classifications if c.artifact_type == ArtifactType.OPERATIONAL_TRUTH]
    
    def get_replay_tables(self) -> List[str]:
        """Get list of replay table names."""
        return [c.table_name for c in self.classifications if c.artifact_type == ArtifactType.REPLAY_ARTIFACT]
    
    def get_classification_summary(self) -> Dict[str, Any]:
        """Get summary of all classifications."""
        operational_count = len([c for c in self.classifications if c.artifact_type == ArtifactType.OPERATIONAL_TRUTH])
        replay_count = len([c for c in self.classifications if c.artifact_type == ArtifactType.REPLAY_ARTIFACT])
        
        return {
            "total_classifications": len(self.classifications),
            "operational_tables": operational_count,
            "replay_tables": replay_count,
            "separation_enforced": operational_count > 0 and replay_count > 0,
            "classification_locked": True,
            "created_at": "2026-05-12T22:45:00Z"
        }


# Global artifact classification instance
_artifact_classification: Optional[ArtifactClassificationRules] = None


def get_artifact_classification() -> ArtifactClassificationRules:
    """Get global artifact classification instance."""
    global _artifact_classification
    if _artifact_classification is None:
        _artifact_classification = ArtifactClassificationRules()
    return _artifact_classification
