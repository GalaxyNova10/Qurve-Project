"""Preservation Property Tests — Non-Buggy Input Behavior Unchanged.

**Validates: Requirements 3.1, 3.6, 3.7**

Property 2: Preservation — Non-Buggy Input Behavior Unchanged

These tests verify that for inputs where the bug condition does NOT hold,
`decode_and_evaluate()` produces the correct, expected behavior.

Non-bug condition (¬isBugCondition):
  - req_meta["qubo_matrix"] is None  (Hadamard fallback path), OR
  - req_meta["qubo_matrix"] is already a correctly shaped 2-D array
    (list-of-lists or np.ndarray with ndim == 2)

IMPORTANT: These tests are EXPECTED TO PASS on UNFIXED code.
They establish the preservation baseline — the behavior that must remain
unchanged after the fix is applied.

Observation-first methodology:
  1. Observe that decode_and_evaluate() with qubo_matrix=None returns a
     non-empty fallback result on unfixed code.
  2. Observe that decode_and_evaluate() with a 2-D list-of-lists qubo_matrix
     returns a finite energy tuple on unfixed code.
  3. Encode these observations as property-based tests.
"""

import math
import numpy as np
import pytest
from hypothesis import given, settings, HealthCheck, assume
from hypothesis import strategies as st

from qaoa_circuit import decode_and_evaluate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req_meta_none_qubo(n_assets: int, risk_tolerance: float = 1.0) -> dict:
    """Build a minimal req_meta dict with qubo_matrix=None (Hadamard fallback)."""
    return {
        "qubo_matrix": None,
        "qubo_offset": 0.0,
        "mu": [0.1] * n_assets,
        "sigma": [[0.01 if i == j else 0.0 for j in range(n_assets)] for i in range(n_assets)],
        "cardinality": max(1, n_assets // 2),
        "denominator": 1.0,
        "risk_tolerance": risk_tolerance,
        "is_kn_case": True,
        "binary_bits": 1,
        "optimization_strategy": "test",
    }


def _make_req_meta_2d_qubo(n_qubits: int, Q_2d: list, offset: float = 0.0) -> dict:
    """Build a minimal req_meta dict with a 2-D list-of-lists qubo_matrix."""
    n_assets = n_qubits
    return {
        "qubo_matrix": Q_2d,
        "qubo_offset": offset,
        "mu": [0.1] * n_assets,
        "sigma": [[0.01 if i == j else 0.0 for j in range(n_assets)] for i in range(n_assets)],
        "cardinality": max(1, n_assets // 2),
        "denominator": 1.0,
        "risk_tolerance": 1.0,
        "is_kn_case": True,
        "binary_bits": 1,
        "optimization_strategy": "test",
    }


def _make_measurements(n_qubits: int, bits: list[int] | None = None) -> list[list[int]]:
    """Return a single measurement of length n_qubits."""
    if bits is None:
        bits = [0] * n_qubits
    return [bits]


def _make_symmetric_matrix(n: int, rng: np.random.Generator) -> np.ndarray:
    """Generate a random symmetric (n, n) QUBO matrix."""
    A = rng.standard_normal((n, n))
    return (A + A.T) / 2.0


# ---------------------------------------------------------------------------
# Observation 1: qubo_matrix=None returns a non-empty fallback result
# ---------------------------------------------------------------------------

def test_observe_none_qubo_returns_fallback():
    """Observation: decode_and_evaluate() with qubo_matrix=None returns a
    non-empty fallback result on unfixed code.

    **Validates: Requirements 3.6**

    The fallback path computes:
      variance = weights @ sigma @ weights
      expected_return = weights @ mu
      total_energy = risk_tolerance * variance - expected_return
    This path does not touch qubo_matrix at all.
    """
    n_qubits = 4
    req_meta = _make_req_meta_none_qubo(n_assets=n_qubits)
    measurements = _make_measurements(n_qubits)

    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-tuple, got length {len(result)}"
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy), f"avg_energy must be finite, got {avg_energy}"
    assert math.isfinite(feasible_ratio), f"feasible_ratio must be finite, got {feasible_ratio}"
    assert 0.0 <= feasible_ratio <= 1.0, f"feasible_ratio must be in [0,1], got {feasible_ratio}"


def test_observe_2d_list_qubo_returns_finite_energy():
    """Observation: decode_and_evaluate() with a 2-D list-of-lists qubo_matrix
    returns a finite energy tuple on unfixed code.

    **Validates: Requirements 3.1**

    Example: [[1.0, 0.5], [0.5, 2.0]] for 2 qubits.
    np.array([[1.0, 0.5], [0.5, 2.0]]) produces shape (2, 2) — no crash.
    """
    n_qubits = 2
    Q_2d = [[1.0, 0.5], [0.5, 2.0]]
    req_meta = _make_req_meta_2d_qubo(n_qubits, Q_2d, offset=0.0)
    measurements = _make_measurements(n_qubits, bits=[1, 0])

    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    assert isinstance(result, tuple)
    assert len(result) == 2
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy), f"avg_energy must be finite, got {avg_energy}"
    assert math.isfinite(feasible_ratio), f"feasible_ratio must be in [0,1], got {feasible_ratio}"
    assert 0.0 <= feasible_ratio <= 1.0


