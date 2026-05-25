"""
Job Persistence & Recovery for QUBO Portfolio Optimizer
Implements persistent job orchestration with checkpoint resumption.
Handles job state persistence, crash recovery, job resumption,
and checkpoint management for long-running optimization tasks.
"""

import asyncio
import json
import logging
import pickle
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import threading

from .config import get_settings
from .audit_logging import AUDIT_LOGGER
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


class JobState(Enum):
    """Job execution states."""
    
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    CHECKPOINTING = "checkpointing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RECOVERING = "recovering"


class CheckpointType(Enum):
    """Checkpoint types."""
    
    AUTO = "auto"           # Automatic periodic checkpoint
    MANUAL = "manual"         # Manual checkpoint request
    ERROR = "error"          # Checkpoint before error
    SHUTDOWN = "shutdown"      # Checkpoint before shutdown


@dataclass
class JobCheckpoint:
    """Job checkpoint data."""
    
    checkpoint_id: str
    job_id: str
    checkpoint_type: CheckpointType
    timestamp: datetime
    progress_percentage: float
    execution_time_seconds: float
    checkpoint_data: Dict[str, Any]
    intermediate_results: Dict[str, Any]
    solver_state: Dict[str, Any]
    resource_usage: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['checkpoint_type'] = self.checkpoint_type.value
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JobCheckpoint':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['checkpoint_type'] = CheckpointType(data['checkpoint_type'])
        return cls(**data)


