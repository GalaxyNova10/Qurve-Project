"""QURVE AI Benchmark Certification Engine — v4 (Statistical Stability).

Priority 2: Strict feasibility certification thresholds.
Priority 8: Final scientific validation gate with manifold health.
"""

from typing import Dict, Any
from qubo_backend.optimization.contracts import OperationalCertification, ScientificCertification

# ── [HARD_NULL_IMMUNIZATION] (Phase 2) ──────────────────────────────
def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    if isinstance(value, (dict, list, tuple)):
        return default
    try:
        f = float(value)
        if f != f or f == float('inf') or f == float('-inf'):
            return default
        return f
    except (TypeError, ValueError):
        return default


# Feasibility certification thresholds (Priority 2)
_RESEARCH_GRADE_MIN = 0.25
_CERTIFIED_MIN = 0.50
_STRONG_MIN = 0.70


class BenchmarkCertifier:
    """Deterministic certification engine for QURVE AI benchmarks.
    Splits certification into Operational and Scientific axes.
    """

    def certify_operational(self, result: Dict[str, Any]) -> OperationalCertification:
        solve_time = result.get("solve_time_ms", 0)
        status = result.get("status")

        latency_ok = solve_time < 30000
        reliability_ok = status in ["success", "fallback"]
        stability_ok = not result.get("fallback_triggered", False)

        cert_status = "CERTIFIED"
        reason = None

        if not reliability_ok:
            cert_status = "FAILED"
            reason = "Execution failed or timed out"
        elif not latency_ok:
            cert_status = "DEGRADED"
            reason = "High latency threshold exceeded"
        elif not stability_ok:
            cert_status = "DEGRADED"
            reason = "Instability detected (fallback triggered)"

        return OperationalCertification(
            status=cert_status,
            latency_ok=latency_ok,
            reliability_ok=reliability_ok,
            stability_ok=stability_ok,
            reason=reason
        )

    def certify_scientific(self, result: Dict[str, Any]) -> ScientificCertification:
        feasible = result.get("feasible") or False
        opt_status = result.get("optimization_status") or ""
        repair_used = opt_status == "repaired"
        encoding_unstable = opt_status == "encoding_instability"
        collapse = opt_status == "sampling_collapse"
        manifold_collapse = opt_status == "collapsed_manifold"
        comparable = result.get("is_energy_comparable") or False

        # Priority 2: Feasibility ratio certification — NULL SAFE
        feas_ratio = _safe_float(result.get("feasible_ratio_raw", 0.0), 0.0)
        feas_above_research = feas_ratio >= _RESEARCH_GRADE_MIN
        feas_above_certified = feas_ratio >= _CERTIFIED_MIN
        feas_above_strong = feas_ratio >= _STRONG_MIN

        # Priority 8: Manifold health gate — NULL SAFE
        manifold_score = _safe_float(result.get("manifold_health_score", None), 0.0)
        manifold_ok = manifold_score >= 0.70

        # Priority 7: Benchmark blockers — NULL SAFE
        avg_card_delta = _safe_float(result.get("avg_cardinality_delta", 0.0), 0.0)
        card_delta_blocked = avg_card_delta > 1.0

        # Core integrity
        decode_ok = opt_status not in ("non_comparable", "encoding_instability", "collapsed_manifold")
        feasibility_ok = feasible
        approx_ratio = _safe_float(result.get("approximation_ratio", None), 1.0)
        approximation_ok = approx_ratio > 0.8
        comparability_ok = comparable

        cert_status = "CERTIFIED"
        reason = None

        # Hard failures first (Priority 7 blockers)
        if manifold_collapse:
            cert_status = "NON_COMPARABLE"
            reason = "Collapsed manifold -- no feasible samples found"
        elif encoding_unstable:
            cert_status = "NON_COMPARABLE"
            reason = "LOCAL encoding instability detected"
        elif collapse:
            cert_status = "NON_COMPARABLE"
            reason = "Sampling collapse -- manifold density too low"
        elif card_delta_blocked:
            cert_status = "NON_COMPARABLE"
            reason = f"avg_cardinality_delta={avg_card_delta:.2f} exceeds blocker threshold 1.0"
        elif not decode_ok or not comparability_ok:
            cert_status = "NON_COMPARABLE"
            reason = "Decode integrity or energy comparability failed"
        elif repair_used:
            cert_status = "NON_COMPARABLE"
            reason = "Repair applied -- scientifically non-comparable"
        elif not feasibility_ok:
            cert_status = "UX_GRADE"
            reason = "Infeasible portfolio; unsuitable for research"
        elif not feas_above_research:
            cert_status = "NON_COMPARABLE"
            reason = f"feasible_ratio_raw={feas_ratio:.4f} below research-grade minimum 0.25"
        elif not feas_above_certified:
            cert_status = "RESEARCH_GRADE"
            reason = f"feasible_ratio_raw={feas_ratio:.4f} below certified minimum 0.50"
        elif not feas_above_strong:
            cert_status = "CERTIFIED"
            reason = f"feasible_ratio_raw={feas_ratio:.4f} — certified but below strong convergence 0.70"
        else:
            cert_status = "STRONG_CONVERGENCE"
            reason = f"feasible_ratio_raw={feas_ratio:.4f} — strong convergence achieved"

        # Manifold health downgrade (Priority 8)
        raw_manifold = result.get("manifold_health_score", None)
        if raw_manifold is not None and not manifold_ok and cert_status in ("CERTIFIED", "STRONG_CONVERGENCE"):
            cert_status = "RESEARCH_GRADE"
            reason = f"manifold_health_score={manifold_score:.4f} below 0.70 threshold"

        return ScientificCertification(
            status=cert_status,
            feasibility_ok=feasibility_ok,
            approximation_ok=approximation_ok,
            decode_integrity_ok=decode_ok,
            comparability_ok=comparability_ok,
            reason=reason
        )


def certify_benchmark_result(result: Dict[str, Any]) -> Dict[str, Any]:
    certifier = BenchmarkCertifier()
    result["operational_certification"] = certifier.certify_operational(result).model_dump()
    result["scientific_certification"] = certifier.certify_scientific(result).model_dump()
    return result
