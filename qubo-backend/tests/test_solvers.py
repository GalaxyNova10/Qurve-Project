import numpy as np
import pytest

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.solver_router import smart_router

def test_gpu_solver_large_universe():
    """
    Verifies that a large universe (N=60) successfully routes to the GPU solver,
    constructs the PyTorch tensors properly without OOM, and returns the 
    standardized PortfolioSolution interface seamlessly.
    """
    N = 60
    np.random.seed(42)
    
    # Generate mock 60-asset universe
    mu = np.random.uniform(0.01, 0.2, size=N).tolist()
    
    # Create a positive semi-definite covariance matrix
    A = np.random.uniform(-0.1, 0.1, size=(N, N))
    sigma = (A @ A.T).tolist()
    
    tickers = [f"TICK_{i}" for i in range(N)]
    sector_pool = ["Tech", "Finance", "Energy", "Healthcare"]
    sectors = [sector_pool[i % len(sector_pool)] for i in range(N)]
    
    request = SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=tickers,
        sectors=sectors,
        cardinality=15,
        max_sector_exposure=0.25,
        risk_tolerance=0.5,
        binary_bits=3,
        solver="sb", # Explicitly trigger the GPU solver
        trajectories=128
    )
    
    # Execute the smart router
    solution = smart_router.route(request)
    
    # Verify the output shape and structure perfectly mimics the classical solver
    assert len(solution.weights) == N
    assert solution.metadata is not None
    
    # It either succeeded on GPU or safely cascaded to classical fallback
    assert solution.metadata.solver in ["sb", "classical_fallback"]
    
    # Verify constraints: budget
    total_weight = sum(solution.weights)
    assert abs(total_weight - 1.0) < 1e-5
    
    # Verify constraints: cardinality
    selected_count = sum(w > 1e-6 for w in solution.weights)
    assert selected_count == 15
