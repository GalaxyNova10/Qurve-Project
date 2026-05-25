from __future__ import annotations

import logging
from math import comb, log2

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.bqm_builder import BQMBuildResult

logger = logging.getLogger(__name__)

class FeasibilityGeometryError(RuntimeError):
    """Raised when the expected feasible volume is zero or topology is unsafe."""
    pass

def analyze_feasibility_geometry(request: SolverRequest, build_result: BQMBuildResult) -> dict:
    """
    Phase 1: Static Feasibility Geometry Analyzer.
    Analyzes the problem geometry before submission and aborts if it is physically impossible to solve.
    """
    n_assets = len(request.mu)
    k = request.cardinality

    # 1. Expected feasible manifold volume
    try:
        raw_volume = comb(n_assets, k)
    except ValueError:
        raw_volume = 0

    # Discount volume based on sector constraints overlapping
    # (A simple heuristic: heavily constrained sectors reduce valid combinations)
    sector_counts = {}
    for s in request.sectors:
        sector_counts[s] = sector_counts.get(s, 0) + 1
    
    # If the cardinality forces us to pick more assets from a sector than its cap allows:
    # Cap per sector = ceil(n_assets * max_sector_exposure) -> Actually it's allocation based,
    # but for K-hot, the max number of assets from one sector is roughly K * max_sector_exposure.
    max_assets_per_sector = max(1, int(k * request.max_sector_exposure))
    
    impossible_sectors = 0
    for s, count in sector_counts.items():
        if count > 0 and max_assets_per_sector == 0:
            impossible_sectors += 1

    feasible_volume = raw_volume if impossible_sectors == 0 else 0

    # 2. Penalty dominance ratio
    # If penalties are far too large compared to objective span, it's unsafe.
    P_card = build_result.penalty_scales.get("P_card", 0.0)
    objective_span = max(1e-9, build_result.objective_span)
    penalty_dominance_ratio = P_card / objective_span

    # 3. Topology entropy (rough approximation based on BQM density)
    n_vars = len(build_result.bqm.variables)
    max_edges = n_vars * (n_vars - 1) / 2
    density = len(build_result.bqm.quadratic) / max(1, max_edges)
    
    # Entropy peaks at density = 0.5
    p = min(max(density, 1e-9), 1.0 - 1e-9)
    topology_entropy = - (p * log2(p) + (1-p) * log2(1-p))

    # 4. Projected feasible basin width
    # In a QUBO, the basin width around a feasible state depends on the penalty gap.
    basin_width = P_card / objective_span

    logger.info(
        f"[CONSTRAINT_CURVATURE_AUDIT] "
        f"feasible_volume={feasible_volume} "
        f"penalty_dominance_ratio={penalty_dominance_ratio:.4f} "
        f"topology_entropy={topology_entropy:.4f} "
        f"projected_basin_width={basin_width:.4f} "
        f"density={density:.4f}"
    )

    if feasible_volume == 0 or raw_volume == 0:
        raise FeasibilityGeometryError(f"Feasible volume is 0. Impossible constraint geometry for K={k}, N={n_assets}")

    if penalty_dominance_ratio > 1e7:
        raise FeasibilityGeometryError(f"Penalty dominance ratio {penalty_dominance_ratio:.2e} > 1e7. Optimization landscape is flat.")

    if request.solver == "AWS_BRAKET_TN1" and (density >= 0.20 or len(build_result.bqm.quadratic) > 24):
        raise FeasibilityGeometryError(f"TN1 Topology Unsafe: density {density:.2f} >= 0.20 or edges > 24.")

    return {
        "feasible_volume": feasible_volume,
        "penalty_dominance_ratio": penalty_dominance_ratio,
        "topology_entropy": topology_entropy,
        "projected_basin_width": basin_width,
    }
