from __future__ import annotations

from typing import Any

from qubo_backend.config import redact_secret
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import (
    PortfolioSolution,
    bqm_energy,
    encode_weights,
    solve_locally,
    verify_constraints,
)
from qubo_backend.optimization.qubo_model import QuboModel, decode_sample_to_weights


def safe_error(exc: BaseException) -> str:
    return redact_secret(f"{type(exc).__name__}: {exc}")


def solution_from_sample(
    request: SolverRequest,
    model: QuboModel,
    sample: dict[str, Any],
    solver_name: str,
    metadata: dict[str, Any],
) -> PortfolioSolution:
    weights = decode_sample_to_weights(model, sample)
    check = verify_constraints(weights, request.sectors, request.cardinality, request.max_sector_exposure, sector_tolerance=1e-5)
    if not check["all_satisfied"]:
        solution = solve_locally(
            request,
            solver_name=f"{solver_name}_repaired",
            fallback_reason=f"Provider sample was infeasible and repaired locally: {check}",
        )
    else:
        encoded = encode_weights(model.build, weights)
        solution = PortfolioSolution(
            weights=weights,
            energy=bqm_energy(model.build, encoded),
            metadata=solve_locally(request, solver_name=solver_name).metadata,
        )
        solution.metadata.solver = solver_name  # type: ignore[misc]
        solution.metadata.energy = solution.energy  # type: ignore[misc]
    for key, value in metadata.items():
        setattr(solution.metadata, key, value)
    return solution
