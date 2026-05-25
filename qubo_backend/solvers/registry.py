from __future__ import annotations

import time

from qubo_backend.config import Settings, get_settings, redact_secret
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution, solve_locally

from qubo_backend.optimization.solver_router import route_and_solve
from qubo_backend.optimization.dwave_solver import dwave_status
from qubo_backend.optimization.qiskit_solver import qiskit_status
from qubo_backend.optimization.braket_solver import braket_status
from qubo_backend.optimization.dwave_sa_solver import get_neal_sa_status


def available_solvers(settings: Settings | None = None) -> list[dict]:
    settings = settings or get_settings()
    return [
        {
            "id": "auto",
            "label": "Auto (Smart Router)",
            "status": "available",
            "production": True,
            "description": "Automatically routes to optimal solver based on problem size.",
        },
        {
            "id": "classical",
            "label": "Classical Feasible Fallback",
            "status": "available",
            "production": True,
            "description": "Deterministic feasibility-preserving local optimizer.",
        },
        {
            "id": "sb",
            "label": "GPU Accelerated (Simulated Bifurcation)",
            "status": "available",
            "production": True,
            "description": "High-performance PyTorch solver for large portfolios (N > 50).",
        },
        {
            "id": "neal",
            "label": "D-Wave Neal Simulated Annealing",
            "status": get_neal_sa_status(),
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
        {
            "id": "braket",
            "label": "AWS Braket LocalSimulator (QAOA)",
            "status": _braket_status(),
            "production": False,
            "description": "Zero-cost local QAOA via Amazon Braket LocalSimulator. Capped to ≤8 assets.",
        },
        {
            "id": "AWS_BRAKET_TN1",
            "label": "AWS Braket TN1 (Cloud Simulator)",
            "status": _braket_status(),
            "production": True,
            "description": "High-performance Tensor Network simulator in the AWS cloud.",
        },
        {
            "id": "AWS_BRAKET_SV1",
            "label": "AWS Braket SV1 (Cloud Simulator)",
            "status": _braket_status(),
            "production": True,
            "description": "State Vector simulator in the AWS cloud for up to 34 qubits.",
        },
        {
            "id": "AWS_BRAKET_DM1",
            "label": "AWS Braket DM1 (Cloud Simulator)",
            "status": _braket_status(),
            "production": True,
            "description": "Density Matrix simulator in the AWS cloud for noise simulation.",
        },
        {
            "id": "AWS_BRAKET_LOCAL",
            "label": "AWS Braket Local (Integrated)",
            "status": _braket_status(),
            "production": False,
            "description": "Integrated local Braket simulation with full telemetry.",
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


def _braket_status() -> str:
    try:
        import braket  # noqa: F401
        return "available"
    except ImportError:
        return "not_installed"
    except Exception as exc:
        return f"error:{redact_secret(exc)}"


def solve(request: SolverRequest, settings: Settings | None = None) -> PortfolioSolution:
    """Route and execute a solver request. Delegates to solver_router."""
    settings = settings or get_settings()
    return route_and_solve(request, settings)


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
