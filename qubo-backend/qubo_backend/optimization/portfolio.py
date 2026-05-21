from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import time

import numpy as np

from .bqm_builder import BQMBuildResult, build_portfolio_bqm
from .contracts import SolverRequest, SolverRunMetadata


# ── [PHASE 4: Safe Reductions] ──────────────────────────────────────
def safe_mean(vals, default=0.0):
    """Safely calculate mean, avoiding empty slice warnings."""
    return float(np.mean(vals)) if len(vals) > 0 else float(default)

def safe_std(vals, default=0.0):
    """Safely calculate std, avoiding empty slice warnings."""
    return float(np.std(vals)) if len(vals) > 0 else float(default)

def safe_min(vals, default=0.0):
    """Safely calculate min, avoiding empty slice warnings."""
    return float(np.min(vals)) if len(vals) > 0 else float(default)

def safe_max(vals, default=0.0):
    """Safely calculate max, avoiding empty slice warnings."""
    return float(np.max(vals)) if len(vals) > 0 else float(default)


def ensure_numpy_weights(weights) -> np.ndarray:
    """Canonical coercion: guarantee np.ndarray before any validation or computation.
    
    Handles dict, list, scalar, or already-correct np.ndarray inputs.
    """
    if isinstance(weights, np.ndarray):
        return weights.astype(float)
    if isinstance(weights, dict):
        return np.array(list(weights.values()), dtype=float)
    if isinstance(weights, (list, tuple)):
        return np.array(weights, dtype=float)
    if weights is None:
        return np.array([], dtype=float)
    # Fallback: try to coerce
    try:
        return np.atleast_1d(np.asarray(weights, dtype=float))
    except Exception:
        return np.array([], dtype=float)


@dataclass(frozen=True)
class PortfolioSolution:
    weights: np.ndarray
    energy: float | None
    metadata: SolverRunMetadata


def compute_metrics(weights: np.ndarray, mu: np.ndarray, sigma: np.ndarray) -> dict[str, float]:
    expected_return = float(weights @ mu)
    variance = float(weights @ sigma @ weights)
    volatility = float(np.sqrt(max(variance, 0.0)))
    risk_free = 0.02
    sharpe = (expected_return - risk_free) / volatility if volatility > 0 else 0.0
    downside = float(np.sqrt(np.mean(np.minimum(mu - expected_return, 0.0) ** 2)))
    sortino = (expected_return - risk_free) / downside if downside > 0 else 0.0
    return {
        "expected_return": expected_return,
        "volatility": volatility,
        "sharpe_ratio": float(sharpe),
        "sortino_ratio": float(sortino),
        "variance": variance,
    }


def sector_allocation(weights: np.ndarray, sectors: list[str]) -> dict[str, float]:
    allocation: dict[str, float] = defaultdict(float)
    for weight, sector in zip(weights, sectors):
        if weight > 1e-12:
            allocation[sector] += float(weight)
    return dict(sorted(allocation.items(), key=lambda item: item[1], reverse=True))


def verify_constraints(
    weights: np.ndarray,
    sectors: list[str],
    cardinality: int,
    max_sector_exposure: float,
    budget_tolerance: float = 1e-6,
    sector_tolerance: float = 1e-6,
) -> dict:
    ALLOCATION_EPSILON = 1e-6
    
    # 1. Active assets > 0 check
    active_mask = weights > ALLOCATION_EPSILON
    selected = int(np.sum(active_mask))
    
    # 2. Normalized weights finite check
    weights_finite = np.all(np.isfinite(weights))
    
    # 3. Sum(weights) ~= 1 check
    budget_sum = float(np.sum(weights))
    budget_ok = abs(budget_sum - 1.0) <= budget_tolerance
    
    # 4. Sector constraints
    allocations = sector_allocation(weights, sectors)
    violations = []
    for sector, exposure in allocations.items():
        if exposure > max_sector_exposure + sector_tolerance:
            violations.append(
                {
                    "sector": sector,
                    "exposure": float(exposure),
                    "limit": float(max_sector_exposure),
                    "excess": float(exposure - max_sector_exposure),
                }
            )
    
    # 5. Cardinality satisfied check
    cardinality_ok = (selected == cardinality)
    
    # 6. Final feasibility synthesis
    sector_ok = len(violations) == 0
    all_satisfied = (
        weights_finite and 
        budget_ok and 
        cardinality_ok and 
        sector_ok and 
        selected > 0
    )
    
    return {
        "budget_satisfaction": budget_sum,
        "cardinality": selected,
        "cardinality_target": cardinality,
        "cardinality_ok": cardinality_ok,
        "sector_violations": violations,
        "sector_ok": sector_ok,
        "weights_finite": weights_finite,
        "non_empty": selected > 0,
        "all_satisfied": all_satisfied,
    }


