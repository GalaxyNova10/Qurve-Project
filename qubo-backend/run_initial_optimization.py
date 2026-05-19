from qubo_backend.data.alpha import load_alpha_data
from qubo_backend.config import get_settings
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.registry import solve
from qubo_backend.optimization.portfolio import result_to_portfolio_response
from qubo_backend.storage.artifacts import ArtifactStore

settings = get_settings()
artifacts = ArtifactStore(settings.output_dir)
alpha = load_alpha_data(settings.output_dir)

request = SolverRequest(
    mu=alpha.mu.tolist(),
    sigma=alpha.sigma.tolist(),
    tickers=alpha.tickers,
    sectors=alpha.sectors,
    cardinality=15,
    max_sector_exposure=0.25,
    risk_tolerance=0.5,
    binary_bits=7,
    solver="classical",
    trajectories=256,
)

solution = solve(request, settings)
result = result_to_portfolio_response(request, solution)
artifacts.write_json("optimal_weights.json", result, safe=True)
print("Optimization complete and optimal_weights.json generated!")
