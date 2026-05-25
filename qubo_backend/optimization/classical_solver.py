"""
Multi-Strategy Classical Solver for QUBO Portfolio Optimization.

Three strategies, ranked by sophistication:
  1. Greedy Heuristic  — deterministic, fast, always feasible
  2. Simulated Annealing — BQM-aware via neal, then repair to feasibility
  3. Genetic Algorithm  — evolutionary search over weight vectors (capped at 5s)

When strategy="auto", all viable strategies run and the best energy wins.
"""

import logging
import time
import random
from typing import Any

import numpy as np

from qubo_backend.optimization.base_solver import BasePortfolioSolver
from qubo_backend.optimization.contracts import SolverRequest, SolverRunMetadata
from qubo_backend.optimization.portfolio import (
    PortfolioSolution,
    greedy_feasible_weights,
    verify_constraints,
    encode_weights,
    bqm_energy,
)
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm

logger = logging.getLogger(__name__)

# Maximum wall-clock seconds for the GA before yielding best-so-far
_GA_TIME_LIMIT = 5.0


# Compatibility wrapper for benchmark.py (matches source backend API)
def solve_classical(
    request: SolverRequest,
    solver_name: str = "classical",
    strategy: str = "auto",
) -> PortfolioSolution:
    """Run classical optimization with the specified strategy."""
    solver = ClassicalSolver()
    return solver.solve(request, solver_name=solver_name, strategy=strategy)


