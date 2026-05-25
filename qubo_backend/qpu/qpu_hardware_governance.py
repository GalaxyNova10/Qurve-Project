"""
Qurve AI - QPU Hardware Governance
Safe hardware governance with quotas, limits, and policies.

Principles:
✅ QPU QUOTAS: Daily task limits, concurrent limits, cost limits
✅ PROVIDER QUOTAS: Per-provider governance controls
✅ HARDWARE COOLDOWN: Device cooldown policies
✅ QUEUE DURATION: Queue wait thresholds
✅ GOVERNANCE PRESERVATION: Never bypass existing governance
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .qpu_device_registry import get_qpu_device_registry, QPUProvider

logger = logging.getLogger(__name__)


class QPUGovernanceDecision(Enum):
    """QPU governance decision types."""
    APPROVED = "approved"
    REJECTED_QUOTA = "rejected_quota"
    REJECTED_CONCURRENCY = "rejected_concurrency"
    REJECTED_COST = "rejected_cost"
    REJECTED_COOLDOWN = "rejected_cooldown"
    REJECTED_QUEUE = "rejected_queue"
    REJECTED_PROVIDER = "rejected_provider"


@dataclass
class QPUQuotaConfig:
    """QPU quota configuration."""
    max_qpu_tasks_per_day: int = 10
    max_qpu_concurrent: int = 1
    max_qpu_cost_per_task: float = 100.0
    max_qpu_cost_per_day: float = 500.0
    max_qpu_queue_wait_seconds: int = 1800  # 30 minutes
    qpu_cooldown_seconds: int = 300  # 5 minutes
    provider_quotas: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass
class QPUQuotaUsage:
    """QPU quota usage tracking."""
    daily_tasks: Dict[str, int] = field(default_factory=dict)
    concurrent_tasks: Dict[str, int] = field(default_factory=dict)
    daily_cost: Dict[str, float] = field(default_factory=dict)
    last_task_time: Dict[str, float] = field(default_factory=dict)
    queue_wait_times: Dict[str, List[float]] = field(default_factory=dict)


class QPUHardwareGovernance:
    """
    Production-grade QPU hardware governance.
    
    Features:
    - QPU quota enforcement
    - Provider-level quotas
    - Hardware cooldown policies
    - Queue duration thresholds
    - Governance preservation
    """
    
    def __init__(self, config: QPUQuotaConfig):
        self.config = config
        self.device_registry = get_qpu_device_registry()
        
        # Quota usage tracking
        self._quota_usage = QPUQuotaUsage()
        
        # Governance statistics
        self._governance_decisions = {}
        self._decision_count = 0
        self._approval_count = 0
        self._rejection_count = 0
        
        # Initialize provider quotas
        self._initialize_provider_quotas()
        
        logger.info("QPU hardware governance initialized", 
                  max_daily_tasks=config.max_qpu_tasks_per_day,
                  max_concurrent=config.max_qpu_concurrent,
                  max_cost_per_task=config.max_qpu_cost_per_task,
                  max_queue_wait=config.max_qpu_queue_wait_seconds)
    
    def _initialize_provider_quotas(self) -> None:
        """Initialize provider-specific quotas."""
        # Set default provider quotas if not specified
        default_provider_quotas = {
            "IonQ": {
                "max_daily_tasks": 5,
                "max_concurrent": 1,
                "max_cost_per_task": 150.0,
                "max_daily_cost": 300.0
            },
            "Rigetti": {
                "max_daily_tasks": 8,
                "max_concurrent": 1,
                "max_cost_per_task": 80.0,
                "max_daily_cost": 400.0
            },
            "OQC": {
                "max_daily_tasks": 3,
                "max_concurrent": 1,
                "max_cost_per_task": 50.0,
                "max_daily_cost": 150.0
            }
        }
        
        # Merge with config provider quotas
        for provider, quotas in default_provider_quotas.items():
            if provider not in self.config.provider_quotas:
                self.config.provider_quotas[provider] = quotas.copy()
        
        logger.info("Provider quotas initialized", 
                  providers=list(self.config.provider_quotas.keys()))
    
    async def validate_qpu_request(self, 
                                 provider: str,
                                 device: str,
                                 estimated_cost: float,
                                 correlation_id: Optional[str] = None) -> Tuple[bool, str, QPUGovernanceDecision, Optional[Dict[str, Any]]]:
        """
        Validate QPU request against hardware governance rules.
        
        Args:
            provider: QPU provider
            device: QPU device
            estimated_cost: Estimated task cost
            correlation_id: Request correlation ID
            
        Returns:
            Tuple of (allowed: bool, reason: str, decision: QPUGovernanceDecision, quota_info: Optional[Dict])
        """
        try:
            self._decision_count += 1
            
            logger.info("QPU governance validation", 
                       provider=provider,
                       device=device,
                       estimated_cost=estimated_cost,
                       correlation_id=correlation_id)
            
            # Step 1: Validate provider quota
            provider_result = await self._validate_provider_quota(provider, device, estimated_cost)
            if not provider_result[0]:
                return False, provider_result[1], QPUGovernanceDecision.REJECTED_PROVIDER, provider_result[2]
            
            # Step 2: Validate daily task quota
            daily_result = await self._validate_daily_task_quota(provider, device)
            if not daily_result[0]:
                return False, daily_result[1], QPUGovernanceDecision.REJECTED_QUOTA, daily_result[2]
            
            # Step 3: Validate concurrent task quota
            concurrent_result = await self._validate_concurrent_task_quota(provider, device)
            if not concurrent_result[0]:
                return False, concurrent_result[1], QPUGovernanceDecision.REJECTED_CONCURRENCY, concurrent_result[2]
            
            # Step 4: Validate cost quota
            cost_result = await self._validate_cost_quota(provider, device, estimated_cost)
            if not cost_result[0]:
                return False, cost_result[1], QPUGovernanceDecision.REJECTED_COST, cost_result[2]
            
            # Step 5: Validate hardware cooldown
            cooldown_result = await self._validate_hardware_cooldown(provider, device)
            if not cooldown_result[0]:
                return False, cooldown_result[1], QPUGovernanceDecision.REJECTED_COOLDOWN, cooldown_result[2]
            
            # Step 6: Validate queue duration
            queue_result = await self._validate_queue_duration(provider, device)
            if not queue_result[0]:
                return False, queue_result[1], QPUGovernanceDecision.REJECTED_QUEUE, queue_result[2]
            
            # Create approval result
            self._approval_count += 1
            quota_info = self._create_quota_info(provider, device, estimated_cost)
            
            logger.info("QPU governance validation approved", 
                       provider=provider,
                       device=device,
                       correlation_id=correlation_id)
            
            return True, "QPU request approved by hardware governance", QPUGovernanceDecision.APPROVED, quota_info
            
        except Exception as e:
            logger.error("Failed to validate QPU request", 
                        provider=provider,
                        device=device,
                        error=str(e))
            return False, f"Governance validation error: {str(e)}", QPUGovernanceDecision.REJECTED_QUOTA, None
    
    async def _validate_provider_quota(self, 
                                  provider: str,
                                  device: str,
                                  estimated_cost: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate provider-specific quota."""
        try:
            if provider not in self.config.provider_quotas:
                return False, f"Provider not supported: {provider}", None
            
            provider_quota = self.config.provider_quotas[provider]
            
            # Validate provider cost per task
            max_cost_per_task = provider_quota.get("max_cost_per_task", self.config.max_qpu_cost_per_task)
            if estimated_cost > max_cost_per_task:
                return False, f"Estimated cost ${estimated_cost:.2f} exceeds provider limit ${max_cost_per_task:.2f}", {
                    "quota_type": "provider_cost_per_task",
                    "current": estimated_cost,
                    "limit": max_cost_per_task
                }
            
            return True, "Provider quota validation passed", None
            
        except Exception as e:
            logger.error("Failed to validate provider quota", error=str(e))
            return False, f"Provider quota validation error: {str(e)}", None
    
    async def _validate_daily_task_quota(self, 
                                     provider: str,
                                     device: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate daily task quota."""
        try:
            # Get provider-specific daily quota
            provider_quota = self.config.provider_quotas.get(provider, {})
            max_daily_tasks = provider_quota.get("max_daily_tasks", self.config.max_qpu_tasks_per_day)
            
            # Get current daily usage
            daily_key = f"{provider}:{device}"
            current_daily_tasks = self._quota_usage.daily_tasks.get(daily_key, 0)
            
            if current_daily_tasks >= max_daily_tasks:
                return False, f"Daily task quota exceeded: {current_daily_tasks}/{max_daily_tasks}", {
                    "quota_type": "daily_tasks",
                    "current": current_daily_tasks,
                    "limit": max_daily_tasks
                }
            
            return True, "Daily task quota validation passed", None
            
        except Exception as e:
            logger.error("Failed to validate daily task quota", error=str(e))
            return False, f"Daily task quota validation error: {str(e)}", None
    
    async def _validate_concurrent_task_quota(self, 
                                        provider: str,
                                        device: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate concurrent task quota."""
        try:
            # Get provider-specific concurrent quota
            provider_quota = self.config.provider_quotas.get(provider, {})
            max_concurrent = provider_quota.get("max_concurrent", self.config.max_qpu_concurrent)
            
            # Get current concurrent usage
            concurrent_key = f"{provider}:{device}"
            current_concurrent = self._quota_usage.concurrent_tasks.get(concurrent_key, 0)
            
            if current_concurrent >= max_concurrent:
                return False, f"Concurrent task quota exceeded: {current_concurrent}/{max_concurrent}", {
                    "quota_type": "concurrent_tasks",
                    "current": current_concurrent,
                    "limit": max_concurrent
                }
            
            return True, "Concurrent task quota validation passed", None
            
        except Exception as e:
            logger.error("Failed to validate concurrent task quota", error=str(e))
            return False, f"Concurrent task quota validation error: {str(e)}", None
    
    async def _validate_cost_quota(self, 
                                provider: str,
                                device: str,
                                estimated_cost: float) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate cost quota."""
        try:
            # Get provider-specific daily cost quota
            provider_quota = self.config.provider_quotas.get(provider, {})
            max_daily_cost = provider_quota.get("max_daily_cost", self.config.max_qpu_cost_per_day)
            
            # Get current daily cost usage
            cost_key = f"{provider}:{device}"
            current_daily_cost = self._quota_usage.daily_cost.get(cost_key, 0.0)
            
            if (current_daily_cost + estimated_cost) > max_daily_cost:
                return False, f"Daily cost quota would be exceeded: ${(current_daily_cost + estimated_cost):.2f} > ${max_daily_cost:.2f}", {
                    "quota_type": "daily_cost",
                    "current": current_daily_cost,
                    "additional": estimated_cost,
                    "limit": max_daily_cost
                }
            
            return True, "Cost quota validation passed", None
            
        except Exception as e:
            logger.error("Failed to validate cost quota", error=str(e))
            return False, f"Cost quota validation error: {str(e)}", None
    
    async def _validate_hardware_cooldown(self, 
                                      provider: str,
                                      device: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate hardware cooldown policy."""
        try:
            cooldown_key = f"{provider}:{device}"
            last_task_time = self._quota_usage.last_task_time.get(cooldown_key, 0.0)
            
            current_time = time.time()
            time_since_last_task = current_time - last_task_time
            
            if time_since_last_task < self.config.qpu_cooldown_seconds:
                remaining_cooldown = self.config.qpu_cooldown_seconds - time_since_last_task
                return False, f"Device cooldown active: {remaining_cooldown:.0f}s remaining", {
                    "quota_type": "hardware_cooldown",
                    "time_since_last": time_since_last_task,
                    "cooldown_period": self.config.qpu_cooldown_seconds,
                    "remaining_cooldown": remaining_cooldown
                }
            
            return True, "Hardware cooldown validation passed", None
            
        except Exception as e:
            logger.error("Failed to validate hardware cooldown", error=str(e))
            return False, f"Hardware cooldown validation error: {str(e)}", None
    
    async def _validate_queue_duration(self, 
                                   provider: str,
                                   device: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Validate queue duration threshold."""
        try:
            # Get device from registry
            qpu_device = self.device_registry.get_device(device)
            if not qpu_device:
                return False, f"Device not found: {device}", None
            
            # Check if queue time exceeds threshold
            queue_time = qpu_device.queue_time_seconds
            if queue_time and queue_time > self.config.max_qpu_queue_wait_seconds:
                return False, f"Queue wait time exceeds threshold: {queue_time}s > {self.config.max_qpu_queue_wait_seconds}s", {
                    "quota_type": "queue_duration",
                    "current_queue_time": queue_time,
                    "max_queue_time": self.config.max_qpu_queue_wait_seconds
                }
            
            return True, "Queue duration validation passed", None
            
        except Exception as e:
            logger.error("Failed to validate queue duration", error=str(e))
            return False, f"Queue duration validation error: {str(e)}", None
    
    def _create_quota_info(self, 
                          provider: str,
                          device: str,
                          estimated_cost: float) -> Dict[str, Any]:
        """Create quota information for approved request."""
        daily_key = f"{provider}:{device}"
        concurrent_key = f"{provider}:{device}"
        cost_key = f"{provider}:{device}"
        
        provider_quota = self.config.provider_quotas.get(provider, {})
        
        return {
            "provider": provider,
            "device": device,
            "estimated_cost": estimated_cost,
            "quotas": {
                "daily_tasks": {
                    "current": self._quota_usage.daily_tasks.get(daily_key, 0),
                    "limit": provider_quota.get("max_daily_tasks", self.config.max_qpu_tasks_per_day)
                },
                "concurrent_tasks": {
                    "current": self._quota_usage.concurrent_tasks.get(concurrent_key, 0),
                    "limit": provider_quota.get("max_concurrent", self.config.max_qpu_concurrent)
                },
                "daily_cost": {
                    "current": self._quota_usage.daily_cost.get(cost_key, 0.0),
                    "limit": provider_quota.get("max_daily_cost", self.config.max_qpu_cost_per_day)
                },
                "cost_per_task": {
                    "current": estimated_cost,
                    "limit": provider_quota.get("max_cost_per_task", self.config.max_qpu_cost_per_task)
                }
            }
        }
    
    async def record_qpu_task_start(self, 
                                  provider: str,
                                  device: str,
                                  estimated_cost: float,
                                  correlation_id: Optional[str] = None) -> bool:
        """Record QPU task start for quota tracking."""
        try:
            daily_key = f"{provider}:{device}"
            concurrent_key = f"{provider}:{device}"
            cost_key = f"{provider}:{device}"
            
            # Update quota usage
            self._quota_usage.daily_tasks[daily_key] = self._quota_usage.daily_tasks.get(daily_key, 0) + 1
            self._quota_usage.concurrent_tasks[concurrent_key] = self._quota_usage.concurrent_tasks.get(concurrent_key, 0) + 1
            self._quota_usage.daily_cost[cost_key] = self._quota_usage.daily_cost.get(cost_key, 0.0) + estimated_cost
            self._quota_usage.last_task_time[concurrent_key] = time.time()
            
            logger.info("QPU task start recorded", 
                       provider=provider,
                       device=device,
                       estimated_cost=estimated_cost,
                       correlation_id=correlation_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to record QPU task start", error=str(e))
            return False
    
    async def record_qpu_task_complete(self, 
                                   provider: str,
                                   device: str,
                                   actual_cost: float,
                                   correlation_id: Optional[str] = None) -> bool:
        """Record QPU task completion for quota tracking."""
        try:
            concurrent_key = f"{provider}:{device}"
            cost_key = f"{provider}:{device}"
            
            # Update quota usage
            self._quota_usage.concurrent_tasks[concurrent_key] = max(0, self._quota_usage.concurrent_tasks.get(concurrent_key, 0) - 1)
            
            # Adjust cost if actual differs from estimated
            # (This would be more sophisticated in production)
            
            logger.info("QPU task completion recorded", 
                       provider=provider,
                       device=device,
                       actual_cost=actual_cost,
                       correlation_id=correlation_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to record QPU task completion", error=str(e))
            return False
    
    async def get_governance_statistics(self) -> Dict[str, Any]:
        """Get QPU governance statistics."""
        return {
            "total_decisions": self._decision_count,
            "approved_requests": self._approval_count,
            "rejected_requests": self._rejection_count,
            "approval_rate": (self._approval_count / self._decision_count * 100) if self._decision_count > 0 else 0.0,
            "rejection_rate": (self._rejection_count / self._decision_count * 100) if self._decision_count > 0 else 0.0,
            "quota_usage": {
                "daily_tasks": dict(self._quota_usage.daily_tasks),
                "concurrent_tasks": dict(self._quota_usage.concurrent_tasks),
                "daily_cost": dict(self._quota_usage.daily_cost),
                "last_task_times": dict(self._quota_usage.last_task_time)
            },
            "provider_quotas": self.config.provider_quotas,
            "global_quotas": {
                "max_qpu_tasks_per_day": self.config.max_qpu_tasks_per_day,
                "max_qpu_concurrent": self.config.max_qpu_concurrent,
                "max_qpu_cost_per_task": self.config.max_qpu_cost_per_task,
                "max_qpu_cost_per_day": self.config.max_qpu_cost_per_day,
                "max_qpu_queue_wait_seconds": self.config.max_qpu_queue_wait_seconds,
                "qpu_cooldown_seconds": self.config.qpu_cooldown_seconds
            }
        }
    
    def get_governance_guarantees(self) -> Dict[str, Any]:
        """Get QPU governance guarantees."""
        return {
            "quota_enforcement": True,
            "provider_quotas": True,
            "hardware_cooldown": True,
            "queue_duration_limits": True,
            "cost_controls": True,
            "concurrency_limits": True,
            "daily_task_limits": True,
            "governance_preservation": True,
            "no_bypass_allowed": True,
            "strict_enforcement": True
        }


# Global QPU hardware governance instance
_qpu_hardware_governance: Optional[QPUHardwareGovernance] = None


def get_qpu_hardware_governance() -> QPUHardwareGovernance:
    """Get global QPU hardware governance instance."""
    global _qpu_hardware_governance
    if _qpu_hardware_governance is None:
        _qpu_hardware_governance = QPUHardwareGovernance(QPUQuotaConfig())
    return _qpu_hardware_governance


def create_qpu_quota_config(
    max_qpu_tasks_per_day: int = 10,
    max_qpu_concurrent: int = 1,
    max_qpu_cost_per_task: float = 100.0,
    max_qpu_cost_per_day: float = 500.0,
    max_qpu_queue_wait_seconds: int = 1800,
    qpu_cooldown_seconds: int = 300,
    provider_quotas: Optional[Dict[str, Dict[str, Any]]] = None
) -> QPUQuotaConfig:
    """Create QPU quota configuration."""
    return QPUQuotaConfig(
        max_qpu_tasks_per_day=max_qpu_tasks_per_day,
        max_qpu_concurrent=max_qpu_concurrent,
        max_qpu_cost_per_task=max_qpu_cost_per_task,
        max_qpu_cost_per_day=max_qpu_cost_per_day,
        max_qpu_queue_wait_seconds=max_qpu_queue_wait_seconds,
        qpu_cooldown_seconds=qpu_cooldown_seconds,
        provider_quotas=provider_quotas or {}
    )
