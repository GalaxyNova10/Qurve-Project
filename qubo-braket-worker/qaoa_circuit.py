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
                       gamma_list: list[float], beta_list: list[float], req_meta: dict = None):
    """Build a p-layer QAOA circuit for the Ising Hamiltonian.
    
    gamma_list/beta_list must be length p.
    """
    if not BRAKET_AVAILABLE:
        raise RuntimeError("Braket SDK not available")

    circuit = Circuit()
    depth = len(gamma_list)
    
    is_kn = req_meta.get("is_kn_case", False) if req_meta else False
    is_tn1 = req_meta and ("tn1" in req_meta.get("device", "").lower() or is_kn)
    if is_tn1:
        depth = 1 # Force p=1 for TN1

    # ── [QAOA INITIALIZATION] (Phase 1) ───────────────────────────────────
    if req_meta and "mu" in req_meta:
        is_tn1_init = is_tn1
        n_assets = len(req_meta["mu"])
        bits_per_asset = 0 if is_tn1_init else req_meta.get("binary_bits", 2)
        weight_bits_total = n_assets * bits_per_asset
        selection_start = weight_bits_total
        selection_end = min(weight_bits_total + n_assets, n_qubits)
        cardinality = req_meta.get("cardinality", 1)
        
        # 1. Weight bits and Slack bits get uniform superposition |+>
        for i in range(n_qubits):
            if i < selection_start or i >= selection_end:
                circuit.h(i)
                
        # 2. Selection bits: Shallow Feasible Warm-Start Manifold Initialization
        # A computational basis feasible seed + localized shallow XY entangling layer
        # This preserves TN1 scalability while ensuring exact K-cardinality initialization.
        n_sel = selection_end - selection_start
        k_sel = min(cardinality, n_sel)
        
        # ── [APPROXIMATE DICKE-STYLE SUPERPOSITION] (Gap 1) ──────────
        # Generate a diverse feasible superposition from a primary K-hot seed
        import random
        k_sel_indices = random.sample(range(n_sel), k_sel)
        for i in k_sel_indices:
            circuit.x(selection_start + i)
            
        if n_sel > 1 and not is_tn1_init:
            # For non-TN1, spread amplitude using explicit partial mixing angles to superpose
            # multiple valid K-hot states before QAOA begins.
            mixing_angles = [np.pi / 4.0, np.pi / 8.0]
            for angle in mixing_angles:
                for step in range(2): 
                    for i in range(step, n_sel - 1, 2):
                        q1 = selection_start + i
                        q2 = selection_start + i + 1
                        circuit.xy(q1, q2, angle)
    else:
        # Fallback for generic inputs
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
        if req_meta and "mu" in req_meta:
            is_tn1_mixer = req_meta and "tn1" in req_meta.get("device", "").lower()
            n_assets = len(req_meta["mu"])
            bits_per_asset = 0 if is_tn1_mixer else req_meta.get("binary_bits", 2)
            weight_bits_total = n_assets * bits_per_asset
            
            # Weight bits get standard Rx mixer
            for i in range(weight_bits_total):
                if i < n_qubits:
                    circuit.rx(i, 2.0 * beta)
                    
            # Selection bits get XY Ring mixer to preserve cardinality
            selection_start = weight_bits_total
            selection_end = min(weight_bits_total + n_assets, n_qubits)
            n_sel = selection_end - selection_start
            
            if n_sel > 1:
                # ── [STRICT LINEAR XY MIXER] ──────────
                # Mixer Sparsification Scheduling: Alternating Layers A and B
                # No ring closure (deleted (i+1) % n_sel) to preserve linear treewidth
                for i in range(0, n_sel - 1, 2): # Layer A
                    circuit.xy(selection_start + i, selection_start + i + 1, 2.0 * beta)
                for i in range(1, n_sel - 1, 2): # Layer B
                    circuit.xy(selection_start + i, selection_start + i + 1, 2.0 * beta)
            elif n_sel == 1:
                circuit.rx(selection_start, 2.0 * beta)
                
            # Slack bits get Phase-only evolution
            if selection_end < n_qubits:
                for i in range(selection_end, n_qubits):
                    circuit.phaseshift(i, 2.0 * beta)
        else:
            # Fallback for generic inputs
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
    # Infer is_tn1 mode from qubits vs assets (if K=N, it's also pure-selection)
    is_tn1 = "tn1" in req_meta.get("device", "").lower() or req_meta.get("is_kn_case", False)
    bits_per_asset = 0 if is_tn1 else req_meta.get("binary_bits", 2)
    weight_bits_total = n_assets * bits_per_asset

    all_energies = []
    raw_feasible_count = 0
    strict_positive_count = 0
    total_samples = len(measurements)
    
    for meas_idx, meas in enumerate(measurements):
        # ── [REGISTER_DECODE_ALIGNMENT_AUDIT] (Gap 2) ────────
        if meas_idx == 0:
            logger.info(f"[REGISTER_DECODE_ALIGNMENT_AUDIT] "
                        f"measurements_length={len(meas)} "
                        f"weight_bits_total={weight_bits_total} "
                        f"selection_start={weight_bits_total} "
                        f"selection_end={weight_bits_total + n_assets} "
                        f"is_kn={is_kn} bits_per_asset={bits_per_asset}")

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
                if is_tn1:
                    weights[i] = 1.0 / cardinality
                else:
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
        
    device_name = req_meta.get("device", "sv1").lower() if req_meta else "sv1"
    is_tn1 = "tn1" in device_name
    
    # ── [HAMILTONIAN LOCALITY TRUNCATION] ────────
    if is_tn1:
        depth = 1
        logger.info("[TN1_DEVICE_PROFILE] Forcing p=1 for TN1 execution.")
        
        # ── [TN1-SPECIFIC HAMILTONIAN LOCALITY REDUCTION] (Gap 3) ────────
        # TN1 treewidth depends on interaction geometry, not just density.
        # We enforce a banded structure (locality) and aggressive thresholding.
        locality_bandwidth = 4 # Maximum index distance for most interactions
        
        total_possible = (n_qubits * (n_qubits - 1)) / 2
        active_j = np.count_nonzero(J) / 2
        current_density = active_j / max(1, total_possible)
        
        if active_j > 0:
            # 1. Base thresholding
            non_zero_J = np.abs(J[J != 0])
            base_cutoff = np.percentile(non_zero_J, 75) # Keep top 25% generally
            
            for i in range(n_qubits):
                for j in range(i + 1, n_qubits):
                    if J[i, j] == 0:
                        continue
                    distance = j - i
                    
                    # 2. Locality-aware pruning: rapidly decay allowed strength by distance
                    # Interactions spanning distance > 4 require strictly higher covariance strength to survive
                    if distance > locality_bandwidth:
                        distance_penalty_factor = (distance / locality_bandwidth) ** 2
                        effective_cutoff = base_cutoff * distance_penalty_factor
                        if abs(J[i, j]) < effective_cutoff:
                            J[i, j] = 0.0
                            J[j, i] = 0.0
                            
            new_active_j = np.count_nonzero(J) / 2
            new_density = new_active_j / max(1, total_possible)
            logger.info(f"[TN1_CONTRACTION_AUDIT] Applied Locality-Aware Pruning. Density: {current_density:.4f} -> {new_density:.4f}")
    
    n_assets = len(req_meta["mu"])
    cardinality_target = req_meta["cardinality"]
    
    current_best_params = None
    current_best_measurements = None
    current_best_raw_energy = float("inf")
    current_best_priority = float("inf")
    current_feasible_ratio = 0.0
    
    # ── [SHOT-ADAPTIVE EXECUTION] (Phase 6) ─────────────
    optimization_shots = 64
    validation_shots = min(1000, max(shots, 512))
    
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
            logger.info(f"[QAOA_WARM_START] source_depth={p-1} target_depth={p}")

        # ── [CRITICAL REFINEMENT 3: OPTIMIZER LANDSCAPE AUDIT] State ─────────────
        objective_history = []

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
                total_weighted_energy = 0.0
                total_samples = len(measurements)
                total_strict_samples = 0
                
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
                        
                    # Calculate feasibility weight for this sample
                    if m_is_exact_k:
                        feasibility_weight = 1.0
                    else:
                        feasibility_weight = max(0.1, 1.0 - (cardinality_violation * 0.2))
                        
                    weighted_energy = m_energy * feasibility_weight
                    total_weighted_energy += weighted_energy
                    
                    # Check positive allocation
                    m_active = 0
                    for i in range(n_assets):
                        if m_selection[i]:
                            u = sum(m[i*bits_per_asset+b]*(2**b) for b in range(bits_per_asset) if i*bits_per_asset+b < len(m))
                            if u > 0:
                                m_active += 1
                    m_is_strict = m_is_exact_k and (m_active == m_selected_count)
                    if m_is_strict:
                        total_strict_samples += 1
                    
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
                
                # ── [PHASE 7: OPTIMIZER REALISM (Adaptive Feasibility Shaping)] ─────────────
                avg_weighted_energy = total_weighted_energy / total_samples if total_samples > 0 else 0.0
                raw_strict_ratio = total_strict_samples / total_samples if total_samples > 0 else 0.0
                
                # ── [FEASIBILITY-FIRST OPTIMIZATION] (Phase 6: Smooth Differentiable Loss) ─────────────
                avg_cardinality_violation = (total_card_violation / total_samples) if total_samples > 0 else 0.0
                
                # We use a smooth continuous differentiable loss function instead of 
                # discrete step-like strict_ratio priorities which cause COBYLA to fail.
                lambda_1 = 5000.0  # Smooth feasibility penalty weight
                lambda_2 = 1000.0  # Expected constraint violation weight
                lambda_3 = 1.0     # Energy weight
                
                # Smooth feasibility penalty (quadratic distance from feasible ratio 1.0)
                smooth_feasibility_penalty = (1.0 - raw_feasible_ratio) ** 2
                expected_constraint_violation = avg_cardinality_violation ** 2
                
                objective = (lambda_1 * smooth_feasibility_penalty) + \
                            (lambda_2 * expected_constraint_violation) + \
                            (lambda_3 * avg_weighted_energy)
                
                objective_history.append(objective)
                
                # ── [REGISTER_ISOLATION_AUDIT] (Phase 3) ─────────────
                logger.info(
                    f"[REGISTER_ISOLATION_AUDIT] depth={p} "
                    f"selection_purity={raw_feasible_ratio:.4f} "
                    f"topology_penalty={topology_penalty:.2f} "
                    f"objective={objective:.4f}"
                )
                
                return objective
            except Exception as e:
                logger.warning(f"[QAOA_OBJECTIVE_ERROR] {e}")
                # Return dynamically scaled penalty, not static 100.0 or 1e6
                penalty = 1000.0 * p
                if objective_history:
                    penalty = np.mean(objective_history) + 500.0 * p
                return float(penalty)

        bounds = [(0, np.pi)] * p + [(0, np.pi/2)] * p
        max_iter = 20 if req_meta.get("benchmark_mode") == "FAST" else 40
        
        res = minimize(
            objective_function, 
            initial_guess, 
            method='COBYLA',
            options={'maxiter': max_iter, 'rhobeg': 0.2},
            bounds=bounds
        )
        
        # ── [CRITICAL REFINEMENT 3: OPTIMIZER LANDSCAPE AUDIT] ─────────────
        if len(objective_history) > 1:
            obj_arr = np.array(objective_history)
            diffs = np.diff(obj_arr)
            local_gradient_variance = float(np.var(diffs))
            loss_curvature = float(np.mean(np.abs(np.diff(diffs)))) if len(objective_history) > 2 else 0.0
            obj_std = float(np.std(obj_arr))
            obj_mean_abs = float(np.mean(np.abs(obj_arr)))
            barren_plateau_risk = max(0.0, 1.0 - (obj_std / max(1e-9, obj_mean_abs)))
            
            # Optimization stagnation score
            optimization_stagnation_score = max(0.0, 1.0 - (local_gradient_variance / max(1e-9, loss_curvature)))
        else:
            local_gradient_variance = 0.0
            loss_curvature = 0.0
            barren_plateau_risk = 1.0
            optimization_stagnation_score = 1.0

        logger.info(
            f"[OPTIMIZER_LANDSCAPE_AUDIT] depth={p} "
            f"evaluations={len(objective_history)} "
            f"local_gradient_variance={local_gradient_variance:.4f} "
            f"loss_curvature={loss_curvature:.4f} "
            f"barren_plateau_risk={barren_plateau_risk:.4f} "
            f"optimization_stagnation_score={optimization_stagnation_score:.4f}"
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
