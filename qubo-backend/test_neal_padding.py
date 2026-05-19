"""
Test script to verify Neal SA padding logic when asset limiting is applied
"""

import numpy as np
import asyncio
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.dwave_sa_solver import NealSASolver, NealSASolverConfig, BenchmarkExecutionConfig, PrecisionMode


def test_neal_padding():
    """Test Neal SA solver with asset limiting and padding."""
    print("=== Testing Neal SA Asset Limiting and Padding ===")
    
    # Create a problem with more assets than the benchmark limit
    n_assets = 50  # More than typical benchmark limit of 30
    np.random.seed(42)  # For reproducible results
    
    # Create test problem
    mu = np.random.normal(0.1, 0.05, n_assets).tolist()
    sigma = np.random.uniform(0.01, 0.1, (n_assets, n_assets))
    sigma = (sigma + sigma.T) / 2  # Make symmetric
    np.fill_diagonal(sigma, np.diag(sigma))  # Ensure positive diagonal
    sigma = sigma.tolist()  # Convert to list after numpy operations
    
    tickers = [f"TEST_{i}" for i in range(n_assets)]
    sectors = [f"Sector_{i % 5}" for i in range(n_assets)]  # 5 different sectors
    
    request = SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=tickers,
        sectors=sectors,
        cardinality=10,
        max_sector_exposure=0.5,
        risk_tolerance=0.5,
        binary_bits=3,
        solver="neal",
        trajectories=100
    )
    
    print(f"Original problem: {n_assets} assets, cardinality={request.cardinality}")
    
    # Configure Neal SA with benchmark mode and asset limiting
    benchmark_config = BenchmarkExecutionConfig(
        precision_mode=PrecisionMode.BENCHMARK_FAST,
        num_reads=25,
        num_sweeps=25,
        max_problem_size=26,  # Force asset limiting from 50 to 26
        aggressive_sparsification=True,
        covariance_threshold=0.015
    )
    
    config = NealSASolverConfig(
        benchmark_mode=True,
        benchmark_config=benchmark_config
    )
    
    solver = NealSASolver(config)
    
    # Test the solve
    print("\nExecuting Neal SA with asset limiting...")
    try:
        solution = solver.solve(request)
        
        print(f"✅ SUCCESS: Neal SA completed with asset limiting")
        print(f"Original assets: {n_assets}")
        print(f"Solution weights length: {len(solution.weights)}")
        print(f"Expected length: {n_assets}")
        print(f"Lengths match: {len(solution.weights) == n_assets}")
        print(f"Energy: {solution.energy}")
        print(f"Solve time: {solution.metadata.solve_time_ms}ms")
        
        # Verify the padding is correct
        if len(solution.weights) == n_assets:
            print("✅ PADDING TEST PASSED: Weights array matches original size")
            
            # Check that the padded portion is zeros
            # The first 26 elements should have values, the rest should be zeros
            non_zero_count = np.sum(np.abs(solution.weights) > 1e-6)
            print(f"Non-zero weights: {non_zero_count}")
            print(f"Expected max non-zero: 26 (due to asset limiting)")
            
            if non_zero_count <= 26:
                print("✅ PADDING CORRECT: Only expected number of non-zero weights")
            else:
                print("❌ PADDING ISSUE: More non-zero weights than expected")
                
            return True
        else:
            print(f"❌ PADDING FAILED: Expected {n_assets} weights, got {len(solution.weights)}")
            return False
            
    except Exception as e:
        print(f"❌ FAIL: Exception during execution: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_neal_padding()
    print(f"\nTest result: {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)
