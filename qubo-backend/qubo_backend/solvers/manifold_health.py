"""Manifold Health Score — QURVE AI Statistical Stability Engine.

Priority 7: Single composite metric describing feasible manifold stability.

    manifold_health_score in [0, 1]

Combines:
  - feasible_ratio_raw       (40% weight)
  - cardinality deviation     (20% weight)
  - repair frequency          (15% weight)
  - energy variance           (15% weight)
  - normalization consistency (10% weight)

Interpretation:
  0.90+       = STABLE
  0.70 - 0.89 = ACCEPTABLE
  0.50 - 0.69 = DEGRADED
  < 0.50      = UNSTABLE
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


def _safe_float(v, default=0.0):
    try:
        if v is None:
            return default
        if isinstance(v, (dict, list, tuple)):
            return default
        x = float(v)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


# ── Tier thresholds ─────────────────────────────────────────────────
TIER_STABLE = 0.90
TIER_ACCEPTABLE = 0.70
TIER_DEGRADED = 0.50


@dataclass
class ManifoldHealthReport:
    """Full manifold health diagnostic."""
    # Composite score
    score: float = 0.0
    tier: str = "UNSTABLE"

    # Component scores (each in [0, 1])
    feasibility_score: float = 0.0
    cardinality_score: float = 0.0
    repair_score: float = 1.0
    energy_score: float = 0.0
    normalization_score: float = 0.0

    # Raw inputs
    feasible_ratio_raw: float = 0.0
    avg_cardinality_delta: float = 0.0
    repair_rate: float = 0.0
    energy_std: float = 0.0
    normalization_spread: float = 0.0
    n_solvers: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": round(self.score, 4),
            "tier": self.tier,
            "feasibility_score": round(self.feasibility_score, 4),
            "cardinality_score": round(self.cardinality_score, 4),
            "repair_score": round(self.repair_score, 4),
            "energy_score": round(self.energy_score, 4),
            "normalization_score": round(self.normalization_score, 4),
            "feasible_ratio_raw": round(self.feasible_ratio_raw, 4),
            "avg_cardinality_delta": round(self.avg_cardinality_delta, 4),
            "repair_rate": round(self.repair_rate, 4),
            "energy_std": round(self.energy_std, 6),
            "normalization_spread": round(self.normalization_spread, 6),
            "n_solvers": self.n_solvers,
        }


def compute_manifold_health(results: List[Dict[str, Any]]) -> ManifoldHealthReport:
    """Compute manifold health score from a set of benchmark results.

    Args:
        results: List of per-solver result dicts from run_benchmark().

    Returns:
        ManifoldHealthReport with composite score and component breakdown.
    """
    report = ManifoldHealthReport()

    # Filter to non-skipped, non-error results
    active = [r for r in results if r.get("status") in ("success", "fallback")]
    report.n_solvers = len(active)

    if not active:
        report.tier = "UNSTABLE"
        logger.warning("[MANIFOLD_HEALTH] No active solver results — score=0.0")
        return report

    # ── Component 1: Feasibility (40%) ──────────────────────────────
    feasible_ratios = [r.get("feasible_ratio_raw", 0.0) for r in active]
    avg_feasibility = sum(feasible_ratios) / len(feasible_ratios)
    report.feasible_ratio_raw = avg_feasibility
    report.feasibility_score = min(1.0, avg_feasibility / 0.7)  # 70% = perfect

    # ── Component 2: Cardinality (20%) ──────────────────────────────
    cardinality_deltas = [r.get("cardinality_deviation", r.get("avg_cardinality_delta", 0.0))
                          for r in active]
    avg_delta = sum(cardinality_deltas) / len(cardinality_deltas)
    report.avg_cardinality_delta = avg_delta
    report.cardinality_score = max(0.0, 1.0 - avg_delta / 3.0)  # delta=3 → 0

    # ── Component 3: Repair frequency (15%) ─────────────────────────
    repair_count = sum(1 for r in active
                       if r.get("optimization_status") == "repaired"
                       or r.get("repaired_sample_ratio", 0) > 0)
    report.repair_rate = repair_count / len(active)
    report.repair_score = 1.0 - report.repair_rate  # no repair = 1.0

    # ── Component 4: Energy variance (15%) ──────────────────────────
    energies = [r["energy"] for r in active
                if r.get("energy") is not None
                and r.get("scientific_comparability")
                and not math.isinf(r["energy"])
                and not math.isnan(r["energy"])]
    if len(energies) >= 2:
        import numpy as np
        e_std = float(np.std(energies))
        report.energy_std = e_std
        # Energy std < 0.01 is excellent, > 0.1 is poor
        report.energy_score = max(0.0, 1.0 - e_std / 0.1)
    elif len(energies) == 1:
        report.energy_score = 0.5  # insufficient data
    else:
        report.energy_score = 0.0  # no comparable energies

    # ── Component 5: Normalization consistency (10%) ─────────────────
    normed = [r["normalized_energy"] for r in active
              if r.get("normalized_energy") is not None]
    if len(normed) >= 2:
        spread = max(normed) - min(normed)
        report.normalization_spread = spread
        report.normalization_score = min(1.0, spread)  # spread=1 is full range = good
    elif len(normed) == 1:
        report.normalization_score = 0.5
    else:
        report.normalization_score = 0.0

    # ── Weighted composite ──────────────────────────────────────────
    report.score = (
        0.40 * report.feasibility_score +
        0.20 * report.cardinality_score +
        0.15 * report.repair_score +
        0.15 * report.energy_score +
        0.10 * report.normalization_score
    )
    report.score = max(0.0, min(1.0, report.score))

    # ── Tier assignment ─────────────────────────────────────────────
    if report.score >= TIER_STABLE:
        report.tier = "STABLE"
    elif report.score >= TIER_ACCEPTABLE:
        report.tier = "ACCEPTABLE"
    elif report.score >= TIER_DEGRADED:
        report.tier = "DEGRADED"
    else:
        report.tier = "UNSTABLE"

    logger.info(
        f"[MANIFOLD_HEALTH] score={report.score:.4f} tier={report.tier} "
        f"feas={report.feasibility_score:.2f} card={report.cardinality_score:.2f} "
        f"repair={report.repair_score:.2f} energy={report.energy_score:.2f} "
        f"norm={report.normalization_score:.2f}")

    return report
