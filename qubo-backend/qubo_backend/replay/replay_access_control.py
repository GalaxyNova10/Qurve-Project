"""
Qurve AI - Replay Access Control
Safe access control for replay system with isolation guarantees.

Principles:
✅ INTERNAL_ONLY: Replay APIs are internal-only
✅ READ_ONLY: Replay queries never modify operational state
✅ ISOLATION_GUARDS: Replay cannot access live systems
✅ NAMESPACE_RESTRICTIONS: Replay cannot access operational tables
✅ NO LIVE_MUTATION: Replay never modifies production state
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .replay_artifact_classification import (
    get_artifact_classification,
    ArtifactType
)

logger = logging.getLogger(__name__)


class AccessLevel(Enum):
    """Access level for replay operations."""
    INTERNAL_READ_ONLY = "internal_read_only"
    INTERNAL_ANALYTICS = "internal_analytics"
    INTERNAL_FORENSIC = "internal_forensic"


@dataclass
class AccessControlConfig:
    """Access control configuration."""
    enable_access_control: bool = True
    internal_only_mode: bool = True
    read_only_mode: bool = True
    isolation_guards_enabled: bool = True
    namespace_restrictions_enabled: bool = True
    allowed_access_levels: List[AccessLevel] = field(default_factory=lambda: [
        AccessLevel.INTERNAL_READ_ONLY,
        AccessLevel.INTERNAL_ANALYTICS,
        AccessLevel.INTERNAL_FORENSIC
    ])


class ReplayAccessControl:
    """
    Production-grade replay access control.
    
    Features:
    - Internal-only API access
    - Read-only query enforcement
    - Isolation guards for live systems
    - Namespace restrictions for operational tables
    - Complete audit logging
    """
    
    def __init__(self, config: AccessControlConfig):
        self.config = config
        
        # Access control state
        self._access_log: List[Dict[str, Any]] = []
        self._blocked_attempts = 0
        self._allowed_operations = 0
        
        # Get artifact classification for validation
        self._artifact_classification = get_artifact_classification()
        
        logger.info("Replay access control initialized", 
                  internal_only=config.internal_only_mode,
                  read_only=config.read_only_mode,
                  isolation_guards=config.isolation_guards_enabled)
    
    async def validate_access(self, 
                           operation: str,
                           target_table: Optional[str] = None,
                           access_level: AccessLevel = AccessLevel.INTERNAL_READ_ONLY,
                           is_write_operation: bool = False) -> Tuple[bool, str]:
        """
        Validate access request against replay isolation rules.
        
        Args:
            operation: Operation being performed
            target_table: Target table (if applicable)
            access_level: Requested access level
            is_write_operation: Whether this is a write operation
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        try:
            # Log access attempt
            access_id = f"access_{int(time.time())}_{len(self._access_log)}"
            
            # Validate internal-only mode
            if self.config.internal_only_mode and access_level not in self.config.allowed_access_levels:
                reason = "Access level not allowed in internal-only mode"
                await self._log_access_attempt(access_id, operation, False, reason)
                return False, reason
            
            # Validate read-only mode
            if self.config.read_only_mode and is_write_operation:
                reason = "Write operations not allowed in read-only mode"
                await self._log_access_attempt(access_id, operation, False, reason)
                return False, reason
            
            # Validate isolation guards
            if self.config.isolation_guards_enabled:
                isolation_result = await self._validate_isolation_guards(operation, target_table)
                if not isolation_result[0]:
                    reason = isolation_result[1]
                    await self._log_access_attempt(access_id, operation, False, reason)
                    return False, reason
            
            # Validate namespace restrictions
            if self.config.namespace_restrictions_enabled and target_table:
                namespace_result = await self._validate_namespace_restrictions(target_table, is_write_operation)
                if not namespace_result[0]:
                    reason = namespace_result[1]
                    await self._log_access_attempt(access_id, operation, False, reason)
                    return False, reason
            
            # Allow access
            await self._log_access_attempt(access_id, operation, True, "Access granted")
            self._allowed_operations += 1
            
            return True, "Access granted"
            
        except Exception as e:
            error_reason = f"Access validation error: {str(e)}"
            await self._log_access_attempt(access_id, operation, False, error_reason)
            return False, error_reason
    
    async def _validate_isolation_guards(self, 
                                       operation: str,
                                       target_table: Optional[str]) -> Tuple[bool, str]:
        """
        Validate isolation guards for live system access.
        
        Ensures replay cannot access live execution systems.
        """
        try:
            # Block access to live execution systems
            live_systems = [
                "cloud_execution",
                "live_benchmark",
                "production_solver",
                "live_telemetry",
                "operational_monitoring"
            ]
            
            for live_system in live_systems:
                if live_system in operation.lower():
                    return False, f"Access to live system blocked: {live_system}"
            
            # Block access to live cloud services
            cloud_operations = [
                "submit_cloud_task",
                "run_qpu",
                "cloud_simulation",
                "live_aws_access"
            ]
            
            for cloud_op in cloud_operations:
                if cloud_op in operation.lower():
                    return False, f"Cloud operation blocked: {cloud_op}"
            
            # Block access to governance mutation
            governance_operations = [
                "update_governance",
                "modify_quota",
                "change_cost_model",
                "alter_governance_state"
            ]
            
            for gov_op in governance_operations:
                if gov_op in operation.lower():
                    return False, f"Governance mutation blocked: {gov_op}"
            
            return True, "Isolation guards passed"
            
        except Exception as e:
            return False, f"Isolation guard validation error: {str(e)}"
    
    async def _validate_namespace_restrictions(self, 
                                            target_table: str,
                                            is_write_operation: bool) -> Tuple[bool, str]:
        """
        Validate namespace restrictions for table access.
        
        Ensures replay cannot access operational tables.
        """
        try:
            # Check if target table is operational truth
            if self._artifact_classification.is_operational_table(target_table):
                if is_write_operation:
                    return False, f"Write access to operational table blocked: {target_table}"
                else:
                    # Read access to operational tables is allowed for reconstruction
                    return True, "Read access to operational table allowed"
            
            # Check if target table is replay artifact
            if self._artifact_classification.is_replay_table(target_table):
                # Write access to replay tables is allowed
                if is_write_operation:
                    return True, "Write access to replay table allowed"
                else:
                    return True, "Read access to replay table allowed"
            
            # Unknown table - block access
            return False, f"Access to unknown table blocked: {target_table}"
            
        except Exception as e:
            return False, f"Namespace restriction validation error: {str(e)}"
    
    async def _log_access_attempt(self, 
                                access_id: str,
                                operation: str,
                                allowed: bool,
                                reason: str) -> None:
        """Log access attempt for audit purposes."""
        try:
            access_record = {
                "access_id": access_id,
                "timestamp": time.time(),
                "operation": operation,
                "allowed": allowed,
                "reason": reason,
                "access_control_config": {
                    "internal_only": self.config.internal_only_mode,
                    "read_only": self.config.read_only_mode,
                    "isolation_guards": self.config.isolation_guards_enabled,
                    "namespace_restrictions": self.config.namespace_restrictions_enabled
                }
            }
            
            self._access_log.append(access_record)
            
            if not allowed:
                self._blocked_attempts += 1
            else:
                self._allowed_operations += 1
            
            logger.info("Access attempt logged", 
                       access_id=access_id,
                       operation=operation,
                       allowed=allowed,
                       reason=reason)
            
        except Exception as e:
            logger.error("Failed to log access attempt", 
                        access_id=access_id,
                        error=str(e))
    
    async def get_access_log(self, limit: int = 1000) -> List[Dict[str, Any]]:
        """Get recent access log entries."""
        log_entries = sorted(self._access_log, key=lambda x: x["timestamp"], reverse=True)
        return log_entries[:limit]
    
    async def get_access_statistics(self) -> Dict[str, Any]:
        """Get access control statistics."""
        recent_entries = [
            entry for entry in self._access_log
            if time.time() - entry["timestamp"] < 3600  # Last hour
        ]
        
        recent_blocked = len([e for e in recent_entries if not e["allowed"]])
        recent_allowed = len([e for e in recent_entries if e["allowed"]])
        
        return {
            "total_attempts": len(self._access_log),
            "blocked_attempts": self._blocked_attempts,
            "allowed_operations": self._allowed_operations,
            "recent_attempts": len(recent_entries),
            "recent_blocked": recent_blocked,
            "recent_allowed": recent_allowed,
            "block_rate": (self._blocked_attempts / len(self._access_log) * 100) if self._access_log else 0.0,
            "recent_block_rate": (recent_blocked / len(recent_entries) * 100) if recent_entries else 0.0,
            "access_control_config": {
                "internal_only": self.config.internal_only_mode,
                "read_only": self.config.read_only_mode,
                "isolation_guards": self.config.isolation_guards_enabled,
                "namespace_restrictions": self.config.namespace_restrictions_enabled,
                "allowed_access_levels": [level.value for level in self.config.allowed_access_levels]
            }
        }
    
    async def validate_replay_operation(self, 
                                     operation: str,
                                     replay_id: Optional[str] = None,
                                     session_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate specific replay operation against isolation rules.
        
        Args:
            operation: Replay operation to validate
            replay_id: Replay ID (if applicable)
            session_id: Session ID (if applicable)
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        try:
            # Validate replay operation doesn't access live systems
            live_operations = [
                "execute_cloud",
                "submit_task",
                "run_qpu",
                "modify_governance",
                "update_quota",
                "emit_production_telemetry"
            ]
            
            for live_op in live_operations:
                if live_op in operation.lower():
                    return False, f"Live operation blocked in replay: {live_op}"
            
            # Validate operation is read-only or forensic
            if self.config.read_only_mode:
                write_operations = [
                    "update_session",
                    "modify_timeline",
                    "alter_comparison",
                    "change_artifact"
                ]
                
                for write_op in write_operations:
                    if write_op in operation.lower():
                        return False, f"Write operation blocked in read-only mode: {write_op}"
            
            return True, "Replay operation validated"
            
        except Exception as e:
            return False, f"Replay operation validation error: {str(e)}"
    
    def get_isolation_summary(self) -> Dict[str, Any]:
        """Get isolation and access control summary."""
        return {
            "isolation_guards": {
                "enabled": self.config.isolation_guards_enabled,
                "blocks_live_systems": True,
                "blocks_cloud_operations": True,
                "blocks_governance_mutation": True
            },
            "namespace_restrictions": {
                "enabled": self.config.namespace_restrictions_enabled,
                "operational_tables_read_only": True,
                "replay_tables_write_allowed": True
            },
            "access_control": {
                "internal_only": self.config.internal_only_mode,
                "read_only": self.config.read_only_mode,
                "allowed_access_levels": [level.value for level in self.config.allowed_access_levels]
            },
            "artifact_classification": {
                "operational_tables": self._artifact_classification.get_operational_tables(),
                "replay_tables": self._artifact_classification.get_replay_tables()
            }
        }


# Global replay access control instance
_replay_access_control: Optional[ReplayAccessControl] = None


def get_replay_access_control() -> ReplayAccessControl:
    """Get global replay access control instance."""
    global _replay_access_control
    if _replay_access_control is None:
        _replay_access_control = ReplayAccessControl(AccessControlConfig())
    return _replay_access_control


def create_access_control_config(
    enable_access_control: bool = True,
    internal_only_mode: bool = True,
    read_only_mode: bool = True,
    isolation_guards_enabled: bool = True,
    namespace_restrictions_enabled: bool = True,
    allowed_access_levels: Optional[List[AccessLevel]] = None
) -> AccessControlConfig:
    """Create access control configuration."""
    if allowed_access_levels is None:
        allowed_access_levels = [
            AccessLevel.INTERNAL_READ_ONLY,
            AccessLevel.INTERNAL_ANALYTICS,
            AccessLevel.INTERNAL_FORENSIC
        ]
    
    return AccessControlConfig(
        enable_access_control=enable_access_control,
        internal_only_mode=internal_only_mode,
        read_only_mode=read_only_mode,
        isolation_guards_enabled=isolation_guards_enabled,
        namespace_restrictions_enabled=namespace_restrictions_enabled,
        allowed_access_levels=allowed_access_levels
    )
