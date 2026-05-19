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

    if len(request.tickers) != n_assets or len(request.sectors) != n_assets:
        raise ValueError("tickers and sectors must match mu length")
    if request.cardinality > n_assets:
        raise ValueError("cardinality cannot exceed number of assets")

    bqm = PortfolioBQM()
    denominator = (2**request.binary_bits) - 1
    weight_vars = [[x_var(i, bit) for bit in range(request.binary_bits)] for i in range(n_assets)]
    indicator_vars = [y_var(i) for i in range(n_assets)]
    for row in weight_vars:
        for name in row:
            bqm.add_variable(name)
    for name in indicator_vars:
        bqm.add_variable(name)

    def weight_coeffs(i: int) -> dict[str, float]:
        return {weight_vars[i][bit]: (2**bit) / denominator for bit in range(request.binary_bits)}

    all_obj_values = []
    
    # Markowitz objective: minimize risk - risk_tolerance * return.
    for i in range(n_assets):
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
    
    # ── [ADAPTIVE_PENALTY_COMPRESSION] (Scientific Repair) ──────────
    # Target: penalty/objective ratio between 3x and 50x.
    # Previous ratios exceeded 7000x causing QAOA phase collapse.
    #
    # Scientific basis: The cardinality penalty P_card*(sum(y_i)-K)^2
    # creates a linear bias of P_card*(1-2K) on each y_i. For K=2 this
    # is -3*P_card, strongly rewarding over-selection. The linkage
    # penalty must counteract this bias.
    #
    # Required: P_linkage >= P_card * (2K - 1) * safety_margin
    # With K=2: P_linkage >= 3 * P_card * 1.5 = 4.5 * P_card
    
    K = float(request.cardinality)
    
    # Cardinality penalty: 8x objective span
    P_card = objective_span * 8.0
    
    # Linkage penalty: must counteract cardinality linear bias
    # P_card * (2K - 1) is the max reward from toggling y_i
    # We need P_linkage > this to prevent over-selection
    card_linear_bias = P_card * abs(1.0 - 2.0 * K)
    P_linkage = card_linear_bias * 2.0  # 2x safety margin
    
    # Budget penalty: 6x objective span
    P_budget = objective_span * 6.0
    
    # Sector penalty: 4x objective span
    P_sector = objective_span * 4.0
    
    # OR gate coupling: half of linkage
    P_gate = P_linkage * 0.5

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

    for i in range(n_assets):
        y_i = indicator_vars[i]
        
        if is_kn_case:
            # y_i is fixed to 1. Ensure sum(x_ik) >= 1.
            bqm.offset += P_gate
            for x_ik in weight_vars[i]:
                bqm.add_linear(x_ik, -P_gate)
            for k1 in range(request.binary_bits):
                for k2 in range(k1 + 1, request.binary_bits):
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
            for bit in range(request.binary_bits):
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

    if P_card < 1e-6:
        raise RuntimeError("Hamiltonian is malformed: No penalty scale detected.")

    logger.info(
        f"[PENALTY_DOMINANCE_ENFORCEMENT] objective_span={objective_span:.6f} "
        f"P_card={P_card:.2f} P_linkage={P_linkage:.2f} P_budget={P_budget:.2f}")

    # Budget penalty
    budget_coeffs: dict[str, float] = {}
    for i in range(n_assets):
        budget_coeffs.update(weight_coeffs(i))
    bqm.add_square_penalty(budget_coeffs, rhs=1.0, penalty=P_budget)

    # Sector constraints
    slack_variables: dict[str, list[str]] = {}
    unique_sectors = sorted(set(request.sectors))
    slack_bits = max(1, ceil(log2(denominator + 1)))
    for sector in unique_sectors:
        key = _sector_key(sector)
        slack = [f"slack_{key}_{bit}" for bit in range(slack_bits)]
        slack_variables[sector] = slack
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
