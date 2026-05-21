"""QURVE AI — QAOA Circuit Construction from QUBO Matrix.

Converts a QUBO matrix to an Ising Hamiltonian and builds a proper
QAOA ansatz circuit for the Braket SDK.

Mapping: x_i in {0,1} -> Z_i in {-1,+1} via x_i = (1 - Z_i) / 2
"""

import math
import numpy as np
import logging

logger = logging.getLogger(__name__)

try:
    from braket.circuits import Circuit
    BRAKET_AVAILABLE = True
except ImportError:
    BRAKET_AVAILABLE = False


def qubo_to_ising(Q: np.ndarray, offset: float = 0.0):
    """Convert upper-triangular QUBO matrix to Ising Hamiltonian.

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


from scipy.optimize import minimize
import time

def build_qaoa_circuit(h: np.ndarray, J: np.ndarray, n_qubits: int,
                       gamma_list: list[float], beta_list: list[float]):
    """Build a p-layer QAOA circuit for the Ising Hamiltonian.
    
    gamma_list/beta_list must be length p.
    """
    if not BRAKET_AVAILABLE:
        raise RuntimeError("Braket SDK not available")

    circuit = Circuit()
    depth = len(gamma_list)

    # Initial superposition |+>^n
    for i in range(n_qubits):
        circuit.h(i)

    for p in range(depth):
        gamma = gamma_list[p]
        beta = beta_list[p]
        
        # ── Cost unitary ────────────────────────────────────────
        for i in range(n_qubits):
            if abs(h[i]) > 1e-12:
                circuit.rz(i, 2.0 * gamma * h[i])

        for i in range(n_qubits):
            for j in range(i + 1, n_qubits):
                if abs(J[i, j]) > 1e-12:
                    circuit.cnot(i, j)
                    circuit.rz(j, 2.0 * gamma * J[i, j])
                    circuit.cnot(i, j)

        # ── Mixer unitary ───────────────────────────────────────
        for i in range(n_qubits):
            circuit.rx(i, 2.0 * beta)

    return circuit


def decode_and_evaluate(measurements, n_qubits, req_meta: dict) -> tuple[float, float]:
    """Decode measurements and return (avg_feasible_canonical_energy, feasible_ratio).
    
    Uses portfolio metadata to compute the TRUE objective for feasible states.
    Infeasible states are penalized.
    """
    mu = np.array(req_meta["mu"])
    sigma = np.array(req_meta["sigma"])
    n_assets = len(mu)
    cardinality = req_meta["cardinality"]
    denominator = req_meta["denominator"]
    risk_tolerance = req_meta["risk_tolerance"]
    is_kn = req_meta.get("is_kn_case", False)
    bits_per_asset = req_meta.get("binary_bits", 2)
    weight_bits_total = n_assets * bits_per_asset

    all_energies = []
    raw_feasible_count = 0
    strict_positive_count = 0
    total_samples = len(measurements)
    
    for meas in measurements:
        # 1. Decode to weights
        weights = np.zeros(n_assets)
        selection_mask = []
        
        # Selection bits (y_i) added AFTER weight bits in bqm_builder.py
        for i in range(n_assets):
            if is_kn:
                selection_mask.append(True)
            else:
                y_idx = weight_bits_total + i
                selection_mask.append(meas[y_idx] == 1 if y_idx < len(meas) else False)
        
        # Weight bits (x_{ik}) start from 0
        for i in range(n_assets):
            if selection_mask[i]:
                units = 0
                for b in range(bits_per_asset):
                    bit_idx = i * bits_per_asset + b
                    if bit_idx < len(meas):
                        units += meas[bit_idx] * (2**b)
                weights[i] = units / denominator
            else:
                weights[i] = 0.0
                
        # 2. Check Feasibility
        active_weights = int(np.sum(weights > 1e-6))
        selected_assets = int(np.sum(selection_mask))
        zero_weight_selected = selected_assets - active_weights
        
        budget = np.sum(weights)
        is_exact_k = (selected_assets == cardinality)
        is_positive_alloc = (zero_weight_selected == 0)
        is_feasible = is_exact_k and is_positive_alloc and (abs(budget - 1.0) < 0.05)

        # 3. Calculate Actual BQM Energy
        Q = req_meta.get("qubo_matrix")
        offset = req_meta.get("qubo_offset", 0.0)
        if not isinstance(offset, (int, float, np.floating)):
            raise RuntimeError("QUBO_OFFSET_CORRUPTION: offset is not a numeric type")
        if not math.isfinite(float(offset)):
            raise RuntimeError("QUBO_OFFSET_CORRUPTION: offset is not finite")

        if Q is not None:
            s = np.array(meas)
            if (isinstance(Q, np.ndarray) and Q.ndim == 2) or \
               (isinstance(Q, list) and len(Q) > 0 and isinstance(Q[0], list)):
                Q_2d = np.array(Q, dtype=np.float64)
            else:
                flat_qubo = Q
                if len(flat_qubo) != n_qubits * n_qubits:
                    raise RuntimeError(
                        f"QUBO_SERIALIZATION_CORRUPTION: expected {n_qubits * n_qubits} "
                        f"elements for {n_qubits}-qubit QUBO, got {len(flat_qubo)}"
                    )
                Q_2d = np.array(flat_qubo, dtype=np.float64).reshape(n_qubits, n_qubits)

            total_energy = float(s.T @ Q_2d @ s) + offset
        else:
            variance = float(weights @ sigma @ weights)
            expected_return = float(weights @ mu)
            total_energy = risk_tolerance * variance - expected_return
            
        all_energies.append(total_energy)

        # 4. Track Feasibility Ratios
        is_raw_feasible = is_exact_k and (abs(budget - 1.0) < 0.05)
        if is_raw_feasible:
            raw_feasible_count += 1
            if is_positive_alloc:
                strict_positive_count += 1
    
    raw_feasible_ratio = raw_feasible_count / total_samples
    strict_positive_ratio = strict_positive_count / total_samples
    
    # ── [FEASIBLE_MANIFOLD_QUALITY] ──────────────────────────────
    logger.info(
        f"[FEASIBLE_MANIFOLD_QUALITY] raw_ratio={raw_feasible_ratio:.4f} "
        f"strict_ratio={strict_positive_ratio:.4f} "
        f"avg_total_energy={np.mean(all_energies):.6f}")

    return float(np.mean(all_energies)), raw_feasible_ratio


def run_qaoa_optimized(h: np.ndarray, J: np.ndarray, n_qubits: int,
                      req_meta: dict, shots: int = 128, depth: int = 1):
    """Run QAOA with recursive warm-start optimization (p=1 to depth) and shot-adaptive execution."""
    from braket.devices import LocalSimulator
    device = LocalSimulator()
    
    # ── [QAOA_INTERFACE_AUDIT] ───────────────────────────
    logger.info(
        f"[QAOA_INTERFACE_AUDIT] caller=run_qaoa_optimized target_depth={depth} "
        f"parameter_dimension={2*depth} strategy={req_meta.get('optimization_strategy')}")
    
    n_assets = len(req_meta["mu"])
    cardinality_target = req_meta["cardinality"]
    
    current_best_params = None
    current_best_measurements = None
    current_best_raw_energy = float("inf")
    current_best_priority = float("inf")
    current_feasible_ratio = 0.0
    
    # ── [SHOT-ADAPTIVE EXECUTION] (Phase 6) ─────────────
    optimization_shots = 64
    validation_shots = min(2048, max(shots, 512))
    
    # ── [QAOA_WARM_START_LOOP] ─────────────────────────────────────
    for p in range(1, depth + 1):
        
        # ── [DEPTH-GATED ESCALATION] (Phase 7) ─────────────
        # Only proceed to p=2 or p=3 if lower depth achieved stable feasibility
        if p == 2 and current_feasible_ratio < 0.3:
            logger.info(f"[QAOA_DEPTH_GATE] Aborting p=2 escalation due to low feasibility ({current_feasible_ratio:.2f} < 0.3)")
            break
        if p == 3 and current_feasible_ratio < 0.5:
            logger.info(f"[QAOA_DEPTH_GATE] Aborting p=3 escalation due to low feasibility ({current_feasible_ratio:.2f} < 0.5)")
            break
            
        # 1. Prepare initial guess
        if p == 1:
            if req_meta.get("warm_start_params") and len(req_meta["warm_start_params"]) == 2 * (p):
                initial_guess = np.array(req_meta["warm_start_params"][:2*p])
            else:
                initial_guess = np.array([np.pi/4] * p + [np.pi/8] * p)
        else:
            # Warm start: p-layer params from (p-1)-layer scaled by 0.8 (Layerwise init)
            prev_gamma = current_best_params[:p-1]
            prev_beta = current_best_params[p-1:]
            initial_guess = np.concatenate([
                prev_gamma, [prev_gamma[-1] * 0.8 if len(prev_gamma)>0 else np.pi/4],
                prev_beta, [prev_beta[-1] * 0.8 if len(prev_beta)>0 else np.pi/8]
            ])
            logger.info(f"[QAOA_WARM_START] source_depth={p-1} target_depth={p}")

        # 2. Optimization loop for current depth p
        def objective_function(params):
            nonlocal current_best_raw_energy, current_best_params, current_best_measurements, current_best_priority, current_feasible_ratio
            
            gamma_list = params[:p]
            beta_list = params[p:]
            
            try:
                circuit = build_qaoa_circuit(h, J, n_qubits, gamma_list, beta_list)
                # Use fast shots for optimization
                task = device.run(circuit, shots=optimization_shots)
                result = task.result()
                
                measurements = result.measurements
                if hasattr(measurements, 'tolist'):
                    measurements = measurements.tolist()
                
                avg_total_energy, raw_feasible_ratio = decode_and_evaluate(measurements, n_qubits, req_meta)
                
                # ── [FEASIBILITY-AWARE OBJECTIVE] (Phase 5) ─────────────
                # We extract constraint violations by scanning the measurements
                Q_raw = req_meta.get("qubo_matrix")
                Q_2d = None
                if Q_raw is not None:
                    Q_2d = np.array(Q_raw, dtype=np.float64)
                    if Q_2d.ndim == 1:
                        Q_2d = Q_2d.reshape(n_qubits, n_qubits)
                
                bits_per_asset = req_meta.get("binary_bits", 2)
                weight_bits_total = n_assets * bits_per_asset
                
                total_card_violation = 0.0
                
                for m in measurements:
                    # Decode selection bits for this sample
                    m_selection = []
                    for i in range(n_assets):
                        y_idx = weight_bits_total + i
                        m_selection.append(m[y_idx] == 1 if y_idx < len(m) else False)
                    
                    m_selected_count = sum(m_selection)
                    m_is_exact_k = (m_selected_count == cardinality_target)
                    
                    # Compute constraint violations
                    cardinality_violation = abs(m_selected_count - cardinality_target)
                    total_card_violation += cardinality_violation
                    
                    # Compute raw BQM energy for this sample
                    if Q_2d is not None:
                        s = np.array(m, dtype=np.float64)
                        m_energy = float(s @ Q_2d @ s) + req_meta.get("qubo_offset", 0.0)
                    else:
                        m_energy = 0.0
                    
                    # Check positive allocation
                    m_active = 0
                    for i in range(n_assets):
                        if m_selection[i]:
                            u = sum(m[i*bits_per_asset+b]*(2**b) for b in range(bits_per_asset) if i*bits_per_asset+b < len(m))
                            if u > 0:
                                m_active += 1
                    m_is_strict = m_is_exact_k and (m_active == m_selected_count)
                    
                    # Priority Score (lower is better)
                    priority_score = 10000 + m_energy
                    if m_is_exact_k:
                        priority_score = 1000 + m_energy
                    if m_is_strict:
                        priority_score = m_energy
                        
                    if priority_score < current_best_priority:
                        current_best_priority = priority_score
                        current_best_raw_energy = m_energy
                        current_best_params = params.copy()
                        current_best_measurements = measurements
                        current_feasible_ratio = raw_feasible_ratio
                        logger.info(f"[NEW_BEST_SAMPLE] priority={priority_score:.4f} energy={m_energy:.4f} exact_k={m_is_exact_k} strict={m_is_strict}")
                
                # Feasibility-weighted objective calculation
                avg_card_violation = total_card_violation / len(measurements)
                LAMBDA_C = 100.0  # Cardinality violation weight
                
                feasibility_penalty = LAMBDA_C * avg_card_violation
                objective = avg_total_energy + feasibility_penalty
                
                # Prefer feasible states even at higher energy
                if raw_feasible_ratio > 0.5:
                    objective -= 10.0  # Feasibility bonus
                
                return objective
            except Exception as e:
                logger.warning(f"[QAOA_OBJECTIVE_ERROR] {e}")
                return 100.0

        bounds = [(0, np.pi)] * p + [(0, np.pi/2)] * p
        max_iter = 20 if req_meta.get("benchmark_mode") == "FAST" else 40
        
        res = minimize(
            objective_function, 
            initial_guess, 
            method='COBYLA',
            options={'maxiter': max_iter, 'rhobeg': 0.2},
            bounds=bounds
        )
        
        logger.info(
            f"[QAOA_DEPTH_AUDIT] solver=braket_local current_depth={p} "
            f"best_raw_energy={current_best_raw_energy:.6f} "
            f"best_priority={current_best_priority:.6f} "
            f"optimization_status={res.message}")

    # ── [FINAL VALIDATION RUN] ─────────────────────────────────────
    if current_best_params is not None:
        try:
            logger.info(f"[QAOA_VALIDATION] Running final validation with {validation_shots} shots")
            best_gamma = current_best_params[:depth]
            best_beta = current_best_params[depth:]
            circuit = build_qaoa_circuit(h, J, n_qubits, best_gamma, best_beta)
            task = device.run(circuit, shots=validation_shots)
            result = task.result()
            measurements = result.measurements
            if hasattr(measurements, 'tolist'):
                measurements = measurements.tolist()
            current_best_measurements = measurements
        except Exception as e:
            logger.warning(f"[QAOA_VALIDATION_ERROR] {e}")

    return current_best_measurements, current_best_raw_energy, current_best_params.tolist() if current_best_params is not None else []
