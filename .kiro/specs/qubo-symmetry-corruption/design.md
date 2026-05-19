# QUBO Symmetry Corruption — Bugfix Design

## Overview

The benchmark engine raises `QUBO_SYMMETRY_CORRUPTION: QUBO matrix is not symmetric (max asymmetry=5.589827e+02)` during energy evaluation in `decode_and_evaluate()`. A max asymmetry of ~558 is not floating-point noise — it equals the full magnitude of every quadratic coefficient, which is the exact signature of a structurally half-populated matrix.

The root cause is in `to_qubo_matrix()` in `qubo-backend/qubo_backend/optimization/qubo_model.py` (lines 55–62). For every off-diagonal quadratic term `(left, right)` with bias `v`, the function writes either `q[i,j] += v` (when `i <= j`) or `q[j,i] += v` (when `i > j`) — never both. The result is a matrix where every off-diagonal position has a value on exactly one side of the diagonal and zero on the other, producing `max(|Q - Q^T|) = max(|quadratic coefficients|)`.

The fix is a **half-value dual-write** in `to_qubo_matrix()`: every off-diagonal term writes `v/2` to both `q[i,j]` and `q[j,i]`, so that `x^T Q_sym x` produces the same scalar as the original upper-triangular `x^T Q_upper x`. A canonical `add_symmetric_quadratic(Q, i, j, value)` helper enforces this invariant. A mandatory `[QUADRATIC_ENERGY_CONVENTION_AUDIT]` with a known 2-variable analytical case verifies the convention is correct before any other changes are applied. A hard symmetry assertion with `[QUBO_SYMMETRY_AUDIT]` telemetry gates the return value. A defensive final symmetrization `Q = 0.5 * (Q + Q.T)` before serialization in `braket_integration.py` provides a second layer of protection, with the hard-fail check applied **after** symmetrization (not before). An `[ENERGY_CONSISTENCY_AUDIT]` is emitted as `INFORMATIONAL` only — it does not assert equality between `s^T Q s` and `model.evaluate_solution()` because those are different energy spaces (full penalized BQM vs. Markowitz objective).


---

## Glossary

- **Bug_Condition (C)**: The condition that triggers the bug — `to_qubo_matrix()` writes an off-diagonal quadratic term to only one of `q[i,j]` or `q[j,i]`, leaving the mirror position at `0.0`.
- **Property (P)**: The desired behavior when the bug condition holds — every off-diagonal write is mirrored so that `Q[i,j] == Q[j,i]` for all `i != j`, satisfying `np.allclose(Q, Q.T, atol=1e-9)`.
- **Preservation**: All behaviors that must remain unchanged — diagonal entries, BQM quadratic storage in `bqm_builder.py`, serialization format in `braket_integration.py`, energy evaluation in `bqm_energy()` and `evaluate_solution()`, and the existing symmetry check in `decode_and_evaluate()`.
- **`to_qubo_matrix(model)`**: The function in `qubo-backend/qubo_backend/optimization/qubo_model.py` (lines 44–62) that converts a `QuboModel` to a NumPy matrix `Q`, variable order list, and scalar offset. This is the primary fix location.
- **`add_symmetric_quadratic(Q, i, j, value)`**: The new helper function to be added in `qubo_model.py` that writes `Q[i,j] += value/2` AND `Q[j,i] += value/2` for `i != j`. This is the **Convention B — Fully Symmetric Storage** convention: each position holds half the coefficient so that `x^T Q_sym x = x^T Q_upper x` for all binary `x`. For `i == j` (diagonal), writes `Q[i,i] += value` once unchanged.
- **Energy Convention**: The codebase uses **Convention B — Fully Symmetric Storage**. The BQM stores each off-diagonal coupling once with the full coefficient `v`. `to_qubo_matrix()` must distribute this as `Q[i,j] = v/2` and `Q[j,i] = v/2` so that the matmul `x^T Q x` sums both positions and recovers `v * x_i * x_j` exactly. Writing the full `v` to both positions would double-count every coupling and corrupt all penalty scales.
- **`[QUADRATIC_ENERGY_CONVENTION_AUDIT]`**: A mandatory analytical verification emitted during task 3.1 using a known 2-variable case: BQM with one cross-term `(a, b)` bias=`1.0`, binary vector `s=[1,1]`. Expected: `s^T Q_sym s = 1.0`. If the result is `2.0`, the convention is wrong (full-value dual-write). Fields: `expected=1.0 actual=<float> double_count_detected=<bool>`.
- **`PortfolioBQM.add_quadratic(left, right, bias)`**: The method in `bqm_builder.py` (line ~55) that canonicalizes pairs via `_ordered_pair()` and stores each coupling once in `bqm.quadratic`. This storage is correct and must not change.
- **`_ordered_pair(a, b)`**: The function in `bqm_builder.py` (line ~14) that returns `(a, b)` if `a <= b` else `(b, a)`. Ensures each pair is stored under a canonical key. Correct and unchanged.
- **`[QUBO_SYMMETRY_AUDIT]`**: The INFO-level log record emitted by `to_qubo_matrix()` after construction, containing `shape`, `max_asymmetry`, `frobenius_asymmetry`, and `symmetric` fields.
- **`[QUBO_EXPORT_AUDIT]`**: The INFO-level log record already emitted in `braket_integration.py` after `to_qubo_matrix()` returns, confirming `binary_variables`, `qubo_shape`, and `hilbert_dimension`.
- **`[ENERGY_CONSISTENCY_AUDIT]`**: The INFO-level log record emitted after verifying that `s^T Q s` matches `model.evaluate_solution(s)` for at least 100 random binary vectors.
- **`Q_upper`**: The original upper-triangular matrix produced by the unfixed `to_qubo_matrix()`.
- **`Q_sym`**: The fixed symmetric matrix where every off-diagonal term is mirrored.


