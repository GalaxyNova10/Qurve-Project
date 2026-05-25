"""
Performance & Stability Framework for QUBO Portfolio Optimizer
Ensures production-ready operation with async API support, proper error handling,
memory management, resource cleanup, and timeout handling.
"""

import asyncio
import logging
import time
import traceback
import signal
import sys
from typing import Any, Callable, Dict, List, Optional, Union, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from functools import wraps
import psutil
import torch

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring."""
    
    operation_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    memory_mb: float = 0.0
    gpu_memory_mb: float = 0.0
    success: bool = True
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class PerformanceMonitor:
    """Monitor and track performance metrics."""
    
    def __init__(self):
        self._metrics: List[PerformanceMetrics] = []
        self._lock = asyncio.Lock()
        self._max_metrics = 10000  # Keep last 10k metrics
        
    async def record_metric(self, metric: PerformanceMetrics) -> None:
        """Record a performance metric."""
        async with self._lock:
            self._metrics.append(metric)
            
            # Keep only recent metrics
            if len(self._metrics) > self._max_metrics:
                self._metrics = self._metrics[-self._max_metrics:]
    
    def get_metrics(self, 
                   operation_name: Optional[str] = None,
                   since: Optional[datetime] = None,
                   limit: int = 100) -> List[PerformanceMetrics]:
        """Get performance metrics with optional filtering."""
        filtered_metrics = self._metrics
        
        if operation_name:
            filtered_metrics = [m for m in filtered_metrics if m.operation_name == operation_name]
        
        if since:
            filtered_metrics = [m for m in filtered_metrics if m.start_time >= since]
        
        # Return most recent metrics
        return filtered_metrics[-limit:] if limit > 0 else filtered_metrics
    
    def get_performance_summary(self, operation_name: str, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for an operation."""
        since = datetime.now() - timedelta(hours=hours)
        metrics = [m for m in self._metrics 
                  if m.operation_name == operation_name and m.start_time >= since]
        
        if not metrics:
            return {
                "operation": operation_name,
                "period_hours": hours,
                "total_executions": 0,
                "success_rate": 0.0,
                "average_duration_ms": 0.0,
                "p95_duration_ms": 0.0,
                "p99_duration_ms": 0.0,
                "average_memory_mb": 0.0,
                "error_count": 0
            }
        
        successful_metrics = [m for m in metrics if m.success]
        durations = [m.duration_ms for m in successful_metrics]
        memory_usage = [m.memory_mb for m in metrics if m.memory_mb > 0]
        
        # Calculate percentiles
        sorted_durations = sorted(durations)
        p95_idx = int(len(sorted_durations) * 0.95)
        p99_idx = int(len(sorted_durations) * 0.99)
        
        return {
            "operation": operation_name,
            "period_hours": hours,
            "total_executions": len(metrics),
            "success_rate": (len(successful_metrics) / len(metrics)) * 100,
            "average_duration_ms": sum(durations) / len(durations) if durations else 0,
            "p95_duration_ms": sorted_durations[p95_idx] if p95_idx < len(sorted_durations) else 0,
            "p99_duration_ms": sorted_durations[p99_idx] if p99_idx < len(sorted_durations) else 0,
            "average_memory_mb": sum(memory_usage) / len(memory_usage) if memory_usage else 0,
            "error_count": len(metrics) - len(successful_metrics)
        }


# Global performance monitor
PERFORMANCE_MONITOR = PerformanceMonitor()


