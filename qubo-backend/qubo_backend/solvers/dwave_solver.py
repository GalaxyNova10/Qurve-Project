from __future__ import annotations

import time
from typing import Any

from qubo_backend.config import Settings
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution, solve_locally
from qubo_backend.optimization.qubo_model import build_qubo_model, to_dimod_bqm

from .quantum_common import safe_error, solution_from_sample


def dwave_status(settings: Settings) -> str:
    try:
        import dwave.system  # noqa: F401
    except ImportError:
        return "not_installed"
    if not settings.dwave_api_token:
        return "missing_token"
    return "configured"


def solve_dwave(request: SolverRequest, settings: Settings, direct_qpu: bool = False) -> PortfolioSolution:
    if not settings.dwave_api_token:
        return solve_locally(request, solver_name="dwave_fallback", fallback_reason="DWAVE_API_TOKEN is not configured")

    try:
        from dwave.system import DWaveSampler, EmbeddingComposite, LeapHybridSampler
    except ImportError:
        return solve_locally(request, solver_name="dwave_fallback", fallback_reason="dwave-ocean-sdk is not installed")

    started = time.perf_counter()
    model = build_qubo_model(request)
    try:
        kwargs: dict[str, Any] = {"token": settings.dwave_api_token}
        if settings.dwave_api_endpoint:
            kwargs["endpoint"] = settings.dwave_api_endpoint

        if direct_qpu:
            sampler = EmbeddingComposite(DWaveSampler(**kwargs))
            sampleset = sampler.sample(to_dimod_bqm(model), num_reads=request.trajectories)
            provider_solver = "dwave_qpu"
            provider_label = getattr(getattr(sampler, "child", None), "solver", None)
            backend_name = getattr(provider_label, "name", None) or "DWaveSampler"
            is_qpu = True
            is_hybrid = False
        else:
            sampler = LeapHybridSampler(**kwargs)
            sample_kwargs = {}
            if request.time_limit_seconds is not None:
                sample_kwargs["time_limit"] = request.time_limit_seconds
            sampleset = sampler.sample(to_dimod_bqm(model), **sample_kwargs)
            provider_solver = "dwave_hybrid"
            backend_name = getattr(getattr(sampler, "solver", None), "name", None) or "LeapHybridSampler"
            is_qpu = False
            is_hybrid = True

        first = sampleset.first
        metadata = {
            "solver": provider_solver,
            "provider": "dwave",
            "quantum_backend": provider_solver,
            "backend_name": backend_name,
            "is_qpu": is_qpu,
            "is_hybrid": is_hybrid,
            "energy": float(first.energy),
            "solve_time_ms": round((time.perf_counter() - started) * 1000, 3),
            "reads": request.trajectories,
            "time_limit_seconds": request.time_limit_seconds,
            "chain_break_fraction": _chain_break_fraction(sampleset),
        }
        return solution_from_sample(request, model, dict(first.sample), provider_solver, metadata)
    except Exception as exc:
        return solve_locally(request, solver_name="dwave_fallback", fallback_reason=safe_error(exc))


def _chain_break_fraction(sampleset: Any) -> float | None:
    try:
        values = sampleset.record.chain_break_fraction
        if len(values) == 0:
            return None
        return float(values[0])
    except Exception:
        return None
