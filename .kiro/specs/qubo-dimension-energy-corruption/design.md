# QUBO Dimension / Energy Corruption — Bugfix Design

## Overview

The benchmark engine crashes with `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 (size 256 is different from 16)` during post-processing energy evaluation. The crash occurs in `decode_and_evaluate()` inside `qubo-braket-worker/qaoa_circuit.py` when the function attempts `s @ Q @ s`.

The QUBO matrix is serialized in `braket_integration.py` as `Q.flatten().tolist()` — a flat list of `n²` floats. The decode layer in `decode_and_evaluate()` calls `np.array(req_meta.get("qubo_matrix"))` without reshaping, producing a 1-D array of shape `(n²,)` instead of the required `(n, n)` matrix. The subsequent matmul fails because `(16,) @ (256,)` is dimensionally invalid.

A secondary inline matmul in `run_qaoa_optimized()`'s `objective_function` closure (`m_energy = float(s @ Q @ s)`) has the same defect. The audit loop in `braket_worker.py`'s `_run_local_execution()` already reshapes Q before the matmul and is correct.

The fix is purely in the classical post-processing decode layer. No quantum circuit, Hamiltonian, statevector, or serialization format changes.

---

## Glossary

- **Bug_Condition (C)**: The condition that triggers the crash — `req_meta["qubo_matrix"]` is a flat list of `n²` floats and `decode_and_evaluate()` (or the inline closure) calls `np.array(Q)` without reshaping before `s @ Q @ s`.
- **Property (P)**: The desired behavior when the bug condition holds — the function reshapes Q to `(n, n)` float64, validates dimensions and symmetry, emits audit telemetry, and returns a finite scalar energy.
- **Preservation**: All behaviors that must remain unchanged — quantum circuit outputs, serialization format, `to_qubo_matrix()` shape contract, `bqm_energy()` / `evaluate_solution()` numerical results, and the Hadamard fallback path.
- **`decode_and_evaluate(measurements, n_qubits, req_meta)`**: The function in `qubo-braket-worker/qaoa_circuit.py` (lines ~89–160) that decodes measurement bitstrings and computes QUBO energy. This is the primary fix location.
- **`run_qaoa_optimized()`**: The function in `qubo-braket-worker/qaoa_circuit.py` (lines ~165–end) whose `objective_function` closure contains a secondary inline `s @ Q @ s` that must also be fixed.
- **`_run_local_execution()`**: The function in `qubo-braket-worker/braket_worker.py` that already reshapes Q before the `HAMILTONIAN_ENERGY_ORDERING` audit loop — this path is correct and must not be changed.
- **`build_portfolio_bqm()`**: The function in `qubo-backend/qubo_backend/optimization/bqm_builder.py` where `QUBO_EXPORT_AUDIT` telemetry must be added after `to_qubo_matrix()` is called in `braket_integration.py`.
- **`to_qubo_matrix(model)`**: Returns `(Q, var_order, offset)` where Q is already `(n_vars, n_vars)` — the shape contract that must be preserved.
- **`flat_qubo`**: The flat Python list of `n²` floats stored in `req_meta["qubo_matrix"]` after serialization via `Q.flatten().tolist()`.
- **`n_qubits`**: The integer number of binary variables; `n_qubits²` is the expected length of `flat_qubo`.
- **`BinaryQUBOData`**: Proposed typed dataclass for the flat serialized form (Phase 6 type isolation).
- **`QuantumOperatorData`**: Proposed typed dataclass for the Ising Hamiltonian parameters `(h, J, C)` (Phase 6 type isolation).

---

## Bug Details

### Bug Condition

The bug manifests when `decode_and_evaluate()` (or the inline closure in `run_qaoa_optimized()`) retrieves `Q = req_meta.get("qubo_matrix")` and converts it with `np.array(Q)` without reshaping. The resulting array has shape `(n_qubits²,)` — a 1-D vector — while the sample vector `s` has shape `(n_qubits,)`. NumPy's matmul requires the inner dimensions to align: `(n,) @ (n, n) @ (n,)` is valid, but `(n,) @ (n²,)` is not.

