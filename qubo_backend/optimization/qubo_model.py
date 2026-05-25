from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import logging

logger = logging.getLogger(__name__)

from .bqm_builder import BQMBuildResult, build_portfolio_bqm
from .contracts import SolverRequest

class DecodeDimensionError(ValueError):
    """Raised when measurement vector dimensions mismatch model expectations."""
    pass

class DecodeRepairError(ValueError):
    """Raised when feasible repair is mathematically impossible."""
    pass

class DecodeConstraintError(ValueError):
    """Raised when decoded state violates hard constraints (e.g. 0 active assets)."""
    pass


@dataclass(frozen=True)
class QuboModel:
    request: SolverRequest
    build: BQMBuildResult

    @property
    def variable_order(self) -> list[str]:
        return self.build.variable_order

    @property
    def variable_count(self) -> int:
        return len(self.build.variable_order)

    def evaluate_solution(self, sample: dict[str, int | float | bool]) -> float:
        """Evaluate the canonical portfolio objective for a given bitstring sample.
        
        This ensures all solvers are compared on the same scale, regardless of 
        internal penalty scales or native energy values.
        """
        # 1. Decode to weights
        weights = decode_sample_to_weights(self, sample)
        
        # 2. Calculate objective (Markowitz: risk - tolerance * return)
        mu = np.asarray(self.request.mu)
        sigma = np.asarray(self.request.sigma)
        
        expected_return = np.dot(mu, weights)
        variance = np.dot(weights, np.dot(sigma, weights))
        
        # Objective must match bqm_builder.py: Risk - risk_tolerance * Return
        # (Note: risk_tolerance acts as a multiplier for expected return)
        return float(variance - self.request.risk_tolerance * expected_return)


def build_qubo_model(request: SolverRequest) -> QuboModel:
    return QuboModel(request=request, build=build_portfolio_bqm(request))


def to_dimod_bqm(model: QuboModel):
    return model.build.bqm.to_dimod()


def add_symmetric_quadratic(Q: np.ndarray, i: int, j: int, value: float) -> None:
    """Write a quadratic coefficient using Convention B — Fully Symmetric Storage.

    For i != j: writes Q[i,j] += value/2 AND Q[j,i] += value/2.
    This ensures x^T Q_sym x == x^T Q_upper x for all binary x, because
    the matmul sums both Q[i,j] and Q[j,i], recovering the full coefficient.

    For i == j (diagonal): writes Q[i,i] += value once (no halving).

    WARNING: Do NOT write the full value to both positions — that doubles
    every coupling and corrupts all penalty scales.
    """
    if i == j:
        Q[i, i] += value
    else:
        half = value / 2.0
        Q[i, j] += half
        Q[j, i] += half


def _verify_energy_convention() -> None:
    """Verify Convention B: x^T Q_sym x == x^T Q_upper x for s=[1,1], bias=1.0."""
    import logging as _log
    _logger = _log.getLogger(__name__)
    Q_test = np.zeros((2, 2))
    add_symmetric_quadratic(Q_test, 0, 1, 1.0)
    s = np.array([1.0, 1.0])
    actual = float(s @ Q_test @ s)
    expected = 1.0
    double_count = abs(actual - 2.0) < 1e-12
    _logger.info(
        f"[QUADRATIC_ENERGY_CONVENTION_AUDIT] "
        f"expected={expected} actual={actual:.6f} "
        f"double_count_detected={double_count}"
    )
    if abs(actual - expected) > 1e-9:
        raise RuntimeError(
            f"ENERGY_CONVENTION_VIOLATION: expected s^T Q s = {expected}, "
            f"got {actual}. Check add_symmetric_quadratic() implementation."
        )


def qubo_to_ising(Q: np.ndarray, offset: float = 0.0) -> tuple[np.ndarray, np.ndarray, float]:
    """[PHASE 6 & 11: CANONICAL HAMILTONIAN SERIALIZATION]
    Convert upper-triangular QUBO matrix to Ising Hamiltonian.
    QUBO:  E(x) = x^T Q x + offset,  x in {0,1}^n
    Ising: H = sum_i h_i Z_i + sum_{i<j} J_ij Z_i Z_j + C
    Returns (h, J, C) where h is linear, J is upper-triangular quadratic, C is constant.
    """
    n = Q.shape[0]
    h = np.zeros(n)
    J = np.zeros((n, n))
    C = float(offset)

    for i in range(n):
        C += Q[i, i] / 2.0
        h[i] -= Q[i, i] / 2.0

        for j in range(i + 1, n):
            C += Q[i, j] / 4.0
            h[i] -= Q[i, j] / 4.0
            h[j] -= Q[i, j] / 4.0
            J[i, j] = Q[i, j] / 4.0

    return h, J, C


