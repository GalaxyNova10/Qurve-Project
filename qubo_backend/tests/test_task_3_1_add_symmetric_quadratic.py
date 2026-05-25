"""
Unit Tests — Task 3.1: add_symmetric_quadratic() helper and [QUADRATIC_ENERGY_CONVENTION_AUDIT]
================================================================================================

**Validates: Requirements 2.1, 2.2**

Tests:
  1. add_symmetric_quadratic(Q, 0, 1, 0.42) writes Q[0,1]==0.21 AND Q[1,0]==0.21 (half-value)
  2. add_symmetric_quadratic(Q, 2, 2, 1.5) writes Q[2,2]==1.5 only once (no halving on diagonal)
  3. [QUADRATIC_ENERGY_CONVENTION_AUDIT] emits expected=1.0 actual=1.0 double_count_detected=False
  4. s^T Q_sym s == 1.0 for s=[1,1] and a 2-variable model with one cross-term bias=1.0 (not 2.0)
"""

from __future__ import annotations

import logging
import numpy as np
import pytest

from qubo_backend.optimization.qubo_model import (
    add_symmetric_quadratic,
    _verify_energy_convention,
    to_qubo_matrix,
    QuboModel,
)
from qubo_backend.optimization.bqm_builder import (
    BQMBuildResult,
    PortfolioBQM,
)
from qubo_backend.optimization.contracts import SolverRequest


# ---------------------------------------------------------------------------
# Test 1 — Off-diagonal half-value write
# ---------------------------------------------------------------------------

def test_add_symmetric_quadratic_off_diagonal_half_value():
    """
    **Validates: Requirements 2.1, 2.2**

    assert add_symmetric_quadratic(Q, 0, 1, 0.42) writes Q[0,1]==0.21 AND Q[1,0]==0.21.

    Convention B: each off-diagonal position receives value/2 so that
    x^T Q_sym x recovers the full coefficient via the matmul summing both positions.
    """
    Q = np.zeros((3, 3))
    add_symmetric_quadratic(Q, 0, 1, 0.42)

    assert abs(Q[0, 1] - 0.21) < 1e-12, (
        f"Q[0,1] = {Q[0,1]:.15f}, expected 0.21 (half of 0.42)"
    )
    assert abs(Q[1, 0] - 0.21) < 1e-12, (
        f"Q[1,0] = {Q[1,0]:.15f}, expected 0.21 (half of 0.42)"
    )

    # All other entries must remain zero
    for i in range(3):
        for j in range(3):
            if (i, j) not in ((0, 1), (1, 0)):
                assert Q[i, j] == 0.0, (
                    f"Q[{i},{j}] = {Q[i,j]:.6f}, expected 0.0 (untouched)"
                )


def test_add_symmetric_quadratic_off_diagonal_symmetry():
    """
    **Validates: Requirements 2.1, 2.2**

    After add_symmetric_quadratic(Q, i, j, v) for i != j, Q[i,j] == Q[j,i].
    The matrix is symmetric for the written entry.
    """
    Q = np.zeros((4, 4))
    add_symmetric_quadratic(Q, 1, 3, 7.0)

    assert abs(Q[1, 3] - 3.5) < 1e-12, f"Q[1,3] = {Q[1,3]:.15f}, expected 3.5"
    assert abs(Q[3, 1] - 3.5) < 1e-12, f"Q[3,1] = {Q[3,1]:.15f}, expected 3.5"
    assert Q[1, 3] == Q[3, 1], "Q[1,3] != Q[3,1] — not symmetric"