**Formal Specification:**

```
FUNCTION isBugCondition(req_meta, meas, n_qubits)
  INPUT: req_meta dict, meas list[int], n_qubits int
  OUTPUT: boolean

  flat_qubo = req_meta.get("qubo_matrix")
  IF flat_qubo IS None THEN RETURN False  -- fallback path, no bug

  Q_raw = np.array(flat_qubo)
  s     = np.array(meas)

  RETURN Q_raw.ndim == 1
         AND len(Q_raw) == n_qubits * n_qubits
         AND len(s) == n_qubits
         AND Q_raw has NOT been reshaped to (n_qubits, n_qubits) before matmul
END FUNCTION
```

### Examples

- **16-qubit portfolio (primary crash)**: `flat_qubo` has 256 elements, `s` has shape `(16,)`. `np.array(flat_qubo)` produces shape `(256,)`. `s @ Q @ s` → `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 (size 256 is different from 16)`.
- **4-qubit test case**: `flat_qubo` has 16 elements, `s` has shape `(4,)`. Same crash pattern: `(4,) @ (16,)` fails.
- **Already-2D input (no bug)**: `braket_worker.py` calls `np.array(req.qubo_matrix, dtype=float).reshape(n_qubits, n_qubits)` before passing to `run_qaoa_optimized()`, so `req_meta["qubo_matrix"]` may arrive as a 2-D list-of-lists. `np.array(Q)` on a 2-D list produces shape `(n, n)` — no crash. The fix must handle both cases.
- **Inline closure in `run_qaoa_optimized()`**: `m_energy = float(s @ Q @ s)` where `Q = req_meta.get("qubo_matrix")` — same defect, same crash path.

---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Quantum circuit construction (`build_qaoa_circuit`, `qubo_to_ising`) must produce bit-for-bit identical outputs before and after the fix.
- `to_qubo_matrix()` in `qubo_model.py` must continue to return a 2-D array of shape `(n_vars, n_vars)` — this is already correct and must not be altered.
- `braket_integration.py` serialization (`Q.flatten().tolist()`) must remain unchanged — the flat list format is the wire format and must not be modified.
- `bqm_energy(model.build, int_sample)` and `model.evaluate_solution(sample)` must return numerically identical results to pre-fix behavior for all inputs.
- The Hadamard fallback path in `decode_and_evaluate()` (when `Q is None`) must continue to work exactly as before.
- The `HAMILTONIAN_ENERGY_ORDERING` audit loop in `braket_worker.py` (which already reshapes Q) must not be changed.

**Scope:**
All inputs that do NOT involve a flat `qubo_matrix` in `req_meta` (i.e., `Q is None`, or Q is already correctly shaped as a 2-D array) are completely unaffected by this fix. This includes:
- The Hadamard fallback path
- Cloud execution paths that already reshape Q
- All `to_qubo_matrix()` callers in `braket_integration.py`
- All `bqm_energy()` and `evaluate_solution()` callers in `_feasibility_filter()`

**Note:** The actual expected correct behavior for buggy inputs is defined in the Correctness Properties section (Property 1). This section focuses on what must NOT change.

---

## Hypothesized Root Cause

Based on the bug description and code inspection, the root cause is confirmed (not merely hypothesized):

1. **Missing reshape in `decode_and_evaluate()`**: Line ~130 in `qaoa_circuit.py` does `s = np.array(meas)` and then `total_energy = float(s @ Q @ s)` where `Q = req_meta.get("qubo_matrix")`. `req_meta` is populated from `request.model_dump()` in `braket_worker.py`, which serializes `qubo_matrix` as the flat list originally passed in the HTTP request. `np.array(flat_list)` produces a 1-D array — no reshape is ever performed in this code path.

2. **Missing reshape in `run_qaoa_optimized()` inline closure**: Line ~220 in `qaoa_circuit.py` does `m_energy = float(s @ Q @ s) + req_meta.get("qubo_offset", 0.0) if Q is not None else 0.0` inside `objective_function`. Same defect — `Q` is taken directly from `req_meta` without reshaping.

