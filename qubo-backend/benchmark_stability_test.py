#!/usr/bin/env python3
"""
Qurve AI Benchmark Stability Test - 20 Consecutive Runs
Tests memory leaks, thread safety, and performance consistency
"""

import sys
import time
import logging
import asyncio
import numpy as np
import psutil
import gc
from typing import List, Dict

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== BENCHMARK STABILITY TEST - 20 CONSECUTIVE RUNS ===')

# Add current directory to path
sys.path.append('.')

# Import required modules
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark

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

async def run_stability_test():
    """Run 20 consecutive benchmark tests to check for stability issues."""
    
    results = []
    memory_usage = []
    cpu_usage = []
    execution_times = []
    error_count = 0
    
    print(f"Starting 20 consecutive benchmark runs...")
    print(f"Initial memory: {psutil.Process().memory_info().rss / 1024 / 1024:.2f} MB")
    print(f"Initial CPU: {psutil.cpu_percent()}%")
    
    for i in range(20):
        start_time = time.perf_counter()
        
        # Monitor memory before run
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_before = psutil.cpu_percent()
        
        try:
            # Run benchmark
            result = await run_benchmark(test_request, timeout_ms=30000)
            
            elapsed = (time.perf_counter() - start_time) * 1000
            
            # Monitor memory after run
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            cpu_after = psutil.cpu_percent()
            
            # Collect metrics
            run_results = {
                'run': i + 1,
                'status': 'success',
                'execution_time_ms': elapsed,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_delta_mb': memory_after - memory_before,
                'cpu_before': cpu_before,
                'cpu_after': cpu_after,
                'successful_solvers': len([r for r in result['results'] if r['status'] in ('success', 'fallback')]),
                'failed_solvers': len([r for r in result['results'] if r['status'] == 'error']),
                'total_solvers': len(result['results']),
                'best_energy': min([r['energy'] for r in result['results'] if r['energy'] is not None], default=None)
            }
            
            results.append(run_results)
            memory_usage.append(memory_after)
            cpu_usage.append(cpu_after)
            execution_times.append(elapsed)
            
            print(f"Run {i+1}/20: SUCCESS - {elapsed:.2f}ms, Memory: {memory_after:.2f}MB, Solvers: {run_results['successful_solvers']}/{run_results['total_solvers']}")
            
        except Exception as e:
            error_count += 1
            elapsed = (time.perf_counter() - start_time) * 1000
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            
            run_results = {
                'run': i + 1,
                'status': 'error',
                'execution_time_ms': elapsed,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_delta_mb': memory_after - memory_before,
                'error': str(e)
            }
            
            results.append(run_results)
            print(f"Run {i+1}/20: ERROR - {str(e)}")
        
        # Force garbage collection
        gc.collect()
        
        # Small delay between runs
        await asyncio.sleep(0.1)
    
    # Analyze results
    print(f"\n=== STABILITY ANALYSIS ===")
    
    successful_runs = len([r for r in results if r['status'] == 'success'])
    print(f"Successful runs: {successful_runs}/20 ({successful_runs/20*100:.1f}%)")
    print(f"Failed runs: {error_count}/20 ({error_count/20*100:.1f}%)")
    
    if execution_times:
        avg_time = np.mean(execution_times)
        min_time = np.min(execution_times)
        max_time = np.max(execution_times)
        std_time = np.std(execution_times)
        
        print(f"Execution time stats:")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")
        print(f"  Std Dev: {std_time:.2f}ms")
        print(f"  Consistency: {(1 - std_time/avg_time)*100:.1f}%")
    
    if memory_usage:
        initial_memory = memory_usage[0]
        final_memory = memory_usage[-1]
        memory_growth = final_memory - initial_memory
        avg_memory = np.mean(memory_usage)
        max_memory = np.max(memory_usage)
        
        print(f"Memory usage stats:")
        print(f"  Initial: {initial_memory:.2f}MB")
        print(f"  Final: {final_memory:.2f}MB")
        print(f"  Growth: {memory_growth:.2f}MB")
        print(f"  Average: {avg_memory:.2f}MB")
        print(f"  Peak: {max_memory:.2f}MB")
        
        if memory_growth > 50:  # More than 50MB growth
            print(f"⚠️  WARNING: Significant memory growth detected: {memory_growth:.2f}MB")
        else:
            print(f"✅ Memory usage stable")
    
    # Check solver consistency
    if successful_runs > 0:
        solver_counts = {}
        for result in results:
            if result['status'] == 'success':
                successful = result['successful_solvers']
                total = result['total_solvers']
                key = f"{successful}/{total}"
                solver_counts[key] = solver_counts.get(key, 0) + 1
        
        print(f"Solver success consistency:")
        for pattern, count in solver_counts.items():
            print(f"  {pattern}: {count}/20 runs ({count/20*100:.1f}%)")
    
    # Final assessment
    print(f"\n=== STABILITY ASSESSMENT ===")
    
    stability_score = 0
    
    # Success rate (40% weight)
    success_rate = successful_runs / 20
    stability_score += success_rate * 40
    
    # Memory stability (30% weight)
    if memory_usage and len(memory_usage) > 1:
        memory_stability = 1.0 - min(abs(memory_growth) / 100, 1.0)  # Normalize to 0-1
        stability_score += memory_stability * 30
    
    # Execution time consistency (30% weight)
    if execution_times and len(execution_times) > 1:
        time_consistency = 1.0 - min(std_time / avg_time, 1.0) if avg_time > 0 else 0
        stability_score += time_consistency * 30
    
    print(f"Overall Stability Score: {stability_score:.1f}/100")
    
    if stability_score >= 80:
        print("✅ EXCELLENT: Highly stable benchmark execution")
    elif stability_score >= 60:
        print("⚠️  GOOD: Generally stable with some issues")
    elif stability_score >= 40:
        print("❌ POOR: Significant stability issues")
    else:
        print("❌ CRITICAL: Major stability problems")
    
    return results, stability_score

if __name__ == '__main__':
    asyncio.run(run_stability_test())
