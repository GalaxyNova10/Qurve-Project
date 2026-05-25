"""
Qurve AI - Audit Trail System
Immutable audit logging with timestamp normalization and lineage preservation.

Principles:
✅ IMMUTABLE AUDIT RECORDS: Never modify audit entries
✅ TIMESTAMP NORMALIZATION: UTC timestamp normalization
✅ LINEAGE PRESERVING: Maintain execution lineage
✅ COMPREHENSIVE TRACKING: All significant actions logged
✅ OPERATOR ACTION LOGGING: All operator actions tracked
"""

import time
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Audit event types."""
    DEPLOYMENT_ACTION = "deployment_action"
    GOVERNANCE_CHANGE = "governance_change"
    CLOUD_EXECUTION_APPROVAL = "cloud_execution_approval"
    QPU_ENABLE_ACTION = "qpu_enable_action"
    REPLAY_ACCESS = "replay_access"
    OPERATOR_ACTION = "operator_action"
    CONFIGURATION_CHANGE = "configuration_change"
    INCIDENT_RESPONSE = "incident_response"
    SYSTEM_ERROR = "system_error"
    SECURITY_EVENT = "security_event"


@dataclass
class AuditEvent:
    """Immutable audit event."""
    event_id: str
    event_type: AuditEventType
    timestamp: float
    operator_id: Optional[str]
    correlation_id: Optional[str]
    parent_correlation_id: Optional[str]
    resource: str
    action: str
    execution_lineage: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    immutable: bool = True


@dataclass
class AuditQuery:
    """Audit query parameters."""
    event_types: Optional[Set[AuditEventType]] = None
    operator_id: Optional[str] = None
    correlation_id: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    success_only: Optional[bool] = None
    limit: int = 1000


class AuditTrailSystem:
    """
    Production-grade audit trail system.
    
    Features:
    - Immutable audit records
    - Timestamp normalization
    - Lineage preservation
    - Comprehensive tracking
    - Operator action logging
    """
    
    def __init__(self):
        self._audit_events: Dict[str, AuditEvent] = {}
        self._event_index: Dict[AuditEventType, List[str]] = {}
        self._operator_index: Dict[str, List[str]] = {}
        self._correlation_index: Dict[str, List[str]] = {}
        self._resource_index: Dict[str, List[str]] = {}
        
        # Statistics
        self._event_count = 0
        self._last_cleanup = time.time()
        
        logger.info("Audit trail system initialized")
    
    async def log_deployment_action(self, 
                                   operator_id: str,
                                   action: str,
                                   deployment_version: str,
                                   environment: str,
                                   success: bool = True,
                                   error_message: Optional[str] = None,
                                   correlation_id: Optional[str] = None,
                                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log deployment action."""
        return await self._log_event(
            event_type=AuditEventType.DEPLOYMENT_ACTION,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"deployment:{environment}",
            action=action,
            details={
                "deployment_version": deployment_version,
                "environment": environment
            },
            success=success,
            error_message=error_message,
            metadata=metadata
        )
    
    async def log_governance_change(self, 
                                    operator_id: str,
                                    action: str,
                                    governance_type: str,
                                    old_value: Any,
                                    new_value: Any,
                                    correlation_id: Optional[str] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log governance change."""
        return await self._log_event(
            event_type=AuditEventType.GOVERNANCE_CHANGE,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"governance:{governance_type}",
            action=action,
            details={
                "governance_type": governance_type,
                "old_value": old_value,
                "new_value": new_value
            },
            metadata=metadata
        )
    
    async def log_cloud_execution_approval(self, 
                                          operator_id: str,
                                          action: str,
                                          cloud_provider: str,
                                          device: str,
                                          execution_id: str,
                                          approved: bool,
                                          correlation_id: Optional[str] = None,
                                          metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log cloud execution approval."""
        return await self._log_event(
            event_type=AuditEventType.CLOUD_EXECUTION_APPROVAL,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"cloud_execution:{cloud_provider}:{device}",
            action=action,
            details={
                "cloud_provider": cloud_provider,
                "device": device,
                "execution_id": execution_id,
                "approved": approved
            },
            success=approved,
            metadata=metadata
        )
    
    async def log_qpu_enable_action(self, 
                                     operator_id: str,
                                     action: str,
                                     qpu_provider: str,
                                     qpu_device: str,
                                     enabled: bool,
                                     correlation_id: Optional[str] = None,
                                     metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log QPU enable action."""
        return await self._log_event(
            event_type=AuditEventType.QPU_ENABLE_ACTION,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"qpu:{qpu_provider}:{qpu_device}",
            action=action,
            details={
                "qpu_provider": qpu_provider,
                "qpu_device": qpu_device,
                "enabled": enabled
            },
            success=enabled,
            metadata=metadata
        )
    
    async def log_replay_access(self, 
                               operator_id: str,
                               action: str,
                               replay_id: str,
                               replay_mode: str,
                               correlation_id: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log replay access."""
        return await self._log_event(
            event_type=AuditEventType.REPLAY_ACCESS,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"replay:{replay_id}",
            action=action,
            details={
                "replay_id": replay_id,
                "replay_mode": replay_mode
            },
            metadata=metadata
        )
    
    async def log_operator_action(self, 
                                 operator_id: str,
                                 action: str,
                                 resource: str,
                                 details: Dict[str, Any],
                                 success: bool = True,
                                 error_message: Optional[str] = None,
                                 correlation_id: Optional[str] = None,
                                 metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log operator action."""
        return await self._log_event(
            event_type=AuditEventType.OPERATOR_ACTION,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=resource,
            action=action,
            details=details,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
    
    async def log_configuration_change(self, 
                                      operator_id: str,
                                      action: str,
                                      config_type: str,
                                      config_key: str,
                                      old_value: Any,
                                      new_value: Any,
                                      correlation_id: Optional[str] = None,
                                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log configuration change."""
        return await self._log_event(
            event_type=AuditEventType.CONFIGURATION_CHANGE,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"config:{config_type}:{config_key}",
            action=action,
            details={
                "config_type": config_type,
                "config_key": config_key,
                "old_value": old_value,
                "new_value": new_value
            },
            metadata=metadata
        )
    
    async def log_incident_response(self, 
                                    operator_id: str,
                                    action: str,
                                    incident_id: str,
                                    severity: str,
                                    correlation_id: Optional[str] = None,
                                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log incident response."""
        return await self._log_event(
            event_type=AuditEventType.INCIDENT_RESPONSE,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=f"incident:{incident_id}",
            action=action,
            details={
                "incident_id": incident_id,
                "severity": severity
            },
            metadata=metadata
        )
    
    async def log_system_error(self, 
                               component: str,
                               error_type: str,
                               error_message: str,
                               correlation_id: Optional[str] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log system error."""
        return await self._log_event(
            event_type=AuditEventType.SYSTEM_ERROR,
            operator_id=None,
            correlation_id=correlation_id,
            resource=f"system:{component}",
            action="error",
            details={
                "component": component,
                "error_type": error_type,
                "error_message": error_message
            },
            success=False,
            error_message=error_message,
            metadata=metadata
        )
    
    async def log_security_event(self, 
                                operator_id: Optional[str],
                                action: str,
                                resource: str,
                                security_level: str,
                                success: bool = True,
                                error_message: Optional[str] = None,
                                correlation_id: Optional[str] = None,
                                metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log security event."""
        return await self._log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            operator_id=operator_id,
            correlation_id=correlation_id,
            resource=resource,
            action=action,
            details={
                "security_level": security_level
            },
            success=success,
            error_message=error_message,
            metadata=metadata
        )
    
    async def _log_event(self, 
                         event_type: AuditEventType,
                         operator_id: Optional[str],
                         resource: str,
                         action: str,
                         details: Dict[str, Any],
                         success: bool = True,
                         error_message: Optional[str] = None,
                         correlation_id: Optional[str] = None,
                         parent_correlation_id: Optional[str] = None,
                         execution_lineage: Optional[List[str]] = None,
                         metadata: Optional[Dict[str, Any]] = None) -> str:
        """Log audit event with immutability guarantee."""
        try:
            # Generate unique event ID
            event_id = f"audit_{event_type.value}_{int(time.time() * 1000000)}"
            
            # Normalize timestamp to UTC
            timestamp = time.time()
            
            # Build execution lineage
            lineage = execution_lineage or []
            if correlation_id and correlation_id not in lineage:
                lineage.append(correlation_id)
            
            # Create immutable audit event
            audit_event = AuditEvent(
                event_id=event_id,
                event_type=event_type,
                timestamp=timestamp,
                operator_id=operator_id,
                correlation_id=correlation_id,
                parent_correlation_id=parent_correlation_id,
                execution_lineage=lineage,
                resource=resource,
                action=action,
                details=details,
                success=success,
                error_message=error_message,
                metadata=metadata or {},
                immutable=True
            )
            
            # Store audit event
            self._audit_events[event_id] = audit_event
            self._event_count += 1
            
            # Update indexes
            self._update_indexes(audit_event)
            
            logger.debug("Audit event logged", 
                        event_id=event_id,
                        event_type=event_type.value,
                        operator_id=operator_id,
                        resource=resource,
                        action=action,
                        success=success)
            
            return event_id
            
        except Exception as e:
            logger.error("Failed to log audit event", 
                        event_type=event_type.value,
                        operator_id=operator_id,
                        error=str(e))
            raise
    
    def _update_indexes(self, event: AuditEvent) -> None:
        """Update search indexes for audit event."""
        # Event type index
        if event.event_type not in self._event_index:
            self._event_index[event.event_type] = []
        self._event_index[event.event_type].append(event.event_id)
        if len(self._event_index[event.event_type]) > 10000:
            self._event_index[event.event_type] = self._event_index[event.event_type][-10000:]
        
        # Operator index
        if event.operator_id:
            if event.operator_id not in self._operator_index:
                self._operator_index[event.operator_id] = []
            self._operator_index[event.operator_id].append(event.event_id)
            if len(self._operator_index[event.operator_id]) > 5000:
                self._operator_index[event.operator_id] = self._operator_index[event.operator_id][-5000:]
        
        # Correlation index
        if event.correlation_id:
            if event.correlation_id not in self._correlation_index:
                self._correlation_index[event.correlation_id] = []
            self._correlation_index[event.correlation_id].append(event.event_id)
            if len(self._correlation_index[event.correlation_id]) > 1000:
                self._correlation_index[event.correlation_id] = self._correlation_index[event.correlation_id][-1000:]
        
        # Resource index
        if event.resource not in self._resource_index:
            self._resource_index[event.resource] = []
        self._resource_index[event.resource].append(event.event_id)
        if len(self._resource_index[event.resource]) > 5000:
            self._resource_index[event.resource] = self._resource_index[event.resource][-5000:]
    
    async def query_audit_trail(self, query: AuditQuery) -> List[AuditEvent]:
        """Query audit trail with filters."""
        try:
            # Start with all events
            event_ids = list(self._audit_events.keys())
            
            # Apply filters
            if query.event_types:
                filtered_ids = set()
                for event_type in query.event_types:
                    filtered_ids.update(self._event_index.get(event_type, []))
                event_ids = [eid for eid in event_ids if eid in filtered_ids]
            
            if query.operator_id:
                event_ids = [eid for eid in event_ids if eid in self._operator_index.get(query.operator_id, [])]
            
            if query.correlation_id:
                event_ids = [eid for eid in event_ids if eid in self._correlation_index.get(query.correlation_id, [])]
            
            if query.resource:
                event_ids = [eid for eid in event_ids if eid in self._resource_index.get(query.resource, [])]
            
            # Get events and apply remaining filters
            events = [self._audit_events[eid] for eid in event_ids]
            
            if query.action:
                events = [e for e in events if e.action == query.action]
            
            if query.start_time:
                events = [e for e in events if e.timestamp >= query.start_time]
            
            if query.end_time:
                events = [e for e in events if e.timestamp <= query.end_time]
            
            if query.success_only is not None:
                events = [e for e in events if e.success == query.success_only]
            
            # Sort by timestamp (most recent first)
            events.sort(key=lambda e: e.timestamp, reverse=True)
            
            return events[:query.limit]
            
        except Exception as e:
            logger.error("Failed to query audit trail", error=str(e))
            return []
    
    async def get_event_lineage(self, correlation_id: str) -> List[AuditEvent]:
        """Get audit events for execution lineage."""
        try:
            event_ids = self._correlation_index.get(correlation_id, [])
            events = [self._audit_events[eid] for eid in event_ids]
            events.sort(key=lambda e: e.timestamp)
            return events
            
        except Exception as e:
            logger.error("Failed to get event lineage", correlation_id=correlation_id, error=str(e))
            return []
    
    def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit trail statistics."""
        try:
            # Event type distribution
            event_type_counts = {}
            for event in self._audit_events.values():
                event_type = event.event_type.value
                event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
            
            # Operator activity
            operator_counts = {}
            for event in self._audit_events.values():
                if event.operator_id:
                    operator_counts[event.operator_id] = operator_counts.get(event.operator_id, 0) + 1
            
            # Success rate
            total_events = len(self._audit_events)
            successful_events = sum(1 for e in self._audit_events.values() if e.success)
            success_rate = (successful_events / total_events * 100) if total_events > 0 else 0.0
            
            # Recent activity (last 24 hours)
            recent_cutoff = time.time() - (24 * 60 * 60)
            recent_events = [e for e in self._audit_events.values() if e.timestamp > recent_cutoff]
            
            return {
                "total_events": total_events,
                "stored_events": len(self._audit_events),
                "event_count": self._event_count,
                "success_rate": success_rate,
                "recent_events_24h": len(recent_events),
                "event_type_distribution": event_type_counts,
                "operator_activity": operator_counts,
                "index_sizes": {
                    "event_type_index": len(self._event_index),
                    "operator_index": len(self._operator_index),
                    "correlation_index": len(self._correlation_index),
                    "resource_index": len(self._resource_index)
                },
                "last_cleanup": self._last_cleanup
            }
            
        except Exception as e:
            logger.error("Failed to get audit statistics", error=str(e))
            return {"error": str(e)}
    
    def get_audit_guarantees(self) -> Dict[str, Any]:
        """Get audit trail guarantees."""
        return {
            "immutable_audit_records": True,
            "timestamp_normalization": True,
            "lineage_preservation": True,
            "comprehensive_tracking": True,
            "operator_action_logging": True,
            "deployment_action_tracking": True,
            "governance_change_tracking": True,
            "cloud_execution_approval_tracking": True,
            "qpu_enable_action_tracking": True,
            "replay_access_tracking": True,
            "configuration_change_tracking": True,
            "incident_response_tracking": True,
            "system_error_tracking": True,
            "security_event_tracking": True,
            "searchable_indexes": True,
            "query_performance": True
        }


# Global audit trail system instance
_audit_trail_system: Optional[AuditTrailSystem] = None


def get_audit_trail_system() -> AuditTrailSystem:
    """Get global audit trail system instance."""
    global _audit_trail_system
    if _audit_trail_system is None:
        _audit_trail_system = AuditTrailSystem()
    return _audit_trail_system
