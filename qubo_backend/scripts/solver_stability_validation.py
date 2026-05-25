import time
import asyncio
import numpy as np
from scipy import stats
from typing import Dict, Any, List
import logging

from qubo_backend.solvers.benchmark import run_benchmark
from qubo_backend.optimization.contracts import SolverRequest

logger = logging.getLogger(__name__)

class SolverStabilityValidator:
    """
    Statistically characterizes solver behavior over multiple runs.
    Decouples Operational vs Optimization metrics.
    """
    
    def __init__(self, iterations: int = 20):
        self.iterations = iterations
        self.operational_results = []
        self.optimization_results = []

    async def run_suite(self, request: SolverRequest):
        print(f"\n[STABILITY_VALIDATION] Starting {self.iterations} iterations...")
        
        for i in range(self.iterations):
            start_wall = time.perf_counter()
            result = await run_benchmark(request)
            end_wall = time.perf_counter()
            
            for res in result.get("results", []):
                # 1. Operational Metrics
                self.operational_results.append({
                    "solver": res["solver"],
                    "latency_ms": res.get("solve_time_ms", 0),
                    "wall_ms": (end_wall - start_wall) * 1000,
                    "status": res["status"]
                })
                
                # 2. Optimization Metrics
                if res["status"] in ["success", "fallback"]:
                    self.optimization_results.append({
                        "solver": res["solver"],
                        "feasible": res.get("feasible", False),
                        "energy": res.get("energy", 0),
                        "approx_ratio": res.get("approximation_ratio", 0),
                        "card_dev": res.get("cardinality_deviation", 0)
                    })
            
            print(f"  Iteration {i+1}/{self.iterations} complete.")

    def compute_statistics(self, data: List[float]) -> Dict[str, float]:
        if not data:
            return {}
        arr = np.array(data)
        return {
            "mean": float(np.mean(arr)),
            "std": float(np.std(arr)),
            "p50": float(np.percentile(arr, 50)),
            "p95": float(np.percentile(arr, 95)),
            "p99": float(np.percentile(arr, 99)),
            "conf_int": stats.t.interval(0.95, len(arr)-1, loc=np.mean(arr), scale=stats.sem(arr)) if len(arr) > 1 else (0, 0)
        }

    def generate_report(self) -> str:
        report = ["# Statistical Stability Report", ""]
        
        solvers = list(set([r["solver"] for r in self.operational_results]))
        
        for solver in solvers:
            report.append(f"## Solver: {solver}")
            
            # Operational Stats
            latencies = [r["latency_ms"] for r in self.operational_results if r["solver"] == solver]
            op_stats = self.compute_statistics(latencies)
            
            report.append("### Operational Metrics (Latency)")
            report.append(f"- Mean: {op_stats.get('mean', 0):.2f} ms")
            report.append(f"- P50: {op_stats.get('p50', 0):.2f} ms")
            report.append(f"- P95: {op_stats.get('p95', 0):.2f} ms")
            report.append(f"- P99: {op_stats.get('p99', 0):.2f} ms")
            report.append(f"- 95% CI: [{op_stats.get('conf_int', (0,0))[0]:.2f}, {op_stats.get('conf_int', (0,0))[1]:.2f}]")
            
            # Optimization Stats
            ratios = [r["approx_ratio"] for r in self.optimization_results if r["solver"] == solver]
            opt_stats = self.compute_statistics(ratios)
            
            if opt_stats:
                report.append("### Optimization Metrics (Approx Ratio)")
                report.append(f"- Mean: {opt_stats.get('mean', 0):.4f}")
                report.append(f"- Std Dev: {opt_stats.get('std', 0):.4f}")
                report.append(f"- Feasible Rate: {len([r for r in self.optimization_results if r['solver'] == solver and r['feasible']]) / len(latencies) * 100:.1f}%")
            
            report.append("")
            
        return "\n".join(report)

if __name__ == "__main__":
    pass