3. **Asymmetric fix in `braket_worker.py`**: `_run_local_execution()` correctly does `Q = np.array(req.qubo_matrix, dtype=float).reshape(n_qubits, n_qubits)` before the `HAMILTONIAN_ENERGY_ORDERING` audit loop. However, this reshaped Q is NOT propagated into `req_meta` — `req_meta = req.model_dump()` is called separately and still contains the flat list. So `run_qaoa_optimized()` and `decode_and_evaluate()` receive the flat form.

4. **No validation or telemetry before matmul**: Neither function checks dimensions or emits audit records before attempting the matmul, so the crash is the first observable signal.

5. **Missing `QUBO_EXPORT_AUDIT` telemetry**: `build_portfolio_bqm()` does not emit a log record confirming the binary-variable-space QUBO shape at export time, making it impossible to distinguish a correct export from a corrupted one in logs.

---

## Correctness Properties

Property 1: Bug Condition — QUBO Matrix Reshape Before Matmul

_For any_ call to `decode_and_evaluate(measurements, n_qubits, req_meta)` where `req_meta["qubo_matrix"]` is a flat list of `n_qubits²` floats (i.e., `isBugCondition` returns true), the fixed function SHALL reshape Q to `(n_qubits, n_qubits)` float64, validate length, symmetry, and dimension alignment, emit `[QUBO_RECONSTRUCTION_AUDIT]` and `[ENERGY_DIMENSION_AUDIT]` telemetry, and return a 2-tuple `(avg_energy, feasible_ratio)` where both elements are finite floats — without raising any exception.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.8, 2.9, 2.10**

Property 2: Preservation — Non-Buggy Input Behavior Unchanged

_For any_ call to `decode_and_evaluate()` where `req_meta["qubo_matrix"]` is either `None` (Hadamard fallback) or already a correctly shaped 2-D array (i.e., `isBugCondition` returns false), the fixed function SHALL produce exactly the same return value as the original function, preserving all existing energy computation, feasibility ratio, and fallback logic.

**Validates: Requirements 3.1, 3.6, 3.7**

Property 3: Preservation — Energy Numerical Correctness

_For any_ sample bitstring `s` and valid `(n, n)` QUBO matrix Q with offset, the energy computed by the fixed `decode_and_evaluate()` as `float(s.T @ Q @ s) + offset` SHALL match the reference BQM energy `bqm_energy(model.build, sample)` to within `abs(energy_decode - energy_reference) < 1e-9`, guaranteeing the reconstructed matrix is numerically correct, not merely dimensionally correct.

**Validates: Requirements 3.5, 3.8**

Property 4: Preservation — Serialization Format Invariance

_For any_ QUBO model built by `to_qubo_matrix(model)`, the flat serialization `Q.flatten().tolist()` SHALL have length exactly `n_vars²` where `n_vars = len(var_order)`, and the fix SHALL NOT alter this serialization format or the shape contract of `to_qubo_matrix()`.

**Validates: Requirements 3.3, 3.4**

---

## Fix Implementation

### Changes Required

Assuming the root cause analysis above is correct:

---

**File**: `qubo-braket-worker/qaoa_circuit.py`

**Function**: `decode_and_evaluate()`

**Specific Changes — Validation Sequence (7 steps)**:

1. **Step 1 — Serialization length check**: Before reshape, verify `len(flat_qubo) == n_qubits * n_qubits`. If not, raise `RuntimeError("QUBO_SERIALIZATION_CORRUPTION: ...")`.

2. **Step 2 — Reshape to (n, n) float64**: Execute `Q_2d = np.array(flat_qubo, dtype=np.float64).reshape(n_qubits, n_qubits)`.

3. **Step 3 — Symmetry check**: Verify `np.allclose(Q_2d, Q_2d.T, atol=1e-9)`. If not, raise `RuntimeError("QUBO_SYMMETRY_CORRUPTION: ...")`.

