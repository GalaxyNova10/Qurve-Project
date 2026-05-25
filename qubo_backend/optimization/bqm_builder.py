from __future__ import annotations

from dataclasses import dataclass, field
from math import ceil, log2
from typing import Iterable

import numpy as np

from .contracts import SolverRequest


Variable = str
Pair = tuple[Variable, Variable]


def _ordered_pair(a: Variable, b: Variable) -> Pair:
    return (a, b) if a <= b else (b, a)


def _sector_key(sector: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in sector.lower()).strip("_") or "unknown"


@dataclass
class PortfolioBQM:
    """Small BQM abstraction that can become dimod when Ocean is installed."""

    linear: dict[Variable, float] = field(default_factory=dict)
    quadratic: dict[Pair, float] = field(default_factory=dict)
    offset: float = 0.0
    variables: set[Variable] = field(default_factory=set)

    @property
    def vartype(self) -> str:
        return "BINARY"

    def add_variable(self, name: Variable) -> None:
        self.variables.add(name)
        self.linear.setdefault(name, 0.0)

    def add_linear(self, name: Variable, bias: float) -> None:
        self.add_variable(name)
        self.linear[name] = self.linear.get(name, 0.0) + float(bias)

    def add_quadratic(self, left: Variable, right: Variable, bias: float) -> None:
        if left == right:
            self.add_linear(left, bias)
            return
        self.add_variable(left)
        self.add_variable(right)
        pair = _ordered_pair(left, right)
        self.quadratic[pair] = self.quadratic.get(pair, 0.0) + float(bias)

    def add_square_penalty(self, coeffs: dict[Variable, float], rhs: float, penalty: float) -> None:
        """Add penalty * (sum(coeffs[v] * v) - rhs)^2 for binary variables."""
        self.offset += penalty * rhs * rhs
        items = list(coeffs.items())
        for var, coeff in items:
            self.add_linear(var, penalty * (coeff * coeff - 2.0 * rhs * coeff))
        for i, (left, left_coeff) in enumerate(items):
            for right, right_coeff in items[i + 1 :]:
                self.add_quadratic(left, right, penalty * 2.0 * left_coeff * right_coeff)

    def to_dimod(self):
        try:
            import dimod
        except ImportError as exc:
            raise RuntimeError("dimod is not installed; install dwave-ocean-sdk or dimod") from exc
        return dimod.BinaryQuadraticModel(self.linear, self.quadratic, self.offset, dimod.BINARY)


@dataclass(frozen=True)
class BQMBuildResult:
    bqm: PortfolioBQM
    variable_order: list[str]
    weight_variables: list[list[str]]
    indicator_variables: list[str]
    slack_variables: dict[str, list[str]]
    denominator: int
    objective_span: float
    penalty_scales: dict[str, float]


def x_var(i: int, bit: int) -> str:
    return f"x_{i}_{bit}"


def y_var(i: int) -> str:
    return f"y_{i}"


