"""
Unit Tests — Task 3.3: [QUBO_SYMMETRY_AUDIT] telemetry and hard assertion in to_qubo_matrix()
==============================================================================================

**Validates: Requirements 2.3, 2.4**

Tests:
  1. [QUBO_SYMMETRY_AUDIT] log record is emitted with symmetric=True,
     max_asymmetry < 1e-9, and correct shape for a valid model.
  2. to_qubo_matrix() raises RuntimeError("QUBO_SYMMETRY_CORRUPTION") when
     a model is manually constructed to produce an asymmetric matrix
     (by bypassing add_symmetric_quadratic()).
"""

from __future__ import annotations

import logging
import unittest.mock as mock

import numpy as np
import pytest

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.qubo_model import (
    QuboModel,
    add_symmetric_quadratic,
    to_qubo_matrix,
)
from qubo_backend.optimization.bqm_builder import (
    BQMBuildResult,
    PortfolioBQM,
    build_portfolio_bqm,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _make_minimal_2var_model() -> QuboModel:
    """Build a QuboModel with two variables and one off-diagonal term.

    Variables: x_0_0, x_1_0
    Quadratic: (x_0_0, x_1_0) -> bias=1.0

    After the fix, to_qubo_matrix() writes Q[0,1]=0.5 AND Q[1,0]=0.5
    (Convention B), producing a symmetric matrix.
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
    """4-asset portfolio — the primary crash scenario."""
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


def _make_linear_only_model() -> QuboModel:
    """Build a model with only linear (diagonal) terms — no quadratic cross-terms.

    This is trivially symmetric and must pass the audit with symmetric=True.
    """
    bqm = PortfolioBQM()
    bqm.add_variable("x_0_0")
    bqm.add_variable("x_1_0")
    bqm.add_variable("x_2_0")
    bqm.add_linear("x_0_0", 2.5)
    bqm.add_linear("x_1_0", 3.7)
    bqm.add_linear("x_2_0", 1.1)

    build = BQMBuildResult(
        bqm=bqm,
        variable_order=["x_0_0", "x_1_0", "x_2_0"],
        weight_variables=[["x_0_0"], ["x_1_0"], ["x_2_0"]],
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
    return QuboModel(request=request, build=build)


# ---------------------------------------------------------------------------
# Test 1 — [QUBO_SYMMETRY_AUDIT] emitted with symmetric=True for valid models
# ---------------------------------------------------------------------------

def test_symmetry_audit_log_emitted_for_2var_model(caplog):
    """
    **Validates: Requirements 2.3**

    [QUBO_SYMMETRY_AUDIT] log record is emitted with:
      - symmetric=True
      - max_asymmetry < 1e-9
      - correct shape=(2, 2)

    for a valid 2-variable model with one cross-term.
    """
    model = _make_minimal_2var_model()

    with caplog.at_level(logging.INFO):
        Q, var_order, offset = to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUBO_SYMMETRY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "No [QUBO_SYMMETRY_AUDIT] log record emitted by to_qubo_matrix(). "
        "Expected at least one INFO record containing this tag."
    )

    msg = audit_records[0].message
    print(f"\n[AUDIT LOG] {msg}")

    # shape must be (2, 2)
    assert "shape=(2, 2)" in msg, (
        f"Expected 'shape=(2, 2)' in audit log, got: {msg}"
    )

    # symmetric=True
    assert "symmetric=True" in msg, (
        f"Expected 'symmetric=True' in audit log, got: {msg}"
    )

    # max_asymmetry must be present and < 1e-9
    # Extract the value from the log message
    import re
    match = re.search(r"max_asymmetry=([0-9.e+\-]+)", msg)
    assert match is not None, f"Could not find max_asymmetry in audit log: {msg}"
    max_asym_logged = float(match.group(1))
    assert max_asym_logged < 1e-9, (
        f"Logged max_asymmetry={max_asym_logged:.6e} >= 1e-9. "
        f"Expected < 1e-9 for a valid symmetric model."
    )

    # frobenius_asymmetry must be present
    assert "frobenius_asymmetry=" in msg, (
        f"Expected 'frobenius_asymmetry=' in audit log, got: {msg}"
    )


def test_symmetry_audit_log_emitted_for_4asset_portfolio(caplog):
    """
    **Validates: Requirements 2.3**

    [QUBO_SYMMETRY_AUDIT] log record is emitted with symmetric=True and
    correct shape for the 4-asset portfolio model.
    """
    model = _make_4asset_portfolio_model()
    n = model.variable_count
    expected_shape = f"({n}, {n})"

    with caplog.at_level(logging.INFO):
        Q, var_order, offset = to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUBO_SYMMETRY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "No [QUBO_SYMMETRY_AUDIT] log record emitted for 4-asset portfolio."
    )

    msg = audit_records[0].message
    print(f"\n[AUDIT LOG] {msg}")

    assert f"shape={expected_shape}" in msg, (
        f"Expected 'shape={expected_shape}' in audit log, got: {msg}"
    )
    assert "symmetric=True" in msg, (
        f"Expected 'symmetric=True' in audit log, got: {msg}"
    )

    import re
    match = re.search(r"max_asymmetry=([0-9.e+\-]+)", msg)
    assert match is not None, f"Could not find max_asymmetry in audit log: {msg}"
    max_asym_logged = float(match.group(1))
    assert max_asym_logged < 1e-9, (
        f"Logged max_asymmetry={max_asym_logged:.6e} >= 1e-9 for 4-asset portfolio."
    )


def test_symmetry_audit_log_emitted_for_linear_only_model(caplog):
    """
    **Validates: Requirements 2.3**

    [QUBO_SYMMETRY_AUDIT] log record is emitted with symmetric=True and
    correct shape=(3, 3) for a linear-only (diagonal) model.

    Diagonal matrices are trivially symmetric — the audit must pass them through.
    """
    model = _make_linear_only_model()

    with caplog.at_level(logging.INFO):
        Q, var_order, offset = to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUBO_SYMMETRY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "No [QUBO_SYMMETRY_AUDIT] log record emitted for linear-only model."
    )

    msg = audit_records[0].message
    assert "shape=(3, 3)" in msg, f"Expected 'shape=(3, 3)' in audit log, got: {msg}"
    assert "symmetric=True" in msg, f"Expected 'symmetric=True' in audit log, got: {msg}"


def test_symmetry_audit_log_contains_all_required_fields(caplog):
    """
    **Validates: Requirements 2.3**

    The [QUBO_SYMMETRY_AUDIT] log record must contain all four required fields:
      shape, max_asymmetry, frobenius_asymmetry, symmetric
    """
    model = _make_minimal_2var_model()

    with caplog.at_level(logging.INFO):
        to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUBO_SYMMETRY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1

    msg = audit_records[0].message
    required_fields = ["shape=", "max_asymmetry=", "frobenius_asymmetry=", "symmetric="]
    for field in required_fields:
        assert field in msg, (
            f"Required field '{field}' missing from [QUBO_SYMMETRY_AUDIT] log: {msg}"
        )


def test_symmetry_audit_log_level_is_info(caplog):
    """
    **Validates: Requirements 2.3**

    The [QUBO_SYMMETRY_AUDIT] log record must be emitted at INFO level.
    """
    model = _make_minimal_2var_model()

    with caplog.at_level(logging.INFO):
        to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUBO_SYMMETRY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1

    record = audit_records[0]
    assert record.levelno == logging.INFO, (
        f"[QUBO_SYMMETRY_AUDIT] emitted at level {record.levelname}, expected INFO"
    )


# ---------------------------------------------------------------------------
# Test 2 — RuntimeError raised for asymmetric matrix
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_raises_runtime_error_for_asymmetric_matrix():
    """
    **Validates: Requirements 2.4**

    to_qubo_matrix() raises RuntimeError("QUBO_SYMMETRY_CORRUPTION: ...")
    when the constructed matrix is asymmetric.

    Strategy: monkeypatch add_symmetric_quadratic to write the full value
    to only one side (simulating the old bug), so the quadratic loop
    produces an asymmetric matrix that triggers the audit's hard assertion.
    """
    model = _make_minimal_2var_model()

    def _asymmetric_write(Q: np.ndarray, i: int, j: int, value: float) -> None:
        """Simulate the old bug: write full value to upper triangle only."""
        if i == j:
            Q[i, i] += value
        elif i <= j:
            Q[i, j] += value  # upper triangle only — no mirror
        else:
            Q[j, i] += value  # lower triangle only — no mirror

    with mock.patch(
        "qubo_backend.optimization.qubo_model.add_symmetric_quadratic",
        side_effect=_asymmetric_write,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            to_qubo_matrix(model)

    error_msg = str(exc_info.value)
    print(f"\n[RUNTIME_ERROR] {error_msg}")

    assert "QUBO_SYMMETRY_CORRUPTION" in error_msg, (
        f"RuntimeError message does not contain 'QUBO_SYMMETRY_CORRUPTION': {error_msg}"
    )
    assert "max_asymmetry=" in error_msg, (
        f"RuntimeError message does not contain 'max_asymmetry=': {error_msg}"
    )


def test_to_qubo_matrix_raises_runtime_error_message_format():
    """
    **Validates: Requirements 2.4**

    The RuntimeError message must match the format:
      "QUBO_SYMMETRY_CORRUPTION: max_asymmetry=<value>"

    Verify the exact format specified in the task.
    """
    model = _make_minimal_2var_model()

    def _asymmetric_write(Q: np.ndarray, i: int, j: int, value: float) -> None:
        """Write full value to upper triangle only (old bug simulation)."""
        if i == j:
            Q[i, i] += value
        elif i <= j:
            Q[i, j] += value
        else:
            Q[j, i] += value

    with mock.patch(
        "qubo_backend.optimization.qubo_model.add_symmetric_quadratic",
        side_effect=_asymmetric_write,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            to_qubo_matrix(model)

    error_msg = str(exc_info.value)

    # Must start with QUBO_SYMMETRY_CORRUPTION:
    assert error_msg.startswith("QUBO_SYMMETRY_CORRUPTION:"), (
        f"RuntimeError message must start with 'QUBO_SYMMETRY_CORRUPTION:', got: {error_msg}"
    )

    # max_asymmetry value must be a non-zero float (the asymmetry is 1.0 for bias=1.0)
    import re
    match = re.search(r"max_asymmetry=([0-9.e+\-]+)", error_msg)
    assert match is not None, f"Could not find max_asymmetry in error message: {error_msg}"
    max_asym_in_error = float(match.group(1))
    assert max_asym_in_error >= 1e-9, (
        f"max_asymmetry in error message = {max_asym_in_error:.6e}, "
        f"expected >= 1e-9 (the matrix is genuinely asymmetric)"
    )


def test_to_qubo_matrix_raises_for_large_asymmetry():
    """
    **Validates: Requirements 2.4**

    to_qubo_matrix() raises RuntimeError when the matrix has large asymmetry
    (simulating the original crash scenario with max_asymmetry ≈ 558).

    Uses a 3-variable model with a large cross-term bias to produce
    a clearly asymmetric matrix when the old bug is simulated.
    """
    bqm = PortfolioBQM()
    bqm.add_variable("a")
    bqm.add_variable("b")
    bqm.add_variable("c")
    bqm.add_quadratic("a", "b", 100.0)   # large bias
    bqm.add_quadratic("b", "c", 200.0)   # large bias

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

    def _asymmetric_write(Q: np.ndarray, i: int, j: int, value: float) -> None:
        """Simulate old bug: upper-triangle only."""
        if i == j:
            Q[i, i] += value
        elif i <= j:
            Q[i, j] += value
        else:
            Q[j, i] += value

    with mock.patch(
        "qubo_backend.optimization.qubo_model.add_symmetric_quadratic",
        side_effect=_asymmetric_write,
    ):
        with pytest.raises(RuntimeError) as exc_info:
            to_qubo_matrix(model)

    error_msg = str(exc_info.value)
    assert "QUBO_SYMMETRY_CORRUPTION" in error_msg, (
        f"Expected QUBO_SYMMETRY_CORRUPTION in error, got: {error_msg}"
    )

    import re
    match = re.search(r"max_asymmetry=([0-9.e+\-]+)", error_msg)
    assert match is not None
    max_asym_in_error = float(match.group(1))
    # With biases of 100 and 200, max_asymmetry should be ~200
    assert max_asym_in_error >= 100.0, (
        f"Expected max_asymmetry >= 100.0 for large-bias model, got {max_asym_in_error:.6e}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Valid symmetric matrices pass through without exception
# ---------------------------------------------------------------------------

def test_to_qubo_matrix_does_not_raise_for_valid_symmetric_model():
    """
    **Validates: Requirements 2.3, 2.4**

    Valid symmetric matrices must pass through to_qubo_matrix() without
    raising RuntimeError. The audit must not block correct matrices.
    """
    model = _make_minimal_2var_model()
    # Should not raise
    Q, var_order, offset = to_qubo_matrix(model)
    assert Q is not None
    assert np.allclose(Q, Q.T, atol=1e-9)


def test_to_qubo_matrix_does_not_raise_for_4asset_portfolio():
    """
    **Validates: Requirements 2.3, 2.4**

    The 4-asset portfolio (primary crash scenario) must pass through
    to_qubo_matrix() without raising RuntimeError after the fix.
    """
    model = _make_4asset_portfolio_model()
    # Should not raise
    Q, var_order, offset = to_qubo_matrix(model)
    assert Q is not None
    assert np.allclose(Q, Q.T, atol=1e-9)


def test_to_qubo_matrix_does_not_raise_for_linear_only_model():
    """
    **Validates: Requirements 2.3, 2.4**

    Linear-only (diagonal) models are trivially symmetric and must not
    trigger the RuntimeError.
    """
    model = _make_linear_only_model()
    # Should not raise
    Q, var_order, offset = to_qubo_matrix(model)
    assert Q is not None
    assert np.allclose(Q, Q.T, atol=1e-9)


# ---------------------------------------------------------------------------
# Test 4 — Audit log emitted with symmetric=False before RuntimeError
# ---------------------------------------------------------------------------

def test_symmetry_audit_log_emitted_with_symmetric_false_before_error(caplog):
    """
    **Validates: Requirements 2.3, 2.4**

    When the matrix is asymmetric, the [QUBO_SYMMETRY_AUDIT] log record
    must be emitted with symmetric=False BEFORE the RuntimeError is raised.

    This confirms the telemetry is always written, even on the error path.
    """
    model = _make_minimal_2var_model()

    def _asymmetric_write(Q: np.ndarray, i: int, j: int, value: float) -> None:
        if i == j:
            Q[i, i] += value
        elif i <= j:
            Q[i, j] += value
        else:
            Q[j, i] += value

    with caplog.at_level(logging.INFO):
        with mock.patch(
            "qubo_backend.optimization.qubo_model.add_symmetric_quadratic",
            side_effect=_asymmetric_write,
        ):
            with pytest.raises(RuntimeError):
                to_qubo_matrix(model)

    audit_records = [
        r for r in caplog.records
        if "[QUBO_SYMMETRY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "No [QUBO_SYMMETRY_AUDIT] log record emitted even on the error path. "
        "Telemetry must be written before raising RuntimeError."
    )

    msg = audit_records[0].message
    print(f"\n[AUDIT LOG on error path] {msg}")

    assert "symmetric=False" in msg, (
        f"Expected 'symmetric=False' in audit log on error path, got: {msg}"
    )
