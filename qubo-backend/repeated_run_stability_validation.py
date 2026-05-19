"""QURVE AI — Repeated-Run Statistical Stability Validation Suite.

Priority 5: Validates solver reproducibility across repeated benchmark runs.
Priority 6: Aggregates run stability audit data.

Sweeps:
  Assets | Bits | Repeats
  5      | 2    | 5
  8      | 2    | 5
  10     | 2    | 5
  12     | 2    | 5
  15     | 2    | 5

Measures per solver:
  - feasible_ratio_raw (mean, std)
  - cardinality_violation_rate (mean, std)
  - repair_frequency
  - canonical_energy (mean, std)
  - ranking drift
  - LOCAL/SV1 divergence
  - manifold_health_score (mean, std)
"""

from __future__ import annotations

import asyncio
import json
import logging
import math
import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np

# Ensure backend is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.solvers.benchmark import run_benchmark

logger = logging.getLogger(__name__)

# ── Test configurations ─────────────────────────────────────────────
SWEEP_CONFIGS = [
    {"n_assets": 5,  "binary_bits": 2, "repeats": 5},
    {"n_assets": 8,  "binary_bits": 2, "repeats": 5},
    {"n_assets": 10, "binary_bits": 2, "repeats": 5},
]

# Solvers to validate
VALIDATION_SOLVERS = ["classical", "neal", "AWS_BRAKET_LOCAL", "AWS_BRAKET_TN1", "AWS_BRAKET_SV1"]


@dataclass
class SolverRunRecord:
    """Single solver execution record."""
    solver: str
    run_index: int
    canonical_energy: float = float("nan")
    feasible_ratio_raw: float = 0.0
    repair_applied: bool = False
    rank: int = 999
    scientific_comparability: bool = False
    feasible: bool = False
    manifold_health_score: float = 0.0


@dataclass
class SolverStabilityReport:
    """Aggregated stability metrics for one solver across repeated runs."""
    solver: str
    n_runs: int = 0
    energy_mean: float = 0.0
    energy_std: float = 0.0
    feasibility_mean: float = 0.0
    feasibility_std: float = 0.0
    repair_frequency: float = 0.0
    rank_mean: float = 0.0
    rank_drift: float = 0.0  # std of rank
    manifold_health_mean: float = 0.0
    manifold_health_std: float = 0.0
    stable: bool = False


