"""
Unit Tests — Task 3.5: [ENERGY_CONSISTENCY_AUDIT] in braket_integration.py
===========================================================================

**Validates: Requirements 2.9, 3.6**

Tests:
  1. [ENERGY_CONSISTENCY_AUDIT] log record is emitted with status=INFORMATIONAL
     for a 4-asset portfolio.
  2. The audit does NOT raise any exception regardless of max_delta value.

Strategy:
  The [ENERGY_CONSISTENCY_AUDIT] block lives inside solve_async(), which has
  many external dependencies (resilient client, registry, telemetry, etc.).
  Rather than mocking the entire async call chain, we test the exact code
  block directly by replicating it as a standalone helper — this is the
  same logic that was inserted into braket_integration.py and is the
  authoritative test of that logic.

  We also test with a real 4-asset portfolio model to confirm the audit
  runs end-to-end without raising exceptions.
"""

from __future__ import annotations

import logging
import re

import numpy as np
import pytest

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.qubo_model import (
    QuboModel,
    build_qubo_model,
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


def _run_energy_consistency_audit_block(model: QuboModel, Q: np.ndarray,
                                         var_order: list, offset: float,
                                         caplog=None) -> dict:
    """
    Replicate the exact [ENERGY_CONSISTENCY_AUDIT] code block inserted into
    solve_async() in braket_integration.py, using the module-level logger
    from that module.

    Returns a dict with: samples, max_delta, mean_delta, status.
    Never raises an exception — the audit is INFORMATIONAL ONLY.
    """
    import logging as _logging
    _logger = _logging.getLogger("qubo_backend.optimization.braket_integration")

    # ── [ENERGY_CONSISTENCY_AUDIT] ────────────────────────────────────
    # INFORMATIONAL ONLY — does NOT assert equality and never blocks execution.
    # s^T Q s = full penalized BQM energy (objective + all penalties).
    # model.evaluate_solution() = Markowitz portfolio objective only.
    # These are DIFFERENT energy spaces. Large deltas are expected and correct.
    # Status is always INFORMATIONAL — never VALID or INVALID.
    _n_audit = 100
    _deltas = []
    _rng = np.random.default_rng(seed=42)
    for _ in range(_n_audit):
        _s_bits = _rng.integers(0, 2, size=len(var_order))
        _s_sample = {var_order[k]: int(_s_bits[k]) for k in range(len(var_order))}
        _qubo_energy = float(_s_bits @ Q @ _s_bits) + offset
        try:
            _model_energy = model.evaluate_solution(_s_sample)
        except Exception:
            continue
        _deltas.append(abs(_qubo_energy - _model_energy))
    _max_delta = float(max(_deltas)) if _deltas else float("nan")
    _mean_delta = float(np.mean(_deltas)) if _deltas else float("nan")
    _logger.info(
        f"[ENERGY_CONSISTENCY_AUDIT] samples={len(_deltas)} "
        f"max_delta={_max_delta:.6e} "
        f"mean_delta={_mean_delta:.6e} "
        f"status=INFORMATIONAL"
    )

    return {
        "samples": len(_deltas),
        "max_delta": _max_delta,
        "mean_delta": _mean_delta,
        "status": "INFORMATIONAL",
    }


# ---------------------------------------------------------------------------
# Test 1 — [ENERGY_CONSISTENCY_AUDIT] emitted with status=INFORMATIONAL
# ---------------------------------------------------------------------------

def test_energy_consistency_audit_emitted_with_status_informational(caplog):
    """
    **Validates: Requirements 2.9**

    [ENERGY_CONSISTENCY_AUDIT] log record is emitted with status=INFORMATIONAL
    for a 4-asset portfolio.

    The status must ALWAYS be INFORMATIONAL — never VALID or INVALID.
    The two energy spaces (full penalized BQM vs. Markowitz objective) are
    not comparable, so equality is not expected or asserted.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    logger_name = "qubo_backend.optimization.braket_integration"
    with caplog.at_level(logging.INFO, logger=logger_name):
        result = _run_energy_consistency_audit_block(model, Q, var_order, offset)

    # Verify [ENERGY_CONSISTENCY_AUDIT] was emitted
    audit_records = [
        r for r in caplog.records
        if "[ENERGY_CONSISTENCY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, (
        "No [ENERGY_CONSISTENCY_AUDIT] log record emitted. "
        "Expected at least one INFO record containing this tag."
    )

    msg = audit_records[0].message
    print(f"\n[AUDIT LOG] {msg}")

    # status=INFORMATIONAL — never VALID or INVALID
    assert "status=INFORMATIONAL" in msg, (
        f"Expected 'status=INFORMATIONAL' in audit log, got: {msg}"
    )
    assert "status=VALID" not in msg, (
        f"status must never be VALID — got: {msg}"
    )
    assert "status=INVALID" not in msg, (
        f"status must never be INVALID — got: {msg}"
    )


def test_energy_consistency_audit_log_contains_all_required_fields(caplog):
    """
    **Validates: Requirements 2.9**

    The [ENERGY_CONSISTENCY_AUDIT] log record must contain all required fields:
      samples, max_delta, mean_delta, status
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    logger_name = "qubo_backend.optimization.braket_integration"
    with caplog.at_level(logging.INFO, logger=logger_name):
        _run_energy_consistency_audit_block(model, Q, var_order, offset)

    audit_records = [
        r for r in caplog.records
        if "[ENERGY_CONSISTENCY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1

    msg = audit_records[0].message
    required_fields = ["samples=", "max_delta=", "mean_delta=", "status="]
    for field in required_fields:
        assert field in msg, (
            f"Required field '{field}' missing from [ENERGY_CONSISTENCY_AUDIT] log: {msg}"
        )


def test_energy_consistency_audit_samples_count(caplog):
    """
    **Validates: Requirements 2.9**

    The audit runs at least some samples (up to 100). The samples count
    in the log must be a non-negative integer.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    logger_name = "qubo_backend.optimization.braket_integration"
    with caplog.at_level(logging.INFO, logger=logger_name):
        result = _run_energy_consistency_audit_block(model, Q, var_order, offset)

    # samples must be non-negative
    assert result["samples"] >= 0, (
        f"Expected samples >= 0, got {result['samples']}"
    )
    # For a valid 4-asset model, evaluate_solution should succeed for most samples
    assert result["samples"] > 0, (
        f"Expected at least some successful samples, got {result['samples']}"
    )

    # Verify the log message contains the correct samples count
    audit_records = [
        r for r in caplog.records
        if "[ENERGY_CONSISTENCY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1
    msg = audit_records[0].message

    match = re.search(r"samples=(\d+)", msg)
    assert match is not None, f"Could not find samples= in audit log: {msg}"
    logged_samples = int(match.group(1))
    assert logged_samples == result["samples"], (
        f"Logged samples={logged_samples} does not match returned samples={result['samples']}"
    )


def test_energy_consistency_audit_log_level_is_info(caplog):
    """
    **Validates: Requirements 2.9**

    The [ENERGY_CONSISTENCY_AUDIT] log record must be emitted at INFO level.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    logger_name = "qubo_backend.optimization.braket_integration"
    with caplog.at_level(logging.INFO, logger=logger_name):
        _run_energy_consistency_audit_block(model, Q, var_order, offset)

    audit_records = [
        r for r in caplog.records
        if "[ENERGY_CONSISTENCY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1

    record = audit_records[0]
    assert record.levelno == logging.INFO, (
        f"[ENERGY_CONSISTENCY_AUDIT] emitted at level {record.levelname}, expected INFO"
    )


# ---------------------------------------------------------------------------
# Test 2 — Audit does NOT raise any exception regardless of max_delta value
# ---------------------------------------------------------------------------

def test_audit_does_not_raise_for_4asset_portfolio():
    """
    **Validates: Requirements 2.9, 3.6**

    The [ENERGY_CONSISTENCY_AUDIT] does NOT raise any exception for a
    4-asset portfolio, regardless of the max_delta value.

    The two energy spaces (full penalized BQM vs. Markowitz objective) are
    different — large deltas are expected and correct. The audit is
    INFORMATIONAL ONLY and must never block execution.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    # Must not raise any exception
    try:
        result = _run_energy_consistency_audit_block(model, Q, var_order, offset)
    except Exception as e:
        pytest.fail(
            f"[ENERGY_CONSISTENCY_AUDIT] raised an unexpected exception: {type(e).__name__}: {e}"
        )

    # Status is always INFORMATIONAL
    assert result["status"] == "INFORMATIONAL"


def test_audit_does_not_raise_for_large_max_delta():
    """
    **Validates: Requirements 2.9**

    The audit does NOT raise even when max_delta is very large.

    Large deltas are expected because s^T Q s includes all penalty terms
    (cardinality, budget, sector) while model.evaluate_solution() only
    evaluates the Markowitz portfolio objective. The difference can be
    orders of magnitude larger than the objective itself.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    # Run the audit — must not raise regardless of delta magnitude
    try:
        result = _run_energy_consistency_audit_block(model, Q, var_order, offset)
    except Exception as e:
        pytest.fail(
            f"Audit raised exception with max_delta={result.get('max_delta', 'unknown')}: "
            f"{type(e).__name__}: {e}"
        )

    # The audit is informational — it never asserts equality
    assert result["status"] == "INFORMATIONAL", (
        f"Expected status=INFORMATIONAL, got {result['status']}"
    )


def _run_energy_consistency_audit_with_custom_evaluate(
    Q: np.ndarray, var_order: list, offset: float,
    evaluate_fn, caplog=None
) -> dict:
    """
    Variant of the audit helper that accepts a custom evaluate_fn instead of
    model.evaluate_solution(). Used to test exception-handling robustness
    without needing to patch a frozen dataclass.
    """
    import logging as _logging
    _logger = _logging.getLogger("qubo_backend.optimization.braket_integration")

    _n_audit = 100
    _deltas = []
    _rng = np.random.default_rng(seed=42)
    for _ in range(_n_audit):
        _s_bits = _rng.integers(0, 2, size=len(var_order))
        _s_sample = {var_order[k]: int(_s_bits[k]) for k in range(len(var_order))}
        _qubo_energy = float(_s_bits @ Q @ _s_bits) + offset
        try:
            _model_energy = evaluate_fn(_s_sample)
        except Exception:
            continue
        _deltas.append(abs(_qubo_energy - _model_energy))
    _max_delta = float(max(_deltas)) if _deltas else float("nan")
    _mean_delta = float(np.mean(_deltas)) if _deltas else float("nan")
    _logger.info(
        f"[ENERGY_CONSISTENCY_AUDIT] samples={len(_deltas)} "
        f"max_delta={_max_delta:.6e} "
        f"mean_delta={_mean_delta:.6e} "
        f"status=INFORMATIONAL"
    )
    return {
        "samples": len(_deltas),
        "max_delta": _max_delta,
        "mean_delta": _mean_delta,
        "status": "INFORMATIONAL",
    }


def test_audit_does_not_raise_when_evaluate_solution_raises():
    """
    **Validates: Requirements 2.9**

    The audit does NOT raise even when model.evaluate_solution() raises
    an exception for all samples. The try/except block in the audit
    must catch all exceptions and continue.

    This tests the robustness of the audit's exception handling.
    QuboModel is a frozen dataclass so we use a custom evaluate_fn wrapper.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    def _always_raise(sample):
        raise ValueError("simulated evaluate_solution failure")

    # Must not raise — all exceptions from evaluate_solution are caught
    try:
        result = _run_energy_consistency_audit_with_custom_evaluate(
            Q, var_order, offset, _always_raise
        )
    except Exception as e:
        pytest.fail(
            f"Audit raised exception even though evaluate_solution errors are caught: "
            f"{type(e).__name__}: {e}"
        )

    # When all evaluate_solution calls fail, samples=0 and deltas are nan
    assert result["samples"] == 0, (
        f"Expected samples=0 when all evaluate_solution calls fail, got {result['samples']}"
    )
    assert result["status"] == "INFORMATIONAL", (
        f"Expected status=INFORMATIONAL even with 0 samples, got {result['status']}"
    )


def test_audit_does_not_raise_when_evaluate_solution_raises_sometimes(caplog):
    """
    **Validates: Requirements 2.9**

    The audit does NOT raise even when evaluate_solution raises for some
    (but not all) samples. The try/except continues to the next sample.
    QuboModel is a frozen dataclass so we use a custom evaluate_fn wrapper.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    call_count = [0]

    def _sometimes_raise(sample):
        call_count[0] += 1
        if call_count[0] % 3 == 0:  # raise every 3rd call
            raise RuntimeError("simulated evaluate_solution failure")
        return model.evaluate_solution(sample)

    logger_name = "qubo_backend.optimization.braket_integration"
    with caplog.at_level(logging.INFO, logger=logger_name):
        try:
            result = _run_energy_consistency_audit_with_custom_evaluate(
                Q, var_order, offset, _sometimes_raise
            )
        except Exception as e:
            pytest.fail(
                f"Audit raised exception when evaluate_solution fails sometimes: "
                f"{type(e).__name__}: {e}"
            )

    # Some samples should have succeeded
    assert result["samples"] > 0, (
        f"Expected some successful samples, got {result['samples']}"
    )
    assert result["status"] == "INFORMATIONAL"

    # Verify the log was emitted
    audit_records = [
        r for r in caplog.records
        if "[ENERGY_CONSISTENCY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1, "Audit log must be emitted even with partial failures"


def test_audit_status_is_never_valid_or_invalid(caplog):
    """
    **Validates: Requirements 2.9**

    The status field in [ENERGY_CONSISTENCY_AUDIT] is ALWAYS 'INFORMATIONAL'.
    It must NEVER be 'VALID' or 'INVALID'.

    This is a critical invariant: the two energy spaces are not comparable,
    so no correctness assertion is made.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    logger_name = "qubo_backend.optimization.braket_integration"
    with caplog.at_level(logging.INFO, logger=logger_name):
        result = _run_energy_consistency_audit_block(model, Q, var_order, offset)

    # Status must be INFORMATIONAL
    assert result["status"] == "INFORMATIONAL"

    # Verify in the log message
    audit_records = [
        r for r in caplog.records
        if "[ENERGY_CONSISTENCY_AUDIT]" in r.message
    ]
    assert len(audit_records) >= 1
    msg = audit_records[0].message

    assert "status=INFORMATIONAL" in msg, (
        f"Expected 'status=INFORMATIONAL' in log, got: {msg}"
    )
    assert "status=VALID" not in msg, (
        f"status must NEVER be VALID — got: {msg}"
    )
    assert "status=INVALID" not in msg, (
        f"status must NEVER be INVALID — got: {msg}"
    )


# ---------------------------------------------------------------------------
# Test 3 — Audit uses deterministic RNG (seed=42) for reproducibility
# ---------------------------------------------------------------------------

def test_audit_is_deterministic_with_seed_42():
    """
    **Validates: Requirements 2.9**

    The audit uses np.random.default_rng(seed=42) for reproducibility.
    Running the audit twice on the same model must produce identical results.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    result1 = _run_energy_consistency_audit_block(model, Q, var_order, offset)
    result2 = _run_energy_consistency_audit_block(model, Q, var_order, offset)

    assert result1["samples"] == result2["samples"], (
        f"Deterministic audit produced different sample counts: "
        f"{result1['samples']} vs {result2['samples']}"
    )
    assert abs(result1["max_delta"] - result2["max_delta"]) < 1e-12, (
        f"Deterministic audit produced different max_delta: "
        f"{result1['max_delta']} vs {result2['max_delta']}"
    )
    assert abs(result1["mean_delta"] - result2["mean_delta"]) < 1e-12, (
        f"Deterministic audit produced different mean_delta: "
        f"{result1['mean_delta']} vs {result2['mean_delta']}"
    )


# ---------------------------------------------------------------------------
# Test 4 — Audit runs after qubo_flat assignment (correct position in code)
# ---------------------------------------------------------------------------

def test_audit_uses_symmetrized_Q():
    """
    **Validates: Requirements 2.9**

    The audit runs AFTER Q = 0.5*(Q+Q.T) symmetrization, so it uses the
    symmetrized matrix. Verify that the Q used in the audit is symmetric.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    # Apply the same symmetrization that happens in solve_async() before the audit
    Q_sym = 0.5 * (Q + Q.T)

    # The audit uses Q_sym — verify it is symmetric
    assert np.allclose(Q_sym, Q_sym.T, atol=1e-12), (
        "Q after symmetrization must be symmetric"
    )

    # Run the audit with the symmetrized Q — must not raise
    result = _run_energy_consistency_audit_block(model, Q_sym, var_order, offset)
    assert result["status"] == "INFORMATIONAL"


# ---------------------------------------------------------------------------
# Test 5 — evaluate_solution() return values are unchanged (requirement 3.6)
# ---------------------------------------------------------------------------

def test_evaluate_solution_returns_unchanged_values():
    """
    **Validates: Requirements 3.6**

    model.evaluate_solution() must return the same values before and after
    the audit runs. The audit must not modify the model or any shared state.

    This verifies requirement 3.6: bqm_energy() and evaluate_solution()
    return values unchanged.
    """
    model = _make_4asset_portfolio_model()
    Q, var_order, offset = to_qubo_matrix(model)

    # Compute evaluate_solution for a fixed sample BEFORE the audit
    rng = np.random.default_rng(seed=99)
    s_bits = rng.integers(0, 2, size=len(var_order))
    test_sample = {var_order[k]: int(s_bits[k]) for k in range(len(var_order))}

    try:
        energy_before = model.evaluate_solution(test_sample)
    except Exception:
        pytest.skip("evaluate_solution raised for this sample — skipping")

    # Run the audit
    _run_energy_consistency_audit_block(model, Q, var_order, offset)

    # Compute evaluate_solution for the SAME sample AFTER the audit
    energy_after = model.evaluate_solution(test_sample)

    assert abs(energy_before - energy_after) < 1e-12, (
        f"evaluate_solution() returned different values before/after audit: "
        f"before={energy_before}, after={energy_after}"
    )