def greedy_feasible_weights(request: SolverRequest) -> np.ndarray:
    """Construct a feasible cardinality/sector-capped portfolio for local fallback."""
    mu = np.asarray(request.mu, dtype=float)
    sigma = np.asarray(request.sigma, dtype=float)
    n_assets = len(mu)
    scores = mu - request.risk_tolerance * np.diag(sigma)
    equal_weight = 1.0 / request.cardinality
    per_sector_count_cap = max(1, int(np.floor((request.max_sector_exposure + 1e-12) / equal_weight)))

    selected: list[int] = []
    sector_counts: dict[str, int] = defaultdict(int)
    for idx in np.argsort(scores)[::-1]:
        sector = request.sectors[int(idx)]
        if sector_counts[sector] >= per_sector_count_cap:
            continue
        selected.append(int(idx))
        sector_counts[sector] += 1
        if len(selected) == request.cardinality:
            break

    if len(selected) < request.cardinality:
        for idx in np.argsort(scores)[::-1]:
            idx_int = int(idx)
            if idx_int not in selected:
                selected.append(idx_int)
                if len(selected) == request.cardinality:
                    break

    weights = np.zeros(n_assets, dtype=float)
    if not selected:
        return weights

    # Allocate by clipped positive score, then repair caps and exact budget.
    selected_scores = scores[selected]
    selected_scores = selected_scores - np.min(selected_scores) + 1e-6
    if float(np.sum(selected_scores)) <= 0:
        selected_scores = np.ones(len(selected), dtype=float)
    raw = selected_scores / np.sum(selected_scores)

    sector_remaining = {sector: request.max_sector_exposure for sector in set(request.sectors)}
    remaining_budget = 1.0
    remaining_slots = len(selected)
    for idx, proposed in sorted(zip(selected, raw), key=lambda item: scores[item[0]], reverse=True):
        sector = request.sectors[idx]
        min_reserve = max(0, remaining_slots - 1) * 1e-6
        cap = min(sector_remaining[sector], remaining_budget - min_reserve)
        weight = max(1e-6, min(float(proposed), cap))
        weights[idx] = weight
        sector_remaining[sector] -= weight
        remaining_budget -= weight
        remaining_slots -= 1

    weights = _repair_budget(weights, selected, request.sectors, request.max_sector_exposure)
    check = verify_constraints(weights, request.sectors, request.cardinality, request.max_sector_exposure, sector_tolerance=1e-5)
    if not check["all_satisfied"]:
        weights = np.zeros(n_assets, dtype=float)
        for idx in selected[: request.cardinality]:
            weights[idx] = 1.0 / request.cardinality
    return weights


