"""
Concurrency Control for QUBO Portfolio Optimizer
Implements execution queue system with GPU task scheduler,
async worker management, cancellation support, and memory explosion prevention.
"""

import asyncio
import logging
import uuid
from typing import Dict, List, Optional, Any, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import threading
from queue import PriorityQueue
import torch

from .config import get_settings
from .resource_guardrails import RESOURCE_GUARDRAILS
from .performance import PERFORMANCE_MONITOR, PerformanceMetrics

logger = logging.getLogger(__name__)


class JobPriority(Enum):
    """Job priority levels for queue ordering."""
    
    URGENT = 1      # Highest priority
    HIGH = 2          # High priority
    NORMAL = 3        # Normal priority
    LOW = 4           # Low priority
    BACKGROUND = 5     # Lowest priority


class JobStatus(Enum):
    """Job execution status."""
    
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


@dataclass
class Job:
    """Job definition for execution queue."""
    
    id: str
    task_func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: JobStatus = JobStatus.QUEUED
    result: Optional[Any] = None
    error: Optional[str] = None
    timeout_seconds: Optional[float] = None
    requires_gpu: bool = False
    estimated_memory_mb: float = 0.0
    user_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __lt__(self, other):
        """Priority queue ordering (lower priority number = higher priority)."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


@dataclass
class WorkerStats:
    """Worker statistics."""
    
    worker_id: str
    jobs_completed: int = 0
    jobs_failed: int = 0
    total_execution_time: float = 0.0
    current_job: Optional[str] = None
    last_activity: datetime = field(default_factory=datetime.now)
    supports_gpu: bool = False


class GPUTaskScheduler:
    """GPU-aware task scheduler with memory management."""
    
    def __init__(self, max_concurrent_gpu_jobs: int = 2):
        self.max_concurrent_gpu_jobs = max_concurrent_gpu_jobs
        self.current_gpu_jobs = 0
        self.gpu_lock = asyncio.Lock()
        
    async def acquire_gpu_slot(self, job: Job) -> bool:
        """Attempt to acquire a GPU execution slot."""
        if not job.requires_gpu:
            return True
        
        async with self.gpu_lock:
            if self.current_gpu_jobs >= self.max_concurrent_gpu_jobs:
                return False
            
            # Check GPU memory availability
            if torch.cuda.is_available():
                try:
                    total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**2)
                    allocated_memory = torch.cuda.memory_allocated(0) / (1024**2)
                    available_memory = total_memory - allocated_memory
                    
                    if job.estimated_memory_mb > available_memory * 0.8:  # 80% threshold
                        return False
                    
                    self.current_gpu_jobs += 1
                    return True
                except Exception as e:
                    logger.error(f"GPU memory check failed: {e}")
                    return False
            else:
                return False
    
    async def release_gpu_slot(self) -> None:
        """Release a GPU execution slot."""
        async with self.gpu_lock:
            if self.current_gpu_jobs > 0:
                self.current_gpu_jobs -= 1
    
    def get_gpu_status(self) -> Dict[str, Any]:
        """Get current GPU scheduler status."""
        status = {
            "max_concurrent_jobs": self.max_concurrent_gpu_jobs,
            "current_jobs": self.current_gpu_jobs,
            "available_slots": self.max_concurrent_gpu_jobs - self.current_gpu_jobs,
            "cuda_available": torch.cuda.is_available()
        }
        
        if torch.cuda.is_available():
            try:
                total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**2)
                allocated_memory = torch.cuda.memory_allocated(0) / (1024**2)
                status.update({
                    "total_memory_mb": total_memory,
                    "allocated_memory_mb": allocated_memory,
                    "available_memory_mb": total_memory - allocated_memory
                })
            except Exception as e:
                status["gpu_memory_error"] = str(e)
        
        return status


class ExecutionQueue:
    """
    High-performance execution queue with GPU scheduling.
    
    Features:
    - Job queue, GPU task scheduler, concurrency limits
    - Async worker management, cancellation support
    - Prevents memory explosion in multi-user scenarios
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 max_gpu_jobs: int = 2,
                 job_timeout_seconds: float = 300.0):
        self.settings = get_settings()
        self.max_workers = max_workers
        self.max_gpu_jobs = max_gpu_jobs
        self.job_timeout_seconds = job_timeout_seconds
        
        # Queue and workers
        self._queue = PriorityQueue()
        self._jobs: Dict[str, Job] = {}
        self._workers: Dict[str, WorkerStats] = {}
        self._worker_tasks: Dict[str, asyncio.Task] = {}
        
        # GPU scheduler
        self._gpu_scheduler = GPUTaskScheduler(max_gpu_jobs)
        
        # Control flags
        self._running = False
        self._shutdown_event = asyncio.Event()
        
        # Thread safety
        self._queue_lock = asyncio.Lock()
        self._jobs_lock = asyncio.Lock()
        
    async def start(self) -> None:
        """Start the execution queue and workers."""
        if self._running:
            return
        
        self._running = True
        self._shutdown_event.clear()
        
        # Start worker tasks
        for i in range(self.max_workers):
            worker_id = f"worker-{i+1}"
            supports_gpu = i < self.max_gpu_jobs
            
            worker_stats = WorkerStats(
                worker_id=worker_id,
                supports_gpu=supports_gpu
            )
            self._workers[worker_id] = worker_stats
            
            # Create and start worker task
            worker_task = asyncio.create_task(
                self._worker_loop(worker_id, supports_gpu),
                name=worker_id
            )
            self._worker_tasks[worker_id] = worker_task
        
        logger.info(f"Execution queue started with {self.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop the execution queue and workers."""
        if not self._running:
            return
        
        self._running = False
        self._shutdown_event.set()
        
        # Cancel all worker tasks
        for worker_id, task in self._worker_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
        
        # Clear worker data
        self._workers.clear()
        self._worker_tasks.clear()
        
        logger.info("Execution queue stopped")
    
    async def submit_job(self, 
                        task_func: Callable,
                        args: tuple = (),
                        kwargs: dict = None,
                        priority: JobPriority = JobPriority.NORMAL,
                        timeout_seconds: Optional[float] = None,
                        requires_gpu: bool = False,
                        estimated_memory_mb: float = 0.0,
                        user_id: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit a job to the execution queue.
        
        Args:
            task_func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            priority: Job priority level
            timeout_seconds: Custom timeout for this job
            requires_gpu: Whether job requires GPU
            estimated_memory_mb: Estimated memory requirement
            user_id: User ID for tracking
            metadata: Additional job metadata
            
        Returns:
            Job ID for tracking
        """
        job_id = str(uuid.uuid4())
        
        job = Job(
            id=job_id,
            task_func=task_func,
            args=args,
            kwargs=kwargs or {},
            priority=priority,
            timeout_seconds=timeout_seconds or self.job_timeout_seconds,
            requires_gpu=requires_gpu,
            estimated_memory_mb=estimated_memory_mb,
            user_id=user_id,
            metadata=metadata or {}
        )
        
        # Check resource guardrails
        can_execute, error_msg = RESOURCE_GUARDRAILS.can_execute_job(
            num_assets=metadata.get('num_assets', 10) if metadata else 10,
            binary_bits=metadata.get('binary_bits', 7) if metadata else 7,
            estimated_memory_mb=estimated_memory_mb,
            estimated_time_seconds=timeout_seconds or self.job_timeout_seconds
        )
        
        if not can_execute:
            job.status = JobStatus.FAILED
            job.error = f"Resource guardrails rejection: {error_msg}"
            job.completed_at = datetime.now()
            
            async with self._jobs_lock:
                self._jobs[job_id] = job
            
            logger.warning(f"Job {job_id} rejected by resource guardrails: {error_msg}")
            return job_id
        
        # Add to queue
        async with self._queue_lock:
            self._queue.put(job)
            self._queue.task_done()  # Reset for proper counting
        
        async with self._jobs_lock:
            self._jobs[job_id] = job
        
        logger.info(f"Job {job_id} submitted to queue (priority: {priority.name})")
        return job_id
    
    async def get_job_status(self, job_id: str) -> Optional[Job]:
        """Get the current status of a job."""
        async with self._jobs_lock:
            return self._jobs.get(job_id)
    
    async def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a queued or running job.
        
        Args:
            job_id: ID of job to cancel
            
        Returns:
            True if job was cancelled successfully
        """
        async with self._jobs_lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                return False
            
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now()
            
            logger.info(f"Job {job_id} cancelled")
            return True
    
    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue and worker status."""
        async with self._queue_lock:
            queue_size = self._queue.qsize()
        
        async with self._jobs_lock:
            jobs_by_status = {}
            for job in self._jobs.values():
                status = job.status.value
                jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
        
        # Worker statistics
        worker_stats = []
        for worker_id, stats in self._workers.items():
            worker_stats.append({
                "worker_id": worker_id,
                "supports_gpu": stats.supports_gpu,
                "jobs_completed": stats.jobs_completed,
                "jobs_failed": stats.jobs_failed,
                "current_job": stats.current_job,
                "success_rate": (
                    stats.jobs_completed / (stats.jobs_completed + stats.jobs_failed) * 100
                    if (stats.jobs_completed + stats.jobs_failed) > 0 else 0
                ),
                "last_activity": stats.last_activity.isoformat()
            })
        
        return {
            "queue_size": queue_size,
            "total_jobs": len(self._jobs),
            "jobs_by_status": jobs_by_status,
            "workers": worker_stats,
            "gpu_scheduler": self._gpu_scheduler.get_gpu_status(),
            "running": self._running
        }
    
    async def _worker_loop(self, worker_id: str, supports_gpu: bool) -> None:
        """Main worker loop for processing jobs."""
        worker_stats = self._workers[worker_id]
        
        logger.info(f"Worker {worker_id} started (GPU: {supports_gpu})")
        
        while self._running and not self._shutdown_event.is_set():
            try:
                # Get job from queue with timeout
                job = await asyncio.wait_for(
                    self._get_next_job(supports_gpu),
                    timeout=1.0
                )
                
                if job is None:
                    continue
                
                # Update worker status
                worker_stats.current_job = job.id
                worker_stats.last_activity = datetime.now()
                
                # Execute job
                await self._execute_job(job, worker_id)
                
                # Clear current job
                worker_stats.current_job = None
                
            except asyncio.TimeoutError:
                # No job available, continue
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1.0)  # Brief pause before retry
        
        logger.info(f"Worker {worker_id} stopped")
    
    async def _get_next_job(self, supports_gpu: bool) -> Optional[Job]:
        """Get the next available job for this worker."""
        async with self._queue_lock:
            if self._queue.empty():
                return None
            
            # Peek at jobs to find suitable one
            temp_jobs = []
            suitable_job = None
            
            while not self._queue.empty():
                job = self._queue.get_nowait()
                temp_jobs.append(job)
                
                # Check if job is suitable for this worker
                if suitable_job is None and self._is_job_suitable(job, supports_gpu):
                    suitable_job = job
                    break
            
            # Put back unsuitable jobs
            for job in temp_jobs:
                if job != suitable_job:
                    self._queue.put(job)
            
            return suitable_job
    
    def _is_job_suitable(self, job: Job, worker_supports_gpu: bool) -> bool:
        """Check if job is suitable for this worker."""
        # GPU requirement check
        if job.requires_gpu and not worker_supports_gpu:
            return False
        
        # GPU slot availability check
        if job.requires_gpu:
            return self._gpu_scheduler.current_gpu_jobs < self._gpu_scheduler.max_concurrent_gpu_jobs
        
        return True
    
    async def _execute_job(self, job: Job, worker_id: str) -> None:
        """Execute a single job."""
        start_time = datetime.now()
        worker_stats = self._workers[worker_id]
        
        # Update job status
        async with self._jobs_lock:
            job.status = JobStatus.RUNNING
            job.started_at = start_time
        
        # Acquire GPU slot if needed
        gpu_acquired = False
        if job.requires_gpu:
            gpu_acquired = await self._gpu_scheduler.acquire_gpu_slot(job)
            if not gpu_acquired:
                # Put job back in queue and retry later
                async with self._queue_lock:
                    self._queue.put(job)
                return
        
        try:
            # Record performance metrics
            performance_metric = PerformanceMetrics(
                operation_name=f"job_execution_{job.id}",
                start_time=start_time
            )
            
            # Execute the job with timeout
            if asyncio.iscoroutinefunction(job.task_func):
                result = await asyncio.wait_for(
                    job.task_func(*job.args, **job.kwargs),
                    timeout=job.timeout_seconds
                )
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: job.task_func(*job.args, **job.kwargs)
                )
            
            # Update job with successful result
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            async with self._jobs_lock:
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = end_time
            
            # Update worker stats
            worker_stats.jobs_completed += 1
            worker_stats.total_execution_time += execution_time
            
            # Record performance metrics
            performance_metric.end_time = end_time
            performance_metric.duration_ms = execution_time * 1000
            performance_metric.success = True
            await PERFORMANCE_MONITOR.record_metric(performance_metric)
            
            logger.info(f"Job {job.id} completed by {worker_id} in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            # Job timed out
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            async with self._jobs_lock:
                job.status = JobStatus.TIMEOUT
                job.error = f"Job timed out after {job.timeout_seconds}s"
                job.completed_at = end_time
            
            worker_stats.jobs_failed += 1
            
            # Record performance metrics
            performance_metric.end_time = end_time
            performance_metric.duration_ms = execution_time * 1000
            performance_metric.success = False
            performance_metric.error_message = job.error
            await PERFORMANCE_MONITOR.record_metric(performance_metric)
            
            logger.warning(f"Job {job.id} timed out after {execution_time:.2f}s")
            
        except Exception as e:
            # Job failed with error
            end_time = datetime.now()
            execution_time = (end_time - start_time).total_seconds()
            
            async with self._jobs_lock:
                job.status = JobStatus.FAILED
                job.error = str(e)
                job.completed_at = end_time
            
            worker_stats.jobs_failed += 1
            
            # Record performance metrics
            performance_metric.end_time = end_time
            performance_metric.duration_ms = execution_time * 1000
            performance_metric.success = False
            performance_metric.error_message = job.error
            await PERFORMANCE_MONITOR.record_metric(performance_metric)
            
            logger.error(f"Job {job.id} failed: {e}")
        
        finally:
            # Release GPU slot if acquired
            if gpu_acquired:
                await self._gpu_scheduler.release_gpu_slot()
    
    async def cleanup_completed_jobs(self, hours_to_keep: int = 24) -> int:
        """Clean up completed jobs older than specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours_to_keep)
        
        async with self._jobs_lock:
            jobs_to_remove = [
                job_id for job_id, job in self._jobs.items()
                if (job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED] and
                    job.completed_at and job.completed_at < cutoff_time)
            ]
            
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
        
        if jobs_to_remove:
            logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        
        return len(jobs_to_remove)


# Global execution queue instance
EXECUTION_QUEUE = ExecutionQueue()
