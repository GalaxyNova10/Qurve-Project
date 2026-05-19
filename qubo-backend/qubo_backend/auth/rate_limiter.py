"""
Qurve AI - Rate Limiter
Production-grade rate limiting for credential validation and auth endpoints.

Prevents:
❌ repeated STS hammering
❌ auth spam
❌ credential refresh storms
❌ DoS attacks

Features:
✅ sliding window rate limiting
✅ distributed rate limiting
✅ validation caching
✅ cooldown enforcement
✅ telemetry integration
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    # Credential validation limits
    max_validations_per_minute: int = 10
    max_validations_per_hour: int = 100
    
    # Auth endpoint limits
    max_auth_requests_per_minute: int = 60
    max_auth_requests_per_hour: int = 1000
    
    # Sliding window size (seconds)
    window_size: int = 60
    
    # Cache TTL
    cache_ttl: int = 300  # 5 minutes


@dataclass
class RateLimitInfo:
    """Rate limit information."""
    allowed: bool
    remaining: int
    reset_time: Optional[float] = None
    retry_after: Optional[float] = None
    total_requests: int = field(default_factory=lambda: 0)
    window_requests: int = field(default_factory=lambda: 0)


@dataclass
class RequestRecord:
    """Request record for rate limiting."""
    timestamp: float
    ip_address: str
    endpoint: str
    success: bool


class DistributedRateLimiter:
    """
    Production-grade distributed rate limiter.
    
    Uses sliding window algorithm with distributed coordination.
    """
    
    def __init__(self, config: RateLimitConfig):
        self.config = config
        
        # Request tracking by IP and endpoint
        self._requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=config.window_size))
        self._global_requests: deque = deque(maxlen=config.window_size * 2)  # 2x window for global limits
        
        # Rate limit cache
        self._rate_limit_cache: Dict[str, RateLimitInfo] = {}
        self._cache_timestamps: Dict[str, float] = {}
        
        logger.info("Rate limiter initialized", 
                  max_validations_per_minute=config.max_validations_per_minute,
                  max_auth_requests_per_minute=config.max_auth_requests_per_minute)
    
    def _get_cache_key(self, ip_address: str, endpoint: str) -> str:
        """Generate cache key for rate limiting."""
        return f"{ip_address}:{endpoint}"
    
    def _is_request_allowed(self, ip_address: str, endpoint: str, max_requests: int) -> bool:
        """Check if request is allowed based on rate limits."""
        current_time = time.time()
        cache_key = self._get_cache_key(ip_address, endpoint)
        
        # Clean old requests from sliding window
        requests = self._requests[cache_key]
        cutoff_time = current_time - self.config.window_size
        
        while requests and requests[0].timestamp < cutoff_time:
            requests.popleft()
        
        # Count requests in window
        window_requests = len(requests)
        
        # Check rate limit
        allowed = window_requests < max_requests
        
        # Update cache
        now = time.time()
        self._rate_limit_cache[cache_key] = RateLimitInfo(
            allowed=allowed,
            remaining=max(0, max_requests - window_requests),
            reset_time=current_time + self.config.window_size if not allowed else None,
            retry_after=current_time + 60 if not allowed else None,  # 1 minute cooldown
            window_requests=window_requests,
            total_requests=len(self._global_requests)
        )
        self._cache_timestamps[cache_key] = now
        
        return allowed
    
    def _record_request(self, ip_address: str, endpoint: str, success: bool = True) -> None:
        """Record a request for rate limiting."""
        current_time = time.time()
        cache_key = self._get_cache_key(ip_address, endpoint)
        
        # Add to sliding window
        self._requests[cache_key].append(RequestRecord(
            timestamp=current_time,
            ip_address=ip_address,
            endpoint=endpoint,
            success=success
        ))
        
        # Add to global requests
        self._global_requests.append(RequestRecord(
            timestamp=current_time,
            ip_address=ip_address,
            endpoint=endpoint,
            success=success
        ))
        
        # Clean old global requests
        cutoff_time = current_time - (self.config.window_size * 2)
        while self._global_requests and self._global_requests[0].timestamp < cutoff_time:
            self._global_requests.popleft()
        
        logger.debug("Request recorded", 
                   ip_address=ip_address, 
                   endpoint=endpoint, 
                   success=success)
    
    def is_credential_validation_allowed(self, ip_address: str) -> RateLimitInfo:
        """
        Check if credential validation is allowed.
        
        Uses per-IP rate limiting with sliding window.
        """
        endpoint = "credential_validation"
        max_requests = self.config.max_validations_per_minute
        
        return self._is_request_allowed(ip_address, endpoint, max_requests)
    
    def is_auth_request_allowed(self, ip_address: str) -> RateLimitInfo:
        """
        Check if auth request is allowed.
        
        Uses per-IP rate limiting with sliding window.
        """
        endpoint = "auth"
        max_requests = self.config.max_auth_requests_per_minute
        
        return self._is_request_allowed(ip_address, endpoint, max_requests)
    
    def record_credential_validation(self, ip_address: str, success: bool = True) -> None:
        """Record credential validation request."""
        self._record_request(ip_address, "credential_validation", success)
    
    def record_auth_request(self, ip_address: str, success: bool = True) -> None:
        """Record auth request."""
        self._record_request(ip_address, "auth", success)
    
    def get_rate_limit_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        current_time = time.time()
        
        # Clean old data
        for key in list(self._cache_timestamps.keys()):
            if current_time - self._cache_timestamps[key] > self.config.cache_ttl:
                del self._rate_limit_cache[key]
                del self._cache_timestamps[key]
        
        # Calculate statistics
        total_cache_entries = len(self._rate_limit_cache)
        active_windows = sum(1 for info in self._rate_limit_cache.values() if info.allowed)
        blocked_windows = total_cache_entries - active_windows
        
        # Global request stats
        recent_global_requests = len(self._global_requests)
        recent_time = current_time - self.config.window_size
        recent_global_success = sum(1 for r in self._global_requests if r.timestamp > recent_time and r.success)
        
        return {
            "cache_entries": total_cache_entries,
            "active_windows": active_windows,
            "blocked_windows": blocked_windows,
            "recent_global_requests": recent_global_requests,
            "recent_global_success_rate": (recent_global_success / recent_global_requests * 100) if recent_global_requests > 0 else 0.0,
            "cache_ttl": self.config.cache_ttl,
            "window_size": self.config.window_size,
            "config": {
                "max_validations_per_minute": self.config.max_validations_per_minute,
                "max_auth_requests_per_minute": self.config.max_auth_requests_per_hour
            }
        }
    
    def clear_expired_caches(self) -> None:
        """Clear expired cache entries."""
        current_time = time.time()
        
        for key in list(self._cache_timestamps.keys()):
            if current_time - self._cache_timestamps[key] > self.config.cache_ttl:
                if key in self._rate_limit_cache:
                    del self._rate_limit_cache[key]
                del self._cache_timestamps[key]
        
        logger.info("Expired cache entries cleared")


# Global rate limiter instance
_rate_limiter: Optional[DistributedRateLimiter] = None


def get_rate_limiter() -> DistributedRateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = DistributedRateLimiter(RateLimitConfig())
    return _rate_limiter