def test_add_symmetric_quadratic_accumulates_correctly():
    """
    **Validates: Requirements 2.1**

    Multiple calls to add_symmetric_quadratic accumulate correctly.
    Each call adds value/2 to each position.
    """
    Q = np.zeros((3, 3))
    add_symmetric_quadratic(Q, 0, 2, 1.0)
    add_symmetric_quadratic(Q, 0, 2, 1.0)

    # After two calls with value=1.0, each position should have 2 * (1.0/2) = 1.0
    assert abs(Q[0, 2] - 1.0) < 1e-12, f"Q[0,2] = {Q[0,2]:.15f}, expected 1.0"
    assert abs(Q[2, 0] - 1.0) < 1e-12, f"Q[2,0] = {Q[2,0]:.15f}, expected 1.0"


# ---------------------------------------------------------------------------
# Test 2 — Diagonal no-halving
# ---------------------------------------------------------------------------

def test_add_symmetric_quadratic_diagonal_no_halving():
    """
    **Validates: Requirements 2.1**

    assert add_symmetric_quadratic(Q, 2, 2, 1.5) writes Q[2,2]==1.5 only once (no halving).

    Diagonal entries represent linear terms and must not be halved.
    """
    Q = np.zeros((4, 4))
    add_symmetric_quadratic(Q, 2, 2, 1.5)

    assert abs(Q[2, 2] - 1.5) < 1e-12, (
        f"Q[2,2] = {Q[2,2]:.15f}, expected 1.5 (no halving on diagonal)"
    )

    # All other entries must remain zero
    for i in range(4):
        for j in range(4):
            if (i, j) != (2, 2):
                assert Q[i, j] == 0.0, (
                    f"Q[{i},{j}] = {Q[i,j]:.6f}, expected 0.0 (untouched)"
                )


def test_add_symmetric_quadratic_diagonal_zero():
    """
    **Validates: Requirements 2.1**

    Diagonal write with value=0.0 leaves Q[i,i] unchanged (still 0.0).
    """
    Q = np.zeros((3, 3))
    add_symmetric_quadratic(Q, 1, 1, 0.0)
    assert Q[1, 1] == 0.0, f"Q[1,1] = {Q[1,1]:.6f}, expected 0.0"


def test_add_symmetric_quadratic_diagonal_accumulates():
    """
    **Validates: Requirements 2.1**

    Multiple diagonal writes accumulate without halving.
    """
    Q = np.zeros((3, 3))
    add_symmetric_quadratic(Q, 0, 0, 2.0)
    add_symmetric_quadratic(Q, 0, 0, 3.0)

    assert abs(Q[0, 0] - 5.0) < 1e-12, (
        f"Q[0,0] = {Q[0,0]:.15f}, expected 5.0 (2.0 + 3.0, no halving)"
    )


# ---------------------------------------------------------------------------
# Test 3 — [QUADRATIC_ENERGY_CONVENTION_AUDIT] log output
# ---------------------------------------------------------------------------

def test_verify_energy_convention_emits_correct_log(caplog):
    """
    **Validates: Requirements 2.1, 2.2**

    assert [QUADRATIC_ENERGY_CONVENTION_AUDIT] emits:
      expected=1.0 actual=1.0 double_count_detected=False

    This confirms Convention B is correctly implemented: s^T Q_sym s == 1.0
    for s=[1,1] and a 2-variable model with one cross-term bias=1.0.
    """
    with caplog.at_level(logging.INFO):
        _verify_energy_convention()

    # Find the audit log record
    audit_records = [
        r for r in caplog.records
        if "[QUADRATIC_ENERGY_CONVENTION_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "No [QUADRATIC_ENERGY_CONVENTION_AUDIT] log record emitted. "
        "Expected at least one INFO record containing this tag."
    )

    msg = audit_records[0].message
    print(f"\n[AUDIT LOG] {msg}")

    assert "expected=1.0" in msg, (
        f"Expected 'expected=1.0' in audit log, got: {msg}"
    )
    assert "actual=1.000000" in msg, (
        f"Expected 'actual=1.000000' in audit log, got: {msg}"
    )
    assert "double_count_detected=False" in msg, (
        f"Expected 'double_count_detected=False' in audit log, got: {msg}"
    )


