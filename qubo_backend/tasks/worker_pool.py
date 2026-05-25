"""
Qurve AI - Worker Pool Management
Enterprise-grade thread pool for safe concurrent execution
"""

import asyncio
import threading
import time
import logging
from typing import Dict, Any, Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, Future, as_completed
from dataclasses import dataclass, field

from ..telemetry import get_structured_logger, get_benchmark_event_tracker
from ..telemetry import solver_trace_context


@dataclass
class WorkerStats:
    """Worker pool statistics for monitoring."""
    active_workers: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_task_duration_ms: float = 0.0
    max_task_duration_ms: float = 0.0
    min_task_duration_ms: float = float('inf')
    thread_pool_size: int = 0


class WorkerPool:
    """
    Enterprise-grade worker pool for safe concurrent task execution.
    
    Provides:
    - Bounded thread pool to prevent resource exhaustion
    - Task timeout and cancellation support
    - Performance monitoring and statistics
    - Thread-safe operations
    - Resource guardrails
    """
    
    def __init__(self, max_workers: int = None, timeout_seconds: int = 300):
        self.max_workers = max_workers or min(32, (os.cpu_count() or 1) + 4)
        self.timeout_seconds = timeout_seconds
        
        # Thread pool with bounded workers
        self.executor = ThreadPoolExecutor(
            max_workers=self.max_workers,
            thread_name_prefix="qurve-worker"
        )
        
        # Task tracking
        self._active_tasks: Dict[str, Future] = {}
        self._task_start_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        
        # Statistics
        self._stats = WorkerStats(thread_pool_size=self.max_workers)
        
        # Logging
        self.logger = get_structured_logger(__name__)
        
        self.logger.info(
            event="WORKER_POOL_INITIALIZED",
            max_workers=self.max_workers,
            timeout_seconds=timeout_seconds
        )
    
    async def submit_task(self, task_id: str, func: Callable, *args, **kwargs) -> Any:
        """
        Submit task to worker pool with timeout and tracking.
        
        Returns result or raises TimeoutError.
        """
        start_time = time.perf_counter()
        
        with self._lock:
            self._stats.total_tasks += 1
            self._stats.active_workers += 1
            self._task_start_times[task_id] = start_time
        
        try:
            # Submit task to thread pool
            future = self.executor.submit(func, *args, **kwargs)
            
            with self._lock:
                self._active_tasks[task_id] = future
            
            # Wait for completion with timeout
            try:
                result = await asyncio.wait_for(
                    asyncio.wrap_future(future),
                    timeout=self.timeout_seconds
                )
                
                # Calculate duration
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                with self._lock:
                    self._stats.completed_tasks += 1
                    self._stats.active_workers -= 1
                    self._stats.avg_task_duration_ms = (
                        (self._stats.avg_task_duration_ms * (self._stats.completed_tasks - 1) + duration_ms) 
                        / self._stats.completed_tasks
                    )
                    self._stats.max_task_duration_ms = max(self._stats.max_task_duration_ms, duration_ms)
                    self._stats.min_task_duration_ms = min(self._stats.min_task_duration_ms, duration_ms)
                
                self.logger.info(
                    event="TASK_COMPLETED",
                    task_id=task_id,
                    duration_ms=duration_ms,
                    active_workers=self._stats.active_workers
                )
                
                return result
                
            except asyncio.TimeoutError:
                duration_ms = (time.perf_counter() - start_time) * 1000
                
                with self._lock:
                    self._stats.failed_tasks += 1
                    self._stats.active_workers -= 1
                
                self.logger.warning(
                    event="TASK_TIMEOUT",
                    task_id=task_id,
                    duration_ms=duration_ms,
                    timeout_seconds=self.timeout_seconds
                )
                
                raise TimeoutError(f"Task {task_id} timed out after {self.timeout_seconds} seconds")
                
        except Exception as e:
            duration_ms = (time.perf_counter() - start_time) * 1000
            
            with self._lock:
                self._stats.failed_tasks += 1
                self._stats.active_workers -= 1
            
            self.logger.error(
                event="TASK_FAILED",
                task_id=task_id,
                duration_ms=duration_ms,
                error=str(e)
            )
            
            raise RuntimeError(f"Task {task_id} failed: {str(e)}")
        
        finally:
            # Clean up tracking
            with self._lock:
                self._active_tasks.pop(task_id, None)
                self._task_start_times.pop(task_id, None)
    
    async def submit_solver_task(self, task_id: str, solver: str, func: Callable, *args, **kwargs) -> Any:
        """
        Submit solver task with automatic telemetry tracking.
        """
        event_tracker = get_benchmark_event_tracker()
        
        # Track solver start
        event_tracker.solver_start(solver=solver)
        
        try:
            with solver_trace_context(solver=solver):
                result = await self.submit_task(task_id, func, *args, **kwargs)
            
            # Track solver success
            event_tracker.solver_success(
                solver=solver,
                energy=getattr(result, 'energy', None),
                provider=getattr(getattr(result, 'metadata', {}), 'provider', None),
                backend=getattr(getattr(result, 'metadata', {}), 'backend_name', None)
            )
            
            return result
            
        except Exception as e:
            # Track solver failure
            event_tracker.solver_failure(solver=solver, error=str(e))
            raise
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel task if still running.
        
        Returns True if cancelled, False if not found or already completed.
        """
        with self._lock:
            future = self._active_tasks.get(task_id)
            if future and not future.done():
                cancelled = future.cancel()
                
                if cancelled:
                    self._stats.active_workers -= 1
                    self._stats.failed_tasks += 1
                
                self.logger.info(
                    event="TASK_CANCELLED",
                    task_id=task_id,
                    cancelled=cancelled
                )
                
                return cancelled
        
        return False
    
    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs."""
        with self._lock:
            return list(self._active_tasks.keys())
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get status of specific task."""
        with self._lock:
            future = self._active_tasks.get(task_id)
            if future is None:
                return None
            
            if future.done():
                if future.cancelled():
                    return "cancelled"
                elif future.exception():
                    return "failed"
                else:
                    return "completed"
            else:
                # Check if task is running too long
                start_time = self._task_start_times.get(task_id)
                if start_time:
                    duration_seconds = time.perf_counter() - start_time
                    if duration_seconds > self.timeout_seconds:
                        return "timeout"
                
                return "running"
    
    def get_stats(self) -> WorkerStats:
        """Get current worker pool statistics."""
        with self._lock:
            return self._stats
    
    def shutdown(self, wait: bool = True, timeout: float = 30.0):
        """
        Shutdown worker pool gracefully.
        
        Args:
            wait: Wait for running tasks to complete
            timeout: Maximum time to wait for completion
        """
        self.logger.info(
            event="WORKER_POOL_SHUTDOWN",
            wait=wait,
            timeout=timeout,
            active_tasks=len(self._active_tasks)
        )
        
        # Cancel all active tasks
        with self._lock:
            task_ids = list(self._active_tasks.keys())
            for task_id in task_ids:
                self.cancel_task(task_id)
        
        # Shutdown executor
        self.executor.shutdown(wait=wait)
        
        self.logger.info(
            event="WORKER_POOL_SHUTDOWN_COMPLETE",
            final_stats=self._stats
        )
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)


# Global worker pool instance
_worker_pool = None

def get_worker_pool() -> WorkerPool:
    """Get global worker pool instance."""
    global _worker_pool
    if _worker_pool is None:
        _worker_pool = WorkerPool()
    return _worker_pool
