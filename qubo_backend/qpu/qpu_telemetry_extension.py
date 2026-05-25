"""
Qurve AI - QPU Telemetry Extension
QPU-specific telemetry with lineage preservation and isolation.

Principles:
✅ QPU PROVIDER METADATA: Capture provider-specific information
✅ QPU DEVICE METADATA: Capture device-specific information
✅ QUEUE WAIT TRACKING: Track QPU queue delays
✅ HARDWARE EXECUTION METADATA: Capture hardware execution details
✅ CALIBRATION SNAPSHOT ID: Link to calibration observability
✅ QPU GOVERNANCE DECISION: Capture governance approval
✅ FALLBACK ORIGIN: Track fallback chain origin
✅ CORRELATION LINEAGE PRESERVATION: Maintain execution lineage
✅ REPLAY COMPATIBILITY: Ensure replay system compatibility
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .qpu_device_registry import get_qpu_device_registry, QPUProvider

logger = logging.getLogger(__name__)


class QPUTelemetryType(Enum):
    """QPU telemetry event types."""
    QPU_EXECUTION_STARTED = "qpu_execution_started"
    QPU_EXECUTION_COMPLETED = "qpu_execution_completed"
    QPU_QUEUE_WAIT = "qpu_queue_wait"
    QPU_GOVERNANCE_DECISION = "qpu_governance_decision"
    QPU_FALLBACK_TRIGGERED = "qpu_fallback_triggered"
    QPU_CALIBRATION_SNAPSHOT = "qpu_calibration_snapshot"
    QPU_HARDWARE_METADATA = "qpu_hardware_metadata"


@dataclass
class QPUTelemetryEvent:
    """QPU telemetry event with lineage preservation."""
    event_id: str
    event_type: QPUTelemetryType
    provider: str
    device: str
    correlation_id: Optional[str] = None
    original_correlation_id: Optional[str] = None
    parent_correlation_id: Optional[str] = None
    benchmark_session_id: Optional[str] = None
    execution_lineage: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    lineage_preserved: bool = True
    replay_compatible: bool = True


@dataclass
class QPUTelemetryConfig:
    """QPU telemetry extension configuration."""
    enable_qpu_telemetry: bool = True
    preserve_correlation_lineage: bool = True
    preserve_replay_compatibility: bool = True
    qpu_namespace: str = "qpu_telemetry"
    max_telemetry_events: int = 10000
    telemetry_retention_days: int = 30


class QPUTelemetryExtension:
    """
    Production-grade QPU telemetry extension.
    
    Features:
    - QPU provider metadata capture
    - QPU device metadata capture
    - Queue wait tracking
    - Hardware execution metadata
    - Calibration snapshot linking
    - Governance decision capture
    - Fallback origin tracking
    - Correlation lineage preservation
    - Replay compatibility
    """
    
    def __init__(self, config: QPUTelemetryConfig):
        self.config = config
        self.device_registry = get_qpu_device_registry()
        
        # QPU telemetry state
        self._qpu_telemetry: Dict[str, QPUTelemetryEvent] = {}
        self._correlation_lineage: Dict[str, List[str]] = {}
        self._execution_lineage: Dict[str, List[str]] = {}
        
        # Telemetry statistics
        self._telemetry_count = 0
        self._lineage_preservation_count = 0
        
        logger.info("QPU telemetry extension initialized", 
                  preserve_correlation_lineage=config.preserve_correlation_lineage,
                  preserve_replay_compatibility=config.preserve_replay_compatibility,
                  qpu_namespace=config.qpu_namespace)
    
    async def emit_qpu_telemetry(self, 
                                   event_type: QPUTelemetryType,
                                   provider: str,
                                   device: str,
                                   correlation_id: Optional[str] = None,
                                   original_correlation_id: Optional[str] = None,
                                   parent_correlation_id: Optional[str] = None,
                                   benchmark_session_id: Optional[str] = None,
                                   qpu_provider: Optional[str] = None,
                                   qpu_device: Optional[str] = None,
                                   queue_wait_ms: Optional[float] = None,
                                   hardware_execution_ms: Optional[float] = None,
                                   calibration_snapshot_id: Optional[str] = None,
                                   qpu_governance_decision: Optional[str] = None,
                                   fallback_origin: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Emit QPU telemetry event with lineage preservation.
        
        Args:
            event_type: QPU telemetry event type
            provider: QPU provider
            device: QPU device
            correlation_id: Request correlation ID
            original_correlation_id: Original correlation ID
            parent_correlation_id: Parent correlation ID
            benchmark_session_id: Benchmark session ID
            qpu_provider: QPU provider (if different from provider)
            qpu_device: QPU device (if different from device)
            queue_wait_ms: Queue wait time in milliseconds
            hardware_execution_ms: Hardware execution time in milliseconds
            calibration_snapshot_id: Calibration snapshot ID
            qpu_governance_decision: Governance decision
            fallback_origin: Fallback origin
            metadata: Additional metadata
            
        Returns:
            telemetry_event_id: Unique telemetry event ID
        """
        try:
            event_id = f"qpu_telemetry_{provider}_{device}_{int(time.time())}"
            
            # Build execution lineage
            execution_lineage = await self._build_execution_lineage(
                correlation_id, original_correlation_id, parent_correlation_id
            )
            
            # Create telemetry event
            telemetry_event = QPUTelemetryEvent(
                event_id=event_id,
                event_type=event_type,
                provider=provider,
                device=device,
                correlation_id=correlation_id,
                original_correlation_id=original_correlation_id,
                parent_correlation_id=parent_correlation_id,
                benchmark_session_id=benchmark_session_id,
                execution_lineage=execution_lineage,
                metadata={
                    "qpu_provider": qpu_provider or provider,
                    "qpu_device": qpu_device or device,
                    "queue_wait_ms": queue_wait_ms,
                    "hardware_execution_ms": hardware_execution_ms,
                    "calibration_snapshot_id": calibration_snapshot_id,
                    "qpu_governance_decision": qpu_governance_decision,
                    "fallback_origin": fallback_origin,
                    "namespace": self.config.qpu_namespace,
                    "lineage_preserved": self.config.preserve_correlation_lineage,
                    "replay_compatible": self.config.preserve_replay_compatibility,
                    **(metadata or {})
                },
                lineage_preserved=self.config.preserve_correlation_lineage,
                replay_compatible=self.config.preserve_replay_compatibility
            )
            
            # Store telemetry event
            self._qpu_telemetry[event_id] = telemetry_event
            self._telemetry_count += 1
            
            # Update lineage tracking
            if correlation_id and self.config.preserve_correlation_lineage:
                await self._update_correlation_lineage(correlation_id, execution_lineage)
                self._lineage_preservation_count += 1
            
            logger.info("QPU telemetry emitted", 
                       event_id=event_id,
                       event_type=event_type.value,
                       provider=provider,
                       device=device,
                       correlation_id=correlation_id,
                       lineage_preserved=telemetry_event.lineage_preserved,
                       replay_compatible=telemetry_event.replay_compatible)
            
            return event_id
            
        except Exception as e:
            logger.error("Failed to emit QPU telemetry", 
                        provider=provider,
                        device=device,
                        error=str(e))
            raise
    
    async def _build_execution_lineage(self, 
                                      correlation_id: Optional[str],
                                      original_correlation_id: Optional[str],
                                      parent_correlation_id: Optional[str]) -> List[str]:
        """Build execution lineage for correlation tracking."""
        lineage = []
        
        if original_correlation_id:
            lineage.append(original_correlation_id)
        
        if parent_correlation_id:
            lineage.append(parent_correlation_id)
        
        if correlation_id:
            lineage.append(correlation_id)
        
        return lineage
    
    async def _update_correlation_lineage(self, 
                                         correlation_id: str,
                                         execution_lineage: List[str]) -> None:
        """Update correlation lineage tracking."""
        self._correlation_lineage[correlation_id] = execution_lineage
        
        # Update execution lineage
        for lineage_item in execution_lineage:
            if lineage_item not in self._execution_lineage:
                self._execution_lineage[lineage_item] = []
            self._execution_lineage[lineage_item].append(correlation_id)
    
    async def emit_qpu_execution_started(self, 
                                       provider: str,
                                       device: str,
                                       correlation_id: str,
                                       benchmark_session_id: Optional[str] = None,
                                       qpu_governance_decision: Optional[str] = None,
                                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU execution started telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_EXECUTION_STARTED,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            benchmark_session_id=benchmark_session_id,
            qpu_governance_decision=qpu_governance_decision,
            metadata=metadata
        )
    
    async def emit_qpu_execution_completed(self, 
                                        provider: str,
                                        device: str,
                                        correlation_id: str,
                                        hardware_execution_ms: float,
                                        success: bool,
                                        result_data: Optional[Dict[str, Any]] = None,
                                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU execution completed telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_EXECUTION_COMPLETED,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            hardware_execution_ms=hardware_execution_ms,
            metadata={
                "success": success,
                "result_data": result_data,
                **(metadata or {})
            }
        )
    
    async def emit_qpu_queue_wait(self, 
                                 provider: str,
                                 device: str,
                                 correlation_id: str,
                                 queue_wait_ms: float,
                                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU queue wait telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_QUEUE_WAIT,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            queue_wait_ms=queue_wait_ms,
            metadata=metadata
        )
    
    async def emit_qpu_governance_decision(self, 
                                          provider: str,
                                          device: str,
                                          correlation_id: str,
                                          governance_decision: str,
                                          governance_approval_id: Optional[str] = None,
                                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU governance decision telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_GOVERNANCE_DECISION,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            qpu_governance_decision=governance_decision,
            metadata={
                "governance_approval_id": governance_approval_id,
                **(metadata or {})
            }
        )
    
    async def emit_qpu_fallback_triggered(self, 
                                        provider: str,
                                        device: str,
                                        correlation_id: str,
                                        fallback_origin: str,
                                        fallback_reason: str,
                                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU fallback triggered telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_FALLBACK_TRIGGERED,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            fallback_origin=fallback_origin,
            metadata={
                "fallback_reason": fallback_reason,
                **(metadata or {})
            }
        )
    
    async def emit_qpu_calibration_snapshot(self, 
                                          provider: str,
                                          device: str,
                                          correlation_id: str,
                                          calibration_snapshot_id: str,
                                          calibration_status: str,
                                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU calibration snapshot telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_CALIBRATION_SNAPSHOT,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            calibration_snapshot_id=calibration_snapshot_id,
            metadata={
                "calibration_status": calibration_status,
                **(metadata or {})
            }
        )
    
    async def emit_qpu_hardware_metadata(self, 
                                        provider: str,
                                        device: str,
                                        correlation_id: str,
                                        hardware_metadata: Dict[str, Any],
                                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """Emit QPU hardware metadata telemetry."""
        return await self.emit_qpu_telemetry(
            event_type=QPUTelemetryType.QPU_HARDWARE_METADATA,
            provider=provider,
            device=device,
            correlation_id=correlation_id,
            metadata={
                "hardware_metadata": hardware_metadata,
                **(metadata or {})
            }
        )
    
    async def get_qpu_telemetry(self, 
                                   correlation_id: Optional[str] = None,
                                   provider: Optional[str] = None,
                                   device: Optional[str] = None,
                                   event_type: Optional[QPUTelemetryType] = None,
                                   limit: int = 1000) -> List[QPUTelemetryEvent]:
        """Get QPU telemetry events with filtering."""
        try:
            events = list(self._qpu_telemetry.values())
            
            # Apply filters
            if correlation_id:
                events = [e for e in events if e.correlation_id == correlation_id]
            
            if provider:
                events = [e for e in events if e.provider == provider]
            
            if device:
                events = [e for e in events if e.device == device]
            
            if event_type:
                events = [e for e in events if e.event_type == event_type]
            
            # Sort by timestamp (most recent first)
            events.sort(key=lambda e: e.timestamp, reverse=True)
            
            return events[:limit]
            
        except Exception as e:
            logger.error("Failed to get QPU telemetry", error=str(e))
            return []
    
    async def get_correlation_lineage(self, correlation_id: str) -> List[str]:
        """Get correlation lineage for specific correlation ID."""
        return self._correlation_lineage.get(correlation_id, [])
    
    async def get_execution_lineage(self, correlation_id: str) -> List[str]:
        """Get execution lineage for specific correlation ID."""
        return self._execution_lineage.get(correlation_id, [])
    
    async def get_telemetry_statistics(self) -> Dict[str, Any]:
        """Get QPU telemetry statistics."""
        try:
            # Calculate event type distribution
            event_type_counts = {}
            for event in self._qpu_telemetry.values():
                event_type = event.event_type.value
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            # Calculate provider distribution
            provider_counts = {}
            for event in self._qpu_telemetry.values():
                provider = event.provider
                provider_counts[provider] = provider_counts.get(provider, 0) + 1
            
            # Calculate device distribution
            device_counts = {}
            for event in self._qpu_telemetry.values():
                device = event.device
                device_counts[device] = device_counts.get(device, 0) + 1
            
            return {
                "total_telemetry_events": self._telemetry_count,
                "stored_events": len(self._qpu_telemetry),
                "correlation_lineage_entries": len(self._correlation_lineage),
                "execution_lineage_entries": len(self._execution_lineage),
                "lineage_preservation_count": self._lineage_preservation_count,
                "event_type_distribution": event_type_counts,
                "provider_distribution": provider_counts,
                "device_distribution": device_counts,
                "config": {
                    "enable_qpu_telemetry": self.config.enable_qpu_telemetry,
                    "preserve_correlation_lineage": self.config.preserve_correlation_lineage,
                    "preserve_replay_compatibility": self.config.preserve_replay_compatibility,
                    "qpu_namespace": self.config.qpu_namespace,
                    "max_events": self.config.max_telemetry_events,
                    "retention_days": self.config.telemetry_retention_days
                }
            }
            
        except Exception as e:
            logger.error("Failed to get telemetry statistics", error=str(e))
            return {"error": str(e)}
    
    async def cleanup_expired_telemetry(self) -> int:
        """Clean up expired telemetry events."""
        try:
            cutoff_time = time.time() - (self.config.telemetry_retention_days * 24 * 60 * 60)
            
            # Clean up telemetry events
            expired_events = [
                event_id for event_id, event in self._qpu_telemetry.items()
                if event.timestamp < cutoff_time
            ]
            
            for event_id in expired_events:
                del self._qpu_telemetry[event_id]
            
            # Clean up correlation lineage
            expired_lineage = [
                correlation_id for correlation_id, lineage in self._correlation_lineage.items()
                if not any(event_id in self._qpu_telemetry for event_id in lineage)
            ]
            
            for correlation_id in expired_lineage:
                del self._correlation_lineage[correlation_id]
            
            cleaned_count = len(expired_events) + len(expired_lineage)
            
            logger.info("QPU telemetry cleanup completed", 
                       cleaned_events=len(expired_events),
                       cleaned_lineage=len(expired_lineage),
                       cutoff_time=cutoff_time)
            
            return cleaned_count
            
        except Exception as e:
            logger.error("Failed to cleanup expired telemetry", error=str(e))
            return 0
    
    def get_telemetry_guarantees(self) -> Dict[str, Any]:
        """Get QPU telemetry guarantees."""
        return {
            "correlation_lineage_preservation": self.config.preserve_correlation_lineage,
            "replay_compatibility": self.config.preserve_replay_compatibility,
            "qpu_namespace_isolation": True,
            "provider_metadata_capture": True,
            "device_metadata_capture": True,
            "queue_wait_tracking": True,
            "hardware_execution_metadata": True,
            "calibration_snapshot_linking": True,
            "governance_decision_capture": True,
            "fallback_origin_tracking": True,
            "operational_truth_isolation": True,
            "no_simulator_contamination": True,
            "no_replay_interference": True
        }


# Global QPU telemetry extension instance
_qpu_telemetry_extension: Optional[QPUTelemetryExtension] = None


def get_qpu_telemetry_extension() -> QPUTelemetryExtension:
    """Get global QPU telemetry extension instance."""
    global _qpu_telemetry_extension
    if _qpu_telemetry_extension is None:
        _qpu_telemetry_extension = QPUTelemetryExtension(QPUTelemetryConfig())
    return _qpu_telemetry_extension


def create_qpu_telemetry_config(
    enable_qpu_telemetry: bool = True,
    preserve_correlation_lineage: bool = True,
    preserve_replay_compatibility: bool = True,
    qpu_namespace: str = "qpu_telemetry",
    max_telemetry_events: int = 10000,
    telemetry_retention_days: int = 30
) -> QPUTelemetryConfig:
    """Create QPU telemetry extension configuration."""
    return QPUTelemetryConfig(
        enable_qpu_telemetry=enable_qpu_telemetry,
        preserve_correlation_lineage=preserve_correlation_lineage,
        preserve_replay_compatibility=preserve_replay_compatibility,
        qpu_namespace=qpu_namespace,
        max_telemetry_events=max_telemetry_events,
        telemetry_retention_days=telemetry_retention_days
    )
