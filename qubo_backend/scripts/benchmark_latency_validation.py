import time
import asyncio
import numpy as np
from typing import Dict, Any, List
import logging

from qubo_backend.solvers.benchmark import run_benchmark
from qubo_backend.optimization.contracts import SolverRequest

logger = logging.getLogger(__name__)

class BenchmarkLatencyCharacterizer:
    """
    Measures and classifies latency across the full quantum-classical pipeline.
    """
    
    def __init__(self):
        self.measurements = []

    async def measure_run(self, request: SolverRequest):
        start_wall = time.perf_counter()
        
        # Run benchmark
        result = await run_benchmark(request)
        
        end_wall = time.perf_counter()
        total_wall_ms = (end_wall - start_wall) * 1000
        
        # Extract internal solver times
        for solver_res in result.get("results", []):
            solve_time = solver_res.get("solve_time_ms", 0)
            solver_id = solver_res.get("solver")
            
            # Classification
            if solve_time < 1000:
                tier = "PRODUCTION_FAST"
            elif solve_time < 10000:
                tier = "INTERACTIVE"
            else:
                tier = "RESEARCH_GRADE"
                
            self.measurements.append({
                "solver": solver_id,
                "solve_time_ms": solve_time,
                "total_wall_ms": total_wall_ms,
                "overhead_ms": total_wall_ms - solve_time,
                "tier": tier
            })
            
        return result

    def generate_report(self) -> str:
        report = ["# Benchmark Latency Characterization Report", ""]
        report.append("| Solver | Solve Time (ms) | Wall Time (ms) | Overhead (ms) | Performance Tier |")
        report.append("| :--- | :--- | :--- | :--- | :--- |")
        
        for m in self.measurements:
            report.append(f"| {m['solver']} | {m['solve_time_ms']:.2f} | {m['total_wall_ms']:.2f} | {m['overhead_ms']:.2f} | {m['tier']} |")
            
        return "\n".join(report)

if __name__ == "__main__":
    # Integration point for validation suite
    pass
