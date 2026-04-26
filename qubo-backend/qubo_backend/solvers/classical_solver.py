from __future__ import annotations

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution, solve_locally


def solve_classical(request: SolverRequest, solver_name: str = "classical") -> PortfolioSolution:
    return solve_locally(request, solver_name=solver_name)
