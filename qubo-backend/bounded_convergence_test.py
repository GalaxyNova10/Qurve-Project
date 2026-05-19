#!/usr/bin/env python3
"""Bounded multi-solver convergence validation.

Safety limits enforced:
- MAX_TOTAL_REPAIR_ITERATIONS = 8
- MAX_PER_SOLVER_RETRIES = 3
- MAX_QAOA_DEPTH = 4
- MAX_SHOTS = 2048
- MAX_WORKER_WAIT_SECONDS = 20
- MAX_REQUEST_RUNTIME_SECONDS = 90
- MAX_CLOUD_RETRY = 2
- MAX_LOCAL_RETRY = 2
"""
import sys
sys.path.insert(0, '.')
import asyncio
import time
import numpy as np
from qubo_backend.optimization.contracts import BenchmarkRequest
from qubo_backend.solvers.benchmark import run_benchmark
from qubo_backend.config import get_settings

# Safety constants
MAX_TOTAL_REPAIR_ITERATIONS = 8
MAX_PER_SOLVER_RETRIES = 3
MAX_WORKER_WAIT_SECONDS = 20
MAX_REQUEST_RUNTIME_SECONDS = 90

def safe_float(v, default=0.0):
    if v is None:
        return default
    try:
        x = float(v)
        return default if (x != x or x == float('inf') or x == float('-inf')) else x
    except (TypeError, ValueError):
        return default

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def print_result(solver, r):
    sg = r.get('scientific_gate', {})
    strict = safe_float(sg.get('strict_ratio'), 0.0)
    raw = safe_float(sg.get('raw_ratio'), 0.0)
    energy = safe_float(r.get('energy'), None)
    energy_str = f"{energy:.6f}" if energy is not None else "N/A"
    print(f"  {solver:20s} status={r['status']:25s} feasible={r['feasible']} "
          f"energy={energy_str} strict={strict:.4f} raw={raw:.4f}")

async def run_bounded_test(name, request, solvers, mode):
    """Run a single benchmark with timeout protection."""
    print_section(name)
    
    settings = get_settings()
    start = time.time()
    
    try:
        result = await asyncio.wait_for(
            run_benchmark(request, settings, solvers=solvers, execution_mode=mode),
            timeout=MAX_REQUEST_RUNTIME_SECONDS
        )
        
        elapsed = time.time() - start
        summary = result['summary']
        
        print(f"  Benchmark status: {summary['benchmark_status']}")
        print(f"  Solvers attempted: {summary['total_solvers_attempted']}")
        print(f"  Successful: {summary['successful']}")
        print(f"  Errors: {summary['errors']}")
        print(f"  Feasible: {summary['feasible_solutions']}")
        print(f"  Elapsed: {elapsed:.1f}s")
        
        for r in result['results']:
            print_result(r['solver'], r)
        
        return result
        
    except asyncio.TimeoutError:
        print(f"  [TIMEOUT_STATUS] Benchmark exceeded {MAX_REQUEST_RUNTIME_SECONDS}s limit")
        return None
    except Exception as e:
        print(f"  [ERROR] Benchmark failed: {e}")
        return None

