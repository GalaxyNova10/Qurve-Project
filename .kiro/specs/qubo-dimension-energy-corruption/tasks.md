# Implementation Plan

## Overview

This plan follows the exploratory bugfix workflow for the QUBO dimension/energy corruption bug. The QUBO matrix is serialized as a flat list of `n²` floats but `decode_and_evaluate()` in `qaoa_circuit.py` never reshapes it before the `s @ Q @ s` matmul, causing a `ValueError` crash. The fix adds a reshape-and-validate sequence in the decode layer without altering any quantum circuit, serialization format, or upstream behavior.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - QUBO Flat List Dimension Mismatch Crash
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate the `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0` crash
  - **Scoped PBT Approach**: Scope the property to concrete failing cases — `n_qubits` in [2, 8] with a flat `qubo_matrix` of length `n_qubits²` in `req_meta`
  - Bug Condition (`isBugCondition`): `req_meta["qubo_matrix"]` is a flat list of `n_qubits²` floats AND `np.array(Q).ndim == 1` AND `len(np.array(Q)) == n_qubits ** 2` AND no reshape has been performed before `s @ Q @ s`
  - Test that `decode_and_evaluate([[0]*n_qubits], n_qubits, {"qubo_matrix": [0.0]*(n_qubits**2), "qubo_offset": 0.0})` raises `ValueError` on unfixed code for all `n_qubits` in [2, 4, 8, 16]
  - Also test the inline closure in `run_qaoa_optimized()` with a flat `qubo_matrix` in `req_meta` — same crash path
  - Run test on UNFIXED code
  - **EXPECTED OUTCOME**: Test FAILS with `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 (size N² is different from N)` — this is correct and proves the bug exists
  - Document counterexamples found (e.g., `decode_and_evaluate([[0]*16], 16, {"qubo_matrix": [0.0]*256})` raises `ValueError`)
  - Mark task complete when test is written, run, and failure is documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Non-Buggy Input Behavior Unchanged
  - **IMPORTANT**: Follow observation-first methodology
  - Non-bug condition (`¬isBugCondition`): `req_meta["qubo_matrix"]` is either `None` (Hadamard fallback) OR already a correctly shaped 2-D array (list-of-lists or `np.ndarray` with `ndim == 2`)
  - Observe: `decode_and_evaluate()` with `qubo_matrix=None` returns a non-empty fallback result on unfixed code
  - Observe: `decode_and_evaluate()` with a 2-D list-of-lists `qubo_matrix` (e.g., `[[1.0, 0.5], [0.5, 2.0]]` for 2 qubits) returns a finite energy tuple on unfixed code
  - Write property-based test: for all `n_qubits` in [2, 8] and random symmetric `(n, n)` QUBO matrices passed as 2-D arrays, the fixed function returns the same energy as computing `float(s.T @ Q @ s) + offset` directly
  - Write property-based test: for all `req_meta` with `qubo_matrix=None`, the fixed function returns the same Hadamard fallback result as the original
  - Verify tests PASS on UNFIXED code (confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.6, 3.7_

- [x] 3. Fix QUBO dimension corruption in decode and evaluate layer

  - [x] 3.1 Add reshape and validation sequence to `decode_and_evaluate()` in `qubo-braket-worker/qaoa_circuit.py`
    - Step 0 — Offset validation: retrieve `offset = req_meta.get("qubo_offset", 0.0)`; verify `isinstance(offset, (int, float, np.floating))`; if not, raise `RuntimeError("QUBO_OFFSET_CORRUPTION: offset is not a numeric type")`; then verify `math.isfinite(offset)`; if not, raise `RuntimeError("QUBO_OFFSET_CORRUPTION: offset is not finite")`
    - Step 1 — Before reshape, check if Q is already 2-D (`isinstance(Q, np.ndarray) and Q.ndim == 2` or `isinstance(Q, list) and isinstance(Q[0], list)`); if so, convert with `Q_2d = np.array(Q, dtype=np.float64)` and skip Steps 2–3
    - Step 2 — Serialization length check: verify `len(flat_qubo) == n_qubits * n_qubits`; if not, raise `RuntimeError("QUBO_SERIALIZATION_CORRUPTION: ...")`
    - Step 3 — Reshape: execute `Q_2d = np.array(flat_qubo, dtype=np.float64).reshape(n_qubits, n_qubits)`
    - Step 4 — Symmetry check: verify `np.allclose(Q_2d, Q_2d.T, atol=1e-9)`; if not, raise `RuntimeError("QUBO_SYMMETRY_CORRUPTION: ...")`
    - Step 5 — Emit `[QUBO_RECONSTRUCTION_AUDIT]` log at INFO level with fields `flat_length`, `reconstructed_shape`, `expected_shape`, `symmetric`, `dtype`, `status`
    - Step 6 — Dimension assertions: assert `s.ndim == 1`, `Q_2d.ndim == 2`, `Q_2d.shape[0] == Q_2d.shape[1]`, `Q_2d.shape[0] == len(s)`; if any fails, raise `RuntimeError("QUBO_DIMENSION_CORRUPTION: ...")`
    - Step 7 — Emit `[ENERGY_DIMENSION_AUDIT]` log at INFO level with fields `sample_dim`, `qubo_dim`, `hilbert_dim`, `status=VALID`
    - Step 8 — Compute energy: `total_energy = float(s.T @ Q_2d @ s) + offset`
    - _Bug_Condition: `isBugCondition` — `req_meta["qubo_matrix"]` is a flat list of `n_qubits²` floats and `np.array(Q).ndim == 1` before matmul_
    - _Expected_Behavior: `decode_and_evaluate()` returns `(avg_energy, feasible_ratio)` where both are finite floats and `0.0 <= feasible_ratio <= 1.0`, with no exception raised_
    - _Preservation: Hadamard fallback path (`Q is None`) unchanged; already-2D input path unchanged; quantum circuit outputs unchanged; `bqm_energy()` and `evaluate_solution()` results unchanged_
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.7, 2.8, 2.9, 2.10, 2.11, 3.1, 3.2_

  - [x] 3.2 Fix inline closure reshape in `run_qaoa_optimized()` in `qubo-braket-worker/qaoa_circuit.py`
    - Replace `m_energy = float(s @ Q @ s) + req_meta.get("qubo_offset", 0.0) if Q is not None else 0.0` with a reshape-safe version
    - Retrieve `Q_raw = req_meta.get("qubo_matrix")`; if not None, convert with `Q_2d = np.array(Q_raw, dtype=np.float64)`; if `Q_2d.ndim == 1`, reshape with `Q_2d = Q_2d.reshape(n_qubits, n_qubits)`; then compute `m_energy = float(s @ Q_2d @ s) + req_meta.get("qubo_offset", 0.0)`
    - This is a minimal fix — full validation sequence not required here (performance-sensitive optimization loop)
    - _Bug_Condition: same flat `qubo_matrix` in `req_meta` reaching the `objective_function` closure_
    - _Expected_Behavior: `objective_function` returns a finite scalar without raising `ValueError`_
    - _Requirements: 2.2, 1.2_

  - [x] 3.3 Add `QUBO_EXPORT_AUDIT` telemetry to `braket_integration.py`
    - After `Q, var_order, offset = to_qubo_matrix(model)`, compute `n_binary = len(var_order)` and `hilbert_dim = 2 ** n_binary`
    - Emit `logger.info(f"[QUBO_EXPORT_AUDIT] binary_variables={n_binary} qubo_shape=({n_binary},{n_binary}) hilbert_dimension={hilbert_dim}")`
    - Verify logged `qubo_shape` equals `(n_binary_variables, n_binary_variables)` — not `(2^n, 2^n)`
    - _Requirements: 2.5_

  - [x] 3.4 Verify `_run_local_execution()` in `braket_worker.py` requires no change
    - Confirm the `HAMILTONIAN_ENERGY_ORDERING` audit loop already does `Q = np.array(req.qubo_matrix, dtype=float).reshape(n_qubits, n_qubits)` before matmul
    - Document explicitly that this path is correct and must not be altered
    - _Preservation: `_run_local_execution()` audit loop behavior unchanged_
    - _Requirements: 3.2_

  - [x] 3.5 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - QUBO Flat List Dimension Mismatch Crash
    - **IMPORTANT**: Re-run the SAME test from task 1 — do NOT write a new test
    - The test from task 1 encodes the expected behavior (no `ValueError`, returns finite energy tuple)
    - When this test passes, it confirms the reshape fix is in place and the bug is resolved
    - Run bug condition exploration test from step 1
    - **EXPECTED OUTCOME**: Test PASSES — `decode_and_evaluate()` returns `(finite_float, finite_float)` for all flat `qubo_matrix` inputs without raising any exception
    - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.8, 2.9, 2.10_

  - [x] 3.6 Verify preservation tests still pass
    - **Property 2: Preservation** - Non-Buggy Input Behavior Unchanged
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run preservation property tests from step 2
    - **EXPECTED OUTCOME**: Tests PASS — Hadamard fallback and already-2D paths return identical results to pre-fix behavior; no regressions
    - Confirm all tests still pass after fix (no regressions)

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite including unit tests, property-based tests, and integration tests
  - Verify: `decode_and_evaluate()` unit tests pass for flat 4-qubit, flat 16-qubit, already-2D, and `qubo_matrix=None` cases
  - Verify: `QUBO_SERIALIZATION_CORRUPTION` raised for malformed flat list (e.g., 255 elements for 16 qubits)
  - Verify: `QUBO_SYMMETRY_CORRUPTION` raised for asymmetric Q
  - Verify: `QUBO_DIMENSION_CORRUPTION` raised when `len(s) != Q.shape[0]` after reshape
  - Verify: `[QUBO_RECONSTRUCTION_AUDIT]` log record emitted with correct fields for valid 16-qubit case
  - Verify: `[ENERGY_DIMENSION_AUDIT]` log record emitted with `sample_dim=16 qubo_dim=16 hilbert_dim=65536 status=VALID`
  - Verify: `[QUBO_EXPORT_AUDIT]` log record emitted from `braket_integration.py` with correct `binary_variables`, `qubo_shape`, `hilbert_dimension`
  - Verify: inline closure in `run_qaoa_optimized()` does not crash with flat `qubo_matrix`
  - Verify: `QUBO_OFFSET_CORRUPTION` raised when `qubo_offset` is a non-numeric type (e.g., string `"nan"`)
  - Verify: `QUBO_OFFSET_CORRUPTION` raised when `qubo_offset` is `float("nan")` or `float("inf")`
  - Verify: energy numerical correctness — `abs(energy_decode - energy_reference) < 1e-9` for all regression cases
  - Verify: serialization format invariance — `len(Q.flatten().tolist()) == len(var_order) ** 2`
  - Ensure all tests pass; ask the user if questions arise

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2"] },
    { "wave": 2, "tasks": ["3.1", "3.2", "3.3", "3.4"] },
    { "wave": 3, "tasks": ["3.5", "3.6"] },
    { "wave": 4, "tasks": ["4"] }
  ]
}
```

## Notes

- Tasks 1 and 2 are standalone and can be written in parallel before any fix is applied.
- Task 1 is expected to FAIL on unfixed code — this is intentional and confirms the bug exists.
- Task 2 is expected to PASS on unfixed code — this establishes the preservation baseline.
- The primary fix location is `qubo-braket-worker/qaoa_circuit.py` in both `decode_and_evaluate()` and the `objective_function` closure inside `run_qaoa_optimized()`.
- `braket_worker.py`'s `_run_local_execution()` already reshapes Q correctly and must NOT be changed.
- The serialization format in `braket_integration.py` (`Q.flatten().tolist()`) must NOT be changed.
- Property-based testing is used for both exploration and preservation to cover the full input domain (random `n_qubits`, random symmetric QUBO matrices, random bitstrings).
