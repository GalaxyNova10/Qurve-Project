from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import time

import numpy as np

from .bqm_builder import BQMBuildResult, build_portfolio_bqm
from .contracts import SolverRequest, SolverRunMetadata


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
    selected = int(np.sum(weights > 1e-6))
    budget_sum = float(np.sum(weights))
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
    cardinality_ok = selected == cardinality
    budget_ok = abs(budget_sum - 1.0) <= budget_tolerance
    sector_ok = len(violations) == 0
    return {
        "budget_satisfaction": budget_sum,
        "cardinality": selected,
        "cardinality_target": cardinality,
        "cardinality_ok": cardinality_ok,
        "sector_violations": violations,
        "sector_ok": sector_ok,
        "all_satisfied": budget_ok and cardinality_ok and sector_ok,
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
        sample[build.indicator_variables[i]] = int(weight > 1e-6)
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
            },
        },
        "constraint_verification": verify_constraints(
            weights,
            request.sectors,
            request.cardinality,
            request.max_sector_exposure,
        ),
    }
