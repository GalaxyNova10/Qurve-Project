"""
Qurve AI - Async Runner
Enterprise-grade async task execution and coordination
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import Future

from .task_models import Task, TaskResult, TaskStatus
from .worker_pool import get_worker_pool
from ..telemetry import get_structured_logger, get_benchmark_event_tracker


class AsyncRunner:
    """
    Enterprise-grade async task runner with coordination.
    
    Provides:
    - Non-blocking task execution
    - Timeout and cancellation support
    - Performance monitoring
    - Error handling and recovery
    - Resource management
    """
    
    def __init__(self):
        self.worker_pool = get_worker_pool()
        self.logger = get_structured_logger(__name__)
        self.event_tracker = get_benchmark_event_tracker()
    
    async def run_task(self, task: Task) -> TaskResult:
        """
        Run single task with full telemetry tracking.
        
        Returns TaskResult with comprehensive metadata.
        """
        # Mark task as running
        task.mark_running()
        
        # Track task start
        self.event_tracker.add_event({
            "event_type": "TASK_EXECUTION_START",
            "task_id": task.task_id,
            "task_type": task.task_type,
            "correlation_id": task.correlation_id,
            "benchmark_session_id": task.benchmark_session_id
        })
        
        try:
            # Execute task based on type
            if task.task_type == "benchmark_execution":
                result = await self._run_benchmark_task(task)
            elif task.task_type == "system_operation":
                result = await self._run_system_task(task)
            else:
                result = await self._run_generic_task(task)
            
            # Mark task as completed
            task.mark_completed(result)
            
            # Track task completion
            self.event_tracker.add_event({
                "event_type": "TASK_EXECUTION_COMPLETE",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": "success",
                "duration_ms": task.duration_ms,
                "correlation_id": task.correlation_id,
                "benchmark_session_id": task.benchmark_session_id
            })
            
            return result
            
        except asyncio.TimeoutError:
            # Mark task as timed out
            task.mark_timeout()
            
            # Track timeout
            self.event_tracker.add_event({
                "event_type": "TASK_EXECUTION_TIMEOUT",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": "timeout",
                "duration_ms": task.duration_ms,
                "correlation_id": task.correlation_id,
                "benchmark_session_id": task.benchmark_session_id
            })
            
            return task.create_result(TaskStatus.TIMEOUT, error=f"Task timed out after {task.timeout_seconds} seconds")
            
        except Exception as e:
            # Mark task as failed
            task.mark_failed(str(e))
            
            # Track failure
            self.event_tracker.add_event({
                "event_type": "TASK_EXECUTION_FAILURE",
                "task_id": task.task_id,
                "task_type": task.task_type,
                "status": "failure",
                "duration_ms": task.duration_ms,
                "error": str(e),
                "correlation_id": task.correlation_id,
                "benchmark_session_id": task.benchmark_session_id
            })
            
            return task.create_result(TaskStatus.FAILED, error=str(e))
    
    async def _run_benchmark_task(self, task: Task) -> Any:
        """Run benchmark task with solver execution."""
        if not task.func:
            raise ValueError("Benchmark task must have execution function")
        
        # Submit to worker pool with solver tracking
        task_id = f"benchmark-{task.task_id}"
        solver_name = getattr(task, 'solver_name', 'unknown')
        
        return await self.worker_pool.submit_solver_task(
            task_id=task_id,
            solver=solver_name,
            func=task.func,
            *task.args,
            **task.kwargs
        )
    
    async def _run_system_task(self, task: Task) -> Any:
        """Run system operation task."""
        if not task.func:
            raise ValueError("System task must have execution function")
        
        # Submit to worker pool
        task_id = f"system-{task.task_id}"
        
        return await self.worker_pool.submit_task(
            task_id=task_id,
            func=task.func,
            *task.args,
            **task.kwargs
        )
    
    async def _run_generic_task(self, task: Task) -> Any:
        """Run generic task."""
        if not task.func:
            raise ValueError("Task must have execution function")
        
        # Submit to worker pool
        task_id = f"generic-{task.task_id}"
        
        return await self.worker_pool.submit_task(
            task_id=task_id,
            func=task.func,
            *task.args,
            **task.kwargs
        )
    
    async def run_tasks(self, tasks: List[Task]) -> List[TaskResult]:
        """
        Run multiple tasks concurrently with coordination.
        
        Returns list of TaskResults in completion order.
        """
        if not tasks:
            return []
        
        # Track batch start
        self.event_tracker.add_event({
            "event_type": "BATCH_EXECUTION_START",
            "batch_size": len(tasks),
            "task_ids": [task.task_id for task in tasks]
        })
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Create task coroutines
            coroutines = [self.run_task(task) for task in tasks]
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*coroutines, return_exceptions=True)
            
            # Process results
            task_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Create failure result for exception
                    task_results.append(TaskResult(
                        task_id=tasks[i].task_id,
                        status=TaskStatus.FAILED,
                        error=str(result)
                    ))
                else:
                    task_results.append(result)
            
            # Track batch completion
            duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
            
            self.event_tracker.add_event({
                "event_type": "BATCH_EXECUTION_COMPLETE",
                "batch_size": len(tasks),
                "duration_ms": duration_ms,
                "success_count": len([r for r in task_results if r.is_success()]),
                "failure_count": len([r for r in task_results if r.is_failure()])
            })
            
            return task_results
            
        except Exception as e:
            # Track batch failure
            self.event_tracker.add_event({
                "event_type": "BATCH_EXECUTION_FAILURE",
                "batch_size": len(tasks),
                "error": str(e)
            })
            
            # Return failure results for all tasks
            return [
                TaskResult(
                    task_id=task.task_id,
                    status=TaskStatus.FAILED,
                    error=f"Batch execution failed: {str(e)}"
                ) for task in tasks
            ]
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel task by ID.
        
        Returns True if cancelled, False if not found.
        """
        return self.worker_pool.cancel_task(task_id)
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get status of specific task."""
        return self.worker_pool.get_task_status(task_id)
    
    def get_active_tasks(self) -> List[str]:
        """Get list of active task IDs."""
        return self.worker_pool.get_active_tasks()
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics from worker pool and event tracker."""
        worker_stats = self.worker_pool.get_stats()
        performance_summary = self.event_tracker.get_performance_summary()
        fallback_analysis = self.event_tracker.get_fallback_analysis()
        
        return {
            "worker_pool": worker_stats,
            "performance_summary": performance_summary,
            "fallback_analysis": fallback_analysis,
            "active_tasks": len(self.get_active_tasks())
        }
    
    async def shutdown(self, wait: bool = True, timeout: float = 30.0):
        """
        Shutdown async runner gracefully.
        
        Args:
            wait: Wait for running tasks to complete
            timeout: Maximum time to wait for completion
        """
        self.logger.info(
            event="ASYNC_RUNNER_SHUTDOWN",
            wait=wait,
            timeout=timeout,
            active_tasks=len(self.get_active_tasks())
        )
        
        # Shutdown worker pool
        self.worker_pool.shutdown(wait=wait, timeout=timeout)
        
        self.logger.info(
            event="ASYNC_RUNNER_SHUTDOWN_COMPLETE",
            final_stats=self.get_performance_stats()
        )


# Global async runner instance
_async_runner = None

def get_async_runner() -> AsyncRunner:
    """Get global async runner instance."""
    global _async_runner
    if _async_runner is None:
        _async_runner = AsyncRunner()
    return _async_runner