4. **Step 4 — Emit `[QUBO_RECONSTRUCTION_AUDIT]`**: Log at INFO level with fields `flat_length`, `reconstructed_shape`, `expected_shape`, `symmetric`, `dtype`, `status`.

5. **Step 5 — Dimension assertions**: Assert `s.ndim == 1`, `Q_2d.ndim == 2`, `Q_2d.shape[0] == Q_2d.shape[1]`, `Q_2d.shape[0] == len(s)`. If any fails, raise `RuntimeError("QUBO_DIMENSION_CORRUPTION: ...")`.

6. **Step 6 — Emit `[ENERGY_DIMENSION_AUDIT]`**: Log at INFO level with fields `sample_dim`, `qubo_dim`, `hilbert_dim`, `status=VALID`.

7. **Step 7 — Compute energy**: `total_energy = float(s.T @ Q_2d @ s) + offset`.

**Handle already-2D input**: Before Step 1, check if `Q` is already a 2-D array (i.e., `isinstance(Q, np.ndarray) and Q.ndim == 2`, or `isinstance(Q, list) and isinstance(Q[0], list)`). If so, convert directly with `Q_2d = np.array(Q, dtype=np.float64)` and skip Steps 1–2, proceeding from Step 3.

---

**File**: `qubo-braket-worker/qaoa_circuit.py`

**Function**: `run_qaoa_optimized()` — `objective_function` closure

**Specific Changes**:

Replace the inline `m_energy = float(s @ Q @ s) + ...` with a helper call or inline reshape:

```python
Q_raw = req_meta.get("qubo_matrix")
if Q_raw is not None:
    Q_2d = np.array(Q_raw, dtype=np.float64)
    if Q_2d.ndim == 1:
        Q_2d = Q_2d.reshape(n_qubits, n_qubits)
    m_energy = float(s @ Q_2d @ s) + req_meta.get("qubo_offset", 0.0)
else:
    m_energy = 0.0
```

This is a minimal fix — the full validation sequence (Steps 1–6) is not required here because this path is inside an optimization loop where performance matters and the matrix has already been validated by `decode_and_evaluate()` earlier in the same call.

---

**File**: `qubo-backend/qubo_backend/optimization/braket_integration.py`

**Function**: `solve_async()` — after `Q, var_order, offset = to_qubo_matrix(model)`

**Specific Changes — Add `QUBO_EXPORT_AUDIT` telemetry**:

```python
Q, var_order, offset = to_qubo_matrix(model)
n_binary = len(var_order)
hilbert_dim = 2 ** n_binary
logger.info(
    f"[QUBO_EXPORT_AUDIT] binary_variables={n_binary} "
    f"qubo_shape=({n_binary},{n_binary}) "
    f"hilbert_dimension={hilbert_dim}"
)
```

This satisfies requirement 2.5. The audit is emitted at the point where the matrix is first constructed in binary-variable space, immediately after `to_qubo_matrix()`.

---

**File**: `qubo-braket-worker/braket_worker.py`

**Function**: `_run_local_execution()`

**Specific Changes — Verify audit loop (no code change required)**:

The `HAMILTONIAN_ENERGY_ORDERING` audit loop already does:
```python
Q = np.array(req.qubo_matrix, dtype=float).reshape(n_qubits, n_qubits)
energy = float(s @ Q @ s) + req.qubo_offset
```
This path is correct. No change is needed. The design documents this explicitly to prevent accidental regression.

---

**Phase 6 — Type Isolation (BinaryQUBOData / QuantumOperatorData)**:

Add typed dataclasses to prevent accidental propagation of flat vs. 2-D forms between layers:

```python
@dataclass(frozen=True)
class BinaryQUBOData:
    """Typed container for the flat serialized QUBO matrix (wire format)."""
    flat: list[float]
    n_qubits: int

    def to_matrix(self) -> np.ndarray:
        """Reshape to (n_qubits, n_qubits) float64 with validation."""
        if len(self.flat) != self.n_qubits * self.n_qubits:
            raise RuntimeError("QUBO_SERIALIZATION_CORRUPTION")
        return np.array(self.flat, dtype=np.float64).reshape(self.n_qubits, self.n_qubits)

@dataclass(frozen=True)
class QuantumOperatorData:
    """Typed container for Ising Hamiltonian parameters."""
    h: np.ndarray   # shape (n,)
    J: np.ndarray   # shape (n, n)
    C: float
    n_qubits: int
```

These dataclasses make the type boundary explicit and prevent the flat list from being passed where a 2-D matrix is expected.

---

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the bug on unfixed code (exploratory), then verify the fix works correctly and preserves existing behavior (fix checking + preservation checking).

---

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the crash BEFORE implementing the fix. Confirm the root cause analysis. If the tests do not fail on unfixed code, the root cause hypothesis must be revised.

**Test Plan**: Write unit tests that call `decode_and_evaluate()` with a flat `qubo_matrix` in `req_meta` and assert that the function returns a finite energy tuple. Run these tests on the UNFIXED code to observe the `ValueError` and confirm the crash path.

**Test Cases**:

1. **16-qubit flat list (primary crash)**: Call `decode_and_evaluate([[0]*16], 16, {"qubo_matrix": [0.0]*256, "qubo_offset": 0.0, ...})`. Expected on unfixed code: `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 (size 256 is different from 16)`. (will fail on unfixed code)

2. **4-qubit flat list**: Call `decode_and_evaluate([[1,0,1,0]], 4, {"qubo_matrix": [0.0]*16, ...})`. Expected on unfixed code: `ValueError` with dimension mismatch. (will fail on unfixed code)

3. **Inline closure in `run_qaoa_optimized()`**: Construct a minimal `req_meta` with a flat `qubo_matrix` and trigger the `objective_function` closure. Expected on unfixed code: same `ValueError`. (will fail on unfixed code)

4. **Already-2D input (no crash expected)**: Call `decode_and_evaluate()` with `qubo_matrix` as a list-of-lists `[[...], [...]]`. Expected on unfixed code: no crash (because `np.array(list_of_lists)` produces 2-D). This confirms the already-2D path is not broken. (should pass on unfixed code)

**Expected Counterexamples**:
- `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 (size N² is different from N)` for any flat input.
- Possible causes confirmed: `np.array(flat_list)` produces 1-D, no reshape is performed before matmul.

---

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed function produces the expected behavior.

**Pseudocode:**
```
FOR ALL (measurements, n_qubits, req_meta) WHERE isBugCondition(req_meta, measurements[0], n_qubits) DO
  result := decode_and_evaluate_fixed(measurements, n_qubits, req_meta)
  ASSERT isinstance(result, tuple) AND len(result) == 2
  ASSERT math.isfinite(result[0])   -- avg_energy is finite
  ASSERT math.isfinite(result[1])   -- feasible_ratio is finite
  ASSERT 0.0 <= result[1] <= 1.0    -- feasible_ratio is a valid ratio
END FOR
```

---

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold, the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL (measurements, n_qubits, req_meta) WHERE NOT isBugCondition(req_meta, measurements[0], n_qubits) DO
  ASSERT decode_and_evaluate_original(measurements, n_qubits, req_meta)
       = decode_and_evaluate_fixed(measurements, n_qubits, req_meta)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many test cases automatically across the input domain (random bitstrings, random QUBO matrices, random portfolio parameters).
- It catches edge cases that manual unit tests might miss (e.g., all-zeros bitstring, identity matrix, near-singular matrices).
- It provides strong guarantees that behavior is unchanged for all non-buggy inputs.

**Test Plan**: Observe behavior on UNFIXED code for already-2D inputs and `Q is None` inputs, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Already-2D preservation**: For any valid `(n, n)` QUBO matrix passed as a 2-D array, verify the fixed function returns the same energy as the original. (observe on unfixed code first)

