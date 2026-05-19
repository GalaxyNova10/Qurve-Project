"""Task 3.6 — Verify `qaoa_circuit.py` decode layer symmetry check passes.

**Validates: Requirements 2.8, 3.5**

This test file documents and verifies the symmetry check at Step 4 of
`decode_and_evaluate()` in `qaoa_circuit.py` (~lines 155–162):

    # ── Step 4: Symmetry check ───────────────────────────────
    is_symmetric = bool(np.allclose(Q_2d, Q_2d.T, atol=1e-9))
    if not is_symmetric:
        raise RuntimeError(
            f"QUBO_SYMMETRY_CORRUPTION: QUBO matrix is not symmetric "
            f"(max asymmetry={float(np.max(np.abs(Q_2d - Q_2d.T))):.6e})"
        )

DESIGN INTENT (intentionally preserved as a downstream safety net):
  The symmetry check in `decode_and_evaluate()` is a downstream safety net
  that must NOT be removed during future refactoring. It provides a second
  layer of protection: even if the upstream `to_qubo_matrix()` guard or the
  `braket_integration.py` pre-serialization guard were accidentally removed,
  this check would still catch any asymmetric matrix before energy evaluation.

  After the upstream fix in `to_qubo_matrix()` (task 3.2), this check passes
  silently for all correctly constructed matrices. Its presence is verified
  by the test `test_asymmetric_matrix_still_raises()` below — if the check
  were removed, that test would fail, alerting developers immediately.

NO CODE CHANGES were made to `qaoa_circuit.py` for this task.
"""

import math
import numpy as np
import pytest

# Import the function under test — no changes to this module
from qaoa_circuit import decode_and_evaluate


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_req_meta_flat(n_qubits: int, flat_qubo: list, offset: float = 0.0) -> dict:
    """Build a minimal req_meta dict with a flat qubo_matrix list."""
    n_assets = n_qubits
    return {
        "qubo_matrix": flat_qubo,
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


def _make_req_meta_2d(n_qubits: int, Q_2d: list, offset: float = 0.0) -> dict:
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


def _make_measurements(n_qubits: int, bits: list | None = None) -> list[list[int]]:
    """Return a single measurement of length n_qubits."""
    if bits is None:
        bits = [0] * n_qubits
    return [bits]


def _make_symmetric_flat(n: int, seed: int = 42) -> list:
    """Generate a random symmetric (n, n) QUBO matrix and return as flat list."""
    rng = np.random.default_rng(seed)
    A = rng.standard_normal((n, n))
    Q_sym = (A + A.T) / 2.0
    return Q_sym.flatten().tolist()


def _make_asymmetric_flat(n: int, seed: int = 42) -> list:
    """Generate a structurally asymmetric (n, n) matrix and return as flat list.

    Simulates the pre-fix bug: off-diagonal term written to upper triangle only.
    For a 2x2 matrix: Q[0,1] = 1.0, Q[1,0] = 0.0 → max_asymmetry = 1.0.
    """
    Q = np.zeros((n, n))
    # Write diagonal (always symmetric)
    for i in range(n):
        Q[i, i] = float(i + 1)
    # Write off-diagonal to upper triangle only (bug condition)
    if n >= 2:
        Q[0, 1] = 1.0   # Q[1,0] remains 0.0 → asymmetric
    if n >= 3:
        Q[0, 2] = 0.5   # Q[2,0] remains 0.0 → asymmetric
    if n >= 4:
        Q[1, 2] = 0.75  # Q[2,1] remains 0.0 → asymmetric
    return Q.flatten().tolist()


# ---------------------------------------------------------------------------
# Test 1: Confirm the symmetry check is present and intact
#
# This test verifies the check raises RuntimeError("QUBO_SYMMETRY_CORRUPTION")
# for an asymmetric matrix. If the check were removed, this test would fail,
# alerting developers that the downstream safety net has been broken.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_qubits", [2, 4, 8])
def test_asymmetric_matrix_still_raises(n_qubits):
    """The symmetry check at Step 4 is present and raises QUBO_SYMMETRY_CORRUPTION
    for an asymmetric matrix.

    **Validates: Requirements 2.8, 3.5**

    This test confirms the downstream safety net is intact. If the check were
    accidentally removed during refactoring, this test would fail immediately.

    The asymmetric matrix simulates the pre-fix bug condition:
      Q[i,j] != 0 but Q[j,i] == 0 for off-diagonal terms.
    """
    flat_qubo = _make_asymmetric_flat(n_qubits)
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    # Verify the input is genuinely asymmetric
    Q_check = np.array(flat_qubo).reshape(n_qubits, n_qubits)
    max_asym = float(np.max(np.abs(Q_check - Q_check.T)))
    assert max_asym > 1e-9, (
        f"Test setup error: matrix should be asymmetric, got max_asymmetry={max_asym}"
    )

    # The symmetry check at Step 4 must raise RuntimeError
    with pytest.raises(RuntimeError, match="QUBO_SYMMETRY_CORRUPTION"):
        decode_and_evaluate(measurements, n_qubits, req_meta)


# ---------------------------------------------------------------------------
# Test 2: Symmetric matrix passes the check without raising
#
# This is the primary verification for task 3.6: after the upstream fix,
# the downstream symmetry check passes silently for all correctly constructed
# matrices. No QUBO_SYMMETRY_CORRUPTION exception is raised.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_qubits", [2, 4, 8])
def test_symmetric_matrix_does_not_raise(n_qubits):
    """The symmetry check at Step 4 passes silently for a symmetric matrix.

    **Validates: Requirements 2.8, 3.5**

    This is the primary verification for task 3.6: after the upstream fix in
    `to_qubo_matrix()`, the QUBO matrix is correctly symmetric, so the
    downstream check in `decode_and_evaluate()` passes without raising.

    The symmetric matrix here represents the output of the fixed
    `to_qubo_matrix()` — a matrix satisfying np.allclose(Q, Q.T, atol=1e-9).
    """
    flat_qubo = _make_symmetric_flat(n_qubits)
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    # Verify the input is genuinely symmetric
    Q_check = np.array(flat_qubo).reshape(n_qubits, n_qubits)
    assert np.allclose(Q_check, Q_check.T, atol=1e-9), (
        f"Test setup error: matrix should be symmetric, "
        f"max_asymmetry={float(np.max(np.abs(Q_check - Q_check.T))):.6e}"
    )

    # Must NOT raise QUBO_SYMMETRY_CORRUPTION
    result = decode_and_evaluate(measurements, n_qubits, req_meta)

    assert isinstance(result, tuple), f"Expected tuple, got {type(result)}"
    assert len(result) == 2, f"Expected 2-tuple, got length {len(result)}"
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy), f"avg_energy must be finite, got {avg_energy}"
    assert math.isfinite(feasible_ratio), f"feasible_ratio must be finite, got {feasible_ratio}"
    assert 0.0 <= feasible_ratio <= 1.0, f"feasible_ratio must be in [0,1], got {feasible_ratio}"


