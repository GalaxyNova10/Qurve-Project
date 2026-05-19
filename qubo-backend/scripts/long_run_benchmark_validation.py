import os
import psutil
import asyncio
import time
from typing import Dict, Any, List
import logging

from qubo_backend.solvers.benchmark import run_benchmark
from qubo_backend.optimization.contracts import SolverRequest

logger = logging.getLogger(__name__)

async def run_stability_stress_test(request: SolverRequest, iterations: int = 20):
    """
    Stress tests the backend by running multiple benchmark sessions and monitoring leaks.
    """
    process = psutil.Process(os.getpid())
    baseline_mem = process.memory_info().rss / 1024 / 1024
    
    print(f"\n[STABILITY_STRESS_TEST] Starting {iterations} sessions...")
    print(f"Baseline Memory: {baseline_mem:.2f} MB")
    
    stats = []
    
    for i in range(iterations):
        start_time = time.perf_counter()
        
        # Run session
        await run_benchmark(request)
        
        end_time = time.perf_counter()
        current_mem = process.memory_info().rss / 1024 / 1024
        active_tasks = len(asyncio.all_tasks())
        
        stats.append({
            "iteration": i + 1,
            "memory_mb": current_mem,
            "tasks": active_tasks,
            "duration_s": end_time - start_time
        })
        
        print(f"  [{i+1}/{iterations}] Memory: {current_mem:.2f} MB (+{current_mem - baseline_mem:.2f}) Tasks: {active_tasks}")
        
    # Analysis
    final_mem = process.memory_info().rss / 1024 / 1024
    mem_growth = final_mem - baseline_mem
    
    print(f"\n[STABILITY_REPORT]")
    print(f"Final Memory: {final_mem:.2f} MB")
    print(f"Total Growth: {mem_growth:.2f} MB")
    
    if mem_growth > 50: # Arbitrary 50MB threshold for 20 runs
        print("[WARNING] Significant memory growth detected. Potential leak.")
    else:
        print("[SUCCESS] Memory stability within acceptable bounds.")
        
    return stats

if __name__ == "__main__":
    pass
