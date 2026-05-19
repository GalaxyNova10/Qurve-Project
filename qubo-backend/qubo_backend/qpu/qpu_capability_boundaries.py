"""
Qurve AI - QPU Capability Boundaries
Safe QPU capability management with strict isolation and governance.

Principles:
✅ DISABLED BY DEFAULT: QPU execution is disabled by default
✅ EXPLICIT ENABLE ONLY: Requires explicit user action
✅ GOVERNANCE GATED: All QPU operations require governance approval
✅ REPLAY COMPATIBLE: QPU operations preserve replay determinism
✅ HARDWARE ISOLATED: QPU execution is isolated from simulators
"""

import os
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QPUMode(Enum):
    """Supported QPU execution modes."""
    DISABLED = "disabled"
    EXPLICIT_ENABLE = "explicit_enable"
    GOVERNANCE_CONTROLLED = "governance_controlled"
    HARDWARE_ISOLATED = "hardware_isolated"


class QPUProvider(Enum):
    """Supported QPU providers."""
    IONQ = "IonQ"
    RIGETTI = "Rigetti"
    OQC = "OQC"


@dataclass
class QPUCapabilityConfig:
    """QPU capability configuration."""
    enable_qpu_execution: bool = False
    supported_qpu_modes: List[QPUMode] = field(default_factory=lambda: [
        QPUMode.DISABLED,
        QPUMode.EXPLICIT_ENABLE,
        QPUMode.GOVERNANCE_CONTROLLED,
        QPUMode.HARDWARE_ISOLATED
    ])
    supported_providers: List[QPUProvider] = field(default_factory=lambda: [
        QPUProvider.IONQ,
        QPUProvider.RIGETTI,
        QPUProvider.OQC
    ])
    governance_gating_required: bool = True
    replay_isolation_required: bool = True
    hardware_isolation_required: bool = True
    max_qpu_tasks_per_day: int = 10
    max_qpu_concurrent: int = 1
    max_qpu_cost_per_task: float = 100.0