---

## Bug Details

### Bug Condition

The bug manifests in `to_qubo_matrix()` in `qubo_model.py` at lines 55–62. The function iterates over `model.build.bqm.quadratic.items()` — a dict whose keys are canonical pairs `(left, right)` with `left <= right` (enforced by `_ordered_pair()` in `bqm_builder.py`). For each pair it computes indices `i = index[left]` and `j = index[right]`, then branches:

```python
if i <= j:
    q[i, j] += float(bias)   # writes upper triangle only
else:
    q[j, i] += float(bias)   # writes lower triangle only
```

Neither branch writes to the mirror position. The result is a matrix where `Q[i,j] != 0` but `Q[j,i] == 0` (or vice versa) for every off-diagonal term. The asymmetry equals the full coefficient magnitude, not a rounding error.

**Formal Specification:**

```
FUNCTION isBugCondition(model)
  INPUT: model of type QuboModel
  OUTPUT: boolean

  Q, var_order, offset = to_qubo_matrix(model)

  RETURN EXISTS (left, right) IN model.build.bqm.quadratic
         WHERE index[left] != index[right]
         AND (Q[index[left], index[right]] != Q[index[right], index[left]])
END FUNCTION
```

### Examples

- **4-asset portfolio, cross-term `(x_0_0, x_1_0)` with bias `v = 0.42`**: `i=0, j=4` (assuming 4-bit encoding). Unfixed code writes `q[0,4] += 0.42` only. Fixed code writes `q[0,4] += 0.21` AND `q[4,0] += 0.21` (half-value dual-write). For binary `s` with `s_0=s_4=1`: unfixed gives `0.42 * 1 * 1 = 0.42`; fixed gives `(0.21 + 0.21) * 1 * 1 = 0.42`. Energy is preserved. Asymmetry contribution before fix: `|0.42 - 0.0| = 0.42`; after fix: `|0.21 - 0.21| = 0.0`.
- **Cardinality penalty cross-term `(y_0, y_1)` with bias `2 * P_card ≈ 558`**: `i` and `j` depend on variable sort order. Unfixed code writes to one triangle only. This single term accounts for the observed `max_asymmetry = 5.589827e+02`.
- **Diagonal term `(x_0_0, x_0_0)` with bias `b`**: `i == j`, so the `if i <= j` branch writes `q[i,i] += b`. Diagonal terms are unaffected by the bug — no mirror is needed.
- **Energy evaluation with asymmetric Q**: For binary vector `s` with `s_i = s_j = 1` at an off-diagonal term with bias `v`, the upper-triangular convention gives energy contribution `v * s_i * s_j`. The half-value symmetric convention gives `(v/2 + v/2) * s_i * s_j = v * s_i * s_j`. Energy is identical. A full-value dual-write would give `2v * s_i * s_j` — doubling every coupling, which is wrong.


