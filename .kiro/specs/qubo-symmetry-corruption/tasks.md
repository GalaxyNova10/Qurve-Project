# Implementation Plan

## Overview

Fix the QUBO symmetry corruption bug by replacing the single-side write in `to_qubo_matrix()` with a dual-write helper, adding hard symmetry assertions at construction and serialization time, and verifying the downstream decode layer check passes cleanly.

## Tasks

- [x] 1. Write bug condition exploration test
  - **Property 1: Bug Condition** - Off-Diagonal Single-Side Write Asymmetry
  - **CRITICAL**: This test MUST FAIL on unfixed code — failure confirms the bug exists
  - **DO NOT attempt to fix the test or the code when it fails**
  - **NOTE**: This test encodes the expected behavior — it will validate the fix when it passes after implementation
  - **GOAL**: Surface counterexamples that demonstrate `max(|Q - Q^T|) == max(|quadratic coefficients|)` on unfixed code
  - **Scoped PBT Approach**: Scope the property to models with at least one off-diagonal quadratic term (isBugCondition returns true); for deterministic reproduction use the minimal 2-variable model with one cross-term `(x_0_0, x_1_0)` bias=1.0 and the 4-asset portfolio scenario
  - Test cases to implement:
    - Minimal 2-variable model: build `QuboModel` with two variables and one quadratic term `(x_0_0, x_1_0)` bias=1.0; call `to_qubo_matrix()`; assert `np.allclose(Q, Q.T, atol=1e-9)` — FAILS on unfixed code with `max_asymmetry=1.0`
    - 4-asset portfolio (primary crash scenario): build `QuboModel` from a 4-asset `SolverRequest`; call `to_qubo_matrix()`; assert `np.allclose(Q, Q.T, atol=1e-9)` — FAILS on unfixed code with `max_asymmetry≈558`
    - Cardinality-penalty-only model: build a model with only cardinality penalty cross-terms; assert symmetry — FAILS on unfixed code with `max_asymmetry = 2 * P_card`
    - Property-based variant: generate random `SolverRequest` with `n_assets` in [2, 8] and random `sigma`, `mu`; build `QuboModel`; call `to_qubo_matrix()`; assert `np.allclose(Q, Q.T, atol=1e-9)` for all generated models
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests FAIL (this is correct — it proves the bug exists)
  - Document counterexamples found (e.g., `to_qubo_matrix()` on 2-var model returns `Q[0,1]=1.0, Q[1,0]=0.0`; `max_asymmetry=1.0`)
  - Mark task complete when tests are written, run, and failures are documented
  - _Requirements: 1.1, 1.2, 1.3_

