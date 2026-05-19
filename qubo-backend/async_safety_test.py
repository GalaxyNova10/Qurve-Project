#!/usr/bin/env python3
"""
Qurve AI Async + Thread Safety Testing
Tests concurrent request handling, deadlock detection, and event loop health
"""

import sys
import time
import logging
import asyncio
import numpy as np
import psutil
import threading
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

# Configure logging for validation
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

print('=== ASYNC + THREAD SAFETY TESTING ===')

# Add current directory to path
sys.path.append('.')

# Import required modules
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark

def create_test_request(request_id: int) -> SolverRequest:
    """Create a unique test request for concurrent testing."""
    
    # Use different seeds for variety
    np.random.seed(42 + request_id)
    
    num_assets = random.choice([5, 7, 8])  # Vary problem sizes
    mu = np.random.uniform(0.05, 0.15, num_assets).tolist()
    
    # Generate covariance matrix
    base_vol = np.random.uniform(0.01, 0.03, num_assets)
    correlation = np.random.uniform(0.1, 0.5, (num_assets, num_assets))
    correlation = (correlation + correlation.T) / 2
    np.fill_diagonal(correlation, 1.0)
    sigma = np.outer(base_vol, base_vol) * correlation
    sigma = sigma + np.eye(num_assets) * 0.001
    
    tickers = [f'ASSET_{request_id:02d}_{i:02d}' for i in range(num_assets)]
    sectors = ['tech'] * num_assets
    
    return SolverRequest(
        mu=mu,
        sigma=sigma.tolist(),
        tickers=tickers,
        sectors=sectors,
        cardinality=max(2, num_assets // 3),
        max_sector_exposure=0.4,
        risk_tolerance=0.5,
        binary_bits=3,
        solver='classical',  # Use reliable solver for safety testing
        trajectories=5,
        time_limit_seconds=30
    )

async def run_concurrent_test(num_concurrent: int) -> Dict[str, Any]:
    """Run concurrent benchmark tests to check for thread safety issues."""
    
    print(f"\n--- Testing {num_concurrent} concurrent requests ---")
    
    # Create unique requests
    requests = [create_test_request(i) for i in range(num_concurrent)]
    
    # Monitor system resources
    process = psutil.Process()
    memory_before = process.memory_info().rss / 1024 / 1024
    cpu_before = psutil.cpu_percent()
    thread_count_before = threading.active_count()
    
    start_time = time.perf_counter()
    
    # Run all requests concurrently
    tasks = [run_benchmark(req, timeout_ms=30000) for req in requests]
    
    try:
        # Wait for all tasks to complete with timeout
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        elapsed = (time.perf_counter() - start_time) * 1000
        
        # Monitor system resources after
        memory_after = process.memory_info().rss / 1024 / 1024
        cpu_after = psutil.cpu_percent()
        thread_count_after = threading.active_count()
        
        # Analyze results
        successful_results = []
        failed_results = []
        exceptions = []
        
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                exceptions.append({'request_id': i, 'error': str(result)})
                failed_results.append({'request_id': i, 'status': 'exception'})
            elif isinstance(result, dict) and 'results' in result:
                successful_solvers = len([r for r in result['results'] if r['status'] in ('success', 'fallback')])
                total_solvers = len(result['results'])
                
                if successful_solvers > 0:
                    successful_results.append({
                        'request_id': i,
                        'successful_solvers': successful_solvers,
                        'total_solvers': total_solvers,
                        'success_rate': successful_solvers / total_solvers
                    })
                else:
                    failed_results.append({'request_id': i, 'status': 'no_successful_solvers'})
            else:
                failed_results.append({'request_id': i, 'status': 'invalid_result'})
        
        # Check for thread safety issues
        thread_safety_issues = []
        
        # Check for deadlocks (requests taking too long)
        avg_time = elapsed / num_concurrent
        if avg_time > 20000:  # > 20 seconds average
            thread_safety_issues.append(f"Potential deadlock: avg time {avg_time:.2f}ms")
        
        # Check for excessive thread creation
        thread_growth = thread_count_after - thread_count_before
        if thread_growth > num_concurrent * 2:  # More than 2x expected threads
            thread_safety_issues.append(f"Excessive thread creation: {thread_count_before} -> {thread_count_after}")
        
        # Check for memory leaks
        memory_growth = memory_after - memory_before
        if memory_growth > num_concurrent * 50:  # > 50MB per request
            thread_safety_issues.append(f"Potential memory leak: {memory_growth:.2f}MB growth")
        
        # Check for inconsistent results
        if len(successful_results) > 1:
            success_rates = [r['success_rate'] for r in successful_results]
            rate_variance = np.var(success_rates)
            if rate_variance > 0.01:  # High variance in success rates
                thread_safety_issues.append(f"Inconsistent results: success rate variance {rate_variance:.4f}")
        
        test_result = {
            'concurrent_requests': num_concurrent,
            'total_requests': num_concurrent,
            'successful_requests': len(successful_results),
            'failed_requests': len(failed_results),
            'exceptions': len(exceptions),
            'execution_time_ms': elapsed,
            'avg_time_per_request': avg_time,
            'memory_before_mb': memory_before,
            'memory_after_mb': memory_after,
            'memory_growth_mb': memory_growth,
            'cpu_before': cpu_before,
            'cpu_after': cpu_after,
            'thread_count_before': thread_count_before,
            'thread_count_after': thread_count_after,
            'thread_growth': thread_growth,
            'thread_safety_issues': thread_safety_issues,
            'success_rate': len(successful_results) / num_concurrent,
            'successful_results': successful_results,
            'failed_results': failed_results,
            'exceptions': exceptions
        }
        
        # Print summary
        print(f"Completed {num_concurrent} concurrent requests in {elapsed:.2f}ms")
        print(f"Success rate: {len(successful_results)}/{num_concurrent} ({len(successful_results)/num_concurrent*100:.1f}%)")
        print(f"Memory growth: {memory_growth:.2f}MB")
        print(f"Thread growth: {thread_count_before} -> {thread_count_after}")
        
        if thread_safety_issues:
            print(f"⚠️  Thread safety issues detected:")
            for issue in thread_safety_issues:
                print(f"  - {issue}")
        else:
            print("✅ No thread safety issues detected")
        
        return test_result
        
    except asyncio.TimeoutError:
        print(f"❌ TIMEOUT: {num_concurrent} concurrent requests exceeded time limit")
        return {
            'concurrent_requests': num_concurrent,
            'status': 'timeout',
            'execution_time_ms': 30000,
            'thread_safety_issues': ['Timeout exceeded']
        }
    except Exception as e:
        print(f"❌ ERROR: Concurrent test failed: {str(e)}")
        return {
            'concurrent_requests': num_concurrent,
            'status': 'error',
            'error': str(e),
            'thread_safety_issues': ['Test execution error']
        }

async def run_thread_safety_suite():
    """Run comprehensive thread safety tests with varying concurrency levels."""
    
    print("Starting comprehensive async + thread safety testing...")
    
    # Test different concurrency levels
    concurrency_levels = [1, 2, 5, 10, 15]
    
    all_results = []
    
    for concurrency in concurrency_levels:
        print(f"\n{'='*60}")
        print(f"TESTING CONCURRENCY LEVEL: {concurrency}")
        print(f"{'='*60}")
        
        # Run test multiple times for consistency
        test_runs = []
        for run in range(3):  # 3 runs per concurrency level
            print(f"\nRun {run + 1}/3 for {concurrency} concurrent requests...")
            
            result = await run_concurrent_test(concurrency)
            result['run_number'] = run + 1
            test_runs.append(result)
            
            # Small delay between runs
            await asyncio.sleep(1.0)
        
        # Analyze consistency across runs
        if len(test_runs) >= 2:
            success_rates = [r['success_rate'] for r in test_runs if 'success_rate' in r]
            execution_times = [r['execution_time_ms'] for r in test_runs if 'execution_time_ms' in r]
            
            if success_rates and execution_times:
                success_variance = np.var(success_rates)
                time_variance = np.var(execution_times)
                
                print(f"\nConsistency analysis for {concurrency} concurrent requests:")
                print(f"  Success rate variance: {success_variance:.6f}")
                print(f"  Execution time variance: {time_variance:.2f}")
                
                if success_variance > 0.01:
                    print(f"  ⚠️  High variance in success rates")
                else:
                    print(f"  ✅ Consistent success rates")
                
                if time_variance > 1000000:  # High time variance
                    print(f"  ⚠️  High variance in execution times")
                else:
                    print(f"  ✅ Consistent execution times")
        
        all_results.extend(test_runs)
    
    # Overall analysis
    print(f"\n{'='*60}")
    print("THREAD SAFETY ANALYSIS")
    print(f"{'='*60}")
    
    # Analyze scaling with concurrency
    concurrency_analysis = {}
    for result in all_results:
        if 'concurrent_requests' in result:
            concurrency = result['concurrent_requests']
            if concurrency not in concurrency_analysis:
                concurrency_analysis[concurrency] = []
            concurrency_analysis[concurrency].append(result)
    
    print(f"Concurrency Scaling Analysis:")
    for concurrency in sorted(concurrency_analysis.keys()):
        results = concurrency_analysis[concurrency]
        avg_success = np.mean([r['success_rate'] for r in results if 'success_rate' in r])
        avg_time = np.mean([r['execution_time_ms'] for r in results if 'execution_time_ms' in r])
        avg_memory = np.mean([r['memory_growth_mb'] for r in results if 'memory_growth_mb' in r])
        
        print(f"  {concurrency:2d} concurrent: {avg_success*100:.1f}% success, {avg_time:.0f}ms, {avg_memory:.1f}MB memory")
    
    # Check for thread safety issues
    all_issues = []
    for result in all_results:
        if 'thread_safety_issues' in result:
            all_issues.extend(result['thread_safety_issues'])
    
    # Count unique issues
    unique_issues = list(set(all_issues))
    issue_counts = {issue: all_issues.count(issue) for issue in unique_issues}
    
    print(f"\nThread Safety Issues Summary:")
    if unique_issues:
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  {count}x: {issue}")
    else:
        print("  ✅ No thread safety issues detected across all tests")
    
    # Overall assessment
    total_tests = len(all_results)
    successful_tests = len([r for r in all_results if r.get('success_rate', 0) > 0.8])
    overall_success_rate = successful_tests / total_tests if total_tests > 0 else 0
    
    print(f"\n=== THREAD SAFETY ASSESSMENT ===")
    print(f"Total tests: {total_tests}")
    print(f"Successful tests: {successful_tests}")
    print(f"Overall success rate: {overall_success_rate*100:.1f}%")
    print(f"Unique issues: {len(unique_issues)}")
    
    # Calculate safety score
    safety_score = 0
    safety_score += min(overall_success_rate * 50, 50)  # Success rate (50% weight)
    safety_score += max(0, 50 - len(unique_issues) * 10)  # Issue penalty (50% weight)
    
    print(f"Thread Safety Score: {safety_score:.1f}/100")
    
    if safety_score >= 80:
        print("✅ EXCELLENT: Highly thread-safe concurrent execution")
    elif safety_score >= 60:
        print("⚠️  GOOD: Generally thread-safe with minor issues")
    elif safety_score >= 40:
        print("❌ POOR: Significant thread safety issues")
    else:
        print("❌ CRITICAL: Major thread safety problems")
    
    return all_results, safety_score

if __name__ == '__main__':
    asyncio.run(run_thread_safety_suite())
