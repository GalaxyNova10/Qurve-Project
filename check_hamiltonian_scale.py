import sys
sys.path.insert(0, 'D:/QUBO/qubo-backend')
import numpy as np
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.optimization.qubo_model import build_qubo_model, to_qubo_matrix

request = SolverRequest(
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

build = build_portfolio_bqm(request)
model = build_qubo_model(request)
Q, var_order, offset = to_qubo_matrix(model)

print(f"[HAMILTONIAN_SCALE] objective_span={build.objective_span:.4f}")
print(f"[HAMILTONIAN_SCALE] penalty_scales={build.penalty_scales}")
print(f"[HAMILTONIAN_SCALE] n_variables={len(var_order)}")
print(f"[HAMILTONIAN_SCALE] Q shape={Q.shape}")

# Check actual coefficient ranges
all_coeffs = list(build.bqm.linear.values()) + list(build.bqm.quadratic.values())
max_coeff = max(abs(c) for c in all_coeffs)
min_nonzero = min(abs(c) for c in all_coeffs if abs(c) > 1e-12)
obj_coeffs = [abs(c) for c in all_coeffs if abs(c) < build.penalty_scales['P_card'] * 0.5]
constraint_coeffs = [abs(c) for c in all_coeffs if abs(c) >= build.penalty_scales['P_card'] * 0.5]

print(f"[HAMILTONIAN_SCALE] max_coeff={max_coeff:.4f}")
print(f"[HAMILTONIAN_SCALE] min_nonzero_coeff={min_nonzero:.6f}")
print(f"[HAMILTONIAN_SCALE] penalty/objective_ratio={max_coeff/build.objective_span:.2f}x")
print(f"[HAMILTONIAN_SCALE] target_ratio=3x-20x")
print(f"[HAMILTONIAN_SCALE] status={'PASS' if max_coeff/build.objective_span <= 20 else 'FAIL - too high'}")

# Check Q matrix diagonal for penalty signatures
n_assets = len(request.mu)
bits = request.binary_bits
weight_bits = n_assets * bits
indicator_start = weight_bits

y_diag = [Q[i, i] for i in range(indicator_start, indicator_start + n_assets)]
print(f"[HAMILTONIAN_SCALE] y_i diagonal values: {y_diag}")
print(f"[HAMILTONIAN_SCALE] y_i diagonal mean: {np.mean(y_diag):.4f}")

# Test energy ordering with the new Q
np.random.seed(42)
f_energies = []
inf_energies = []
denominator = (2 ** bits) - 1

for _ in range(500):
    s = np.random.randint(0, 2, len(var_order))
    energy = float(s @ Q @ s) + offset
    
    # Decode to check feasibility
    weights = np.zeros(n_assets)
    selection = []
    for i in range(n_assets):
        y_idx = indicator_start + i
        sel = bool(s[y_idx]) if y_idx < len(s) else False
        selection.append(sel)
        if sel:
            units = sum(s[i*bits+b] * (2**b) for b in range(bits) if i*bits+b < len(s))
            weights[i] = units / denominator
    
    selected_count = sum(selection)
    budget = np.sum(weights)
    is_feasible = (selected_count == request.cardinality) and (abs(budget - 1.0) < 0.05)
    
    # Check linkage: selected assets must have positive weight
    if is_feasible:
        zero_weight = sum(1 for i in range(n_assets) if selection[i] and weights[i] <= 1e-6)
        is_feasible = (zero_weight == 0)
    
    if is_feasible:
        f_energies.append(energy)
    else:
        inf_energies.append(energy)

if f_energies and inf_energies:
    f_mean = np.mean(f_energies)
    inf_mean = np.mean(inf_energies)
    f_min = np.min(f_energies)
    inf_min = np.min(inf_energies)
    inversion = f_mean > inf_mean or f_min > inf_min
    
    print(f"\n[FEASIBILITY_STATUS] feasible_count={len(f_energies)} infeasible_count={len(inf_energies)}")
    print(f"[FEASIBILITY_STATUS] feasible_mean={f_mean:.4f} infeasible_mean={inf_mean:.4f}")
    print(f"[FEASIBILITY_STATUS] feasible_min={f_min:.4f} infeasible_min={inf_min:.4f}")
    print(f"[FEASIBILITY_STATUS] energy_gap={inf_mean - f_mean:.4f}")
    print(f"[FEASIBILITY_STATUS] inversion_detected={inversion}")
    print(f"[FEASIBILITY_STATUS] status={'PASS' if not inversion else 'FAIL'}")
else:
    print(f"\n[FEASIBILITY_STATUS] insufficient samples: f={len(f_energies)} inf={len(inf_energies)}")
