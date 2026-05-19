import numpy as np
import itertools
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.qubo_model import QuboModel, decode_sample_to_weights

def exhaustive_audit(n_assets=3, bits=2, cardinality=1):
    req = SolverRequest(
        mu=[0.1] * n_assets,
        sigma=[[0.01] * n_assets for _ in range(n_assets)],
        tickers=[str(i) for i in range(n_assets)],
        sectors=['S'] * n_assets,
        cardinality=cardinality,
        binary_bits=bits,
        risk_tolerance=1.0
    )
    
    build = build_portfolio_bqm(req)
    model = QuboModel(req, build)
    
    vars = build.variable_order
    n_vars = len(vars)
    print(f"Auditing {2**n_vars} states...")
    
    feasible_energies = []
    infeasible_energies = []
    
    for bits_tuple in itertools.product([0, 1], repeat=n_vars):
        sample = {vars[i]: bits_tuple[i] for i in range(n_vars)}
        
        # Calculate BQM energy
        energy = float(build.bqm.offset)
        for var, bias in build.bqm.linear.items():
            energy += sample[var] * bias
        for (u, v), bias in build.bqm.quadratic.items():
            energy += sample[u] * sample[v] * bias
            
        # Determine feasibility
        try:
            # Check cardinality
            y_vars = [f"y_{i}" for i in range(n_assets)]
            selected = sum(sample.get(y, 0) for y in y_vars)
            is_exact_k = (selected == cardinality)
            
            # Check budget
            weights = decode_sample_to_weights(model, sample)
            budget_ok = abs(np.sum(weights) - 1.0) < 0.01
            
            # Check linkage (Strictly positive)
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
    
    print(f"[EXHAUSTIVE_ENERGY_ORDERING_AUDIT]")
    print(f"feasible_count={len(feasible_energies)}")
    print(f"infeasible_count={len(infeasible_energies)}")
    print(f"min_feasible={min_f:.6f}")
    print(f"min_infeasible={min_inf:.6f}")
    print(f"energy_gap={min_inf - min_f:.6f}")
    
    if min_inf <= min_f:
        print("!!! ENERGY TOPOLOGY COLLAPSE DETECTED !!!")
        # Find the state that broke it
        return False
    return True

if __name__ == "__main__":
    exhaustive_audit(n_assets=3, bits=2, cardinality=1)
