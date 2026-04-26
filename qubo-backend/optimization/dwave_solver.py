import dimod
import numpy as np
from .qubo_model import build_portfolio_hamiltonian, decode_solution

def solve_with_dwave_local(mu, sigma, cardinality, risk_tolerance, binary_bits=7):
    """Solves using D-Wave's local Simulated Annealing."""
    model = build_portfolio_hamiltonian(mu, sigma, cardinality, risk_tolerance, binary_bits)
    
    # Define penalty factor for constraints
    feed_dict = {'lam': 5.0}
    qubo, offset = model.to_qubo(feed_dict=feed_dict)
    
    # Local sampler
    sampler = dimod.SimulatedAnnealingSampler()
    sampleset = sampler.sample_qubo(qubo, num_reads=100)
    
    best_sample = sampleset.first.sample
    weights = decode_solution(best_sample, len(mu), binary_bits)
    
    return {
        "weights": weights.tolist(),
        "energy": float(sampleset.first.energy),
        "num_reads": 100,
        "solver": "dwave_simulated_annealing"
    }