# ---------------------------------------------------------------------------
# Test 3: Known symmetric matrix — exact energy value
#
# Verifies that a symmetric matrix with a known analytical result produces
# the correct energy, confirming the check passes AND energy is computed
# correctly.
# ---------------------------------------------------------------------------

def test_symmetric_matrix_known_energy():
    """Symmetric matrix passes the check and produces the correct energy.

    **Validates: Requirements 2.8, 3.5**

    For Q = [[1, 0.5], [0.5, 2]], s = [1, 1], offset = 0:
      energy = s.T @ Q @ s = 1*1 + 1*0.5 + 0.5*1 + 1*2 = 4.0

    This matrix is symmetric: Q[0,1] == Q[1,0] == 0.5.
    np.allclose(Q, Q.T, atol=1e-9) returns True → no exception raised.
    """
    n_qubits = 2
    # Symmetric matrix: Q[0,1] == Q[1,0] == 0.5
    Q_sym = np.array([[1.0, 0.5], [0.5, 2.0]])
    assert np.allclose(Q_sym, Q_sym.T, atol=1e-9), "Test matrix must be symmetric"

    flat_qubo = Q_sym.flatten().tolist()
    bits = [1, 1]
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo, offset=0.0)
    measurements = [bits]

    # Must not raise
    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    avg_energy, _ = result

    # s = [1,1], Q = [[1,0.5],[0.5,2]], energy = 1+0.5+0.5+2 = 4.0
    expected = float(np.array([1.0, 1.0]) @ Q_sym @ np.array([1.0, 1.0]))
    assert abs(avg_energy - expected) < 1e-9, (
        f"Expected energy {expected}, got {avg_energy}"
    )


# ---------------------------------------------------------------------------
# Test 4: Half-value symmetric matrix from fixed to_qubo_matrix()
#
# Simulates the exact output of the fixed to_qubo_matrix() using
# Convention B (half-value dual-write): for a cross-term bias=1.0,
# Q[0,1] = 0.5 and Q[1,0] = 0.5.
# Verifies the check passes and energy is correct.
# ---------------------------------------------------------------------------

