"""
Comprehensive Solver State Machine for QUBO Portfolio Optimizer
Provides precise status tracking for all solver types and their operational states.
"""

from enum import Enum, auto
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class SolverState(Enum):
    """Comprehensive solver state enumeration for precise status tracking."""
    
    # Installation and Import States
    INSTALLED = auto()           # Solver package is installed and importable
    IMPORT_FAILED = auto()       # Failed to import solver package
    GPU_READY = auto()           # GPU resources are available and configured
    TOKEN_MISSING = auto()       # Required API token is missing
    AUTH_FAILED = auto()         # Authentication with cloud provider failed
    
    # Network and Cloud States
    NETWORK_UNAVAILABLE = auto() # Network connectivity issues
    CLOUD_READY = auto()         # Cloud service is accessible and authenticated
    LOCAL_SIMULATOR_READY = auto() # Local simulator is ready for use
    
    # Execution States
    EXECUTION_FAILED = auto()    # Last execution failed
    BENCHMARK_READY = auto()     # Solver has been benchmarked and is ready
    FALLBACK_ONLY = auto()       # Only available as fallback option
    
    # Special States
    DISABLED = auto()            # Explicitly disabled by configuration
    EXPERIMENTAL = auto()        # Experimental solver, use with caution
    DEPRECATED = auto()          # Deprecated solver, will be removed


@dataclass
class SolverCapabilities:
    """Metadata describing solver capabilities and constraints."""
    
    max_assets: int = 50
    max_binary_bits: int = 7
    supports_gpu: bool = False
    supports_cloud: bool = False
    supports_local: bool = True
    requires_auth: bool = False
    estimated_cost_per_run: float = 0.0
    average_solve_time_seconds: float = 1.0
    quality_score: float = 1.0  # 1.0 = best quality, 0.0 = worst
    memory_requirement_mb: int = 512
    vram_requirement_mb: int = 0
    supported_problem_sizes: List[int] = field(default_factory=lambda: [5, 10, 15, 20, 25, 30, 40, 50])
    
    def can_handle_problem(self, num_assets: int, binary_bits: int) -> bool:
        """Check if solver can handle the given problem size."""
        return (num_assets <= self.max_assets and 
                binary_bits <= self.max_binary_bits and
                num_assets in self.supported_problem_sizes)


@dataclass
class SolverHealthMetrics:
    """Health and performance metrics for a solver."""
    
    last_health_check: Optional[datetime] = None
    last_successful_run: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    total_runs: int = 0
    successful_runs: int = 0
    average_latency_seconds: float = 0.0
    last_error_message: Optional[str] = None
    benchmark_score: Optional[float] = None
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.total_runs == 0:
            return 0.0
        return (self.successful_runs / self.total_runs) * 100.0
    
    @property
    def is_healthy(self) -> bool:
        """Determine if solver is considered healthy."""
        if self.consecutive_failures >= 3:
            return False
        if self.success_rate < 50.0 and self.total_runs >= 10:
            return False
        return True


@dataclass
class SolverInfo:
    """Complete information about a registered solver."""
    
    name: str
    solver_type: str  # 'quantum', 'classical', 'hybrid'
    state: SolverState
    capabilities: SolverCapabilities
    health_metrics: SolverHealthMetrics
    description: str = ""
    version: str = "1.0.0"
    priority: int = 100  # Lower number = higher priority
    enabled: bool = True
    experimental: bool = False
    deprecated: bool = False
    tags: Set[str] = field(default_factory=set)
    registration_time: datetime = field(default_factory=datetime.now)
    
    @property
    def is_available(self) -> bool:
        """Check if solver is currently available for use."""
        return (self.enabled and 
                not self.deprecated and
                self.state in [SolverState.INSTALLED, SolverState.GPU_READY, 
                             SolverState.CLOUD_READY, SolverState.LOCAL_SIMULATOR_READY,
                             SolverState.BENCHMARK_READY])
    
    @property
    def is_recommended(self) -> bool:
        """Check if solver is recommended for production use."""
        return (self.is_available and 
                not self.experimental and
                self.health_metrics.is_healthy and
                self.state != SolverState.FALLBACK_ONLY)


class SolverStateMachine:
    """Manages state transitions for solvers."""
    
    @staticmethod
    def can_transition(from_state: SolverState, to_state: SolverState) -> bool:
        """Check if a state transition is valid."""
        # Define valid transitions
        valid_transitions = {
            SolverState.IMPORT_FAILED: [
                SolverState.INSTALLED, SolverState.DISABLED
            ],
            SolverState.INSTALLED: [
                SolverState.GPU_READY, SolverState.TOKEN_MISSING, 
                SolverState.NETWORK_UNAVAILABLE, SolverState.LOCAL_SIMULATOR_READY,
                SolverState.DISABLED, SolverState.EXECUTION_FAILED
            ],
            SolverState.GPU_READY: [
                SolverState.LOCAL_SIMULATOR_READY, SolverState.EXECUTION_FAILED,
                SolverState.DISABLED
            ],
            SolverState.TOKEN_MISSING: [
                SolverState.AUTH_FAILED, SolverState.CLOUD_READY,
                SolverState.DISABLED
            ],
            SolverState.AUTH_FAILED: [
                SolverState.CLOUD_READY, SolverState.TOKEN_MISSING,
                SolverState.DISABLED
            ],
            SolverState.NETWORK_UNAVAILABLE: [
                SolverState.CLOUD_READY, SolverState.LOCAL_SIMULATOR_READY,
                SolverState.DISABLED
            ],
            SolverState.CLOUD_READY: [
                SolverState.BENCHMARK_READY, SolverState.EXECUTION_FAILED,
                SolverState.NETWORK_UNAVAILABLE, SolverState.DISABLED
            ],
            SolverState.LOCAL_SIMULATOR_READY: [
                SolverState.BENCHMARK_READY, SolverState.EXECUTION_FAILED,
                SolverState.DISABLED
            ],
            SolverState.EXECUTION_FAILED: [
                SolverState.BENCHMARK_READY, SolverState.FALLBACK_ONLY,
                SolverState.INSTALLED, SolverState.DISABLED
            ],
            SolverState.BENCHMARK_READY: [
                SolverState.EXECUTION_FAILED, SolverState.FALLBACK_ONLY,
                SolverState.DISABLED
            ],
            SolverState.FALLBACK_ONLY: [
                SolverState.BENCHMARK_READY, SolverState.DISABLED
            ],
            SolverState.DISABLED: [
                SolverState.INSTALLED, SolverState.EXPERIMENTAL
            ],
            SolverState.EXPERIMENTAL: [
                SolverState.INSTALLED, SolverState.DISABLED
            ],
            SolverState.DEPRECATED: [
                SolverState.DISABLED
            ]
        }
        
        return to_state in valid_transitions.get(from_state, [])
    
    @staticmethod
    def transition_state(solver_info: SolverInfo, new_state: SolverState, 
                        reason: str = "") -> bool:
        """Attempt to transition solver to a new state."""
        if not SolverStateMachine.can_transition(solver_info.state, new_state):
            logger.warning(f"Invalid state transition for {solver_info.name}: "
                         f"{solver_info.state} -> {new_state}")
            return False
        
        old_state = solver_info.state
        solver_info.state = new_state
        
        logger.info(f"Solver {solver_info.name} transitioned: "
                   f"{old_state} -> {new_state}" + 
                   (f" ({reason})" if reason else ""))
        
        return True