def _repair_budget(weights: np.ndarray, selected: list[int], sectors: list[str], sector_cap: float) -> np.ndarray:
    for _ in range(1000):
        deficit = 1.0 - float(np.sum(weights))
        if abs(deficit) < 1e-10:
            break
        if deficit > 0:
            changed = False
            allocations = sector_allocation(weights, sectors)
            for idx in sorted(selected, key=lambda i: weights[i]):
                sector_room = sector_cap - allocations.get(sectors[idx], 0.0)
                add = min(deficit, max(0.0, sector_room))
                if add > 0:
                    weights[idx] += add
                    deficit -= add
                    changed = True
                    allocations[sectors[idx]] = allocations.get(sectors[idx], 0.0) + add
                if deficit <= 1e-10:
                    break
            if not changed:
                break
        else:
            surplus = -deficit
            for idx in sorted(selected, key=lambda i: weights[i], reverse=True):
                removable = max(0.0, weights[idx] - 1e-6)
                take = min(surplus, removable)
                weights[idx] -= take
                surplus -= take
                if surplus <= 1e-10:
                    break
    total = float(np.sum(weights))
    if total > 0 and abs(total - 1.0) > 1e-8:
        weights /= total
    return weights


def _repair_sector_violations(
    weights: np.ndarray,
    selected: list[int],
    sectors: list[str],
    sector_cap: float,
    max_rounds: int = 20,
) -> np.ndarray:
    """Minimally perturb weights to satisfy sector constraints.

    Strategy:
    1. Identify violating sectors
    2. Reduce weights in violating sectors proportionally
    3. Redistribute excess to non-violating sectors (by weight priority)
    4. Normalize to sum=1.0
    5. Preserve selected assets and objective structure

    Returns repaired weights with sector exposure <= sector_cap + tolerance.
    """
    weights = weights.copy().astype(float)
    tolerance = 1e-6

    for round_idx in range(max_rounds):
        allocations = sector_allocation(weights, sectors)
        violating = {
            s: exp for s, exp in allocations.items()
            if exp > sector_cap + tolerance
        }
        if not violating:
            break

        # Collect excess from violating sectors
        total_excess = 0.0
        reduction_plan: list[tuple[int, float]] = []

        for idx in selected:
            sector = sectors[idx]
            if sector in violating:
                # Calculate how much this asset should be reduced
                sector_total = allocations[sector]
                sector_excess = sector_total - sector_cap
                # Proportional reduction: each asset contributes proportionally
                if sector_total > 0:
                    share = weights[idx] / sector_total
                    reduction = share * sector_excess
                    if reduction > 0:
                        reduction_plan.append((idx, reduction))
                        total_excess += reduction

        # Apply reductions
        for idx, reduction in reduction_plan:
            weights[idx] = max(0.0, weights[idx] - reduction)

        # Redistribute excess to non-violating sectors
        if total_excess > 0:
            non_violating = [
                idx for idx in selected
                if sectors[idx] not in violating and weights[idx] > 0
            ]
            if non_violating:
                # Distribute proportionally to existing weights
                total_non_violating = sum(weights[idx] for idx in non_violating)
                if total_non_violating > 0:
                    for idx in non_violating:
                        share = weights[idx] / total_non_violating
                        addition = share * total_excess
                        # Check sector room before adding
                        sector = sectors[idx]
                        current_sector_exp = sum(
                            weights[i] for i in selected if sectors[i] == sector
                        )
                        room = sector_cap - current_sector_exp
                        weights[idx] += min(addition, max(0.0, room))

        # Normalize to sum=1.0
        total = float(np.sum(weights))
        if total > 0 and abs(total - 1.0) > 1e-10:
            weights /= total

    # Final normalization
    total = float(np.sum(weights))
    if total > 0:
        weights /= total

    return weights


def bqm_energy(build: BQMBuildResult, sample: dict[str, int]) -> float:
    energy = build.bqm.offset
    for var, bias in build.bqm.linear.items():
        energy += bias * sample.get(var, 0)
    for (left, right), bias in build.bqm.quadratic.items():
        energy += bias * sample.get(left, 0) * sample.get(right, 0)
    return float(energy)


