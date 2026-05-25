"""
Production Solver Hierarchy for QUBO Portfolio Optimizer
Maintains realistic production solver priority system with automatic fallback
and intelligent solver selection based on problem characteristics.
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from enum import Enum
from dataclasses import dataclass

from .solver_registry import SOLVER_REGISTRY, SolverInfo
from .solver_states import SolverState
from .resource_guardrails import RESOURCE_GUARDRAILS
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


class SolverCategory(Enum):
    """Categories of solvers for hierarchical selection."""
    
    PRIMARY_WORKHORSE = "primary_workhorse"    # Main production solver
    PRODUCTION_CLOUD = "production_cloud"        # Production-scale cloud solver
    EXPERIMENTAL_DIRECT = "experimental_direct"  # Experimental direct access
    RESEARCH_VALIDATION = "research_validation"   # Research/validation solver
    ZERO_COST_LOCAL = "zero_cost_local"         # Zero-cost local simulator
    DETERMINISTIC_FALLBACK = "deterministic_fallback"  # Guaranteed fallback


@dataclass
class SolverPreference:
    """Solver preference configuration."""
    
    category: SolverCategory
    priority: int  # Lower number = higher priority
    min_problem_size: int = 5
    max_problem_size: int = 50
    requires_gpu: bool = False
    requires_cloud: bool = False
    cost_per_run: float = 0.0
    quality_weight: float = 1.0
    speed_weight: float = 1.0
    reliability_weight: float = 1.0


class ProductionSolverHierarchy:
    """
    Production solver hierarchy implementing the priority system from the plan:
    
    1. GPU Simulated Bifurcation (primary workhorse)
    2. D-Wave Hybrid (production-scale cloud)
    3. D-Wave QPU (experimental direct access)
    4. Qiskit Experimental (research/validation)
    5. AWS Braket (zero-cost local simulator)
    6. Classical Fallback (deterministic guarantee)
    """
    
    def __init__(self):
        self._preferences = self._initialize_preferences()
        self._cached_hierarchy: Optional[List[SolverInfo]] = None
        self._hierarchy_cache_time = 0
        
    def _initialize_preferences(self) -> Dict[str, SolverPreference]:
        """Initialize solver preferences based on production hierarchy."""
        return {
            # 1. GPU Simulated Bifurcation (primary workhorse)
            "sb_gpu": SolverPreference(
                category=SolverCategory.PRIMARY_WORKHORSE,
                priority=10,
                min_problem_size=5,
                max_problem_size=50,
                requires_gpu=True,
                requires_cloud=False,
                cost_per_run=0.001,
                quality_weight=0.9,
                speed_weight=1.0,
                reliability_weight=0.95
            ),
            
            # 2. D-Wave Hybrid (production-scale cloud)
            "dwave_hybrid": SolverPreference(
                category=SolverCategory.PRODUCTION_CLOUD,
                priority=20,
                min_problem_size=10,
                max_problem_size=50,
                requires_gpu=False,
                requires_cloud=True,
                cost_per_run=0.05,
                quality_weight=0.95,
                speed_weight=0.7,
                reliability_weight=0.9
            ),
            
            # 3. D-Wave QPU (experimental direct access)
            "dwave_qpu": SolverPreference(
                category=SolverCategory.EXPERIMENTAL_DIRECT,
                priority=30,
                min_problem_size=15,
                max_problem_size=50,
                requires_gpu=False,
                requires_cloud=True,
                cost_per_run=0.1,
                quality_weight=1.0,
                speed_weight=0.5,
                reliability_weight=0.7
            ),
            
            # 4. Qiskit Experimental (research/validation)
            "qiskit_qaoa": SolverPreference(
                category=SolverCategory.RESEARCH_VALIDATION,
                priority=40,
                min_problem_size=5,
                max_problem_size=20,
                requires_gpu=False,
                requires_cloud=False,
                cost_per_run=0.01,
                quality_weight=0.8,
                speed_weight=0.6,
                reliability_weight=0.8
            ),
            
            # 5. AWS Braket (zero-cost local simulator)
            "braket_local": SolverPreference(
                category=SolverCategory.ZERO_COST_LOCAL,
                priority=50,
                min_problem_size=5,
                max_problem_size=30,
                requires_gpu=False,
                requires_cloud=False,
                cost_per_run=0.0,
                quality_weight=0.7,
                speed_weight=0.8,
                reliability_weight=0.85
            ),
            
            # 6. Classical Fallback (deterministic guarantee)
            "classical": SolverPreference(
                category=SolverCategory.DETERMINISTIC_FALLBACK,
                priority=100,  # Lowest priority
                min_problem_size=5,
                max_problem_size=100,  # Can handle larger problems
                requires_gpu=False,
                requires_cloud=False,
                cost_per_run=0.0001,
                quality_weight=0.6,
                speed_weight=0.9,
                reliability_weight=1.0
            ),
            
            # Additional local simulators
            "dwave_local": SolverPreference(
                category=SolverCategory.ZERO_COST_LOCAL,
                priority=45,
                min_problem_size=5,
                max_problem_size=40,
                requires_gpu=False,
                requires_cloud=False,
                cost_per_run=0.0,
                quality_weight=0.75,
                speed_weight=0.7,
                reliability_weight=0.9
            ),
            
            "qiskit_local": SolverPreference(
                category=SolverCategory.RESEARCH_VALIDATION,
                priority=55,
                min_problem_size=5,
                max_problem_size=15,
                requires_gpu=False,
                requires_cloud=False,
                cost_per_run=0.0,
                quality_weight=0.7,
                speed_weight=0.6,
                reliability_weight=0.85
            )
        }
    
    def get_production_hierarchy(self) -> List[SolverInfo]:
        """
        Get current production solver hierarchy based on availability and health.
        
        Returns:
            List of available solvers ordered by production priority
        """
        # Check cache validity (cache for 60 seconds)
        import time
        current_time = time.time()
        if (self._cached_hierarchy and 
            current_time - self._hierarchy_cache_time < 60):
            return self._cached_hierarchy
        
        available_solvers = []
        
        # Get all available solvers from registry
        all_solvers = SOLVER_REGISTRY.get_available_solvers()
        
        for solver in all_solvers:
            preference = self._preferences.get(solver.name)
            if not preference:
                # Unknown solver, give lowest priority
                preference = SolverPreference(
                    category=SolverCategory.DETERMINISTIC_FALLBACK,
                    priority=999,
                    cost_per_run=0.0
                )
            
            # Check if solver meets problem requirements
            if self._solver_meets_requirements(solver, preference):
                # Calculate production score
                production_score = self._calculate_production_score(solver, preference)
                
                available_solvers.append((solver, preference, production_score))
        
        # Sort by priority, then by production score
        available_solvers.sort(key=lambda x: (x[1].priority, -x[2]))
        
        # Extract just the solver info
        hierarchy = [solver for solver, _, _ in available_solvers]
        
        # Cache result
        self._cached_hierarchy = hierarchy
        self._hierarchy_cache_time = current_time
        
        logger.info(f"Production hierarchy updated: {len(hierarchy)} solvers available")
        return hierarchy
    
    def _solver_meets_requirements(self, solver: SolverInfo, preference: SolverPreference) -> bool:
        """Check if solver meets basic requirements."""
        # Check GPU requirement
        if preference.requires_gpu and not solver.capabilities.supports_gpu:
            return False
        
        # Check cloud requirement
        if preference.requires_cloud and not solver.capabilities.supports_cloud:
            return False
        
        # Check if solver is healthy enough for production
        if not solver.health_metrics.is_healthy:
            # Allow unhealthy solvers only as fallback
            if preference.category != SolverCategory.DETERMINISTIC_FALLBACK:
                return False
        
        return True
    
    def _calculate_production_score(self, solver: SolverInfo, preference: SolverPreference) -> float:
        """Calculate production score for solver ranking."""
        score = 0.0
        
        # Quality component
        quality_score = solver.capabilities.quality_score * preference.quality_weight
        score += quality_score * 0.4
        
        # Speed component (inverse of average latency)
        if solver.health_metrics.average_latency_seconds > 0:
            speed_score = (1.0 / solver.health_metrics.average_latency_seconds) * preference.speed_weight
        else:
            speed_score = 1.0 * preference.speed_weight
        score += min(speed_score, 1.0) * 0.3
        
        # Reliability component
        reliability_score = (solver.health_metrics.success_rate / 100.0) * preference.reliability_weight
        score += reliability_score * 0.2
        
        # Cost component (lower cost is better)
        if preference.cost_per_run > 0:
            cost_score = (1.0 / preference.cost_per_run) * 0.1
        else:
            cost_score = 1.0 * 0.1
        score += min(cost_score, 0.1)
        
        return score
    
    def select_best_solver(self, 
                         num_assets: int, 
                         binary_bits: int,
                         solver_type: Optional[str] = None,
                         require_gpu: bool = False,
                         cost_limit: Optional[float] = None) -> Optional[SolverInfo]:
        """
        Select the best solver for a specific problem using production hierarchy.
        
        Args:
            num_assets: Number of assets in the problem
            binary_bits: Number of binary bits per asset
            solver_type: Preferred solver type ('quantum', 'classical', 'hybrid')
            require_gpu: Whether GPU acceleration is required
            cost_limit: Maximum cost per run
            
        Returns:
            Best matching solver or None if no suitable solver found
        """
        hierarchy = self.get_production_hierarchy()
        
        for solver in hierarchy:
            preference = self._preferences.get(solver.name)
            if not preference:
                continue
            
            # Check problem size constraints
            if not (preference.min_problem_size <= num_assets <= preference.max_problem_size):
                continue
            
            # Check solver type preference
            if solver_type and solver.solver_type != solver_type:
                continue
            
            # Check GPU requirement
            if require_gpu and not solver.capabilities.supports_gpu:
                continue
            
            # Check cost limit
            if cost_limit and preference.cost_per_run > cost_limit:
                continue
            
            # Check if solver can handle the problem
            if not solver.capabilities.can_handle_problem(num_assets, binary_bits):
                continue
            
            # Check resource guardrails
            resource_reqs = RESOURCE_GUARDRAILS.estimate_resource_requirements(
                num_assets, binary_bits, solver.solver_type
            )
            can_execute, error = RESOURCE_GUARDRAILS.can_execute_job(
                num_assets, binary_bits,
                resource_reqs['estimated_memory_mb'],
                resource_reqs['estimated_time_seconds'],
                preference.cost_per_run
            )
            
            if not can_execute:
                logger.debug(f"Solver {solver.name} rejected by resource guardrails: {error}")
                continue
            
            return solver
        
        return None
    
    def get_solver_recommendations(self, 
                                 num_assets: int, 
                                 binary_bits: int,
                                 max_recommendations: int = 3) -> List[Dict[str, Any]]:
        """
        Get solver recommendations with reasoning.
        
        Args:
            num_assets: Number of assets in the problem
            binary_bits: Number of binary bits per asset
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            List of solver recommendations with details
        """
        hierarchy = self.get_production_hierarchy()
        recommendations = []
        
        for solver in hierarchy[:max_recommendations * 2]:  # Check more to find best matches
            preference = self._preferences.get(solver.name)
            if not preference:
                continue
            
            # Check if solver can handle the problem
            if not solver.capabilities.can_handle_problem(num_assets, binary_bits):
                continue
            
            # Calculate recommendation score
            score = self._calculate_production_score(solver, preference)
            
            # Generate reasoning
            reasoning = self._generate_solver_reasoning(solver, preference, num_assets, binary_bits)
            
            recommendations.append({
                "solver_name": solver.name,
                "solver_type": solver.solver_type,
                "category": preference.category.value,
                "priority": preference.priority,
                "score": round(score, 3),
                "estimated_cost": preference.cost_per_run,
                "estimated_time": solver.capabilities.average_solve_time_seconds,
                "quality_score": solver.capabilities.quality_score,
                "success_rate": solver.health_metrics.success_rate,
                "reasoning": reasoning,
                "supports_gpu": solver.capabilities.supports_gpu,
                "requires_cloud": preference.requires_cloud
            })
            
            if len(recommendations) >= max_recommendations:
                break
        
        # Sort by score and return top recommendations
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:max_recommendations]
    
    def _generate_solver_reasoning(self, 
                                  solver: SolverInfo, 
                                  preference: SolverPreference,
                                  num_assets: int, 
                                  binary_bits: int) -> List[str]:
        """Generate reasoning for solver recommendation."""
        reasoning = []
        
        # Category-based reasoning
        if preference.category == SolverCategory.PRIMARY_WORKHORSE:
            reasoning.append("Primary production workhorse with best balance of speed and quality")
        elif preference.category == SolverCategory.PRODUCTION_CLOUD:
            reasoning.append("Production-scale cloud solver with high quality results")
        elif preference.category == SolverCategory.EXPERIMENTAL_DIRECT:
            reasoning.append("Experimental direct quantum access for cutting-edge performance")
        elif preference.category == SolverCategory.RESEARCH_VALIDATION:
            reasoning.append("Research-grade solver for validation and experimentation")
        elif preference.category == SolverCategory.ZERO_COST_LOCAL:
            reasoning.append("Zero-cost local simulator for development and testing")
        elif preference.category == SolverCategory.DETERMINISTIC_FALLBACK:
            reasoning.append("Reliable deterministic fallback with guaranteed results")
        
        # Performance-based reasoning
        if solver.capabilities.quality_score >= 0.9:
            reasoning.append("Excellent solution quality")
        elif solver.health_metrics.success_rate >= 90:
            reasoning.append("High reliability and success rate")
        elif solver.capabilities.average_solve_time_seconds <= 1.0:
            reasoning.append("Fast execution speed")
        
        # Cost-based reasoning
        if preference.cost_per_run == 0:
            reasoning.append("No cost - free to use")
        elif preference.cost_per_run <= 0.01:
            reasoning.append("Low cost operation")
        
        # Hardware-based reasoning
        if solver.capabilities.supports_gpu:
            reasoning.append("GPU acceleration available")
        
        # Problem-size reasoning
        if num_assets <= 15 and preference.category in [SolverCategory.ZERO_COST_LOCAL, SolverCategory.RESEARCH_VALIDATION]:
            reasoning.append("Well-suited for small to medium problems")
        elif num_assets >= 30 and preference.category == SolverCategory.PRODUCTION_CLOUD:
            reasoning.append("Optimized for larger problems")
        
        return reasoning
    
    def get_hierarchy_stats(self) -> Dict[str, Any]:
        """Get statistics about the current solver hierarchy."""
        hierarchy = self.get_production_hierarchy()
        
        stats = {
            "total_available": len(hierarchy),
            "by_category": {},
            "by_type": {},
            "gpu_available": 0,
            "cloud_available": 0,
            "average_quality": 0.0,
            "average_cost": 0.0
        }
        
        if hierarchy:
            total_quality = 0
            total_cost = 0
            
            for solver in hierarchy:
                preference = self._preferences.get(solver.name)
                
                # Category stats
                category = preference.category.value if preference else "unknown"
                stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
                
                # Type stats
                solver_type = solver.solver_type
                stats["by_type"][solver_type] = stats["by_type"].get(solver_type, 0) + 1
                
                # Hardware stats
                if solver.capabilities.supports_gpu:
                    stats["gpu_available"] += 1
                if solver.capabilities.supports_cloud:
                    stats["cloud_available"] += 1
                
                # Quality and cost stats
                total_quality += solver.capabilities.quality_score
                if preference:
                    total_cost += preference.cost_per_run
            
            stats["average_quality"] = total_quality / len(hierarchy)
            stats["average_cost"] = total_cost / len(hierarchy)
        
        return stats
    
    def invalidate_cache(self) -> None:
        """Invalidate cached hierarchy."""
        self._cached_hierarchy = None
        self._hierarchy_cache_time = 0


# Global production hierarchy instance
PRODUCTION_HIERARCHY = ProductionSolverHierarchy()
