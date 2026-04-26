import numpy as np
from qiskit_optimization import QuadraticProgram
from qiskit_optimization.algorithms import MinimumEigenOptimizer
from qiskit_algorithms import QAOA
from qiskit_algorithms.optimizers import COBYLA
from qiskit.primitives import StatevectorSampler
from .qubo_model import build_portfolio_hamiltonian, decode_solution

def solve_with_qiskit_local(mu, sigma, cardinality, risk_tolerance, binary_bits=3):
    """
    Solves using Qiskit QAOA (Local Simulator).
    Note: Lowering binary_bits for Qiskit as it's more qubit-intensive.
    """
    model = build_portfolio_hamiltonian(mu, sigma, cardinality, risk_tolerance, binary_bits)
    feed_dict = {'lam': 5.0}
    qubo, offset = model.to_qubo(feed_dict=feed_dict)
    
    # Convert pyqubo to Qiskit QuadraticProgram
    qp = QuadraticProgram()
    # Add variables
    vars_list = sorted(qubo.keys(), key=lambda x: str(x))
    # Collect all unique variable names
    all_vars = set()
    for k in qubo.keys():
        if isinstance(k, tuple):
            all_vars.add(k[0])
            all_vars.add(k[1])
        else:
            all_vars.add(k)
            
    for v in sorted(list(all_vars)):
        qp.binary_var(name=v)
        
    # Add objective
    linear = {}
    quadratic = {}
    for k, v in qubo.items():
        if isinstance(k, tuple):
            quadratic[k] = v
        else:
            linear[k] = v
    qp.minimize(linear=linear, quadratic=quadratic)
    
    # Solve using QAOA
    qaoa = QAOA(sampler=StatevectorSampler(), optimizer=COBYLA())
    optimizer = MinimumEigenOptimizer(qaoa)
    result = optimizer.solve(qp)
    
    # Map result back
    best_sample = result.variables_dict
    weights = decode_solution(best_sample, len(mu), binary_bits)
    
    return {
        "weights": weights.tolist(),
        "energy": float(result.fval),
        "solver": "qiskit_qaoa_local"
    }
