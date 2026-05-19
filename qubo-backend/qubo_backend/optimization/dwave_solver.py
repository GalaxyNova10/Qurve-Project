import time
from typing import Any

from qubo_backend.config import get_settings
from qubo_backend.optimization.base_solver import BasePortfolioSolver
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution
from qubo_backend.optimization.qubo_model import build_qubo_model, to_dimod_bqm
from qubo_backend.solvers.quantum_common import safe_error, solution_from_sample


def dwave_status(settings=None) -> str:
    """Check if D-Wave API is configured."""
    if settings is None:
        settings = get_settings()
    if not settings.dwave_api_token:
        return "missing_token"
    try:
        from dwave.system import DWaveSampler, LeapHybridSampler  # noqa: F401
        return "configured"
    except ImportError:
        return "not_installed"


def solve_dwave(request: SolverRequest, settings=None, direct_qpu=False) -> PortfolioSolution:
    """Compatibility wrapper for benchmark.py."""
    solver = DWaveSolver()
    return solver.solve(request, direct_qpu=direct_qpu)


class DWaveSolver(BasePortfolioSolver):
    """
    D-Wave Cloud Quantum Solver.
    Utilizes LeapHybridSampler for production-scale runs, or EmbeddingComposite for direct QPU.
    """
    
    def solve(self, request: SolverRequest, **kwargs: Any) -> PortfolioSolution:
        # 1. D-Wave API Resiliency Pre-Check
        settings = get_settings()
        if not settings.dwave_api_token:
            # Raise a specific exception so the router can immediately catch it
            raise ValueError("DWAVE_API_TOKEN is missing or not configured. D-Wave solver requires a valid token.")
            
        try:
            from dwave.system import DWaveSampler, EmbeddingComposite, LeapHybridSampler
        except ImportError:
            raise ImportError("dwave-ocean-sdk is not installed.")
            
        started = time.perf_counter()
        model = build_qubo_model(request)
        
        try:
            dwave_kwargs: dict[str, Any] = {"token": settings.dwave_api_token}
            if settings.dwave_api_endpoint:
                dwave_kwargs["endpoint"] = settings.dwave_api_endpoint
                
            direct_qpu = kwargs.get("direct_qpu", False)
            
            if direct_qpu:
                sampler = EmbeddingComposite(DWaveSampler(**dwave_kwargs))
                sampleset = sampler.sample(to_dimod_bqm(model), num_reads=request.trajectories)
                provider_solver = "dwave_qpu"
                provider_label = getattr(getattr(sampler, "child", None), "solver", None)
                backend_name = getattr(provider_label, "name", None) or "DWaveSampler"
                is_qpu = True
                is_hybrid = False
            else:
                sampler = LeapHybridSampler(**dwave_kwargs)
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
            }
            
            try:
                values = sampleset.record.chain_break_fraction
                if len(values) > 0:
                    metadata["chain_break_fraction"] = float(values[0])
            except Exception:
                pass
                
            # 3. Unified Output & Repair
            # Uses the exact same repair flow via solution_from_sample
            return solution_from_sample(request, model, dict(first.sample), provider_solver, metadata)
            
        except Exception as exc:
            # Re-raise with a clear message so the router handles the fallback gracefully
            raise RuntimeError(f"D-Wave execution failed: {safe_error(exc)}")
