"""
Unit Tests — Task 3.2: Replace defective if/else branch with add_symmetric_quadratic()
========================================================================================

**Validates: Requirements 2.1, 2.2, 3.1, 3.2, 3.3**

Tests:
  1. to_qubo_matrix() on 2-variable model with cross-term bias=1.0 returns
     np.allclose(Q, Q.T, atol=1e-9) == True
  2. to_qubo_matrix() on 4-asset portfolio returns max(|Q - Q^T|) < 1e-9
  3. For 2-variable model with cross-term bias=1.0 and s=[1,1],
     float(s @ Q_fixed @ s) == 1.0 (not 2.0 — confirms no double-counting)
"""

from __future__ import annotations

import numpy as np
import pytest

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.qubo_model import QuboModel, to_qubo_matrix
from qubo_backend.optimization.bqm_builder import (
    BQMBuildResult,
    PortfolioBQM,
    build_portfolio_bqm,
)


# ---------------------------------------------------------------------------
# Helpers (shared with bug condition tests)
# ---------------------------------------------------------------------------

def _make_minimal_2var_model() -> QuboModel:
    """Build a QuboModel with exactly two variables and one off-diagonal term.

    Variables: x_0_0, x_1_0
    Quadratic: (x_0_0, x_1_0) -> bias=1.0
    No linear terms, no other quadratic terms.

    After the fix, to_qubo_matrix() must write Q[0,1]=0.5 AND Q[1,0]=0.5
    (Convention B half-value dual-write), producing a symmetric matrix.
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
    request = SolverRequest(
        mu=[0.1, 0.1],
        sigma=[[1.0, 0.0], [0.0, 1.0]],
        tickers=["A", "B"],
        sectors=["Tech", "Tech"],
        cardinality=1,
        binary_bits=2,
    )
    return QuboModel(request=request, build=build)


def _make_4asset_portfolio_model() -> QuboModel:
    """4-asset portfolio — the primary crash scenario.

    Uses a realistic covariance matrix with off-diagonal entries so that
    build_portfolio_bqm() generates cross-terms. The cardinality penalty
    cross-terms (y_i, y_j) with bias 2*P_card dominate the asymmetry
    on unfixed code (max_asymmetry ≈ 558).

    After the fix, all cross-terms must be written symmetrically.
    """
    A = np.array([
        [0.04, 0.01, 0.02, 0.005],
        [0.01, 0.09, 0.03, 0.01],
        [0.02, 0.03, 0.06, 0.015],
        [0.005, 0.01, 0.015, 0.05],
    ])
    request = SolverRequest(
        mu=[0.10, 0.12, 0.08, 0.15],
        sigma=A.tolist(),
        tickers=["AAPL", "GOOG", "MSFT", "AMZN"],
        sectors=["Tech", "Tech", "Tech", "Tech"],
        cardinality=2,
        max_sector_exposure=0.5,
        risk_tolerance=0.5,
        binary_bits=2,
    )
    build = build_portfolio_bqm(request)
    return QuboModel(request=request, build=build)


# ---------------------------------------------------------------------------
# Test 1 — 2-variable model: to_qubo_matrix() returns symmetric matrix
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_2var_model_is_symmetric():
    """
    **Validates: Requirements 2.1, 2.2**

    to_qubo_matrix() on 2-variable model with cross-term bias=1.0 returns
    np.allclose(Q, Q.T, atol=1e-9) == True.

    After the fix, the defective if/else branch is replaced with
    add_symmetric_quadratic(), which writes Q[0,1]=0.5 AND Q[1,0]=0.5.
    The resulting matrix is symmetric.
    """
    model = _make_minimal_2var_model()
    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))

    print(f"\n[TASK_3_2] 2-var model after fix:")
    print(f"  Q =\n{Q}")
    print(f"  Q[0,1] = {Q[0,1]:.6f},  Q[1,0] = {Q[1,0]:.6f}")
    print(f"  max_asymmetry = {max_asymmetry:.6e}")
    print(f"  symmetric = {np.allclose(Q, Q.T, atol=1e-9)}")

    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"QUBO matrix is not symmetric after fix! "
        f"Q[0,1]={Q[0,1]:.6f}, Q[1,0]={Q[1,0]:.6f}, "
        f"max_asymmetry={max_asymmetry:.6e}. "
        f"The defective if/else branch was not replaced with add_symmetric_quadratic()."
    )


def test_to_qubo_matrix_2var_model_half_value_positions():
    """
    **Validates: Requirements 2.1, 2.2**

    After the fix, Q[0,1] == Q[1,0] == 0.5 for a 2-variable model with
    cross-term bias=1.0 (Convention B: each position holds value/2).
    """
    model = _make_minimal_2var_model()
    Q, var_order, offset = to_qubo_matrix(model)

    assert abs(Q[0, 1] - 0.5) < 1e-12, (
        f"Q[0,1] = {Q[0,1]:.15f}, expected 0.5 (half of bias=1.0). "
        f"Convention B requires value/2 at each off-diagonal position."
    )
    assert abs(Q[1, 0] - 0.5) < 1e-12, (
        f"Q[1,0] = {Q[1,0]:.15f}, expected 0.5 (half of bias=1.0). "
        f"The mirror position must also be written."
    )


# ---------------------------------------------------------------------------
# Test 2 — 4-asset portfolio: max(|Q - Q^T|) < 1e-9
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_4asset_portfolio_max_asymmetry():
    """
    **Validates: Requirements 2.1, 2.2**

    to_qubo_matrix() on 4-asset portfolio returns max(|Q - Q^T|) < 1e-9.

    Before the fix, max_asymmetry ≈ 558 (cardinality penalty cross-terms).
    After the fix, all cross-terms are written symmetrically via
    add_symmetric_quadratic(), so max_asymmetry < 1e-9.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))
    diff = np.abs(Q - Q.T)
    worst_idx = np.unravel_index(np.argmax(diff), diff.shape)
    i_w, j_w = worst_idx

    print(f"\n[TASK_3_2] 4-asset portfolio after fix:")
    print(f"  Q shape = {Q.shape}")
    print(f"  max_asymmetry = {max_asymmetry:.6e}")
    print(f"  worst pair: Q[{i_w},{j_w}]={Q[i_w,j_w]:.6f}, Q[{j_w},{i_w}]={Q[j_w,i_w]:.6f}")
    print(f"  symmetric = {np.allclose(Q, Q.T, atol=1e-9)}")

    assert max_asymmetry < 1e-9, (
        f"max(|Q - Q^T|) = {max_asymmetry:.6e}, expected < 1e-9. "
        f"Worst pair: Q[{i_w},{j_w}]={Q[i_w,j_w]:.6f}, Q[{j_w},{i_w}]={Q[j_w,i_w]:.6f}. "
        f"The fix did not eliminate asymmetry in the 4-asset portfolio."
    )


