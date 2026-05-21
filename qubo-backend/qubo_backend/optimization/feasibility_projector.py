"""QURVE AI — Hard Feasibility Projector.

Post-decode projector that enforces cardinality constraints by retaining
only the top-K allocations. This is the safety net for QAOA states that
find low-energy solutions but violate sparsity/cardinality constraints.

Scientific basis: QAOA at p=1 frequently finds globally lower-energy states
that violate cardinality constraints because the penalty gap is finite.
The hard projector repairs these states post-decode without corrupting
the energy ranking — feasible states are ALWAYS preferred when available.
"""

import logging
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


def hard_cardinality_projector(
    weights: np.ndarray,
    K: int,
    tickers: Optional[list[str]] = None,
    renormalize: bool = True,
) -> tuple[np.ndarray, bool]:
    """If selected_assets > K, retain top-K allocations, zero remainder, renormalize.
    
    Args:
        weights: Portfolio weight vector (n_assets,)
        K: Target cardinality (number of active assets)
        tickers: Optional ticker labels for logging
        renormalize: If True, renormalize to budget=1.0 after projection
        
    Returns:
        (projected_weights, was_projected): Tuple of projected weights and
            boolean indicating if projection was applied.
    """
    weights = np.asarray(weights, dtype=float).copy()
    n_assets = len(weights)
    
    # Count active assets (weight > epsilon)
    active_mask = weights > 1e-6
    active_count = int(np.sum(active_mask))
    
    if active_count <= K:
        # No projection needed — already within cardinality constraint
        logger.info(
            f"[HARD_PROJECTOR_SKIP] active={active_count} target={K} "
            f"projection=NOT_NEEDED")
        return weights, False
    
    # ── Projection: retain top-K by weight magnitude ─────────────
    # Sort indices by weight descending
    sorted_indices = np.argsort(-weights)
    
    # Top-K indices (the ones we keep)
    top_k_indices = set(sorted_indices[:K].tolist())
    
    # Zero out everything not in top-K
    removed_assets = []
    removed_weights = []
    for i in range(n_assets):
        if i not in top_k_indices:
            if weights[i] > 1e-6:
                removed_assets.append(i)
                removed_weights.append(weights[i])
            weights[i] = 0.0
    
    # ── Renormalize to budget = 1.0 ──────────────────────────────
    weight_sum = float(np.sum(weights))
    if renormalize and weight_sum > 1e-9:
        weights = weights / weight_sum
    
    # ── Telemetry ────────────────────────────────────────────────
    post_active = int(np.sum(weights > 1e-6))
    post_sum = float(np.sum(weights))
    
    removed_labels = []
    if tickers:
        removed_labels = [tickers[i] for i in removed_assets if i < len(tickers)]
    
    logger.info(
        f"[HARD_PROJECTOR_APPLIED] "
        f"pre_active={active_count} target_K={K} post_active={post_active} "
        f"removed_count={len(removed_assets)} "
        f"removed_weight_total={sum(removed_weights):.4f} "
        f"post_budget={post_sum:.6f}")
    
    if removed_labels:
        logger.info(
            f"[PROJECTOR_CARDINALITY_FIX] "
            f"removed_assets={removed_labels} "
            f"removed_weights={[round(w, 4) for w in removed_weights]}")
    
    # Final feasibility check
    cardinality_ok = post_active == K
    budget_ok = abs(post_sum - 1.0) < 0.01
    
    logger.info(
        f"[POST_PROJECTOR_FEASIBILITY] "
        f"cardinality_ok={cardinality_ok} budget_ok={budget_ok} "
        f"cardinality={post_active}/{K} budget={post_sum:.6f}")
    
    return weights, True


def hard_budget_projector(
    weights: np.ndarray,
    target_budget: float = 1.0,
) -> np.ndarray:
    """Renormalize weights to target budget without changing selection.
    
    This is a softer projector that only fixes budget violations
    without touching cardinality.
    """
    weights = np.asarray(weights, dtype=float).copy()
    weight_sum = float(np.sum(weights))
    
    if weight_sum > 1e-9 and abs(weight_sum - target_budget) > 0.001:
        scale = target_budget / weight_sum
        weights *= scale
        logger.info(
            f"[BUDGET_PROJECTOR_APPLIED] "
            f"pre_sum={weight_sum:.6f} post_sum={float(np.sum(weights)):.6f} "
            f"scale={scale:.6f}")
    
    return weights