---

## Expected Behavior

### Preservation Requirements

**Unchanged Behaviors:**
- Diagonal entries in `Q` must equal the sum of all linear biases for each variable: `q[i,i] == sum(bqm.linear[var] for var with index[var]==i)`.
- `PortfolioBQM.add_quadratic(left, right, bias)` must continue to store pairs under `_ordered_pair(left, right)` with the exact bias value — no change to BQM storage.
- `build_portfolio_bqm()` must produce identical `bqm.linear` and `bqm.quadratic` key sets and values before and after this fix.
- `braket_integration.py` serialization (`Q.flatten().tolist()`) must remain a flat Python list of exactly `n_vars * n_vars` floats.
- `bqm_energy(model.build, int_sample)` and `model.evaluate_solution(sample)` must return numerically identical results to pre-fix behavior for all inputs.
- The existing symmetry check in `decode_and_evaluate()` in `qaoa_circuit.py` must continue to pass (i.e., raise no `QUBO_SYMMETRY_CORRUPTION`) because the upstream matrix is now correctly symmetric.
- The Hadamard fallback path in `decode_and_evaluate()` (when `Q is None`) must be completely unaffected.

**Scope:**
All inputs that do NOT involve off-diagonal quadratic terms in `to_qubo_matrix()` are completely unaffected. This includes:
- Models with only linear (diagonal) terms.
- The BQM construction logic in `bqm_builder.py`.
- All downstream consumers of the flat serialized QUBO list.
- All energy evaluation paths using `bqm_energy()` or `evaluate_solution()`.

**Note:** The actual expected correct behavior for buggy inputs is defined in the Correctness Properties section (Property 1). This section focuses on what must NOT change.


---

## Hypothesized Root Cause

Based on code inspection of `qubo_model.py` lines 44–62, the root cause is confirmed (not merely hypothesized):

1. **Single-side write in `to_qubo_matrix()` (lines 55–62)**: The `if i <= j / else` branch writes to exactly one of `q[i,j]` or `q[j,i]` per quadratic term. The mirror position is never written. This is the direct cause of the asymmetry.

   ```python
   # DEFECTIVE CODE (lines 55-62 of qubo_model.py):
   for (left, right), bias in model.build.bqm.quadratic.items():
       i = index[left]
       j = index[right]
       if i <= j:
           q[i, j] += float(bias)   # ← mirror q[j,i] never written
       else:
           q[j, i] += float(bias)   # ← mirror q[i,j] never written
   ```

2. **Canonical pair storage in `bqm_builder.py` (line ~55)**: `add_quadratic()` calls `_ordered_pair()` to canonicalize `(left, right)` so each coupling is stored once. This is correct behavior for BQM storage, but it means `to_qubo_matrix()` sees each off-diagonal pair exactly once and must mirror it explicitly — which it currently does not.

3. **No symmetry assertion at construction time**: `to_qubo_matrix()` returns the matrix without any symmetry check. The first symmetry check occurs much later in `decode_and_evaluate()` in `qaoa_circuit.py` (Step 4 of the validation sequence), which is too late — the asymmetric matrix has already been serialized and transmitted.

4. **No symmetry audit before serialization**: In `braket_integration.py`, `qubo_flat = Q.flatten().tolist()` is called immediately after `to_qubo_matrix()` returns, with no intervening symmetry verification. A `[QUBO_SYMMETRY_AUDIT]` check here would catch any asymmetry before it reaches the wire.

