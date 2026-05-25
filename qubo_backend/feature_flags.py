"""
Feature Flags & Cost Control for QUBO Portfolio Optimizer
Implements advanced platform control with budgeting and quotas.
Provides dynamic configuration, usage quotas, cost tracking,
and policy enforcement for different user tiers.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import uuid
import threading

from .config import get_settings
from .audit_logging import AUDIT_LOGGER
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


class FlagType(Enum):
    """Types of feature flags."""
    
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"


class UserTier(Enum):
    """User access tiers."""
    
    FREE = "free"
    BASIC = "basic"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    ADMIN = "admin"


class ResourceType(Enum):
    """Types of resources for quotas."""
    
    API_CALLS = "api_calls"
    COMPUTE_TIME = "compute_time"
    GPU_HOURS = "gpu_hours"
    STORAGE_MB = "storage_mb"
    JOBS_PER_DAY = "jobs_per_day"
    SOLVER_USAGE = "solver_usage"


@dataclass
class FeatureFlag:
    """Feature flag definition."""
    
    flag_key: str
    name: str
    description: str
    flag_type: FlagType
    default_value: Any
    current_value: Any
    enabled_for_tiers: List[UserTier]
    rollout_percentage: float = 100.0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "flag_key": self.flag_key,
            "name": self.name,
            "description": self.description,
            "flag_type": self.flag_type.value,
            "default_value": self.default_value,
            "current_value": self.current_value,
            "enabled_for_tiers": [tier.value for tier in self.enabled_for_tiers],
            "rollout_percentage": self.rollout_percentage,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "created_by": self.created_by
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FeatureFlag':
        """Create from dictionary."""
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        data['enabled_for_tiers'] = [UserTier(tier) for tier in data['enabled_for_tiers']]
        data['flag_type'] = FlagType(data['flag_type'])
        return cls(**data)


@dataclass
class ResourceQuota:
    """Resource quota definition."""
    
    resource_type: ResourceType
    tier: UserTier
    daily_limit: Optional[int] = None
    monthly_limit: Optional[int] = None
    per_job_limit: Optional[int] = None
    cost_per_unit: float = 0.0
    reset_policy: str = "daily"  # daily, monthly, never
    grace_period_hours: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resource_type": self.resource_type.value,
            "tier": self.tier.value,
            "daily_limit": self.daily_limit,
            "monthly_limit": self.monthly_limit,
            "per_job_limit": self.per_job_limit,
            "cost_per_unit": self.cost_per_unit,
            "reset_policy": self.reset_policy,
            "grace_period_hours": self.grace_period_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceQuota':
        """Create from dictionary."""
        data['resource_type'] = ResourceType(data['resource_type'])
        data['tier'] = UserTier(data['tier'])
        return cls(**data)


@dataclass
class UsageRecord:
    """Resource usage record."""
    
    record_id: str
    user_id: str
    resource_type: ResourceType
    amount: float
    timestamp: datetime
    job_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "record_id": self.record_id,
            "user_id": self.user_id,
            "resource_type": self.resource_type.value,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "job_id": self.job_id,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageRecord':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['resource_type'] = ResourceType(data['resource_type'])
        return cls(**data)


@dataclass
class UserPolicy:
    """User-specific policy configuration."""
    
    user_id: str
    tier: UserTier
    custom_limits: Dict[ResourceType, int] = field(default_factory=dict)
    allowed_solvers: List[str] = field(default_factory=list)
    blocked_features: List[str] = field(default_factory=list)
    budget_limit: Optional[float] = None
    billing_period_start: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "user_id": self.user_id,
            "tier": self.tier.value,
            "custom_limits": {rt.value: limit for rt, limit in self.custom_limits.items()},
            "allowed_solvers": self.allowed_solvers,
            "blocked_features": self.blocked_features,
            "budget_limit": self.budget_limit,
            "billing_period_start": self.billing_period_start.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserPolicy':
        """Create from dictionary."""
        data['tier'] = UserTier(data['tier'])
        data['billing_period_start'] = datetime.fromisoformat(data['billing_period_start'])
        
        custom_limits = {}
        for rt_str, limit in data.get('custom_limits', {}).items():
            custom_limits[ResourceType(rt_str)] = limit
        data['custom_limits'] = custom_limits
        
        return cls(**data)


class FeatureFlagManager:
    """Manages feature flags and dynamic configuration."""
    
    def __init__(self):
        self.settings = get_settings()
        self.flags_dir = self.settings.output_dir / "flags"
        self.flags_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.flags_file = self.flags_dir / "flags.json"
        
        # In-memory cache
        self._flags: Dict[str, FeatureFlag] = {}
        self._lock = threading.Lock()
        
        # Load existing flags
        self._load_flags()
        self._setup_default_flags()
    
    def _load_flags(self) -> None:
        """Load existing feature flags."""
        try:
            if self.flags_file.exists():
                with open(self.flags_file, 'r') as f:
                    flags_data = json.load(f)
                
                for flag_key, flag_data in flags_data.items():
                    self._flags[flag_key] = FeatureFlag.from_dict(flag_data)
            
            logger.info(f"Loaded {len(self._flags)} feature flags")
            
        except Exception as e:
            logger.error(f"Failed to load feature flags: {e}")
            self._flags = {}
    
    def _save_flags(self) -> None:
        """Save feature flags to storage."""
        try:
            flags_data = {}
            for flag_key, flag in self._flags.items():
                flags_data[flag_key] = flag.to_dict()
            
            with open(self.flags_file, 'w') as f:
                json.dump(flags_data, f, indent=2)
            
            logger.debug("Feature flags saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save feature flags: {e}")
    
    def _setup_default_flags(self) -> None:
        """Setup default feature flags."""
        default_flags = [
            FeatureFlag(
                flag_key="quantum_solvers_enabled",
                name="Quantum Solvers Enabled",
                description="Enable quantum optimization solvers",
                flag_type=FlagType.BOOLEAN,
                default_value=True,
                current_value=True,
                enabled_for_tiers=[UserTier.BASIC, UserTier.PROFESSIONAL, UserTier.ENTERPRISE, UserTier.ADMIN],
                tags=["quantum", "solvers"]
            ),
            FeatureFlag(
                flag_key="gpu_acceleration",
                name="GPU Acceleration",
                description="Enable GPU-accelerated optimization",
                flag_type=FlagType.BOOLEAN,
                default_value=True,
                current_value=True,
                enabled_for_tiers=[UserTier.PROFESSIONAL, UserTier.ENTERPRISE, UserTier.ADMIN],
                tags=["gpu", "performance"]
            ),
            FeatureFlag(
                flag_key="advanced_benchmarks",
                name="Advanced Benchmarks",
                description="Enable advanced benchmarking features",
                flag_type=FlagType.BOOLEAN,
                default_value=False,
                current_value=False,
                enabled_for_tiers=[UserTier.PROFESSIONAL, UserTier.ENTERPRISE, UserTier.ADMIN],
                tags=["benchmarks", "analytics"]
            ),
            FeatureFlag(
                flag_key="concurrent_jobs_limit",
                name="Concurrent Jobs Limit",
                description="Maximum number of concurrent jobs",
                flag_type=FlagType.NUMBER,
                default_value=3,
                current_value=3,
                enabled_for_tiers=[UserTier.BASIC, UserTier.PROFESSIONAL, UserTier.ENTERPRISE, UserTier.ADMIN],
                tags=["concurrency", "limits"]
            ),
            FeatureFlag(
                flag_key="model_training_enabled",
                name="Model Training Enabled",
                description="Enable custom model training features",
                flag_type=FlagType.BOOLEAN,
                default_value=False,
                current_value=False,
                enabled_for_tiers=[UserTier.ENTERPRISE, UserTier.ADMIN],
                tags=["ml", "training"]
            )
        ]
        
        for flag in default_flags:
            if flag.flag_key not in self._flags:
                self._flags[flag.flag_key] = flag
        
        self._save_flags()
    
    def get_flag(self, flag_key: str, user_tier: UserTier = UserTier.FREE) -> Any:
        """Get feature flag value for user tier."""
        flag = self._flags.get(flag_key)
        if not flag:
            return flag.default_value if hasattr(flag, 'default_value') else None
        
        # Check if flag is enabled for user's tier
        if user_tier not in flag.enabled_for_tiers:
            return flag.default_value
        
        # Check rollout percentage (simplified - would use user ID hash in production)
        import random
        user_hash = hash(user_tier.value) % 100
        if user_hash > flag.rollout_percentage:
            return flag.default_value
        
        return flag.current_value
    
    def set_flag(self, 
                 flag_key: str,
                 value: Any,
                 updated_by: Optional[str] = None) -> bool:
        """Set feature flag value."""
        with self._lock:
            flag = self._flags.get(flag_key)
            if not flag:
                logger.error(f"Feature flag not found: {flag_key}")
                return False
            
            flag.current_value = value
            flag.updated_at = datetime.now()
            
            self._save_flags()
            
            # Log flag change
            AUDIT_LOGGER.log_model_versioning(
                model_name=f"feature_flag_{flag_key}",
                version="current",
                action="updated",
                previous_version=str(flag.default_value),
                performance_metrics={"old_value": flag.default_value, "new_value": value},
                user_id=updated_by
            )
        
        logger.info(f"Updated feature flag {flag_key} to {value}")
        return True
    
    def create_flag(self,
                    flag_key: str,
                    name: str,
                    description: str,
                    flag_type: FlagType,
                    default_value: Any,
                    enabled_for_tiers: List[UserTier],
                    created_by: Optional[str] = None,
                    rollout_percentage: float = 100.0,
                    tags: Optional[List[str]] = None) -> bool:
        """Create a new feature flag."""
        flag = FeatureFlag(
            flag_key=flag_key,
            name=name,
            description=description,
            flag_type=flag_type,
            default_value=default_value,
            current_value=default_value,
            enabled_for_tiers=enabled_for_tiers,
            created_by=created_by,
            rollout_percentage=rollout_percentage,
            tags=tags or []
        )
        
        with self._lock:
            self._flags[flag_key] = flag
            self._save_flags()
        
        logger.info(f"Created feature flag {flag_key}")
        return True
    
    def get_all_flags(self) -> Dict[str, FeatureFlag]:
        """Get all feature flags."""
        return self._flags.copy()


class CostControlManager:
    """Manages cost control, quotas, and billing."""
    
    def __init__(self):
        self.settings = get_settings()
        self.cost_dir = self.settings.output_dir / "cost_control"
        self.cost_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.quotas_file = self.cost_dir / "quotas.json"
        self.usage_file = self.cost_dir / "usage.jsonl"
        self.policies_file = self.cost_dir / "policies.json"
        
        # In-memory data
        self._quotas: Dict[str, ResourceQuota] = {}
        self._usage_records: List[UsageRecord] = []
        self._user_policies: Dict[str, UserPolicy] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Load existing data
        self._load_quotas()
        self._load_usage()
        self._load_policies()
        self._setup_default_quotas()
    
    def _load_quotas(self) -> None:
        """Load resource quotas."""
        try:
            if self.quotas_file.exists():
                with open(self.quotas_file, 'r') as f:
                    quotas_data = json.load(f)
                
                for quota_key, quota_data in quotas_data.items():
                    self._quotas[quota_key] = ResourceQuota.from_dict(quota_data)
            
            logger.info(f"Loaded {len(self._quotas)} resource quotas")
            
        except Exception as e:
            logger.error(f"Failed to load quotas: {e}")
            self._quotas = {}
    
    def _load_usage(self) -> None:
        """Load usage records."""
        try:
            if self.usage_file.exists():
                with open(self.usage_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            usage_data = json.loads(line)
                            self._usage_records.append(UsageRecord.from_dict(usage_data))
            
            logger.info(f"Loaded {len(self._usage_records)} usage records")
            
        except Exception as e:
            logger.error(f"Failed to load usage: {e}")
            self._usage_records = []
    
    def _load_policies(self) -> None:
        """Load user policies."""
        try:
            if self.policies_file.exists():
                with open(self.policies_file, 'r') as f:
                    policies_data = json.load(f)
                
                for user_id, policy_data in policies_data.items():
                    self._user_policies[user_id] = UserPolicy.from_dict(policy_data)
            
            logger.info(f"Loaded {len(self._user_policies)} user policies")
            
        except Exception as e:
            logger.error(f"Failed to load policies: {e}")
            self._user_policies = {}
    
    def _setup_default_quotas(self) -> None:
        """Setup default resource quotas."""
        default_quotas = [
            # Free tier
            ResourceQuota(
                resource_type=ResourceType.API_CALLS,
                tier=UserTier.FREE,
                daily_limit=100,
                monthly_limit=3000,
                cost_per_unit=0.0
            ),
            ResourceQuota(
                resource_type=ResourceType.COMPUTE_TIME,
                tier=UserTier.FREE,
                daily_limit=3600,  # 1 hour
                monthly_limit=108000,  # 30 hours
                cost_per_unit=0.0
            ),
            ResourceQuota(
                resource_type=ResourceType.JOBS_PER_DAY,
                tier=UserTier.FREE,
                daily_limit=5,
                cost_per_unit=0.0
            ),
            
            # Basic tier
            ResourceQuota(
                resource_type=ResourceType.API_CALLS,
                tier=UserTier.BASIC,
                daily_limit=1000,
                monthly_limit=30000,
                cost_per_unit=0.001
            ),
            ResourceQuota(
                resource_type=ResourceType.COMPUTE_TIME,
                tier=UserTier.BASIC,
                daily_limit=14400,  # 4 hours
                monthly_limit=432000,  # 120 hours
                cost_per_unit=0.0001
            ),
            ResourceQuota(
                resource_type=ResourceType.JOBS_PER_DAY,
                tier=UserTier.BASIC,
                daily_limit=25,
                cost_per_unit=0.0
            ),
            
            # Professional tier
            ResourceQuota(
                resource_type=ResourceType.API_CALLS,
                tier=UserTier.PROFESSIONAL,
                daily_limit=10000,
                monthly_limit=300000,
                cost_per_unit=0.0005
            ),
            ResourceQuota(
                resource_type=ResourceType.GPU_HOURS,
                tier=UserTier.PROFESSIONAL,
                daily_limit=8,
                monthly_limit=240,
                cost_per_unit=0.50
            ),
            ResourceQuota(
                resource_type=ResourceType.JOBS_PER_DAY,
                tier=UserTier.PROFESSIONAL,
                daily_limit=100,
                cost_per_unit=0.0
            ),
            
            # Enterprise tier
            ResourceQuota(
                resource_type=ResourceType.API_CALLS,
                tier=UserTier.ENTERPRISE,
                monthly_limit=1000000,
                cost_per_unit=0.0002
            ),
            ResourceQuota(
                resource_type=ResourceType.GPU_HOURS,
                tier=UserTier.ENTERPRISE,
                monthly_limit=1000,
                cost_per_unit=0.30
            ),
            ResourceQuota(
                resource_type=ResourceType.JOBS_PER_DAY,
                tier=UserTier.ENTERPRISE,
                daily_limit=1000,
                cost_per_unit=0.0
            )
        ]
        
        for quota in default_quotas:
            quota_key = f"{quota.resource_type.value}_{quota.tier.value}"
            if quota_key not in self._quotas:
                self._quotas[quota_key] = quota
        
        self._save_quotas()
    
    def _save_quotas(self) -> None:
        """Save resource quotas."""
        try:
            quotas_data = {}
            for quota_key, quota in self._quotas.items():
                quotas_data[quota_key] = quota.to_dict()
            
            with open(self.quotas_file, 'w') as f:
                json.dump(quotas_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save quotas: {e}")
    
    def _save_usage(self) -> None:
        """Save usage records."""
        try:
            with open(self.usage_file, 'a') as f:
                for record in self._usage_records[-100:]:  # Save last 100 records
                    f.write(json.dumps(record.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to save usage: {e}")
    
    def _save_policies(self) -> None:
        """Save user policies."""
        try:
            policies_data = {}
            for user_id, policy in self._user_policies.items():
                policies_data[user_id] = policy.to_dict()
            
            with open(self.policies_file, 'w') as f:
                json.dump(policies_data, f, indent=2)
            
        except Exception as e:
            logger.error(f"Failed to save policies: {e}")
    
    def record_usage(self,
                    user_id: str,
                    resource_type: ResourceType,
                    amount: float,
                    job_id: Optional[str] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> str:
        """Record resource usage."""
        record = UsageRecord(
            record_id=str(uuid.uuid4()),
            user_id=user_id,
            resource_type=resource_type,
            amount=amount,
            timestamp=datetime.now(),
            job_id=job_id,
            metadata=metadata or {}
        )
        
        with self._lock:
            self._usage_records.append(record)
            self._save_usage()
        
        # Update cache
        cache_key = f"usage_{user_id}_{resource_type.value}"
        CACHE_MANAGER.set_system_metrics(cache_key, {
            "total_usage": amount,
            "timestamp": record.timestamp.isoformat()
        })
        
        return record.record_id
    
    def check_quota(self,
                    user_id: str,
                    resource_type: ResourceType,
                    amount: float = 1.0) -> tuple[bool, str]:
        """
        Check if user has sufficient quota.
        
        Returns:
            (allowed, reason)
        """
        user_policy = self._user_policies.get(user_id)
        user_tier = user_policy.tier if user_policy else UserTier.FREE
        
        # Check custom limits first
        if user_policy and resource_type in user_policy.custom_limits:
            custom_limit = user_policy.custom_limits[resource_type]
            current_usage = self._get_current_usage(user_id, resource_type)
            if current_usage + amount > custom_limit:
                return False, f"Custom limit exceeded: {current_usage + amount}/{custom_limit}"
        
        # Check standard quotas
        quota_key = f"{resource_type.value}_{user_tier.value}"
        quota = self._quotas.get(quota_key)
        
        if not quota:
            return True, "No quota defined"
        
        current_usage = self._get_current_usage(user_id, resource_type)
        
        # Check per-job limit
        if quota.per_job_limit and amount > quota.per_job_limit:
            return False, f"Per-job limit exceeded: {amount}/{quota.per_job_limit}"
        
        # Check daily limit
        if quota.daily_limit:
            daily_usage = self._get_period_usage(user_id, resource_type, "daily")
            if daily_usage + amount > quota.daily_limit:
                return False, f"Daily limit exceeded: {daily_usage + amount}/{quota.daily_limit}"
        
        # Check monthly limit
        if quota.monthly_limit:
            monthly_usage = self._get_period_usage(user_id, resource_type, "monthly")
            if monthly_usage + amount > quota.monthly_limit:
                return False, f"Monthly limit exceeded: {monthly_usage + amount}/{quota.monthly_limit}"
        
        return True, "Quota available"
    
    def _get_current_usage(self, user_id: str, resource_type: ResourceType) -> float:
        """Get current usage for user and resource type."""
        user_records = [r for r in self._usage_records if r.user_id == user_id and r.resource_type == resource_type]
        return sum(r.amount for r in user_records)
    
    def _get_period_usage(self, user_id: str, resource_type: ResourceType, period: str) -> float:
        """Get usage for a specific period."""
        now = datetime.now()
        
        if period == "daily":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == "monthly":
            start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            return self._get_current_usage(user_id, resource_type)
        
        period_records = [
            r for r in self._usage_records
            if (r.user_id == user_id and 
                r.resource_type == resource_type and
                r.timestamp >= start_time)
        ]
        
        return sum(r.amount for r in period_records)
    
    def get_user_quota_status(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive quota status for user."""
        user_policy = self._user_policies.get(user_id)
        user_tier = user_policy.tier if user_policy else UserTier.FREE
        
        quota_status = {}
        
        for resource_type in ResourceType:
            current_usage = self._get_current_usage(user_id, resource_type)
            daily_usage = self._get_period_usage(user_id, resource_type, "daily")
            monthly_usage = self._get_period_usage(user_id, resource_type, "monthly")
            
            quota_key = f"{resource_type.value}_{user_tier.value}"
            quota = self._quotas.get(quota_key)
            
            if quota:
                quota_status[resource_type.value] = {
                    "current_usage": current_usage,
                    "daily_usage": daily_usage,
                    "monthly_usage": monthly_usage,
                    "daily_limit": quota.daily_limit,
                    "monthly_limit": quota.monthly_limit,
                    "per_job_limit": quota.per_job_limit,
                    "cost_per_unit": quota.cost_per_unit,
                    "daily_remaining": max(0, (quota.daily_limit or 0) - daily_usage),
                    "monthly_remaining": max(0, (quota.monthly_limit or 0) - monthly_usage),
                    "estimated_monthly_cost": monthly_usage * quota.cost_per_unit
                }
            else:
                quota_status[resource_type.value] = {
                    "current_usage": current_usage,
                    "daily_usage": daily_usage,
                    "monthly_usage": monthly_usage,
                    "no_quota_defined": True
                }
        
        return {
            "user_id": user_id,
            "tier": user_tier.value,
            "quotas": quota_status,
            "policy": user_policy.to_dict() if user_policy else None
        }
    
    def set_user_policy(self,
                       user_id: str,
                       tier: UserTier,
                       custom_limits: Optional[Dict[ResourceType, int]] = None,
                       allowed_solvers: Optional[List[str]] = None,
                       blocked_features: Optional[List[str]] = None,
                       budget_limit: Optional[float] = None) -> bool:
        """Set or update user policy."""
        policy = UserPolicy(
            user_id=user_id,
            tier=tier,
            custom_limits=custom_limits or {},
            allowed_solvers=allowed_solvers or [],
            blocked_features=blocked_features or [],
            budget_limit=budget_limit
        )
        
        with self._lock:
            self._user_policies[user_id] = policy
            self._save_policies()
        
        logger.info(f"Set policy for user {user_id}: tier {tier.value}")
        return True
    
    def get_cost_estimate(self,
                        user_id: str,
                        resource_type: ResourceType,
                        amount: float) -> Dict[str, Any]:
        """Get cost estimate for resource usage."""
        user_policy = self._user_policies.get(user_id)
        user_tier = user_policy.tier if user_policy else UserTier.FREE
        
        quota_key = f"{resource_type.value}_{user_tier.value}"
        quota = self._quotas.get(quota_key)
        
        if not quota:
            return {"cost": 0.0, "no_pricing": True}
        
        cost = amount * quota.cost_per_unit
        
        return {
            "cost": cost,
            "cost_per_unit": quota.cost_per_unit,
            "currency": "USD",
            "tier": user_tier.value
        }
    
    def get_billing_summary(self, user_id: str, month: Optional[int] = None, year: Optional[int] = None) -> Dict[str, Any]:
        """Get billing summary for user."""
        now = datetime.now()
        month = month or now.month
        year = year or now.year
        
        # Get usage for the billing period
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        billing_records = [
            r for r in self._usage_records
            if (r.user_id == user_id and
                r.timestamp >= start_date and r.timestamp < end_date)
        ]
        
        # Calculate costs by resource type
        costs_by_resource = {}
        total_cost = 0.0
        
        for resource_type in ResourceType:
            resource_records = [r for r in billing_records if r.resource_type == resource_type]
            
            if resource_records:
                user_policy = self._user_policies.get(user_id)
                user_tier = user_policy.tier if user_policy else UserTier.FREE
                
                quota_key = f"{resource_type.value}_{user_tier.value}"
                quota = self._quotas.get(quota_key)
                
                if quota:
                    usage_amount = sum(r.amount for r in resource_records)
                    cost = usage_amount * quota.cost_per_unit
                    costs_by_resource[resource_type.value] = {
                        "usage": usage_amount,
                        "cost": cost,
                        "unit": quota.cost_per_unit
                    }
                    total_cost += cost
        
        return {
            "user_id": user_id,
            "billing_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "month": month,
                "year": year
            },
            "costs_by_resource": costs_by_resource,
            "total_cost": total_cost,
            "currency": "USD"
        }


