from __future__ import annotations

import time

from qubo_backend.config import Settings, get_settings, redact_secret
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution, solve_locally

from .classical_solver import solve_classical
from .dwave_solver import dwave_status, solve_dwave
from .qiskit_solver import qiskit_status, solve_qiskit_qaoa

# New Local Quantum Simulators
from optimization.dwave_solver import solve_with_dwave_local
from optimization.qiskit_solver import solve_with_qiskit_local


def available_solvers(settings: Settings | None = None) -> list[dict]:
    settings = settings or get_settings()
    return [
        {
            "id": "classical",
            "label": "Classical Feasible Fallback",
            "status": "available",
            "production": True,
            "description": "Deterministic feasibility-preserving local optimizer.",
        },
        {
            "id": "sb",
            "label": "Local Simulated Bifurcation Fallback",
            "status": "available",
            "production": True,
            "description": "Legacy alias for the local feasibility-preserving path unless SB runtime is configured.",
        },
        {
            "id": "neal",
            "label": "D-Wave Neal Simulated Annealing",
            "status": _optional_status("neal"),
            "production": True,
            "description": "Local CPU simulated annealing for dimod BQMs with feasibility repair.",
        },
        {
            "id": "dwave_hybrid",
            "label": "D-Wave Leap Hybrid BQM",
            "status": dwave_status(settings),
            "production": True,
            "description": "Cloud hybrid sampler for production-size BQM runs. Requires DWAVE_API_TOKEN.",
        },
        {
            "id": "dwave_qpu",
            "label": "D-Wave Direct QPU",
            "status": dwave_status(settings),
            "production": False,
            "description": "Experimental direct annealing with embedding diagnostics. Requires DWAVE_API_TOKEN.",
        },
        {
            "id": "qiskit_qaoa",
            "label": "IBM Qiskit QAOA",
            "status": qiskit_status(settings),
            "production": False,
            "description": "Local-first QAOA/MinimumEigenOptimizer path capped to reduced universes.",
        },
        {
            "id": "hybrid",
            "label": "Hybrid Quantum-Classical",
            "status": "available",
            "production": True,
            "description": "Attempts D-Wave, then eligible Qiskit QAOA, then classical fallback.",
        },
        {
            "id": "dwave_local",
            "label": "D-Wave Local (SA)",
            "status": "available",
            "production": False,
            "description": "Local Simulated Annealing via dimod (No API key needed).",
        },
        {
            "id": "qiskit_local",
            "label": "Qiskit Local (QAOA)",
            "status": "available",
            "production": False,
            "description": "Local QAOA simulator via Qiskit Aer (No API key needed).",
        },
    ]


def _optional_status(module_name: str) -> str:
    try:
        __import__(module_name)
        return "available"
    except ImportError:
        return "not_installed"
    except Exception as exc:
        return f"error:{redact_secret(exc)}"


def solve(request: SolverRequest, settings: Settings | None = None) -> PortfolioSolution:
    settings = settings or get_settings()
    if request.solver in {"classical", "sb"}:
        return solve_classical(request, solver_name=request.solver)
    if request.solver == "neal":
        return _solve_with_neal(request)
    if request.solver == "dwave_hybrid":
        return solve_dwave(request, settings, direct_qpu=False)
    if request.solver == "dwave_qpu":
        return solve_dwave(request, settings, direct_qpu=True)
    if request.solver in {"qiskit", "qiskit_qaoa"}:
        return solve_qiskit_qaoa(request, settings)
    if request.solver == "hybrid":
        return solve_hybrid(request, settings)
    if request.solver == "dwave_local":
        return _solve_dwave_local_wrapper(request)
    if request.solver == "qiskit_local":
        return _solve_qiskit_local_wrapper(request)
    return solve_classical(request, solver_name="classical")