def encode_weights(build: BQMBuildResult, weights: np.ndarray) -> dict[str, int]:
    sample: dict[str, int] = {}
    for i, weight in enumerate(weights):
        units = int(round(float(weight) * build.denominator))
        for bit, var in enumerate(build.weight_variables[i]):
            sample[var] = (units >> bit) & 1
        # Only include indicator variable if it exists in the BQM (K!=N case)
        y_var = build.indicator_variables[i]
        if y_var in build.bqm.variables:
            sample[y_var] = int(weight > 1e-6)
    for vars_for_sector in build.slack_variables.values():
        for var in vars_for_sector:
            sample[var] = 0
    return sample


def solve_locally(request: SolverRequest, solver_name: str = "classical_feasible", fallback_reason: str | None = None) -> PortfolioSolution:
    started = time.perf_counter()
    build = build_portfolio_bqm(request)
    weights = greedy_feasible_weights(request)
    sample = encode_weights(build, weights)
    metadata = SolverRunMetadata(
        solver=solver_name,
        bqm_backend="internal_dimod_compatible",
        qubo_variables=len(build.variable_order),
        linear_terms=len(build.bqm.linear),
        quadratic_terms=len(build.bqm.quadratic),
        solve_time_ms=round((time.perf_counter() - started) * 1000, 3),
        reads=request.trajectories,
        time_limit_seconds=request.time_limit_seconds,
        energy=bqm_energy(build, sample),
        fallback_reason=fallback_reason,
        provider="local",
        backend_name="greedy_feasible_repair",
        is_qpu=False,
        is_hybrid=False,
    )
    return PortfolioSolution(weights=weights, energy=metadata.energy, metadata=metadata)


def result_to_portfolio_response(request: SolverRequest, solution: PortfolioSolution) -> dict:
    mu = np.asarray(request.mu, dtype=float)
    sigma = np.asarray(request.sigma, dtype=float)
    weights = solution.weights
    portfolio = {
        ticker: {"weight": float(weight), "sector": sector}
        for ticker, sector, weight in zip(request.tickers, request.sectors, weights)
        if weight > 1e-6
    }
    return {
        "portfolio": portfolio,
        "metrics": compute_metrics(weights, mu, sigma),
        "sector_allocation": sector_allocation(weights, request.sectors),
        "parameters": {
            "k_bits": request.binary_bits,
            "cardinality": request.cardinality,
            "max_sector_exposure": request.max_sector_exposure,
            "risk_tolerance": request.risk_tolerance,
        },
        "solver_metadata": {
            "qubo_variables": solution.metadata.qubo_variables,
            "solve_time_ms": solution.metadata.solve_time_ms,
            "actual_solver_used": solution.metadata.actual_solver_used,
            "attempt": 1,
            "penalty_weights": {
                "solver": solution.metadata.solver,
                "bqm_backend": solution.metadata.bqm_backend,
                "linear_terms": solution.metadata.linear_terms,
                "quadratic_terms": solution.metadata.quadratic_terms,
                "reads": solution.metadata.reads,
                "energy": solution.metadata.energy,
                "fallback_reason": solution.metadata.fallback_reason,
                "quantum_backend": solution.metadata.quantum_backend,
                "chain_break_fraction": solution.metadata.chain_break_fraction,
                "provider": solution.metadata.provider,
                "backend_name": solution.metadata.backend_name,
                "is_qpu": solution.metadata.is_qpu,
                "is_hybrid": solution.metadata.is_hybrid,
                "time_limit_seconds": solution.metadata.time_limit_seconds,
                "qiskit_max_assets": solution.metadata.qiskit_max_assets,
                "qiskit_max_binary_bits": solution.metadata.qiskit_max_binary_bits,
                "eligibility_reason": solution.metadata.eligibility_reason,
                "execution_origin": solution.metadata.execution_origin,
                "fallback_triggered": solution.metadata.fallback_triggered,
                "fallback_chain": getattr(solution.metadata, "fallback_chain", []),
                "task_arn": solution.metadata.task_arn,
                "device_arn": solution.metadata.device_arn,
                "execution_mode": solution.metadata.execution_mode,
            },
        },
        "constraint_verification": verify_constraints(
            weights,
            request.sectors,
            request.cardinality,
            request.max_sector_exposure,
        ),
    }