def monitor_performance(operation_name: str, 
                      include_memory: bool = True,
                      include_gpu_memory: bool = True):
    """
    Decorator to monitor function performance.
    
    Args:
        operation_name: Name of the operation for metrics
        include_memory: Whether to track memory usage
        include_gpu_memory: Whether to track GPU memory usage
    """
    def decorator(func: Callable) -> Callable:
        async def async_wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            # Get initial memory usage
            initial_memory = 0
            initial_gpu_memory = 0
            
            if include_memory:
                process = psutil.Process()
                initial_memory = process.memory_info().rss / (1024 * 1024)
            
            if include_gpu_memory and torch.cuda.is_available():
                initial_gpu_memory = torch.cuda.memory_allocated() / (1024 * 1024)
            
            try:
                # Execute function
                result = await func(*args, **kwargs)
                
                # Calculate final metrics
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                final_memory = 0
                final_gpu_memory = 0
                
                if include_memory:
                    process = psutil.Process()
                    final_memory = process.memory_info().rss / (1024 * 1024)
                
                if include_gpu_memory and torch.cuda.is_available():
                    final_gpu_memory = torch.cuda.memory_allocated() / (1024 * 1024)
                
                # Record metric
                metric = PerformanceMetrics(
                    operation_name=operation_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    memory_mb=final_memory - initial_memory,
                    gpu_memory_mb=final_gpu_memory - initial_gpu_memory,
                    success=True
                )
                
                await PERFORMANCE_MONITOR.record_metric(metric)
                return result
                
            except Exception as e:
                # Record error metric
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                metric = PerformanceMetrics(
                    operation_name=operation_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    memory_mb=0,
                    gpu_memory_mb=0,
                    success=False,
                    error_message=str(e)
                )
                
                await PERFORMANCE_MONITOR.record_metric(metric)
                raise
        
        def sync_wrapper(*args, **kwargs):
            start_time = datetime.now()
            
            # Get initial memory usage
            initial_memory = 0
            if include_memory:
                process = psutil.Process()
                initial_memory = process.memory_info().rss / (1024 * 1024)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Calculate final metrics
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                final_memory = 0
                if include_memory:
                    process = psutil.Process()
                    final_memory = process.memory_info().rss / (1024 * 1024)
                
                # Record metric (synchronously)
                metric = PerformanceMetrics(
                    operation_name=operation_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    memory_mb=final_memory - initial_memory,
                    gpu_memory_mb=0,
                    success=True
                )
                
                # Schedule async recording
                asyncio.create_task(PERFORMANCE_MONITOR.record_metric(metric))
                return result
                
            except Exception as e:
                # Record error metric
                end_time = datetime.now()
                duration_ms = (end_time - start_time).total_seconds() * 1000
                
                metric = PerformanceMetrics(
                    operation_name=operation_name,
                    start_time=start_time,
                    end_time=end_time,
                    duration_ms=duration_ms,
                    memory_mb=0,
                    gpu_memory_mb=0,
                    success=False,
                    error_message=str(e)
                )
                
                asyncio.create_task(PERFORMANCE_MONITOR.record_metric(metric))
                raise
        
        # Return appropriate wrapper
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class TimeoutError(Exception):
    """Custom timeout error."""
    pass


async def with_timeout(coro: Coroutine, timeout_seconds: float, operation_name: str = "operation") -> Any:
    """
    Execute coroutine with timeout.
    
    Args:
        coro: Coroutine to execute
        timeout_seconds: Timeout in seconds
        operation_name: Name of operation for logging
        
    Returns:
        Result of coroutine
        
    Raises:
        TimeoutError: If operation times out
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Operation '{operation_name}' timed out after {timeout_seconds} seconds")
        raise TimeoutError(f"Operation '{operation_name}' timed out after {timeout_seconds} seconds")


class CircuitBreaker:
    """Circuit breaker pattern for preventing cascade failures."""
    
    def __init__(self, 
                 failure_threshold: int = 5,
                 recovery_timeout: float = 60.0,
                 expected_exception: type = Exception):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Execute function with circuit breaker protection."""
        if self._state == "OPEN":
            if self._should_attempt_reset():
                self._state = "HALF_OPEN"
                logger.info("Circuit breaker transitioning to HALF_OPEN")
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit breaker should attempt reset."""
        return (self._last_failure_time and 
                time.time() - self._last_failure_time >= self.recovery_timeout)
    
    def _on_success(self) -> None:
        """Handle successful operation."""
        self._failure_count = 0
        if self._state == "HALF_OPEN":
            self._state = "CLOSED"
            logger.info("Circuit breaker reset to CLOSED")
    
    def _on_failure(self) -> None:
        """Handle failed operation."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._failure_count >= self.failure_threshold:
            self._state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self._failure_count} failures")


