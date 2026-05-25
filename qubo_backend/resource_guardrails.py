"""
Resource Guardrails for QUBO Portfolio Optimizer
Provides critical resource protection including QUBO dimension limits, 
VRAM protection, CPU memory ceilings, and execution timeouts.
"""

import logging
import psutil
import asyncio
from typing import Dict, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import torch

logger = logging.getLogger(__name__)


@dataclass
class ResourceLimits:
    """Configurable resource limits for optimization tasks."""
    
    # QUBO dimension limits
    max_assets: int = 50
    max_binary_bits: int = 7
    max_qubo_size: int = 10000  # Maximum number of QUBO variables
    
    # Memory limits (in MB)
    max_cpu_memory_mb: int = 4096  # 4GB
    max_gpu_memory_mb: int = 8192  # 8GB
    memory_safety_margin: float = 0.8  # Use only 80% of available memory
    
    # Execution limits
    max_execution_time_seconds: int = 300  # 5 minutes
    max_queue_wait_time_seconds: int = 600  # 10 minutes
    
    # Batch processing limits
    max_concurrent_jobs: int = 4
    max_batch_size: int = 10
    
    # Cost control
    max_cost_per_job: float = 10.0  # USD
    daily_cost_limit: float = 100.0  # USD


@dataclass
class ResourceUsage:
    """Current resource usage statistics."""
    
    cpu_memory_used_mb: float
    cpu_memory_available_mb: float
    gpu_memory_used_mb: float
    gpu_memory_available_mb: float
    cpu_usage_percent: float
    gpu_usage_percent: float
    active_jobs: int
    queued_jobs: int


