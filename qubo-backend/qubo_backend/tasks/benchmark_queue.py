"""
Qurve AI - Benchmark Queue Management
Enterprise-grade benchmark task queuing and coordination
"""

import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from collections import deque

from .task_models import Task, BenchmarkTask, TaskStatus, TaskPriority
from .async_runner import get_async_runner
from ..telemetry import get_structured_logger, get_benchmark_event_tracker
from ..telemetry.correlation import generate_correlation_id, generate_benchmark_session_id


@dataclass
class QueueStats:
    """Benchmark queue statistics for monitoring."""
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_wait_time_ms: float = 0.0
    avg_execution_time_ms: float = 0.0
    max_queue_size: int = 0
    total_processed: int = 0


class BenchmarkQueue:
    """
    Enterprise-grade benchmark queue with priority management.
    
    Provides:
    - Priority-based task scheduling
    - Concurrent execution limits
    - Performance monitoring
    - Resource guardrails
    - Telemetry integration
    - Backpressure handling
    """
    
    def __init__(self, max_concurrent_benchmarks: int = 3, max_queue_size: int = 100):
        self.max_concurrent_benchmarks = max_concurrent_benchmarks
        self.max_queue_size = max_queue_size
        
        # Task queues by priority
        self._queues = {
            TaskPriority.CRITICAL: deque(maxlen=max_queue_size),
            TaskPriority.HIGH: deque(maxlen=max_queue_size),
            TaskPriority.MEDIUM: deque(maxlen=max_queue_size),
            TaskPriority.LOW: deque(maxlen=max_queue_size)
        }
        
        # Active benchmark tracking
        self._active_benchmarks: Dict[str, Dict[str, Any]] = {}
        self._benchmark_lock = asyncio.Lock()
        
        # Statistics
        self._stats = QueueStats()
        self._stats_lock = asyncio.Lock()
        
        # Components
        self.async_runner = get_async_runner()
        self.logger = get_structured_logger(__name__)
        self.event_tracker = get_benchmark_event_tracker()
        
        self.logger.info(
            event="BENCHMARK_QUEUE_INITIALIZED",
            max_concurrent_benchmarks=max_concurrent_benchmarks,
            max_queue_size=max_queue_size
        )
    
    async def submit_benchmark(self, 
                          solver_request: Any,
                          solver_func: Callable,
                          solver_name: str,
                          provider: str = None,
                          backend: str = None,
                          priority: TaskPriority = TaskPriority.MEDIUM,
                          timeout_seconds: int = 300) -> str:
        """
        Submit benchmark task with automatic correlation and session tracking.
        
        Returns benchmark ID for tracking.
        """
        # Check queue capacity
        total_pending = sum(len(queue) for queue in self._queues.values())
        if total_pending >= self.max_queue_size:
            raise RuntimeError(f"Benchmark queue full: {total_pending}/{self.max_queue_size}")
        
        # Generate IDs
        correlation_id = generate_correlation_id()
        benchmark_session_id = generate_benchmark_session_id()
        benchmark_id = f"bench-{uuid.uuid4()}"
        
        # Create benchmark task
        from ..optimization.contracts import SolverRequest
        if isinstance(solver_request, SolverRequest):
            benchmark_task = BenchmarkTask(
                task_id=benchmark_id,
                solver_name=solver_name,
                provider=provider or solver_name,
                backend=backend or "local",
                num_assets=len(solver_request.mu),
                binary_bits=solver_request.binary_bits,
                cardinality=solver_request.cardinality,
                risk_tolerance=solver_request.risk_tolerance,
                max_sector_exposure=solver_request.max_sector_exposure,
                trajectories=solver_request.trajectories,
                time_limit_seconds=solver_request.time_limit_seconds or timeout_seconds,
                correlation_id=correlation_id,
                benchmark_session_id=benchmark_session_id
            )
        else:
            benchmark_task = Task(
                task_id=benchmark_id,
                task_type="benchmark_execution",
                priority=priority,
                func=solver_func,
                args=(solver_request,),
                timeout_seconds=timeout_seconds,
                correlation_id=correlation_id,
                benchmark_session_id=benchmark_session_id,
                solver_name=solver_name,
                provider=provider,
                backend=backend
            )
        
        # Add to appropriate priority queue
        queue = self._queues[priority]
        queue.append(benchmark_task)
        
        # Update statistics
        async with self._stats_lock:
            self._stats.pending_tasks += 1
            self._stats.max_queue_size = max(self._stats.max_queue_size, total_pending + 1)
        
        self.logger.info(
            event="BENCHMARK_QUEUED",
            benchmark_id=benchmark_id,
            solver_name=solver_name,
            priority=priority.name,
            queue_size=total_pending + 1,
            correlation_id=correlation_id,
            benchmark_session_id=benchmark_session_id
        )
        
        return benchmark_id
    
    async def process_benchmarks(self) -> List[str]:
        """
        Process benchmark tasks from queue with concurrency limits.
        
        Returns list of completed benchmark IDs.
        """
        completed_benchmarks = []
        
        # Process while there are tasks and capacity available
        while self._has_pending_tasks() and len(self._active_benchmarks) < self.max_concurrent_benchmarks:
            # Get next task by priority
            task = self._get_next_task()
            if task is None:
                break
            
            benchmark_id = task.task_id
            
            # Track benchmark start
            start_time = time.perf_counter()
            
            async with self._benchmark_lock:
                self._active_benchmarks[benchmark_id] = {
                    'task': task,
                    'start_time': start_time,
                    'correlation_id': task.correlation_id,
                    'benchmark_session_id': task.benchmark_session_id
                }
                
                # Update statistics
                async with self._stats_lock:
                    self._stats.pending_tasks -= 1
                    self._stats.running_tasks += 1
            
            # Track benchmark start
            self.event_tracker.benchmark_start(
                num_solvers=1,  # Will be updated by individual solvers
                problem_size=getattr(task, 'num_assets', 0)
            )
            
            # Process benchmark in separate async function
            await self._process_single_benchmark(benchmark_id, task, start_time)
        
        return completed_benchmarks
    
    async def _process_single_benchmark(self, benchmark_id: str, task: Task, start_time: float):
        """Process single benchmark with tracking."""
        try:
            # Process benchmark
            result = await self.async_runner.run_task(task)
            
            # Calculate elapsed time
            elapsed = (time.perf_counter() - start_time) * 1000
        
        except Exception as e:
            # Handle benchmark execution failure
            elapsed = (time.perf_counter() - start_time) * 1000
            result = e
        
        # Track benchmark completion
        self.event_tracker.benchmark_complete(
            duration_ms=elapsed,
            successful_solvers=1 if result and not isinstance(result, Exception) else 0,
            total_solvers=1
        )
        
        # Update statistics
        async with self._stats_lock:
            self._stats.running_tasks -= 1
            if result and not isinstance(result, Exception):
                self._stats.completed_tasks += 1
            else:
                self._stats.failed_tasks += 1
            self._stats.total_processed += 1
            
            # Update averages
            if self._stats.total_processed > 0:
                self._stats.avg_execution_time_ms = (
                    (self._stats.avg_execution_time_ms * (self._stats.total_processed - 1) + elapsed) 
                    / self._stats.total_processed
                )
                async with self._stats_lock:
                    self._stats.running_tasks -= 1
                    self._stats.failed_tasks += 1
                    self._stats.total_processed += 1
                
                self.logger.error(
                    event="BENCHMARK_FAILED",
                    benchmark_id=benchmark_id,
                    duration_ms=execution_time_ms,
                    error=str(e),
                    correlation_id=task.correlation_id,
                    benchmark_session_id=task.benchmark_session_id
                )
                
            finally:
                # Clean up active benchmark tracking
                async with self._benchmark_lock:
                    self._active_benchmarks.pop(benchmark_id, None)
        
        return completed_benchmarks
    
    def _has_pending_tasks(self) -> bool:
        """Check if any tasks are pending in priority queues."""
        return any(len(queue) > 0 for queue in self._queues.values())
    
    def _get_next_task(self) -> Optional[Task]:
        """Get next task by priority order."""
        # Check queues in priority order
        for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, TaskPriority.MEDIUM, TaskPriority.LOW]:
            queue = self._queues[priority]
            if queue:
                return queue.popleft()
        
        return None
    
    async def get_benchmark_status(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of specific benchmark.
        
        Returns comprehensive status information.
        """
        async with self._benchmark_lock:
            active_info = self._active_benchmarks.get(benchmark_id)
            
            if active_info:
                task = active_info['task']
                start_time = active_info['start_time']
                current_time = time.perf_counter()
                duration_ms = (current_time - start_time) * 1000
                
                return {
                    'benchmark_id': benchmark_id,
                    'status': 'running',
                    'duration_ms': duration_ms,
                    'correlation_id': active_info['correlation_id'],
                    'benchmark_session_id': active_info['benchmark_session_id'],
                    'solver_name': getattr(task, 'solver_name', None),
                    'provider': getattr(task, 'provider', None),
                    'backend': getattr(task, 'backend', None)
                }
            else:
                # Check if in queue
                for priority_queue in self._queues.values():
                    for task in priority_queue:
                        if task.task_id == benchmark_id:
                            return {
                                'benchmark_id': benchmark_id,
                                'status': 'queued',
                                'priority': task.priority.name,
                                'correlation_id': task.correlation_id,
                                'benchmark_session_id': task.benchmark_session_id,
                                'solver_name': getattr(task, 'solver_name', None),
                                'provider': getattr(task, 'provider', None),
                                'backend': getattr(task, 'backend', None)
                            }
                
                return None
    
    def get_queue_stats(self) -> QueueStats:
        """Get current queue statistics."""
        async with self._stats_lock:
            return self._stats
    
    def get_active_benchmarks(self) -> List[str]:
        """Get list of active benchmark IDs."""
        async with self._benchmark_lock:
            return list(self._active_benchmarks.keys())
    
    async def clear_queue(self):
        """Clear all pending tasks."""
        total_cleared = 0
        
        for priority_queue in self._queues.values():
            total_cleared += len(priority_queue)
            priority_queue.clear()
        
        async with self._stats_lock:
            self._stats.pending_tasks = 0
        
        self.logger.info(
            event="BENCHMARK_QUEUE_CLEARED",
            total_cleared=total_cleared
        )
    
    async def shutdown(self, wait: bool = True, timeout: float = 30.0):
        """
        Shutdown benchmark queue gracefully.
        
        Args:
            wait: Wait for active benchmarks to complete
            timeout: Maximum time to wait for completion
        """
        self.logger.info(
            event="BENCHMARK_QUEUE_SHUTDOWN",
            wait=wait,
            timeout=timeout,
            active_benchmarks=len(self._active_benchmarks)
        )
        
        # Clear pending tasks
        await self.clear_queue()
        
        # Wait for active benchmarks to complete
        if wait and self._active_benchmarks:
            try:
                await asyncio.wait_for(
                    self._wait_for_benchmarks_completion(),
                    timeout=timeout
                )
            except asyncio.TimeoutError:
                self.logger.warning(
                    event="BENCHMARK_QUEUE_SHUTDOWN_TIMEOUT",
                    timeout=timeout,
                    remaining_benchmarks=len(self._active_benchmarks)
                )
        
        # Shutdown async runner
        await self.async_runner.shutdown(wait=wait, timeout=timeout)
        
        self.logger.info(
            event="BENCHMARK_QUEUE_SHUTDOWN_COMPLETE",
            final_stats=self.get_queue_stats()
        )
    
    async def _wait_for_benchmarks_completion(self):
        """Wait for all active benchmarks to complete."""
        while self._active_benchmarks:
            await asyncio.sleep(0.1)  # Small delay to prevent busy waiting


# Global benchmark queue instance
_benchmark_queue = None

def get_benchmark_queue() -> BenchmarkQueue:
    """Get global benchmark queue instance."""
    global _benchmark_queue
    if _benchmark_queue is None:
        _benchmark_queue = BenchmarkQueue()
    return _benchmark_queue