class ResourceManager:
    """Manage system resources and cleanup."""
    
    def __init__(self):
        self._cleanup_tasks: List[Callable] = []
        self._shutdown_handlers: List[Callable] = []
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def register_cleanup_task(self, cleanup_func: Callable) -> None:
        """Register a cleanup task to be called on shutdown."""
        self._cleanup_tasks.append(cleanup_func)
    
    def register_shutdown_handler(self, handler: Callable) -> None:
        """Register a shutdown handler."""
        self._shutdown_handlers.append(handler)
    
    def _signal_handler(self, signum: int, frame) -> None:
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown")
        asyncio.create_task(self.shutdown())
    
    async def shutdown(self) -> None:
        """Perform graceful shutdown."""
        logger.info("Starting graceful shutdown...")
        
        # Call shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler()
                else:
                    handler()
            except Exception as e:
                logger.error(f"Error in shutdown handler: {e}")
        
        # Call cleanup tasks
        for cleanup_func in self._cleanup_tasks:
            try:
                if asyncio.iscoroutinefunction(cleanup_func):
                    await cleanup_func()
                else:
                    cleanup_func()
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")
        
        # Cleanup GPU memory
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            logger.info("GPU memory cleared")
        
        logger.info("Graceful shutdown completed")
    
    @asynccontextmanager
    async def managed_operation(self, operation_name: str):
        """Context manager for managed operations with automatic cleanup."""
        start_time = datetime.now()
        
        try:
            yield
        except Exception as e:
            logger.error(f"Operation '{operation_name}' failed: {e}")
            raise
        finally:
            duration = (datetime.now() - start_time).total_seconds()
            logger.debug(f"Operation '{operation_name}' completed in {duration:.2f}s")


# Global resource manager
RESOURCE_MANAGER = ResourceManager()


class RetryHandler:
    """Handle retry logic with exponential backoff."""
    
    def __init__(self, 
                 max_retries: int = 3,
                 base_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
    
    async def retry_async(self, func: Callable, *args, **kwargs) -> Any:
        """Retry async function with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Function failed after {self.max_retries} retries: {e}")
                    raise
                
                delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                await asyncio.sleep(delay)
        
        raise last_exception
    
    def retry_sync(self, func: Callable, *args, **kwargs) -> Any:
        """Retry sync function with exponential backoff."""
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_exception = e
                
                if attempt == self.max_retries:
                    logger.error(f"Function failed after {self.max_retries} retries: {e}")
                    raise
                
                delay = min(self.base_delay * (self.backoff_factor ** attempt), self.max_delay)
                logger.warning(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s: {e}")
                time.sleep(delay)
        
        raise last_exception


def async_error_handler(func: Callable) -> Callable:
    """
    Decorator for consistent async error handling.
    
    Provides logging, error categorization, and proper error responses.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.TimeoutError as e:
            logger.error(f"Timeout in {func.__name__}: {e}")
            raise
        except ValueError as e:
            logger.warning(f"Validation error in {func.__name__}: {e}")
            raise
        except KeyError as e:
            logger.error(f"Key error in {func.__name__}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            logger.debug(f"Traceback: {traceback.format_exc()}")
            raise
    
    return wrapper


class HealthChecker:
    """Periodic health checking for system components."""
    
    def __init__(self, check_interval: float = 60.0):
        self.check_interval = check_interval
        self._health_checks: Dict[str, Callable] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    def register_health_check(self, name: str, check_func: Callable) -> None:
        """Register a health check function."""
        self._health_checks[name] = check_func
    
    async def start_monitoring(self) -> None:
        """Start periodic health monitoring."""
        if self._running:
            return
        
        self._running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info("Health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health monitoring stopped")
    
    async def _monitoring_loop(self) -> None:
        """Main monitoring loop."""
        while self._running:
            try:
                await self._run_health_checks()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def _run_health_checks(self) -> None:
        """Run all registered health checks."""
        for name, check_func in self._health_checks.items():
            try:
                if asyncio.iscoroutinefunction(check_func):
                    await check_func()
                else:
                    check_func()
            except Exception as e:
                logger.error(f"Health check '{name}' failed: {e}")


# Global health checker
HEALTH_CHECKER = HealthChecker()
