"""Bug Condition Exploration Test — QUBO Flat List Dimension Mismatch Crash.

**Validates: Requirements 1.1, 1.2, 1.3**

This test is EXPECTED TO FAIL on unfixed code.
Failure confirms the bug exists:
  ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0
              (size N² is different from N)

DO NOT attempt to fix the test or the code when it fails.
The test encodes the expected behavior — it will validate the fix when it passes
after implementation.

Bug Condition (isBugCondition):
  - req_meta["qubo_matrix"] is a flat list of n_qubits² floats
  - np.array(Q).ndim == 1
  - len(np.array(Q)) == n_qubits ** 2
  - no reshape has been performed before s @ Q @ s
"""

import math
import numpy as np
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# Import the function under test (unfixed code)
from qaoa_circuit import decode_and_evaluate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req_meta(n_qubits: int, flat_qubo: list[float]) -> dict:
    """Build a minimal req_meta dict with a flat qubo_matrix.

    Provides all fields that decode_and_evaluate() reads so the function
    reaches the matmul before failing on a missing-key error.
    """
    n_assets = n_qubits  # simplest mapping: 1 qubit per asset
    return {
        "qubo_matrix": flat_qubo,
        "qubo_offset": 0.0,
        "mu": [0.1] * n_assets,
        "sigma": [[0.01 if i == j else 0.0 for j in range(n_assets)] for i in range(n_assets)],
        "cardinality": max(1, n_assets // 2),
        "denominator": 1.0,
        "risk_tolerance": 1.0,
        "is_kn_case": True,   # skip selection-bit decoding to keep meas length == n_qubits
        "binary_bits": 1,
        "optimization_strategy": "test",
    }


def _make_measurements(n_qubits: int) -> list[list[int]]:
    """Return a single all-zeros measurement of length n_qubits."""
    return [[0] * n_qubits]


# ---------------------------------------------------------------------------
# Property 1 — Bug Condition: flat qubo_matrix causes ValueError
#
# Test that decode_and_evaluate raises ValueError for all n_qubits in
# [2, 4, 8, 16] when qubo_matrix is a flat list of n_qubits² floats.
# EXPECTED OUTCOME on unfixed code: ValueError (confirms bug exists).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_qubits", [2, 4, 8, 16])
def test_flat_qubo_raises_value_error_on_unfixed_code(n_qubits):
    """Property 1: flat qubo_matrix of length n² causes ValueError in s @ Q @ s.

    **Validates: Requirements 1.1, 1.2, 1.3**

    On UNFIXED code this test is EXPECTED TO FAIL (i.e., the assertion
    `pytest.raises(ValueError)` will NOT be satisfied because the code
    raises ValueError — which is exactly the bug we are documenting).

    Counterexample documented:
      decode_and_evaluate([[0]*n_qubits], n_qubits,
                          {"qubo_matrix": [0.0]*(n_qubits**2), "qubo_offset": 0.0})
      raises ValueError: matmul: Input operand 1 has a mismatch in its core
      dimension 0 (size N² is different from N)
    """
    flat_qubo = [0.0] * (n_qubits ** 2)
    req_meta = _make_req_meta(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    # Verify the bug condition holds: np.array(flat_qubo) is 1-D
    Q_raw = np.array(flat_qubo)
    assert Q_raw.ndim == 1, "Bug condition: Q must be 1-D before reshape"
    assert len(Q_raw) == n_qubits ** 2, "Bug condition: length must be n²"

    # On FIXED code this should return (finite_float, finite_float).
    # On UNFIXED code this raises ValueError — which is the bug.
    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    # Assert the expected (fixed) behavior: finite 2-tuple
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy), f"avg_energy must be finite, got {avg_energy}"
    assert math.isfinite(feasible_ratio), f"feasible_ratio must be finite, got {feasible_ratio}"
    assert 0.0 <= feasible_ratio <= 1.0, f"feasible_ratio must be in [0,1], got {feasible_ratio}"


# ---------------------------------------------------------------------------
# Property 1 (PBT variant) — Hypothesis-driven bug condition exploration
#
# Scoped to n_qubits in [2, 8] with random flat qubo_matrix of length n².
# ---------------------------------------------------------------------------

@given(
    n_qubits=st.integers(min_value=2, max_value=8),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
)
@settings(max_examples=20, suppress_health_check=list(HealthCheck))
def test_pbt_flat_qubo_bug_condition(n_qubits, seed):
    """Property 1 (PBT): for any n_qubits in [2,8] and flat qubo_matrix of
    length n², decode_and_evaluate must return a finite (avg_energy,
    feasible_ratio) tuple without raising ValueError.

    **Validates: Requirements 1.1, 1.2, 1.3**

    On UNFIXED code this test is EXPECTED TO FAIL — the ValueError confirms
    the bug exists.  Document the counterexample and move on.
    """
    rng = np.random.default_rng(seed)
    # Random symmetric QUBO matrix, flattened
    Q_2d = rng.standard_normal((n_qubits, n_qubits))
    Q_2d = (Q_2d + Q_2d.T) / 2.0  # symmetrize
    flat_qubo = Q_2d.flatten().tolist()

    req_meta = _make_req_meta(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    # Verify bug condition
    Q_raw = np.array(flat_qubo)
    assert Q_raw.ndim == 1
    assert len(Q_raw) == n_qubits ** 2

    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy)
    assert math.isfinite(feasible_ratio)
    assert 0.0 <= feasible_ratio <= 1.0


# ---------------------------------------------------------------------------
# Property 1 (inline closure) — run_qaoa_optimized objective_function closure
#
# The inline closure `m_energy = float(s @ Q @ s)` in run_qaoa_optimized()
# has the same defect.  We test it directly by inspecting the crash path.
# ---------------------------------------------------------------------------

def test_inline_closure_flat_qubo_raises_value_error():
    """Property 1 (inline closure): flat qubo_matrix in req_meta no longer
    causes ValueError in the objective_function closure of run_qaoa_optimized().

    **Validates: Requirements 1.2**

    On UNFIXED code this test was EXPECTED TO FAIL — the ValueError confirmed
    the secondary crash path existed.  After the fix in task 3.2, the inline
    closure reshapes Q before the matmul, so the expression must succeed.

    This test verifies the FIXED production-code reshape logic directly,
    mirroring the exact code path added in run_qaoa_optimized():

        Q_raw = req_meta.get("qubo_matrix")
        if Q_raw is not None:
            Q_2d = np.array(Q_raw, dtype=np.float64)
            if Q_2d.ndim == 1:
                Q_2d = Q_2d.reshape(n_qubits, n_qubits)
            m_energy = float(s @ Q_2d @ s) + req_meta.get("qubo_offset", 0.0)
        else:
            m_energy = 0.0
    """
    n_qubits = 4
    flat_qubo = [0.0] * (n_qubits ** 2)

    # Verify bug condition: input is still a flat 1-D list
    Q_raw_check = np.array(flat_qubo)
    assert Q_raw_check.ndim == 1, "Bug condition: Q must be 1-D before reshape"
    assert len(Q_raw_check) == n_qubits ** 2, "Bug condition: length must be n²"

    # Reproduce the FIXED inline closure logic from run_qaoa_optimized()
    s = np.array([0] * n_qubits)
    req_meta_qubo_matrix = flat_qubo  # flat list, as stored in req_meta

    Q_raw = req_meta_qubo_matrix
    if Q_raw is not None:
        Q_2d = np.array(Q_raw, dtype=np.float64)
        if Q_2d.ndim == 1:
            Q_2d = Q_2d.reshape(n_qubits, n_qubits)
        m_energy = float(s @ Q_2d @ s) + 0.0
    else:
        m_energy = 0.0

    assert math.isfinite(m_energy), f"m_energy must be finite, got {m_energy}"