class FeatureFlagsAndCostControl:
    """Combined feature flags and cost control system."""
    
    def __init__(self):
        self.feature_manager = FeatureFlagManager()
        self.cost_manager = CostControlManager()
    
    def is_feature_enabled(self, flag_key: str, user_id: str) -> bool:
        """Check if feature is enabled for user."""
        user_policy = self.cost_manager._user_policies.get(user_id)
        user_tier = user_policy.tier if user_policy else UserTier.FREE
        
        return bool(self.feature_manager.get_flag(flag_key, user_tier))
    
    def can_use_solver(self, solver_name: str, user_id: str) -> tuple[bool, str]:
        """Check if user can use specific solver."""
        user_policy = self.cost_manager._user_policies.get(user_id)
        
        if not user_policy:
            return True, "No policy restrictions"
        
        if user_policy.allowed_solvers and solver_name not in user_policy.allowed_solvers:
            return False, f"Solver {solver_name} not in allowed list"
        
        return True, "Solver allowed"
    
    def get_platform_status(self) -> Dict[str, Any]:
        """Get overall platform status."""
        return {
            "feature_flags": {
                "total_flags": len(self.feature_manager._flags),
                "enabled_flags": len([f for f in self.feature_manager._flags.values() if f.current_value])
            },
            "cost_control": {
                "total_quotas": len(self.cost_manager._quotas),
                "total_users": len(self.cost_manager._user_policies),
                "total_usage_records": len(self.cost_manager._usage_records)
            },
            "timestamp": datetime.now().isoformat()
        }


# Global instances
FEATURE_FLAG_MANAGER = FeatureFlagManager()
COST_CONTROL_MANAGER = CostControlManager()
FEATURE_FLAGS_AND_COST_CONTROL = FeatureFlagsAndCostControl()