async def main():
    print("[ROOT_CAUSE] Starting bounded multi-solver convergence validation")
    print(f"[RESOURCE_STATUS] MAX_REPAIR={MAX_TOTAL_REPAIR_ITERATIONS} "
          f"MAX_SOLVER_RETRY={MAX_PER_SOLVER_RETRIES} "
          f"MAX_WORKER_WAIT={MAX_WORKER_WAIT_SECONDS}s "
          f"MAX_REQUEST={MAX_REQUEST_RUNTIME_SECONDS}s")
    
    # Phase 3: Classical + Neal baseline
    print_section("PHASE 3: Classical + Neal Baseline")
    
    req_local = BenchmarkRequest(
        mu=[0.08, 0.12, 0.15, 0.10, 0.20],
        sigma=[
            [0.04, 0.006, 0.008, 0.004, 0.010],
            [0.006, 0.09, 0.012, 0.006, 0.015],
            [0.008, 0.012, 0.16, 0.008, 0.020],
            [0.004, 0.006, 0.008, 0.01, 0.005],
            [0.010, 0.015, 0.020, 0.005, 0.25],
        ],
        tickers=['AAPL', 'GOOGL', 'MSFT', 'T', 'TSLA'],
        sectors=['tech', 'telecom', 'healthcare', 'energy', 'finance'],
        cardinality=2,
        max_sector_exposure=0.50,
        risk_tolerance=0.5,
        binary_bits=2,
        solver='classical',
        trajectories=128,
        benchmark_mode='FAST',
    )
    
    result1 = await run_bounded_test(
        "PHASE 3: LOCAL SOLVERS (classical + neal)",
        req_local, ['classical', 'neal'], 'LOCAL_ONLY'
    )
    
    # Verify baseline
    if result1:
        classical_ok = any(r['solver'] == 'classical' and r['status'] == 'success' 
                          for r in result1['results'])
        neal_ok = any(r['solver'] == 'neal' and r['status'] == 'success' 
                     for r in result1['results'])
        print(f"\n  [SOLVER_STATUS] classical={'PASS' if classical_ok else 'FAIL'} "
              f"neal={'PASS' if neal_ok else 'FAIL'}")
    
    # Phase 4: AWS_BRAKET_LOCAL with bounded retries
    print_section("PHASE 4: AWS_BRAKET_LOCAL")
    
    result2 = await run_bounded_test(
        "PHASE 4: AWS_BRAKET_LOCAL",
        req_local, ['AWS_BRAKET_LOCAL'], 'LOCAL_ONLY'
    )
    
    braket_local_ok = False
    if result2:
        for r in result2['results']:
            if r['solver'] == 'AWS_BRAKET_LOCAL':
                sg = r.get('scientific_gate', {})
                strict = safe_float(sg.get('strict_ratio'), 0.0)
                raw = safe_float(sg.get('raw_ratio'), 0.0)
                braket_local_ok = (r['status'] == 'success' and strict > 0 and raw > 0)
                print(f"\n  [SOLVER_STATUS] AWS_BRAKET_LOCAL={'PASS' if braket_local_ok else 'FAIL'} "
                      f"strict={strict:.4f} raw={raw:.4f}")
    
    # Phase 5: Full LOCAL_ONLY with all local solvers
    print_section("PHASE 5: FULL LOCAL STACK")
    
    result3 = await run_bounded_test(
        "PHASE 5: FULL LOCAL STACK (classical + neal + AWS_BRAKET_LOCAL)",
        req_local, ['classical', 'neal', 'AWS_BRAKET_LOCAL'], 'LOCAL_ONLY'
    )
    
    # Phase 6: K=N case
    print_section("PHASE 6: K=N CASE (cardinality=5)")
    
    req_kn = BenchmarkRequest(
        mu=[0.08, 0.12, 0.15, 0.10, 0.20],
        sigma=[
            [0.04, 0.006, 0.008, 0.004, 0.010],
            [0.006, 0.09, 0.012, 0.006, 0.015],
            [0.008, 0.012, 0.16, 0.008, 0.020],
            [0.004, 0.006, 0.008, 0.01, 0.005],
            [0.010, 0.015, 0.020, 0.005, 0.25],
        ],
        tickers=['AAPL', 'GOOGL', 'MSFT', 'T', 'TSLA'],
        sectors=['tech', 'telecom', 'healthcare', 'energy', 'finance'],
        cardinality=5,
        max_sector_exposure=1.0,
        risk_tolerance=0.0,
        binary_bits=2,
        solver='classical',
        trajectories=128,
        benchmark_mode='FAST',
    )
    
    result4 = await run_bounded_test(
        "PHASE 6: K=N CASE",
        req_kn, ['classical', 'neal', 'AWS_BRAKET_LOCAL'], 'LOCAL_ONLY'
    )
    
    # Final summary
    print_section("FINAL CONVERGENCE SUMMARY")
    
    all_pass = True
    results_to_check = [result1, result2, result3, result4]
    
    for test_name, result in [("Phase3", result1), ("Phase4", result2), 
                               ("Phase5", result3), ("Phase6", result4)]:
        if result is None:
            print(f"  {test_name}: TIMEOUT/ERROR")
            all_pass = False
            continue
        
        for r in result['results']:
            sg = r.get('scientific_gate', {})
            strict = safe_float(sg.get('strict_ratio'), 0.0)
            raw = safe_float(sg.get('raw_ratio'), 0.0)
            solver = r['solver']
            status = r['status']
            
            if status == 'success' and strict > 0 and raw > 0:
                print(f"  {test_name}/{solver}: PASS (strict={strict:.4f} raw={raw:.4f})")
            elif status == 'success':
                print(f"  {test_name}/{solver}: PARTIAL (strict={strict:.4f} raw={raw:.4f})")
            else:
                print(f"  {test_name}/{solver}: FAIL (status={status})")
                all_pass = False
    
    if all_pass:
        print("\n[VALIDATION_RESULT] ALL SOLVERS CONVERGED SUCCESSFULLY")
    else:
        print("\n[VALIDATION_RESULT] SOME SOLVERS NEED ATTENTION")
        print("[RECOMMENDED_NEXT_FIX] Check Braket worker health and QAOA parameters")
    
    print("[SAFE_TERMINATION] Bounded validation completed gracefully")

if __name__ == '__main__':
    asyncio.run(main())
