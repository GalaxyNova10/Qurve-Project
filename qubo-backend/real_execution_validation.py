#!/usr/bin/env python3
"""
Qurve AI Real Execution Validation - Quantum vs Classical
Tests actual quantum solver execution vs classical fallback
"""

import sys
import time
import logging
import asyncio
import numpy as np
from typing import List, Dict, Any
from collections import defaultdict

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== REAL EXECUTION VALIDATION - QUANTUM VS CLASSICAL ===')

# Add current directory to path
sys.path.append('.')

# Import required modules
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark

def create_test_request() -> SolverRequest:
    """Create a test request for real execution validation."""
    
    return SolverRequest(
        mu=[0.05, 0.08, 0.12, 0.15, 0.20],
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
        solver='auto',  # Let auto select best solver
        trajectories=10,
        time_limit_seconds=30
    )

def analyze_solver_execution(results: List[Dict]) -> Dict[str, Any]:
    """Analyze solver execution to distinguish quantum vs classical."""
    
    analysis = {
        'quantum_solvers': [],
        'classical_solvers': [],
        'hybrid_solvers': [],
        'actual_quantum_execution': False,
        'actual_classical_execution': False,
        'performance_comparison': {},
        'execution_characteristics': {}
    }
    
    for result in results:
        solver_name = result.get('solver', 'unknown')
        actual_solver = result.get('actual_solver', 'unknown')
        status = result.get('status', 'unknown')
        energy = result.get('energy', None)
        solve_time = result.get('solve_time_ms', None)
        provider = result.get('provider', 'unknown')
        backend = result.get('backend', 'unknown')
        
        # Categorize solvers
        if solver_name in ['qiskit_qaoa', 'qiskit_local']:
            analysis['quantum_solvers'].append(result)
        elif solver_name in ['braket', 'braket_local']:
            analysis['quantum_solvers'].append(result)
        elif solver_name in ['neal']:
            analysis['quantum_solvers'].append(result)  # Quantum-inspired
        elif solver_name in ['classical', 'sb']:
            analysis['classical_solvers'].append(result)
        elif solver_name in ['hybrid', 'auto']:
            analysis['hybrid_solvers'].append(result)
        
        # Check for actual quantum execution
        if actual_solver and 'qiskit' in actual_solver.lower():
            analysis['actual_quantum_execution'] = True
            analysis['execution_characteristics']['qiskit'] = {
                'solver': actual_solver,
                'provider': provider,
                'backend': backend,
                'energy': energy,
                'time_ms': solve_time,
                'status': status
            }
        elif actual_solver and 'braket' in actual_solver.lower():
            analysis['actual_quantum_execution'] = True
            analysis['execution_characteristics']['braket'] = {
                'solver': actual_solver,
                'provider': provider,
                'backend': backend,
                'energy': energy,
                'time_ms': solve_time,
                'status': status
            }
        elif actual_solver and 'neal' in actual_solver.lower():
            analysis['actual_quantum_execution'] = True
            analysis['execution_characteristics']['neal'] = {
                'solver': actual_solver,
                'provider': provider,
                'backend': backend,
                'energy': energy,
                'time_ms': solve_time,
                'status': status
            }
        elif actual_solver and 'classical' in actual_solver.lower():
            analysis['actual_classical_execution'] = True
            analysis['execution_characteristics']['classical'] = {
                'solver': actual_solver,
                'provider': provider,
                'backend': backend,
                'energy': energy,
                'time_ms': solve_time,
                'status': status
            }
    
    # Performance comparison
    quantum_results = []
    classical_results = []
    
    for result in results:
        if result.get('status') == 'success' and result.get('energy') is not None:
            actual_solver = result.get('actual_solver', '')
            if any(q in actual_solver.lower() for q in ['qiskit', 'braket', 'neal']):
                quantum_results.append(result)
            elif 'classical' in actual_solver.lower():
                classical_results.append(result)
    
    if quantum_results and classical_results:
        quantum_times = [r['solve_time_ms'] for r in quantum_results]
        classical_times = [r['solve_time_ms'] for r in classical_results]
        quantum_energies = [r['energy'] for r in quantum_results]
        classical_energies = [r['energy'] for r in classical_results]
        
        analysis['performance_comparison'] = {
            'quantum_avg_time': np.mean(quantum_times) if quantum_times else None,
            'classical_avg_time': np.mean(classical_times) if classical_times else None,
            'quantum_avg_energy': np.mean(quantum_energies) if quantum_energies else None,
            'classical_avg_energy': np.mean(classical_energies) if classical_energies else None,
            'time_ratio': np.mean(quantum_times) / np.mean(classical_times) if quantum_times and classical_times else None,
            'energy_ratio': np.mean(quantum_energies) / np.mean(classical_energies) if quantum_energies and classical_energies else None
        }
    
    return analysis