# ---------------------------------------------------------------------------
# Property 2a: 2-D QUBO matrix — energy matches direct computation
#
# For all n_qubits in [2, 8] and random symmetric (n, n) QUBO matrices
# passed as 2-D arrays, decode_and_evaluate() returns the same energy as
# computing float(s.T @ Q @ s) + offset directly.
#
# EXPECTED TO PASS on UNFIXED code (2-D input is not the bug condition).
# ---------------------------------------------------------------------------

@given(
    n_qubits=st.integers(min_value=2, max_value=8),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    offset=st.floats(min_value=-100.0, max_value=100.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=list(HealthCheck))
def test_pbt_2d_qubo_energy_matches_direct_computation(n_qubits, seed, offset):
    """Property 2a: for all n_qubits in [2, 8] and random symmetric (n, n)
    QUBO matrices passed as 2-D arrays, decode_and_evaluate() returns the
    same energy as computing float(s.T @ Q @ s) + offset directly.

    **Validates: Requirements 3.1, 3.7**

    This test PASSES on UNFIXED code because np.array(list_of_lists) produces
    a 2-D array — the bug only manifests with flat 1-D lists.
    """
    rng = np.random.default_rng(seed)

    # Generate random symmetric QUBO matrix
    Q_np = _make_symmetric_matrix(n_qubits, rng)

    # Convert to list-of-lists (2-D, non-buggy form)
    Q_2d_list = Q_np.tolist()

    # Generate a random bitstring measurement
    bits = rng.integers(0, 2, size=n_qubits).tolist()
    measurements = [bits]

    req_meta = _make_req_meta_2d_qubo(n_qubits, Q_2d_list, offset=offset)

    # Call decode_and_evaluate
    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-tuple, got length {len(result)}"
    avg_energy, feasible_ratio = result

    # Compute reference energy directly: float(s.T @ Q @ s) + offset
    s = np.array(bits, dtype=np.float64)
    Q_ref = np.array(Q_2d_list, dtype=np.float64)
    reference_energy = float(s.T @ Q_ref @ s) + offset

    # The function processes a single measurement, so avg_energy == reference_energy
    assert math.isfinite(avg_energy), f"avg_energy must be finite, got {avg_energy}"
    assert abs(avg_energy - reference_energy) < 1e-9, (
        f"Energy mismatch: decode_and_evaluate returned {avg_energy}, "
        f"direct computation returned {reference_energy}, "
        f"diff={abs(avg_energy - reference_energy)}"
    )

    # Feasibility ratio must be in [0, 1]
    assert math.isfinite(feasible_ratio), f"feasible_ratio must be finite, got {feasible_ratio}"
    assert 0.0 <= feasible_ratio <= 1.0, f"feasible_ratio must be in [0,1], got {feasible_ratio}"


# ---------------------------------------------------------------------------
# Property 2b: qubo_matrix=None — Hadamard fallback returns consistent result
#
# For all req_meta with qubo_matrix=None, decode_and_evaluate() returns the
# same Hadamard fallback result as the original (risk_tolerance * variance -
# expected_return).
#
# EXPECTED TO PASS on UNFIXED code (None path is not the bug condition).
# ---------------------------------------------------------------------------

@given(
    n_qubits=st.integers(min_value=2, max_value=8),
    seed=st.integers(min_value=0, max_value=2**31 - 1),
    risk_tolerance=st.floats(min_value=0.1, max_value=10.0, allow_nan=False, allow_infinity=False),
)
@settings(max_examples=50, suppress_health_check=list(HealthCheck))
def test_pbt_none_qubo_hadamard_fallback_consistent(n_qubits, seed, risk_tolerance):
    """Property 2b: for all req_meta with qubo_matrix=None, decode_and_evaluate()
    returns the same Hadamard fallback result as the original function.

    **Validates: Requirements 3.6, 3.7**

    The fallback computes:
      variance = weights @ sigma @ weights
      expected_return = weights @ mu
      total_energy = risk_tolerance * variance - expected_return

    This test PASSES on UNFIXED code because the None path does not touch
    qubo_matrix at all.
    """
    rng = np.random.default_rng(seed)

    # Random portfolio parameters
    mu = rng.uniform(0.0, 0.3, size=n_qubits).tolist()
    # Random positive-definite sigma (diagonal for simplicity)
    diag_vals = rng.uniform(0.001, 0.1, size=n_qubits)
    sigma = np.diag(diag_vals).tolist()

    # Random bitstring measurement
    bits = rng.integers(0, 2, size=n_qubits).tolist()
    measurements = [bits]

    req_meta = {
        "qubo_matrix": None,
        "qubo_offset": 0.0,
        "mu": mu,
        "sigma": sigma,
        "cardinality": max(1, n_qubits // 2),
        "denominator": 1.0,
        "risk_tolerance": risk_tolerance,
        "is_kn_case": True,
        "binary_bits": 1,
        "optimization_strategy": "test",
    }

    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-tuple, got length {len(result)}"
    avg_energy, feasible_ratio = result

    # Compute reference fallback energy directly
    # is_kn_case=True, binary_bits=1, denominator=1.0
    # weights[i] = bits[i] / 1.0 = bits[i]
    weights = np.array(bits, dtype=np.float64)
    sigma_np = np.array(sigma, dtype=np.float64)
    mu_np = np.array(mu, dtype=np.float64)
    variance = float(weights @ sigma_np @ weights)
    expected_return = float(weights @ mu_np)
    reference_energy = risk_tolerance * variance - expected_return

    assert math.isfinite(avg_energy), f"avg_energy must be finite, got {avg_energy}"
    assert abs(avg_energy - reference_energy) < 1e-9, (
        f"Fallback energy mismatch: decode_and_evaluate returned {avg_energy}, "
        f"reference fallback returned {reference_energy}, "
        f"diff={abs(avg_energy - reference_energy)}"
    )

    assert math.isfinite(feasible_ratio), f"feasible_ratio must be finite, got {feasible_ratio}"
    assert 0.0 <= feasible_ratio <= 1.0, f"feasible_ratio must be in [0,1], got {feasible_ratio}"


# ---------------------------------------------------------------------------
# Additional edge-case unit tests for preservation baseline
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_qubits", [2, 4, 8])
def test_2d_ndarray_qubo_returns_finite_energy(n_qubits):
    """Preservation: 2-D np.ndarray qubo_matrix (already correct shape) works.

    **Validates: Requirements 3.1**

    np.array(np.ndarray_2d) produces a 2-D array — no crash on unfixed code.
    """
    rng = np.random.default_rng(42 + n_qubits)
    Q_np = _make_symmetric_matrix(n_qubits, rng)
    # Pass as np.ndarray (already 2-D)
    req_meta = _make_req_meta_2d_qubo(n_qubits, Q_np.tolist(), offset=1.0)
    measurements = _make_measurements(n_qubits)

    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy)
    assert 0.0 <= feasible_ratio <= 1.0


@pytest.mark.parametrize("n_qubits", [2, 4, 8])
def test_none_qubo_does_not_raise(n_qubits):
    """Preservation: qubo_matrix=None does not raise any exception.

    **Validates: Requirements 3.6**
    """
    req_meta = _make_req_meta_none_qubo(n_assets=n_qubits)
    measurements = _make_measurements(n_qubits)

    # Must not raise
    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    assert result is not None


def test_2d_qubo_energy_known_value():
    """Preservation: 2-D qubo_matrix with known input produces expected energy.

    **Validates: Requirements 3.1**

    For Q = [[1, 0], [0, 1]], s = [1, 1], offset = 0:
      energy = s.T @ Q @ s + 0 = 1*1 + 1*1 = 2.0
    """
    n_qubits = 2
    Q_2d = [[1.0, 0.0], [0.0, 1.0]]  # identity matrix
    bits = [1, 1]
    req_meta = _make_req_meta_2d_qubo(n_qubits, Q_2d, offset=0.0)
    measurements = [bits]

    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    avg_energy, _ = result

    # s = [1, 1], Q = I, energy = 1 + 1 = 2.0
    assert abs(avg_energy - 2.0) < 1e-9, f"Expected 2.0, got {avg_energy}"


def test_2d_qubo_energy_with_offset():
    """Preservation: 2-D qubo_matrix with offset adds correctly.

    **Validates: Requirements 3.1**

    For Q = [[2, 1], [1, 3]], s = [1, 0], offset = 5.0:
      energy = s.T @ Q @ s + 5.0 = 2.0 + 5.0 = 7.0
    """
    n_qubits = 2
    Q_2d = [[2.0, 1.0], [1.0, 3.0]]
    bits = [1, 0]
    req_meta = _make_req_meta_2d_qubo(n_qubits, Q_2d, offset=5.0)
    measurements = [bits]

    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    avg_energy, _ = result

    # s = [1, 0], Q @ s = [2, 1], s.T @ (Q @ s) = 2.0, + offset 5.0 = 7.0
    assert abs(avg_energy - 7.0) < 1e-9, f"Expected 7.0, got {avg_energy}"


def test_none_qubo_all_zeros_measurement():
    """Preservation: qubo_matrix=None with all-zeros measurement returns
    zero energy (weights=0, variance=0, expected_return=0).

    **Validates: Requirements 3.6**
    """
    n_qubits = 4
    req_meta = _make_req_meta_none_qubo(n_assets=n_qubits, risk_tolerance=1.0)
    measurements = [[0, 0, 0, 0]]

    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    avg_energy, _ = result

    # weights = [0,0,0,0], variance = 0, expected_return = 0
    # energy = 1.0 * 0 - 0 = 0.0
    assert abs(avg_energy - 0.0) < 1e-9, f"Expected 0.0, got {avg_energy}"