def test_to_qubo_matrix_4asset_portfolio_is_symmetric():
    """
    **Validates: Requirements 2.1, 2.2**

    np.allclose(Q, Q.T, atol=1e-9) == True for the 4-asset portfolio.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"QUBO matrix is not symmetric for 4-asset portfolio! "
        f"max_asymmetry={float(np.max(np.abs(Q - Q.T))):.6e}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Energy: s^T Q_fixed s == 1.0 for s=[1,1], bias=1.0 (no double-counting)
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_2var_energy_no_double_counting():
    """
    **Validates: Requirements 2.1, 2.2, 3.1**

    For 2-variable model with cross-term bias=1.0 and s=[1,1],
    float(s @ Q_fixed @ s) == 1.0 (not 2.0).

    This confirms Convention B (half-value dual-write) is correct:
    - BQM stores coupling (x_0_0, x_1_0) with bias=1.0 (full coefficient)
    - add_symmetric_quadratic writes Q[0,1]=0.5 and Q[1,0]=0.5
    - s^T Q s = s[0]*Q[0,1]*s[1] + s[1]*Q[1,0]*s[0] = 0.5 + 0.5 = 1.0
    - NOT 2.0 (which would indicate full-value dual-write / double-counting)

    If the result were 2.0, every coupling would be doubled, corrupting
    all penalty scales and the Markowitz objective.
    """
    model = _make_minimal_2var_model()
    Q, var_order, offset = to_qubo_matrix(model)

    s = np.array([1.0, 1.0])
    energy = float(s @ Q @ s)

    print(f"\n[TASK_3_2] Energy convention check:")
    print(f"  Q =\n{Q}")
    print(f"  s = {s}")
    print(f"  s^T Q s = {energy:.6f} (expected 1.0, NOT 2.0)")

    assert abs(energy - 1.0) < 1e-12, (
        f"s^T Q_fixed s = {energy:.6f}, expected 1.0. "
        f"If result is 2.0, the fix is writing the full value to both positions "
        f"(double-counting). Convention B requires value/2 at each position so "
        f"that the matmul recovers the full coefficient exactly once."
    )

    # Explicitly confirm it is NOT 2.0 (double-counting)
    assert abs(energy - 2.0) > 0.5, (
        f"s^T Q_fixed s = {energy:.6f} is suspiciously close to 2.0. "
        f"This indicates double-counting — the full value was written to both "
        f"Q[i,j] and Q[j,i] instead of value/2 to each."
    )


# ---------------------------------------------------------------------------
# Test 4 — Diagonal entries preserved (Requirement 3.1)
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_diagonal_entries_preserved():
    """
    **Validates: Requirements 3.1**

    The fix must not alter diagonal entries. For a model with both linear
    and quadratic terms, Q[i,i] must equal the sum of linear biases for
    variable i, unchanged by the quadratic fix.
    """
    bqm = PortfolioBQM()
    bqm.add_variable("x_0_0")
    bqm.add_variable("x_1_0")
    bqm.add_linear("x_0_0", 3.0)
    bqm.add_linear("x_1_0", 5.0)
    bqm.add_quadratic("x_0_0", "x_1_0", 2.0)

    build = BQMBuildResult(
        bqm=bqm,
        variable_order=["x_0_0", "x_1_0"],
        weight_variables=[["x_0_0"], ["x_1_0"]],
        indicator_variables=[],
        slack_variables={},
        denominator=1,
        objective_span=1.0,
    )
    request = SolverRequest(
        mu=[0.1, 0.1],
        sigma=[[1.0, 0.0], [0.0, 1.0]],
        tickers=["A", "B"],
        sectors=["Tech", "Tech"],
        cardinality=1,
        binary_bits=2,
    )
    model = QuboModel(request=request, build=build)
    Q, var_order, offset = to_qubo_matrix(model)

    # Diagonal entries must equal the linear biases
    assert abs(Q[0, 0] - 3.0) < 1e-12, (
        f"Q[0,0] = {Q[0,0]:.15f}, expected 3.0 (linear bias for x_0_0). "
        f"The fix must not alter diagonal entries."
    )
    assert abs(Q[1, 1] - 5.0) < 1e-12, (
        f"Q[1,1] = {Q[1,1]:.15f}, expected 5.0 (linear bias for x_1_0). "
        f"The fix must not alter diagonal entries."
    )

    # Off-diagonal entries must be symmetric (half-value)
    assert abs(Q[0, 1] - 1.0) < 1e-12, (
        f"Q[0,1] = {Q[0,1]:.15f}, expected 1.0 (half of bias=2.0)"
    )
    assert abs(Q[1, 0] - 1.0) < 1e-12, (
        f"Q[1,0] = {Q[1,0]:.15f}, expected 1.0 (half of bias=2.0)"
    )

    # Matrix must be symmetric
    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"Matrix not symmetric after fix. max_asymmetry={float(np.max(np.abs(Q - Q.T))):.6e}"
    )


# ---------------------------------------------------------------------------
# Test 5 — Multiple cross-terms all symmetric
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_multiple_cross_terms_all_symmetric():
    """
    **Validates: Requirements 2.1, 2.2**

    A model with multiple cross-terms must produce a fully symmetric matrix.
    Every off-diagonal pair (i,j) must satisfy Q[i,j] == Q[j,i].
    """
    bqm = PortfolioBQM()
    for name in ["a", "b", "c"]:
        bqm.add_variable(name)
    bqm.add_quadratic("a", "b", 1.0)
    bqm.add_quadratic("a", "c", 2.0)
    bqm.add_quadratic("b", "c", 3.0)

    build = BQMBuildResult(
        bqm=bqm,
        variable_order=["a", "b", "c"],
        weight_variables=[["a"], ["b"], ["c"]],
        indicator_variables=[],
        slack_variables={},
        denominator=1,
        objective_span=1.0,
    )
    request = SolverRequest(
        mu=[0.1, 0.1, 0.1],
        sigma=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]],
        tickers=["A", "B", "C"],
        sectors=["Tech", "Tech", "Tech"],
        cardinality=1,
        binary_bits=2,
    )
    model = QuboModel(request=request, build=build)
    Q, var_order, offset = to_qubo_matrix(model)

    max_asymmetry = float(np.max(np.abs(Q - Q.T)))

    print(f"\n[TASK_3_2] 3-variable model with 3 cross-terms:")
    print(f"  Q =\n{Q}")
    print(f"  max_asymmetry = {max_asymmetry:.6e}")

    assert np.allclose(Q, Q.T, atol=1e-9), (
        f"Matrix not symmetric with multiple cross-terms. "
        f"max_asymmetry={max_asymmetry:.6e}"
    )

    # Verify specific half-values
    idx = {name: i for i, name in enumerate(var_order)}
    ia, ib, ic = idx["a"], idx["b"], idx["c"]

    assert abs(Q[ia, ib] - 0.5) < 1e-12, f"Q[a,b]={Q[ia,ib]:.6f}, expected 0.5"
    assert abs(Q[ib, ia] - 0.5) < 1e-12, f"Q[b,a]={Q[ib,ia]:.6f}, expected 0.5"
    assert abs(Q[ia, ic] - 1.0) < 1e-12, f"Q[a,c]={Q[ia,ic]:.6f}, expected 1.0"
    assert abs(Q[ic, ia] - 1.0) < 1e-12, f"Q[c,a]={Q[ic,ia]:.6f}, expected 1.0"
    assert abs(Q[ib, ic] - 1.5) < 1e-12, f"Q[b,c]={Q[ib,ic]:.6f}, expected 1.5"
    assert abs(Q[ic, ib] - 1.5) < 1e-12, f"Q[c,b]={Q[ic,ib]:.6f}, expected 1.5"