def test_half_value_symmetric_matrix_from_fixed_upstream():
    """Symmetric matrix from fixed to_qubo_matrix() (Convention B) passes check.

    **Validates: Requirements 2.8, 3.5**

    The fixed to_qubo_matrix() uses Convention B (half-value dual-write):
      add_symmetric_quadratic(Q, 0, 1, 1.0) writes Q[0,1] = 0.5, Q[1,0] = 0.5

    For a 2-variable model with one cross-term bias=1.0 and s=[1,1]:
      energy = s.T @ Q_sym @ s = 0.5 + 0.5 = 1.0  (not 2.0 — no double-count)

    This test verifies:
      1. The symmetry check passes (Q[0,1] == Q[1,0] == 0.5)
      2. The energy is 1.0 (Convention B preserves energy vs. upper-triangular)
      3. No QUBO_SYMMETRY_CORRUPTION is raised
    """
    n_qubits = 2
    # Simulate fixed to_qubo_matrix() output for a 2-var model with bias=1.0
    # Linear terms: Q[0,0] = 0.1, Q[1,1] = 0.2 (arbitrary)
    # Quadratic term (0,1) with bias=1.0 → Convention B: Q[0,1]=0.5, Q[1,0]=0.5
    Q_fixed = np.array([
        [0.1, 0.5],
        [0.5, 0.2],
    ])
    assert np.allclose(Q_fixed, Q_fixed.T, atol=1e-9), (
        "Test matrix must be symmetric (Convention B output)"
    )

    flat_qubo = Q_fixed.flatten().tolist()
    bits = [1, 1]
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo, offset=0.0)
    measurements = [bits]

    # Must not raise QUBO_SYMMETRY_CORRUPTION
    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    avg_energy, _ = result

    # s = [1,1], energy = 0.1 + 0.5 + 0.5 + 0.2 = 1.3
    s = np.array([1.0, 1.0])
    expected = float(s @ Q_fixed @ s)
    assert abs(avg_energy - expected) < 1e-9, (
        f"Expected energy {expected}, got {avg_energy}"
    )


# ---------------------------------------------------------------------------
# Test 5: 2-D list-of-lists symmetric matrix also passes the check
#
# Verifies that a symmetric matrix passed as a 2-D list-of-lists (not flat)
# also passes the Step 4 symmetry check. This covers the alternative input
# path (Step 1 in decode_and_evaluate).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_qubits", [2, 4])
def test_2d_symmetric_matrix_does_not_raise(n_qubits):
    """2-D list-of-lists symmetric matrix passes the Step 4 symmetry check.

    **Validates: Requirements 2.8, 3.5**

    When qubo_matrix is already a 2-D list-of-lists, decode_and_evaluate()
    takes the Step 1 path (no reshape needed). The Step 4 symmetry check
    still applies and must pass for a symmetric matrix.
    """
    rng = np.random.default_rng(99 + n_qubits)
    A = rng.standard_normal((n_qubits, n_qubits))
    Q_sym = (A + A.T) / 2.0
    assert np.allclose(Q_sym, Q_sym.T, atol=1e-9)

    Q_2d_list = Q_sym.tolist()
    req_meta = _make_req_meta_2d(n_qubits, Q_2d_list)
    measurements = _make_measurements(n_qubits)

    # Must not raise
    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    assert isinstance(result, tuple)
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy)
    assert 0.0 <= feasible_ratio <= 1.0


# ---------------------------------------------------------------------------
# Test 6: Diagonal-only matrix (trivially symmetric) passes the check
#
# A diagonal matrix is always symmetric. Verifies the check passes for
# the simplest possible case.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("n_qubits", [2, 4, 8])
def test_diagonal_matrix_passes_symmetry_check(n_qubits):
    """Diagonal matrix (trivially symmetric) passes the Step 4 symmetry check.

    **Validates: Requirements 2.8, 3.5**

    A diagonal matrix satisfies Q == Q.T exactly. This is the simplest
    symmetric case and must pass the check without raising.
    """
    # Diagonal matrix: Q[i,i] = i+1, all off-diagonal = 0
    Q_diag = np.diag([float(i + 1) for i in range(n_qubits)])
    assert np.allclose(Q_diag, Q_diag.T, atol=1e-9)

    flat_qubo = Q_diag.flatten().tolist()
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    # Must not raise
    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    assert isinstance(result, tuple)
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy)
    assert 0.0 <= feasible_ratio <= 1.0


