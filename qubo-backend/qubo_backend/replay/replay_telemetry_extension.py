"""
Qurve AI - Replay Telemetry Extension
Forensic-only telemetry for replay system with isolation guarantees.

Principles:
✅ FORENSIC-ONLY: Never affects production telemetry
✅ ISOLATED NAMESPACE: Separate from live telemetry
✅ CORRELATION PRESERVATION: Maintains execution lineage
✅ REPLAY METADATA: replay_id, replay_mode, divergence_score
✅ LINEAGE INTEGRITY: Preserves benchmark and governance lineage
"""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

from .replay_schemas import (
    ReplayTelemetrySchema,
    ReplayModeSchema
)

logger = logging.getLogger(__name__)


@dataclass
class ReplayTelemetryConfig:
    """Replay telemetry configuration."""
    enable_replay_telemetry: bool = True
    max_replay_events: int = 10000
    replay_telemetry_retention_days: int = 365
    isolation_namespace: str = "replay"
    forensic_only: bool = True


class ReplayTelemetryExtension:
    """
    Production-grade replay telemetry extension.
    
    Features:
    - Forensic-only telemetry collection
    - Isolated namespace from production
    - Correlation ID preservation
    - Replay metadata enrichment
    - Lineage integrity maintenance
    """
    
    def __init__(self, config: ReplayTelemetryConfig):
        self.config = config
        
        # Replay telemetry state
        self._replay_telemetry: Dict[str, ReplayTelemetrySchema] = {}
        self._replay_events: List[Dict[str, Any]] = []
        
        # Telemetry statistics
        self._telemetry_count = 0
        self._replay_sessions_tracked = set()
        
        logger.info("Replay telemetry extension initialized", 
                  forensic_only=config.forensic_only,
                  isolation_namespace=config.isolation_namespace)
    
    async def emit_replay_telemetry(self, 
                                   replay_id: str,
                                   replay_mode: ReplayModeSchema,
                                   replay_source_execution_id: str,
                                   timeline_reconstruction_ms: float,
                                   divergence_score: Optional[float] = None,
                                   reconstruction_status: str = "completed",
                                   lineage_integrity_status: str = "preserved",
                                   replay_duration_ms: Optional[float] = None,
                                   correlation_id: Optional[str] = None,
                                   benchmark_lineage: Optional[List[str]] = None,
                                   governance_lineage: Optional[List[str]] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Emit forensic-only replay telemetry.
        
        Args:
            replay_id: Unique replay identifier
            replay_mode: Replay execution mode
            replay_source_execution_id: Original execution ID
            timeline_reconstruction_ms: Timeline reconstruction duration
            divergence_score: Divergence analysis score
            reconstruction_status: Reconstruction completion status
            lineage_integrity_status: Lineage preservation status
            replay_duration_ms: Total replay execution duration
            correlation_id: Original execution correlation ID
            benchmark_lineage: Benchmark execution lineage
            governance_lineage: Governance decision lineage
            metadata: Additional replay metadata
            
        Returns:
            telemetry_id: Unique telemetry event ID
        """
        try:
            # Validate forensic-only requirement
            if not self.config.forensic_only:
                raise ValueError("Replay telemetry must be forensic-only")
            
            telemetry_id = f"replay_telemetry_{replay_id}_{int(time.time())}"
            
            # Create replay telemetry with isolation guarantees
            telemetry = ReplayTelemetrySchema(
                replay_id=replay_id,
                replay_mode=replay_mode,
                replay_source_execution_id=replay_source_execution_id,
                timeline_reconstruction_ms=timeline_reconstruction_ms,
                divergence_score=divergence_score,
                timestamp=datetime.now(),
                correlation_id=correlation_id or "",
                metadata={
                    "telemetry_id": telemetry_id,
                    "reconstruction_status": reconstruction_status,
                    "lineage_integrity_status": lineage_integrity_status,
                    "replay_duration_ms": replay_duration_ms,
                    "benchmark_lineage": benchmark_lineage or [],
                    "governance_lineage": governance_lineage or [],
                    "isolation_namespace": self.config.isolation_namespace,
                    "forensic_only": self.config.forensic_only,
                    "reconstructed": True,
                    "artifact_type": "replay",
                    **(metadata or {})
                }
            )
            
            # Store telemetry in isolated namespace
            self._replay_telemetry[telemetry_id] = telemetry
            self._replay_sessions_tracked.add(replay_id)
            self._telemetry_count += 1
            
            # Emit forensic event (never to production telemetry)
            await self._emit_forensic_event(telemetry)
            
            logger.info("Replay telemetry emitted", 
                       telemetry_id=telemetry_id,
                       replay_id=replay_id,
                       replay_mode=replay_mode.value,
                       divergence_score=divergence_score,
                       forensic_only=True)
            
            return telemetry_id
            
        except Exception as e:
            logger.error("Failed to emit replay telemetry", 
                        replay_id=replay_id,
                        error=str(e))
            raise
    
    async def _emit_forensic_event(self, telemetry: ReplayTelemetrySchema) -> None:
        """
        Emit forensic event to isolated replay namespace.
        
        Never emits to production telemetry systems.
        """
        try:
            # Create forensic event with isolation guarantees
            forensic_event = {
                "event_id": telemetry.metadata.get("telemetry_id"),
                "namespace": self.config.isolation_namespace,
                "event_type": "replay_telemetry",
                "timestamp": telemetry.timestamp.isoformat(),
                "replay_id": telemetry.replay_id,
                "replay_mode": telemetry.replay_mode.value,
                "replay_source_execution_id": telemetry.replay_source_execution_id,
                "timeline_reconstruction_ms": telemetry.timeline_reconstruction_ms,
                "divergence_score": telemetry.divergence_score,
                "correlation_id": telemetry.correlation_id,
                "reconstruction_status": telemetry.metadata.get("reconstruction_status"),
                "lineage_integrity_status": telemetry.metadata.get("lineage_integrity_status"),
                "replay_duration_ms": telemetry.metadata.get("replay_duration_ms"),
                "benchmark_lineage": telemetry.metadata.get("benchmark_lineage"),
                "governance_lineage": telemetry.metadata.get("governance_lineage"),
                "isolation_namespace": self.config.isolation_namespace,
                "forensic_only": telemetry.metadata.get("forensic_only"),
                "reconstructed": telemetry.metadata.get("reconstructed"),
                "artifact_type": telemetry.metadata.get("artifact_type"),
                "metadata": telemetry.metadata
            }
            
            # Store in isolated replay events
            self._replay_events.append(forensic_event)
            
            # Enforce event limit
            if len(self._replay_events) > self.config.max_replay_events:
                self._replay_events = self._replay_events[-self.config.max_replay_events:]
            
            logger.debug("Forensic event emitted", 
                       event_id=forensic_event["event_id"],
                       namespace=self.config.isolation_namespace,
                       forensic_only=True)
            
        except Exception as e:
            logger.error("Failed to emit forensic event", 
                        replay_id=telemetry.replay_id,
                        error=str(e))
    
    async def get_replay_telemetry(self, replay_id: str) -> List[ReplayTelemetrySchema]:
        """Get telemetry for specific replay."""
        return [
            telemetry for telemetry in self._replay_telemetry.values()
            if telemetry.replay_id == replay_id
        ]
    
    async def get_replay_telemetry_by_correlation(self, correlation_id: str) -> List[ReplayTelemetrySchema]:
        """Get telemetry by original correlation ID."""
        return [
            telemetry for telemetry in self._replay_telemetry.values()
            if telemetry.correlation_id == correlation_id
        ]
    
    async def get_forensic_events(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent forensic events from isolated namespace."""
        events = sorted(self._replay_events, key=lambda e: e["timestamp"], reverse=True)
        return events[:limit]
    
    async def get_replay_sessions_summary(self) -> Dict[str, Any]:
        """Get summary of tracked replay sessions."""
        sessions_summary = {}
        
        for replay_id in self._replay_sessions_tracked:
            session_telemetry = await self.get_replay_telemetry(replay_id)
            if session_telemetry:
                latest_telemetry = max(session_telemetry, key=lambda t: t.timestamp)
                
                sessions_summary[replay_id] = {
                    "replay_mode": latest_telemetry.replay_mode.value,
                    "replay_source_execution_id": latest_telemetry.replay_source_execution_id,
                    "latest_divergence_score": latest_telemetry.divergence_score,
                    "latest_timeline_reconstruction_ms": latest_telemetry.timeline_reconstruction_ms,
                    "telemetry_count": len(session_telemetry),
                    "latest_timestamp": latest_telemetry.timestamp.isoformat(),
                    "lineage_integrity_status": latest_telemetry.metadata.get("lineage_integrity_status"),
                    "reconstruction_status": latest_telemetry.metadata.get("reconstruction_status")
                }
        
        return sessions_summary
    
    def get_telemetry_statistics(self) -> Dict[str, Any]:
        """Get replay telemetry statistics."""
        return {
            "total_telemetry_events": self._telemetry_count,
            "tracked_replay_sessions": len(self._replay_sessions_tracked),
            "stored_telemetry_records": len(self._replay_telemetry),
            "stored_forensic_events": len(self._replay_events),
            "isolation_namespace": self.config.isolation_namespace,
            "forensic_only": self.config.forensic_only,
            "max_events_limit": self.config.max_replay_events,
            "retention_days": self.config.replay_telemetry_retention_days
        }
    
    async def cleanup_expired_telemetry(self) -> int:
        """Clean up expired telemetry records."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.replay_telemetry_retention_days)
            
            # Clean up telemetry records
            expired_telemetry = [
                telemetry_id for telemetry_id, telemetry in self._replay_telemetry.items()
                if telemetry.timestamp < cutoff_date
            ]
            
            for telemetry_id in expired_telemetry:
                del self._replay_telemetry[telemetry_id]
            
            # Clean up forensic events
            cutoff_timestamp = cutoff_date.isoformat()
            original_count = len(self._replay_events)
            self._replay_events = [
                event for event in self._replay_events
                if event["timestamp"] >= cutoff_timestamp
            ]
            
            cleaned_count = len(expired_telemetry) + (original_count - len(self._replay_events))
            
            logger.info("Replay telemetry cleanup completed", 
                       cleaned_records=cleaned_count,
                       cutoff_date=cutoff_date.isoformat())
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired telemetry", error=str(e))
            return 0


# Global replay telemetry extension instance
_replay_telemetry_extension: Optional[ReplayTelemetryExtension] = None


def get_replay_telemetry_extension() -> ReplayTelemetryExtension:
    """Get global replay telemetry extension instance."""
    global _replay_telemetry_extension
    if _replay_telemetry_extension is None:
        _replay_telemetry_extension = ReplayTelemetryExtension(ReplayTelemetryConfig())
    return _replay_telemetry_extension


def create_replay_telemetry_config(
    enable_replay_telemetry: bool = True,
    max_replay_events: int = 10000,
    replay_telemetry_retention_days: int = 365,
    isolation_namespace: str = "replay",
    forensic_only: bool = True
) -> ReplayTelemetryConfig:
    """Create replay telemetry configuration."""
    return ReplayTelemetryConfig(
        enable_replay_telemetry=enable_replay_telemetry,
        max_replay_events=max_replay_events,
        replay_telemetry_retention_days=replay_telemetry_retention_days,
        isolation_namespace=isolation_namespace,
        forensic_only=forensic_only
    )