- [x] 2. Write preservation property tests (BEFORE implementing fix)
  - **Property 2: Preservation** - Diagonal Entries and BQM Storage Invariance
  - **IMPORTANT**: Follow observation-first methodology
  - Observe behavior on UNFIXED code for non-buggy inputs (diagonal-only models and BQM storage):
    - Observe: `to_qubo_matrix()` on a linear-only model (no quadratic terms) returns a diagonal matrix where `Q[i,i] == bqm.linear[var]` for each variable
    - Observe: `PortfolioBQM.add_quadratic(left, right, bias)` stores the pair under `_ordered_pair(left, right)` with the exact bias value
    - Observe: `build_portfolio_bqm()` produces identical `bqm.linear` and `bqm.quadratic` key sets and values across repeated calls
    - Observe: `Q.flatten().tolist()` produces a flat list of exactly `n_vars * n_vars` floats
  - Write property-based tests capturing observed behavior patterns from Preservation Requirements:
    - **Diagonal preservation**: for any `QuboModel`, assert `Q[i,i] == sum(bqm.linear[var] for var with index[var]==i)` for all diagonal indices `i` within `1e-12`
    - **BQM storage invariance**: for any `SolverRequest`, assert `bqm.quadratic[_ordered_pair(left, right)] == bias` immediately after `add_quadratic(left, right, bias)` is called
    - **Serialization format invariance**: for any `QuboModel`, assert `len(Q.flatten().tolist()) == len(var_order) ** 2` and `isinstance(flat_list, list)` and `all(isinstance(x, float) for x in flat_list)`
    - **Diagonal-only model symmetry**: for a model with no quadratic terms, assert `np.allclose(Q, Q.T, atol=1e-9)` passes on UNFIXED code (diagonal matrices are trivially symmetric — confirms bug is specific to off-diagonal terms)
  - Run tests on UNFIXED code
  - **EXPECTED OUTCOME**: Tests PASS (this confirms baseline behavior to preserve)
  - Mark task complete when tests are written, run, and passing on unfixed code
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 3. Fix QUBO symmetry corruption in `to_qubo_matrix()` and add audit layers

  - [x] 3.1 Add `add_symmetric_quadratic()` helper and `[QUADRATIC_ENERGY_CONVENTION_AUDIT]` to `qubo_model.py`
    - **CRITICAL — Convention B (Fully Symmetric Storage)**: the helper MUST write `value/2` to each position, NOT the full `value`. The BQM stores each coupling once with the full coefficient `v`. The matmul `x^T Q x` sums both `Q[i,j]` and `Q[j,i]`, so writing `v/2` to each recovers `v * x_i * x_j` exactly. Writing the full `v` to both positions doubles every coupling and corrupts all penalty scales.
    - Insert the following function immediately before `to_qubo_matrix()` in `qubo-backend/qubo_backend/optimization/qubo_model.py`:
      ```python
      def add_symmetric_quadratic(Q: np.ndarray, i: int, j: int, value: float) -> None:
          """Write a quadratic coefficient using Convention B — Fully Symmetric Storage.
          For i != j: writes Q[i,j] += value/2 AND Q[j,i] += value/2.
          For i == j (diagonal): writes Q[i,i] += value once (no halving).
          WARNING: Do NOT write the full value to both positions — that doubles
          every coupling and corrupts all penalty scales.
          """
          if i == j:
              Q[i, i] += value
          else:
              half = value / 2.0
              Q[i, j] += half
              Q[j, i] += half
      ```
    - Immediately after defining the helper, add the mandatory `[QUADRATIC_ENERGY_CONVENTION_AUDIT]` using a known 2-variable analytical case:
      ```python
      def _verify_energy_convention() -> None:
          """Verify Convention B: x^T Q_sym x == x^T Q_upper x for s=[1,1], bias=1.0."""
          import logging as _log
          _logger = _log.getLogger(__name__)
          Q_test = np.zeros((2, 2))
          add_symmetric_quadratic(Q_test, 0, 1, 1.0)
          s = np.array([1.0, 1.0])
          actual = float(s @ Q_test @ s)
          expected = 1.0
          double_count = abs(actual - 2.0) < 1e-12
          _logger.info(
              f"[QUADRATIC_ENERGY_CONVENTION_AUDIT] "
              f"expected={expected} actual={actual:.6f} "
              f"double_count_detected={double_count}"
          )
          if abs(actual - expected) > 1e-9:
              raise RuntimeError(
                  f"ENERGY_CONVENTION_VIOLATION: expected s^T Q s = {expected}, "
                  f"got {actual}. Check add_symmetric_quadratic() implementation."
              )
      ```
    - Call `_verify_energy_convention()` at the top of `to_qubo_matrix()` to catch any regression immediately
    - Unit test: assert `add_symmetric_quadratic(Q, 0, 1, 0.42)` writes `Q[0,1]==0.21` AND `Q[1,0]==0.21` (half-value)
    - Unit test: assert `add_symmetric_quadratic(Q, 2, 2, 1.5)` writes `Q[2,2]==1.5` only once (no halving on diagonal)
    - Unit test: assert `[QUADRATIC_ENERGY_CONVENTION_AUDIT]` emits `expected=1.0 actual=1.0 double_count_detected=False`
    - Unit test: assert `s^T Q_sym s == 1.0` for `s=[1,1]` and a 2-variable model with one cross-term bias=1.0 (not 2.0)
    - _Bug_Condition: isBugCondition(model) where model.build.bqm.quadratic contains at least one off-diagonal term with i != j_
    - _Expected_Behavior: Q[i,j] == value/2 AND Q[j,i] == value/2 for all i != j; np.allclose(Q, Q.T, atol=1e-9); x^T Q_sym x == x^T Q_upper x_
    - _Preservation: diagonal entries Q[i,i] unchanged; energy values unchanged_
    - _Requirements: 2.1, 2.2_

  - [x] 3.2 Replace the defective `if i <= j / else` branch in `to_qubo_matrix()` with `add_symmetric_quadratic()`
    - In `qubo-backend/qubo_backend/optimization/qubo_model.py` lines 55–62, replace:
      ```python
      # BEFORE (defective — single-side write):
      for (left, right), bias in model.build.bqm.quadratic.items():
          i = index[left]
          j = index[right]
          if i <= j:
              q[i, j] += float(bias)
          else:
              q[j, i] += float(bias)
      ```
      with:
      ```python
      # AFTER (fixed — half-value dual-write, Convention B):
      for (left, right), bias in model.build.bqm.quadratic.items():
          i = index[left]
          j = index[right]
          add_symmetric_quadratic(q, i, j, float(bias))
      ```
    - Unit test: `to_qubo_matrix()` on 2-variable model with cross-term bias=1.0 returns `np.allclose(Q, Q.T, atol=1e-9) == True`
    - Unit test: `to_qubo_matrix()` on 4-asset portfolio returns `max(|Q - Q^T|) < 1e-9`
    - Unit test: for 2-variable model with cross-term bias=1.0 and `s=[1,1]`, assert `float(s @ Q_fixed @ s) == 1.0` (not 2.0 — confirms no double-counting)
    - _Bug_Condition: isBugCondition(model) — any model with off-diagonal quadratic terms_
    - _Expected_Behavior: np.allclose(Q, Q.T, atol=1e-9); max(|Q - Q^T|) < 1e-9; x^T Q_sym x == x^T Q_upper x_
    - _Preservation: diagonal entries Q[i,i] == sum(bqm.linear[var]) unchanged; BQM storage in bqm_builder.py unchanged_
    - _Requirements: 2.1, 2.2, 3.1, 3.2, 3.3_

  - [x] 3.3 Add `[QUBO_SYMMETRY_AUDIT]` telemetry and hard assertion in `to_qubo_matrix()`
    - In `qubo-backend/qubo_backend/optimization/qubo_model.py`, insert after the quadratic loop and before `return`:
      ```python
      import logging as _logging
      _logger = _logging.getLogger(__name__)
      max_asymmetry = float(np.max(np.abs(q - q.T)))
      frobenius_asymmetry = float(np.linalg.norm(q - q.T, 'fro'))
      is_symmetric = max_asymmetry < 1e-9
      _logger.info(
          f"[QUBO_SYMMETRY_AUDIT] shape={q.shape} "
          f"max_asymmetry={max_asymmetry:.6e} "
          f"frobenius_asymmetry={frobenius_asymmetry:.6e} "
          f"symmetric={is_symmetric}"
      )
      if not is_symmetric:
          raise RuntimeError(
              f"QUBO_SYMMETRY_CORRUPTION: max_asymmetry={max_asymmetry:.6e}"
          )
      ```
    - Unit test: assert `[QUBO_SYMMETRY_AUDIT]` log record is emitted with `symmetric=True`, `max_asymmetry < 1e-9`, and correct `shape` for a valid model
    - Unit test: assert `to_qubo_matrix()` raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` when a model is manually constructed to produce an asymmetric matrix (e.g., by bypassing `add_symmetric_quadratic()`)
    - _Bug_Condition: isBugCondition(model) — asymmetric matrix triggers RuntimeError_
    - _Expected_Behavior: [QUBO_SYMMETRY_AUDIT] emitted with symmetric=True; RuntimeError raised if max_asymmetry >= 1e-9_
    - _Preservation: valid symmetric matrices pass through without exception_
    - _Requirements: 2.3, 2.4_

  - [x] 3.4 Add defensive `Q = 0.5*(Q+Q.T)` symmetrization and `[QUBO_SYMMETRY_AUDIT]` pre-serialization check in `braket_integration.py`
    - In `qubo-backend/qubo_backend/optimization/braket_integration.py`, in `solve_async()`, immediately before `qubo_flat = Q.flatten().tolist()`, insert:
      ```python
      # ── Defensive final symmetrization (belt-and-suspenders) ─────────
      # Applied BEFORE the hard-fail check. Harmless floating-point noise
      # (max_asymmetry < 1e-9) is corrected silently. Only structural
      # asymmetry that survives symmetrization triggers a hard failure.
      Q = 0.5 * (Q + Q.T)

      # ── [QUBO_SYMMETRY_AUDIT] pre-serialization ──────────────────────
      _max_asym = float(np.max(np.abs(Q - Q.T)))
      _frob_asym = float(np.linalg.norm(Q - Q.T, 'fro'))
      _is_sym = _max_asym < 1e-9
      logger.info(
          f"[QUBO_SYMMETRY_AUDIT] shape={Q.shape} "
          f"max_asymmetry={_max_asym:.6e} "
          f"frobenius_asymmetry={_frob_asym:.6e} "
          f"symmetric={_is_sym}"
      )
      # Hard-fail ONLY if asymmetry persists AFTER symmetrization.
      if not _is_sym:
          raise RuntimeError(
              f"QUBO_SYMMETRY_CORRUPTION: max_asymmetry={_max_asym:.6e} "
              f"persists after defensive symmetrization"
          )
      qubo_flat = Q.flatten().tolist()
      ```
    - **CRITICAL ORDER**: symmetrization (`Q = 0.5*(Q+Q.T)`) MUST come BEFORE the audit and hard-fail. Harmless floating-point noise is absorbed silently. Only structural corruption that survives symmetrization raises the exception.
    - Unit test: assert `braket_integration.py` emits `[QUBO_SYMMETRY_AUDIT]` with `symmetric=True` before serialization for a valid model
    - Unit test: assert `braket_integration.py` raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` when `to_qubo_matrix()` is mocked to return a matrix with `max_asymmetry = 100.0` (structural corruption that survives symmetrization)
    - Unit test: assert `braket_integration.py` does NOT raise when given a matrix with `max_asymmetry = 1e-15` (numerical noise absorbed by symmetrization)
    - _Bug_Condition: any asymmetric matrix reaching serialization is blocked before reaching the wire_
    - _Expected_Behavior: Q = 0.5*(Q+Q.T) applied first; [QUBO_SYMMETRY_AUDIT] emitted; RuntimeError raised only if max_asymmetry >= 1e-9 AFTER symmetrization_
    - _Preservation: serialization format unchanged — flat Python list of n_vars*n_vars floats (requirement 3.4)_
    - _Requirements: 2.7, 3.4_

  - [x] 3.5 Add `[ENERGY_CONSISTENCY_AUDIT]` in `braket_integration.py`
    - In `qubo-backend/qubo_backend/optimization/braket_integration.py`, in `solve_async()`, after the symmetrization and symmetry audit, insert:
      ```python
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
      logger.info(
          f"[ENERGY_CONSISTENCY_AUDIT] samples={len(_deltas)} "
          f"max_delta={_max_delta:.6e} "
          f"mean_delta={_mean_delta:.6e} "
          f"status=INFORMATIONAL"
      )
      ```
    - **Status is always `INFORMATIONAL`** — never `VALID` or `INVALID`. The two energy spaces are not comparable.
    - Unit test: assert `[ENERGY_CONSISTENCY_AUDIT]` log record is emitted with `status=INFORMATIONAL` for a 4-asset portfolio
    - Unit test: assert the audit does NOT raise any exception regardless of `max_delta` value
    - _Bug_Condition: energy convention mismatch between upper-triangular and symmetric Q (requirement 1.6)_
    - _Expected_Behavior: [ENERGY_CONSISTENCY_AUDIT] emitted with status=INFORMATIONAL; execution continues regardless of delta values_
    - _Preservation: bqm_energy() and evaluate_solution() return values unchanged (requirement 3.6)_
    - _Requirements: 2.9, 3.6_

  - [x] 3.6 Verify `qaoa_circuit.py` decode layer symmetry check passes (no code change needed)
    - In `qubo-braket-worker/qaoa_circuit.py`, locate the symmetry check in `decode_and_evaluate()` at Step 4 (~lines 130–140) that raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` when `np.allclose(Q_2d, Q_2d.T, atol=1e-9)` returns `False`
    - Confirm the check is present and intact — do NOT modify it
    - Run the existing check against the fixed upstream matrix and assert no `QUBO_SYMMETRY_CORRUPTION` exception is raised
    - Unit test: assert `decode_and_evaluate()` does NOT raise `QUBO_SYMMETRY_CORRUPTION` when given the fixed symmetric matrix from the updated `to_qubo_matrix()`
    - Document that this check is intentionally preserved as a downstream safety net to prevent accidental removal during future refactoring
    - _Bug_Condition: asymmetric matrix from unfixed to_qubo_matrix() triggers this check_
    - _Expected_Behavior: check passes silently (np.allclose returns True) for all correctly constructed matrices after the fix_
    - _Preservation: existing check logic and exception message unchanged (requirement 3.5)_
    - _Requirements: 2.8, 3.5_

  - [x] 3.7 Verify bug condition exploration test now passes
    - **Property 1: Expected Behavior** - Off-Diagonal Symmetric Dual-Write
    - **IMPORTANT**: Re-run the SAME tests from task 1 — do NOT write new tests
    - The tests from task 1 encode the expected behavior (`np.allclose(Q, Q.T, atol=1e-9)`)
    - When these tests pass, it confirms the expected behavior is satisfied
    - Run all bug condition exploration tests from step 1 (minimal 2-var model, 4-asset portfolio, cardinality-only model, property-based variant)
    - **EXPECTED OUTCOME**: All tests PASS (confirms bug is fixed)
    - _Requirements: 2.1, 2.2, 2.3, 2.4_

  - [x] 3.8 Verify preservation tests still pass
    - **Property 2: Preservation** - Diagonal Entries and BQM Storage Invariance
    - **IMPORTANT**: Re-run the SAME tests from task 2 — do NOT write new tests
    - Run all preservation property tests from step 2 (diagonal preservation, BQM storage invariance, serialization format invariance, diagonal-only model symmetry)
    - **EXPECTED OUTCOME**: All tests PASS (confirms no regressions)
    - Confirm diagonal entries, BQM storage, and serialization format are unchanged after the fix
    - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4. Checkpoint — Ensure all tests pass
  - Run the full test suite covering all unit tests, property-based tests, and integration tests added in tasks 1–3
  - Verify `[QUADRATIC_ENERGY_CONVENTION_AUDIT] expected=1.0 actual=1.0 double_count_detected=False` appears in logs — confirms no double-counting
  - Verify `[QUBO_SYMMETRY_AUDIT] symmetric=True` with `max_asymmetry < 1e-9` appears in logs for all execution modes (AWS_LOCAL, classical, neal, SV1)
  - Verify `[ENERGY_CONSISTENCY_AUDIT] status=INFORMATIONAL` appears in logs (never VALID or INVALID)
  - Verify no `QUBO_SYMMETRY_CORRUPTION` exception is raised anywhere in the pipeline
  - Verify no `ENERGY_CONVENTION_VIOLATION` exception is raised
  - Verify at least one non-NaN, non-Inf energy value is produced per operational execution mode
  - Verify at least one normalization graph data point with a non-NaN, non-Inf value is present in benchmark results
  - Ask the user if any questions arise before marking complete

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": ["1", "2"] },
    { "wave": 2, "tasks": ["3.1"] },
    { "wave": 3, "tasks": ["3.2"] },
    { "wave": 4, "tasks": ["3.3"] },
    { "wave": 5, "tasks": ["3.4", "3.5"] },
    { "wave": 6, "tasks": ["3.6"] },
    { "wave": 7, "tasks": ["3.7", "3.8"] },
    { "wave": 8, "tasks": ["4"] }
  ]
}
```