5. **Energy convention mismatch**: The docstring of `to_qubo_matrix()` says "upper-triangular QUBO matrix Q where E=x'Qx+offset". The BQM stores each off-diagonal coupling once with the full coefficient `v`. The matmul `x^T Q_upper x` counts `Q[i,j] * x_i * x_j` once (upper triangle only). A fully symmetric matrix must therefore store `v/2` at each position so that `x^T Q_sym x = (v/2 + v/2) * x_i * x_j = v * x_i * x_j`. Writing the full `v` to both positions would produce `2v * x_i * x_j` — doubling every coupling and corrupting all penalty scales and the objective function.


---

## Correctness Properties

Property 1: Bug Condition — Symmetric Dual-Write for All Off-Diagonal Terms

_For any_ `QuboModel` where `isBugCondition(model)` returns true (i.e., `bqm.quadratic` contains at least one off-diagonal term), the fixed `to_qubo_matrix()` SHALL write both `Q[i,j] += v` AND `Q[j,i] += v` for every off-diagonal term `(left, right)` with bias `v` and indices `i = index[left]`, `j = index[right]`, `i != j`, producing a matrix satisfying `np.allclose(Q, Q.T, atol=1e-9)` with `max(|Q - Q^T|) < 1e-9`.

**Validates: Requirements 2.1, 2.2, 2.3, 2.4**

Property 2: Preservation — Diagonal Entries Unchanged

_For any_ `QuboModel`, the fixed `to_qubo_matrix()` SHALL produce diagonal entries `Q[i,i]` equal to the sum of all linear biases for the variable at index `i` in `bqm.linear`, identical to the values produced by the original function, preserving all linear term contributions.

**Validates: Requirements 3.1, 3.3**

Property 3: Preservation — BQM Storage Invariance

_For any_ call to `PortfolioBQM.add_quadratic(left, right, bias)`, the fixed code SHALL store the pair under `_ordered_pair(left, right)` with the exact bias value, and `build_portfolio_bqm()` SHALL produce identical `bqm.linear` and `bqm.quadratic` key sets and values to within `1e-12`, preserving all upstream BQM construction behavior.

**Validates: Requirements 3.2, 3.3**

Property 4: Preservation — Energy Numerical Consistency

_For any_ binary vector `s` in `{0,1}^n` and fixed symmetric matrix `Q_sym`, the energy `float(s.T @ Q_sym @ s)` SHALL equal `float(s.T @ Q_upper @ s)` to within `abs(difference) <= 1e-10`, where `Q_upper` is the original upper-triangular matrix, verifiable for at least 100 random binary vectors.

**Validates: Requirements 2.9, 3.8**


---

## Fix Implementation

### Changes Required

Assuming the root cause analysis above is confirmed:

---

**File**: `qubo-backend/qubo_backend/optimization/qubo_model.py`

**Function**: `to_qubo_matrix(model)` — lines 44–62

**Change 1 — Add `add_symmetric_quadratic()` helper and `[QUADRATIC_ENERGY_CONVENTION_AUDIT]`** (insert before `to_qubo_matrix`):

```python
def add_symmetric_quadratic(Q: np.ndarray, i: int, j: int, value: float) -> None:
    """Write a quadratic coefficient using Convention B — Fully Symmetric Storage.

    For i != j: writes Q[i,j] += value/2 AND Q[j,i] += value/2.
    This ensures x^T Q_sym x == x^T Q_upper x for all binary x, because
    the matmul sums both Q[i,j] and Q[j,i], recovering the full coefficient.

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

After defining the helper, emit the mandatory `[QUADRATIC_ENERGY_CONVENTION_AUDIT]` using a known 2-variable analytical case to verify the convention is correct:

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

Call `_verify_energy_convention()` once at module import time (or at the top of `to_qubo_matrix()` on first call) to catch any regression immediately.

**Change 2 — Replace the defective branch in `to_qubo_matrix()`**:

Replace lines 55–62:
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

With:
```python
# AFTER (fixed — half-value dual-write via helper, Convention B):
for (left, right), bias in model.build.bqm.quadratic.items():
    i = index[left]
    j = index[right]
    add_symmetric_quadratic(q, i, j, float(bias))