class ResourceGuardrails:
    """
    Enforces resource limits and prevents resource exhaustion.
    
    Provides protection against QUBO explosion, GPU memory crashes,
    CPU memory exhaustion, and runaway execution times.
    """
    
    def __init__(self, limits: Optional[ResourceLimits] = None):
        self.limits = limits or ResourceLimits()
        self._daily_cost_used = 0.0
        self._last_cost_reset = datetime.now().date()
        self._active_jobs = set()
        self._job_start_times = {}
        
    def validate_problem_size(self, num_assets: int, binary_bits: int) -> Tuple[bool, str]:
        """
        Validate problem size against configured limits.
        
        Args:
            num_assets: Number of assets in the portfolio
            binary_bits: Number of binary bits per asset
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check asset count
        if num_assets > self.limits.max_assets:
            return False, f"Too many assets: {num_assets} > {self.limits.max_assets}"
        
        # Check binary bits
        if binary_bits > self.limits.max_binary_bits:
            return False, f"Too many binary bits: {binary_bits} > {self.limits.max_binary_bits}"
        
        # Calculate QUBO size
        qubo_size = num_assets * binary_bits
        if qubo_size > self.limits.max_qubo_size:
            return False, f"QUBO too large: {qubo_size} > {self.limits.max_qubo_size}"
        
        return True, ""
    
    def check_memory_availability(self, estimated_memory_mb: float) -> Tuple[bool, str]:
        """
        Check if sufficient memory is available for the task.
        
        Args:
            estimated_memory_mb: Estimated memory requirement in MB
            
        Returns:
            Tuple of (is_available, error_message)
        """
        # Check CPU memory
        cpu_memory = psutil.virtual_memory()
        cpu_available_mb = cpu_memory.available / (1024 * 1024)
        cpu_safe_limit_mb = cpu_available_mb * self.limits.memory_safety_margin
        
        if estimated_memory_mb > cpu_safe_limit_mb:
            return False, f"Insufficient CPU memory: need {estimated_memory_mb:.1f}MB, available {cpu_safe_limit_mb:.1f}MB"
        
        # Check GPU memory if available
        if torch.cuda.is_available():
            try:
                gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                gpu_reserved = torch.cuda.memory_reserved(0) / (1024 * 1024)
                gpu_available_mb = gpu_memory - gpu_reserved
                gpu_safe_limit_mb = gpu_available_mb * self.limits.memory_safety_margin
                
                if estimated_memory_mb > gpu_safe_limit_mb:
                    return False, f"Insufficient GPU memory: need {estimated_memory_mb:.1f}MB, available {gpu_safe_limit_mb:.1f}MB"
            except Exception as e:
                logger.warning(f"Failed to check GPU memory: {e}")
        
        return True, ""
    
    def check_execution_limits(self, estimated_time_seconds: float) -> Tuple[bool, str]:
        """
        Check if execution time is within limits.
        
        Args:
            estimated_time_seconds: Estimated execution time in seconds
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        if estimated_time_seconds > self.limits.max_execution_time_seconds:
            return False, f"Execution time too long: {estimated_time_seconds:.1f}s > {self.limits.max_execution_time_seconds}s"
        
        return True, ""
    
    def check_concurrency_limits(self) -> Tuple[bool, str]:
        """
        Check if we can start another job based on concurrency limits.
        
        Returns:
            Tuple of (can_start, error_message)
        """
        if len(self._active_jobs) >= self.limits.max_concurrent_jobs:
            return False, f"Too many active jobs: {len(self._active_jobs)} >= {self.limits.max_concurrent_jobs}"
        
        return True, ""
    
    def check_cost_limits(self, estimated_cost: float) -> Tuple[bool, str]:
        """
        Check if job cost is within limits.
        
        Args:
            estimated_cost: Estimated cost in USD
            
        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Reset daily cost if needed
        today = datetime.now().date()
        if today != self._last_cost_reset:
            self._daily_cost_used = 0.0
            self._last_cost_reset = today
        
        # Check per-job cost
        if estimated_cost > self.limits.max_cost_per_job:
            return False, f"Job cost too high: ${estimated_cost:.2f} > ${self.limits.max_cost_per_job:.2f}"
        
        # Check daily cost
        if self._daily_cost_used + estimated_cost > self.limits.daily_cost_limit:
            return False, f"Daily cost limit exceeded: ${self._daily_cost_used + estimated_cost:.2f} > ${self.limits.daily_cost_limit:.2f}"
        
        return True, ""
    
    def can_execute_job(self, 
                        num_assets: int, 
                        binary_bits: int,
                        estimated_memory_mb: float = 512.0,
                        estimated_time_seconds: float = 60.0,
                        estimated_cost: float = 1.0) -> Tuple[bool, str]:
        """
        Comprehensive check if a job can be executed.
        
        Args:
            num_assets: Number of assets
            binary_bits: Number of binary bits
            estimated_memory_mb: Estimated memory requirement
            estimated_time_seconds: Estimated execution time
            estimated_cost: Estimated job cost
            
        Returns:
            Tuple of (can_execute, error_message)
        """
        # Check problem size
        valid, error = self.validate_problem_size(num_assets, binary_bits)
        if not valid:
            return False, f"Problem size validation failed: {error}"
        
        # Check memory availability
        available, error = self.check_memory_availability(estimated_memory_mb)
        if not available:
            return False, f"Memory check failed: {error}"
        
        # Check execution limits
        allowed, error = self.check_execution_limits(estimated_time_seconds)
        if not allowed:
            return False, f"Execution limit check failed: {error}"
        
        # Check concurrency limits
        can_start, error = self.check_concurrency_limits()
        if not can_start:
            return False, f"Concurrency limit check failed: {error}"
        
        # Check cost limits
        cost_ok, error = self.check_cost_limits(estimated_cost)
        if not cost_ok:
            return False, f"Cost limit check failed: {error}"
        
        return True, ""
    
    def register_job_start(self, job_id: str) -> None:
        """Register the start of a job execution."""
        self._active_jobs.add(job_id)
        self._job_start_times[job_id] = datetime.now()
        
    def register_job_completion(self, job_id: str, actual_cost: float = 0.0) -> None:
        """Register the completion of a job execution."""
        if job_id in self._active_jobs:
            self._active_jobs.remove(job_id)
        
        if job_id in self._job_start_times:
            del self._job_start_times[job_id]
        
        # Update cost tracking
        self._daily_cost_used += actual_cost
    
    def get_resource_usage(self) -> ResourceUsage:
        """Get current resource usage statistics."""
        # CPU memory
        cpu_memory = psutil.virtual_memory()
        cpu_memory_used_mb = cpu_memory.used / (1024 * 1024)
        cpu_memory_available_mb = cpu_memory.available / (1024 * 1024)
        cpu_usage_percent = cpu_memory.percent
        
        # GPU memory (if available)
        gpu_memory_used_mb = 0.0
        gpu_memory_available_mb = 0.0
        gpu_usage_percent = 0.0
        
        if torch.cuda.is_available():
            try:
                gpu_memory_total = torch.cuda.get_device_properties(0).total_memory / (1024 * 1024)
                gpu_memory_used_mb = torch.cuda.memory_allocated(0) / (1024 * 1024)
                gpu_memory_available_mb = gpu_memory_total - gpu_memory_used_mb
                # Note: GPU usage percentage would require nvidia-ml-py for accurate measurement
                gpu_usage_percent = (gpu_memory_used_mb / gpu_memory_total) * 100
            except Exception as e:
                logger.warning(f"Failed to get GPU stats: {e}")
        
        return ResourceUsage(
            cpu_memory_used_mb=cpu_memory_used_mb,
            cpu_memory_available_mb=cpu_memory_available_mb,
            gpu_memory_used_mb=gpu_memory_used_mb,
            gpu_memory_available_mb=gpu_memory_available_mb,
            cpu_usage_percent=cpu_usage_percent,
            gpu_usage_percent=gpu_usage_percent,
            active_jobs=len(self._active_jobs),
            queued_jobs=0  # Would be populated by queue manager
        )
    
    def estimate_resource_requirements(self, 
                                     num_assets: int, 
                                     binary_bits: int,
                                     solver_type: str = "classical") -> Dict[str, float]:
        """
        Estimate resource requirements for a given problem.
        
        Args:
            num_assets: Number of assets
            binary_bits: Number of binary bits
            solver_type: Type of solver being used
            
        Returns:
            Dictionary with estimated resource requirements
        """
        # Base memory estimation
        qubo_size = num_assets * binary_bits
        
        # Memory scales quadratically with QUBO size for dense matrices
        base_memory_mb = (qubo_size ** 2 * 8) / (1024 * 1024)  # 8 bytes per double
        
        # Add solver-specific overhead
        solver_overhead = {
            "classical": 1.5,
            "quantum": 3.0,
            "hybrid": 2.0
        }.get(solver_type, 2.0)
        
        estimated_memory_mb = base_memory_mb * solver_overhead
        
        # Time estimation (very rough)
        base_time_seconds = qubo_size / 100.0  # 100 variables per second baseline
        solver_time_factor = {
            "classical": 1.0,
            "quantum": 5.0,  # Quantum solvers often have network overhead
            "hybrid": 2.0
        }.get(solver_type, 2.0)
        
        estimated_time_seconds = base_time_seconds * solver_time_factor
        
        # Cost estimation (simplified)
        cost_per_second = {
            "classical": 0.001,  # $0.001/second
            "quantum": 0.01,     # $0.01/second (cloud quantum)
            "hybrid": 0.005      # $0.005/second
        }.get(solver_type, 0.005)
        
        estimated_cost = estimated_time_seconds * cost_per_second
        
        return {
            "estimated_memory_mb": min(estimated_memory_mb, self.limits.max_cpu_memory_mb),
            "estimated_time_seconds": min(estimated_time_seconds, self.limits.max_execution_time_seconds),
            "estimated_cost": min(estimated_cost, self.limits.max_cost_per_job),
            "qubo_size": qubo_size
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status for monitoring."""
        usage = self.get_resource_usage()
        
        return {
            "resource_limits": {
                "max_assets": self.limits.max_assets,
                "max_binary_bits": self.limits.max_binary_bits,
                "max_cpu_memory_mb": self.limits.max_cpu_memory_mb,
                "max_gpu_memory_mb": self.limits.max_gpu_memory_mb,
                "max_execution_time_seconds": self.limits.max_execution_time_seconds,
                "max_concurrent_jobs": self.limits.max_concurrent_jobs,
                "max_cost_per_job": self.limits.max_cost_per_job,
                "daily_cost_limit": self.limits.daily_cost_limit
            },
            "current_usage": {
                "cpu_memory_used_mb": usage.cpu_memory_used_mb,
                "cpu_memory_available_mb": usage.cpu_memory_available_mb,
                "cpu_usage_percent": usage.cpu_usage_percent,
                "gpu_memory_used_mb": usage.gpu_memory_used_mb,
                "gpu_memory_available_mb": usage.gpu_memory_available_mb,
                "gpu_usage_percent": usage.gpu_usage_percent,
                "active_jobs": usage.active_jobs,
                "queued_jobs": usage.queued_jobs
            },
            "cost_tracking": {
                "daily_cost_used": self._daily_cost_used,
                "daily_cost_remaining": self.limits.daily_cost_limit - self._daily_cost_used,
                "last_cost_reset": self._last_cost_reset.isoformat()
            },
            "system_health": {
                "cpu_memory_pressure": usage.cpu_usage_percent > 80,
                "gpu_memory_pressure": usage.gpu_usage_percent > 80,
                "job_queue_pressure": usage.active_jobs >= self.limits.max_concurrent_jobs * 0.8,
                "cost_pressure": self._daily_cost_used >= self.limits.daily_cost_limit * 0.8
            }
        }


# Global resource guardrails instance
RESOURCE_GUARDRAILS = ResourceGuardrails()
