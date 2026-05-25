"""
Qurve AI - Cost Fallback System
Safe fallback chain preservation when cloud governance blocks execution.

Features:
✅ Cloud → Local Braket → Qiskit → Neal → Classical
✅ Fallback telemetry emission
✅ Governance decision integration
✅ Cost impact tracking
✅ Fallback chain reconstruction
"""

import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import logging

from .governance_schemas import (
    GovernanceDecisionSchema,
    FallbackEventSchema,
    CostTelemetrySchema
)

logger = logging.getLogger(__name__)


class SolverType(Enum):
    """Solver type enumeration for fallback chain."""
    CLOUD_BRAKET = "cloud_braket"
    LOCAL_BRAKET = "local_braket"
    QISKIT = "qiskit"
    NEAL = "neal"
    CLASSICAL = "classical"


@dataclass
class FallbackDecision:
    """Fallback decision data structure."""
    correlation_id: str
    governance_decision: GovernanceDecisionSchema
    original_solver: SolverType
    selected_solver: SolverType
    fallback_reason: str
    cost_impact_usd: Optional[float] = None
    cloud_cost_avoided_usd: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FallbackConfig:
    """Fallback configuration."""
    enable_cloud_fallback: bool = True
    enable_local_fallback: bool = True
    fallback_chain: List[SolverType] = field(default_factory=lambda: [
        SolverType.LOCAL_BRAKET,
        SolverType.QISKIT,
        SolverType.NEAL,
        SolverType.CLASSICAL
    ])
    max_fallback_depth: int = 4