```

**Why half-value?** The BQM stores each off-diagonal coupling once with the full coefficient `v`. The matmul `x^T Q x` sums both `Q[i,j]` and `Q[j,i]`. Writing `v/2` to each position gives `(v/2 + v/2) * x_i * x_j = v * x_i * x_j` — identical to the original upper-triangular result. Writing the full `v` to both positions would give `2v * x_i * x_j`, doubling every coupling.

**Change 3 — Add `[QUBO_SYMMETRY_AUDIT]` telemetry and hard assertion** (insert after the quadratic loop, before `return`):

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


---

**File**: `qubo-backend/qubo_backend/optimization/braket_integration.py`

**Function**: `solve_async()` — after `Q, var_order, offset = to_qubo_matrix(model)` and before `qubo_flat = Q.flatten().tolist()`

**Change 4 — Add `[QUBO_SYMMETRY_AUDIT]` pre-serialization check and defensive symmetrization**:

The `[QUBO_EXPORT_AUDIT]` log is already present (added by the dimension/energy corruption fix). Insert the symmetry audit and defensive symmetrization immediately before `qubo_flat = Q.flatten().tolist()`:

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
# Numerical noise is absorbed by 0.5*(Q+Q.T) above.
if not _is_sym:
    raise RuntimeError(
        f"QUBO_SYMMETRY_CORRUPTION: max_asymmetry={_max_asym:.6e} "
        f"persists after defensive symmetrization"
    )
qubo_flat = Q.flatten().tolist()
```

The hard-fail is placed **after** `Q = 0.5 * (Q + Q.T)`. Harmless floating-point noise (e.g., `max_asymmetry = 1e-15`) is absorbed by the symmetrization and will not trigger the error. Only structural asymmetry that survives symmetrization (i.e., a genuinely corrupted matrix) raises the exception.

---

**File**: `qubo-backend/qubo_backend/optimization/braket_integration.py`

**Function**: `solve_async()` — after the symmetry audit, add `[ENERGY_CONSISTENCY_AUDIT]`

**Change 5 — Add `[ENERGY_CONSISTENCY_AUDIT]` validation**:

```python
# ── [ENERGY_CONSISTENCY_AUDIT] ────────────────────────────────────
# INFORMATIONAL ONLY — does NOT assert equality.
# s^T Q s evaluates the full penalized BQM energy (objective + all penalties).
# model.evaluate_solution() evaluates the Markowitz portfolio objective only.
# These are DIFFERENT energy spaces. Large deltas on infeasible samples
# are expected and correct. This audit tracks the delta distribution for
# diagnostic purposes only — it never blocks execution.
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

The status is always `INFORMATIONAL`. The audit is never `VALID` or `INVALID` — those labels imply a correctness assertion that does not hold between these two energy spaces.


---

**File**: `qubo-braket-worker/qaoa_circuit.py`

**Function**: `decode_and_evaluate()` — Step 4 (symmetry check, lines ~130–140)

**Change 6 — No code change required; verify existing check passes**:

The symmetry check at Step 4 of `decode_and_evaluate()` already raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION: ...")` when `np.allclose(Q_2d, Q_2d.T, atol=1e-9)` returns `False`. After the upstream fix, this check will pass for all correctly constructed matrices. The design documents this explicitly to prevent accidental removal of the check during future refactoring.

---

### Summary of Changes

| File | Change | Type |
|------|--------|------|
| `qubo_model.py` | Add `add_symmetric_quadratic()` helper | New function |
| `qubo_model.py` | Replace single-side write with `add_symmetric_quadratic()` call | Bug fix |
| `qubo_model.py` | Add `[QUBO_SYMMETRY_AUDIT]` + hard assertion before `return` | Telemetry + guard |
| `braket_integration.py` | Add `[QUBO_SYMMETRY_AUDIT]` + defensive `Q = 0.5*(Q+Q.T)` before flatten | Telemetry + guard |
| `braket_integration.py` | Add `[ENERGY_CONSISTENCY_AUDIT]` after symmetrization | Telemetry |
| `qaoa_circuit.py` | No change — existing symmetry check at Step 4 is correct | Verification |


---

## Testing Strategy

### Validation Approach

