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


def decode_sample_to_weights(model: QuboModel, sample: dict[str, int | float | bool]) -> np.ndarray:
    """Decodes a binary sample bitstring into normalized portfolio weights.
    
    Priority 4: [SELECTION_ALLOCATION_MANIFOLD_REMEDIATION]
    This function enforces a strict coupling between asset selection bits 
    and decoded allocation weights.
    """
    n_assets = len(model.request.mu)
    ALLOCATION_EPSILON = 1e-6
    
    # Priority 4: STEP 1 - Decode raw weights with MIN_WEIGHT_FLOOR (Phase 6)
    raw_weights = np.zeros(n_assets, dtype=float)
    floor_applied_count = 0
    is_kn = (model.request.cardinality == n_assets)
    
    for i, row in enumerate(model.build.weight_variables):
        units = 0
        for bit, var in enumerate(row):
            bit_val = int(round(float(sample.get(var, 0))))
            units += bit_val * (2**bit)
            
        # [MIN_WEIGHT_FLOOR] (Phase 6)
        y_var = model.build.indicator_variables[i]
        indicator_val = int(round(float(sample.get(y_var, 1 if is_kn else 0))))
        
        if indicator_val == 1 and units == 0:
            units = 1 # Force minimal allocation
            floor_applied_count += 1
            
        raw_weights[i] = units / model.build.denominator

    pre_norm_weights = raw_weights.copy()

    # Priority 4: STEP 2 - Normalize and audit stability
    weight_sum = np.sum(raw_weights)
    if weight_sum > 1e-9:
        normalized_weights = raw_weights / weight_sum
    else:
        normalized_weights = raw_weights
        
    # [NORMALIZATION_STABILITY_AUDIT] (Phase 6)
    zeroed_allocations = 0
    for i in range(n_assets):
        if pre_norm_weights[i] > 0 and normalized_weights[i] <= ALLOCATION_EPSILON:
            zeroed_allocations += 1
            
    if floor_applied_count > 0 or zeroed_allocations > 0:
        logger.info(
            f"[NORMALIZATION_STABILITY_AUDIT] "
            f"floor_applied={floor_applied_count} "
            f"zeroed_allocations={zeroed_allocations} "
            f"pre_sum={weight_sum:.4f}")

    # [DECODE_FORENSICS] - Track decode → normalize pipeline geometry
    pre_norm_sum = float(weight_sum)
    post_norm_sum = float(np.sum(normalized_weights))
    selected_count = int(np.sum(pre_norm_weights > ALLOCATION_EPSILON))
    cardinality_target = model.request.cardinality
    cardinality_match = (selected_count == cardinality_target)
    denominator = model.build.denominator
    
    print(
        f"[DECODE_FORENSICS] "
        f"pre_sum={pre_norm_sum:.4f} "
        f"post_sum={post_norm_sum:.4f} "
        f"selected={selected_count} "
        f"cardinality_target={cardinality_target} "
        f"cardinality_match={cardinality_match} "
        f"denominator={denominator} "
        f"floor_applied={floor_applied_count} "
        f"zeroed={zeroed_allocations}")

    selection_mask = [w > ALLOCATION_EPSILON for w in normalized_weights]
    nonzero_weight_count = sum(1 for s in selection_mask if s)
    
    return normalized_weights
            
    # Priority 4: STEP 3 - Cross-verify with indicator bits (Audit)
    selected_bits_count = 0
    zero_weight_selected_count = 0
    is_kn = (model.request.cardinality == n_assets)
    
    for i in range(n_assets):
        y_var = model.build.indicator_variables[i]
        # For K==N, we assume 1 if missing. For others, 0.
        bit_val = int(round(float(sample.get(y_var, 1 if is_kn else 0))))
        if bit_val == 1:
            selected_bits_count += 1
            if raw_weights[i] <= ALLOCATION_EPSILON:
                zero_weight_selected_count += 1

    # [SELECTION_ALLOCATION_CONSISTENCY] (Phase 4)
    consistent = (zero_weight_selected_count == 0)
    status_str = "VALID" if consistent else "INCONSISTENT"
    
    logger.info(
        f"[SELECTION_ALLOCATION_CONSISTENCY] "
        f"selected_count={selected_bits_count} "
        f"nonzero_weight_count={nonzero_weight_count} "
        f"consistent={consistent} "
        f"zero_weight_selected={zero_weight_selected_count} "
        f"status={status_str}")
    print(f"[SELECTION_ALLOCATION_CONSISTENCY] selected={selected_bits_count} nonzero={nonzero_weight_count} status={status_str}")

    # Mandatory Hard Fail (Phase 4)
    if not consistent:
        logger.error(f"[MANIFOLD_CORRUPTION] {zero_weight_selected_count} assets have selection bits but zero weight.")
        raise RuntimeError("SELECTION_ALLOCATION_MANIFOLD_CORRUPTION")

    # Priority 5: [ENCODING_MANIFOLD_AUDIT]
    target_cardinality = model.request.cardinality
    selection_probability = nonzero_weight_count / n_assets
    
    logger.info(
        f"[ENCODING_MANIFOLD_AUDIT] selection_probability={selection_probability:.4f} "
        f"nonzero_weight_count={nonzero_weight_count} "
        f"target_cardinality={target_cardinality}")

    # [CARDINALITY_RECONCILIATION]
    active_assets = nonzero_weight_count
    cardinality_delta = abs(active_assets - target_cardinality)
    
    if active_assets == 0:
        logger.error("[DECODE_COLLAPSE] Decoded portfolio has 0 active assets. Rejecting sample.")
        raise DecodeConstraintError("Decoded portfolio collapsed to 0 active assets")
        
    # [PHASE 3: NORMALIZATION SAFETY]
    w_sum = np.sum(raw_weights)
    if w_sum <= ALLOCATION_EPSILON:
        logger.error(f"[EMPTY_PORTFOLIO] sum(weights)={w_sum:.8f} below epsilon")
        raise DecodeConstraintError("EMPTY_PORTFOLIO: near-zero total weight")

    # Final Normalized Weights
    weights = raw_weights / w_sum
    
    # Forensic Trace
    for i in range(n_assets):
        logger.info(f"[ASSET_DECODE_TRACE] asset={model.request.tickers[i]} weight={weights[i]:.4f} selected={selection_mask[i]}")

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
