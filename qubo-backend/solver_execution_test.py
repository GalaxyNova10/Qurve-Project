#!/usr/bin/env python3
"""
Qurve AI Solver Execution Validation Script
Tests each solver individually for actual execution
"""

import sys
import time
import logging
import asyncio
import numpy as np

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== SOLVER EXECUTION VALIDATION ===')

# Add current directory to path
sys.path.append('.')

# Import required modules
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import verify_constraints, compute_metrics
from qubo_backend.optimization.solver_router import route_and_solve

# Create a simple test request
test_request = SolverRequest(
    mu=[0.05, 0.08, 0.12, 0.15, 0.20],  # 5 assets
    sigma=[[0.01, 0.002, 0.003, 0.004, 0.005],
            [0.002, 0.003, 0.004, 0.005, 0.006],
            [0.003, 0.004, 0.005, 0.006, 0.007],
            [0.004, 0.005, 0.006, 0.007, 0.008],
            [0.005, 0.006, 0.007, 0.008, 0.009]],
    tickers=['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA'],
    sectors=['tech', 'tech', 'tech', 'tech', 'tech'],
    cardinality=3,
    max_sector_exposure=0.3,
    risk_tolerance=0.5,
    binary_bits=3,
    solver='classical',
    trajectories=10,
    time_limit_seconds=30
)

solvers_to_test = ['classical', 'neal', 'qiskit_qaoa', 'braket_local']
results = {}

async def test_solver(solver_id):
    print(f'\n--- Testing {solver_id} ---')
    start_time = time.perf_counter()
    
    try:
        # Create solver-specific request
        solver_request = test_request.model_copy(update={'solver': solver_id})
        
        # Execute solver
        solution = route_and_solve(solver_request, None)
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # Ensure weights are numpy array
        weights = np.asarray(solution.weights, dtype=float)
        
        # Validate solution
        constraints = verify_constraints(
            weights,
            solver_request.sectors,
            solver_request.cardinality,
            solver_request.max_sector_exposure,
            sector_tolerance=1e-5,
        )
        
        # Ensure all inputs are numpy arrays for compute_metrics
        mu_array = np.asarray(solver_request.mu, dtype=float)
        sigma_array = np.asarray(solver_request.sigma, dtype=float)
        metrics = compute_metrics(weights, mu_array, sigma_array)
        
        results[solver_id] = {
            'status': 'success',
            'actual_solver': solution.metadata.solver,
            'energy': solution.energy,
            'solve_time_ms': elapsed,
            'feasible': constraints['all_satisfied'],
            'selected_assets': int(np.sum(solution.weights > 1e-6)),
            'provider': solution.metadata.provider,
            'backend': solution.metadata.backend_name,
        }
        
        print(f'✅ {solver_id}: SUCCESS')
        print(f'  - actual_solver: {solution.metadata.solver}')
        print(f'  - energy: {solution.energy:.6f}')
        print(f'  - time: {elapsed:.2f}ms')
        print(f'  - feasible: {constraints["all_satisfied"]}')
        print(f'  - assets: {int(np.sum(solution.weights > 1e-6))}')
        
    except Exception as e:
        results[solver_id] = {
            'status': 'error',
            'reason': str(e),
            'energy': None,
            'solve_time_ms': 0,
            'feasible': False,
            'actual_solver': None,
        }
        print(f'❌ {solver_id}: ERROR - {e}')

async def main():
    print('Starting solver execution validation...')
    
    # Test each solver
    for solver_id in solvers_to_test:
        await test_solver(solver_id)
    
    print(f'\n=== EXECUTION SUMMARY ===')
    for solver_id, result in results.items():
        print(f'{solver_id}: {result["status"]}')
        if result['status'] == 'success':
            print(f'  - Energy: {result["energy"]:.6f}')
            print(f'  - Time: {result["solve_time_ms"]:.2f}ms')
            print(f'  - Solver: {result["actual_solver"]}')
        else:
            print(f'  - Error: {result["reason"]}')

if __name__ == '__main__':
    asyncio.run(main())
