import sys
import os
import numpy as np
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Mock some dependencies if needed or just try importing
try:
    from qubo_backend.optimization.contracts import SolverRequest
    from qubo_backend.optimization.classical_solver import ClassicalSolver
    from qubo_backend.optimization.solver_router import smart_router
    from qubo_backend.solvers.benchmark import benchmark
    print("SUCCESS: All modules imported successfully.")
except ImportError as e:
    print(f"FAILURE: Import failed: {e}")
    sys.exit(1)

def test_classical_strategies():
    print("\nTesting Classical Multi-Strategy...")
    mu = [0.1, 0.2, 0.15, 0.12, 0.18]
    sigma = np.eye(5).tolist()
    tickers = ["A", "B", "C", "D", "E"]
    sectors = ["Tech", "Tech", "Fin", "Fin", "Health"]
    
    request = SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=tickers,
        sectors=sectors,
        cardinality=3,
        max_sector_exposure=0.5,
        risk_tolerance=0.5,
        binary_bits=3,
        solver="classical",
        trajectories=10
    )
    
    solver = ClassicalSolver()
    
    # Test Auto
    print("Running strategy='auto'...")
    sol = solver.solve(request, strategy="auto")
    print(f"Winner strategy: {sol.metadata.strategy}")
    print(f"Weights: {sol.weights}")
    
    # Test individual strategies
    for strat in ["greedy", "sa", "ga"]:
        print(f"Running strategy='{strat}'...")
        sol = solver.solve(request, strategy=strat)
        print(f"Result {strat}: energy={sol.energy:.4f}")

def test_router_cascade():
    print("\nTesting Router Cascade (Braket Fallback)...")
    mu = [0.1] * 5
    sigma = np.eye(5).tolist()
    request = SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=["T"+str(i) for i in range(5)],
        sectors=["S1"]*5,
        cardinality=2,
        solver="braket" # Should fallback to classical if braket not installed
    )
    
    sol = smart_router.route(request)
    print(f"Requested 'braket', actually used: {sol.metadata.actual_solver_used}")
    if sol.metadata.fallback_reason:
        print(f"Fallback reason: {sol.metadata.fallback_reason}")

def test_benchmark():
    print("\nTesting Benchmarking Engine...")
    mu = [0.1, 0.2, 0.15, 0.12, 0.18]
    sigma = np.eye(5).tolist()
    request = SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=["A", "B", "C", "D", "E"],
        sectors=["T", "T", "F", "F", "H"],
        cardinality=3,
        solver="auto"
    )
    
    results = benchmark(request, include_quantum=True)
    print(f"Benchmark finished. Winner: {results['winner']}")
    for r in results['results']:
        print(f"  - {r['label']}: {r['status']} (Energy: {r['energy']})")

if __name__ == "__main__":
    try:
        test_classical_strategies()
        test_router_cascade()
        test_benchmark()
        print("\nVerification complete!")
    except Exception as e:
        print(f"FAILURE: Verification failed: {e}")
        import traceback
        traceback.print_exc()
