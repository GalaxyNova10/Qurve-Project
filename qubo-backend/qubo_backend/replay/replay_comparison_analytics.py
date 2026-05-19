"""
Qurve AI - Replay Comparison Analytics
Causal integrity preservation in replay divergence analysis.

Principles:
✅ Causal lineage preservation
✅ Execution ancestry tracking
✅ Fallback chain integrity
✅ Governance decision causality
✅ Non-inferential divergence scoring
✅ Traceability maintenance
"""

import asyncio
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .replay_schemas import (
    ReplayComparisonSchema,
    ReplayTimelineEventSchema,
    DivergenceTypeSchema
)

logger = logging.getLogger(__name__)


@dataclass
class CausalLineage:
    """Causal lineage information for event tracking."""
    correlation_id: str
    parent_correlation_id: Optional[str]
    benchmark_session_id: Optional[str]
    execution_lineage: List[str]
    fallback_ancestry: List[str]
    governance_decision_ancestry: List[str]
    telemetry_lineage: List[str]
    unknown_causes: List[str] = field(default_factory=list)


@dataclass
class DivergenceAnalysis:
    """Divergence analysis with causal integrity."""
    divergence_type: DivergenceTypeSchema
    divergence_score: float
    causal_lineage: CausalLineage
    original_cause: Optional[str] = None
    replay_cause: Optional[str] = None
    lineage_preserved: bool = True
    unknown_causality: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ComparisonConfig:
    """Comparison configuration."""
    enable_causal_analysis: bool = True
    enable_lineage_preservation: bool = True
    divergence_threshold_ms: float = 100.0
    max_lineage_depth: int = 10
    unknown_cause_handling: str = "mark_unknown"  # "mark_unknown" or "infer"