def to_qubo_matrix(model: QuboModel) -> tuple[np.ndarray, list[str], float]:
    """Return upper-triangular QUBO matrix Q where E=x'Qx+offset."""
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    _verify_energy_convention()
    order = model.variable_order
    index = {name: pos for pos, name in enumerate(order)}
    q = np.zeros((len(order), len(order)), dtype=float)
    for var, bias in model.build.bqm.linear.items():
        q[index[var], index[var]] += float(bias)
    for (left, right), bias in model.build.bqm.quadratic.items():
        i = index[left]
        j = index[right]
        add_symmetric_quadratic(q, i, j, float(bias))
    max_asymmetry = float(np.max(np.abs(q - q.T)))
    frobenius_asymmetry = float(np.linalg.norm(q - q.T, 'fro'))
    is_symmetric = max_asymmetry < 1e-9
    _logger.info(
        f"[QUBO_SYMMETRY_AUDIT] shape={q.shape} "
        f"max_asymmetry={max_asymmetry:.6e} "
        f"frobenius_asymmetry={frobenius_asymmetry:.6e} "
        f"symmetric={is_symmetric}"
    )
    if not is_symmetric:
        raise RuntimeError(
            f"QUBO_SYMMETRY_CORRUPTION: max_asymmetry={max_asymmetry:.6e}"
        )
    return q, order, float(model.build.bqm.offset)


class AllocationLeakageError(Exception):
    """Raised when classical normalization mutates the quantum selection topology."""
    pass

def decode_sample_to_weights(model: QuboModel, sample: dict[str, int | float | bool]) -> np.ndarray:
    """Decodes a binary sample bitstring into normalized portfolio weights.
    
    Priority 4: [SELECTION_ALLOCATION_MANIFOLD_REMEDIATION]
    This function enforces a strict coupling between asset selection bits 
    and decoded allocation weights.
    """
    n_assets = len(model.request.mu)
    ALLOCATION_EPSILON = 1e-6
    
    is_kn = (model.request.cardinality == n_assets)
    y_bits = np.array([int(round(float(sample.get(model.build.indicator_variables[i], 1 if is_kn else 0)))) for i in range(n_assets)])
    selection_mask = y_bits.astype(bool)
    raw_weights = np.zeros(n_assets, dtype=float)

    # ── [TN1 BINARY SELECTION SWITCH] ─────────────
    if len(model.build.weight_variables) == 0:
        # Combinatorial Only (TN1). Classical convex optimization (scipy.optimize)
        from scipy.optimize import minimize
        selected_indices = np.where(selection_mask)[0].tolist()
                
        if len(selected_indices) > 0:
            mu = np.array(model.request.mu)
            sigma = np.array(model.request.sigma)
            lambda_r = model.request.risk_tolerance
            
            def objective(w_sel):
                return w_sel.T @ sigma[np.ix_(selected_indices, selected_indices)] @ w_sel - lambda_r * (mu[selected_indices].T @ w_sel)
                
            constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
            bounds = [(1e-5, 1.0) for _ in selected_indices]
            initial_guess = np.ones(len(selected_indices)) / len(selected_indices)
            
            res = minimize(objective, initial_guess, method='SLSQP', bounds=bounds, constraints=constraints)
            
            if not res.success:
                raise ValueError("INVALID_STATE: Classical convex optimization failed for selected subset.")
                
            for idx, w_val in zip(selected_indices, res.x):
                raw_weights[idx] = max(1e-5, float(w_val))
    else:
        for i, row in enumerate(model.build.weight_variables):
            if selection_mask[i]:
                units = sum(int(round(float(sample.get(var, 0)))) * (2**bit) for bit, var in enumerate(row))
                raw_weights[i] = units / model.build.denominator

    # STRICT INVARIANT-PRESERVING LOGIC (Phase 1/2)
    # Step 1: Raw Weights
    raw_sum = np.sum(raw_weights)
    logger.info(
        f"[ALLOCATION_DECODE_AUDIT] raw_bitstring_sample_keys={len(sample)} "
        f"raw_selected_count={np.sum(selection_mask)} "
        f"raw_allocation_sum={raw_sum:.6f}"
    )

    # Step 2: Hard Masking
    weights = raw_weights.copy()
    weights[~selection_mask] = 0.0
    
    # [TOPOLOGY_INVARIANT_AUDIT]
    invariant_violations = np.sum((~selection_mask) & (raw_weights > 0.0))
    if invariant_violations > 0:
        logger.warning(
            f"[TOPOLOGY_INVARIANT_AUDIT] Detected {invariant_violations} assets where y_i == 0 but w_i > 0! "
            f"Hard masking applied to restore invariant."
        )

    # Step 3: Normalization
    pre_norm_sum = np.sum(weights)
    logger.info(
        f"[NORMALIZATION_AUDIT] pre_normalization_sum={pre_norm_sum:.6f} "
        f"zero_weight_assets={np.sum(weights <= 1e-8)}"
    )
    
    if pre_norm_sum <= 1e-8:
        raise AllocationLeakageError("No surviving selected weights after masking")

    weights[selection_mask] /= pre_norm_sum
    post_selection_count = np.count_nonzero(weights > 1e-8)
    
    logger.info(
        f"[NORMALIZATION_AUDIT] post_normalization_sum={np.sum(weights):.6f} "
        f"removed_allocations={np.sum(selection_mask) - post_selection_count}"
    )

    logger.info(
        f"[FEASIBLE_MANIFOLD_AUDIT] raw_selection_count={np.sum(selection_mask)} "
        f"post_selection_count={post_selection_count} "
        f"selected_sum={pre_norm_sum:.4f}"
    )
    
    logger.info("[TOPOLOGY_PRESERVATION_AUDIT] Topology strictly evaluated.")
    logger.info("[POST_DECODE_INVARIANT] Verifying topological immutability.")

    if post_selection_count != np.sum(selection_mask):
        raise AllocationLeakageError(
            f"Topology mutation detected "
            f"before={np.sum(selection_mask)} "
            f"after={post_selection_count}"
        )

    # ── [ALLOCATION VALIDATION TRACKING] (Phase 5) ───────────────
    try:
        from qubo_backend.optimization.portfolio import verify_constraints
        validation = verify_constraints(weights, model.request)
        logger.info(
            f"[ALLOCATION_VALIDATION_RESULT] "
            f"feasible={validation.feasible} "
            f"leakage_detected={validation.leakage_detected} "
            f"normalization_valid={validation.normalization_valid} "
            f"allocation_sum={validation.allocation_sum:.6f} "
            f"selected_count={validation.selected_count} "
            f"violations={len(validation.violations)}"
        )
    except Exception as e:
        logger.error(f"[ALLOCATION_VALIDATION_ERROR] Failed to track validation result: {e}")

    return weights