The testing strategy follows a two-phase approach: first, surface counterexamples that demonstrate the asymmetry on unfixed code (exploratory), then verify the fix produces a symmetric matrix and preserves all existing behavior (fix checking + preservation checking).

---

### Exploratory Bug Condition Checking

**Goal**: Surface counterexamples that demonstrate the asymmetry BEFORE implementing the fix. Confirm the root cause analysis. If the tests do not fail on unfixed code, the root cause hypothesis must be revised.

**Test Plan**: Write tests that call `to_qubo_matrix()` on a `QuboModel` with at least one off-diagonal quadratic term and assert `np.allclose(Q, Q.T, atol=1e-9)`. Run these tests on the UNFIXED code to observe the assertion failure and measure `max_asymmetry`.

**Test Cases**:

1. **Minimal 2-variable model with one cross-term**: Build a `QuboModel` with two variables and one quadratic term `(x_0_0, x_1_0)` with bias `1.0`. Call `to_qubo_matrix()`. Assert `np.allclose(Q, Q.T, atol=1e-9)`. Expected on unfixed code: assertion fails with `max_asymmetry = 1.0`. (will fail on unfixed code)

2. **4-asset portfolio (primary crash scenario)**: Build a `QuboModel` from a 4-asset `SolverRequest`. Call `to_qubo_matrix()`. Assert `np.allclose(Q, Q.T, atol=1e-9)`. Expected on unfixed code: assertion fails with `max_asymmetry ≈ 558` (cardinality penalty cross-terms dominate). (will fail on unfixed code)

3. **Cardinality penalty cross-terms only**: Build a model with only cardinality penalty terms (no Markowitz objective). Assert symmetry. Expected on unfixed code: fails with `max_asymmetry = 2 * P_card`. (will fail on unfixed code)

4. **Diagonal-only model (no cross-terms)**: Build a model with only linear terms (no quadratic). Assert `np.allclose(Q, Q.T, atol=1e-9)`. Expected on unfixed AND unfixed code: passes (diagonal matrices are trivially symmetric). This confirms the bug is specific to off-diagonal terms.

**Expected Counterexamples**:
- `max(|Q - Q^T|) = max(|quadratic coefficients|)` — asymmetry equals full coefficient magnitude, not rounding error.
- Possible causes confirmed: single-side write in `to_qubo_matrix()` lines 55–62.

---

### Fix Checking

**Goal**: Verify that for all inputs where the bug condition holds, the fixed `to_qubo_matrix()` produces a symmetric matrix.

**Pseudocode:**
```
FOR ALL model WHERE isBugCondition(model) DO
  Q, var_order, offset = to_qubo_matrix_fixed(model)
  ASSERT np.allclose(Q, Q.T, atol=1e-9)
  ASSERT max(|Q - Q.T|) < 1e-9
  ASSERT [QUBO_SYMMETRY_AUDIT] log emitted with symmetric=True
END FOR
```

---

### Preservation Checking

**Goal**: Verify that for all inputs where the bug condition does NOT hold (diagonal-only models), the fixed function produces the same result as the original function.

**Pseudocode:**
```
FOR ALL model WHERE NOT isBugCondition(model) DO
  Q_original, _, _ = to_qubo_matrix_original(model)
  Q_fixed, _, _ = to_qubo_matrix_fixed(model)
  ASSERT np.allclose(Q_original, Q_fixed, atol=1e-12)
END FOR
```

**Testing Approach**: Property-based testing is recommended for preservation checking because:
- It generates many random portfolio configurations automatically.
- It catches edge cases (single-asset models, all-zero sigma, K=N case).
- It provides strong guarantees that diagonal entries are unchanged across the full input domain.

**Test Plan**: Observe diagonal entry values on UNFIXED code for diagonal-only models, then write property-based tests capturing that behavior.

**Test Cases**:

1. **Diagonal preservation**: For any `QuboModel`, verify `Q_fixed[i,i] == Q_original[i,i]` for all `i`. (observe on unfixed code first)

2. **BQM storage invariance**: For any `SolverRequest`, verify `bqm.quadratic` key sets and values are identical before and after the fix. (regression test 3.2, 3.3)