class CostFallbacks:
    """
    Production-grade cost fallback system.
    
    Features:
    - Safe fallback chain preservation
    - Cost impact tracking
    - Governance decision integration
    - Fallback telemetry emission
    - Cloud cost avoidance tracking
    """
    
    def __init__(self, config: FallbackConfig):
        self.config = config
        
        # Fallback state
        self._fallback_history: List[FallbackEventSchema] = []
        
        logger.info("Cost fallbacks initialized", 
                  fallback_chain=[s.value for s in config.fallback_chain],
                  max_depth=config.max_fallback_depth)
    
    def evaluate_fallback(self, 
                        governance_decision: GovernanceDecisionSchema,
                        correlation_id: str,
                        original_solver: SolverType,
                        estimated_cost_usd: Optional[float] = None) -> FallbackDecision:
        """
        Evaluate if fallback is needed based on governance decision.
        
        Args:
            governance_decision: Governance decision from cost system
            correlation_id: Execution correlation ID
            original_solver: Originally requested solver
            estimated_cost_usd: Estimated cost of cloud execution
            
        Returns:
            Fallback decision with selected solver
        """
        try:
            # Determine fallback decision
            if governance_decision == GovernanceDecisionSchema.ALLOW:
                selected_solver = original_solver
                fallback_reason = "Governance allowed execution"
                cost_impact = estimated_cost_usd
                cloud_cost_avoided = 0.0
                
            elif governance_decision == GovernanceDecisionSchema.THROTTLE:
                if self.config.enable_cloud_fallback:
                    selected_solver = self.config.fallback_chain[0]  # First fallback
                    fallback_reason = "Governance throttled cloud, falling back to local"
                    cost_impact = 0.0  # Local execution cost
                    cloud_cost_avoided = estimated_cost_usd if estimated_cost_usd else 0.0
                else:
                    selected_solver = original_solver
                    fallback_reason = "Cloud throttled but fallback disabled"
                    cost_impact = estimated_cost_usd
                    cloud_cost_avoided = 0.0
                    
            elif governance_decision == GovernanceDecisionSchema.FALLBACK:
                if self.config.enable_cloud_fallback and self.config.fallback_chain:
                    selected_solver = self.config.fallback_chain[0]  # First fallback
                    fallback_reason = "Governance forced fallback to local"
                    cost_impact = 0.0  # Local execution cost
                    cloud_cost_avoided = estimated_cost_usd if estimated_cost_usd else 0.0
                else:
                    selected_solver = original_solver
                    fallback_reason = "Governance requested fallback but fallback disabled"
                    cost_impact = estimated_cost_usd
                    cloud_cost_avoided = 0.0
                    
            else:  # REJECT
                if self.config.enable_local_fallback and self.config.fallback_chain:
                    selected_solver = self.config.fallback_chain[0]  # First fallback
                    fallback_reason = "Governance rejected cloud, falling back to local"
                    cost_impact = 0.0  # Local execution cost
                    cloud_cost_avoided = estimated_cost_usd if estimated_cost_usd else 0.0
                else:
                    selected_solver = SolverType.CLASSICAL  # Final fallback
                    fallback_reason = "All options rejected, using classical fallback"
                    cost_impact = 0.0
                    cloud_cost_avoided = 0.0
            
            decision = FallbackDecision(
                correlation_id=correlation_id,
                governance_decision=governance_decision,
                original_solver=original_solver,
                selected_solver=selected_solver,
                fallback_reason=fallback_reason,
                cost_impact_usd=cost_impact,
                cloud_cost_avoided_usd=cloud_cost_avoided,
                metadata={
                    "governance_decision": governance_decision.value,
                    "fallback_chain_position": self._get_fallback_position(original_solver, selected_solver),
                    "is_fallback": selected_solver != original_solver
                }
            )
            
            # Record fallback event
            self._record_fallback_event(decision)
            
            return decision
            
        except Exception as e:
            logger.error("Fallback evaluation failed", 
                        correlation_id=correlation_id,
                        governance_decision=governance_decision.value,
                        error=str(e))
            
            # Safe fallback to classical
            return FallbackDecision(
                correlation_id=correlation_id,
                governance_decision=governance_decision,
                original_solver=original_solver,
                selected_solver=SolverType.CLASSICAL,
                fallback_reason=f"Fallback evaluation error: {str(e)}",
                cost_impact_usd=0.0,
                cloud_cost_avoided_usd=estimated_cost_usd if estimated_cost_usd else 0.0
            )
    
    def _get_fallback_position(self, original: SolverType, selected: SolverType) -> int:
        """Get position in fallback chain."""
        if original == selected:
            return 0
        
        try:
            return self.config.fallback_chain.index(selected) + 1
        except ValueError:
            return len(self.config.fallback_chain) + 1
    
    def _record_fallback_event(self, decision: FallbackDecision) -> None:
        """Record fallback event for telemetry."""
        try:
            event = FallbackEventSchema(
                event_id=f"fallback_{int(time.time())}_{len(self._fallback_history)}",
                correlation_id=decision.correlation_id,
                timestamp=datetime.now(),
                from_solver=decision.original_solver.value,
                to_solver=decision.selected_solver.value,
                fallback_reason=decision.fallback_reason,
                governance_decision=decision.governance_decision,
                cloud_cost_impact=decision.cost_impact_usd,
                metadata=decision.metadata
            )
            
            self._fallback_history.append(event)
            
            # Emit fallback telemetry
            logger.info("Fallback event recorded", 
                       correlation_id=decision.correlation_id,
                       from_solver=decision.original_solver.value,
                       to_solver=decision.selected_solver.value,
                       reason=decision.fallback_reason,
                       governance_decision=decision.governance_decision.value,
                       cloud_cost_avoided=decision.cloud_cost_avoided_usd)
            
            # TODO: Integrate with monitoring service
            # monitoring_service = get_monitoring_service()
            # await monitoring_service.store_telemetry_event(...)
            
        except Exception as e:
            logger.error("Failed to record fallback event", 
                        correlation_id=decision.correlation_id, 
                        error=str(e))
    
    def get_fallback_chain(self) -> List[SolverType]:
        """Get current fallback chain."""
        return self.config.fallback_chain.copy()
    
    def get_fallback_history(self, limit: int = 100) -> List[FallbackEventSchema]:
        """Get recent fallback events."""
        return sorted(self._fallback_history, key=lambda e: e.timestamp, reverse=True)[:limit]
    
    def get_fallback_statistics(self) -> Dict[str, Any]:
        """Get fallback statistics and metrics."""
        if not self._fallback_history:
            return {
                "total_fallbacks": 0,
                "fallback_rate": 0.0,
                "cost_savings_usd": 0.0,
                "most_common_reason": None,
                "fallback_by_solver": {},
                "fallback_by_reason": {}
            }
        
        # Calculate statistics
        total_fallbacks = len(self._fallback_history)
        cloud_fallbacks = [f for f in self._fallback_history if f.from_solver == SolverType.CLOUD_BRAKET.value]
        cost_savings = sum(f.cloud_cost_impact or 0.0 for f in cloud_fallbacks)
        
        # Most common fallback reason
        reason_counts = {}
        for event in self._fallback_history:
            reason = event.fallback_reason
            reason_counts[reason] = reason_counts.get(reason, 0) + 1
        
        most_common_reason = max(reason_counts.items(), key=lambda x: x[1])[0] if reason_counts else None
        
        # Fallback by solver
        solver_counts = {}
        for event in self._fallback_history:
            to_solver = event.to_solver
            solver_counts[to_solver] = solver_counts.get(to_solver, 0) + 1
        
        # Fallback by reason
        fallback_by_reason = {}
        for event in self._fallback_history:
            reason = event.fallback_reason
            if reason not in fallback_by_reason:
                fallback_by_reason[reason] = []
            fallback_by_reason[reason].append({
                "timestamp": event.timestamp.isoformat(),
                "correlation_id": event.correlation_id,
                "from_solver": event.from_solver,
                "to_solver": event.to_solver
            })
        
        return {
            "total_fallbacks": total_fallbacks,
            "cloud_fallbacks": len(cloud_fallbacks),
            "fallback_rate": (len(cloud_fallbacks) / total_fallbacks * 100) if total_fallbacks > 0 else 0.0,
            "cost_savings_usd": cost_savings,
            "most_common_reason": most_common_reason,
            "fallback_by_solver": solver_counts,
            "fallback_by_reason": fallback_by_reason,
            "fallback_chain": [s.value for s in self.config.fallback_chain],
            "max_fallback_depth": self.config.max_fallback_depth
        }
    
    def update_config(self, new_config: FallbackConfig) -> None:
        """Update fallback configuration."""
        self.config = new_config
        logger.info("Fallback configuration updated", 
                  fallback_chain=[s.value for s in new_config.fallback_chain],
                  max_depth=new_config.max_fallback_depth)


# Global cost fallbacks instance
_cost_fallbacks: Optional[CostFallbacks] = None


def get_cost_fallbacks() -> CostFallbacks:
    """Get global cost fallbacks instance."""
    global _cost_fallbacks
    if _cost_fallbacks is None:
        _cost_fallbacks = CostFallbacks(FallbackConfig())
    return _cost_fallbacks


def create_fallback_config(
    enable_cloud_fallback: bool = True,
    enable_local_fallback: bool = True,
    fallback_chain: Optional[List[str]] = None,
    max_fallback_depth: int = 4
) -> FallbackConfig:
    """Create fallback configuration."""
    if fallback_chain is None:
        fallback_chain = [SolverType.LOCAL_BRAKET, SolverType.QISKIT, SolverType.NEAL, SolverType.CLASSICAL]
    else:
        # Convert string list to enum list
        fallback_chain = [SolverType(s) for s in fallback_chain]
    
    return FallbackConfig(
        enable_cloud_fallback=enable_cloud_fallback,
        enable_local_fallback=enable_local_fallback,
        fallback_chain=fallback_chain,
        max_fallback_depth=max_fallback_depth
    )