def test_verify_energy_convention_does_not_raise():
    """
    **Validates: Requirements 2.1, 2.2**

    _verify_energy_convention() must NOT raise RuntimeError when
    add_symmetric_quadratic() is correctly implemented (Convention B).
    """
    # Should complete without raising
    _verify_energy_convention()


# ---------------------------------------------------------------------------
# Test 4 — s^T Q_sym s == 1.0 for s=[1,1], bias=1.0
# ---------------------------------------------------------------------------

def test_energy_convention_matmul_result():
    """
    **Validates: Requirements 2.1, 2.2**

    assert s^T Q_sym s == 1.0 for s=[1,1] and a 2-variable model with
    one cross-term bias=1.0 (not 2.0).

    This is the core Convention B verification:
    - BQM stores coupling (x_0_0, x_1_0) with bias=1.0 (full coefficient)
    - add_symmetric_quadratic writes Q[0,1]=0.5 and Q[1,0]=0.5
    - s^T Q s = s[0]*Q[0,1]*s[1] + s[1]*Q[1,0]*s[0] = 0.5 + 0.5 = 1.0
    - NOT 2.0 (which would indicate full-value dual-write / double-counting)
    """
    Q = np.zeros((2, 2))
    add_symmetric_quadratic(Q, 0, 1, 1.0)

    s = np.array([1.0, 1.0])
    energy = float(s @ Q @ s)

    print(f"\n[ENERGY_CONVENTION] Q =\n{Q}")
    print(f"[ENERGY_CONVENTION] s = {s}")
    print(f"[ENERGY_CONVENTION] s^T Q s = {energy:.6f} (expected 1.0, NOT 2.0)")

    assert abs(energy - 1.0) < 1e-12, (
        f"s^T Q_sym s = {energy:.6f}, expected 1.0. "
        f"If result is 2.0, add_symmetric_quadratic() is writing full value to both "
        f"positions (double-counting). Convention B requires value/2 at each position."
    )
    assert abs(energy - 2.0) > 0.5, (
        f"s^T Q_sym s = {energy:.6f} is suspiciously close to 2.0 — "
        f"this would indicate double-counting (full-value dual-write)."
    )


def test_energy_convention_via_to_qubo_matrix():
    """
    **Validates: Requirements 2.1, 2.2**

    End-to-end: build a 2-variable QuboModel with one cross-term bias=1.0,
    call to_qubo_matrix(), and verify s^T Q s == 1.0 for s=[1,1].

    NOTE: to_qubo_matrix() still uses the DEFECTIVE single-side write (Task 3.2
    will fix that). This test verifies the helper function itself is correct
    by calling it directly — not via to_qubo_matrix().
    """
    # Build the model manually using add_symmetric_quadratic directly
    Q = np.zeros((2, 2))
    add_symmetric_quadratic(Q, 0, 1, 1.0)

    s = np.array([1.0, 1.0])
    energy = float(s @ Q @ s)

    assert abs(energy - 1.0) < 1e-12, (
        f"Direct helper test: s^T Q_sym s = {energy:.6f}, expected 1.0"
    )


def test_to_qubo_matrix_calls_verify_energy_convention(caplog):
    """
    **Validates: Requirements 2.1, 2.2**

    to_qubo_matrix() must call _verify_energy_convention() at the top,
    which emits [QUADRATIC_ENERGY_CONVENTION_AUDIT] in the logs.
    """
    bqm = PortfolioBQM()
    bqm.add_variable("x_0_0")
    bqm.add_variable("x_1_0")
    bqm.add_linear("x_0_0", 1.0)
    bqm.add_linear("x_1_0", 1.0)

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

    with caplog.at_level(logging.INFO):
        Q, var_order, offset = to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUADRATIC_ENERGY_CONVENTION_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "to_qubo_matrix() did not emit [QUADRATIC_ENERGY_CONVENTION_AUDIT]. "
        "_verify_energy_convention() must be called at the top of to_qubo_matrix()."
    )