class ReplayComparisonAnalytics:
    """
    Production-grade replay comparison analytics.
    
    Features:
    - Causal integrity preservation
    - Execution lineage tracking
    - Fallback chain integrity
    - Governance decision causality
    - Non-inferential divergence scoring
    - Complete traceability
    """
    
    def __init__(self, config: ComparisonConfig):
        self.config = config
        
        # Comparison state
        self._comparisons: Dict[str, ReplayComparisonSchema] = {}
        self._lineage_cache: Dict[str, CausalLineage] = {}
        
        logger.info("Replay comparison analytics initialized", 
                  causal_analysis=config.enable_causal_analysis,
                  lineage_preservation=config.enable_lineage_preservation)
    
    async def compare_executions(self, 
                             original_session_id: str,
                             replay_session_id: str,
                             original_timeline: List[ReplayTimelineEventSchema],
                             replay_timeline: List[ReplayTimelineEventSchema],
                             original_lineage: CausalLineage,
                             replay_lineage: CausalLineage) -> ReplayComparisonSchema:
        """
        Compare original and replayed executions with causal integrity.
        
        Args:
            original_session_id: Original execution session ID
            replay_session_id: Replay session ID
            original_timeline: Original execution timeline
            replay_timeline: Replayed execution timeline
            original_lineage: Original execution lineage
            replay_lineage: Replayed execution lineage
            
        Returns:
            Comparison analysis with causal integrity preserved
        """
        try:
            comparison_id = f"comparison_{original_session_id}_{replay_session_id}_{int(time.time())}"
            
            # Perform causal integrity analysis
            divergence_analyses = await self._analyze_causal_divergence(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            
            # Calculate overall divergence score
            overall_divergence_score = await self._calculate_overall_divergence_score(divergence_analyses)
            
            # Create comparison schema
            comparison = ReplayComparisonSchema(
                comparison_id=comparison_id,
                original_session_id=original_session_id,
                replay_session_id=replay_session_id,
                timestamp=datetime.now(),
                timing_drift_ms=await self._calculate_timing_drift(original_timeline, replay_timeline),
                solver_divergence=await self._analyze_solver_divergence(original_timeline, replay_timeline),
                fallback_divergence=await self._analyze_fallback_divergence(original_timeline, replay_timeline),
                telemetry_divergence=await self._analyze_telemetry_divergence(original_timeline, replay_timeline),
                governance_divergence=await self._analyze_governance_divergence(original_timeline, replay_timeline),
                overall_divergence_score=overall_divergence_score,
                divergence_breakdown={
                    "causal_analyses": [
                        {
                            "type": analysis.divergence_type.value,
                            "score": analysis.divergence_score,
                            "lineage_preserved": analysis.lineage_preserved,
                            "unknown_causality": analysis.unknown_causality
                        }
                        for analysis in divergence_analyses
                    ]
                },
                metadata={
                    "causal_integrity": self._assess_causal_integrity(divergence_analyses),
                    "lineage_preservation": self._assess_lineage_preservation(original_lineage, replay_lineage),
                    "comparison_config": {
                        "causal_analysis": self.config.enable_causal_analysis,
                        "lineage_preservation": self.config.enable_lineage_preservation
                    }
                }
            )
            
            # Store comparison
            self._comparisons[comparison_id] = comparison
            
            logger.info("Replay comparison completed", 
                       comparison_id=comparison_id,
                       overall_divergence_score=overall_divergence_score,
                       causal_integrity=comparison.metadata["causal_integrity"])
            
            return comparison
            
        except Exception as e:
            logger.error("Failed to compare executions", 
                        original_session_id=original_session_id,
                        replay_session_id=replay_session_id,
                        error=str(e))
            raise
    
    async def _analyze_causal_divergence(self, 
                                       original_timeline: List[ReplayTimelineEventSchema],
                                       replay_timeline: List[ReplayTimelineEventSchema],
                                       original_lineage: CausalLineage,
                                       replay_lineage: CausalLineage) -> List[DivergenceAnalysis]:
        """
        Analyze causal divergence between timelines.
        
        Preserves causal integrity without inference.
        """
        try:
            analyses = []
            
            # Analyze timing divergence with causal context
            timing_divergence = await self._analyze_timing_divergence_with_causality(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            analyses.append(timing_divergence)
            
            # Analyze solver divergence with lineage preservation
            solver_divergence = await self._analyze_solver_divergence_with_lineage(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            analyses.append(solver_divergence)
            
            # Analyze fallback divergence with ancestry preservation
            fallback_divergence = await self._analyze_fallback_divergence_with_ancestry(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            analyses.append(fallback_divergence)
            
            # Analyze governance divergence with decision causality
            governance_divergence = await self._analyze_governance_divergence_with_causality(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            analyses.append(governance_divergence)
            
            # Analyze telemetry divergence with lineage preservation
            telemetry_divergence = await self._analyze_telemetry_divergence_with_lineage(
                original_timeline, replay_timeline, original_lineage, replay_lineage
            )
            analyses.append(telemetry_divergence)
            
            logger.debug("Causal divergence analysis completed", 
                        analyses_count=len(analyses),
                        lineage_preserved=all(a.lineage_preserved for a in analyses))
            
            return analyses
            
        except Exception as e:
            logger.error("Failed to analyze causal divergence", error=str(e))
            return []
    
    async def _analyze_timing_divergence_with_causality(self, 
                                                      original_timeline: List[ReplayTimelineEventSchema],
                                                      replay_timeline: List[ReplayTimelineEventSchema],
                                                      original_lineage: CausalLineage,
                                                      replay_lineage: CausalLineage) -> DivergenceAnalysis:
        """
        Analyze timing divergence with causal context.
        
        Preserves causal lineage without inference.
        """
        try:
            # Create event maps by correlation for causal analysis
            original_events = {event.correlation_id: event for event in original_timeline}
            replay_events = {event.correlation_id: event for event in replay_timeline}
            
            # Find common correlation IDs for causal comparison
            common_correlations = set(original_events.keys()) & set(replay_events.keys())
            
            timing_differences = []
            for correlation_id in common_correlations:
                original_event = original_events[correlation_id]
                replay_event = replay_events[correlation_id]
                
                if original_event.timing_ms is not None and replay_event.timing_ms is not None:
                    diff = abs(original_event.timing_ms - replay_event.timing_ms)
                    if diff > self.config.diverggence_threshold_ms:
                        timing_differences.append({
                            "correlation_id": correlation_id,
                            "timing_diff_ms": diff,
                            "original_timing_ms": original_event.timing_ms,
                            "replay_timing_ms": replay_event.timing_ms,
                            "causal_lineage": original_lineage.execution_lineage
                        })
            
            # Calculate divergence score
            divergence_score = 0.0
            if timing_differences:
                total_diff = sum(d["timing_diff_ms"] for d in timing_differences)
                divergence_score = min(1.0, total_diff / (len(timing_differences) * 1000))
            
            # Assess lineage preservation
            lineage_preserved = self._assess_timing_lineage_preservation(
                original_lineage, replay_lineage, timing_differences
            )
            
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.TIMING,
                divergence_score=divergence_score,
                causal_lineage=replay_lineage,
                original_cause="original_execution_timing",
                replay_cause="replay_reconstruction_timing",
                lineage_preserved=lineage_preserved,
                unknown_causality=False,
                metadata={
                    "timing_differences": timing_differences,
                    "common_correlations": len(common_correlations),
                    "threshold_ms": self.config.divergence_threshold_ms
                }
            )
            
        except Exception as e:
            logger.error("Failed to analyze timing divergence with causality", error=str(e))
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.TIMING,
                divergence_score=1.0,
                causal_lineage=replay_lineage,
                unknown_causality=True,
                metadata={"error": str(e)}
            )
    
    async def _analyze_solver_divergence_with_lineage(self, 
                                                    original_timeline: List[ReplayTimelineEventSchema],
                                                    replay_timeline: List[ReplayTimelineEventSchema],
                                                    original_lineage: CausalLineage,
                                                    replay_lineage: CausalLineage) -> DivergenceAnalysis:
        """
        Analyze solver divergence with lineage preservation.
        
        Preserves solver execution ancestry.
        """
        try:
            # Extract solver events
            original_solver_events = [e for e in original_timeline if e.event_type == "solver_execution"]
            replay_solver_events = [e for e in replay_timeline if e.event_type == "solver_execution"]
            
            # Compare solver sequences with lineage context
            divergence_score = 0.0
            solver_differences = []
            
            # Check if solver sequences match with lineage preservation
            if len(original_solver_events) != len(replay_solver_events):
                divergence_score = 1.0
                solver_differences.append({
                    "type": "sequence_length_mismatch",
                    "original_count": len(original_solver_events),
                    "replay_count": len(replay_solver_events),
                    "lineage_preserved": False
                })
            else:
                for i, (orig_event, replay_event) in enumerate(zip(original_solver_events, replay_solver_events)):
                    if orig_event.solver != replay_event.solver:
                        divergence_score += 0.2  # Partial divergence per mismatch
                        solver_differences.append({
                            "position": i,
                            "original_solver": orig_event.solver,
                            "replay_solver": replay_event.solver,
                            "lineage_preserved": orig_event.solver == replay_event.solver
                        })
            
            # Assess lineage preservation
            lineage_preserved = self._assess_solver_lineage_preservation(
                original_lineage, replay_lineage, solver_differences
            )
            
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.SOLVER,
                divergence_score=min(1.0, divergence_score),
                causal_lineage=replay_lineage,
                original_cause="original_solver_execution",
                replay_cause="replay_solver_reconstruction",
                lineage_preserved=lineage_preserved,
                unknown_causality=False,
                metadata={
                    "solver_differences": solver_differences,
                    "original_solver_sequence": [e.solver for e in original_solver_events],
                    "replay_solver_sequence": [e.solver for e in replay_solver_events]
                }
            )
            
        except Exception as e:
            logger.error("Failed to analyze solver divergence with lineage", error=str(e))
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.SOLVER,
                divergence_score=1.0,
                causal_lineage=replay_lineage,
                unknown_causality=True,
                metadata={"error": str(e)}
            )
    
    async def _analyze_fallback_divergence_with_ancestry(self, 
                                                      original_timeline: List[ReplayTimelineEventSchema],
                                                      replay_timeline: List[ReplayTimelineEventSchema],
                                                      original_lineage: CausalLineage,
                                                      replay_lineage: CausalLineage) -> DivergenceAnalysis:
        """
        Analyze fallback divergence with ancestry preservation.
        
        Preserves explicit fallback chain ancestry.
        """
        try:
            # Extract fallback events
            original_fallback_events = [e for e in original_timeline if e.event_type == "fallback"]
            replay_fallback_events = [e for e in replay_timeline if e.event_type == "fallback"]
            
            # Compare fallback chains with ancestry preservation
            divergence_score = 0.0
            fallback_differences = []
            
            # Check if fallback chains match with ancestry preservation
            if len(original_fallback_events) != len(replay_fallback_events):
                divergence_score = 1.0
                fallback_differences.append({
                    "type": "fallback_chain_length_mismatch",
                    "original_count": len(original_fallback_events),
                    "replay_count": len(replay_fallback_events),
                    "ancestry_preserved": False
                })
            else:
                for i, (orig_event, replay_event) in enumerate(zip(original_fallback_events, replay_fallback_events)):
                    if (orig_event.solver != replay_event.solver or 
                        orig_event.to_solver != replay_event.to_solver or
                        orig_event.fallback_reason != replay_event.fallback_reason):
                        divergence_score += 0.25  # Partial divergence per mismatch
                        fallback_differences.append({
                            "position": i,
                            "original_transition": f"{orig_event.solver}→{orig_event.to_solver}",
                            "replay_transition": f"{replay_event.solver}→{replay_event.to_solver}",
                            "ancestry_preserved": (orig_event.solver == replay_event.solver and 
                                                    orig_event.to_solver == replay_event.to_solver)
                        })
            
            # Assess ancestry preservation
            ancestry_preserved = self._assess_fallback_ancestry_preservation(
                original_lineage, replay_lineage, fallback_differences
            )
            
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.FALLBACK,
                divergence_score=min(1.0, divergence_score),
                causal_lineage=replay_lineage,
                original_cause="original_fallback_chain",
                replay_cause="replay_fallback_reconstruction",
                lineage_preserved=ancestry_preserved,
                unknown_causality=False,
                metadata={
                    "fallback_differences": fallback_differences,
                    "original_fallback_chain": [
                        f"{e.solver}→{e.to_solver}" for e in original_fallback_events
                    ],
                    "replay_fallback_chain": [
                        f"{e.solver}→{e.to_solver}" for e in replay_fallback_events
                    ]
                }
            )
            
        except Exception as e:
            logger.error("Failed to analyze fallback divergence with ancestry", error=str(e))
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.FALLBACK,
                divergence_score=1.0,
                causal_lineage=replay_lineage,
                unknown_causality=True,
                metadata={"error": str(e)}
            )
    
    async def _analyze_governance_divergence_with_causality(self, 
                                                        original_timeline: List[ReplayTimelineEventSchema],
                                                        replay_timeline: List[ReplayTimelineEventSchema],
                                                        original_lineage: CausalLineage,
                                                        replay_lineage: CausalLineage) -> DivergenceAnalysis:
        """
        Analyze governance divergence with decision causality.
        
        Preserves governance decision causality links.
        """
        try:
            # Extract governance events
            original_governance_events = [e for e in original_timeline if e.event_type == "governance_decision"]
            replay_governance_events = [e for e in replay_timeline if e.event_type == "governance_decision"]
            
            # Compare governance decisions with causality preservation
            divergence_score = 0.0
            governance_differences = []
            
            # Check if governance decisions match with causality preservation
            if len(original_governance_events) != len(replay_governance_events):
                divergence_score = 1.0
                governance_differences.append({
                    "type": "governance_decision_count_mismatch",
                    "original_count": len(original_governance_events),
                    "replay_count": len(replay_governance_events),
                    "causality_preserved": False
                })
            else:
                for i, (orig_event, replay_event) in enumerate(zip(original_governance_events, replay_governance_events)):
                    if (orig_event.governance_decision != replay_event.governance_decision or
                        orig_event.cloud_decision != replay_event.cloud_decision):
                        divergence_score += 0.3  # Partial divergence per mismatch
                        governance_differences.append({
                            "position": i,
                            "original_decision": orig_event.governance_decision,
                            "replay_decision": replay_event.governance_decision,
                            "causality_preserved": (orig_event.governance_decision == replay_event.governance_decision)
                        })
            
            # Assess causality preservation
            causality_preserved = self._assess_governance_causality_preservation(
                original_lineage, replay_lineage, governance_differences
            )
            
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.GOVERNANCE,
                divergence_score=min(1.0, divergence_score),
                causal_lineage=replay_lineage,
                original_cause="original_governance_decisions",
                replay_cause="replay_governance_reconstruction",
                lineage_preserved=causality_preserved,
                unknown_causality=False,
                metadata={
                    "governance_differences": governance_differences,
                    "original_governance_sequence": [e.governance_decision for e in original_governance_events],
                    "replay_governance_sequence": [e.governance_decision for e in replay_governance_events]
                }
            )
            
        except Exception as e:
            logger.error("Failed to analyze governance divergence with causality", error=str(e))
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.GOVERNANCE,
                divergence_score=1.0,
                causal_lineage=replay_lineage,
                unknown_causality=True,
                metadata={"error": str(e)}
            )
    
    async def _analyze_telemetry_divergence_with_lineage(self, 
                                                      original_timeline: List[ReplayTimelineEventSchema],
                                                      replay_timeline: List[ReplayTimelineEventSchema],
                                                      original_lineage: CausalLineage,
                                                      replay_lineage: CausalLineage) -> DivergenceAnalysis:
        """
        Analyze telemetry divergence with lineage preservation.
        
        Preserves telemetry trace lineage.
        """
        try:
            # Extract telemetry events
            original_telemetry_events = [e for e in original_timeline if e.event_type == "telemetry"]
            replay_telemetry_events = [e for e in replay_timeline if e.event_type == "telemetry"]
            
            # Compare telemetry traces with lineage preservation
            divergence_score = 0.0
            telemetry_differences = []
            
            # Check if telemetry traces match with lineage preservation
            if len(original_telemetry_events) != len(replay_telemetry_events):
                divergence_score = 1.0
                telemetry_differences.append({
                    "type": "telemetry_trace_count_mismatch",
                    "original_count": len(original_telemetry_events),
                    "replay_count": len(replay_telemetry_events),
                    "lineage_preserved": False
                })
            else:
                for i, (orig_event, replay_event) in enumerate(zip(original_telemetry_events, replay_telemetry_events)):
                    # Compare telemetry metadata with lineage preservation
                    orig_metadata = orig_event.metadata
                    replay_metadata = replay_event.metadata
                    
                    if orig_metadata != replay_metadata:
                        divergence_score += 0.1  # Partial divergence per mismatch
                        telemetry_differences.append({
                            "position": i,
                            "correlation_id": orig_event.correlation_id,
                            "lineage_preserved": orig_metadata == replay_metadata
                        })
            
            # Assess lineage preservation
            lineage_preserved = self._assess_telemetry_lineage_preservation(
                original_lineage, replay_lineage, telemetry_differences
            )
            
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.TELEMETRY,
                divergence_score=min(1.0, divergence_score),
                causal_lineage=replay_lineage,
                original_cause="original_telemetry_traces",
                replay_cause="replay_telemetry_reconstruction",
                lineage_preserved=lineage_preserved,
                unknown_causality=False,
                metadata={
                    "telemetry_differences": telemetry_differences,
                    "original_telemetry_count": len(original_telemetry_events),
                    "replay_telemetry_count": len(replay_telemetry_events)
                }
            )
            
        except Exception as e:
            logger.error("Failed to analyze telemetry divergence with lineage", error=str(e))
            return DivergenceAnalysis(
                divergence_type=DivergenceTypeSchema.TELEMETRY,
                divergence_score=1.0,
                causal_lineage=replay_lineage,
                unknown_causality=True,
                metadata={"error": str(e)}
            )
    
    async def _calculate_overall_divergence_score(self, analyses: List[DivergenceAnalysis]) -> float:
        """Calculate overall divergence score from individual analyses."""
        if not analyses:
            return 1.0
        
        # Weight different divergence types
        weights = {
            DivergenceTypeSchema.TIMING: 0.2,
            DivergenceTypeSchema.SOLVER: 0.3,
            DivergenceTypeSchema.FALLBACK: 0.2,
            DivergenceTypeSchema.GOVERNANCE: 0.2,
            DivergenceTypeSchema.TELEMETRY: 0.1
        }
        
        weighted_score = 0.0
        total_weight = 0.0
        
        for analysis in analyses:
            weight = weights.get(analysis.divergence_type, 0.1)
            weighted_score += analysis.divergence_score * weight
            total_weight += weight
        
        return weighted_score / total_weight if total_weight > 0 else 1.0
    
    async def _calculate_timing_drift(self, 
                                  original_timeline: List[ReplayTimelineEventSchema],
                                  replay_timeline: List[ReplayTimelineEventSchema]) -> Optional[float]:
        """Calculate timing drift between timelines."""
        try:
            # Create timing maps
            original_timing = {event.correlation_id: event.timing_ms for event in original_timeline if event.timing_ms is not None}
            replay_timing = {event.correlation_id: event.timing_ms for event in replay_timeline if event.timing_ms is not None}
            
            # Find common correlations
            common_correlations = set(original_timing.keys()) & set(replay_timing.keys())
            
            if not common_correlations:
                return None
            
            # Calculate average timing difference
            total_diff = 0.0
            count = 0
            
            for correlation_id in common_correlations:
                diff = abs(original_timing[correlation_id] - replay_timing[correlation_id])
                total_diff += diff
                count += 1
            
            return total_diff / count if count > 0 else None
            
        except Exception as e:
            logger.error("Failed to calculate timing drift", error=str(e))
            return None
    
    async def _analyze_solver_divergence(self, 
                                       original_timeline: List[ReplayTimelineEventSchema],
                                       replay_timeline: List[ReplayTimelineEventSchema]) -> Optional[Dict[str, Any]]:
        """Analyze solver divergence between timelines."""
        try:
            # Extract solver sequences
            original_solvers = [e.solver for e in original_timeline if e.event_type == "solver_execution"]
            replay_solvers = [e.solver for e in replay_timeline if e.event_type == "solver_execution"]
            
            if not original_solvers or not replay_solvers:
                return None
            
            # Compare solver sequences
            matches = len(original_solvers) == len(replay_solvers)
            sequence_match = original_solvers == replay_solvers
            
            return {
                "solver_sequence_match": sequence_match,
                "original_solvers": original_solvers,
                "replay_solvers": replay_solvers,
                "divergence_detected": not sequence_match
            }
            
        except Exception as e:
            logger.error("Failed to analyze solver divergence", error=str(e))
            return None
    
    async def _analyze_fallback_divergence(self, 
                                         original_timeline: List[ReplayTimelineEventSchema],
                                         replay_timeline: List[ReplayTimelineEventSchema]) -> Optional[Dict[str, Any]]:
        """Analyze fallback divergence between timelines."""
        try:
            # Extract fallback chains
            original_fallbacks = []
            replay_fallbacks = []
            
            for event in original_timeline:
                if event.event_type == "fallback" and hasattr(event, 'to_solver'):
                    original_fallbacks.append(f"{event.solver}→{event.to_solver}")
            
            for event in replay_timeline:
                if event.event_type == "fallback" and hasattr(event, 'to_solver'):
                    replay_fallbacks.append(f"{event.solver}→{event.to_solver}")
            
            if not original_fallbacks or not replay_fallbacks:
                return None
            
            # Compare fallback chains
            chain_match = original_fallbacks == replay_fallbacks
            
            return {
                "fallback_chain_match": chain_match,
                "original_fallback_chain": original_fallbacks,
                "replay_fallback_chain": replay_fallbacks,
                "divergence_detected": not chain_match
            }
            
        except Exception as e:
            logger.error("Failed to analyze fallback divergence", error=str(e))
            return None
    
    async def _analyze_telemetry_divergence(self, 
                                           original_timeline: List[ReplayTimelineEventSchema],
                                           replay_timeline: List[ReplayTimelineEventSchema]) -> Optional[Dict[str, Any]]:
        """Analyze telemetry divergence between timelines."""
        try:
            # Extract telemetry events
            original_telemetry = [e.metadata for e in original_timeline if e.event_type == "telemetry"]
            replay_telemetry = [e.metadata for e in replay_timeline if e.event_type == "telemetry"]
            
            if not original_telemetry or not replay_telemetry:
                return None
            
            # Compare telemetry traces
            trace_match = original_telemetry == replay_telemetry
            
            return {
                "telemetry_trace_match": trace_match,
                "original_telemetry_count": len(original_telemetry),
                "replay_telemetry_count": len(replay_telemetry),
                "divergence_detected": not trace_match
            }
            
        except Exception as e:
            logger.error("Failed to analyze telemetry divergence", error=str(e))
            return None
    
    async def _analyze_governance_divergence(self, 
                                             original_timeline: List[ReplayTimelineEventSchema],
                                             replay_timeline: List[ReplayTimelineEventSchema]) -> Optional[Dict[str, Any]]:
        """Analyze governance divergence between timelines."""
        try:
            # Extract governance decisions
            original_governance = [e.governance_decision for e in original_timeline if e.event_type == "governance_decision"]
            replay_governance = [e.governance_decision for e in replay_timeline if e.event_type == "governance_decision"]
            
            if not original_governance or not replay_governance:
                return None
            
            # Compare governance sequences
            sequence_match = original_governance == replay_governance
            
            return {
                "governance_sequence_match": sequence_match,
                "original_governance_sequence": original_governance,
                "replay_governance_sequence": replay_governance,
                "divergence_detected": not sequence_match
            }
            
        except Exception as e:
            logger.error("Failed to analyze governance divergence", error=str(e))
            return None
    
    def _assess_timing_lineage_preservation(self, 
                                         original_lineage: CausalLineage,
                                         replay_lineage: CausalLineage,
                                         timing_differences: List[Dict[str, Any]]) -> bool:
        """Assess timing lineage preservation."""
        # Check if execution lineage is preserved
        lineage_preserved = original_lineage.execution_lineage == replay_lineage.execution_lineage
        
        # Check if timing differences affect causality
        causal_impact = any(diff["timing_diff_ms"] > self.config.divergence_threshold_ms for diff in timing_differences)
        
        return lineage_preserved and not causal_impact
    
    def _assess_solver_lineage_preservation(self, 
                                          original_lineage: CausalLineage,
                                          replay_lineage: CausalLineage,
                                          solver_differences: List[Dict[str, Any]]) -> bool:
        """Assess solver lineage preservation."""
        # Check if execution lineage is preserved
        lineage_preserved = original_lineage.execution_lineage == replay_lineage.execution_lineage
        
        # Check if solver differences affect causality
        causal_impact = any(diff["lineage_preserved"] is False for diff in solver_differences)
        
        return lineage_preserved and not causal_impact
    
    def _assess_fallback_ancestry_preservation(self, 
                                              original_lineage: CausalLineage,
                                              replay_lineage: CausalLineage,
                                              fallback_differences: List[Dict[str, Any]]) -> bool:
        """Assess fallback ancestry preservation."""
        # Check if fallback ancestry is preserved
        ancestry_preserved = original_lineage.fallback_ancestry == replay_lineage.fallback_ancestry
        
        # Check if fallback differences affect causality
        causal_impact = any(diff["ancestry_preserved"] is False for diff in fallback_differences)
        
        return ancestry_preserved and not causal_impact
    
    def _assess_governance_causality_preservation(self, 
                                                    original_lineage: CausalLineage,
                                                    replay_lineage: CausalLineage,
                                                    governance_differences: List[Dict[str, Any]]) -> bool:
        """Assess governance causality preservation."""
        # Check if governance decision ancestry is preserved
        causality_preserved = original_lineage.governance_decision_ancestry == replay_lineage.governance_decision_ancestry
        
        # Check if governance differences affect causality
        causal_impact = any(diff["causality_preserved"] is False for diff in governance_differences)
        
        return causality_preserved and not causal_impact
    
    def _assess_telemetry_lineage_preservation(self, 
                                               original_lineage: CausalLineage,
                                               replay_lineage: CausalLineage,
                                               telemetry_differences: List[Dict[str, Any]]) -> bool:
        """Assess telemetry lineage preservation."""
        # Check if telemetry lineage is preserved
        lineage_preserved = original_lineage.telemetry_lineage == replay_lineage.telemetry_lineage
        
        # Check if telemetry differences affect causality
        causal_impact = any(diff["lineage_preserved"] is False for diff in telemetry_differences)
        
        return lineage_preserved and not causal_impact
    
    def _assess_causal_integrity(self, analyses: List[DivergenceAnalysis]) -> Dict[str, Any]:
        """Assess overall causal integrity."""
        if not analyses:
            return {"integrity_preserved": False, "reason": "no_analyses"}
        
        lineage_preserved = all(analysis.lineage_preserved for analysis in analyses)
        unknown_causality = any(analysis.unknown_causality for analysis in analyses)
        
        return {
            "integrity_preserved": lineage_preserved and not unknown_causality,
            "lineage_preserved": lineage_preserved,
            "unknown_causality": unknown_causality,
            "divergence_types": [analysis.divergence_type.value for analysis in analyses],
            "overall_divergence_score": sum(analysis.divergence_score for analysis in analyses) / len(analyses)
        }
    
    def _assess_lineage_preservation(self, 
                                    original_lineage: CausalLineage,
                                    replay_lineage: CausalLineage) -> Dict[str, Any]:
        """Assess lineage preservation between original and replay."""
        return {
            "execution_lineage_preserved": original_lineage.execution_lineage == replay_lineage.execution_lineage,
            "fallback_ancestry_preserved": original_lineage.fallback_ancestry == replay_lineage.fallback_ancestry,
            "governance_decision_ancestry_preserved": original_lineage.governance_decision_ancestry == replay_lineage.governance_decision_ancestry,
            "telemetry_lineage_preserved": original_lineage.telemetry_lineage == replay_lineage.telemetry_lineage,
            "unknown_causes_preserved": original_lineage.unknown_causes == replay_lineage.unknown_causes
        }
    
    async def get_comparison(self, comparison_id: str) -> Optional[ReplayComparisonSchema]:
        """Get comparison by ID."""
        return self._comparisons.get(comparison_id)
    
    async def get_comparisons(self, limit: int = 100) -> List[ReplayComparisonSchema]:
        """Get recent comparisons."""
        comparisons = list(self._comparisons.values())
        comparisons.sort(key=lambda c: c.timestamp, reverse=True)
        return comparisons[:limit]
    
    def get_comparison_statistics(self) -> Dict[str, Any]:
        """Get comparison analytics statistics."""
        if not self._comparisons:
            return {
                "total_comparisons": 0,
                "average_divergence_score": 0.0,
                "divergence_distribution": {},
                "causal_integrity_rate": 0.0
            }
        
        total_comparisons = len(self._comparisons)
        divergence_scores = [c.overall_divergence_score for c in self._comparisons.values() if c.overall_divergence_score is not None]
        
        # Calculate divergence distribution
        divergence_distribution = {}
        for comparison in self._comparisons.values():
            if comparison.divergence_breakdown:
                for analysis in comparison.divergence_breakdown.get("causal_analyses", []):
                    divergence_type = analysis["type"]
                    divergence_distribution[divergence_type] = divergence_distribution.get(divergence_type, 0) + 1
        
        # Calculate causal integrity rate
        causal_integrity_count = sum(
            1 for c in self._comparisons.values() 
            if c.metadata and c.metadata.get("causal_integrity", {}).get("integrity_preserved", False)
        )
        causal_integrity_rate = (causal_integrity_count / total_comparisons * 100) if total_comparisons > 0 else 0.0
        
        return {
            "total_comparisons": total_comparisons,
            "average_divergence_score": sum(divergence_scores) / len(divergence_scores) if divergence_scores else 0.0,
            "divergence_distribution": divergence_distribution,
            "causal_integrity_rate": causal_integrity_rate,
            "config": {
                "causal_analysis": self.config.enable_causal_analysis,
                "lineage_preservation": self.config.enable_lineage_preservation
            }
        }


# Global comparison analytics instance
_replay_comparison_analytics: Optional[ReplayComparisonAnalytics] = None


def get_replay_comparison_analytics() -> ReplayComparisonAnalytics:
    """Get global replay comparison analytics instance."""
    global _replay_comparison_analytics
    if _replay_comparison_analytics is None:
        _replay_comparison_analytics = ReplayComparisonAnalytics(ComparisonConfig())
    return _replay_comparison_analytics


def create_comparison_config(
    enable_causal_analysis: bool = True,
    enable_lineage_preservation: bool = True,
    divergence_threshold_ms: float = 100.0,
    max_lineage_depth: int = 10,
    unknown_cause_handling: str = "mark_unknown"
) -> ComparisonConfig:
    """Create comparison configuration."""
    return ComparisonConfig(
        enable_causal_analysis=enable_causal_analysis,
        enable_lineage_preservation=enable_lineage_preservation,
        divergence_threshold_ms=divergence_threshold_ms,
        max_lineage_depth=max_lineage_depth,
        unknown_cause_handling=unknown_cause_handling
    )
