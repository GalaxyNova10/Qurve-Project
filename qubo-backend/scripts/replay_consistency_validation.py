import asyncio
import numpy as np
from typing import Dict, Any, List
import logging
import json

from qubo_backend.solvers.benchmark import run_benchmark
from qubo_backend.optimization.contracts import SolverRequest

logger = logging.getLogger(__name__)

async def validate_replay_consistency(request: SolverRequest, iterations: int = 3):
    """
    Validates that a deterministic request produces identical outputs across multiple runs.
    """
    print(f"\n[REPLAY_CONSISTENCY_VALIDATION] Starting {iterations} iterations...")
    
    results = []
    for i in range(iterations):
        print(f"  Iteration {i+1}...")
        # Note: In a real system, we'd ensure seeds are fixed in the request
        benchmark_output = await run_benchmark(request)
        results.append(benchmark_output)
        
    # Compare results
    is_consistent = True
    baseline = results[0]
    
    for i in range(1, iterations):
        current = results[i]
        
        # 1. Compare result counts
        if len(current["results"]) != len(baseline["results"]):
            print(f"  [ERROR] Iteration {i+1}: Result count mismatch")
            is_consistent = False
            continue
            
        # 2. Compare per-solver outputs
        for b_res, c_res in zip(baseline["results"], current["results"]):
            solver = b_res["solver"]
            
            # Compare energy
            if b_res["energy"] != c_res["energy"]:
                print(f"  [ERROR] Iteration {i+1} Solver {solver}: Energy mismatch")
                is_consistent = False
                
            # Compare weights
            if not np.array_equal(b_res.get("weights"), c_res.get("weights")):
                print(f"  [ERROR] Iteration {i+1} Solver {solver}: Weights mismatch")
                is_consistent = False
                
            # Compare rankings
            if b_res.get("rank") != c_res.get("rank"):
                print(f"  [ERROR] Iteration {i+1} Solver {solver}: Rank mismatch")
                is_consistent = False

    if is_consistent:
        print("\n[SUCCESS] Replay consistency validated! All iterations produced identical outputs.")
    else:
        print("\n[FAILURE] Replay consistency check failed. Non-deterministic behavior detected.")
        
    return is_consistent

if __name__ == "__main__":
    # Example usage (would be integrated into a larger test suite)
    pass
