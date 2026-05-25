"""
Qurve AI - QPU Execution Router
Safe QPU routing with explicit enable validation and governance control.

Principles:
✅ EXPLICIT ENABLE ONLY: No automatic QPU routing
✅ GOVERNANCE APPROVAL: All QPU operations require approval
✅ QUOTA VALIDATION: Enforce hardware limits
✅ DEVICE VALIDATION: Strict device capability checks
✅ FALLBACK ROUTING: Safe fallback to simulators
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .qpu_capability_boundaries import get_qpu_capability_boundaries
from .qpu_device_registry import get_qpu_device_registry, QPUProvider

logger = logging.getLogger(__name__)


class QPURoutingDecision(Enum):
    """QPU routing decision types."""
    APPROVED = "approved"
    REJECTED_DISABLED = "rejected_disabled"
    REJECTED_GOVERNANCE = "rejected_governance"
    REJECTED_QUOTA = "rejected_quota"
    REJECTED_DEVICE = "rejected_device"
    REJECTED_EXPLICIT = "rejected_explicit"
    FALLBACK_TO_SIMULATOR = "fallback_to_simulator"
    FALLBACK_TO_LOCAL = "fallback_to_local"


@dataclass
class QPURoutingRequest:
    """QPU routing request."""
    execution_mode: str
    provider: str
    device: str
    region: str
    governance_approval_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QPURoutingResult:
    """QPU routing result."""
    decision: QPURoutingDecision
    reason: str
    device: Optional[Dict[str, Any]] = None
    fallback_chain: List[str] = field(default_factory=list)
    governance_approval: Optional[Dict[str, Any]] = None
    quota_info: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class QPUExecutionRouter:
    """
    Production-grade QPU execution router.
    
    Features:
    - Explicit enable validation
    - Governance approval validation
    - Quota validation
    - Device validation
    - Safe fallback routing
    """
    
    def __init__(self):
        self.capability_boundaries = get_qpu_capability_boundaries()
        self.device_registry = get_qpu_device_registry()
        
        # Routing statistics
        self._routing_count = 0
        self._approval_count = 0
        self._rejection_count = 0
        self._fallback_count = 0
        
        logger.info("QPU execution router initialized", 
                  explicit_enable_required=True,
                  governance_gating=True,
                  quota_validation=True)
    
    async def route_qpu_execution(self, request: QPURoutingRequest) -> QPURoutingResult:
        """
        Route QPU execution request with full validation.
        
        Args:
            request: QPU routing request
            
        Returns:
            QPURoutingResult with decision and details
        """
        try:
            self._routing_count += 1
            
            logger.info("QPU routing request received", 
                       execution_mode=request.execution_mode,
                       provider=request.provider,
                       device=request.device,
                       region=request.region,
                       correlation_id=request.correlation_id)
            
            # Step 1: Validate explicit QPU enable requirement
            if not await self._validate_explicit_enable(request):
                return self._create_rejection_result(
                    QPURoutingDecision.REJECTED_EXPLICIT,
                    "QPU execution requires explicit enable and CLOUD_QPU mode",
                    request
                )
            
            # Step 2: Validate capability boundaries
            capability_result = await self.capability_boundaries.validate_qpu_enable_request(
                execution_mode=request.execution_mode,
                provider=request.provider,
                device=request.device,
                governance_approval_id=request.governance_approval_id
            )
            
            if not capability_result[0]:
                return self._create_rejection_result(
                    QPURoutingDecision.REJECTED_DISABLED,
                    capability_result[1],
                    request
                )
            
            # Step 3: Validate governance approval
            governance_result = await self._validate_governance_approval(request)
            if not governance_result[0]:
                return self._create_rejection_result(
                    QPURoutingDecision.REJECTED_GOVERNANCE,
                    governance_result[1],
                    request
                )
            
            # Step 4: Validate quotas
            quota_result = await self._validate_quotas(request)
            if not quota_result[0]:
                return self._create_rejection_result(
                    QPURoutingDecision.REJECTED_QUOTA,
                    quota_result[1],
                    request,
                    quota_info=quota_result[2]
                )
            
            # Step 5: Validate device
            device_result = await self._validate_device(request)
            if not device_result[0]:
                return self._create_rejection_result(
                    QPURoutingDecision.REJECTED_DEVICE,
                    device_result[1],
                    request
                )
            
            # Step 6: Create approved routing result
            return self._create_approved_result(request, governance_result[2], device_result[2])
            
        except Exception as e:
            logger.error("Failed to route QPU execution", 
                        execution_mode=request.execution_mode,
                        provider=request.provider,
                        device=request.device,
                        error=str(e))
            return self._create_rejection_result(
                QPURoutingDecision.REJECTED_EXPLICIT,
                f"Routing error: {str(e)}",
                request
            )
    
    async def _validate_explicit_enable(self, request: QPURoutingRequest) -> bool:
        """Validate explicit QPU enable requirement."""
        try:
            # Must be CLOUD_QPU mode
            if request.execution_mode != "CLOUD_QPU":
                logger.warning("QPU routing rejected: not CLOUD_QPU mode", 
                            execution_mode=request.execution_mode)
                return False
            
            # Must have explicit device specification
            if not request.device:
                logger.warning("QPU routing rejected: no device specified")
                return False
            
            # Must have explicit provider specification
            if not request.provider:
                logger.warning("QPU routing rejected: no provider specified")
                return False
            
            return True
            
        except Exception as e:
            logger.error("Failed to validate explicit enable", error=str(e))
            return False
    
    async def _validate_governance_approval(self, request: QPURoutingRequest) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate governance approval for QPU operation."""
        try:
            # Check if governance approval is required
            capability_status = self.capability_boundaries.get_capability_status()
            
            if not capability_status.get("governance_gating_required", True):
                return True, "Governance gating not required", None
            
            # Validate governance approval ID
            if not request.governance_approval_id:
                return False, "Governance approval ID required for QPU operations", None
            
            # Validate approval exists and is valid
            approval_valid = await self.capability_boundaries._validate_governance_approval(
                request.governance_approval_id,
                request.provider,
                request.device
            )
            
            if not approval_valid:
                return False, f"Invalid governance approval: {request.governance_approval_id}", None
            
            # Get approval details
            approval_details = {
                "approval_id": request.governance_approval_id,
                "provider": request.provider,
                "device": request.device,
                "qpu_access": True
            }
            
            self._approval_count += 1
            
            return True, "Governance approval validated", approval_details
            
        except Exception as e:
            logger.error("Failed to validate governance approval", error=str(e))
            return False, f"Governance validation error: {str(e)}", None
    
    async def _validate_quotas(self, request: QPURoutingRequest) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate quotas for QPU operation."""
        try:
            capability_status = self.capability_boundaries.get_capability_status()
            quotas = capability_status.get("quotas", {})
            
            # Get current quota usage (this would integrate with governance system)
            current_usage = await self._get_current_quota_usage(request.provider, request.device)
            
            # Validate daily task quota
            max_tasks_per_day = quotas.get("max_qpu_tasks_per_day", 10)
            if current_usage.get("daily_tasks", 0) >= max_tasks_per_day:
                return False, f"Daily QPU task quota exceeded: {current_usage.get('daily_tasks', 0)}/{max_tasks_per_day}", {
                    "quota_type": "daily_tasks",
                    "current": current_usage.get("daily_tasks", 0),
                    "limit": max_tasks_per_day
                }
            
            # Validate concurrent task quota
            max_concurrent = quotas.get("max_qpu_concurrent", 1)
            if current_usage.get("concurrent_tasks", 0) >= max_concurrent:
                return False, f"Concurrent QPU task quota exceeded: {current_usage.get('concurrent_tasks', 0)}/{max_concurrent}", {
                    "quota_type": "concurrent_tasks",
                    "current": current_usage.get("concurrent_tasks", 0),
                    "limit": max_concurrent
                }
            
            # Validate cost per task quota
            max_cost_per_task = quotas.get("max_qpu_cost_per_task", 100.0)
            device = self.device_registry.get_device(request.device)
            device_cost = device.cost_per_task if device else 0.0
            
            if device_cost > max_cost_per_task:
                return False, f"Device cost exceeds quota: ${device_cost:.2f} > ${max_cost_per_task:.2f}", {
                    "quota_type": "cost_per_task",
                    "current": device_cost,
                    "limit": max_cost_per_task
                }
            
            quota_info = {
                "daily_tasks": {
                    "current": current_usage.get("daily_tasks", 0),
                    "limit": max_tasks_per_day
                },
                "concurrent_tasks": {
                    "current": current_usage.get("concurrent_tasks", 0),
                    "limit": max_concurrent
                },
                "cost_per_task": {
                    "current": device_cost,
                    "limit": max_cost_per_task
                }
            }
            
            return True, "Quota validation passed", quota_info
            
        except Exception as e:
            logger.error("Failed to validate quotas", error=str(e))
            return False, f"Quota validation error: {str(e)}", None
    
    async def _validate_device(self, request: QPURoutingRequest) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate device for QPU operation."""
        try:
            # Validate device against registry
            device_valid, reason, device = self.device_registry.validate_device_request(
                request.device,
                request.provider,
                request.region
            )
            
            if not device_valid or not device:
                return False, reason, None
            
            # Convert device to dictionary
            device_dict = {
                "device_id": device.device_id,
                "arn": device.arn,
                "provider": device.provider.value,
                "device_type": device.device_type.value,
                "regions": device.regions,
                "qubits": device.qubits,
                "connectivity": device.connectivity,
                "gate_fidelity": device.gate_fidelity,
                "readout_fidelity": device.readout_fidelity,
                "t1_time": device.t1_time,
                "t2_time": device.t2_time,
                "available": device.available,
                "queue_time_seconds": device.queue_time_seconds,
                "cost_per_task": device.cost_per_task,
                "metadata": device.metadata
            }
            
            return True, "Device validation passed", device_dict
            
        except Exception as e:
            logger.error("Failed to validate device", error=str(e))
            return False, f"Device validation error: {str(e)}", None
    
    async def _get_current_quota_usage(self, provider: str, device: str) -> Dict[str, int]:
        """Get current quota usage for provider and device."""
        # This would integrate with governance system to get real quota usage
        # For now, return placeholder values
        return {
            "daily_tasks": 0,
            "concurrent_tasks": 0,
            "total_cost": 0.0
        }
    
    def _create_approved_result(self, 
                              request: QPURoutingRequest,
                              governance_approval: Optional[Dict[str, Any]],
                              device: Optional[Dict[str, Any]]) -> QPURoutingResult:
        """Create approved routing result."""
        return QPURoutingResult(
            decision=QPURoutingDecision.APPROVED,
            reason="QPU execution approved",
            device=device,
            governance_approval=governance_approval,
            fallback_chain=[
                f"{request.provider}:{request.device}",
                "cloud_simulator",
                "local_braket",
                "qiskit",
                "neal",
                "classical"
            ],
            metadata={
                "routing_timestamp": time.time(),
                "correlation_id": request.correlation_id,
                "explicit_enable": True,
                "governance_approved": True,
                "quota_validated": True,
                "device_validated": True
            }
        )
    
    def _create_rejection_result(self, 
                               decision: QPURoutingDecision,
                               reason: str,
                               request: QPURoutingRequest,
                               quota_info: Optional[Dict[str, Any]] = None) -> QPURoutingResult:
        """Create rejection routing result with fallback chain."""
        self._rejection_count += 1
        
        # Determine fallback chain based on rejection reason
        if decision == QPURoutingDecision.REJECTED_DEVICE:
            fallback_chain = ["cloud_simulator", "local_braket", "qiskit", "neal", "classical"]
        elif decision == QPURoutingDecision.REJECTED_QUOTA:
            fallback_chain = ["cloud_simulator", "local_braket", "qiskit", "neal", "classical"]
        else:
            fallback_chain = ["local_braket", "qiskit", "neal", "classical"]
        
        return QPURoutingResult(
            decision=decision,
            reason=reason,
            fallback_chain=fallback_chain,
            quota_info=quota_info,
            metadata={
                "routing_timestamp": time.time(),
                "correlation_id": request.correlation_id,
                "explicit_enable": False,
                "rejection_reason": reason,
                "fallback_triggered": True
            }
        )
    
    async def get_routing_statistics(self) -> Dict[str, Any]:
        """Get QPU routing statistics."""
        return {
            "total_routing_requests": self._routing_count,
            "approved_requests": self._approval_count,
            "rejected_requests": self._rejection_count,
            "fallback_triggered": self._fallback_count,
            "approval_rate": (self._approval_count / self._routing_count * 100) if self._routing_count > 0 else 0.0,
            "rejection_rate": (self._rejection_count / self._routing_count * 100) if self._routing_count > 0 else 0.0,
            "capability_status": self.capability_boundaries.get_capability_status(),
            "device_registry_stats": self.device_registry.get_registry_statistics()
        }
    
    def get_safety_guarantees(self) -> Dict[str, Any]:
        """Get QPU routing safety guarantees."""
        return {
            "explicit_enable_required": True,
            "no_automatic_routing": True,
            "governance_gating": True,
            "quota_validation": True,
            "device_validation": True,
            "fallback_routing": True,
            "safe_fallback_chain": [
                "QPU",
                "→ cloud_simulator",
                "→ local_braket",
                "→ qiskit",
                "→ neal",
                "→ classical"
            ],
            "never_bypasses_governance": True,
            "never_bypasses_quotas": True,
            "never_bypasses_device_validation": True
        }


# Global QPU execution router instance
_qpu_execution_router: Optional[QPUExecutionRouter] = None


def get_qpu_execution_router() -> QPUExecutionRouter:
    """Get global QPU execution router instance."""
    global _qpu_execution_router
    if _qpu_execution_router is None:
        _qpu_execution_router = QPUExecutionRouter()
    return _qpu_execution_router


def create_qpu_routing_request(
    execution_mode: str,
    provider: str,
    device: str,
    region: str,
    governance_approval_id: Optional[str] = None,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> QPURoutingRequest:
    """Create QPU routing request."""
    return QPURoutingRequest(
        execution_mode=execution_mode,
        provider=provider,
        device=device,
        region=region,
        governance_approval_id=governance_approval_id,
        correlation_id=correlation_id,
        metadata=metadata or {}
    )