# ---------------------------------------------------------------------------
# Test 7: Near-symmetric matrix (floating-point noise) passes the check
#
# A matrix with max_asymmetry < 1e-9 (floating-point noise level) must
# pass the check. This verifies the atol=1e-9 tolerance is respected.
# ---------------------------------------------------------------------------

def test_near_symmetric_matrix_within_tolerance_passes():
    """Matrix with max_asymmetry < 1e-9 passes the Step 4 symmetry check.

    **Validates: Requirements 2.8, 3.5**

    The check uses atol=1e-9. A matrix with max_asymmetry = 1e-12 (well
    within tolerance) must pass without raising.
    """
    n_qubits = 4
    rng = np.random.default_rng(7)
    A = rng.standard_normal((n_qubits, n_qubits))
    Q_sym = (A + A.T) / 2.0

    # Introduce tiny floating-point noise (well within atol=1e-9)
    noise = np.zeros((n_qubits, n_qubits))
    noise[0, 1] = 1e-12
    noise[1, 0] = -1e-12
    Q_noisy = Q_sym + noise

    max_asym = float(np.max(np.abs(Q_noisy - Q_noisy.T)))
    assert max_asym < 1e-9, f"Test setup: max_asymmetry={max_asym} should be < 1e-9"

    flat_qubo = Q_noisy.flatten().tolist()
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    # Must not raise (noise is within atol=1e-9)
    result = decode_and_evaluate(measurements, n_qubits, req_meta)
    assert isinstance(result, tuple)
    avg_energy, feasible_ratio = result
    assert math.isfinite(avg_energy)
    assert 0.0 <= feasible_ratio <= 1.0


# ---------------------------------------------------------------------------
# Test 8: Structurally asymmetric matrix (large asymmetry) raises the check
#
# A matrix with large structural asymmetry (e.g., max_asymmetry = 1.0,
# simulating the pre-fix bug) must raise QUBO_SYMMETRY_CORRUPTION.
# This verifies the threshold is enforced for the actual bug scenario.
#
# Note: np.allclose(Q, Q.T, atol=1e-9) uses rtol=1e-5 by default, so
# tiny asymmetries (e.g., 1e-8) may pass when matrix values are O(1).
# The relevant test case is the structural asymmetry from the pre-fix bug
# (max_asymmetry == full coefficient magnitude, e.g., 1.0 or 558.0).
# ---------------------------------------------------------------------------

def test_structurally_asymmetric_matrix_raises():
    """Structurally asymmetric matrix (pre-fix bug pattern) raises QUBO_SYMMETRY_CORRUPTION.

    **Validates: Requirements 2.8, 3.5**

    The pre-fix bug produces max_asymmetry equal to the full coefficient
    magnitude (e.g., 1.0 for a cross-term with bias=1.0, or ~558 for the
    cardinality penalty). This test uses a 4x4 matrix with Q[0,1]=1.0 and
    Q[1,0]=0.0 — the exact pattern produced by the unfixed to_qubo_matrix().

    np.allclose([[0,1,0,0],[0,0,0,0],...], [[0,0,0,0],[1,0,0,0],...], atol=1e-9)
    returns False because |1.0 - 0.0| = 1.0 >> atol=1e-9 and rtol*|0.0| = 0.
    """
    n_qubits = 4
    # Simulate pre-fix bug: diagonal only + upper-triangle write for (0,1)
    Q_buggy = np.zeros((n_qubits, n_qubits))
    for i in range(n_qubits):
        Q_buggy[i, i] = float(i + 1)
    Q_buggy[0, 1] = 1.0   # upper triangle only — Q[1,0] remains 0.0

    max_asym = float(np.max(np.abs(Q_buggy - Q_buggy.T)))
    assert max_asym >= 1.0, f"Test setup: max_asymmetry={max_asym} should be >= 1.0"
    # Confirm np.allclose returns False for this structural asymmetry
    assert not np.allclose(Q_buggy, Q_buggy.T, atol=1e-9), (
        "Test setup: np.allclose should return False for structural asymmetry"
    )

    flat_qubo = Q_buggy.flatten().tolist()
    req_meta = _make_req_meta_flat(n_qubits, flat_qubo)
    measurements = _make_measurements(n_qubits)

    with pytest.raises(RuntimeError, match="QUBO_SYMMETRY_CORRUPTION"):
        decode_and_evaluate(measurements, n_qubits, req_meta)