class ClassicalSolver(BasePortfolioSolver):
    """
    Production-grade classical optimizer with three strategies.
    Acts as the ultimate safety net — must never crash.
    """

    def solve(self, request: SolverRequest, **kwargs: Any) -> PortfolioSolution:
        solver_name = kwargs.get("solver_name", "classical")
        fallback_reason = kwargs.get("fallback_reason", None)
        strategy = kwargs.get("strategy", "auto")

        started = time.perf_counter()
        build = build_portfolio_bqm(request)

        # Track (strategy_name, weights, energy, is_feasible)
        candidates: list[tuple[str, np.ndarray, float, bool]] = []

        # ── Strategy 1: Greedy Heuristic (always feasible) ──────────
        try:
            greedy_w = greedy_feasible_weights(request)
            greedy_sample = encode_weights(build, greedy_w)
            greedy_energy = bqm_energy(build, greedy_sample)
            candidates.append(("greedy", greedy_w, greedy_energy, True))
        except Exception as e:
            logger.warning(f"Greedy strategy failed: {e}")

        # ── Strategy 2: Simulated Annealing via neal ────────────────
        if strategy in ("auto", "sa", "simulated_annealing"):
            try:
                sa_w, sa_energy, sa_feasible = self._run_simulated_annealing(request, build)
                if sa_w is not None:
                    candidates.append(("simulated_annealing", sa_w, sa_energy, sa_feasible))
            except Exception as e:
                logger.warning(f"Simulated Annealing strategy failed: {e}")

        # ── Strategy 3: Genetic Algorithm ───────────────────────────
        if strategy in ("auto", "ga", "genetic"):
            try:
                ga_w, ga_energy, ga_feasible = self._run_genetic_algorithm(request, build)
                if ga_w is not None:
                    candidates.append(("genetic_algorithm", ga_w, ga_energy, ga_feasible))
            except Exception as e:
                logger.warning(f"Genetic Algorithm strategy failed: {e}")

        # ── Pick winner (feasibility-first, then lowest energy) ─────
        if not candidates:
            logger.error("All classical strategies failed. No feasible solution.")
            metadata = SolverRunMetadata(
                solver=solver_name,
                bqm_backend="internal_dimod_compatible",
                qubo_variables=len(build.variable_order),
                linear_terms=len(build.bqm.linear),
                quadratic_terms=len(build.bqm.quadratic),
                solve_time_ms=round((time.perf_counter() - started) * 1000, 3),
                reads=request.trajectories,
                time_limit_seconds=request.time_limit_seconds,
                energy=None,
                fallback_reason=fallback_reason,
                provider="local",
                backend_name="classical_failed",
                is_qpu=False,
                is_hybrid=False,
                strategy="failed",
                optimization_status="failed",
                execution_status="failed",
            )
            return PortfolioSolution(weights=np.zeros(len(request.mu)), energy=None, metadata=metadata)

        feasible = [(n, w, e, f) for n, w, e, f in candidates if f]
        if feasible:
            best_strategy, best_weights, best_energy, _ = min(feasible, key=lambda c: c[2])
        else:
            best_strategy, best_weights, best_energy, _ = min(candidates, key=lambda c: c[2])

        elapsed_ms = round((time.perf_counter() - started) * 1000, 3)

        logger.info(
            f"Classical solver chose '{best_strategy}' (energy={best_energy:.4f}) "
            f"from {len(candidates)} candidate(s) in {elapsed_ms:.1f}ms"
        )
        
        # Eliminate inf/nan propagation
        if best_energy is not None and not np.isfinite(best_energy):
            logger.error(f"Numerical instability: Classical solver energy {best_energy} is not finite.")
            best_energy = None
            best_strategy = "failed_numerical_instability"

        metadata = SolverRunMetadata(
            solver=solver_name,
            bqm_backend="internal_dimod_compatible",
            qubo_variables=len(build.variable_order),
            linear_terms=len(build.bqm.linear),
            quadratic_terms=len(build.bqm.quadratic),
            solve_time_ms=elapsed_ms,
            reads=request.trajectories,
            time_limit_seconds=request.time_limit_seconds,
            energy=best_energy,
            fallback_reason=fallback_reason,
            provider="local",
            backend_name=f"classical_{best_strategy}",
            is_qpu=False,
            is_hybrid=False,
            strategy=best_strategy,
            optimization_status="NUMERICAL_INSTABILITY" if best_energy is None else "decoded"
        )
        return PortfolioSolution(weights=best_weights, energy=best_energy, metadata=metadata)

    # ─────────────────────────────────────────────────────────────────
    # Strategy 2: Simulated Annealing (neal)
    # ─────────────────────────────────────────────────────────────────
    def _run_simulated_annealing(self, request, build):
        """
        Use neal.SimulatedAnnealingSampler on the full BQM, then decode
        and repair the resulting binary sample into a feasible portfolio.
        Returns (weights, energy, is_feasible).
        """
        try:
            import neal
        except ImportError:
            logger.info("neal not installed — skipping SA strategy")
            return None, float("inf"), False

        sampler = neal.SimulatedAnnealingSampler()
        num_reads = min(request.trajectories, 128)
        sampleset = sampler.sample(build.bqm.to_dimod(), num_reads=num_reads)

        best_sample = dict(sampleset.first.sample)
        best_raw_energy = float(sampleset.first.energy)

        # Decode binary sample → continuous weights
        weights = self._decode_sample_to_weights(request, build, best_sample)

        # Simple normalization
        if np.sum(weights) > 1e-6:
            weights = weights / np.sum(weights)

        check = verify_constraints(
            weights, request.sectors, request.cardinality,
            request.max_sector_exposure, sector_tolerance=1e-5
        )
        if check["all_satisfied"]:
            repaired_sample = encode_weights(build, weights)
            repaired_energy = bqm_energy(build, repaired_sample)
            return weights, repaired_energy, True
        else:
            return weights, best_raw_energy, False

    # ─────────────────────────────────────────────────────────────────
    # Strategy 3: Genetic Algorithm
    # ─────────────────────────────────────────────────────────────────
    def _run_genetic_algorithm(self, request, build):
        """
        Evolutionary search over weight vectors. Returns (weights, energy, is_feasible).
        """
        N = len(request.mu)
        mu = np.asarray(request.mu)
        sigma = np.asarray(request.sigma)
        K = request.cardinality
        pop_size = 40
        deadline = time.perf_counter() + _GA_TIME_LIMIT

        # Initialize population with random feasible portfolios
        population = []
        for _ in range(pop_size):
            try:
                individual = self._random_feasible_portfolio(request, N, K)
                population.append(individual)
            except Exception:
                continue

        if not population:
            logger.warning("[GA_FALLBACK] Empty population — falling back to greedy solution")
            w = greedy_feasible_weights(request)
            sample = encode_weights(build, w)
            return w, bqm_energy(build, sample), True

        def fitness(w):
            ret = float(w @ mu)
            vol = float(np.sqrt(max(1e-12, w @ sigma @ w)))
            return -(ret / vol) if vol > 1e-12 else float("inf")

        best_w = population[0].copy()
        best_fit = fitness(best_w)
        generation = 0

        while time.perf_counter() < deadline:
            generation += 1
            fits = [fitness(ind) for ind in population]
            gen_best_idx = int(np.argmin(fits))
            if fits[gen_best_idx] < best_fit:
                best_fit = fits[gen_best_idx]
                best_w = population[gen_best_idx].copy()

            new_pop = [best_w.copy()]
            while len(new_pop) < pop_size:
                p1 = self._tournament_select(population, fits)
                p2 = self._tournament_select(population, fits)
                child = np.where(np.random.random(N) < 0.5, p1, p2)
                if random.random() < 0.3:
                    idx = random.randint(0, N - 1)
                    child[idx] += np.random.normal(0, 0.02)
                    child = np.maximum(child, 0)
                if np.count_nonzero(child > 1e-6) > K:
                    threshold = np.sort(child)[-K]
                    child[child < threshold] = 0.0
                total = child.sum()
                if total > 1e-12:
                    child /= total
                if np.sum(child) > 1e-6:
                    child = child / np.sum(child)
                new_pop.append(child)
            population = new_pop

        check = verify_constraints(
            best_w, request.sectors, request.cardinality,
            request.max_sector_exposure, sector_tolerance=1e-5
        )
        sample = encode_weights(build, best_w)
        energy = bqm_energy(build, sample)
        return best_w, energy, check["all_satisfied"]

    # ─────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────
    @staticmethod
    def _decode_sample_to_weights(request, build, sample):
        """Decode a binary BQM sample dict into a continuous weight vector."""
        weights = np.zeros(len(request.mu), dtype=float)
        for i in range(len(request.mu)):
            w_val = 0.0
            if i < len(build.weight_variables):
                for bit, var in enumerate(build.weight_variables[i]):
                    w_val += sample.get(var, 0) * (2 ** bit) / build.denominator
            if i < len(build.indicator_variables) and sample.get(build.indicator_variables[i], 0) == 1:
                if i < len(build.weight_variables):
                    weights[i] = max(1e-6, w_val)
                else:
                    weights[i] = 1.0 / request.cardinality
            else:
                weights[i] = 0.0
        return weights

    @staticmethod
    def _random_feasible_portfolio(request, N, K):
        """Generate a random feasible portfolio weight vector."""
        indices = random.sample(range(N), min(K, N))
        w = np.zeros(N)
        raw = np.random.dirichlet(np.ones(len(indices)))
        for i, idx in enumerate(indices):
            w[idx] = raw[i]
        if np.sum(w) > 1e-6:
            w = w / np.sum(w)
        return w

    @staticmethod
    def _tournament_select(population, fits, k=3):
        """Tournament selection: pick the best of k random individuals."""
        indices = random.sample(range(len(population)), min(k, len(population)))
        best = min(indices, key=lambda i: fits[i])
        return population[best].copy()