@dataclass
class PersistentJob:
    """Persistent job definition."""
    
    job_id: str
    job_name: str
    job_type: str  # "optimization", "benchmark", "training"
    
    # Job definition
    parameters: Dict[str, Any]
    solver_name: str
    solver_config: Dict[str, Any]
    
    # Execution state
    state: JobState
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_checkpoint_at: Optional[datetime] = None
    
    # Progress tracking
    progress_percentage: float = 0.0
    current_step: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    
    # Results
    final_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    
    # Checkpointing
    checkpoints: List[JobCheckpoint] = field(default_factory=list)
    latest_checkpoint_id: Optional[str] = None
    
    # Resumption info
    resume_count: int = 0
    original_job_id: Optional[str] = None  # For resumed jobs
    
    # Resource allocation
    allocated_resources: Dict[str, Any] = field(default_factory=dict)
    
    # Metadata
    user_id: Optional[str] = None
    priority: int = 5
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['state'] = self.state.value
        data['created_at'] = self.created_at.isoformat()
        
        if self.started_at:
            data['started_at'] = self.started_at.isoformat()
        if self.completed_at:
            data['completed_at'] = self.completed_at.isoformat()
        if self.last_checkpoint_at:
            data['last_checkpoint_at'] = self.last_checkpoint_at.isoformat()
        
        # Convert checkpoints
        data['checkpoints'] = [cp.to_dict() for cp in self.checkpoints]
        
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersistentJob':
        """Create from dictionary."""
        data['state'] = JobState(data['state'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        
        if data.get('started_at'):
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data.get('completed_at'):
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        if data.get('last_checkpoint_at'):
            data['last_checkpoint_at'] = datetime.fromisoformat(data['last_checkpoint_at'])
        
        # Convert checkpoints
        if 'checkpoints' in data:
            data['checkpoints'] = [JobCheckpoint.from_dict(cp) for cp in data['checkpoints']]
        
        return cls(**data)


class JobPersistenceManager:
    """
    Persistent job orchestration with checkpoint resumption.
    
    Features:
    - Job state persistence and recovery
    - Checkpoint management and resumption
    - Crash recovery and job restart
    - Resource allocation tracking
    - Job lifecycle management
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.jobs_dir = self.settings.output_dir / "jobs"
        self.jobs_dir.mkdir(parents=True, exist_ok=True)
        
        # Storage files
        self.jobs_file = self.jobs_dir / "jobs.json"
        self.checkpoints_dir = self.jobs_dir / "checkpoints"
        self.checkpoints_dir.mkdir(exist_ok=True)
        
        # In-memory state
        self._jobs: Dict[str, PersistentJob] = {}
        self._running_jobs: Dict[str, PersistentJob] = {}
        self._checkpoint_callbacks: Dict[str, Callable] = {}
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Load existing jobs
        self._load_jobs()
        
        # Start background tasks
        self._running = False
        self._checkpoint_task: Optional[asyncio.Task] = None
        self._recovery_task: Optional[asyncio.Task] = None
    
    def _load_jobs(self) -> None:
        """Load existing jobs from storage."""
        try:
            if self.jobs_file.exists():
                with open(self.jobs_file, 'r') as f:
                    jobs_data = json.load(f)
                
                for job_id, job_data in jobs_data.items():
                    self._jobs[job_id] = PersistentJob.from_dict(job_data)
                    
                    # Load checkpoints separately
                    self._load_job_checkpoints(job_id)
            
            logger.info(f"Loaded {len(self._jobs)} jobs from storage")
            
        except Exception as e:
            logger.error(f"Failed to load jobs: {e}")
            self._jobs = {}
    
    def _load_job_checkpoints(self, job_id: str) -> None:
        """Load checkpoints for a specific job."""
        checkpoint_file = self.checkpoints_dir / f"{job_id}_checkpoints.json"
        
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    checkpoints_data = json.load(f)
                
                job = self._jobs.get(job_id)
                if job:
                    job.checkpoints = [JobCheckpoint.from_dict(cp) for cp in checkpoints_data]
                    
                    if job.checkpoints:
                        job.latest_checkpoint_id = job.checkpoints[-1].checkpoint_id
                        job.last_checkpoint_at = job.checkpoints[-1].timestamp
                
            except Exception as e:
                logger.error(f"Failed to load checkpoints for job {job_id}: {e}")
    
    def _save_jobs(self) -> None:
        """Save jobs to storage."""
        try:
            # Save jobs metadata
            jobs_data = {}
            for job_id, job in self._jobs.items():
                jobs_data[job_id] = job.to_dict()
            
            with open(self.jobs_file, 'w') as f:
                json.dump(jobs_data, f, indent=2)
            
            # Save checkpoints separately
            for job_id, job in self._jobs.items():
                if job.checkpoints:
                    self._save_job_checkpoints(job_id, job.checkpoints)
            
            logger.debug("Jobs saved to storage")
            
        except Exception as e:
            logger.error(f"Failed to save jobs: {e}")
    
    def _save_job_checkpoints(self, job_id: str, checkpoints: List[JobCheckpoint]) -> None:
        """Save checkpoints for a specific job."""
        checkpoint_file = self.checkpoints_dir / f"{job_id}_checkpoints.json"
        
        try:
            checkpoints_data = [cp.to_dict() for cp in checkpoints]
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoints_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save checkpoints for job {job_id}: {e}")
    
    async def create_job(self,
                        job_name: str,
                        job_type: str,
                        parameters: Dict[str, Any],
                        solver_name: str,
                        solver_config: Dict[str, Any],
                        user_id: Optional[str] = None,
                        priority: int = 5,
                        tags: Optional[List[str]] = None) -> str:
        """
        Create a new persistent job.
        
        Args:
            job_name: Human-readable job name
            job_type: Type of job
            parameters: Job parameters
            solver_name: Solver to use
            solver_config: Solver configuration
            user_id: User ID
            priority: Job priority (1-10, lower is higher)
            tags: Job tags
            
        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())
        
        job = PersistentJob(
            job_id=job_id,
            job_name=job_name,
            job_type=job_type,
            parameters=parameters,
            solver_name=solver_name,
            solver_config=solver_config,
            state=JobState.PENDING,
            created_at=datetime.now(),
            user_id=user_id,
            priority=priority,
            tags=tags or []
        )
        
        with self._lock:
            self._jobs[job_id] = job
            self._save_jobs()
        
        # Log job creation
        AUDIT_LOGGER.log_optimization_parameters(
            job_id=job_id,
            solver_name=solver_name,
            parameters=parameters,
            user_id=user_id
        )
        
        logger.info(f"Created job {job_id}: {job_name}")
        return job_id
    
    async def start_job(self, job_id: str) -> bool:
        """
        Start a job execution.
        
        Args:
            job_id: Job ID to start
            
        Returns:
            True if started successfully
        """
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.error(f"Job not found: {job_id}")
                return False
            
            if job.state not in [JobState.PENDING, JobState.QUEUED]:
                logger.warning(f"Job {job_id} not in startable state: {job.state.value}")
                return False
            
            job.state = JobState.RUNNING
            job.started_at = datetime.now()
            self._running_jobs[job_id] = job
            self._save_jobs()
        
        logger.info(f"Started job {job_id}")
        return True
    
    async def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.state != JobState.RUNNING:
                return False
            
            job.state = JobState.PAUSED
            self._save_jobs()
        
        logger.info(f"Paused job {job_id}")
        return True
    
    async def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job or job.state != JobState.PAUSED:
                return False
            
            job.state = JobState.RUNNING
            self._running_jobs[job_id] = job
            self._save_jobs()
        
        logger.info(f"Resumed job {job_id}")
        return True
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            if job.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED]:
                return False
            
            job.state = JobState.CANCELLED
            job.completed_at = datetime.now()
            
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            
            self._save_jobs()
        
        logger.info(f"Cancelled job {job_id}")
        return True
    
    async def complete_job(self, job_id: str, result: Dict[str, Any]) -> bool:
        """Mark a job as completed."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.state = JobState.COMPLETED
            job.completed_at = datetime.now()
            job.progress_percentage = 100.0
            job.final_result = result
            
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            
            self._save_jobs()
        
        logger.info(f"Completed job {job_id}")
        return True
    
    async def fail_job(self, job_id: str, error_message: str) -> bool:
        """Mark a job as failed."""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                return False
            
            job.state = JobState.FAILED
            job.completed_at = datetime.now()
            job.error_message = error_message
            
            if job_id in self._running_jobs:
                del self._running_jobs[job_id]
            
            self._save_jobs()
        
        logger.error(f"Failed job {job_id}: {error_message}")
        return False
    
    async def create_checkpoint(self,
                            job_id: str,
                            checkpoint_type: CheckpointType,
                            progress_percentage: float,
                            checkpoint_data: Dict[str, Any],
                            intermediate_results: Dict[str, Any],
                            solver_state: Dict[str, Any],
                            resource_usage: Dict[str, Any]) -> str:
        """
        Create a checkpoint for a job.
        
        Args:
            job_id: Job ID
            checkpoint_type: Type of checkpoint
            progress_percentage: Current progress (0-100)
            checkpoint_data: Custom checkpoint data
            intermediate_results: Intermediate results
            solver_state: Solver state information
            resource_usage: Current resource usage
            
        Returns:
            Checkpoint ID
        """
        checkpoint_id = str(uuid.uuid4())
        
        checkpoint = JobCheckpoint(
            checkpoint_id=checkpoint_id,
            job_id=job_id,
            checkpoint_type=checkpoint_type,
            timestamp=datetime.now(),
            progress_percentage=progress_percentage,
            execution_time_seconds=0.0,  # Will be calculated
            checkpoint_data=checkpoint_data,
            intermediate_results=intermediate_results,
            solver_state=solver_state,
            resource_usage=resource_usage
        )
        
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.error(f"Job not found for checkpoint: {job_id}")
                return checkpoint_id
            
            # Calculate execution time
            if job.started_at:
                checkpoint.execution_time_seconds = (checkpoint.timestamp - job.started_at).total_seconds()
            
            # Add checkpoint to job
            job.checkpoints.append(checkpoint)
            job.latest_checkpoint_id = checkpoint_id
            job.last_checkpoint_at = checkpoint.timestamp
            job.progress_percentage = progress_percentage
            
            # Save checkpoints
            self._save_job_checkpoints(job_id, job.checkpoints)
            self._save_jobs()
        
        logger.info(f"Created checkpoint {checkpoint_id} for job {job_id}")
        return checkpoint_id
    
    async def resume_from_checkpoint(self, job_id: str, checkpoint_id: Optional[str] = None) -> Optional[PersistentJob]:
        """
        Resume a job from checkpoint.
        
        Args:
            job_id: Job ID to resume
            checkpoint_id: Specific checkpoint ID (None = latest)
            
        Returns:
            Resumed job object or None
        """
        with self._lock:
            original_job = self._jobs.get(job_id)
            if not original_job:
                logger.error(f"Job not found for resumption: {job_id}")
                return None
            
            if not original_job.checkpoints:
                logger.warning(f"No checkpoints found for job {job_id}")
                return None
            
            # Select checkpoint
            if checkpoint_id:
                checkpoint = next((cp for cp in original_job.checkpoints if cp.checkpoint_id == checkpoint_id), None)
                if not checkpoint:
                    logger.error(f"Checkpoint not found: {checkpoint_id}")
                    return None
            else:
                checkpoint = original_job.checkpoints[-1]  # Latest checkpoint
            
            # Create new job for resumption
            resumed_job = PersistentJob(
                job_id=str(uuid.uuid4()),
                job_name=f"{original_job.job_name}_resumed",
                job_type=original_job.job_type,
                parameters=original_job.parameters.copy(),
                solver_name=original_job.solver_name,
                solver_config=original_job.solver_config.copy(),
                state=JobState.RECOVERING,
                created_at=datetime.now(),
                progress_percentage=checkpoint.progress_percentage,
                original_job_id=job_id,
                resume_count=original_job.resume_count + 1,
                user_id=original_job.user_id,
                priority=original_job.priority,
                tags=original_job.tags + ["resumed"]
            )
            
            # Add checkpoint to resumed job
            resumed_job.checkpoints = [checkpoint]
            resumed_job.latest_checkpoint_id = checkpoint.checkpoint_id
            resumed_job.last_checkpoint_at = checkpoint.timestamp
            
            # Store resumed job
            self._jobs[resumed_job.job_id] = resumed_job
            self._save_jobs()
        
        logger.info(f"Resumed job {job_id} as {resumed_job.job_id} from checkpoint {checkpoint.checkpoint_id}")
        return resumed_job
    
    def get_job(self, job_id: str) -> Optional[PersistentJob]:
        """Get job by ID."""
        return self._jobs.get(job_id)
    
    def get_jobs(self,
                state: Optional[JobState] = None,
                user_id: Optional[str] = None,
                job_type: Optional[str] = None,
                limit: int = 100) -> List[PersistentJob]:
        """Get jobs with optional filtering."""
        jobs = list(self._jobs.values())
        
        # Apply filters
        if state:
            jobs = [j for j in jobs if j.state == state]
        
        if user_id:
            jobs = [j for j in jobs if j.user_id == user_id]
        
        if job_type:
            jobs = [j for j in jobs if j.job_type == job_type]
        
        # Sort by creation time (newest first) and limit
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[:limit]
    
    def get_running_jobs(self) -> List[PersistentJob]:
        """Get currently running jobs."""
        return list(self._running_jobs.values())
    
    def get_job_checkpoints(self, job_id: str) -> List[JobCheckpoint]:
        """Get all checkpoints for a job."""
        job = self._jobs.get(job_id)
        return job.checkpoints if job else []
    
    async def cleanup_old_jobs(self, days_to_keep: int = 30) -> int:
        """Clean up old completed jobs."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        jobs_to_remove = []
        checkpoints_to_remove = []
        
        with self._lock:
            for job_id, job in self._jobs.items():
                if (job.state in [JobState.COMPLETED, JobState.FAILED, JobState.CANCELLED] and
                    job.completed_at and job.completed_at < cutoff_date):
                    
                    jobs_to_remove.append(job_id)
                    checkpoints_to_remove.append(job_id)
            
            # Remove jobs
            for job_id in jobs_to_remove:
                del self._jobs[job_id]
                if job_id in self._running_jobs:
                    del self._running_jobs[job_id]
            
            # Remove checkpoint files
            for job_id in checkpoints_to_remove:
                checkpoint_file = self.checkpoints_dir / f"{job_id}_checkpoints.json"
                try:
                    checkpoint_file.unlink()
                except Exception as e:
                    logger.error(f"Failed to remove checkpoint file {checkpoint_file}: {e}")
            
            if jobs_to_remove:
                self._save_jobs()
        
        logger.info(f"Cleaned up {len(jobs_to_remove)} old jobs")
        return len(jobs_to_remove)
    
    def register_checkpoint_callback(self, job_id: str, callback: Callable) -> None:
        """Register a callback for checkpoint creation."""
        self._checkpoint_callbacks[job_id] = callback
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job execution statistics."""
        total_jobs = len(self._jobs)
        running_jobs = len(self._running_jobs)
        
        # Count by state
        state_counts = {}
        for job in self._jobs.values():
            state = job.state.value
            state_counts[state] = state_counts.get(state, 0) + 1
        
        # Count by type
        type_counts = {}
        for job in self._jobs.values():
            job_type = job.job_type
            type_counts[job_type] = type_counts.get(job_type, 0) + 1
        
        # Calculate average execution time
        completed_jobs = [j for j in self._jobs.values() if j.state == JobState.COMPLETED and j.started_at and j.completed_at]
        
        if completed_jobs:
            execution_times = [(j.completed_at - j.started_at).total_seconds() for j in completed_jobs]
            avg_execution_time = sum(execution_times) / len(execution_times)
        else:
            avg_execution_time = 0.0
        
        return {
            "total_jobs": total_jobs,
            "running_jobs": running_jobs,
            "state_distribution": state_counts,
            "type_distribution": type_counts,
            "average_execution_time_seconds": avg_execution_time,
            "total_checkpoints": sum(len(j.checkpoints) for j in self._jobs.values()),
            "storage_directory": str(self.jobs_dir)
        }
    
    async def start_background_tasks(self) -> None:
        """Start background tasks for job management."""
        if self._running:
            return
        
        self._running = True
        
        loop = asyncio.get_event_loop()
        self._checkpoint_task = loop.create_task(self._checkpoint_monitoring_loop())
        self._recovery_task = loop.create_task(self._recovery_loop())
        
        logger.info("Job persistence background tasks started")
    
    async def stop_background_tasks(self) -> None:
        """Stop background tasks."""
        self._running = False
        
        if self._checkpoint_task:
            self._checkpoint_task.cancel()
        
        if self._recovery_task:
            self._recovery_task.cancel()
        
        logger.info("Job persistence background tasks stopped")
    
    async def _checkpoint_monitoring_loop(self) -> None:
        """Background loop for automatic checkpointing."""
        while self._running:
            try:
                # Check running jobs for automatic checkpointing
                for job in list(self._running_jobs.values()):
                    if job.job_type == "optimization":
                        # Create automatic checkpoint every 5 minutes
                        if (job.last_checkpoint_at and 
                            (datetime.now() - job.last_checkpoint_at).total_seconds() >= 300):
                            
                            await self.create_checkpoint(
                                job_id=job.job_id,
                                checkpoint_type=CheckpointType.AUTO,
                                progress_percentage=job.progress_percentage,
                                checkpoint_data={"auto_checkpoint": True},
                                intermediate_results={},
                                solver_state={},
                                resource_usage={}
                            )
                
                await asyncio.sleep(60)  # Check every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Checkpoint monitoring error: {e}")
                await asyncio.sleep(60)
    
    async def _recovery_loop(self) -> None:
        """Background loop for crash recovery."""
        while self._running:
            try:
                # Check for jobs that were running but are no longer active
                current_time = datetime.now()
                
                for job_id, job in list(self._running_jobs.items()):
                    # If job has been running for more than 10 minutes without recent activity
                    if (job.last_checkpoint_at and 
                        (current_time - job.last_checkpoint_at).total_seconds() > 600):
                        
                        logger.warning(f"Job {job_id} appears to be stalled, marking for recovery")
                        job.state = JobState.RECOVERING
                        self._save_jobs()
                
                await asyncio.sleep(300)  # Check every 5 minutes
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Recovery loop error: {e}")
                await asyncio.sleep(300)


# Global job persistence manager instance
JOB_PERSISTENCE_MANAGER = JobPersistenceManager()
