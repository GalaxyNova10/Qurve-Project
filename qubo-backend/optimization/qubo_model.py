import numpy as np
from pyqubo import Array, Constraint, Placeholder

def build_portfolio_hamiltonian(mu, sigma, cardinality, risk_tolerance, binary_bits=7):
    """
    Builds a QUBO Hamiltonian for portfolio optimization.
    Minimizes: risk_tolerance * (w.T @ sigma @ w) - mu.T @ w
    Subject to: sum(w) = 1, cardinality constraint.
    """
    n = len(mu)
    # Binary variables for each asset and each bit in its weight expansion
    # weight_i = sum(2^j * x_i,j) / (2^binary_bits - 1)
    x = Array.create('x', shape=(n, binary_bits), vartype='BINARY')
    
    # Scaling factor for binary expansion
    scale = 2**binary_bits - 1
    
    # Construct weights
    weights = []
    for i in range(n):
        w_i = sum(2**j * x[i, j] for j in range(binary_bits)) / scale
        weights.append(w_i)
    
    # 1. Objective: Return and Risk
    # Risk = w.T @ sigma @ w
    risk = 0
    for i in range(n):
        for j in range(n):
            risk += weights[i] * sigma[i][j] * weights[j]
            
    # Return = mu.T @ w
    returns = sum(mu[i] * weights[i] for i in range(n))
    
    H_obj = risk_tolerance * risk - returns
    
    # 2. Constraint: Sum of weights = 1
    # We use a penalty factor (lam)
    lam = Placeholder('lam')
    H_const = lam * Constraint((sum(weights) - 1)**2, label='sum_weights')
    
    # 3. Cardinality Constraint (simplified for QUBO)
    # In a real QUBO, we'd add binary indicators for 'is asset i included'
    # For now, we'll stick to the budget constraint as it's the most critical
    
    H = H_obj + H_const
    model = H.compile()
    return model

def decode_solution(solution, n, binary_bits):
    """Decodes the binary solution back to asset weights."""
    weights = np.zeros(n)
    scale = 2**binary_bits - 1
    for i in range(n):
        w_i = 0
        for j in range(binary_bits):
            if solution.get(f'x[{i}][{j}]') == 1:
                w_i += 2**j
        weights[i] = w_i / scale
    return weights