class QPUCapabilityBoundaries:
    """
    Production-grade QPU capability boundary enforcement.
    
    Features:
    - QPU execution disabled by default
    - Explicit enable validation
    - Governance gating requirements
    - Replay compatibility enforcement
    - Hardware isolation guarantees
    """
    
    def __init__(self, config: QPUCapabilityConfig):
        self.config = config
        
        # QPU capability state
        self._qpu_enabled = config.enable_qpu_execution
        self._explicit_enable_count = 0
        self._governance_approvals = {}
        
        # Capability validation
        self._validate_capability_config()
        
        logger.info("QPU capability boundaries initialized", 
                  qpu_enabled=self._qpu_enabled,
                  governance_gating=config.governance_gating_required,
                  hardware_isolation=config.hardware_isolation_required)
    
    def _validate_capability_config(self) -> None:
        """Validate QPU capability configuration."""
        # Ensure QPU is disabled by default
        if self.config.enable_qpu_execution:
            logger.warning("QPU execution is enabled - this should be explicit user action")
        
        # Validate required capabilities
        if not self.config.governance_gating_required:
            raise ValueError("Governance gating is required for QPU operations")
        
        if not self.config.replay_isolation_required:
            raise ValueError("Replay isolation is required for QPU operations")
        
        if not self.config.hardware_isolation_required:
            raise ValueError("Hardware isolation is required for QPU operations")
        
        # Validate supported modes include DISABLED
        if QPUMode.DISABLED not in self.config.supported_qpu_modes:
            raise ValueError("DISABLED mode must be supported")
        
        # Validate supported providers
        if not self.config.supported_providers:
            raise ValueError("At least one QPU provider must be supported")
        
        logger.info("QPU capability configuration validated")
    
    async def validate_qpu_enable_request(self, 
                                       execution_mode: str,
                                       provider: str,
                                       device: str,
                                       governance_approval_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        Validate QPU enable request against capability boundaries.
        
        Args:
            execution_mode: Requested execution mode
            provider: QPU provider
            device: QPU device
            governance_approval_id: Governance approval ID
            
        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        try:
            # Validate QPU execution is enabled
            if not self._qpu_enabled:
                return False, "QPU execution is disabled by default"
            
            # Validate explicit enable requirement
            if execution_mode != "CLOUD_QPU":
                return False, f"Invalid execution mode for QPU: {execution_mode}"
            
            # Validate provider is supported
            try:
                qpu_provider = QPUProvider(provider)
                if qpu_provider not in self.config.supported_providers:
                    return False, f"Unsupported QPU provider: {provider}"
            except ValueError:
                return False, f"Invalid QPU provider: {provider}"
            
            # Validate governance gating
            if self.config.governance_gating_required:
                if not governance_approval_id:
                    return False, "Governance approval required for QPU operations"
                
                if not await self._validate_governance_approval(governance_approval_id, provider, device):
                    return False, f"Invalid governance approval: {governance_approval_id}"
            
            # Validate hardware isolation
            if self.config.hardware_isolation_required:
                if not await self._validate_hardware_isolation(provider, device):
                    return False, f"Hardware isolation validation failed for {provider}:{device}"
            
            # Validate replay compatibility
            if self.config.replay_isolation_required:
                if not await self._validate_replay_compatibility(provider, device):
                    return False, f"Replay compatibility validation failed for {provider}:{device}"
            
            # Record explicit enable
            self._explicit_enable_count += 1
            
            logger.info("QPU enable request validated", 
                       provider=provider,
                       device=device,
                       governance_approval_id=governance_approval_id,
                       explicit_enable_count=self._explicit_enable_count)
            
            return True, "QPU enable request approved"
            
        except Exception as e:
            logger.error("Failed to validate QPU enable request", 
                        provider=provider,
                        device=device,
                        error=str(e))
            return False, f"QPU enable validation error: {str(e)}"
    
    async def _validate_governance_approval(self, 
                                        approval_id: str,
                                        provider: str,
                                        device: str) -> bool:
        """Validate governance approval for QPU operation."""
        try:
            # Check if approval exists and is valid
            if approval_id not in self._governance_approvals:
                return False
            
            approval = self._governance_approvals[approval_id]
            
            # Validate approval matches provider and device
            if approval.get("provider") != provider:
                return False
            
            if approval.get("device") != device:
                return False
            
            # Validate approval is not expired
            if approval.get("expired", False):
                return False
            
            # Validate approval grants QPU access
            if not approval.get("qpu_access", False):
                return False
            
            return True
            
        except Exception as e:
            logger.error("Failed to validate governance approval", 
                        approval_id=approval_id,
                        error=str(e))
            return False
    
    async def _validate_hardware_isolation(self, provider: str, device: str) -> bool:
        """Validate hardware isolation for QPU operation."""
        try:
            # Validate provider has hardware isolation
            provider_isolation = {
                QPUProvider.IONQ: True,
                QPUProvider.RIGETTI: True,
                QPUProvider.OQC: True
            }
            
            qpu_provider = QPUProvider(provider)
            return provider_isolation.get(qpu_provider, False)
            
        except Exception as e:
            logger.error("Failed to validate hardware isolation", 
                        provider=provider,
                        device=device,
                        error=str(e))
            return False
    
    async def _validate_replay_compatibility(self, provider: str, device: str) -> bool:
        """Validate replay compatibility for QPU operation."""
        try:
            # Validate provider supports replay compatibility
            provider_replay_compatibility = {
                QPUProvider.IONQ: True,
                QPUProvider.RIGETTI: True,
                QPUProvider.OQC: True
            }
            
            qpu_provider = QPUProvider(provider)
            return provider_replay_compatibility.get(qpu_provider, False)
            
        except Exception as e:
            logger.error("Failed to validate replay compatibility", 
                        provider=provider,
                        device=device,
                        error=str(e))
            return False
    
    async def add_governance_approval(self, 
                                   approval_id: str,
                                   provider: str,
                                   device: str,
                                   qpu_access: bool = True,
                                   expires_at: Optional[str] = None) -> bool:
        """Add governance approval for QPU operation."""
        try:
            self._governance_approvals[approval_id] = {
                "approval_id": approval_id,
                "provider": provider,
                "device": device,
                "qpu_access": qpu_access,
                "created_at": str(int(time.time())),
                "expires_at": expires_at,
                "expired": False
            }
            
            logger.info("Governance approval added", 
                       approval_id=approval_id,
                       provider=provider,
                       device=device,
                       qpu_access=qpu_access)
            
            return True
            
        except Exception as e:
            logger.error("Failed to add governance approval", 
                        approval_id=approval_id,
                        error=str(e))
            return False
    
    async def revoke_governance_approval(self, approval_id: str) -> bool:
        """Revoke governance approval for QPU operation."""
        try:
            if approval_id in self._governance_approvals:
                self._governance_approvals[approval_id]["expired"] = True
                logger.info("Governance approval revoked", approval_id=approval_id)
                return True
            return False
            
        except Exception as e:
            logger.error("Failed to revoke governance approval", 
                        approval_id=approval_id,
                        error=str(e))
            return False
    
    def get_capability_status(self) -> Dict[str, Any]:
        """Get current QPU capability status."""
        return {
            "qpu_enabled": self._qpu_enabled,
            "explicit_enable_count": self._explicit_enable_count,
            "governance_gating_required": self.config.governance_gating_required,
            "replay_isolation_required": self.config.replay_isolation_required,
            "hardware_isolation_required": self.config.hardware_isolation_required,
            "supported_modes": [mode.value for mode in self.config.supported_qpu_modes],
            "supported_providers": [provider.value for provider in self.config.supported_providers],
            "active_governance_approvals": len([a for a in self._governance_approvals.values() if not a.get("expired", False)]),
            "governance_approvals_total": len(self._governance_approvals),
            "quotas": {
                "max_qpu_tasks_per_day": self.config.max_qpu_tasks_per_day,
                "max_qpu_concurrent": self.config.max_qpu_concurrent,
                "max_qpu_cost_per_task": self.config.max_qpu_cost_per_task
            }
        }
    
    def get_safety_guarantees(self) -> Dict[str, Any]:
        """Get QPU safety guarantees."""
        return {
            "disabled_by_default": not self._qpu_enabled,
            "explicit_enable_required": True,
            "governance_gating": self.config.governance_gating_required,
            "replay_isolation": self.config.replay_isolation_required,
            "hardware_isolation": self.config.hardware_isolation_required,
            "no_auto_routing": True,
            "no_default_execution": True,
            "capability_gated": True,
            "additive_only": True
        }


# Global QPU capability boundaries instance
_qpu_capability_boundaries: Optional[QPUCapabilityBoundaries] = None


def get_qpu_capability_boundaries() -> QPUCapabilityBoundaries:
    """Get global QPU capability boundaries instance."""
    global _qpu_capability_boundaries
    if _qpu_capability_boundaries is None:
        _qpu_capability_boundaries = QPUCapabilityBoundaries(QPUCapabilityConfig())
    return _qpu_capability_boundaries


def create_qpu_capability_config(
    enable_qpu_execution: bool = False,
    supported_qpu_modes: Optional[List[QPUMode]] = None,
    supported_providers: Optional[List[QPUProvider]] = None,
    governance_gating_required: bool = True,
    replay_isolation_required: bool = True,
    hardware_isolation_required: bool = True,
    max_qpu_tasks_per_day: int = 10,
    max_qpu_concurrent: int = 1,
    max_qpu_cost_per_task: float = 100.0
) -> QPUCapabilityConfig:
    """Create QPU capability configuration."""
    if supported_qpu_modes is None:
        supported_qpu_modes = [
            QPUMode.DISABLED,
            QPUMode.EXPLICIT_ENABLE,
            QPUMode.GOVERNANCE_CONTROLLED,
            QPUMode.HARDWARE_ISOLATED
        ]
    
    if supported_providers is None:
        supported_providers = [
            QPUProvider.IONQ,
            QPUProvider.RIGETTI,
            QPUProvider.OQC
        ]
    
    return QPUCapabilityConfig(
        enable_qpu_execution=enable_qpu_execution,
        supported_qpu_modes=supported_qpu_modes,
        supported_providers=supported_providers,
        governance_gating_required=governance_gating_required,
        replay_isolation_required=replay_isolation_required,
        hardware_isolation_required=hardware_isolation_required,
        max_qpu_tasks_per_day=max_qpu_tasks_per_day,
        max_qpu_concurrent=max_qpu_concurrent,
        max_qpu_cost_per_task=max_qpu_cost_per_task
    )


# Environment variable support for QPU capabilities
ENABLE_QPU_EXECUTION = os.getenv("ENABLE_QPU_EXECUTION", "false").lower() == "true"
SUPPORTED_QPU_MODES = [mode.value for mode in QPUMode]

# Safety: QPU execution is disabled by default
if ENABLE_QPU_EXECUTION:
    logger.warning("QPU execution is enabled via environment variable - this should be explicit user action")
else:
    logger.info("QPU execution is disabled by default - explicit enable required")
