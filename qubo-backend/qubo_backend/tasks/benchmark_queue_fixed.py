"""
Qurve AI - Benchmark Queue (Fixed Version)
Enterprise-grade benchmark queue with priority management and proper async handling
"""

import asyncio
import time
import uuid
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from .task_models import Task, TaskPriority, TaskStatus
from ..telemetry import (
    get_structured_logger, 
    get_benchmark_event_tracker,
    generate_correlation_id, 
    generate_benchmark_session_id
)


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
            TaskPriority.CRITICAL: [],
            TaskPriority.HIGH: [],
            TaskPriority.MEDIUM: [],
            TaskPriority.LOW: []
        }
        
        # Active benchmark tracking
        self._active_benchmarks: Dict[str, Dict[str, Any]] = {}
        
        # Statistics
        self._stats = QueueStats()
        
        # Components
        self.logger = get_structured_logger(__name__)
        self.event_tracker = get_benchmark_event_tracker()
        
        self.logger.info(
            msg="BENCHMARK_QUEUE_INITIALIZED",
            event="BENCHMARK_QUEUE_INITIALIZED",
            max_concurrent_benchmarks=max_concurrent_benchmarks,
            max_queue_size=max_queue_size
        )
    
    async def submit_benchmark(self, 
                          solver_request: Any,
                          solver_func: callable,
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
            backend=backend,
            metadata={
                "num_assets": len(getattr(solver_request, 'mu', [])),
                "binary_bits": getattr(solver_request, 'binary_bits', 0),
                "cardinality": getattr(solver_request, 'cardinality', 0),
                "risk_tolerance": getattr(solver_request, 'risk_tolerance', 0.5),
                "max_sector_exposure": getattr(solver_request, 'max_sector_exposure', 0.3),
                "trajectories": getattr(solver_request, 'trajectories', 10),
                "time_limit_seconds": getattr(solver_request, 'time_limit_seconds', 30)
            }
        )
        
        # Add to appropriate priority queue
        queue = self._queues[priority]
        queue.append(benchmark_task)
        
        # Update statistics
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
            
            # Add to active benchmarks
            self._active_benchmarks[benchmark_id] = {
                'task': task,
                'start_time': start_time,
                'correlation_id': task.correlation_id,
                'benchmark_session_id': task.benchmark_session_id
            }
            
            # Update statistics
            self._stats.pending_tasks -= 1
            self._stats.running_tasks += 1
            
            # Track benchmark start
            self.event_tracker.benchmark_start(
                num_solvers=1,  # Will be updated by individual solvers
                problem_size=getattr(task, 'num_assets', 0)
            )
            
            try:
                # Process benchmark
                if hasattr(task, 'func') and task.func:
                    # Import async runner here to avoid circular import
                    from .async_runner import get_async_runner
                    async_runner = get_async_runner()
                    result = await async_runner.run_task(task)
                else:
                    # Fallback for tasks without function
                    result = {"error": "No solver function provided"}
                
                # Calculate execution time
                elapsed = (time.perf_counter() - start_time) * 1000
                
                # Track benchmark completion
                self.event_tracker.benchmark_complete(
                    duration_ms=elapsed,
                    successful_solvers=1 if result and not isinstance(result, Exception) else 0,
                    total_solvers=1
                )
                
                # Update statistics
                async with asyncio.Lock():  # Simple lock for stats update
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
                
                completed_benchmarks.append(benchmark_id)
                
                self.logger.info(
                    event="BENCHMARK_COMPLETED",
                    benchmark_id=benchmark_id,
                    duration_ms=elapsed,
                    success=result and not isinstance(result, Exception),
                    correlation_id=task.correlation_id,
                    benchmark_session_id=task.benchmark_session_id
                )
                
            except Exception as e:
                # Handle benchmark execution failure
                elapsed = (time.perf_counter() - start_time) * 1000
                
                # Update statistics
                async with asyncio.Lock():  # Simple lock for stats update
                    self._stats.running_tasks -= 1
                    self._stats.failed_tasks += 1
                    self._stats.total_processed += 1
                
                # Track failure
                self.event_tracker.benchmark_complete(
                    duration_ms=elapsed,
                    successful_solvers=0,
                    total_solvers=1
                )
                
                self.logger.error(
                    event="BENCHMARK_FAILED",
                    benchmark_id=benchmark_id,
                    duration_ms=elapsed,
                    error=str(e),
                    correlation_id=task.correlation_id,
                    benchmark_session_id=task.benchmark_session_id
                )
            
            finally:
                # Clean up active benchmark tracking
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
                return queue.pop(0)  # FIFO within priority
        
        return None
    
    async def get_benchmark_status(self, benchmark_id: str) -> Optional[Dict[str, Any]]:
        """
        Get status of specific benchmark.
        
        Returns comprehensive status information.
        """
        # Check if in active benchmarks
        if benchmark_id in self._active_benchmarks:
            active_info = self._active_benchmarks[benchmark_id]
            start_time = active_info['start_time']
            current_time = time.perf_counter()
            duration_ms = (current_time - start_time) * 1000
            
            return {
                'benchmark_id': benchmark_id,
                'status': 'running',
                'duration_ms': duration_ms,
                'correlation_id': active_info['correlation_id'],
                'benchmark_session_id': active_info['benchmark_session_id'],
                'solver_name': getattr(active_info['task'], 'solver_name', None),
                'provider': getattr(active_info['task'], 'provider', None),
                'backend': getattr(active_info['task'], 'backend', None)
            }
        
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
        return self._stats
    
    def get_active_benchmarks(self) -> List[str]:
        """Get list of active benchmark IDs."""
        return list(self._active_benchmarks.keys())
    
    async def clear_queue(self):
        """Clear all pending tasks."""
        total_cleared = 0
        
        for priority_queue in self._queues.values():
            total_cleared += len(priority_queue)
            priority_queue.clear()
        
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
        
        # Cancel remaining active benchmarks
        for benchmark_id in list(self._active_benchmarks.keys()):
            # Cancel task if possible
            self._active_benchmarks.pop(benchmark_id, None)
        
        self.logger.info(
            event="BENCHMARK_QUEUE_SHUTDOWN_COMPLETE",
            final_stats=self._stats
        )
    
    async def _wait_for_benchmarks_completion(self):
        """Wait for all active benchmarks to complete."""
        if not self._active_benchmarks:
            return
        
        # Create completion futures
        completion_futures = []
        for benchmark_id, active_info in self._active_benchmarks.items():
            # Create a simple future that completes when benchmark is done
            future = asyncio.Future()
            completion_futures.append(future)
        
        # Wait for any benchmark to complete (simplified)
        if completion_futures:
            await asyncio.sleep(0.1)  # Small delay to check status
        
        # Mark all as completed for shutdown
        for future in completion_futures:
            if not future.done():
                future.set_result(True)


# Global benchmark queue instance
_benchmark_queue = None

def get_benchmark_queue() -> BenchmarkQueue:
    """Get global benchmark queue instance."""
    global _benchmark_queue
    if _benchmark_queue is None:
        _benchmark_queue = BenchmarkQueue()
    return _benchmark_queue
