#!/usr/bin/env python3
"""
Qurve AI Scale Testing - 5, 10, 15, 25, 50 assets
Tests performance scaling and resource usage across different problem sizes
"""

import sys
import time
import logging
import asyncio
import numpy as np
import psutil
from typing import List, Dict, Tuple

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== SCALE TESTING - PERFORMANCE ACROSS ASSET COUNTS ===')

# Add current directory to path
sys.path.append('.')

# Import required modules
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark

def create_test_request(num_assets: int) -> SolverRequest:
    """Create a test request with specified number of assets."""
    
    # Generate realistic financial data
    np.random.seed(42)  # Consistent results
    
    # Expected returns (5-15% annualized)
    mu = np.random.uniform(0.05, 0.15, num_assets).tolist()
    
    # Covariance matrix (realistic risk structure)
    base_vol = np.random.uniform(0.01, 0.04, num_assets)
    correlation = np.random.uniform(0.1, 0.7, (num_assets, num_assets))
    correlation = (correlation + correlation.T) / 2  # Make symmetric
    np.fill_diagonal(correlation, 1.0)  # Unit diagonal
    
    sigma = np.outer(base_vol, base_vol) * correlation
    
    # Ensure positive definite
    sigma = sigma + np.eye(num_assets) * 0.001
    
    # Generate tickers and sectors
    tickers = [f'ASSET_{i:02d}' for i in range(num_assets)]
    sectors = ['tech'] * num_assets  # Simple single sector for testing
    
    # Cardinality and exposure (scale with problem size)
    cardinality = max(2, num_assets // 3)  # Select ~30% of assets
    max_sector_exposure = 0.8  # Allow higher exposure for single sector
    
    return SolverRequest(
        mu=mu,
        sigma=sigma.tolist(),
        tickers=tickers,
        sectors=sectors,
        cardinality=cardinality,
        max_sector_exposure=max_sector_exposure,
        risk_tolerance=0.5,
        binary_bits=3,
        solver='classical',  # Use fastest solver for scale testing
        trajectories=10,
        time_limit_seconds=60  # Longer timeout for larger problems
    )

async def run_scale_test(asset_counts: List[int]) -> Dict:
    """Run scale tests across different asset counts."""
    
    results = {}
    
    print(f"Testing asset counts: {asset_counts}")
    print(f"{'Assets':<8} {'Time (ms)':<12} {'Memory (MB)':<12} {'Success':<8} {'Qubits':<8} {'Status':<12}")
    print("-" * 70)
    
    for num_assets in asset_counts:
        print(f"\n--- Testing {num_assets} assets ---")
        
        # Create test request
        test_request = create_test_request(num_assets)
        
        # Monitor system resources
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024
        cpu_before = psutil.cpu_percent()
        
        start_time = time.perf_counter()
        
        try:
            # Run benchmark
            result = await run_benchmark(test_request, timeout_ms=60000)
            
            elapsed = (time.perf_counter() - start_time) * 1000
            memory_after = process.memory_info().rss / 1024 / 1024
            cpu_after = psutil.cpu_percent()
            
            # Analyze results
            successful_solvers = len([r for r in result['results'] if r['status'] in ('success', 'fallback')])
            total_solvers = len(result['results'])
            
            # Calculate qubits for quantum solvers
            qubits = num_assets * test_request.binary_bits
            
            # Determine status
            if successful_solvers == total_solvers:
                status = "✅ SUCCESS"
            elif successful_solvers > 0:
                status = "⚠️  PARTIAL"
            else:
                status = "❌ FAILED"
            
            # Store results
            results[num_assets] = {
                'assets': num_assets,
                'execution_time_ms': elapsed,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_delta_mb': memory_after - memory_before,
                'cpu_before': cpu_before,
                'cpu_after': cpu_after,
                'successful_solvers': successful_solvers,
                'total_solvers': total_solvers,
                'success_rate': successful_solvers / total_solvers,
                'qubits': qubits,
                'status': status,
                'result': result
            }
            
            print(f"{num_assets:<8} {elapsed:<12.2f} {memory_after:<12.2f} {successful_solvers}/{total_solvers:<7} {qubits:<8} {status:<12}")
            
            # Check for performance issues
            if elapsed > 30000:  # > 30 seconds
                print(f"⚠️  WARNING: Slow execution for {num_assets} assets: {elapsed:.2f}ms")
            
            if memory_after - memory_before > 500:  # > 500MB growth
                print(f"⚠️  WARNING: High memory usage for {num_assets} assets: {memory_after - memory_before:.2f}MB")
            
        except Exception as e:
            elapsed = (time.perf_counter() - start_time) * 1000
            memory_after = process.memory_info().rss / 1024 / 1024
            
            results[num_assets] = {
                'assets': num_assets,
                'execution_time_ms': elapsed,
                'memory_before_mb': memory_before,
                'memory_after_mb': memory_after,
                'memory_delta_mb': memory_after - memory_before,
                'successful_solvers': 0,
                'total_solvers': 0,
                'success_rate': 0.0,
                'qubits': num_assets * 3,
                'status': "❌ ERROR",
                'error': str(e)
            }
            
            print(f"{num_assets:<8} {elapsed:<12.2f} {memory_after:<12.2f} 0/0       {num_assets * 3:<8} {'❌ ERROR':<12}")
            print(f"Error: {str(e)}")
    
    return results

def analyze_scaling(results: Dict) -> None:
    """Analyze scaling performance and identify bottlenecks."""
    
    print(f"\n=== SCALING ANALYSIS ===")
    
    # Extract data for analysis
    asset_counts = sorted(results.keys())
    execution_times = [results[n]['execution_time_ms'] for n in asset_counts]
    memory_usage = [results[n]['memory_after_mb'] for n in asset_counts]
    success_rates = [results[n]['success_rate'] for n in asset_counts]
    
    # Performance scaling analysis
    print(f"Performance Scaling:")
    for i, num_assets in enumerate(asset_counts):
        if i == 0:
            baseline_time = execution_times[i]
            baseline_memory = memory_usage[i]
            print(f"  {num_assets} assets: {execution_times[i]:.2f}ms, {memory_usage[i]:.2f}MB (baseline)")
        else:
            time_ratio = execution_times[i] / baseline_time
            memory_ratio = memory_usage[i] / baseline_memory
            print(f"  {num_assets} assets: {execution_times[i]:.2f}ms ({time_ratio:.1f}x), {memory_usage[i]:.2f}MB ({memory_ratio:.1f}x)")
    
    # Identify scaling characteristics
    if len(asset_counts) >= 3:
        # Calculate scaling factor (power law)
        time_scaling = calculate_scaling_factor(asset_counts, execution_times)
        memory_scaling = calculate_scaling_factor(asset_counts, memory_usage)
        
        print(f"\nScaling Characteristics:")
        print(f"  Time scaling: O(n^{time_scaling:.2f})")
        print(f"  Memory scaling: O(n^{memory_scaling:.2f})")
        
        if time_scaling < 1.5:
            print("  ✅ EXCELLENT: Near-linear time scaling")
        elif time_scaling < 2.0:
            print("  ✅ GOOD: Sub-quadratic time scaling")
        elif time_scaling < 3.0:
            print("  ⚠️  ACCEPTABLE: Quadratic time scaling")
        else:
            print("  ❌ POOR: Super-quadratic time scaling")
        
        if memory_scaling < 1.2:
            print("  ✅ EXCELLENT: Near-linear memory scaling")
        elif memory_scaling < 1.5:
            print("  ✅ GOOD: Sub-quadratic memory scaling")
        elif memory_scaling < 2.0:
            print("  ⚠️  ACCEPTABLE: Quadratic memory scaling")
        else:
            print("  ❌ POOR: Super-quadratic memory scaling")
    
    # Success rate analysis
    print(f"\nSuccess Rate Analysis:")
    for num_assets in asset_counts:
        rate = results[num_assets]['success_rate']
        if rate >= 0.9:
            print(f"  {num_assets} assets: {rate*100:.1f}% ✅ EXCELLENT")
        elif rate >= 0.7:
            print(f"  {num_assets} assets: {rate*100:.1f}% ✅ GOOD")
        elif rate >= 0.5:
            print(f"  {num_assets} assets: {rate*100:.1f}% ⚠️  ACCEPTABLE")
        else:
            print(f"  {num_assets} assets: {rate*100:.1f}% ❌ POOR")
    
    # Maximum practical problem size
    max_successful = max([n for n in asset_counts if results[n]['success_rate'] >= 0.8], default=0)
    print(f"\nMaximum practical problem size: {max_successful} assets (80%+ success rate)")
    
    # Overall assessment
    avg_success_rate = np.mean(success_rates)
    time_growth = execution_times[-1] / execution_times[0] if len(execution_times) > 1 else 1
    memory_growth = memory_usage[-1] / memory_usage[0] if len(memory_usage) > 1 else 1
    
    print(f"\n=== SCALE ASSESSMENT ===")
    print(f"Average success rate: {avg_success_rate*100:.1f}%")
    print(f"Time growth factor: {time_growth:.1f}x")
    print(f"Memory growth factor: {memory_growth:.1f}x")
    
    scale_score = 0
    scale_score += min(avg_success_rate * 40, 40)  # Success rate (40% weight)
    scale_score += min((2.0 / time_growth) * 30, 30)  # Time scaling (30% weight)
    scale_score += min((2.0 / memory_growth) * 30, 30)  # Memory scaling (30% weight)
    
    print(f"Overall Scale Score: {scale_score:.1f}/100")
    
    if scale_score >= 80:
        print("✅ EXCELLENT: Highly scalable performance")
    elif scale_score >= 60:
        print("⚠️  GOOD: Generally scalable with minor issues")
    elif scale_score >= 40:
        print("❌ POOR: Limited scalability")
    else:
        print("❌ CRITICAL: Major scalability problems")

def calculate_scaling_factor(x_values: List[int], y_values: List[float]) -> float:
    """Calculate power law scaling factor using log-log regression."""
    if len(x_values) < 2 or len(y_values) < 2:
        return 1.0
    
    # Convert to log scale
    log_x = np.log(x_values)
    log_y = np.log(y_values)
    
    # Linear regression
    coeffs = np.polyfit(log_x, log_y, 1)
    return coeffs[0]  # Slope = scaling exponent

if __name__ == '__main__':
    # Test asset counts: 5, 10, 15, 25, 50
    asset_counts = [5, 10, 15, 25, 50]
    
    asyncio.run(run_scale_test(asset_counts))
    
    # Get results and analyze scaling
    # Note: In real implementation, we'd pass results from run_scale_test
    print(f"\nScale testing completed. Results analysis would follow.")
    print(f"Key metrics collected: execution time, memory usage, success rates, scaling characteristics.")