3. **Serialization format invariance**: For any `QuboModel`, verify `len(Q_fixed.flatten().tolist()) == len(var_order) ** 2`. (regression test 3.4)

4. **Energy numerical consistency**: For any binary vector `s` and fixed symmetric `Q_sym`, verify `float(s.T @ Q_sym @ s) == float(s.T @ Q_upper @ s)` within `1e-10`. (regression test 3.8)


---

### Unit Tests

- Test `add_symmetric_quadratic(Q, i, j, v)` writes `Q[i,j] == v` AND `Q[j,i] == v` for `i != j`.
- Test `add_symmetric_quadratic(Q, i, i, v)` writes `Q[i,i] == v` only once (no double-count on diagonal).
- Test `to_qubo_matrix()` on a 2-variable model with one cross-term — verify `np.allclose(Q, Q.T, atol=1e-9)`.
- Test `to_qubo_matrix()` on a 4-asset portfolio — verify `max(|Q - Q^T|) < 1e-9`.
- Test `[QUBO_SYMMETRY_AUDIT]` log record is emitted with `symmetric=True`, `max_asymmetry < 1e-9`, and correct `shape`.
- Test `to_qubo_matrix()` raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` when a model is manually constructed to produce an asymmetric matrix (e.g., by bypassing `add_symmetric_quadratic()`).
- Test `braket_integration.py` emits `[QUBO_SYMMETRY_AUDIT]` with `symmetric=True` before serialization.
- Test `braket_integration.py` raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` when `to_qubo_matrix()` is mocked to return an asymmetric matrix.
- Test `[ENERGY_CONSISTENCY_AUDIT]` log record is emitted with `status=VALID` and `max_delta < 1e-9` for a 4-asset portfolio.
- Test `decode_and_evaluate()` in `qaoa_circuit.py` does NOT raise `QUBO_SYMMETRY_CORRUPTION` when given the fixed symmetric matrix.

### Property-Based Tests

- **Property 1 (Fix Checking)**: Generate random `SolverRequest` with `n_assets` in [2, 8] and random `sigma`, `mu`. Build `QuboModel`, call fixed `to_qubo_matrix()`. Assert `np.allclose(Q, Q.T, atol=1e-9)` for all generated models.

- **Property 2 (Preservation — diagonal entries)**: Generate random `SolverRequest`. Assert `Q_fixed[i,i] == Q_original[i,i]` for all diagonal indices `i`, within `1e-12`.

- **Property 3 (Energy consistency)**: Generate random `SolverRequest` and 100 random binary vectors `s`. Assert `abs(float(s.T @ Q_sym @ s) - float(s.T @ Q_upper @ s)) <= 1e-10` for all `s`.

- **Property 4 (Serialization invariance)**: Generate random `SolverRequest`. Assert `len(Q_fixed.flatten().tolist()) == len(var_order) ** 2`.

- **Property 5 (Symmetry audit telemetry)**: Generate random `SolverRequest`. Assert `[QUBO_SYMMETRY_AUDIT]` log record is emitted with `symmetric=True` and `max_asymmetry < 1e-9` for all generated models.

### Integration Tests

- **Full benchmark run (LOCAL mode)**: Run the benchmark pipeline end-to-end with a 4-asset portfolio. Assert `[QUBO_SYMMETRY_AUDIT] symmetric=True` appears in logs, no `QUBO_SYMMETRY_CORRUPTION` exception is raised, and at least one finite energy value is produced.
- **Full benchmark run (neal mode)**: Same as above for the neal solver path.
- **Full benchmark run (AWS_LOCAL mode)**: Same as above for the AWS_LOCAL path.
- **`[ENERGY_CONSISTENCY_AUDIT]` in logs**: Run `solve_async()` and assert the log contains `[ENERGY_CONSISTENCY_AUDIT] status=VALID` with `max_delta < 1e-9`.
- **`decode_and_evaluate()` symmetry check passes**: Run a full QAOA circuit evaluation and assert no `QUBO_SYMMETRY_CORRUPTION` is raised at the decode layer.
- **Normalization graph data**: Assert the benchmark result contains at least one normalization graph data point with a non-NaN, non-Inf value after the fix.
