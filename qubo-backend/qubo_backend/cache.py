"""
Performance Optimization Caching Layer for QUBO Portfolio Optimizer
Provides caching for solver capabilities, benchmark metadata, API connectivity state,
and GPU hardware information to reduce repeated API calls and improve responsiveness.
"""

import asyncio
import json
import logging
import hashlib
import time
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path
import threading

from .config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with value and expiration metadata."""
    
    value: Any
    created_at: datetime
    expires_at: datetime
    access_count: int = 0
    last_accessed: datetime = field(default_factory=datetime.now)
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def touch(self) -> None:
        """Update access statistics."""
        self.access_count += 1
        self.last_accessed = datetime.now()


class MemoryCache:
    """In-memory cache with thread-safe operations."""
    
    def __init__(self, max_size: int = 1000, default_ttl_seconds: int = 300):
        self.max_size = max_size
        self.default_ttl_seconds = default_ttl_seconds
        self._cache: Dict[str, CacheEntry] = {}
        self._lock = threading.RLock()
    
    def _make_key(self, key: Union[str, Dict, List, tuple]) -> str:
        """Generate a consistent cache key from various input types."""
        if isinstance(key, str):
            return key
        elif isinstance(key, (dict, list)):
            # Sort dict keys for consistency
            key_str = json.dumps(key, sort_keys=True)
        else:
            key_str = str(key)
        
        # Hash long keys to avoid memory issues
        if len(key_str) > 200:
            key_str = hashlib.md5(key_str.encode()).hexdigest()
        
        return key_str
    
    def get(self, key: Union[str, Dict, List, tuple], default: Any = None) -> Any:
        """Get value from cache."""
        cache_key = self._make_key(key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                return default
            
            if entry.is_expired:
                del self._cache[cache_key]
                return default
            
            entry.touch()
            return entry.value
    
    def set(self, key: Union[str, Dict, List, tuple], value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set value in cache with optional TTL."""
        cache_key = self._make_key(key)
        ttl = ttl_seconds or self.default_ttl_seconds
        
        with self._lock:
            # Remove oldest entries if cache is full
            if len(self._cache) >= self.max_size and cache_key not in self._cache:
                self._evict_oldest()
            
            now = datetime.now()
            entry = CacheEntry(
                value=value,
                created_at=now,
                expires_at=now + timedelta(seconds=ttl)
            )
            
            self._cache[cache_key] = entry
    
    def delete(self, key: Union[str, Dict, List, tuple]) -> bool:
        """Delete entry from cache."""
        cache_key = self._make_key(key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                return True
            return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count of removed items."""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if entry.is_expired
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            return len(expired_keys)
    
    def _evict_oldest(self) -> None:
        """Evict least recently used entry."""
        if not self._cache:
            return
        
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k].last_accessed
        )
        del self._cache[oldest_key]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_entries = len(self._cache)
            expired_entries = sum(1 for entry in self._cache.values() if entry.is_expired)
            
            total_accesses = sum(entry.access_count for entry in self._cache.values())
            
            return {
                "total_entries": total_entries,
                "expired_entries": expired_entries,
                "max_size": self.max_size,
                "utilization": total_entries / self.max_size if self.max_size > 0 else 0,
                "total_accesses": total_accesses,
                "average_accesses": total_accesses / total_entries if total_entries > 0 else 0
            }


class CacheManager:
    """
    Centralized cache management for the QUBO optimizer.
    
    Provides caching for:
    - Solver capability checks
    - Benchmark metadata
    - API connectivity state
    - GPU hardware information
    - Quantum package availability
    """
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize caches with different TTLs
        self.solver_capabilities = MemoryCache(max_size=500, default_ttl_seconds=600)  # 10 minutes
        self.benchmark_metadata = MemoryCache(max_size=200, default_ttl_seconds=1800)  # 30 minutes
        self.api_connectivity = MemoryCache(max_size=100, default_ttl_seconds=300)   # 5 minutes
        self.gpu_info = MemoryCache(max_size=50, default_ttl_seconds=3600)         # 1 hour
        self.quantum_packages = MemoryCache(max_size=100, default_ttl_seconds=7200)  # 2 hours
        self.system_metrics = MemoryCache(max_size=1000, default_ttl_seconds=60)    # 1 minute
        
        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self) -> None:
        """Start background task to clean expired entries."""
        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(300)  # Clean every 5 minutes
                    self.cleanup_all_caches()
                except Exception as e:
                    logger.error(f"Cache cleanup error: {e}")
        
        self._cleanup_task = asyncio.create_task(cleanup_loop())
    
    def cleanup_all_caches(self) -> Dict[str, int]:
        """Clean expired entries from all caches."""
        return {
            "solver_capabilities": self.solver_capabilities.cleanup_expired(),
            "benchmark_metadata": self.benchmark_metadata.cleanup_expired(),
            "api_connectivity": self.api_connectivity.cleanup_expired(),
            "gpu_info": self.gpu_info.cleanup_expired(),
            "quantum_packages": self.quantum_packages.cleanup_expired(),
            "system_metrics": self.system_metrics.cleanup_expired()
        }
    
    def get_solver_capabilities(self, solver_name: str, problem_params: Dict) -> Optional[Dict]:
        """Get cached solver capabilities."""
        key = {"solver": solver_name, "params": problem_params}
        return self.solver_capabilities.get(key)
    
    def set_solver_capabilities(self, solver_name: str, problem_params: Dict, capabilities: Dict) -> None:
        """Cache solver capabilities."""
        key = {"solver": solver_name, "params": problem_params}
        self.solver_capabilities.set(key, capabilities)
    
    def get_benchmark_result(self, solver_name: str, problem_hash: str) -> Optional[Dict]:
        """Get cached benchmark result."""
        key = {"solver": solver_name, "problem": problem_hash}
        return self.benchmark_metadata.get(key)
    
    def set_benchmark_result(self, solver_name: str, problem_hash: str, result: Dict) -> None:
        """Cache benchmark result."""
        key = {"solver": solver_name, "problem": problem_hash}
        self.benchmark_metadata.set(key, result)
    
    def get_api_connectivity(self, service_name: str) -> Optional[Dict]:
        """Get cached API connectivity status."""
        return self.api_connectivity.get(service_name)
    
    def set_api_connectivity(self, service_name: str, status: Dict) -> None:
        """Cache API connectivity status."""
        self.api_connectivity.set(service_name, status)
    
    def get_gpu_info(self) -> Optional[Dict]:
        """Get cached GPU information."""
        return self.gpu_info.get("gpu_info")
    
    def set_gpu_info(self, gpu_info: Dict) -> None:
        """Cache GPU information."""
        self.gpu_info.set("gpu_info", gpu_info)
    
    def get_quantum_package_status(self, package_name: str) -> Optional[Dict]:
        """Get cached quantum package status."""
        return self.quantum_packages.get(package_name)
    
    def set_quantum_package_status(self, package_name: str, status: Dict) -> None:
        """Cache quantum package status."""
        self.quantum_packages.set(package_name, status)
    
    def get_system_metrics(self, metric_name: str) -> Optional[Any]:
        """Get cached system metrics."""
        return self.system_metrics.get(metric_name)
    
    def set_system_metrics(self, metric_name: str, value: Any, ttl_seconds: int = 60) -> None:
        """Cache system metrics with custom TTL."""
        self.system_metrics.set(metric_name, value, ttl_seconds)
    
    def invalidate_solver_cache(self, solver_name: Optional[str] = None) -> None:
        """Invalidate solver-related cache entries."""
        if solver_name:
            # Invalidate specific solver
            keys_to_remove = []
            for key in self.solver_capabilities._cache.keys():
                if isinstance(key, str) and solver_name in key:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                self.solver_capabilities.delete(key)
        else:
            # Invalidate all solver caches
            self.solver_capabilities.clear()
    
    def invalidate_benchmark_cache(self) -> None:
        """Invalidate all benchmark cache entries."""
        self.benchmark_metadata.clear()
    
    def invalidate_connectivity_cache(self, service_name: Optional[str] = None) -> None:
        """Invalidate connectivity cache entries."""
        if service_name:
            self.api_connectivity.delete(service_name)
        else:
            self.api_connectivity.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        return {
            "solver_capabilities": self.solver_capabilities.get_stats(),
            "benchmark_metadata": self.benchmark_metadata.get_stats(),
            "api_connectivity": self.api_connectivity.get_stats(),
            "gpu_info": self.gpu_info.get_stats(),
            "quantum_packages": self.quantum_packages.get_stats(),
            "system_metrics": self.system_metrics.get_stats()
        }
    
    def export_cache_state(self) -> Dict[str, Any]:
        """Export current cache state for debugging."""
        return {
            "timestamp": datetime.now().isoformat(),
            "stats": self.get_cache_stats(),
            "settings": {
                "solver_capabilities_ttl": self.solver_capabilities.default_ttl_seconds,
                "benchmark_metadata_ttl": self.benchmark_metadata.default_ttl_seconds,
                "api_connectivity_ttl": self.api_connectivity.default_ttl_seconds,
                "gpu_info_ttl": self.gpu_info.default_ttl_seconds,
                "quantum_packages_ttl": self.quantum_packages.default_ttl_seconds,
                "system_metrics_ttl": self.system_metrics.default_ttl_seconds
            }
        }


def cache_result(ttl_seconds: int = 300, cache_manager: Optional[CacheManager] = None, 
                cache_name: str = "system_metrics"):
    """
    Decorator to cache function results.
    
    Args:
        ttl_seconds: Time to live for cached results
        cache_manager: Cache manager instance (uses global if None)
        cache_name: Name of cache to use
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            cm = cache_manager or CACHE_MANAGER
            cache = getattr(cm, cache_name)
            
            # Generate cache key from function name and arguments
            key = {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        
        def sync_wrapper(*args, **kwargs):
            cm = cache_manager or CACHE_MANAGER
            cache = getattr(cm, cache_name)
            
            # Generate cache key from function name and arguments
            key = {
                "function": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            
            # Try to get from cache
            cached_result = cache.get(key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(key, result, ttl_seconds)
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global cache manager instance
CACHE_MANAGER = CacheManager()