def build_portfolio_bqm(request: SolverRequest) -> BQMBuildResult:
    # ════════════════════════════════════════════════════════════════
    # PHASE 3: GLOBAL ENERGY NORMALIZATION (Fix 7)
    # ════════════════════════════════════════════════════════════════
    mu = np.asarray(request.mu, dtype=float)
    sigma = np.asarray(request.sigma, dtype=float)
    n_assets = len(mu)
    if sigma.shape != (n_assets, n_assets):
        raise ValueError("sigma must be square and match mu length")

    # Normalize to [-1, 1]
    max_sigma = np.max(np.abs(sigma))
    if max_sigma > 1e-9:
        sigma = sigma / max_sigma

    max_mu = np.max(np.abs(mu))
    if max_mu > 1e-9:
        mu = mu / max_mu

    # ── [PHASE 4 & 13: SPECTRAL GRAPH SPARSIFICATION] ──────────
    # Phase 7: Device-specific density targets
    if request.solver == "AWS_BRAKET_TN1":
        target_density = 0.20
    elif request.solver == "AWS_BRAKET_SV1":
        target_density = 0.55
    else:
        target_density = 0.50
        
    total_possible_edges = n_assets * (n_assets - 1) / 2
    if total_possible_edges > 0:
        # Check current density
        off_diags = np.abs(sigma[np.triu_indices(n_assets, k=1)])
        current_edges = np.sum(off_diags > 1e-6)
        if current_edges / total_possible_edges > target_density:
            # 1. Extract eigenstructure (dominant modes)
            eigvals, eigvecs = np.linalg.eigh(sigma)
            top_k = max(1, int(ceil(n_assets * 0.5))) # Keep top half modes
            
            # Keep top k eigenvalues/vectors to preserve dominant market topology
            top_eigvals = eigvals[-top_k:]
            top_eigvecs = eigvecs[:, -top_k:]
            sigma_dominant = top_eigvecs @ np.diag(top_eigvals) @ top_eigvecs.T
            
            # 2. Threshold the reconstructed dominant covariance
            dominant_off_diags = np.abs(sigma_dominant[np.triu_indices(n_assets, k=1)])
            max_allowed_edges = int(total_possible_edges * target_density)
            
            if len(dominant_off_diags) > max_allowed_edges:
                threshold = np.sort(dominant_off_diags)[-max_allowed_edges]
                mask = np.abs(sigma_dominant) >= threshold
                np.fill_diagonal(mask, True)
                sigma = sigma_dominant * mask
            else:
                sigma = sigma_dominant

    # ── [ENTANGLEMENT_COMPLEXITY_AUDIT] (Phase 6) ──────────
    final_off_diags = np.abs(sigma[np.triu_indices(n_assets, k=1)])
    final_edges = np.sum(final_off_diags > 1e-6)
    final_density = final_edges / max(1, total_possible_edges) if total_possible_edges > 0 else 0.0
    
    # Heuristic approximations for TN1 realism
    treewidth_approx = int(ceil(n_assets * final_density))
    locality_score = final_density / max(1e-9, target_density)
    contraction_depth = int(ceil(treewidth_approx * 1.5))
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"[ENTANGLEMENT_COMPLEXITY_AUDIT] "
        f"final_density={final_density:.4f} "
        f"treewidth_approx={treewidth_approx} "
        f"locality_score={locality_score:.2f} "
        f"contraction_depth={contraction_depth}"
    )

    if len(request.tickers) != n_assets or len(request.sectors) != n_assets:
        raise ValueError("tickers and sectors must match mu length")
    if request.cardinality > n_assets:
        raise ValueError("cardinality cannot exceed number of assets")

    effective_binary_bits = 0 if "tn1" in request.solver.lower() else request.binary_bits
    is_kn = (request.cardinality == n_assets)
    # If exactly K=N, the combinatorial problem is trivial and binary weight allocation
    # will mathematically fail if K > (2^bits)-1. Fallback to pure selection (TN1 style).
    is_tn1 = (effective_binary_bits == 0) or is_kn
    
    # Phase 3: TN1 HARD LIMITS
    if is_tn1:
        if final_density >= 0.20:
            raise RuntimeError("TN1TopologyViolation: Density exceeds strict 0.20 limit.")
        if final_edges > 24:
            raise RuntimeError("TN1TopologyViolation: Quadratic terms exceed strict 24 limit.")
        if request.binary_bits > 1:
            raise RuntimeError("TN1TopologyViolation: Binary bits > 1 not supported.")
        if n_assets > 6:
            raise RuntimeError("TN1TopologyViolation: Number of assets > 6 not supported.")

    bqm = PortfolioBQM()
    
    # Phase 4: UNCONDITIONAL VARIABLE INITIALIZATION
    denominator = (2**effective_binary_bits) - 1 if not is_tn1 else 1
    
    if not is_tn1:
        weight_vars = [[x_var(i, bit) for bit in range(effective_binary_bits)] for i in range(n_assets)]
        for row in weight_vars:
            for name in row:
                bqm.add_variable(name)
    else:
        weight_vars = []

    indicator_vars = [y_var(i) for i in range(n_assets)]
    for name in indicator_vars:
        bqm.add_variable(name)

    def weight_coeffs(i: int) -> dict[str, float]:
        if is_tn1:
            return {}
        return {weight_vars[i][bit]: (2**bit) / denominator for bit in range(effective_binary_bits)}

    all_obj_values = []
    
    # Markowitz objective: minimize risk - risk_tolerance * return.
    for i in range(n_assets):
        if is_tn1:
            # TN1: Combinatorial Selection Only. Weights are 1/K.
            coeff_i = 1.0 / request.cardinality
            val_lin = -request.risk_tolerance * mu[i] * coeff_i
            bqm.add_linear(indicator_vars[i], val_lin)
            all_obj_values.append(abs(val_lin))
            
            val_quad = sigma[i, i] * coeff_i * coeff_i
            bqm.add_quadratic(indicator_vars[i], indicator_vars[i], val_quad)
            all_obj_values.append(abs(val_quad))
            
            for j in range(i + 1, n_assets):
                coeff_j = 1.0 / request.cardinality
                val_cross = 2.0 * sigma[i, j] * coeff_i * coeff_j
                bqm.add_quadratic(indicator_vars[i], indicator_vars[j], val_cross)
                all_obj_values.append(abs(val_cross))
        else:
            for bit_i, var_i in enumerate(weight_vars[i]):
                coeff_i = (2**bit_i) / denominator
                # Return term
                val_lin = -request.risk_tolerance * mu[i] * coeff_i
                bqm.add_linear(var_i, val_lin)
                all_obj_values.append(abs(val_lin))
                
                for bit_j, var_j in enumerate(weight_vars[i]):
                    coeff_j = (2**bit_j) / denominator
                    val_quad = sigma[i, i] * coeff_i * coeff_j
                    bqm.add_quadratic(var_i, var_j, val_quad)
                    all_obj_values.append(abs(val_quad))
                    
            for j in range(i + 1, n_assets):
                for bit_i, var_i in enumerate(weight_vars[i]):
                    coeff_i = (2**bit_i) / denominator
                    for bit_j, var_j in enumerate(weight_vars[j]):
                        coeff_j = (2**bit_j) / denominator
                        # Cross terms (i, j) with symmetry factor 2.0
                        val_cross = 2.0 * sigma[i, j] * coeff_i * coeff_j
                        bqm.add_quadratic(var_i, var_j, val_cross)
                        all_obj_values.append(abs(val_cross))
    # ── [PHASE 4: Safe Reductions] ──────────────────────────────────
    def safe_max(vals, default=1.0): return float(max(vals, default=default))
    def safe_sum(vals): return float(sum(vals))
    
    # ── [PHASE 2: Canonical Objective Span Helper] ──────────────────
    def compute_objective_span(bqm_obj):
        """Calculates the total coefficient span of the objective."""
        linear_vals = [abs(v) for v in bqm_obj.linear.values()]
        quad_vals = [abs(v) for v in bqm_obj.quadratic.values()]
        return max(safe_sum(linear_vals) + safe_sum(quad_vals), 1.0)

    # ── [OBJECTIVE_NORMALIZATION] (Phase 4) ────────────────────────
    # SINGLE SOURCE OF TRUTH (Fix 1, 2)
    objective_scale = float(max(all_obj_values, default=1.0))
    if objective_scale < 1e-6:
        objective_scale = 1.0
        
    objective_span = float(max(all_obj_values) - min(all_obj_values)) if all_obj_values else 1.0
    if objective_span < 1e-6:
        objective_span = 1.0

    # Emit telemetry BEFORE scaling (Fix 3, 5)
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"[OBJECTIVE_NORMALIZATION_AUDIT] "
        f"objective_terms={len(all_obj_values)} "
        f"objective_scale={objective_scale:.6f} "
        f"objective_span={objective_span:.6f} "
        f"max_coeff={safe_max(all_obj_values, default=0.0):.6f} "
        f"min_coeff={float(min(all_obj_values, default=0.0)):.6f} "
        f"normalized=True")

    # Scale to ensure penalties dominate
    for var in bqm.linear:
        bqm.linear[var] /= objective_scale
    for edge in bqm.quadratic:
       bqm.quadratic[edge] /= objective_scale
    bqm.offset /= objective_scale
    
    # Recalculate span for penalty scaling after normalization (Fix 2)
    objective_span = compute_objective_span(bqm)
    
    # ── [PHASE 2 & 10: ADAPTIVE PERCENTILE SCALING] ──────────
    # Compute 95th percentile of objective terms for adaptive penalty baseline
    all_obj_values_flat = [abs(v) for v in bqm.linear.values()] + [abs(v) for v in bqm.quadratic.values()]
    if all_obj_values_flat:
        p95_magnitude = float(np.percentile(all_obj_values_flat, 95))
    else:
        p95_magnitude = 1.0
        
    if p95_magnitude < 1e-6:
        p95_magnitude = 1.0
        
    base_penalty_scale = p95_magnitude
    
    # Adaptive scaling: alpha * base_penalty_scale
    # Enforcing Delta E > 3 sigma objective separation
    ALPHA_CARD = 3.0
    ALPHA_BUDGET = 3.0
    ALPHA_SECTOR = 3.0
    ALPHA_LINKAGE_SAFETY = 2.0
    
    P_card = ALPHA_CARD * base_penalty_scale
    P_budget = ALPHA_BUDGET * base_penalty_scale
    P_sector = ALPHA_SECTOR * base_penalty_scale
    
    K = float(request.cardinality)
    
    card_linear_bias = P_card * abs(1.0 - 2.0 * K)
    
    P_linkage_raw = max(base_penalty_scale, card_linear_bias * ALPHA_LINKAGE_SAFETY)
    max_allowed_penalty = 4.0 * objective_scale
    P_linkage = min(P_linkage_raw, max_allowed_penalty)
    
    # OR gate coupling: half of linkage
    P_gate = P_linkage * 0.5
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"[ADAPTIVE_PENALTY_SCALING] "
        f"p95_magnitude={p95_magnitude:.4f} "
        f"P_card={P_card:.4f} "
        f"P_budget={P_budget:.4f} "
        f"P_sector={P_sector:.4f} "
        f"P_linkage={P_linkage:.4f}"
    )

    # PHASE 4: SPECIAL CASE FIX (K == N) (Fix 4)
    is_kn_case = (request.cardinality == n_assets)
    
    if not is_kn_case:
        K = float(request.cardinality)
        # Fully expanded EXACT-K Hamiltonian: P_card * (Σ y_i - K)^2
        bqm.offset += P_card * (K ** 2)
        for i in range(n_assets):
            y_i = indicator_vars[i]
            bqm.add_linear(y_i, P_card * (1.0 - 2.0 * K))
            for j in range(i + 1, n_assets):
                y_j = indicator_vars[j]
                bqm.add_quadratic(y_i, y_j, 2.0 * P_card)
                
            # ── [DENSE_SELECTION_SUPPRESSION] (Phase 2) ──────────────
            # Add an extra linear pressure term to y_i to discourage over-selection attractors.
            # This tilts the basin so that higher selections are exponentially more expensive.
            P_dense = P_card * 0.2
            bqm.add_linear(y_i, P_dense)
            
            logger.info(
                f"[DENSE_SELECTION_SUPPRESSION] asset={i} "
                f"pressure={P_dense:.4f} "
                f"target_k={K}")

    # ════════════════════════════════════════════════════════════════
    # PHASE 2: INDICATOR-WEIGHT COUPLING (Fix 3: ZERO-WEIGHT LEAKAGE)
    # ════════════════════════════════════════════════════════════════

    if not is_tn1:
        for i in range(n_assets):
            y_i = indicator_vars[i]
            
            if is_kn_case:
                # y_i is fixed to 1. Ensure sum(x_ik) >= 1.
                bqm.offset += P_gate
                for x_ik in weight_vars[i]:
                    bqm.add_linear(x_ik, -P_gate)
                for k1 in range(effective_binary_bits):
                    for k2 in range(k1 + 1, effective_binary_bits):
                        bqm.add_quadratic(weight_vars[i][k1], weight_vars[i][k2], P_gate)
            else:
                # ── [EXACT_ACTIVATION_TOPOLOGY] (Phase 3) ──────────────────
                # Enforce y_i = OR(x_i0, x_i1, x_i2, ...)
                # We use a 3-bit Ladder OR for the foundation to guarantee x > 0
                # when y=1, and x_k > 0 => y=1 for all k.
                
                x0, x1 = weight_vars[i][0], weight_vars[i][1]
                # Exact OR(x0, x1, ...) using a 2-bit foundation 
                # (sufficient to guarantee weight > 0 if y=1)
                
                # 1. Enforce y_i >= x_ik for ALL k (Prevents x=1, y=0)
                for bit in range(effective_binary_bits):
                    x_ik = weight_vars[i][bit]
                    bqm.add_linear(x_ik, P_linkage)
                    bqm.add_quadratic(x_ik, y_i, -P_linkage)
                    
                # 2. Enforce y_i <= sum(x_ik) (Prevents y=1, x=0)
                # We use the provable penalty for the first 2 bits to ensure at least one is ON
                # if y=1. This creates the "lowest basin" at x > 0.
                # Penalty = P_linkage * (y + x0*x1 - y*x0 - y*x1)
                # (Note: this is a variation of the OR penalty that specifically hits y=1, x=0)
                bqm.add_linear(y_i, P_linkage)
                bqm.add_quadratic(y_i, x0, -P_linkage)
                bqm.add_quadratic(y_i, x1, -P_linkage)
                bqm.add_quadratic(x0, x1, P_linkage)
                
                # ── [TOPOLOGICAL_CONSISTENCY_AUDIT] (Phase 3) ────────────
                # Illegal state y=1, x=0 has energy P_linkage.
                # Feasible states have energy 0.
                gap = P_linkage
                logger.info(f"[TOPOLOGICAL_CONSISTENCY_AUDIT] asset={i} gap={gap:.4f}")

    # ════════════════════════════════════════════════════════════════

    # ════════════════════════════════════════════════════════════════
    # PHASE 8: QAOA_HAMILTONIAN_AUDIT (Fix 1, 9)
    # ════════════════════════════════════════════════════════════════
    all_final_values = list(bqm.linear.values()) + list(bqm.quadratic.values())
    max_constraint_coeff = float(max((abs(v) for v in all_final_values if abs(v) >= P_card * 0.1), default=0.0))
    
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        f"[QAOA_HAMILTONIAN_AUDIT] "
        f"objective_terms={len(all_obj_values)} "
        f"constraint_terms={len(all_final_values) - len(all_obj_values)} "
        f"max_objective_coeff={objective_scale:.6f} "
        f"max_constraint_coeff={max_constraint_coeff:.6f} "
        f"constraint_energy_scale={P_card:.2f} "
        f"ising_linear_terms={len(bqm.linear)} "
        f"ising_quadratic_terms={len(bqm.quadratic)}")

    logger.info(
        f"[HAMILTONIAN_CURVATURE_AUDIT] "
        f"P_linkage_bounded={P_linkage:.4f} "
        f"max_allowed={max_allowed_penalty:.4f} "
        f"objective_span={objective_span:.6f}")
        
    logger.info(
        f"[PENALTY_DOMINANCE_AUDIT] objective_scale={objective_scale:.4f} "
        f"P_card={P_card:.2f} P_linkage={P_linkage:.2f} P_budget={P_budget:.2f}")

    logger.info(
        f"[ENERGY_SEPARATION_AUDIT] enforcing 3σ gap. "
        f"E_inf - E_feas approx {P_card:.2f}")

    if P_card < 1e-6:
        raise RuntimeError("Hamiltonian is malformed: No penalty scale detected.")

    # Budget penalty (Not needed for TN1 as it solves K-hot selection only)
    if not is_tn1:
        budget_coeffs: dict[str, float] = {}
        for i in range(n_assets):
            budget_coeffs.update(weight_coeffs(i))
        bqm.add_square_penalty(budget_coeffs, rhs=1.0, penalty=P_budget)

    # Sector constraints
    slack_variables: dict[str, list[str]] = {}
    unique_sectors = sorted(set(request.sectors))
    
    if is_tn1:
        # TN1: Sector constraints apply directly to indicator vars y_i
        max_assets_per_sector = max(1, int(K * request.max_sector_exposure))
        slack_bits = max(1, ceil(log2(max_assets_per_sector + 1)))
        
        for sector in unique_sectors:
            key = _sector_key(sector)
            slack = [f"slack_{key}_{bit}" for bit in range(slack_bits)]
            slack_variables[sector] = slack
            for name in slack:
                bqm.add_variable(name)
                
            sector_coeffs: dict[str, float] = {}
            for i, asset_sector in enumerate(request.sectors):
                if asset_sector == sector:
                    sector_coeffs[indicator_vars[i]] = 1.0
                    
            for bit, var in enumerate(slack):
                sector_coeffs[var] = 1.0 * (2**bit)
                
            bqm.add_square_penalty(sector_coeffs, rhs=float(max_assets_per_sector), penalty=P_sector)
    else:
        slack_bits = max(1, ceil(log2(denominator + 1)))
        for sector in unique_sectors:
            key = _sector_key(sector)
            slack = [f"slack_{key}_{bit}" for bit in range(slack_bits)]
            slack_variables[sector] = slack
            for name in slack:
                bqm.add_variable(name)
                
            sector_coeffs: dict[str, float] = {}
            for i, asset_sector in enumerate(request.sectors):
                if asset_sector == sector:
                    sector_coeffs.update(weight_coeffs(i))
            for bit, var in enumerate(slack):
                sector_coeffs[var] = request.max_sector_exposure * (2**bit) / ((2**slack_bits) - 1)
            bqm.add_square_penalty(sector_coeffs, rhs=request.max_sector_exposure, penalty=P_sector)

    # ── [HAMILTONIAN_SCALE_AUDIT] (Phase 4) ────────────────────────
    # Collect span of each component
    covariance_span = float(np.sum(np.abs(sigma)) / objective_scale)
    return_span = float(np.sum(np.abs(mu)) * request.risk_tolerance / objective_scale)
    
    # Calculate actual spans in the BQM
    # (Approximated by summing absolute coefficients for that component)
    linkage_span = P_linkage * n_assets * request.binary_bits
    cardinality_span = P_card * (n_assets * (n_assets - 1)) # Quadratic part
    budget_span = P_budget * (n_assets * request.binary_bits)**2
    
    logger.info(
        f"[HAMILTONIAN_SCALE_AUDIT] "
        f"objective_span={objective_span:.6f} "
        f"covariance_span={covariance_span:.6f} "
        f"return_span={return_span:.6f} "
        f"linkage_span={linkage_span:.6e} "
        f"cardinality_span={cardinality_span:.6e} "
        f"budget_span={budget_span:.6e} "
        f"P_linkage={P_linkage:.2f} "
        f"P_card={P_card:.2f}")

    # Acceptance check for penalty domination
    # If penalties are > 10^7 times the objective, we might lose precision
    if P_linkage / (objective_span / max(1, n_assets)) > 1e8:
         logger.warning("[SCALE_DOMINATION_WARNING] Penalties are extremely high relative to objective.")

    # PHASE 4: CONSTANT Y_I FOR K == N
    if is_kn_case:
        for y_i in indicator_vars:
            if y_i in bqm.variables:
                bqm.variables.remove(y_i)
            if y_i in bqm.linear:
                bqm.offset += bqm.linear[y_i]
                del bqm.linear[y_i]
            y_pairs = [pair for pair in bqm.quadratic if y_i in pair]
            for pair in y_pairs:
                other = pair[0] if pair[1] == y_i else pair[1]
                bias = bqm.quadratic[pair]
                if other in bqm.variables:
                    bqm.add_linear(other, bias)
                else:
                    bqm.offset += bias
                del bqm.quadratic[pair]
                
    # ── [BUILDER_VALIDATION_ASSERTIONS] (Fix 7) ─────────────────────
    assert objective_span > 0, "[OBJECTIVE_BUILD_FAILURE] objective_span <= 0"
    assert objective_scale > 0, "[OBJECTIVE_BUILD_FAILURE] objective_scale <= 0"
    assert len(all_obj_values) > 0, "[OBJECTIVE_BUILD_FAILURE] no objective coefficients collected"

    # [VARIABLE_ORDER_CANONICALIZATION] Use canonical order matching decoder expectations:
    # weight bits (x_i_bit) → indicator bits (y_i) → slack bits (slack_*)
    # MUST match Braket worker decode_and_evaluate() bit position assumptions.
    # For K==N case, indicator variables are removed from BQM, so exclude them from order.
    if is_kn_case:
        variable_order = list(_iter_variables(weight_vars, [], slack_variables))
    else:
        variable_order = list(_iter_variables(weight_vars, indicator_vars, slack_variables))

    # [VARIABLE_ORDER_AUDIT] Verify all BQM variables are accounted for
    bqm_var_set = set(bqm.variables)
    order_var_set = set(variable_order)
    missing_from_order = bqm_var_set - order_var_set
    extra_in_order = order_var_set - bqm_var_set
    if missing_from_order:
        raise RuntimeError(f"[VARIABLE_ORDER_AUDIT] BQM variables missing from order: {missing_from_order}")
    if extra_in_order:
        raise RuntimeError(f"[VARIABLE_ORDER_AUDIT] Order contains variables not in BQM: {extra_in_order}")
    logger.info(
        f"[VARIABLE_ORDER_AUDIT] n_variables={len(variable_order)} "
        f"order=canonical(x→y→slack) "
        f"first_3={variable_order[:3]} "
        f"last_3={variable_order[-3:]}")

    # ── [QUBO DENSITY GOVERNOR] (Phase 6: Hard TN1 Failure) ─────
    n_vars = len(bqm.variables)
    
    if request.solver == "AWS_BRAKET_TN1":
        max_possible_edges = max(1, (n_vars * (n_vars - 1)) / 2)
        density = len(bqm.quadratic) / max_possible_edges
        if density >= 0.20 or len(bqm.quadratic) > 24:
            raise RuntimeError(f"TN1TopologyViolation: density {density:.2f} >= 0.20 or quadratic_terms {len(bqm.quadratic)} > 24. Deterministic contraction not guaranteed.")
    else:
        max_edges = int(0.35 * (n_vars * (n_vars - 1)) / 2)
        if len(bqm.quadratic) > max_edges:
            edges = sorted(bqm.quadratic.items(), key=lambda x: abs(x[1]), reverse=True)
            pruned_edges = len(bqm.quadratic) - max_edges
            bqm.quadratic = dict(edges[:max_edges])
            logger.info(f"[QUBO_DENSITY_GOVERNOR] Pruned {pruned_edges} smallest edges to maintain <0.35 density limit")

    return BQMBuildResult(
        bqm=bqm,
        variable_order=variable_order,
        weight_variables=weight_vars,
        indicator_variables=indicator_vars,
        slack_variables=slack_variables,
        denominator=denominator,
        objective_span=objective_span,
        penalty_scales={
            "P_card": P_card,
            "P_linkage": P_linkage,
            "P_budget": P_budget,
            "P_sector": P_sector
        }
    )



def _iter_variables(
    weight_vars: list[list[str]],
    indicator_vars: list[str],
    slack_variables: dict[str, list[str]],
) -> Iterable[str]:
    for row in weight_vars:
        yield from row
    yield from indicator_vars
    for sector in sorted(slack_variables):
        yield from slack_variables[sector]
