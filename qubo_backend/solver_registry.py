"""
Centralized Solver Registry for QUBO Portfolio Optimizer
Provides unified solver registration, health tracking, and capability management.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Type, Callable, Any
from datetime import datetime, timedelta
import importlib
from dataclasses import dataclass, field

from .solver_states import (
    SolverState, SolverInfo, SolverCapabilities, 
    SolverHealthMetrics, SolverStateMachine
)
from .config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class SolverRegistration:
    """Registration information for a solver."""
    
    solver_class: Type
    factory_function: Optional[Callable] = None
    health_check_function: Optional[Callable] = None
    benchmark_function: Optional[Callable] = None
    config_requirements: Dict[str, Any] = field(default_factory=dict)


class SolverRegistry:
    """
    Centralized registry for managing all optimization solvers.
    
    Provides dynamic solver registration, health state tracking, 
    runtime availability detection, and benchmarking history.
    """
    
    def __init__(self):
        self._solvers: Dict[str, SolverInfo] = {}
        self._registrations: Dict[str, SolverRegistration] = {}
        self._health_check_interval = 300  # 5 minutes
        self._settings = get_settings()
        self._lock = asyncio.Lock()
        
    def register_solver(self, 
                       name: str,
                       solver_type: str,
                       capabilities: SolverCapabilities,
                       registration: SolverRegistration,
                       description: str = "",
                       version: str = "1.0.0",
                       priority: int = 100,
                       experimental: bool = False,
                       tags: Optional[set] = None) -> bool:
        """
        Register a new solver with the registry.
        
        Args:
            name: Unique solver identifier
            solver_type: Type of solver ('quantum', 'classical', 'hybrid')
            capabilities: Solver capabilities and constraints
            registration: Registration information including classes and functions
            description: Human-readable description
            version: Solver version
            priority: Priority for solver selection (lower = higher priority)
            experimental: Whether this is an experimental solver
            tags: Tags for categorization
            
        Returns:
            True if registration successful, False if name already exists
        """
        if name in self._solvers:
            logger.warning(f"Solver {name} already registered, skipping")
            return False
        
        # Create solver info with initial state
        health_metrics = SolverHealthMetrics()
        solver_info = SolverInfo(
            name=name,
            solver_type=solver_type,
            state=SolverState.IMPORT_FAILED,  # Will be updated during health check
            capabilities=capabilities,
            health_metrics=health_metrics,
            description=description,
            version=version,
            priority=priority,
            experimental=experimental,
            tags=tags or set(),
            registration_time=datetime.now()
        )
        
        self._solvers[name] = solver_info
        self._registrations[name] = registration
        
        logger.info(f"Registered solver: {name} ({solver_type})")
        return True
    
    async def initialize_solver_health(self) -> None:
        """Initialize health state for all registered solvers."""
        async with self._lock:
            for name, solver_info in self._solvers.items():
                await self._check_solver_health(name)
    
    async def _check_solver_health(self, solver_name: str) -> None:
        """Check health status of a specific solver."""
        if solver_name not in self._solvers:
            return
        
        solver_info = self._solvers[solver_name]
        registration = self._registrations.get(solver_name)
        
        if not registration:
            return
        
        try:
            # Check if solver package can be imported
            if hasattr(registration.solver_class, '__module__'):
                module_name = registration.solver_class.__module__
                importlib.import_module(module_name)
                SolverStateMachine.transition_state(
                    solver_info, SolverState.INSTALLED, "Import successful"
                )
            else:
                SolverStateMachine.transition_state(
                    solver_info, SolverState.IMPORT_FAILED, "No module found"
                )
                return
            
            # Check GPU availability if required
            if solver_info.capabilities.supports_gpu:
                if await self._check_gpu_availability():
                    SolverStateMachine.transition_state(
                        solver_info, SolverState.GPU_READY, "GPU available"
                    )
                else:
                    # Keep as INSTALLED but note GPU not available
                    pass
            
            # Check authentication for cloud solvers
            if solver_info.capabilities.supports_cloud:
                if await self._check_cloud_auth(solver_name):
                    SolverStateMachine.transition_state(
                        solver_info, SolverState.CLOUD_READY, "Cloud auth successful"
                    )
                else:
                    SolverStateMachine.transition_state(
                        solver_info, SolverState.TOKEN_MISSING, "Cloud auth failed"
                    )
            else:
                # Local simulator
                SolverStateMachine.transition_state(
                    solver_info, SolverState.LOCAL_SIMULATOR_READY, "Local simulator ready"
                )
            
            # Run custom health check if provided
            if registration.health_check_function:
                health_result = await registration.health_check_function()
                if health_result:
                    SolverStateMachine.transition_state(
                        solver_info, SolverState.BENCHMARK_READY, "Custom health check passed"
                    )
                else:
                    SolverStateMachine.transition_state(
                        solver_info, SolverState.EXECUTION_FAILED, "Custom health check failed"
                    )
            
            # Update health metrics
            solver_info.health_metrics.last_health_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Health check failed for {solver_name}: {e}")
            SolverStateMachine.transition_state(
                solver_info, SolverState.IMPORT_FAILED, f"Health check error: {str(e)}"
            )
            solver_info.health_metrics.last_error_message = str(e)
    
    async def _check_gpu_availability(self) -> bool:
        """Check if GPU is available and configured."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    async def _check_cloud_auth(self, solver_name: str) -> bool:
        """Check cloud authentication for a specific solver."""
        try:
            if solver_name.startswith('dwave'):
                return bool(self._settings.dwave_api_token)
            elif solver_name.startswith('qiskit'):
                return bool(self._settings.ibm_quantum_token)
            elif solver_name.startswith('braket'):
                # AWS Braket would check AWS credentials
                return True  # Simplified for now
            return False
        except Exception:
            return False
    
    def get_solver(self, name: str) -> Optional[SolverInfo]:
        """Get solver information by name."""
        return self._solvers.get(name)
    
    def get_available_solvers(self, 
                             solver_type: Optional[str] = None,
                             min_quality_score: float = 0.0,
                             require_gpu: bool = False) -> List[SolverInfo]:
        """
        Get list of available solvers matching criteria.
        
        Args:
            solver_type: Filter by solver type ('quantum', 'classical', 'hybrid')
            min_quality_score: Minimum quality score threshold
            require_gpu: Only return GPU-enabled solvers
            
        Returns:
            List of available solver information
        """
        available = []
        
        for solver in self._solvers.values():
            if not solver.is_available:
                continue
            
            if solver_type and solver.solver_type != solver_type:
                continue
            
            if solver.capabilities.quality_score < min_quality_score:
                continue
            
            if require_gpu and not solver.capabilities.supports_gpu:
                continue
            
            available.append(solver)
        
        # Sort by priority (lower number = higher priority)
        available.sort(key=lambda s: s.priority)
        return available
    
    def get_best_solver(self, 
                       num_assets: int, 
                       binary_bits: int,
                       solver_type: Optional[str] = None,
                       require_gpu: bool = False) -> Optional[SolverInfo]:
        """
        Get the best solver for a specific problem.
        
        Args:
            num_assets: Number of assets in the problem
            binary_bits: Number of binary bits per asset
            solver_type: Preferred solver type
            require_gpu: Whether GPU acceleration is required
            
        Returns:
            Best matching solver or None if no suitable solver found
        """
        candidates = []
        
        for solver in self.get_available_solvers(solver_type, require_gpu=require_gpu):
            if solver.capabilities.can_handle_problem(num_assets, binary_bits):
                # Calculate suitability score
                score = solver.capabilities.quality_score
                
                # Prefer healthy solvers
                if solver.health_metrics.is_healthy:
                    score += 0.2
                
                # Prefer solvers with good success rate
                if solver.health_metrics.success_rate > 80:
                    score += 0.1
                
                # Prefer faster solvers for small problems
                if num_assets <= 15 and solver.capabilities.average_solve_time_seconds < 1.0:
                    score += 0.1
                
                candidates.append((score, solver))
        
        if not candidates:
            return None
        
        # Return solver with highest suitability score
        _, best_solver = max(candidates, key=lambda x: x[0])
        return best_solver
    
    def update_solver_metrics(self, 
                            solver_name: str, 
                            success: bool, 
                            execution_time: float,
                            error_message: Optional[str] = None) -> None:
        """Update solver health metrics after execution."""
        if solver_name not in self._solvers:
            return
        
        solver = self._solvers[solver_name]
        metrics = solver.health_metrics
        
        metrics.total_runs += 1
        
        if success:
            metrics.successful_runs += 1
            metrics.last_successful_run = datetime.now()
            metrics.consecutive_failures = 0
            
            # Update average latency
            if metrics.average_latency_seconds == 0:
                metrics.average_latency_seconds = execution_time
            else:
                # Exponential moving average
                alpha = 0.1
                metrics.average_latency_seconds = (
                    alpha * execution_time + 
                    (1 - alpha) * metrics.average_latency_seconds
                )
        else:
            metrics.consecutive_failures += 1
            metrics.last_failure_time = datetime.now()
            if error_message:
                metrics.last_error_message = error_message
            
            # Transition to failed state if too many consecutive failures
            if metrics.consecutive_failures >= 3:
                SolverStateMachine.transition_state(
                    solver, SolverState.EXECUTION_FAILED, 
                    f"Too many failures: {metrics.consecutive_failures}"
                )
    
    def get_solver_stats(self) -> Dict[str, Any]:
        """Get overall registry statistics."""
        stats = {
            'total_solvers': len(self._solvers),
            'available_solvers': len([s for s in self._solvers.values() if s.is_available]),
            'healthy_solvers': len([s for s in self._solvers.values() if s.health_metrics.is_healthy]),
            'solver_types': {},
            'states': {}
        }
        
        for solver in self._solvers.values():
            # Count by type
            solver_type = solver.solver_type
            stats['solver_types'][solver_type] = stats['solver_types'].get(solver_type, 0) + 1
            
            # Count by state
            state_name = solver.state.name
            stats['states'][state_name] = stats['states'].get(state_name, 0) + 1
        
        return stats
    
    async def start_health_monitoring(self) -> None:
        """Start background health monitoring for all solvers."""
        while True:
            try:
                await asyncio.sleep(self._health_check_interval)
                await self.initialize_solver_health()
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")


# Global registry instance
SOLVER_REGISTRY = SolverRegistry()
