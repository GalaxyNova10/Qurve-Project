import time
import logging
from typing import Any
import numpy as np

try:
    import torch
except ImportError:
    torch = None

from qubo_backend.optimization.base_solver import BasePortfolioSolver
from qubo_backend.optimization.contracts import SolverRequest, SolverRunMetadata
from qubo_backend.optimization.portfolio import PortfolioSolution, verify_constraints, greedy_feasible_weights
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm

logger = logging.getLogger(__name__)

class GPUSolver(BasePortfolioSolver):
    """
    GPU-accelerated solver using Simulated Bifurcation via PyTorch.
    Designed for large universes (N > 50) requiring massive parallel trajectory searches.
    """
    def __init__(self, dt: float = 0.1, max_steps: int = 1000):
        self.dt = dt
        self.max_steps = max_steps
        
    def solve(self, request: SolverRequest, **kwargs: Any) -> PortfolioSolution:
        # 1. Device & Memory Management (RTX 4060 Constraints)
        if torch is None:
            raise ImportError("PyTorch is not installed. GPUSolver requires torch.")
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is unexpectedly unavailable on this machine. GPUSolver requires a GPU.")
            
        started = time.perf_counter()
        
        # 2. Hardcode safe maximum for parallel trajectories (VRAM limit protection)
        trajectories = min(request.trajectories, 256)
        
        try:
            # Dynamically construct the PyTorch tensors from the input QUBO dictionary
            build = build_portfolio_bqm(request)
            N = len(build.variable_order)
            var_to_idx = {v: i for i, v in enumerate(build.variable_order)}
            
            # Explicitly target CUDA and use FP32 to fit within an 8GB VRAM ceiling
            device = torch.device('cuda')
            Q = torch.zeros((N, N), dtype=torch.float32, device=device)
            
            for var, bias in build.bqm.linear.items():
                i = var_to_idx[var]
                Q[i, i] += float(bias)
                
            for (u, v), bias in build.bqm.quadratic.items():
                i, j = var_to_idx[u], var_to_idx[v]
                Q[i, j] += float(bias) / 2.0
                Q[j, i] += float(bias) / 2.0
                
            # Convert QUBO to Ising: x = (s + 1) / 2
            # J_ij = -0.25 * Q_ij
            # h_i = -0.25 * sum(Q_ij + Q_ji) - 0.5 * Q_ii
            
            Q_sym = Q.clone()
            diag_Q = torch.diag(Q_sym)
            Q_sym.fill_diagonal_(0.0)
            
            J = -0.25 * Q_sym
            h = -0.25 * torch.sum(Q_sym, dim=1) - 0.5 * diag_Q
            
            # Simulated Bifurcation parameters
            a = torch.empty((trajectories, N), dtype=torch.float32, device=device).uniform_(-0.1, 0.1)
            v = torch.empty((trajectories, N), dtype=torch.float32, device=device).uniform_(-0.1, 0.1)
            
            c0 = 1.0
            a_max = 1.0
            
            # Momentum-based discrete-time SB update loop
            for step in range(self.max_steps):
                a_t = (step / self.max_steps) * a_max
                force = - (1.0 - a_t) * a + c0 * (torch.matmul(torch.sign(a), J) + h)
                v += force * self.dt
                a += v * self.dt
                
            s_best = torch.sign(a)
            x_best = (s_best + 1.0) / 2.0
            
            # Evaluate energy efficiently on GPU
            # E = x^T Q x
            x_eval = x_best.unsqueeze(-1)
            energies = torch.bmm(x_best.unsqueeze(1), torch.matmul(Q.unsqueeze(0), x_eval)).squeeze()
            
            best_idx = torch.argmin(energies).item()
            best_bits = x_best[best_idx].cpu().numpy().astype(int)
            best_energy = energies[best_idx].item() + build.bqm.offset
            
            sample = {build.variable_order[i]: best_bits[i] for i in range(N)}
            
            # ── [GPU_DECODE_REMEDIATION] (Phase 1/2) ────────────────────
            from qubo_backend.optimization.qubo_model import QuboModel, decode_sample_to_weights
            model = QuboModel(request=request, build=build)
            
            # Decode best sample
            weights = decode_sample_to_weights(model, sample)
            
            # Calculate feasibility_native from parallel trajectories (Phase 6)
            n_feasible = 0
            # x_best has shape (trajectories, N)
            for t in range(trajectories):
                try:
                    t_bits = x_best[t].cpu().numpy().astype(int)
                    t_sample = {build.variable_order[i]: t_bits[i] for i in range(N)}
                    t_weights = decode_sample_to_weights(model, t_sample)
                    t_active = int(np.sum(t_weights > 1e-6))
                    if t_active == request.cardinality:
                        n_feasible += 1
                except Exception:
                    continue
            
            feasibility_native = n_feasible / max(1, trajectories)
                
            metadata = SolverRunMetadata(
                solver="sb",
                bqm_backend="pytorch_cuda",
                qubo_variables=N,
                linear_terms=len(build.bqm.linear),
                quadratic_terms=len(build.bqm.quadratic),
                solve_time_ms=round((time.perf_counter() - started) * 1000, 3),
                reads=trajectories,
                energy=best_energy,
                provider="local_gpu",
                backend_name="simulated_bifurcation",
                is_qpu=False,
                is_hybrid=False,
                fallback_reason=kwargs.get("fallback_reason"),
                feasibility_native=feasibility_native
            )
            return PortfolioSolution(weights=weights, energy=best_energy, metadata=metadata)
            
        finally:
            # 1. Strict VRAM Hygiene - guarantee no memory leaks
            if torch is not None and torch.cuda.is_available():
                torch.cuda.empty_cache()
