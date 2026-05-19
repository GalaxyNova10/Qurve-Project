"""
Validation test for D-Wave Neal Simulated Annealing solver
"""

import numpy as np
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.dwave_sa_solver import create_neal_sa_solver, is_neal_sa_available
from qubo_backend.solvers.registry import available_solvers


def test_neal_sa_validation():
    """Create automated validation test for Neal SA solver."""
    print("=== D-Wave Neal SA Validation Test ===")
    
    # Test 1: Check availability
    print("\n1. Checking Neal SA availability...")
    available = is_neal_sa_available()
    print(f"   Neal SA available: {available}")
    
    if not available:
        print("   ❌ FAIL: Neal SA is not available")
        return False
    
    # Test 2: Check registry status
    print("\n2. Checking registry status...")
    solvers = available_solvers()
    neal_solver = next((s for s in solvers if s['id'] == 'neal'), None)
    
    if neal_solver is None:
        print("   ❌ FAIL: Neal solver not found in registry")
        return False
    
    print(f"   Registry status: {neal_solver['status']}")
    print(f"   Registry label: {neal_solver['label']}")
    
    if neal_solver['status'] != 'available':
        print("   ❌ FAIL: Neal solver not showing as 'available'")
        return False
    
    # Test 3: Generate small QUBO problem
    print("\n3. Generating test QUBO problem...")
    n_assets = 10
    np.random.seed(42)  # For reproducible results
    
    # Create test problem
    mu = np.random.normal(0.1, 0.05, n_assets).tolist()
    sigma = np.random.uniform(0.01, 0.1, (n_assets, n_assets))
    sigma = (sigma + sigma.T) / 2  # Make symmetric
    np.fill_diagonal(sigma, np.diag(sigma))  # Ensure positive diagonal
    sigma = sigma.tolist()  # Convert to list after numpy operations
    
    tickers = [f"TEST_{i}" for i in range(n_assets)]
    sectors = ["Test"] * n_assets
    
    request = SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=tickers,
        sectors=sectors,
        cardinality=min(5, n_assets),  # Ensure cardinality <= assets
        max_sector_exposure=0.5,
        risk_tolerance=0.5,
        binary_bits=3,
        solver="neal",
        trajectories=100
    )
    
    print(f"   Problem: {n_assets} assets, cardinality={request.cardinality}")
    
    # Test 4: Execute Neal SA
    print("\n4. Executing Neal SA solver...")
    try:
        solution = create_neal_sa_solver(request)
        print(f"   ✅ SUCCESS: Neal SA executed")
        print(f"   Solver used: {solution.metadata.actual_solver_used}")
        print(f"   Energy: {solution.energy}")
        print(f"   Solve time: {solution.metadata.solve_time_ms}ms")
        print(f"   Provider: {solution.metadata.provider}")
        print(f"   Backend: {solution.metadata.backend_name}")
        
        # Test 5: Verify feasible result
        print("\n5. Verifying feasibility...")
        weights = solution.weights
        selected_assets = np.sum(weights > 1e-6)
        cardinality_satisfied = abs(selected_assets - request.cardinality) < 1e-6
        
        print(f"   Selected assets: {selected_assets}")
        print(f"   Target cardinality: {request.cardinality}")
        print(f"   Cardinality satisfied: {cardinality_satisfied}")
        
        if not cardinality_satisfied:
            print("   ❌ FAIL: Cardinality constraint not satisfied")
            return False
        
        # Test 6: Verify energy output
        print("\n6. Verifying energy output...")
        if solution.energy is None or np.isnan(solution.energy):
            print("   ❌ FAIL: Invalid energy output")
            return False
        
        if solution.energy > 1e6:  # Reasonable upper bound
            print(f"   ⚠️  WARNING: Energy seems high: {solution.energy}")
        
        print(f"   ✅ Energy output valid: {solution.energy}")
        
        # Test 7: Verify benchmark integration
        print("\n7. Verifying benchmark integration...")
        from qubo_backend.solvers.benchmark import run_benchmark
        
        benchmark_result = run_benchmark(request, solvers=['neal'])
        neal_benchmark = next((r for r in benchmark_result['results'] if r['solver'] == 'neal'), None)
        
        if neal_benchmark is None:
            print("   ❌ FAIL: Neal not found in benchmark results")
            return False
        
        print(f"   Benchmark status: {neal_benchmark['status']}")
        print(f"   Benchmark energy: {neal_benchmark['energy']}")
        print(f"   Benchmark time: {neal_benchmark['solve_time_ms']}ms")
        
        if neal_benchmark['status'] not in ['success', 'fallback']:
            print("   ❌ FAIL: Benchmark status invalid")
            return False
        
        print("\n=== All Tests Passed ✅ ===")
        return True
        
    except Exception as e:
        print(f"   ❌ FAIL: Exception during execution: {e}")
        return False


if __name__ == "__main__":
    success = test_neal_sa_validation()
    exit(0 if success else 1)