2. **Hadamard fallback preservation**: For any `req_meta` with `qubo_matrix=None`, verify the fixed function returns the same fallback energy as the original. (observe on unfixed code first)

3. **Energy numerical correctness**: For any sample `s` and valid `(n, n)` Q, verify `float(s.T @ Q @ s) + offset` matches `bqm_energy(model.build, sample)` within `1e-9`. (regression test 3.8)

4. **Serialization format invariance**: For any `QuboModel`, verify `len(Q.flatten().tolist()) == len(var_order) ** 2`. (regression test 3.4)

---

### Unit Tests

- Test `decode_and_evaluate()` with flat 16-element list for 4-qubit case — verify returns `(finite_float, finite_float)`.
- Test `decode_and_evaluate()` with already-2D 4×4 array — verify same result as flat input.
- Test `decode_and_evaluate()` with `qubo_matrix=None` — verify Hadamard fallback path returns without exception.
- Test `QUBO_SERIALIZATION_CORRUPTION` is raised when `len(flat_qubo) != n_qubits²` (e.g., 255 elements for 16 qubits).
- Test `QUBO_SYMMETRY_CORRUPTION` is raised when Q is asymmetric (e.g., Q[0,1] = 1.0, Q[1,0] = 0.0).
- Test `QUBO_DIMENSION_CORRUPTION` is raised when `len(s) != Q.shape[0]` after reshape.
- Test `[QUBO_RECONSTRUCTION_AUDIT]` log record is emitted with correct fields for a valid 16-qubit case.
- Test `[ENERGY_DIMENSION_AUDIT]` log record is emitted with `sample_dim=16 qubo_dim=16 hilbert_dim=65536 status=VALID`.
- Test `[QUBO_EXPORT_AUDIT]` log record is emitted from `braket_integration.py` with correct `binary_variables`, `qubo_shape`, `hilbert_dimension`.
- Test inline closure in `run_qaoa_optimized()` does not crash with flat `qubo_matrix`.

---

### Property-Based Tests

- **Property 1 (Fix Checking)**: Generate random `n_qubits` in [2, 8], random symmetric `(n, n)` QUBO matrix, random bitstring `s`. Flatten Q to a list, pass to fixed `decode_and_evaluate()`. Assert result is `(finite_float, finite_float)` with no exception.

- **Property 2 (Preservation — already-2D)**: Generate random valid 2-D QUBO matrix. Assert fixed `decode_and_evaluate()` returns the same energy as computing `float(s.T @ Q @ s) + offset` directly.

- **Property 3 (Energy correctness)**: Generate random `SolverRequest`, build `QuboModel`, call `to_qubo_matrix()`, flatten, pass to fixed `decode_and_evaluate()`. Assert energy matches `bqm_energy(model.build, sample)` within `1e-9`.

- **Property 4 (Serialization invariance)**: Generate random `SolverRequest`, build `QuboModel`, call `to_qubo_matrix()`. Assert `len(Q.flatten().tolist()) == len(var_order) ** 2`.

- **Property 5 (Feasible ratio bounds)**: For any valid input, assert `0.0 <= feasible_ratio <= 1.0` from `decode_and_evaluate()`.

---

### Integration Tests

- **Full benchmark run (LOCAL mode)**: Run the benchmark pipeline end-to-end with a 4-asset portfolio. Assert at least one finite energy value is produced, feasible ratio > 0.0, and no `ValueError` appears in logs.
- **Full benchmark run (neal mode)**: Same as above for the neal solver path.
- **Full benchmark run (AWS_LOCAL mode)**: Same as above for the AWS_LOCAL path.
- **Context switching**: Verify that switching between execution modes (LOCAL → neal → AWS_LOCAL) does not produce dimension errors.
- **`QUBO_EXPORT_AUDIT` in logs**: Run `solve_async()` and assert the log contains `[QUBO_EXPORT_AUDIT]` with correct `qubo_shape` matching `(n_vars, n_vars)` — not `(2^n, 2^n)`.
- **Normalization graph data**: Assert the benchmark result contains at least one normalization graph data point after the fix.
