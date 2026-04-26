from __future__ import annotations

import time

from qubo_backend.config import Settings
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution, solve_locally
from qubo_backend.optimization.qubo_model import build_qubo_model, to_qiskit_quadratic_program

from .quantum_common import safe_error, solution_from_sample


def qiskit_status(settings: Settings) -> str:
    try:
        import qiskit_optimization  # noqa: F401
    except ImportError:
        return "not_installed"
    return "available_with_ibm_token" if settings.ibm_quantum_token else "available_local"


def solve_qiskit_qaoa(request: SolverRequest, settings: Settings) -> PortfolioSolution:
    eligibility = _eligibility_reason(request, settings)
    if eligibility:
        solution = solve_locally(request, solver_name="qiskit_qaoa_fallback", fallback_reason=eligibility)
        solution.metadata.provider = "ibm-qiskit"  # type: ignore[misc]
        solution.metadata.qiskit_max_assets = settings.qiskit_max_assets  # type: ignore[misc]
        solution.metadata.qiskit_max_binary_bits = settings.qiskit_max_binary_bits  # type: ignore[misc]
        solution.metadata.eligibility_reason = eligibility  # type: ignore[misc]
        return solution

    try:
        from qiskit_optimization.algorithms import MinimumEigenOptimizer
        from qiskit_optimization.converters import QuadraticProgramToQubo
    except ImportError:
        return solve_locally(
            request,
            solver_name="qiskit_qaoa_fallback",
            fallback_reason="qiskit-optimization is not installed",
        )

    started = time.perf_counter()
    model = build_qubo_model(request)
    try:
        qp = to_qiskit_quadratic_program(model)
        converted = QuadraticProgramToQubo().convert(qp)
        minimum_eigensolver = _make_qaoa_solver()
        optimizer = MinimumEigenOptimizer(minimum_eigensolver)
        result = optimizer.solve(converted)
        sample = dict(zip(model.variable_order, [int(round(float(value))) for value in result.x]))
        metadata = {
            "solver": "qiskit_qaoa",
            "provider": "ibm-qiskit",
            "quantum_backend": "local_qaoa",
            "backend_name": type(minimum_eigensolver).__name__,
            "is_qpu": False,
            "is_hybrid": True,
            "energy": float(result.fval) if result.fval is not None else None,
            "solve_time_ms": round((time.perf_counter() - started) * 1000, 3),
            "reads": request.trajectories,
            "qiskit_max_assets": settings.qiskit_max_assets,
            "qiskit_max_binary_bits": settings.qiskit_max_binary_bits,
        }
        return solution_from_sample(request, model, sample, "qiskit_qaoa", metadata)
    except Exception as exc:
        return solve_locally(request, solver_name="qiskit_qaoa_fallback", fallback_reason=safe_error(exc))


def _eligibility_reason(request: SolverRequest, settings: Settings) -> str | None:
    if len(request.tickers) > settings.qiskit_max_assets:
        return f"Qiskit QAOA is capped to {settings.qiskit_max_assets} assets for local simulation"
    if request.binary_bits > settings.qiskit_max_binary_bits:
        return f"Qiskit QAOA is capped to {settings.qiskit_max_binary_bits} binary bits for local simulation"
    return None


def _make_qaoa_solver():
    try:
        from qiskit.primitives import StatevectorSampler
        from qiskit_algorithms.minimum_eigensolvers import QAOA
        from qiskit_algorithms.optimizers import COBYLA

        return QAOA(sampler=StatevectorSampler(), optimizer=COBYLA(maxiter=40), reps=1)
    except ImportError:
        from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver

        return NumPyMinimumEigensolver()
