import sys
import numpy as np
import itertools
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.qubo_model import QuboModel, decode_sample_to_weights

def run_ci_audit():
    print("--- STARTING CI HAMILTONIAN TOPOLOGY AUDIT ---")
    
    # Test cases for small models
    test_params = [
        {"n_assets": 2, "bits": 2, "k": 1},
        {"n_assets": 3, "bits": 2, "k": 1},
        {"n_assets": 3, "bits": 3, "k": 2},
    ]
    
    overall_pass = True
    
    for params in test_params:
        n = params["n_assets"]
        b = params["bits"]
        k = params["k"]
        print(f"\n[TEST_CASE] assets={n} bits={b} k={k}")
        
        req = SolverRequest(
            mu=[0.1] * n,
            sigma=[[0.01] * n for _ in range(n)],
            tickers=[str(i) for i in range(n)],
            sectors=['S'] * n,
            cardinality=k,
            binary_bits=b,
            risk_tolerance=1.0
        )
        
        build = build_portfolio_bqm(req)
        model = QuboModel(req, build)
        
        vars = build.variable_order
        feasible_energies = []
        infeasible_energies = []
        
        for bits_tuple in itertools.product([0, 1], repeat=len(vars)):
            sample = {vars[i]: bits_tuple[i] for i in range(len(vars))}
            
            # Energy calculation
            energy = float(build.bqm.offset)
            for var, bias in build.bqm.linear.items():
                energy += sample[var] * bias
            for (u, v), bias in build.bqm.quadratic.items():
                energy += sample[u] * sample[v] * bias
                
            # Feasibility check
            try:
                weights = decode_sample_to_weights(model, sample)
                y_vars = [f"y_{i}" for i in range(n)]
                selected = sum(sample.get(y, 0) for y in y_vars)
                
                is_exact_k = (selected == k)
                budget_ok = abs(np.sum(weights) - 1.0) < 0.05
                active_weights = sum(1 for w in weights if w > 1e-6)
                is_strictly_positive = (selected == active_weights)
                
                is_feasible = is_exact_k and budget_ok and is_strictly_positive
            except Exception:
                is_feasible = False
            
            if is_feasible:
                feasible_energies.append(energy)
            else:
                infeasible_energies.append(energy)
        
        min_f = min(feasible_energies) if feasible_energies else float('inf')
        min_inf = min(infeasible_energies) if infeasible_energies else float('inf')
        
        gap = min_inf - min_f
        passed = gap > 0
        
        print(f"  feasible_count={len(feasible_energies)}")
        print(f"  min_feasible={min_f:.6f}")
        print(f"  min_infeasible={min_inf:.6f}")
        print(f"  energy_gap={gap:.6f}")
        print(f"  status={'PASS' if passed else 'FAIL'}")
        
        if not passed:
            overall_pass = False
            
    if not overall_pass:
        print("\n!!! CI AUDIT FAILED: ENERGY TOPOLOGY COLLAPSE DETECTED !!!")
        sys.exit(1)
        
    print("\n--- CI AUDIT COMPLETED SUCCESSFULLY ---")

if __name__ == "__main__":
    run_ci_audit()