def to_qiskit_quadratic_program(model: QuboModel):
    try:
        from qiskit_optimization import QuadraticProgram
        from qiskit_optimization.converters import QuadraticProgramToQubo
        from qiskit.quantum_info import SparsePauliOp
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("qiskit-optimization is not installed") from exc

    qp = QuadraticProgram("qubo_portfolio")
    for variable in model.variable_order:
        qp.binary_var(variable)
    
    # Build QUBO dictionary with string keys and ensure np.float64 dtype
    qubo = {}
    for (left, right), bias in model.build.bqm.quadratic.items():
        if abs(float(bias)) > 1e-12:
            qubo[(left, right)] = np.float64(float(bias))
    for name, bias in model.build.bqm.linear.items():
        if abs(float(bias)) > 1e-12:
            qubo[(name, name)] = np.float64(float(bias))
    
    # 1. Extract all unique string variables
    all_vars = list(set([k for pair in qubo.keys() for k in pair]))
    # 2. Map them to integers
    var_map = {var: i for i, var in enumerate(all_vars)}
    # 3. Rebuild QUBO with strictly integers and np.float64 weights
    int_qubo = {}
    for (k1, k2), weight in qubo.items():
        int_qubo[(var_map[k1], var_map[k2])] = np.float64(weight)
    
    # Validate matrix dtype before sparse conversion
    for (i, j), weight in int_qubo.items():
        assert isinstance(weight, (np.float64, float, np.float32)), f"[QISKIT_MATRIX_DTYPE] Invalid dtype {type(weight)} for weight {weight}"
        assert np.issubdtype(type(weight), np.number), f"[QISKIT_MATRIX_DTYPE] Weight {weight} is not numeric"
    
    # Ensure all weights are strictly numeric before Qiskit processing
    for (i, j), weight in int_qubo.items():
        int_qubo[(i, j)] = float(weight)  # Force float conversion
    
    # Keep integer indices for Qiskit to avoid string dtype issues
    linear_terms = {}
    quadratic_terms = {}
    for (i, j), weight in int_qubo.items():
        if i == j:
            linear_terms[str(i)] = weight  # Use string key for Qiskit
        else:
            quadratic_terms[(str(i), str(j))] = weight  # Use string keys for Qiskit
    
    # Create QuadraticProgram with integer variable names
    qp_int = QuadraticProgram("qubo_portfolio")
    for i in range(len(all_vars)):
        qp_int.binary_var(str(i))  # Use string representation of integer
    
    qp_int.minimize(
        constant=float(model.build.bqm.offset),
        linear=linear_terms,
        quadratic=quadratic_terms,
    )
    return qp_int
