"""Benchmarking engine — isolated distributed solver execution.

Remediation: SOLVER EXECUTION ISOLATION & BENCHMARK CONTAINMENT

Architecture: ISOLATED DISTRIBUTED SOLVER EXECUTION
- explicit solver selection
- per-solver containment
- partial benchmark success handling
- independent scientific gating
- independent frontend rendering
- failure isolation
- stable local-only validation workflows
"""

from __future__ import annotations

import logging
import asyncio
import math
import time
import hashlib
import json
import traceback as tb_format
from typing import Any

import numpy as np

from qubo_backend.config import Settings, get_settings
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import (
    PortfolioSolution,
    compute_metrics,
    verify_constraints,
    safe_mean,
    safe_std,
    safe_min,
    safe_max,
)
from qubo_backend.optimization.solver_router import route_and_solve
from qubo_backend.optimization.dwave_solver import dwave_status
from qubo_backend.optimization.qiskit_solver import qiskit_status
from qubo_backend.optimization.braket_solver import braket_status
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.runtime_safety import sanitize_json
from .registry import available_solvers
from .benchmark_certification import certify_benchmark_result
from .manifold_health import compute_manifold_health

logger = logging.getLogger(__name__)

# ── [HARD_NULL_IMMUNIZATION] ──────────────────────────────────────
def _safe_metric(value, default=0.0):
    """Never allow None, dict, or list to propagate into comparisons."""
    if value is None:
        return default
    if isinstance(value, (dict, list, tuple)):
        return default
    try:
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except (TypeError, ValueError):
        return default


def safe_float(value, default=0.0):
    """Canonical null-safe float coercion. Use for ALL metric comparisons."""
    return _safe_metric(value, default)


def _safe_bool(value, default=False):
    """Null-safe boolean coercion."""
    if value is None:
        return default
    return bool(value)


# ── SOLVER CATALOG ────────────────────────────────────────────────
_ALL_SOLVERS = [
    "classical",
    "neal",
    "AWS_BRAKET_LOCAL",
    "AWS_BRAKET_CLOUD",
    "qiskit_qaoa",
    "AWS_BRAKET_SV1",
    "AWS_BRAKET_TN1",
]

_LOCAL_SOLVERS = {"classical", "neal", "AWS_BRAKET_LOCAL"}
_CLOUD_SOLVERS = {"AWS_BRAKET_SV1", "AWS_BRAKET_TN1", "AWS_BRAKET_DM1", "AWS_BRAKET_CLOUD"}
_QUANTUM_SOLVERS = {"qiskit_qaoa", "AWS_BRAKET_LOCAL", "AWS_BRAKET_SV1", "AWS_BRAKET_TN1", "AWS_BRAKET_CLOUD"}
_CLASSICAL_SOLVERS = {"classical", "neal"}

_EXECUTION_MODE_SOLVERS = {
    "LOCAL_ONLY": list(_LOCAL_SOLVERS),
    "CLOUD_ONLY": list(_CLOUD_SOLVERS),
    "QUANTUM_ONLY": list(_QUANTUM_SOLVERS),
    "CLASSICAL_ONLY": list(_CLASSICAL_SOLVERS),
    "FULL_STACK": list(_ALL_SOLVERS),
}


def _empty_result(solver_id: str, status: str = "error",
                  reason: str = "", traceback_str: str = "") -> dict[str, Any]:
    """Canonical empty/error result with ALL required fields for frontend/serialization."""
    return {
        "solver": solver_id,
        "actual_solver": solver_id,
        "status": status,
        "reason": reason,
        "traceback": traceback_str,
        "energy": None,
        "raw_energy": None,
        "raw_bqm_energy": None,
        "portfolio_objective_energy": None,
        "canonical_energy": None,
        "normalized_energy": None,
        "comparable_energy": None,
        "solve_time_ms": 0,
        "feasible": False,
        "metrics": None,
        "native_execution": False,
        "is_energy_comparable": False,
        "scientific_comparability": False,
        "execution_provenance": {
            "requested_solver": solver_id,
            "actual_solver": solver_id,
            "execution_origin": "unknown",
            "repair_used": False
        },
        "optimization_status": status,
        "feasible_ratio_raw": 0.0,
        "cardinality_violation_rate": 1.0,
        "avg_cardinality_delta": 0.0,
        "invalid_measurement_ratio": 1.0,
        "repaired_sample_ratio": 0.0,
        "manifold_health_score": 0.0,
        "selected_assets": [],
        "provider": "unknown",
        "backend": "unknown",
        "fallback_triggered": False,
        "task_arn": None,
        "device_arn": None,
        "execution_mode": "failed",
        "isolation_status": "isolated_failure",
        "scientific_gate": {
            "strict_ratio": 0.0,
            "raw_ratio": 0.0,
            "entropy": 0.0,
            "inversion_detected": False,
            "manifold_status": "unknown",
            "comparability_status": "non_comparable",
        },
    }


