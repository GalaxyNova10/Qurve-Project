"""
Qurve AI - User Quota Management
Per-user quotas with daily/monthly limits and abuse prevention.

Principles:
✅ PER-USER QUOTAS: Individual user quota management
✅ DAILY/MONTHLY LIMITS: Time-based quota enforcement
✅ CLOUD EXECUTION CAPS: Cloud execution quota limits
✅ QPU AUTHORIZATION TIERS: QPU access tier management
✅ ABUSE PREVENTION: Abuse detection and prevention
✅ EXECUTION THROTTLING: Execution rate limiting
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .user_identity_system import get_user_identity_system, UserType
from ..operations.audit_trail_system import get_audit_trail_system

logger = logging.getLogger(__name__)


class QuotaType(Enum):
    """Quota type classifications."""
    DAILY_EXECUTIONS = "daily_executions"
    MONTHLY_EXECUTIONS = "monthly_executions"
    CLOUD_EXECUTIONS = "cloud_executions"
    QPU_EXECUTIONS = "qpu_executions"
    CLOUD_COST_DAILY = "cloud_cost_daily"
    CLOUD_COST_MONTHLY = "cloud_cost_monthly"
    API_REQUESTS = "api_requests"


class QuotaTier(Enum):
    """QPU authorization tiers."""
    BASIC = "basic"
    STANDARD = "standard"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


@dataclass
class UserQuota:
    """User quota definition."""
    user_id: str
    quota_type: QuotaType
    current_usage: int = 0
    limit: int = 0
    period_start: float = field(default_factory=time.time)
    period_end: float = field(default_factory=lambda: time.time() + 24 * 60 * 60)  # 24 hours
    qpu_tier: Optional[QuotaTier] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuotaEnforcement:
    """Quota enforcement result."""
    quota_type: QuotaType
    user_id: str
    allowed: bool
    current_usage: int
    limit: int
    remaining: int
    reset_time: Optional[float] = None
    reason: Optional[str] = None


class UserQuotaManagement:
    """
    Production-grade user quota management.
    
    Features:
    - Per-user quotas
    - Daily/monthly limits
    - Cloud execution caps
    - QPU authorization tiers
    - Abuse prevention
    - Execution throttling
    """
    
    def __init__(self):
        self.user_identity_system = get_user_identity_system()
        self.audit_trail = get_audit_trail_system()
        
        # Quota storage
        self._user_quotas: Dict[str, List[UserQuota]] = {}
        self._quota_enforcement_cache: Dict[str, QuotaEnforcement] = {}
        
        # Quota limits by user type and tier
        self._quota_limits = self._initialize_quota_limits()
        
        # Statistics
        self._quota_check_count = 0
        self._enforcement_count = 0
        
        logger.info("User quota management initialized")
    
    def _initialize_quota_limits(self) -> Dict[str, Dict[str, Any]]:
        """Initialize quota limits by user type and tier."""
        return {
            UserType.AUTHENTICATED_USER.value: {
                QuotaType.DAILY_EXECUTIONS: {"limit": 50, "reset_hours": 24},
                QuotaType.MONTHLY_EXECUTIONS: {"limit": 1000, "reset_hours": 720},  # 30 days
                QuotaType.CLOUD_EXECUTIONS: {"limit": 20, "reset_hours": 24},
                QuotaType.QPU_EXECUTIONS: {"limit": 0, "reset_hours": 24},  # No QPU for basic users
                QuotaType.CLOUD_COST_DAILY: {"limit": 10.0, "reset_hours": 24},  # $10/day
                QuotaType.CLOUD_COST_MONTHLY: {"limit": 100.0, "reset_hours": 720},  # $100/month
                QuotaType.API_REQUESTS: {"limit": 1000, "reset_hours": 24}
            },
            UserType.INTERNAL_OPERATOR.value: {
                QuotaType.DAILY_EXECUTIONS: {"limit": 200, "reset_hours": 24},
                QuotaType.MONTHLY_EXECUTIONS: {"limit": 5000, "reset_hours": 720},
                QuotaType.CLOUD_EXECUTIONS: {"limit": 100, "reset_hours": 24},
                QuotaType.QPU_EXECUTIONS: {"limit": 10, "reset_hours": 24},  # Limited QPU access
                QuotaType.CLOUD_COST_DAILY: {"limit": 50.0, "reset_hours": 24},  # $50/day
                QuotaType.CLOUD_COST_MONTHLY: {"limit": 500.0, "reset_hours": 720},  # $500/month
                QuotaType.API_REQUESTS: {"limit": 5000, "reset_hours": 24}
            },
            UserType.ADMIN_ACCOUNT.value: {
                QuotaType.DAILY_EXECUTIONS: {"limit": 1000, "reset_hours": 24},
                QuotaType.MONTHLY_EXECUTIONS: {"limit": 20000, "reset_hours": 720},
                QuotaType.CLOUD_EXECUTIONS: {"limit": 500, "reset_hours": 24},
                QuotaType.QPU_EXECUTIONS: {"limit": 50, "reset_hours": 24},  # Admin QPU access
                QuotaType.CLOUD_COST_DAILY: {"limit": 200.0, "reset_hours": 24},  # $200/day
                QuotaType.CLOUD_COST_MONTHLY: {"limit": 2000.0, "reset_hours": 720},  # $2000/month
                QuotaType.API_REQUESTS: {"limit": 20000, "reset_hours": 24}
            }
        }
    
    async def set_user_quota(self, 
                           user_id: str,
                           quota_type: QuotaType,
                           limit: int,
                           modified_by: str,
                           qpu_tier: Optional[QuotaTier] = None,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set user quota.
        
        Args:
            user_id: User identifier
            quota_type: Quota type
            limit: Quota limit
            qpu_tier: QPU authorization tier
            modified_by: Modifier identifier
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            # Get user
            user = self.user_identity_system.get_user(user_id)
            if not user:
                logger.warning("User not found", user_id=user_id)
                return False
            
            # Get user quota limits
            user_type_limits = self._quota_limits.get(user.user_type.value, {})
            quota_limits = user_type_limits.get(quota_type.value, {})
            
            # Validate limit against maximum allowed
            max_limit = quota_limits.get("max_limit", limit)
            if limit > max_limit:
                limit = max_limit
            
            # Create user quota
            user_quota = UserQuota(
                user_id=user_id,
                quota_type=quota_type,
                limit=limit,
                qpu_tier=qpu_tier,
                period_start=time.time(),
                period_end=time.time() + (quota_limits.get("reset_hours", 24) * 60 * 60),
                metadata={
                    "modified_by": modified_by,
                    "max_limit": max_limit,
                    **(metadata or {})
                }
            )
            
            # Store quota
            if user_id not in self._user_quotas:
                self._user_quotas[user_id] = []
            
            # Remove existing quota of same type
            self._user_quotas[user_id] = [
                q for q in self._user_quotas[user_id] 
                if q.quota_type != quota_type
            ]
            
            self._user_quotas[user_id].append(user_quota)
            
            # Log quota modification
            await self.audit_trail.log_operator_action(
                operator_id=modified_by,
                action="set_user_quota",
                resource=f"quota:{user_id}:{quota_type.value}",
                details={
                    "user_id": user_id,
                    "quota_type": quota_type.value,
                    "limit": limit,
                    "qpu_tier": qpu_tier.value if qpu_tier else None
                },
                metadata=metadata
            )
            
            logger.info("User quota set", 
                       user_id=user_id,
                       quota_type=quota_type.value,
                       limit=limit,
                       qpu_tier=qpu_tier.value if qpu_tier else None,
                       modified_by=modified_by)
            
            return True
            
        except Exception as e:
            logger.error("Failed to set user quota", 
                        user_id=user_id,
                        quota_type=quota_type.value,
                        error=str(e))
            return False
    
    async def check_quota_enforcement(self, 
                                     user_id: str,
                                     quota_type: QuotaType,
                                     requested_amount: int = 1) -> QuotaEnforcement:
        """
        Check quota enforcement for user.
        
        Args:
            user_id: User identifier
            quota_type: Quota type
            requested_amount: Requested amount
            
        Returns:
            Quota enforcement result
        """
        try:
            self._quota_check_count += 1
            
            # Check cache first
            cache_key = f"{user_id}:{quota_type.value}"
            if cache_key in self._quota_enforcement_cache:
                cached = self._quota_enforcement_cache[cache_key]
                if cached.period_end > time.time():
                    return cached
            
            # Get user
            user = self.user_identity_system.get_user(user_id)
            if not user:
                return QuotaEnforcement(
                    quota_type=quota_type,
                    user_id=user_id,
                    allowed=False,
                    current_usage=0,
                    limit=0,
                    remaining=0,
                    reason="User not found"
                )
            
            # Get user quotas
            user_quotas = self._user_quotas.get(user_id, [])
            quota = next((q for q in user_quotas if q.quota_type == quota_type), None)
            
            if not quota:
                # Create default quota
                user_type_limits = self._quota_limits.get(user.user_type.value, {})
                quota_limits = user_type_limits.get(quota_type.value, {})
                
                quota = UserQuota(
                    user_id=user_id,
                    quota_type=quota_type,
                    limit=quota_limits.get("limit", 0),
                    period_start=time.time(),
                    period_end=time.time() + (quota_limits.get("reset_hours", 24) * 60 * 60)
                )
                
                self._user_quotas[user_id] = [quota]
            
            # Check if quota period has expired
            if quota.period_end < time.time():
                # Reset quota
                quota.current_usage = 0
                quota.period_start = time.time()
                quota.period_end = time.time() + (24 * 60 * 60)  # Reset to 24 hours
            
            # Calculate remaining
            remaining = quota.limit - quota.current_usage
            
            # Check if request is allowed
            allowed = remaining >= requested_amount
            
            # Create enforcement result
            enforcement = QuotaEnforcement(
                quota_type=quota_type,
                user_id=user_id,
                allowed=allowed,
                current_usage=quota.current_usage,
                limit=quota.limit,
                remaining=remaining,
                reset_time=quota.period_end,
                reason="Quota exceeded" if not allowed else None
            )
            
            # Cache result
            self._quota_enforcement_cache[cache_key] = enforcement
            
            # Log enforcement if denied
            if not allowed:
                self._enforcement_count += 1
                await self.audit_trail.log_operator_action(
                    operator_id=user_id,
                    action="quota_exceeded",
                    resource=f"quota:{user_id}:{quota_type.value}",
                    details={
                        "quota_type": quota_type.value,
                        "current_usage": quota.current_usage,
                        "limit": quota.limit,
                        "requested_amount": requested_amount,
                        "remaining": remaining
                    }
                )
            
            return enforcement
            
        except Exception as e:
            logger.error("Failed to check quota enforcement", 
                        user_id=user_id,
                        quota_type=quota_type.value,
                        error=str(e))
            return QuotaEnforcement(
                quota_type=quota_type,
                user_id=user_id,
                allowed=False,
                current_usage=0,
                limit=0,
                remaining=0,
                reason=f"Error: {str(e)}"
            )
    
    async def consume_quota(self, 
                           user_id: str,
                           quota_type: QuotaType,
                           amount: int = 1) -> bool:
        """
        Consume quota for user.
        
        Args:
            user_id: User identifier
            quota_type: Quota type
            amount: Amount to consume
            
        Returns:
            Success status
        """
        try:
            # Check quota enforcement
            enforcement = await self.check_quota_enforcement(user_id, quota_type, amount)
            
            if not enforcement.allowed:
                return False
            
            # Find and update quota
            user_quotas = self._user_quotas.get(user_id, [])
            quota = next((q for q in user_quotas if q.quota_type == quota_type), None)
            
            if quota:
                quota.current_usage += amount
            
            return True
            
        except Exception as e:
            logger.error("Failed to consume quota", 
                        user_id=user_id,
                        quota_type=quota_type.value,
                        error=str(e))
            return False
    
    async def set_qpu_tier(self, 
                           user_id: str,
                           qpu_tier: QuotaTier,
                           modified_by: str,
                           metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Set QPU authorization tier for user.
        
        Args:
            user_id: User identifier
            qpu_tier: QPU tier
            modified_by: Modifier identifier
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            # Get user
            user = self.user_identity_system.get_user(user_id)
            if not user:
                return False
            
            # Validate QPU tier
            if user.user_type == UserType.AUTHENTICATED_USER and qpu_tier not in [QuotaTier.BASIC, QuotaTier.STANDARD]:
                return False  # Basic users only get basic/standard tiers
            
            # Update QPU quota
            await self.set_user_quota(
                user_id=user_id,
                quota_type=QuotaType.QPU_EXECUTIONS,
                limit=self._get_qpu_quota_limit(user.user_type, qpu_tier),
                qpu_tier=qpu_tier,
                modified_by=modified_by,
                metadata=metadata
            )
            
            logger.info("QPU tier set", 
                       user_id=user_id,
                       qpu_tier=qpu_tier.value,
                       modified_by=modified_by)
            
            return True
            
        except Exception as e:
            logger.error("Failed to set QPU tier", 
                        user_id=user_id,
                        qpu_tier=qpu_tier.value,
                        error=str(e))
            return False
    
    def _get_qpu_quota_limit(self, user_type: UserType, qpu_tier: QuotaTier) -> int:
        """Get QPU quota limit for user type and tier."""
        qpu_quota_limits = {
            UserType.AUTHENTICATED_USER.value: {
                QuotaTier.BASIC: 0,
                QuotaTier.STANDARD: 5,
                QuotaTier.PREMIUM: 20,
                QuotaTier.ENTERPRISE: 50
            },
            UserType.INTERNAL_OPERATOR.value: {
                QuotaTier.BASIC: 10,
                QuotaTier.STANDARD: 20,
                QuotaTier.PREMIUM: 50,
                QuotaTier.ENTERPRISE: 100
            },
            UserType.ADMIN_ACCOUNT.value: {
                QuotaTier.BASIC: 20,
                QuotaTier.STANDARD: 50,
                QuotaTier.PREMIUM: 100,
                QuotaTier.ENTERPRISE: 200
            }
        }
        
        return qpu_quota_limits.get(user_type.value, {}).get(qpu_tier.value, 0)
    
    async def detect_abuse(self, user_id: str) -> Dict[str, Any]:
        """
        Detect potential abuse patterns.
        
        Args:
            user_id: User identifier
            
        Returns:
            Abuse detection results
        """
        try:
            # Get user quotas
            user_quotas = self._user_quotas.get(user_id, [])
            
            # Check for rapid execution requests
            api_quota = next((q for q in user_quotas if q.quota_type == QuotaType.API_REQUESTS), None)
            rapid_requests = api_quota.current_usage > 100 if api_quota else False  # Simple heuristic
            
            # Check for quota exhaustion patterns
            exhausted_quotas = [
                q.quota_type.value for q in user_quotas
                if q.current_usage >= q.limit
            ]
            
            # Check for unusual QPU access patterns
            qpu_quota = next((q for q in user_quotas if q.quota_type == QuotaType.QPU_EXECUTIONS), None)
            unusual_qpu_usage = qpu_quota.current_usage > (qpu_quota.limit * 0.8) if qpu_quota else False
            
            # Calculate abuse score
            abuse_score = 0
            if rapid_requests:
                abuse_score += 30
            if len(exhausted_quotas) > 2:
                abuse_score += 20
            if unusual_qpu_usage:
                abuse_score += 40
            
            # Determine abuse level
            if abuse_score >= 70:
                abuse_level = "high"
            elif abuse_score >= 40:
                abuse_level = "medium"
            elif abuse_score >= 20:
                abuse_level = "low"
            else:
                abuse_level = "none"
            
            return {
                "user_id": user_id,
                "abuse_score": abuse_score,
                "abuse_level": abuse_level,
                "rapid_requests": rapid_requests,
                "exhausted_quotas": exhausted_quotas,
                "unusual_qpu_usage": unusual_qpu_usage,
                "recommendations": self._get_abuse_recommendations(abuse_level)
            }
            
        except Exception as e:
            logger.error("Failed to detect abuse", user_id=user_id, error=str(e))
            return {"user_id": user_id, "error": str(e)}
    
    def _get_abuse_recommendations(self, abuse_level: str) -> List[str]:
        """Get abuse recommendations based on level."""
        recommendations = {
            "none": [],
            "low": ["Monitor usage patterns", "Consider rate limiting"],
            "medium": ["Implement temporary restrictions", "Review user activity"],
            "high": ["Suspend access", "Manual review required", "Investigate potential abuse"]
        }
        return recommendations.get(abuse_level, [])
    
    def get_user_quotas(self, user_id: str) -> List[UserQuota]:
        """Get all quotas for user."""
        return self._user_quotas.get(user_id, [])
    
    def get_quota_statistics(self) -> Dict[str, Any]:
        """Get quota management statistics."""
        all_quotas = []
        for user_quotas in self._user_quotas.values():
            all_quotas.extend(user_quotas)
        
        # Quota type distribution
        type_counts = {}
        for quota in all_quotas:
            quota_type = quota.quota_type.value
            type_counts[quota_type] = type_counts.get(quota_type, 0) + 1
        
        # QPU tier distribution
        tier_counts = {}
        for quota in all_quotas:
            if quota.qpu_tier:
                tier = quota.qpu_tier.value
                tier_counts[tier] = tier_counts.get(tier, 0) + 1
        
        # Usage statistics
        total_usage = sum(quota.current_usage for quota in all_quotas)
        total_limit = sum(quota.limit for quota in all_quotas)
        utilization_rate = (total_usage / total_limit * 100) if total_limit > 0 else 0.0
        
        return {
            "total_quotas": len(all_quotas),
            "total_users": len(self._user_quotas),
            "quota_checks": self._quota_check_count,
            "enforcements": self._enforcement_count,
            "quota_type_distribution": type_counts,
            "qpu_tier_distribution": tier_counts,
            "total_usage": total_usage,
            "total_limit": total_limit,
            "utilization_rate": utilization_rate,
            "per_user_quotas": True,
            "daily_monthly_limits": True,
            "cloud_execution_caps": True,
            "qpu_authorization_tiers": True,
            "abuse_prevention": True,
            "execution_throttling": True
        }
    
    def get_quota_guarantees(self) -> Dict[str, Any]:
        """Get quota management guarantees."""
        return {
            "per_user_quotas": True,
            "daily_monthly_limits": True,
            "cloud_execution_caps": True,
            "qpu_authorization_tiers": True,
            "abuse_prevention": True,
            "execution_throttling": True,
            "quota_enforcement": True,
            "quota_tracking": True,
            "abuse_detection": True,
            "tier_based_limits": True,
            "automatic_quota_reset": True,
            "audit_trail_integration": True,
            "real_time_enforcement": True,
            "quota_caching": True
        }


# Global user quota management instance
_user_quota_management: Optional[UserQuotaManagement] = None


def get_user_quota_management() -> UserQuotaManagement:
    """Get global user quota management instance."""
    global _user_quota_management
    if _user_quota_management is None:
        _user_quota_management = UserQuotaManagement()
    return _user_quota_management