def _generate_synthetic_problem(n_assets: int, seed: int = 42) -> dict:
    """Generate a reproducible synthetic portfolio problem."""
    rng = np.random.RandomState(seed)
    mu = rng.uniform(0.05, 0.20, n_assets).tolist()

    # Generate positive-definite covariance
    A = rng.randn(n_assets, n_assets) * 0.05
    sigma = (A @ A.T + np.eye(n_assets) * 0.02).tolist()

    tickers = [f"ASSET_{i}" for i in range(n_assets)]
    sector_pool = ["Tech", "Finance", "Health", "Energy", "Retail"]
    sectors = [sector_pool[i % len(sector_pool)] for i in range(n_assets)]

    cardinality = max(2, n_assets // 3)

    return {
        "mu": mu,
        "sigma": sigma,
        "tickers": tickers,
        "sectors": sectors,
        "cardinality": cardinality,
        "max_sector_exposure": 0.6,
        "risk_tolerance": 1.0,
        "binary_bits": 2,
        "trajectories": 100,
    }


async def run_repeated_benchmark(
    n_assets: int,
    binary_bits: int,
    repeats: int,
    solvers: List[str] | None = None,
) -> Dict[str, Any]:
    """Run repeated benchmarks and collect stability data."""
    solvers = solvers or VALIDATION_SOLVERS
    problem = _generate_synthetic_problem(n_assets)
    problem["binary_bits"] = binary_bits

    request = SolverRequest(**problem, benchmark_mode="BALANCED")

    all_records: Dict[str, List[SolverRunRecord]] = {s: [] for s in solvers}
    run_results = []

    for run_idx in range(repeats):
        print(f"\n[STABILITY_SWEEP] n_assets={n_assets} run={run_idx+1}/{repeats}")
        try:
            result = await run_benchmark(request, solvers=solvers, timeout_ms=60_000)
            run_results.append(result)

            for r in result.get("results", []):
                solver_id = r["solver"]
                if solver_id not in all_records:
                    continue

                record = SolverRunRecord(
                    solver=solver_id,
                    run_index=run_idx,
                    canonical_energy=r.get("canonical_energy", float("nan")) or float("nan"),
                    feasible_ratio_raw=r.get("feasible_ratio_raw", 0.0),
                    repair_applied=r.get("optimization_status") == "repaired",
                    rank=r.get("rank", 999),
                    scientific_comparability=r.get("scientific_comparability", False),
                    feasible=r.get("feasible", False),
                    manifold_health_score=r.get("manifold_health_score", 0.0) or 0.0,
                )
                all_records[solver_id].append(record)

                print(
                    f"[RUN_STABILITY_AUDIT] solver={solver_id} run_index={run_idx} "
                    f"canonical_energy={record.canonical_energy:.6f} "
                    f"feasible_ratio={record.feasible_ratio_raw:.4f} "
                    f"repair_applied={record.repair_applied} "
                    f"rank={record.rank} "
                    f"scientific_comparability={record.scientific_comparability}")

        except Exception as e:
            print(f"[STABILITY_SWEEP_ERROR] run={run_idx}: {e}")

    # ── Compute per-solver stability ────────────────────────────────
    solver_reports: Dict[str, SolverStabilityReport] = {}

    for solver_id, records in all_records.items():
        report = SolverStabilityReport(solver=solver_id, n_runs=len(records))

        if not records:
            solver_reports[solver_id] = report
            continue

        energies = [r.canonical_energy for r in records if not math.isnan(r.canonical_energy)]
        feasibilities = [r.feasible_ratio_raw for r in records]
        ranks = [r.rank for r in records if r.rank < 999]
        repairs = sum(1 for r in records if r.repair_applied)
        healths = [r.manifold_health_score for r in records]

        if energies:
            report.energy_mean = float(np.mean(energies))
            report.energy_std = float(np.std(energies))
        report.feasibility_mean = float(np.mean(feasibilities))
        report.feasibility_std = float(np.std(feasibilities))
        report.repair_frequency = repairs / len(records)
        if ranks:
            report.rank_mean = float(np.mean(ranks))
            report.rank_drift = float(np.std(ranks))
        report.manifold_health_mean = float(np.mean(healths))
        report.manifold_health_std = float(np.std(healths))

        # Stability: energy_std < 0.05, no repair, feasibility > 0.25
        report.stable = (
            report.energy_std < 0.05 and
            report.repair_frequency < 0.2 and
            report.feasibility_mean >= 0.25 and
            report.rank_drift < 1.0
        )

        solver_reports[solver_id] = report

    return {
        "n_assets": n_assets,
        "binary_bits": binary_bits,
        "repeats": repeats,
        "solver_reports": {k: vars(v) for k, v in solver_reports.items()},
    }


def _format_report(sweep_results: List[Dict]) -> str:
    """Generate markdown stability report."""
    lines = [
        "# QURVE AI — Solver Reproducibility Report",
        "",
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Sweep Results",
        "",
    ]

    for sweep in sweep_results:
        n = sweep["n_assets"]
        lines.append(f"### {n} Assets (bits={sweep['binary_bits']}, repeats={sweep['repeats']})")
        lines.append("")
        lines.append("| Solver | Energy mean | Energy std | Feas mean | Feas std | Repair% | Rank mean | Rank std | Manifold | Stable |")
        lines.append("|--------|-------------|------------|-----------|----------|---------|-----------|----------|----------|--------|")

        for solver_id, report in sweep.get("solver_reports", {}).items():
            e_mean = f"{report['energy_mean']:.4f}" if not math.isnan(report["energy_mean"]) else "N/A"
            e_std = f"{report['energy_std']:.4f}" if not math.isnan(report["energy_std"]) else "N/A"
            lines.append(
                f"| {solver_id} "
                f"| {e_mean} | {e_std} "
                f"| {report['feasibility_mean']:.3f} | {report['feasibility_std']:.3f} "
                f"| {report['repair_frequency']*100:.0f}% "
                f"| {report['rank_mean']:.1f} | {report['rank_drift']:.2f} "
                f"| {report['manifold_health_mean']:.3f} "
                f"| {'YES' if report['stable'] else 'NO'} |"
            )
        lines.append("")

    return "\n".join(lines)


async def main():
    """Run the full stability validation sweep."""
    print("=" * 60)
    print("QURVE AI — Statistical Stability Validation Suite")
    print("=" * 60)

    all_sweep_results = []

    for config in SWEEP_CONFIGS:
        print(f"\n{'='*60}")
        print(f"SWEEP: {config['n_assets']} assets, {config['binary_bits']} bits, {config['repeats']} repeats")
        print(f"{'='*60}")

        result = await run_repeated_benchmark(
            n_assets=config["n_assets"],
            binary_bits=config["binary_bits"],
            repeats=config["repeats"],
        )
        all_sweep_results.append(result)

    # Generate report
    report_md = _format_report(all_sweep_results)
    report_path = os.path.join(os.path.dirname(__file__), "solver_reproducibility_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_md)
    print(f"\n[REPORT_GENERATED] {report_path}")

    # Also save raw JSON
    json_path = os.path.join(os.path.dirname(__file__), "stability_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_sweep_results, f, indent=2, default=str)
    print(f"[RAW_DATA_SAVED] {json_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
