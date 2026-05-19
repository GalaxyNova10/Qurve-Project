"""
Bug Condition Exploration Tests — QUBO Symmetry Corruption
==========================================================

**Validates: Requirements 1.1, 1.2, 1.3**

CRITICAL: These tests are EXPECTED TO FAIL on unfixed code.
Failure confirms the bug exists. DO NOT fix the code when these fail.

The bug: to_qubo_matrix() writes off-diagonal quadratic terms to only one
triangle of the matrix (either Q[i,j] or Q[j,i]), leaving the mirror
position at 0.0. This produces max(|Q - Q^T|) == max(|quadratic coefficients|).

Goal: Surface counterexamples demonstrating the asymmetry on unfixed code.
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
    build_portfolio_bqm,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_2var_model() -> QuboModel:
    """Build a QuboModel with exactly two variables and one off-diagonal term.

    Variables: x_0_0, x_1_0
    Quadratic: (x_0_0, x_1_0) -> bias=1.0
    No linear terms, no other quadratic terms.

    On unfixed code to_qubo_matrix() writes only Q[0,1]=1.0 (or Q[1,0]=1.0),
    leaving the mirror at 0.0 → max_asymmetry = 1.0.
    """
    bqm = PortfolioBQM()
    bqm.add_variable("x_0_0")
    bqm.add_variable("x_1_0")
    bqm.add_quadratic("x_0_0", "x_1_0", 1.0)

    build = BQMBuildResult(
        bqm=bqm,
        variable_order=["x_0_0", "x_1_0"],
        weight_variables=[["x_0_0"], ["x_1_0"]],
        indicator_variables=[],
        slack_variables={},
        denominator=1,
        objective_span=1.0,
    )
    # Minimal SolverRequest — values don't matter for this test
    request = SolverRequest(
        mu=[0.1, 0.1],
        sigma=[[1.0, 0.0], [0.0, 1.0]],
        tickers=["A", "B"],
        sectors=["Tech", "Tech"],
        cardinality=1,
        binary_bits=2,
    )
    return QuboModel(request=request, build=build)


def _make_4asset_portfolio_request() -> SolverRequest:
    """4-asset portfolio — the primary crash scenario.

    Uses a realistic covariance matrix with off-diagonal entries so that
    build_portfolio_bqm() generates cross-terms. The cardinality penalty
    cross-terms (y_i, y_j) with bias 2*P_card dominate the asymmetry,
    producing max_asymmetry ≈ 558 on unfixed code.
    """
    np.random.seed(42)
    n = 4
    A = np.array([
        [0.04, 0.01, 0.02, 0.005],
        [0.01, 0.09, 0.03, 0.01],
        [0.02, 0.03, 0.06, 0.015],
        [0.005, 0.01, 0.015, 0.05],
    ])
    return SolverRequest(
        mu=[0.10, 0.12, 0.08, 0.15],
        sigma=A.tolist(),
        tickers=["AAPL", "GOOG", "MSFT", "AMZN"],
        sectors=["Tech", "Tech", "Tech", "Tech"],
        cardinality=2,          # K < N → cardinality penalty cross-terms exist
        max_sector_exposure=0.5,
        risk_tolerance=0.5,
        binary_bits=2,
    )


def _make_cardinality_only_model() -> QuboModel:
    """Model with only cardinality penalty cross-terms (y_i, y_j).

    Uses 3 assets with K=1 so that the cardinality Hamiltonian
    P_card * (y_0 + y_1 + y_2 - 1)^2 generates cross-terms
    (y_0,y_1), (y_0,y_2), (y_1,y_2) each with bias 2*P_card.

    On unfixed code each cross-term is written to only one triangle,
    so max_asymmetry = 2 * P_card.
    """
    # Build via the real builder so we get genuine cardinality cross-terms
    request = SolverRequest(
        mu=[0.1, 0.1, 0.1],
        sigma=[[1.0, 0.0, 0.0],
               [0.0, 1.0, 0.0],
               [0.0, 0.0, 1.0]],
        tickers=["A", "B", "C"],
        sectors=["X", "X", "X"],
        cardinality=1,          # K=1 < N=3 → cardinality cross-terms
        max_sector_exposure=0.5,
        risk_tolerance=0.0,     # zero risk tolerance → no Markowitz cross-terms
        binary_bits=2,
    )
    build = build_portfolio_bqm(request)
    return QuboModel(request=request, build=build)


# ---------------------------------------------------------------------------
# Test 1 — Minimal 2-variable model
# ---------------------------------------------------------------------------

def test_minimal_2var_model_symmetry_EXPECTED_TO_FAIL_ON_UNFIXED_CODE():
    """
    **Validates: Requirements 1.1, 1.2**

    Minimal 2-variable model with one cross-term (x_0_0, x_1_0) bias=1.0.

    On unfixed code:
      - to_qubo_matrix() writes Q[0,1]=1.0 but NOT Q[1,0]=1.0 (or vice versa)
      - max_asymmetry = 1.0
      - np.allclose(Q, Q.T, atol=1e-9) returns False → assertion FAILS

    EXPECTED OUTCOME: This test FAILS on unfixed code (confirms bug exists).
    """
    model = _make_minimal_2var_model()
    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))

    # Document what we observe on unfixed code
    print(f"\n[BUG_CONDITION] Minimal 2-var model:")
    print(f"  Q =\n{Q}")
    print(f"  Q[0,1] = {Q[0,1]:.6f},  Q[1,0] = {Q[1,0]:.6f}")
    print(f"  max_asymmetry = {max_asymmetry:.6f}")
    print(f"  symmetric = {np.allclose(Q, Q.T, atol=1e-9)}")

    # This assertion FAILS on unfixed code (max_asymmetry = 1.0)
    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"QUBO matrix is not symmetric! "
        f"Q[0,1]={Q[0,1]:.6f}, Q[1,0]={Q[1,0]:.6f}, "
        f"max_asymmetry={max_asymmetry:.6e}. "
        f"Counterexample: to_qubo_matrix() on 2-var model returns "
        f"Q[0,1]={Q[0,1]:.6f}, Q[1,0]={Q[1,0]:.6f}; max_asymmetry={max_asymmetry:.6f}"
    )


# ---------------------------------------------------------------------------
# Test 2 — 4-asset portfolio (primary crash scenario)
# ---------------------------------------------------------------------------

def test_4asset_portfolio_symmetry_EXPECTED_TO_FAIL_ON_UNFIXED_CODE():
    """
    **Validates: Requirements 1.1, 1.2, 1.3**

    4-asset portfolio — the primary crash scenario that triggered the bug report.

    On unfixed code:
      - Cardinality penalty cross-terms (y_i, y_j) with bias 2*P_card dominate
      - max_asymmetry ≈ 558 (observed: 5.589827e+02)
      - np.allclose(Q, Q.T, atol=1e-9) returns False → assertion FAILS

    EXPECTED OUTCOME: This test FAILS on unfixed code (confirms bug exists).
    """
    request = _make_4asset_portfolio_request()
    build = build_portfolio_bqm(request)
    model = QuboModel(request=request, build=build)

    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))
    n = Q.shape[0]

    # Find the worst asymmetric pair for documentation
    diff = np.abs(Q - Q.T)
    worst_idx = np.unravel_index(np.argmax(diff), diff.shape)
    i_w, j_w = worst_idx

    print(f"\n[BUG_CONDITION] 4-asset portfolio:")
    print(f"  Q shape = {Q.shape}")
    print(f"  max_asymmetry = {max_asymmetry:.6e}")
    print(f"  worst pair: Q[{i_w},{j_w}]={Q[i_w,j_w]:.6f}, Q[{j_w},{i_w}]={Q[j_w,i_w]:.6f}")
    print(f"  symmetric = {np.allclose(Q, Q.T, atol=1e-9)}")

    # This assertion FAILS on unfixed code (max_asymmetry ≈ 558)
    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"QUBO matrix is not symmetric! "
        f"max_asymmetry={max_asymmetry:.6e}. "
        f"Worst pair: Q[{i_w},{j_w}]={Q[i_w,j_w]:.6f}, Q[{j_w},{i_w}]={Q[j_w,i_w]:.6f}. "
        f"This matches the observed crash: QUBO_SYMMETRY_CORRUPTION max_asymmetry=5.589827e+02"
    )


# ---------------------------------------------------------------------------
# Test 3 — Cardinality-penalty-only model
# ---------------------------------------------------------------------------

def test_cardinality_only_model_symmetry_EXPECTED_TO_FAIL_ON_UNFIXED_CODE():
    """
    **Validates: Requirements 1.1, 1.2**

    Model with only cardinality penalty cross-terms (y_i, y_j) with bias 2*P_card.

    On unfixed code:
      - Each (y_i, y_j) cross-term is written to only one triangle
      - max_asymmetry = 2 * P_card
      - np.allclose(Q, Q.T, atol=1e-9) returns False → assertion FAILS

    EXPECTED OUTCOME: This test FAILS on unfixed code (confirms bug exists).
    """
    model = _make_cardinality_only_model()
    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))
    diff = np.abs(Q - Q.T)
    worst_idx = np.unravel_index(np.argmax(diff), diff.shape)
    i_w, j_w = worst_idx

    print(f"\n[BUG_CONDITION] Cardinality-only model:")
    print(f"  Q shape = {Q.shape}")
    print(f"  max_asymmetry = {max_asymmetry:.6e}")
    print(f"  worst pair: Q[{i_w},{j_w}]={Q[i_w,j_w]:.6f}, Q[{j_w},{i_w}]={Q[j_w,i_w]:.6f}")
    print(f"  symmetric = {np.allclose(Q, Q.T, atol=1e-9)}")

    # This assertion FAILS on unfixed code (max_asymmetry = 2 * P_card)
    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"QUBO matrix is not symmetric! "
        f"max_asymmetry={max_asymmetry:.6e}. "
        f"Worst pair: Q[{i_w},{j_w}]={Q[i_w,j_w]:.6f}, Q[{j_w},{i_w}]={Q[j_w,i_w]:.6f}. "
        f"Asymmetry = 2 * P_card confirms single-side write bug in cardinality cross-terms."
    )


# ---------------------------------------------------------------------------
# Test 4 — Property-based variant (Hypothesis)
# ---------------------------------------------------------------------------

def _make_spd_sigma(n: int, rng: np.random.Generator) -> list[list[float]]:
    """Generate a random symmetric positive-definite covariance matrix."""
    A = rng.uniform(-0.1, 0.1, size=(n, n))
    sigma = A @ A.T + np.eye(n) * 0.01  # ensure positive definite
    return sigma.tolist()


@st.composite
def solver_requests(draw: st.DrawFn) -> SolverRequest:
    """Hypothesis strategy: random SolverRequest with n_assets in [2, 8]."""
    n_assets = draw(st.integers(min_value=2, max_value=8))
    seed = draw(st.integers(min_value=0, max_value=2**31 - 1))
    rng = np.random.default_rng(seed)

    mu = rng.uniform(0.01, 0.20, size=n_assets).tolist()
    sigma = _make_spd_sigma(n_assets, rng)

    tickers = [f"T{i}" for i in range(n_assets)]
    sector_pool = ["Tech", "Finance", "Energy", "Healthcare"]
    sectors = [sector_pool[i % len(sector_pool)] for i in range(n_assets)]

    # cardinality in [1, n_assets-1] to ensure cardinality cross-terms exist
    # (K < N guarantees the cardinality Hamiltonian generates off-diagonal terms)
    cardinality = draw(st.integers(min_value=1, max_value=max(1, n_assets - 1)))

    return SolverRequest(
        mu=mu,
        sigma=sigma,
        tickers=tickers,
        sectors=sectors,
        cardinality=cardinality,
        max_sector_exposure=0.5,
        risk_tolerance=draw(st.floats(min_value=0.0, max_value=2.0)),
        binary_bits=2,  # keep small for speed
    )


@given(request=solver_requests())
@settings(
    max_examples=30,
    suppress_health_check=[HealthCheck.too_slow],
    deadline=None,
)
def test_property_qubo_symmetry_EXPECTED_TO_FAIL_ON_UNFIXED_CODE(
    request: SolverRequest,
) -> None:
    """
    **Validates: Requirements 1.1, 1.2, 1.3**

    Property-based variant: for any SolverRequest with n_assets in [2, 8]
    and cardinality < n_assets (guaranteeing off-diagonal quadratic terms),
    to_qubo_matrix() must return a symmetric matrix.

    On unfixed code:
      - Every generated model has cardinality cross-terms
      - to_qubo_matrix() writes each cross-term to only one triangle
      - np.allclose(Q, Q.T, atol=1e-9) returns False → assertion FAILS

    EXPECTED OUTCOME: Hypothesis finds a counterexample on the first example
    (confirms bug exists for all models with off-diagonal terms).
    """
    build = build_portfolio_bqm(request)
    model = QuboModel(request=request, build=build)

    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))

    # This assertion FAILS on unfixed code
    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"QUBO matrix is not symmetric for n_assets={len(request.tickers)}, "
        f"cardinality={request.cardinality}. "
        f"max_asymmetry={max_asymmetry:.6e}. "
        f"Counterexample confirms single-side write bug in to_qubo_matrix()."
    )