def _solve_dwave_local_wrapper(request: SolverRequest) -> PortfolioSolution:
    import time
    import numpy as np
    from qubo_backend.optimization.portfolio import PortfolioSolution
    
    started = time.perf_counter()
    res = solve_with_dwave_local(
        mu=np.array(request.mu),
        sigma=np.array(request.sigma),
        cardinality=request.cardinality,
        risk_tolerance=request.risk_tolerance,
        binary_bits=request.binary_bits
    )
    
    # Map back to PortfolioSolution
    # Note: This is a simplified mapping for the demonstration
    from qubo_backend.optimization.contracts import SolverMetadata
    return PortfolioSolution(
        weights={ticker: w for ticker, w in zip(request.tickers, res["weights"])},
        metadata=SolverMetadata(
            solver="dwave_local",
            energy=res["energy"],
            solve_time_ms=round((time.perf_counter() - started) * 1000, 3),
            provider="local"
        )
    )

def _solve_qiskit_local_wrapper(request: SolverRequest) -> PortfolioSolution:
    import time
    import numpy as np
    from qubo_backend.optimization.portfolio import PortfolioSolution
    
    started = time.perf_counter()
    res = solve_with_qiskit_local(
        mu=np.array(request.mu),
        sigma=np.array(request.sigma),
        cardinality=request.cardinality,
        risk_tolerance=request.risk_tolerance,
        binary_bits=min(request.binary_bits, 3) # Cap qubits for local sim
    )
    
    from qubo_backend.optimization.contracts import SolverMetadata
    return PortfolioSolution(
        weights={ticker: w for ticker, w in zip(request.tickers, res["weights"])},
        metadata=SolverMetadata(
            solver="qiskit_local",
            energy=res["energy"],
            solve_time_ms=round((time.perf_counter() - started) * 1000, 3),
            provider="local"
        )
    )


def solve_hybrid(request: SolverRequest, settings: Settings) -> PortfolioSolution:
    dwave_request = request.model_copy(update={"solver": "dwave_hybrid"})
    dwave_solution = solve_dwave(dwave_request, settings, direct_qpu=False)
    if not _is_fallback(dwave_solution):
        return dwave_solution

    qiskit_request = request.model_copy(update={"solver": "qiskit_qaoa"})
    qiskit_solution = solve_qiskit_qaoa(qiskit_request, settings)
    if not _is_fallback(qiskit_solution):
        qiskit_solution.metadata.fallback_reason = (
            f"D-Wave unavailable; used Qiskit. D-Wave reason: {dwave_solution.metadata.fallback_reason}"
        )  # type: ignore[misc]
        return qiskit_solution

    classical = solve_classical(request, solver_name="hybrid_classical_fallback")
    classical.metadata.fallback_reason = (  # type: ignore[misc]
        "D-Wave and Qiskit were unavailable or ineligible; "
        f"D-Wave: {dwave_solution.metadata.fallback_reason}; "
        f"Qiskit: {qiskit_solution.metadata.fallback_reason}"
    )
    classical.metadata.provider = "local"  # type: ignore[misc]
    return classical


def _is_fallback(solution: PortfolioSolution) -> bool:
    return "fallback" in solution.metadata.solver or bool(solution.metadata.fallback_reason)


def _solve_with_neal(request: SolverRequest) -> PortfolioSolution:
    try:
        import neal
    except ImportError:
        return solve_locally(request, solver_name="neal_fallback", fallback_reason="neal is not installed")

    started = time.perf_counter()
    build = build_portfolio_bqm(request)
    try:
        sampler = neal.SimulatedAnnealingSampler()
        sampleset = sampler.sample(build.bqm.to_dimod(), num_reads=request.trajectories)
        energy = float(sampleset.first.energy)
        solution = solve_locally(request, solver_name="neal_repaired")
        solution.metadata.energy = energy  # type: ignore[misc]
        solution.metadata.solve_time_ms = round((time.perf_counter() - started) * 1000, 3)  # type: ignore[misc]
        solution.metadata.provider = "local"  # type: ignore[misc]
        solution.metadata.backend_name = "neal.SimulatedAnnealingSampler"  # type: ignore[misc]
        return solution
    except Exception as exc:
        return solve_locally(request, solver_name="neal_fallback", fallback_reason=redact_secret(exc))