async def run_real_execution_validation():
    """Run real execution validation to verify quantum vs classical execution."""
    
    print("Starting real execution validation...")
    print("This test verifies that quantum solvers actually execute quantum algorithms")
    print("rather than falling back to classical solvers.\n")
    
    # Create test request
    test_request = create_test_request()
    
    print("Running benchmark with auto solver selection...")
    start_time = time.perf_counter()
    
    try:
        # Run benchmark
        result = await run_benchmark(test_request, timeout_ms=30000)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        
        print(f"Benchmark completed in {elapsed:.2f}ms")
        
        # Analyze results
        results = result.get('results', [])
        analysis = analyze_solver_execution(results)
        
        # Print detailed analysis
        print(f"\n=== EXECUTION ANALYSIS ===")
        print(f"Total solver attempts: {len(results)}")
        print(f"Quantum solvers: {len(analysis['quantum_solvers'])}")
        print(f"Classical solvers: {len(analysis['classical_solvers'])}")
        print(f"Hybrid solvers: {len(analysis['hybrid_solvers'])}")
        
        print(f"\n=== QUANTUM EXECUTION VERIFICATION ===")
        print(f"Actual quantum execution detected: {analysis['actual_quantum_execution']}")
        print(f"Actual classical execution detected: {analysis['actual_classical_execution']}")
        
        if analysis['execution_characteristics']:
            print(f"\nExecution characteristics:")
            for solver_type, characteristics in analysis['execution_characteristics'].items():
                print(f"  {solver_type.upper()}:")
                for key, value in characteristics.items():
                    print(f"    {key}: {value}")
        
        print(f"\n=== PERFORMANCE COMPARISON ===")
        perf_comp = analysis['performance_comparison']
        if perf_comp.get('quantum_avg_time') and perf_comp.get('classical_avg_time'):
            print(f"Quantum avg time: {perf_comp['quantum_avg_time']:.2f}ms")
            print(f"Classical avg time: {perf_comp['classical_avg_time']:.2f}ms")
            print(f"Time ratio (quantum/classical): {perf_comp['time_ratio']:.2f}x")
            
            if perf_comp['time_ratio'] > 1:
                print("⚠️  Quantum solvers are slower than classical")
            else:
                print("✅ Quantum solvers are faster than classical")
        
        if perf_comp.get('quantum_avg_energy') and perf_comp.get('classical_avg_energy'):
            print(f"Quantum avg energy: {perf_comp['quantum_avg_energy']:.6f}")
            print(f"Classical avg energy: {perf_comp['classical_avg_energy']:.6f}")
            print(f"Energy ratio (quantum/classical): {perf_comp['energy_ratio']:.4f}")
            
            # Energy comparison (lower is better)
            if perf_comp['energy_ratio'] < 1:
                print("✅ Quantum solvers found better solutions")
            else:
                print("⚠️  Classical solvers found better solutions")
        
        # Check for fallback behavior
        print(f"\n=== FALLBACK ANALYSIS ===")
        fallback_count = 0
        quantum_fallback_count = 0
        
        for result in results:
            if result.get('status') == 'fallback':
                fallback_count += 1
                actual_solver = result.get('actual_solver', '')
                if any(q in result.get('solver', '') for q in ['qiskit', 'braket']):
                    quantum_fallback_count += 1
                    print(f"Quantum solver {result.get('solver')} fell back to {actual_solver}")
        
        print(f"Total fallbacks: {fallback_count}/{len(results)}")
        print(f"Quantum fallbacks: {quantum_fallback_count}")
        
        if quantum_fallback_count > 0:
            print("⚠️  Quantum solvers are falling back to classical")
        else:
            print("✅ Quantum solvers executing independently")
        
        # Real execution assessment
        print(f"\n=== REAL EXECUTION ASSESSMENT ===")
        
        execution_score = 0
        
        # Quantum execution verification (40% weight)
        if analysis['actual_quantum_execution']:
            execution_score += 40
            print("✅ Quantum execution verified (40/40)")
        else:
            print("❌ No quantum execution detected (0/40)")
        
        # Performance comparison (30% weight)
        if perf_comp.get('time_ratio'):
            if perf_comp['time_ratio'] < 5:  # Reasonable time ratio
                execution_score += 30
                print("✅ Reasonable performance ratio (30/30)")
            else:
                execution_score += 15
                print("⚠️  High performance overhead (15/30)")
        else:
            print("❌ No performance comparison possible (0/30)")
        
        # Fallback analysis (30% weight)
        if quantum_fallback_count == 0:
            execution_score += 30
            print("✅ No quantum fallbacks (30/30)")
        else:
            fallback_penalty = max(0, 30 - quantum_fallback_count * 10)
            execution_score += fallback_penalty
            print(f"⚠️  Quantum fallbacks detected ({fallback_penalty}/30)")
        
        print(f"\nReal Execution Score: {execution_score}/100")
        
        # Overall assessment
        if execution_score >= 80:
            print("✅ EXCELLENT: Genuine quantum execution with good performance")
        elif execution_score >= 60:
            print("⚠️  GOOD: Some quantum execution with performance issues")
        elif execution_score >= 40:
            print("❌ POOR: Limited quantum execution, heavy fallback")
        else:
            print("❌ CRITICAL: No quantum execution detected")
        
        return analysis, execution_score
        
    except Exception as e:
        print(f"❌ Real execution validation failed: {e}")
        return None, 0

if __name__ == '__main__':
    asyncio.run(run_real_execution_validation())