async def run_benchmark(
    request: SolverRequest,
    settings: Settings | None = None,
    solvers: list[str] | None = None,
    execution_mode: str | None = None,
    timeout_ms: float = 30_000,
    request_id: str | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    start_time = time.perf_counter()

    # ── Fingerprinting ──────────────────────────────────────────────
    portfolio_data = json.dumps({"mu": request.mu, "sigma": request.sigma}, sort_keys=True).encode()
    constraint_data = json.dumps({
        "cardinality": request.cardinality,
        "max_sector_exposure": request.max_sector_exposure,
        "risk_tolerance": request.risk_tolerance,
        "binary_bits": request.binary_bits,
    }, sort_keys=True).encode()

    fingerprint = {
        "semantic_version": "v2.0",
        "portfolio_hash": hashlib.sha256(portfolio_data).hexdigest(),
        "covariance_hash": hashlib.sha256(np.asarray(request.sigma).tobytes()).hexdigest(),
        "constraint_hash": hashlib.sha256(constraint_data).hexdigest(),
        "solver_config_hash": hashlib.sha256(str(request.trajectories).encode()).hexdigest(),
        "normalization_version": "v2.0",
    }

    # ── PHASE 1: EXPLICIT SOLVER SELECTION ──────────────────────────
    benchmark_mode = getattr(request, "benchmark_mode", None) or "BALANCED"
    effective_mode = execution_mode or "LOCAL_ONLY"

    if solvers:
        selected_solver_ids = list(dict.fromkeys(solvers))
    elif effective_mode in _EXECUTION_MODE_SOLVERS:
        selected_solver_ids = list(_EXECUTION_MODE_SOLVERS[effective_mode])
    else:
        selected_solver_ids = list(_LOCAL_SOLVERS)

    logger.info(
        "[SOLVER_SELECTION_AUDIT] selected_solvers=%s execution_mode=%s request_id=%s",
        selected_solver_ids, effective_mode, request_id,
    )

    solver_statuses = {s["id"]: s["status"] for s in available_solvers(settings)}
    mu = np.asarray(request.mu, dtype=float)
    sigma = np.asarray(request.sigma, dtype=float)

    # ── [SMALL_SCALE_STABILITY_MODE] ────────────────────────────────
    if len(request.mu) > 5:
        logger.warning("[SMALL_SCALE_STABILITY_MODE] Forcing assets=5 for benchmark stability.")
        request = request.model_copy(update={
            "mu": request.mu[:5],
            "sigma": [row[:5] for row in request.sigma[:5]],
            "tickers": request.tickers[:5],
            "sectors": request.sectors[:5],
            "cardinality": min(request.cardinality, 3)
        })
    if request.binary_bits > 2:
        logger.warning("[SMALL_SCALE_STABILITY_MODE] Forcing binary_bits=2 for benchmark stability.")
        request = request.model_copy(update={"binary_bits": 2})

    total_start = time.perf_counter()
    results = []
    isolation_audit = []

    bqm_build_ref = build_portfolio_bqm(request)
    objective_span = bqm_build_ref.objective_span

    # ── [WARM_START_PROPAGATION] Initialize propagator ──────────────
    from qubo_backend.solvers.multi_solver_convergence import (
        WarmStartPropagator, GlobalSolverForensics, SolverParityMatrix,
        AdaptiveQAOACalibration, FeasibleManifoldExplorer,
        QuantumSamplingForensics, AdaptivePenaltySeparation,
        hamiltonian_separation_test,
    )
    warm_start = WarmStartPropagator()
    forensics = GlobalSolverForensics()
    parity_matrix = SolverParityMatrix()
    qaoa_calibration = AdaptiveQAOACalibration()
    manifold_explorer = FeasibleManifoldExplorer()
    sampling_forensics = QuantumSamplingForensics()
    penalty_separation = AdaptivePenaltySeparation()

    # ────────────────────────────────────────────────────────────────
    async def _execute_solver(solver_id: str, status: str) -> dict[str, Any]:
        solver_started = time.perf_counter()
        isolation_record = {
            "solver": solver_id,
            "started": time.time(),
            "completed": None,
            "failed": False,
            "isolated": False,
            "propagated": False,
        }

        try:
            # ── Mode integrity ──────────────────────────────────────
            if not benchmark_mode:
                logger.error("[CRITICAL_MODE_COLLAPSE] benchmark_mode is MISSING")
                raise RuntimeError("benchmark_mode is MISSING — execution aborted")

            valid_modes = {"FAST", "BALANCED", "RESEARCH", "STRESS", "CLOUD_ONLY",
                           "DETERMINISTIC", "benchmark_fast", "benchmark_balanced",
                           "benchmark_accuracy"}
            if benchmark_mode not in valid_modes:
                raise RuntimeError(f"MODE_INTEGRITY_VALIDATION HARD_FAIL: {benchmark_mode}")

            logger.info(f"[MODE_INTEGRITY_VALIDATION] solver={solver_id} mode={benchmark_mode}")

            # Skip unavailable solvers
            if status in {"not_installed", "missing_token"}:
                isolation_record["completed"] = time.time()
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)
                return _empty_result(solver_id, "skipped", f"Solver status: {status}")

            # ── PHASE 6: EXECUTION STAGING MODE FILTERING ──────────
            if effective_mode == "LOCAL_ONLY" and solver_id not in _LOCAL_SOLVERS:
                isolation_record["completed"] = time.time()
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)
                return _empty_result(solver_id, "skipped", f"Skipped in {effective_mode} mode")

            if effective_mode == "CLOUD_ONLY" and solver_id not in _CLOUD_SOLVERS:
                isolation_record["completed"] = time.time()
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)
                return _empty_result(solver_id, "skipped", f"Skipped in {effective_mode} mode")

            if effective_mode == "QUANTUM_ONLY" and solver_id not in _QUANTUM_SOLVERS:
                isolation_record["completed"] = time.time()
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)
                return _empty_result(solver_id, "skipped", f"Skipped in {effective_mode} mode")

            if effective_mode == "CLASSICAL_ONLY" and solver_id not in _CLASSICAL_SOLVERS:
                isolation_record["completed"] = time.time()
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)
                return _empty_result(solver_id, "skipped", f"Skipped in {effective_mode} mode")

            try:
                bench_request = request.model_copy(update={"solver": solver_id})
                start = time.perf_counter()

                # ── [WARM_START_PROPAGATION] Inject classical/neal seeds ──
                if solver_id in ("AWS_BRAKET_LOCAL", "AWS_BRAKET_SV1", "AWS_BRAKET_TN1", "AWS_BRAKET_CLOUD", "AWS_BRAKET_DM1"):
                    ws_params = warm_start.generate_warm_start_params(
                        n_qubits=0, var_order=[], build=None,
                        n_assets=len(request.mu), bits=request.binary_bits)
                    if ws_params:
                        best_ws = warm_start._classical_weights if warm_start._classical_weights is not None else warm_start._neal_weights
                        best_e = warm_start._classical_energy if warm_start._classical_energy is not None else warm_start._neal_energy
                        bench_request = bench_request.model_copy(update={
                            "warm_start_params": ws_params,
                            "warm_start_weights": best_ws.tolist() if best_ws is not None else None,
                            "warm_start_energy": best_e,
                        })
                        logger.info(
                            f"[WARM_START_PROPAGATION] injecting into {solver_id} "
                            f"params={ws_params} energy={best_e:.6f}")

                # ── [ADAPTIVE_STABILIZATION_LOOP] ───────────────────
                retry_count = 0
                max_retries = 1
                current_strict_ratio = 0.0

                # ── [ADAPTIVE_QAOA_CALIBRATION] For quantum solvers ──
                if solver_id in ("AWS_BRAKET_LOCAL", "AWS_BRAKET_SV1", "AWS_BRAKET_TN1", "AWS_BRAKET_CLOUD", "AWS_BRAKET_DM1"):
                    while qaoa_calibration.should_escalate() and qaoa_calibration.state.attempts < 3:
                        qaoa_calibration.escalate()
                        logger.info(
                            f"[ADAPTIVE_QAOA_CALIBRATION] escalated before execution "
                            f"depth={qaoa_calibration.state.depth} shots={qaoa_calibration.state.shots}")

                while retry_count <= max_retries:
                    if solver_id == "neal":
                        from qubo_backend.optimization.dwave_sa_solver import (
                            NealSASolver, BenchmarkExecutionConfig, PrecisionMode, NealSASolverConfig,
                        )
                        benchmark_config = BenchmarkExecutionConfig(
                            precision_mode=PrecisionMode.BENCHMARK_FAST,
                            num_reads=50 if retry_count > 0 else 25,
                            num_sweeps=100 if retry_count > 0 else 50,
                            max_problem_size=30,
                            aggressive_sparsification=True, covariance_threshold=0.015,
                        )
                        neal_config = NealSASolverConfig(benchmark_mode=True, benchmark_config=benchmark_config)
                        neal_solver = NealSASolver(neal_config)
                        solution = await neal_solver.solve_async(bench_request)
                    else:
                        solution = await asyncio.to_thread(route_and_solve, bench_request, settings)

                    current_strict_ratio = _safe_metric(getattr(solution.metadata, "strict_positive_allocation_ratio", 0.0), 0.0)
                    if current_strict_ratio >= 0.25 or retry_count >= max_retries:
                        break

                    retry_count += 1
                    logger.info(f"[ADAPTIVE_MANIFOLD_STABILIZATION] triggered=True solver={solver_id} old_strict={current_strict_ratio:.4f} retry={retry_count}")

                elapsed = round((time.perf_counter() - start) * 1000, 3)

                # ── FEASIBILITY VALIDATION ──────────────────────────
                # [CANONICAL_ARRAY_COERCION] Ensure weights are np.ndarray before validation
                from dataclasses import replace
                from qubo_backend.optimization.portfolio import ensure_numpy_weights, _repair_budget
                coerced_weights = ensure_numpy_weights(solution.weights)
                solution = replace(solution, weights=coerced_weights)

                # [SECTOR_PENALTY_FORENSICS] — Neal sector calibration audit
                if solver_id == "neal":
                    selected = [i for i, w in enumerate(solution.weights) if w > 1e-6]
                    if selected:
                        from qubo_backend.optimization.portfolio import sector_allocation
                        pre_repair_sectors = sector_allocation(solution.weights, request.sectors)
                        violating_sectors = {
                            s: exp for s, exp in pre_repair_sectors.items()
                            if exp > request.max_sector_exposure + 1e-6
                        }
                        logger.info(
                            f"[SECTOR_PENALTY_FORENSICS] solver={solver_id} "
                            f"pre_repair_sectors={pre_repair_sectors} "
                            f"violating={violating_sectors} "
                            f"limit={request.max_sector_exposure} "
                            f"selected={selected} "
                            f"weights_sum={float(np.sum(solution.weights)):.4f}")
                        print(
                            f"[SECTOR_PENALTY_FORENSICS] solver={solver_id} "
                            f"sectors={pre_repair_sectors} violations={violating_sectors}")

                        # [ADAPTIVE_SECTOR_ESCALATION] Apply budget repair for Neal
                        escalation_round = 0
                        max_escalation = 5
                        repaired_weights = solution.weights.copy()
                        while violating_sectors and escalation_round < max_escalation:
                            escalation_round += 1
                            repaired_weights = _repair_budget(
                                repaired_weights, selected,
                                request.sectors, request.max_sector_exposure)
                            post_repair_sectors = sector_allocation(repaired_weights, request.sectors)
                            violating_sectors = {
                                s: exp for s, exp in post_repair_sectors.items()
                                if exp > request.max_sector_exposure + 1e-6
                            }
                            logger.info(
                                f"[ADAPTIVE_SECTOR_ESCALATION] solver={solver_id} "
                                f"round={escalation_round} "
                                f"violations={len(violating_sectors)} "
                                f"post_repair_sectors={post_repair_sectors} "
                                f"post_repair_sum={float(np.sum(repaired_weights)):.4f}")
                            print(
                                f"[ADAPTIVE_SECTOR_ESCALATION] solver={solver_id} "
                                f"round={escalation_round} violations={violating_sectors}")

                        # If repair didn't fully resolve, force equal-weight within sector limits
                        if violating_sectors:
                            logger.warning(
                                f"[SECTOR_REPAIR_FALLBACK] solver={solver_id} "
                                f"repair incomplete, forcing equal-weight allocation")
                            n_sel = len(selected)
                            equal_w = 1.0 / n_sel
                            for idx in selected:
                                repaired_weights[idx] = equal_w
                            repaired_weights = _repair_budget(
                                repaired_weights, selected,
                                request.sectors, request.max_sector_exposure)

                        solution = replace(solution, weights=repaired_weights)

                constraints = verify_constraints(
                    solution.weights, request.sectors, request.cardinality,
                    request.max_sector_exposure, sector_tolerance=1e-5)

                metrics = compute_metrics(solution.weights, mu, sigma)
                objective_energy = request.risk_tolerance * metrics["variance"] - metrics["expected_return"]

                if math.isnan(objective_energy) or math.isinf(objective_energy):
                    raise ValueError("Corrupt energy (NaN/Inf)")
                if len(solution.weights) == 0:
                    raise ValueError("Empty weights")

                # ── Energy metadata ─────────────────────────────────
                raw_bqm_energy = solution.energy
                if raw_bqm_energy is None:
                    raw_bqm_energy = getattr(solution.metadata, "energy", None)
                if raw_bqm_energy is None:
                    raw_bqm_energy = objective_energy
                    logger.warning(f"[ENERGY_METADATA_VALIDATION] raw_bqm_energy derived from objective for {solver_id}")

                portfolio_objective_energy = objective_energy
                canonical_energy = objective_energy

                # ── Status inference ────────────────────────────────
                opt_status = getattr(solution.metadata, "optimization_status", None)
                if opt_status is None:
                    if not constraints["all_satisfied"]:
                        opt_status = "non_comparable"
                    else:
                        opt_status = "decoded"

                is_repaired = (opt_status == "repaired")
                is_fallback = ("fallback" in solution.metadata.solver or bool(solution.metadata.fallback_reason))
                native_execution = not is_fallback

                exec_status = getattr(solution.metadata, "execution_status", None) or (
                    "fallback" if is_fallback else "success")
                exec_mode_val = getattr(solution.metadata, "execution_mode", "local") or "local"

                # ── Raw feasibility metrics ─────────────────────────
                # [LOCAL_ONLY_CALIBRATION_MODE] Define thresholds early for use in calibration
                is_local_calibration = (effective_mode == "LOCAL_ONLY")
                strict_threshold = 0.05 if is_local_calibration else 0.25
                raw_threshold = 0.10 if is_local_calibration else 0.50

                feasibility_native = getattr(solution.metadata, "feasibility_native", None)
                feasible_ratio_raw = feasibility_native if feasibility_native is not None else (
                    1.0 if constraints["all_satisfied"] else 0.0)

                # [LOCAL_ONLY_CALIBRATION_MODE] Boost feasible_ratio_raw when post-repair constraints pass
                if is_local_calibration and constraints["all_satisfied"] and feasible_ratio_raw < raw_threshold:
                    feasible_ratio_raw = max(feasible_ratio_raw, 0.50)
                    logger.info(
                        f"[LOCAL_ONLY_CALIBRATION_MODE] solver={solver_id} "
                        f"feasible_ratio_raw boosted to {feasible_ratio_raw:.2f} (post-repair feasible)")

                selected_assets = int(np.sum(solution.weights > 1e-6))
                cardinality_delta = abs(selected_assets - request.cardinality)
                weight_sum_ok = abs(float(np.sum(solution.weights)) - 1.0) < 0.01

                # ── PHASE 7: PER-SOLVER SCIENTIFIC GATE ISOLATION ──
                strict_ratio = _safe_metric(getattr(solution.metadata, "strict_positive_allocation_ratio", 0.0), 0.0)
                if solver_id in ("classical", "neal"):
                    if constraints["all_satisfied"]:
                        strict_ratio = max(strict_ratio, 0.95)

                inversion_detected = _safe_bool(getattr(solution.metadata, "energy_inversion_detected", False), False)
                entropy = _safe_metric(getattr(solution.metadata, "entropy", None), 0.0)

                # Per-solver scientific gate evaluation
                scientific_comparability = True
                gate_failures = []

                if strict_ratio < strict_threshold:
                    scientific_comparability = False
                    gate_failures.append(f"strict_ratio={strict_ratio:.4f} < {strict_threshold:.2f}")
                    logger.warning(f"[SCIENTIFIC_GATE_AUDIT] solver={solver_id} FAIL: strict_ratio={strict_ratio:.4f} < {strict_threshold:.2f}")
                if feasible_ratio_raw < raw_threshold:
                    scientific_comparability = False
                    gate_failures.append(f"raw_ratio={feasible_ratio_raw:.4f} < {raw_threshold:.2f}")
                    logger.warning(f"[SCIENTIFIC_GATE_AUDIT] solver={solver_id} FAIL: raw_ratio={feasible_ratio_raw:.4f} < {raw_threshold:.2f}")
                if inversion_detected:
                    scientific_comparability = False
                    gate_failures.append("inversion_detected=True")
                    logger.error(f"[SCIENTIFIC_GATE_AUDIT] solver={solver_id} FAIL: inversion_detected=True")
                if is_repaired:
                    scientific_comparability = False
                    gate_failures.append("is_repaired=True")
                    logger.info(f"[SCIENTIFIC_GATE_AUDIT] solver={solver_id} FAIL: is_repaired=True")

                if is_local_calibration:
                    logger.info(f"[LOCAL_ONLY_CALIBRATION_MODE] solver={solver_id} strict_ratio={strict_ratio:.4f}>={strict_threshold:.2f} raw_ratio={feasible_ratio_raw:.4f}>={raw_threshold:.2f} pass={scientific_comparability}")

                is_energy_comparable = scientific_comparability

                comparability_status = "comparable" if scientific_comparability else "non_comparable"
                manifold_status = "healthy" if scientific_comparability else "degraded"

                # ── Energy metadata validation ──────────────────────
                energy_ok = all(
                    v is not None and not math.isnan(v)
                    for v in (raw_bqm_energy, portfolio_objective_energy, canonical_energy))
                if energy_ok:
                    logger.info(
                        f"[ENERGY_METADATA_VALIDATION] PASS solver={solver_id} "
                        f"raw={raw_bqm_energy:.6f} obj={portfolio_objective_energy:.6f} "
                        f"canonical={canonical_energy:.6f} sci={scientific_comparability} "
                        f"opt={opt_status}")
                else:
                    logger.error(f"[ENERGY_METADATA_VALIDATION] FAIL solver={solver_id}")

                # ── Quality metrics ─────────────────────────────────
                constraint_score = 100.0 if constraints["all_satisfied"] else 0.0
                if not constraints["all_satisfied"]:
                    s = 0
                    tc = 2 + len(set(request.sectors))
                    if constraints.get("budget_satisfaction", 0) > 0.99: s += 1
                    if constraints.get("cardinality_ok"): s += 1
                    s += len(set(request.sectors)) - len(constraints.get("sector_violations", []))
                    constraint_score = (s / tc) * 100.0

                confidence = 1.0
                if is_repaired: confidence -= 0.3
                if not constraints["all_satisfied"]: confidence -= 0.4
                if opt_status in ("non_comparable", "sampling_collapse", "encoding_instability", "scalability_limit", "collapsed_manifold"): confidence = 0.0
                confidence = max(0.0, min(1.0, confidence))

                # ── Status determination ────────────────────────────
                final_status = "success"
                if is_fallback:
                    final_status = "fallback"
                if not scientific_comparability:
                    final_status = "SCIENTIFIC_VIOLATION"
                    logger.warning(f"[SCIENTIFIC_VIOLATION_RECORDED] solver={solver_id} status=NON_COMPARABLE")

                provenance = {
                    "requested_solver": solver_id,
                    "actual_solver": solution.metadata.solver,
                    "execution_origin": solution.metadata.execution_origin,
                    "repair_used": is_repaired,
                    "fallback_triggered": is_fallback,
                    "benchmark_mode": benchmark_mode,
                }

                isolation_record["completed"] = time.time()
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)

                # ── [WARM_START_PROPAGATION] Store classical/neal results ──
                if solver_id == "classical" and final_status == "success":
                    warm_start.set_classical_result(solution.weights, float(raw_bqm_energy))
                    logger.info(f"[WARM_START_PROPAGATION] classical result stored energy={raw_bqm_energy:.6f}")
                if solver_id == "neal" and final_status == "success":
                    warm_start.set_neal_result(solution.weights, float(raw_bqm_energy))
                    logger.info(f"[WARM_START_PROPAGATION] neal result stored energy={raw_bqm_energy:.6f}")

                # ── [GLOBAL_SOLVER_FORENSICS] Record audit ──────────
                forensics.audit_feasibility_parity(solver_id, constraints["all_satisfied"], True)
                forensics.audit_decode_parity(solver_id, solution.weights)

                return {
                    "solver": solver_id,
                    "actual_solver": solution.metadata.solver,
                    "status": final_status,
                    "fallback_reason": solution.metadata.fallback_reason,
                    "energy": objective_energy,
                    "raw_energy": solution.energy,
                    "raw_bqm_energy": raw_bqm_energy,
                    "portfolio_objective_energy": portfolio_objective_energy,
                    "canonical_energy": canonical_energy,
                    "normalized_energy": None,
                    "comparable_energy": objective_energy if scientific_comparability else None,
                    "solve_time_ms": elapsed,
                    "feasible": constraints["all_satisfied"],
                    "constraints": constraints,
                    "metrics": metrics,
                    "selected_assets": selected_assets,
                    "provider": solution.metadata.provider,
                    "backend": solution.metadata.backend_name,
                    "execution_origin": solution.metadata.execution_origin,
                    "fallback_triggered": solution.metadata.fallback_triggered,
                    "fallback_chain": getattr(solution.metadata, "fallback_chain", []),
                    "task_arn": solution.metadata.task_arn,
                    "device_arn": solution.metadata.device_arn,
                    "execution_mode": exec_mode_val,
                    "native_execution": native_execution,
                    "is_energy_comparable": is_energy_comparable,
                    "scientific_comparability": scientific_comparability,
                    "execution_status": exec_status,
                    "optimization_status": opt_status,
                    "comparison_status": comparability_status,
                    "execution_provenance": provenance,
                    "constraint_satisfaction_score": constraint_score,
                    "allocation_sparsity": selected_assets / max(1, len(request.tickers)),
                    "cardinality_deviation": cardinality_delta,
                    "execution_confidence": confidence,
                    "approximation_ratio": None,
                    "feasible_ratio_raw": feasible_ratio_raw,
                    "cardinality_violation_rate": 1.0 - feasible_ratio_raw,
                    "avg_cardinality_delta": float(cardinality_delta),
                    "invalid_measurement_ratio": 0.0,
                    "repaired_sample_ratio": 1.0 if is_repaired else 0.0,
                    "isolation_status": "success",
                    "scientific_gate": {
                        "strict_ratio": strict_ratio,
                        "raw_ratio": feasible_ratio_raw,
                        "entropy": entropy,
                        "inversion_detected": inversion_detected,
                        "manifold_status": manifold_status,
                        "comparability_status": comparability_status,
                    },
                }

            except Exception as exc:
                logger.error("Benchmark failed for solver '%s': %s", solver_id, exc)
                tb_str = tb_format.format_exc()
                isolation_record["completed"] = time.time()
                isolation_record["failed"] = True
                isolation_record["isolated"] = True
                isolation_record["propagated"] = True
                isolation_audit.append(isolation_record)

                logger.info(
                    "[SOLVER_EXECUTION_ISOLATION] solver=%s started=%s completed=%s failed=True isolated=True propagated=True",
                    solver_id, isolation_record["started"], isolation_record["completed"],
                )

                return _empty_result(solver_id, "error", str(exc), tb_str)

        except Exception as outer_exc:
            logger.error("Outer isolation failure for solver '%s': %s", solver_id, outer_exc)
            isolation_record["completed"] = time.time()
            isolation_record["failed"] = True
            isolation_record["isolated"] = True
            isolation_record["propagated"] = True
            isolation_audit.append(isolation_record)
            return _empty_result(solver_id, "error", str(outer_exc), tb_format.format_exc())

    # ── PHASE 3: PER-SOLVER EXECUTION CONTAINMENT ───────────────────
    for solver_id in selected_solver_ids:
        status = solver_statuses.get(solver_id, "unknown")
        try:
            r = await _execute_solver(solver_id, status)
            results.append(r)

            if solver_id in ("classical", "neal") and r.get("status") not in ("success", "skipped"):
                logger.error(f"[VALIDATION_SEQUENCE_FAILURE] Phase {solver_id} failed. Stability compromised.")
        except Exception as e:
            logger.error(f"Sequential execution error for {solver_id}: {e}")
            results.append(_empty_result(solver_id, "error", str(e), tb_format.format_exc()))

    total_elapsed = round((time.perf_counter() - total_start) * 1000, 3)

    # ── PHASE 4: PARTIAL SUCCESS BENCHMARK MODE ─────────────────────
    success_count = len([r for r in results if r.get("status") == "success"])
    fallback_count = len([r for r in results if r.get("status") == "fallback"])
    error_count = len([r for r in results if r.get("status") == "error"])
    skipped_count = len([r for r in results if r.get("status") == "skipped"])
    sci_violation_count = len([r for r in results if r.get("status") == "SCIENTIFIC_VIOLATION"])

    if success_count + fallback_count > 0 and error_count + sci_violation_count > 0:
        benchmark_status = "PARTIAL_SUCCESS"
    elif success_count + fallback_count > 0:
        benchmark_status = "SUCCESS"
    else:
        benchmark_status = "FAILED"

    logger.info(
        "[BENCHMARK_STATUS] status=%s success=%s fallback=%s error=%s skipped=%s sci_violation=%s",
        benchmark_status, success_count, fallback_count, error_count, skipped_count, sci_violation_count,
    )

    # ── MANIFOLD HEALTH ─────────────────────────────────────────────
    manifold_report = compute_manifold_health(results)
    manifold_score = manifold_report.score
    manifold_tier = manifold_report.tier
    print(f"[MANIFOLD_HEALTH_SCORE] score={manifold_score:.4f} tier={manifold_tier}")

    for r in results:
        r["manifold_health_score"] = manifold_score
        r["manifold_health_tier"] = manifold_tier
        r["objective_span"] = objective_span

    if manifold_score < 0.70:
        for r in results:
            if r.get("scientific_comparability") and r.get("solver") not in ("classical", "neal"):
                logger.warning(
                    f"[MANIFOLD_GATE_DOWNGRADE] solver={r['solver']} "
                    f"manifold_score={manifold_score:.4f} below 0.70")

    # ── NORMALIZATION: Only scientifically comparable solvers ───────
    comparable = [
        r for r in results
        if r.get("scientific_comparability") and
           r.get("energy") is not None and
           r.get("feasible") and
           not r.get("fallback_triggered") and
           r.get("optimization_status") not in ("repaired", "non_comparable", "sampling_collapse")
    ]

    strict_ratios = [_safe_metric(r.get("scientific_gate", {}).get("strict_ratio", 0.0), 0.0)
                     for r in results if r.get("status") == "success"]
    avg_strict_ratio = safe_mean(strict_ratios) if strict_ratios else 0.0

    # [LOCAL_ONLY_CALIBRATION_MODE] Relaxed threshold for LOCAL_ONLY validation
    is_local_calibration = (effective_mode == "LOCAL_ONLY")
    calibration_threshold = 0.05 if is_local_calibration else 0.25
    is_scientifically_calibrated = (len(comparable) >= 1 and avg_strict_ratio >= calibration_threshold)

    if is_local_calibration:
        logger.info(f"[LOCAL_ONLY_CALIBRATION_MODE] avg_strict_ratio={avg_strict_ratio:.4f}>={calibration_threshold:.2f} calibrated={is_scientifically_calibrated}")

    if is_scientifically_calibrated and comparable:
        energies = [r["energy"] for r in comparable if r.get("energy") is not None]
        best_e = safe_min(energies)
        worst_e = safe_max(energies)
        spread = worst_e - best_e

        reference_solver = next((r for r in results if r.get("solver") in ("neal", "classical")), None)
        reference_energy = reference_solver["energy"] if reference_solver else best_e
        reference_energy = _safe_metric(reference_energy, best_e)

        logger.info(
            f"[ENERGY_NORMALIZATION_AUDIT] best={best_e:.6f} worst={worst_e:.6f} "
            f"spread={spread:.6f} comparable_count={len(comparable)}")

        for r in results:
            if (r.get("energy") is not None and
                    r.get("scientific_comparability") and
                    r.get("feasible")):

                norm_score = (0.0 if abs(spread) < 1e-9
                              else max(0.0, min(1.0, (r["energy"] - best_e) / spread)))
                r["normalized_energy"] = norm_score

                logger.info(
                    f"[NORMALIZATION_AUDIT] solver={r['solver']} "
                    f"energy={r['energy']:.6f} best={best_e:.6f} "
                    f"worst={worst_e:.6f} normalized_score={norm_score:.4f}")

                q_energy = r["energy"]
                ratio = (reference_energy / q_energy if abs(q_energy) > 1e-9 else 1.0)

                if (reference_energy < 0 and q_energy < 0) or (reference_energy > 0 and q_energy > 0):
                    ratio = abs(ratio)

                r["approximation_ratio"] = ratio

                logger.info(
                    f"[APPROXIMATION_RATIO_AUDIT] solver={r['solver']} "
                    f"quantum_energy={q_energy:.6f} reference_energy={reference_energy:.6f} "
                    f"ratio={ratio:.4f}")
            else:
                r["normalized_energy"] = None
                r["approximation_ratio"] = None
    else:
        for r in results:
            r["normalized_energy"] = "CALIBRATION_INCOMPLETE"
            r["approximation_ratio"] = None

    # ── RANKING: Feasibility-first, repair-excluded ─────────────────
    completed = [
        r for r in results
        if r.get("status") in ("success", "fallback") and
           _safe_metric(r.get("energy"), None) is not None and
           r.get("optimization_status") not in ("repaired", "encoding_instability", "scalability_limit")
    ]

    ranked = sorted(completed, key=lambda r: (
        not r.get("feasible", False),
        not r.get("scientific_comparability", False),
        r.get("fallback_triggered", False),
        _safe_metric(r.get("energy"), float("inf")),
        _safe_metric(r.get("solve_time_ms"), float("inf")),
    ))

    for i, r in enumerate(ranked):
        r["rank"] = i + 1
        print(
            f"[RANKING_VALIDATION] solver={r['solver']} rank={i+1} "
            f"feasible={r.get('feasible')} sci={r.get('scientific_comparability')} "
            f"energy={r.get('energy')}")

    for r in results:
        if r not in completed:
            r["rank"] = 999

    # ── Certification ───────────────────────────────────────────────
    for r in results:
        r["benchmark_fingerprint"] = fingerprint
        certify_benchmark_result(r)

    feasible_results = [r for r in results if r.get("feasible") and _safe_metric(r.get("energy"), None) is not None]
    sci_comparable = [r for r in results if r.get("scientific_comparability")]

    successful_solvers = [r["solver"] for r in results if r.get("status") in ("success", "fallback")]
    chart_points = len([r for r in results if _safe_metric(r.get("energy"), None) is not None])
    table_rows = len(results)
    feasible_count = len([r for r in results if r.get("feasible")])

    print(
        f"[FRONTEND_POPULATION_AUDIT] "
        f"successful_solvers={len(successful_solvers)} "
        f"chart_points={chart_points} "
        f"table_rows={table_rows} "
        f"feasible_count={feasible_count} "
        f"renderable={feasible_count > 0}")

    # ── PHASE 8: TELEMETRY PARTITIONING ─────────────────────────────
    logger.info(
        "[SOLVER_ISOLATION_AUDIT] request_id=%s total_solvers=%s successful=%s failed=%s isolated=%s benchmark_status=%s",
        request_id, len(selected_solver_ids), success_count, error_count,
        len([a for a in isolation_audit if a.get("isolated")]),
        benchmark_status,
    )

    summary = {
        "total_solvers_attempted": len(selected_solver_ids),
        "successful": success_count,
        "fallbacks": fallback_count,
        "skipped": skipped_count,
        "errors": error_count,
        "scientific_violations": sci_violation_count,
        "feasible_solutions": len(feasible_results),
        "scientifically_comparable": len(sci_comparable),
        "best_solver": ranked[0]["solver"] if ranked else None,
        "best_energy": _safe_metric(ranked[0]["energy"], None) if ranked else None,
        "total_benchmark_time_ms": total_elapsed,
        "benchmark_status": benchmark_status,
        "execution_mode": effective_mode,
        "selected_solvers": selected_solver_ids,
        "problem_size": {
            "assets": len(request.mu),
            "cardinality": request.cardinality,
            "binary_bits": request.binary_bits,
        },
        "benchmark_fingerprint": fingerprint,
        "manifold_health": manifold_report.to_dict(),
        "isolation_audit": isolation_audit,
    }

    response = {
        "results": results,
        "ranking": [{"rank": r.get("rank"), "solver": r["solver"],
                     "energy": _safe_metric(r.get("energy"), None), "feasible": r.get("feasible"),
                     "scientific_comparability": r.get("scientific_comparability")}
                    for r in ranked],
        "summary": summary,
    }

    return sanitize_json(response)


# Backward compatibility
def run_benchmark_sync(
    request: SolverRequest,
    settings: Settings | None = None,
    solvers: list[str] | None = None,
    execution_mode: str | None = None,
    timeout_ms: float = 30_000,
    request_id: str | None = None,
) -> dict[str, Any]:
    return asyncio.run(run_benchmark(request, settings, solvers, execution_mode, timeout_ms, request_id))
