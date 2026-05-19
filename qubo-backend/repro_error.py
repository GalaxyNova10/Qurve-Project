import asyncio
import numpy as np
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.braket_integration import IntegratedBraketSolver

async def test():
    n_assets = 3
    mu = [0.1] * n_assets
    sigma = [[0.01 if i == j else 0.0 for j in range(n_assets)] for i in range(n_assets)]
    tickers = ["A", "B", "C"]
    sectors = ["S", "S", "S"]
    request = SolverRequest(
        mu=mu, sigma=sigma, tickers=tickers, sectors=sectors,
        cardinality=2, max_sector_exposure=1.0,
        risk_tolerance=1.0, binary_bits=2, solver="AWS_BRAKET_LOCAL",
        benchmark_mode="FAST"
    )
    solver = IntegratedBraketSolver()
    try:
        solution = await solver.solve_async(request)
        print("SUCCESS")
        print(f"Energy: {solution.energy}")
        print(f"Weights: {solution.weights}")
        print(f"Scientific Pass: {solution.metadata.scientific_comparability}")
        print(f"Optimization Status: {solution.metadata.optimization_status}")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())
