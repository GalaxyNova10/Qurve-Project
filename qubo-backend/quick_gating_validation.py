"""Quick validation of the gating Hamiltonian fix.

Runs a focused 5-asset test with classical + neal + BRAKET_LOCAL
to verify the new P_gate = P_card/2 coupling fix improves
feasibility ratios above the 0.25 scientific threshold.
"""
import asyncio
import json
import logging
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark


def _generate_problem(n_assets: int, seed: int = 42) -> dict:
    rng = np.random.RandomState(seed)
    mu = rng.uniform(0.05, 0.20, n_assets).tolist()
    A = rng.randn(n_assets, n_assets) * 0.05
    sigma = (A @ A.T + np.eye(n_assets) * 0.02).tolist()
    tickers = [f"ASSET_{i}" for i in range(n_assets)]
    sector_pool = ["Tech", "Finance", "Health", "Energy", "Retail"]
    sectors = [sector_pool[i % len(sector_pool)] for i in range(n_assets)]
    cardinality = max(2, n_assets // 3)
    return {
        "mu": mu, "sigma": sigma, "tickers": tickers, "sectors": sectors,
        "cardinality": cardinality, "max_sector_exposure": 0.6,
        "risk_tolerance": 1.0, "binary_bits": 2, "trajectories": 100,
    }


async def main():
    print("=" * 60)
    print("GATING HAMILTONIAN FIX — Quick Validation")
    print("=" * 60)

    configs = [
        {"n_assets": 3, "repeats": 5},
    ]
    solvers = ["classical", "neal", "AWS_BRAKET_LOCAL"]

    all_results = []

    for cfg in configs:
        n_assets = cfg["n_assets"]
        repeats = cfg["repeats"]
        problem = _generate_problem(n_assets)
        request = SolverRequest(**problem, benchmark_mode="FAST")

        print(f"\n{'='*60}")
        print(f"TEST: {n_assets} assets, {repeats} repeats, solvers={solvers}")
        print(f"{'='*60}")

        run_data = {"n_assets": n_assets, "runs": []}

        for run_idx in range(repeats):
            print(f"\n--- Run {run_idx+1}/{repeats} ---")
            t0 = time.time()
            try:
                result = await run_benchmark(request, solvers=solvers, timeout_ms=60_000)
                elapsed = time.time() - t0

                for r in result.get("results", []):
                    solver_id = r["solver"]
                    energy = r.get("canonical_energy", 0)
                    feas_raw = r.get("feasible_ratio_raw", 0)
                    sci = r.get("scientific_comparability", False)
                    opt_status = r.get("optimization_status", "unknown")
                    feasible = r.get("feasible", False)

                    print(
                        f"  [{solver_id}] energy={energy:.6f} "
                        f"feasible_ratio={feas_raw:.4f} "
                        f"feasible={feasible} "
                        f"scientific={sci} "
                        f"status={opt_status}")

                    run_data["runs"].append({
                        "run": run_idx,
                        "solver": solver_id,
                        "energy": energy,
                        "feasible_ratio_raw": feas_raw,
                        "scientific": sci,
                        "feasible": feasible,
                        "status": opt_status,
                        "elapsed_ms": elapsed * 1000,
                    })

            except Exception as e:
                print(f"  ERROR: {e}")
                run_data["runs"].append({
                    "run": run_idx, "error": str(e)
                })

        all_results.append(run_data)

    # Summary
    print("\n" + "=" * 60)
    print("GATING FIX VALIDATION SUMMARY")
    print("=" * 60)

    for data in all_results:
        n = data["n_assets"]
        print(f"\n{n} Assets:")
        by_solver = {}
        for r in data["runs"]:
            s = r.get("solver", "error")
            if s not in by_solver:
                by_solver[s] = []
            by_solver[s].append(r)

        for solver, runs in by_solver.items():
            feas_vals = [r.get("feasible_ratio_raw", 0) for r in runs]
            energy_vals = [r.get("energy", 0) for r in runs if r.get("energy")]
            sci_vals = [r.get("scientific", False) for r in runs]
            avg_feas = np.mean(feas_vals) if feas_vals else 0
            avg_energy = np.mean(energy_vals) if energy_vals else 0
            sci_rate = sum(sci_vals) / len(sci_vals) if sci_vals else 0

            status = "OK" if avg_feas >= 0.25 else "FAIL"
            print(
                f"  {solver:20s}: feas_avg={avg_feas:.4f} "
                f"energy_avg={avg_energy:.6f} "
                f"scientific_rate={sci_rate:.0%} "
                f"[{status}]")

    # Save
    out_path = os.path.join(os.path.dirname(__file__), "gating_fix_results.json")
    with open(out_path, "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print(f"\n[SAVED] {out_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
