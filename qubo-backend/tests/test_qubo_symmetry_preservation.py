"""
Preservation Property Tests — QUBO Symmetry Bugfix
====================================================

**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

OBSERVATION-FIRST METHODOLOGY:
These tests are written BEFORE the fix is applied. They capture baseline
behavior on UNFIXED code for inputs that do NOT trigger the bug condition
(i.e., diagonal-only models and BQM storage invariance).

EXPECTED OUTCOME: All tests PASS on unfixed code.
If any test fails on unfixed code, investigate before proceeding to the fix.

Preservation properties tested:
  1. Diagonal preservation: Q[i,i] == sum(bqm.linear[var]) for each index i
  2. BQM storage invariance: bqm.quadratic[_ordered_pair(l,r)] == bias after add_quadratic
  3. Serialization format invariance: flat list has n_vars**2 floats
  4. Diagonal-only model symmetry: np.allclose(Q, Q.T) passes for linear-only models
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.qubo_model import QuboModel, to_qubo_matrix
from qubo_backend.optimization.bqm_builder import (
    BQMBuildResult,
    PortfolioBQM,
    _ordered_pair,
    build_portfolio_bqm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_linear_only_model(n_vars: int = 3, biases: list[float] | None = None) -> QuboModel:
    """Build a QuboModel with only linear (diagonal) terms — no quadratic terms.

    This is the canonical non-buggy input: diagonal matrices are trivially
    symmetric, so to_qubo_matrix() should return np.allclose(Q, Q.T) == True
    on both unfixed and fixed code.
    """
    if biases is None:
        biases = [float(i + 1) for i in range(n_vars)]

    bqm = PortfolioBQM()
    var_names = [f"x_{i}_0" for i in range(n_vars)]
    for name, bias in zip(var_names, biases):
        bqm.add_variable(name)
        bqm.add_linear(name, bias)

    build = BQMBuildResult(
        bqm=bqm,
        variable_order=var_names,
        weight_variables=[[v] for v in var_names],
        indicator_variables=[],
        slack_variables={},
        denominator=1,
        objective_span=1.0,
    )
    request = SolverRequest(
        mu=[0.1] * n_vars,
        sigma=[[1.0 if i == j else 0.0 for j in range(n_vars)] for i in range(n_vars)],
        tickers=[f"T{i}" for i in range(n_vars)],
        sectors=["Tech"] * n_vars,
        cardinality=1,
        binary_bits=2,
    )
    return QuboModel(request=request, build=build)


def _make_spd_sigma(n: int, rng: np.random.Generator) -> list[list[float]]:
    """Generate a random symmetric positive-definite covariance matrix."""
    A = rng.uniform(-0.1, 0.1, size=(n, n))
    sigma = A @ A.T + np.eye(n) * 0.01
    return sigma.tolist()


@st.composite
def solver_requests_any_cardinality(draw: st.DrawFn) -> SolverRequest:
    """Hypothesis strategy: random SolverRequest with n_assets in [2, 6].

    Cardinality can be any valid value including n_assets (K==N case),
    which exercises the full range of BQM construction paths.
    """
    n_assets = draw(st.integers(min_value=2, max_value=6))
    seed = draw(st.integers(min_value=0, max_value=2**31 - 1))
    rng = np.random.default_rng(seed)

    mu = rng.uniform(0.01, 0.20, size=n_assets).tolist()
    sigma = _make_spd_sigma(n_assets, rng)

    tickers = [f"T{i}" for i in range(n_assets)]
    sector_pool = ["Tech", "Finance", "Energy", "Healthcare"]
    sectors = [sector_pool[i % len(sector_pool)] for i in range(n_assets)]

    cardinality = draw(st.integers(min_value=1, max_value=n_assets))

    return SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=tickers,
        sectors=sectors,
        cardinality=cardinality,
        max_sector_exposure=0.5,
        risk_tolerance=draw(st.floats(min_value=0.0, max_value=2.0)),
        binary_bits=2,
    )


# ---------------------------------------------------------------------------
# Observation 1 — Diagonal-only model returns a diagonal matrix
# ---------------------------------------------------------------------------

def test_observe_linear_only_model_diagonal_entries():
    """
    **Validates: Requirements 3.1**

    OBSERVATION: to_qubo_matrix() on a linear-only model (no quadratic terms)
    returns a diagonal matrix where Q[i,i] == bqm.linear[var] for each variable.

    This confirms the baseline behavior that must be preserved after the fix.
    """
    biases = [1.5, 2.7, 0.3]
    model = _make_linear_only_model(n_vars=3, biases=biases)
    Q, var_order, offset = to_qubo_matrix(model)

    print(f"\n[OBSERVATION] Linear-only model diagonal entries:")
    print(f"  Q =\n{Q}")
    for i, (var, expected_bias) in enumerate(zip(var_order, biases)):
        actual = Q[i, i]
        print(f"  Q[{i},{i}] = {actual:.6f}  (bqm.linear[{var}] = {expected_bias:.6f})")
        assert abs(actual - expected_bias) < 1e-12, (
            f"Diagonal entry mismatch: Q[{i},{i}]={actual:.6f} != "
            f"bqm.linear[{var}]={expected_bias:.6f}"
        )

    # Off-diagonal entries must be zero for a linear-only model
    n = len(var_order)
    for i in range(n):
        for j in range(n):
            if i != j:
                assert Q[i, j] == 0.0, (
                    f"Off-diagonal entry Q[{i},{j}]={Q[i,j]:.6f} should be 0.0 "
                    f"for a linear-only model"
                )


def test_observe_bqm_add_quadratic_storage():
    """
    **Validates: Requirements 3.2**

    OBSERVATION: PortfolioBQM.add_quadratic(left, right, bias) stores the pair
    under _ordered_pair(left, right) with the exact bias value.

    This confirms the BQM storage behavior that must remain unchanged after the fix.
    """
    bqm = PortfolioBQM()
    bqm.add_variable("x_0_0")
    bqm.add_variable("x_1_0")

    # Test canonical ordering: (x_0_0, x_1_0) — already ordered
    bqm.add_quadratic("x_0_0", "x_1_0", 0.42)
    key = _ordered_pair("x_0_0", "x_1_0")
    assert key in bqm.quadratic, f"Key {key} not found in bqm.quadratic"
    assert abs(bqm.quadratic[key] - 0.42) < 1e-12, (
        f"bqm.quadratic[{key}] = {bqm.quadratic[key]:.6f} != 0.42"
    )
    print(f"\n[OBSERVATION] add_quadratic('x_0_0', 'x_1_0', 0.42):")
    print(f"  key = {key}")
    print(f"  bqm.quadratic[{key}] = {bqm.quadratic[key]:.6f}")

    # Test reverse ordering: (x_1_0, x_0_0) — should be stored under canonical key
    bqm2 = PortfolioBQM()
    bqm2.add_variable("x_0_0")
    bqm2.add_variable("x_1_0")
    bqm2.add_quadratic("x_1_0", "x_0_0", 0.99)
    key2 = _ordered_pair("x_1_0", "x_0_0")
    assert key2 in bqm2.quadratic, f"Key {key2} not found in bqm2.quadratic"
    assert abs(bqm2.quadratic[key2] - 0.99) < 1e-12, (
        f"bqm2.quadratic[{key2}] = {bqm2.quadratic[key2]:.6f} != 0.99"
    )
    print(f"\n[OBSERVATION] add_quadratic('x_1_0', 'x_0_0', 0.99):")
    print(f"  key = {key2}")
    print(f"  bqm2.quadratic[{key2}] = {bqm2.quadratic[key2]:.6f}")


def test_observe_build_portfolio_bqm_determinism():
    """
    **Validates: Requirements 3.3**

    OBSERVATION: build_portfolio_bqm() produces identical bqm.linear and
    bqm.quadratic key sets and values across repeated calls.

    This confirms the BQM construction is deterministic and must remain so.
    """
    request = SolverRequest(
        mu=[0.10, 0.12, 0.08],
        sigma=[
            [0.04, 0.01, 0.02],
            [0.01, 0.09, 0.03],
            [0.02, 0.03, 0.06],
        ],
        tickers=["A", "B", "C"],
        sectors=["Tech", "Tech", "Tech"],
        cardinality=2,
        max_sector_exposure=0.5,
        risk_tolerance=0.5,
        binary_bits=2,
    )

    build1 = build_portfolio_bqm(request)
    build2 = build_portfolio_bqm(request)

    # Key sets must be identical
    assert set(build1.bqm.linear.keys()) == set(build2.bqm.linear.keys()), (
        "bqm.linear key sets differ across repeated calls"
    )
    assert set(build1.bqm.quadratic.keys()) == set(build2.bqm.quadratic.keys()), (
        "bqm.quadratic key sets differ across repeated calls"
    )

    # Values must be identical within 1e-12
    for var in build1.bqm.linear:
        v1 = build1.bqm.linear[var]
        v2 = build2.bqm.linear[var]
        assert abs(v1 - v2) < 1e-12, (
            f"bqm.linear[{var}] differs: {v1:.15f} vs {v2:.15f}"
        )

    for pair in build1.bqm.quadratic:
        v1 = build1.bqm.quadratic[pair]
        v2 = build2.bqm.quadratic[pair]
        assert abs(v1 - v2) < 1e-12, (
            f"bqm.quadratic[{pair}] differs: {v1:.15f} vs {v2:.15f}"
        )

    print(f"\n[OBSERVATION] build_portfolio_bqm() is deterministic:")
    print(f"  linear terms: {len(build1.bqm.linear)}")
    print(f"  quadratic terms: {len(build1.bqm.quadratic)}")


def test_observe_serialization_format():
    """
    **Validates: Requirements 3.4**

    OBSERVATION: Q.flatten().tolist() produces a flat list of exactly
    n_vars * n_vars floats.

    This confirms the serialization format that must remain unchanged.
    """
    model = _make_linear_only_model(n_vars=4)
    Q, var_order, offset = to_qubo_matrix(model)

    flat_list = Q.flatten().tolist()
    n_vars = len(var_order)

    print(f"\n[OBSERVATION] Serialization format:")
    print(f"  n_vars = {n_vars}")
    print(f"  len(flat_list) = {len(flat_list)}")
    print(f"  isinstance(flat_list, list) = {isinstance(flat_list, list)}")
    print(f"  all floats = {all(isinstance(x, float) for x in flat_list)}")

    assert len(flat_list) == n_vars ** 2, (
        f"flat_list length {len(flat_list)} != n_vars**2 = {n_vars**2}"
    )
    assert isinstance(flat_list, list), "Q.flatten().tolist() must return a list"
    assert all(isinstance(x, float) for x in flat_list), (
        "All elements of flat_list must be float"
    )


# ---------------------------------------------------------------------------
# Property 1 — Diagonal preservation
# ---------------------------------------------------------------------------

def test_diagonal_preservation_linear_only_model():
    """
    **Validates: Requirements 3.1**

    For a linear-only model, Q[i,i] must equal bqm.linear[var] for each variable.
    Tests with various bias values including zero, negative, and large values.
    """
    test_cases = [
        [0.0, 0.0, 0.0],           # all-zero biases
        [1.0, -1.0, 0.5],          # mixed signs
        [100.0, 200.0, 300.0],     # large values
        [1e-10, 1e-10, 1e-10],     # near-zero values
    ]

    for biases in test_cases:
        model = _make_linear_only_model(n_vars=3, biases=biases)
        Q, var_order, offset = to_qubo_matrix(model)

        for i, var in enumerate(var_order):
            expected = model.build.bqm.linear[var]
            actual = Q[i, i]
            assert abs(actual - expected) < 1e-12, (
                f"Diagonal mismatch for biases={biases}: "
                f"Q[{i},{i}]={actual:.15f} != bqm.linear[{var}]={expected:.15f}"
            )


@given(request=solver_requests_any_cardinality())
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_diagonal_preservation(request: SolverRequest) -> None:
    """
    **Validates: Requirements 3.1**

    Property: For any QuboModel, Q[i,i] == sum(bqm.linear[var] for var with index[var]==i)
    for all diagonal indices i, within 1e-12.

    This property holds on UNFIXED code because the bug only affects off-diagonal
    quadratic terms — diagonal (linear) terms are written correctly in both
    unfixed and fixed code.

    EXPECTED OUTCOME: PASSES on unfixed code.
    """
    build = build_portfolio_bqm(request)
    model = QuboModel(request=request, build=build)
    Q, var_order, offset = to_qubo_matrix(model)

    index = {name: pos for pos, name in enumerate(var_order)}

    # For each diagonal index i, sum all linear biases for variables at that index
    for i, var in enumerate(var_order):
        # Each variable maps to exactly one diagonal index
        expected_diagonal = model.build.bqm.linear.get(var, 0.0)
        actual_diagonal = Q[i, i]

        assert abs(actual_diagonal - expected_diagonal) < 1e-12, (
            f"Diagonal preservation violated for var={var} at index={i}: "
            f"Q[{i},{i}]={actual_diagonal:.15f} != "
            f"bqm.linear[{var}]={expected_diagonal:.15f}. "
            f"n_assets={len(request.tickers)}, cardinality={request.cardinality}"
        )


# ---------------------------------------------------------------------------
# Property 2 — BQM storage invariance
# ---------------------------------------------------------------------------

@given(
    bias=st.floats(min_value=-1000.0, max_value=1000.0, allow_nan=False, allow_infinity=False),
    left_idx=st.integers(min_value=0, max_value=9),
    right_idx=st.integers(min_value=0, max_value=9),
)
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_bqm_storage_invariance(
    bias: float, left_idx: int, right_idx: int
) -> None:
    """
    **Validates: Requirements 3.2**

    Property: For any call to PortfolioBQM.add_quadratic(left, right, bias),
    bqm.quadratic[_ordered_pair(left, right)] == bias immediately after the call.

    This property holds on UNFIXED code because the bug is in to_qubo_matrix(),
    not in bqm_builder.py. BQM storage is correct and must remain unchanged.

    EXPECTED OUTCOME: PASSES on unfixed code.
    """
    # Generate distinct variable names (skip same-variable case — that becomes linear)
    if left_idx == right_idx:
        right_idx = (right_idx + 1) % 10

    left = f"x_{left_idx}_0"
    right = f"x_{right_idx}_0"

    bqm = PortfolioBQM()
    bqm.add_variable(left)
    bqm.add_variable(right)
    bqm.add_quadratic(left, right, bias)

    canonical_key = _ordered_pair(left, right)

    assert canonical_key in bqm.quadratic, (
        f"Key {canonical_key} not found in bqm.quadratic after "
        f"add_quadratic({left!r}, {right!r}, {bias})"
    )

    stored_bias = bqm.quadratic[canonical_key]
    assert abs(stored_bias - bias) < 1e-12, (
        f"BQM storage invariance violated: "
        f"bqm.quadratic[{canonical_key}]={stored_bias:.15f} != bias={bias:.15f}. "
        f"add_quadratic({left!r}, {right!r}, {bias})"
    )


@given(request=solver_requests_any_cardinality())
@settings(
    max_examples=20,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_bqm_storage_invariance_full_build(request: SolverRequest) -> None:
    """
    **Validates: Requirements 3.2, 3.3**

    Property: For any SolverRequest, build_portfolio_bqm() produces a BQM where
    every quadratic entry is stored under its canonical _ordered_pair key.

    Verifies that all keys in bqm.quadratic satisfy key == _ordered_pair(*key).

    EXPECTED OUTCOME: PASSES on unfixed code.
    """
    build = build_portfolio_bqm(request)

    for pair, bias in build.bqm.quadratic.items():
        left, right = pair
        canonical = _ordered_pair(left, right)
        assert pair == canonical, (
            f"Non-canonical key in bqm.quadratic: {pair} != {canonical}. "
            f"All keys must satisfy key == _ordered_pair(*key)."
        )
        # Bias must be a finite float
        assert np.isfinite(bias), (
            f"Non-finite bias {bias} for pair {pair}"
        )


# ---------------------------------------------------------------------------
# Property 3 — Serialization format invariance
# ---------------------------------------------------------------------------

@given(request=solver_requests_any_cardinality())
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_serialization_format_invariance(request: SolverRequest) -> None:
    """
    **Validates: Requirements 3.4**

    Property: For any QuboModel, Q.flatten().tolist() produces:
      - a flat Python list
      - of exactly n_vars * n_vars elements
      - where all elements are float

    This property holds on UNFIXED code because the bug does not affect
    the shape or type of the serialized output.

    EXPECTED OUTCOME: PASSES on unfixed code.
    """
    build = build_portfolio_bqm(request)
    model = QuboModel(request=request, build=build)
    Q, var_order, offset = to_qubo_matrix(model)

    flat_list = Q.flatten().tolist()
    n_vars = len(var_order)

    assert isinstance(flat_list, list), (
        f"Q.flatten().tolist() must return a list, got {type(flat_list)}"
    )
    assert len(flat_list) == n_vars ** 2, (
        f"Serialization length mismatch: len(flat_list)={len(flat_list)} "
        f"!= n_vars**2={n_vars**2} for n_vars={n_vars}"
    )
    assert all(isinstance(x, float) for x in flat_list), (
        f"Not all elements are float: "
        f"{[type(x) for x in flat_list if not isinstance(x, float)][:5]}"
    )


# ---------------------------------------------------------------------------
# Property 4 — Diagonal-only model symmetry
# ---------------------------------------------------------------------------

def test_diagonal_only_model_is_symmetric_on_unfixed_code():
    """
    **Validates: Requirements 3.1, 3.4**

    For a model with no quadratic terms, np.allclose(Q, Q.T, atol=1e-9) PASSES
    on UNFIXED code. Diagonal matrices are trivially symmetric.

    This confirms the bug is specific to off-diagonal terms — diagonal-only
    models are unaffected by the single-side write bug.

    EXPECTED OUTCOME: PASSES on unfixed code.
    """
    for n_vars in [1, 2, 3, 5, 8]:
        biases = [float(i + 1) * 0.5 for i in range(n_vars)]
        model = _make_linear_only_model(n_vars=n_vars, biases=biases)
        Q, var_order, offset = to_qubo_matrix(model)

        max_asymmetry = float(np.max(np.abs(Q - Q.T)))

        print(f"\n[DIAGONAL_ONLY] n_vars={n_vars}:")
        print(f"  Q shape = {Q.shape}")
        print(f"  max_asymmetry = {max_asymmetry:.2e}")
        print(f"  symmetric = {np.allclose(Q, Q.T, atol=1e-9)}")

        assert np.allclose(Q, Q.T, atol=1e-9), (
            f"Diagonal-only model with n_vars={n_vars} is not symmetric! "
            f"max_asymmetry={max_asymmetry:.6e}. "
            f"This should never happen — diagonal matrices are trivially symmetric."
        )
        assert max_asymmetry < 1e-12, (
            f"max_asymmetry={max_asymmetry:.6e} for diagonal-only model — "
            f"expected exactly 0.0 (no off-diagonal terms)"
        )


@given(
    n_vars=st.integers(min_value=1, max_value=10),
    biases=st.lists(
        st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        min_size=1,
        max_size=10,
    ),
)
@settings(
    max_examples=50,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_diagonal_only_model_symmetry(
    n_vars: int, biases: list[float]
) -> None:
    """
    **Validates: Requirements 3.1**

    Property: For any linear-only QuboModel (no quadratic terms),
    np.allclose(Q, Q.T, atol=1e-9) is True on UNFIXED code.

    Diagonal matrices are trivially symmetric. This property confirms the bug
    is specific to off-diagonal quadratic terms and does not affect linear-only models.

    EXPECTED OUTCOME: PASSES on unfixed code.
    """
    # Pad or truncate biases to match n_vars
    padded_biases = (biases * n_vars)[:n_vars]

    model = _make_linear_only_model(n_vars=n_vars, biases=padded_biases)
    Q, var_order, offset = to_qubo_matrix(model)

    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"Diagonal-only model is not symmetric! "
        f"n_vars={n_vars}, biases={padded_biases}, "
        f"max_asymmetry={float(np.max(np.abs(Q - Q.T))):.6e}. "
        f"Diagonal matrices must always be symmetric."
    )