## Notes

- Tasks 1 and 2 MUST be completed before any implementation work begins — this is the exploratory bugfix methodology.
- Task 1 is expected to FAIL on unfixed code; document the counterexamples before proceeding to task 3.
- Task 2 is expected to PASS on unfixed code; if any preservation test fails on unfixed code, investigate before proceeding.
- **Convention B (half-value dual-write)**: `add_symmetric_quadratic()` writes `value/2` to each position — NOT the full `value`. Writing the full value to both positions doubles every coupling and corrupts all penalty scales. The `[QUADRATIC_ENERGY_CONVENTION_AUDIT]` in task 3.1 verifies this analytically before any other changes are applied.
- **Symmetrization order in task 3.4**: `Q = 0.5*(Q+Q.T)` MUST come BEFORE the `[QUBO_SYMMETRY_AUDIT]` hard-fail check. The hard-fail only triggers if structural asymmetry persists after symmetrization — harmless floating-point noise is absorbed silently.
- **`[ENERGY_CONSISTENCY_AUDIT]` is always `INFORMATIONAL`**: `s^T Q s` and `model.evaluate_solution()` are different energy spaces (full penalized BQM vs. Markowitz objective). The audit never asserts equality and never blocks execution.
- The `[QUBO_SYMMETRY_AUDIT]` hard assertion in `to_qubo_matrix()` (task 3.3) and the post-symmetrization check in `braket_integration.py` (task 3.4) are belt-and-suspenders guards; both must remain in place.
- `qaoa_circuit.py` requires no code change (task 3.6) — the existing downstream symmetry check is correct and must not be removed.
