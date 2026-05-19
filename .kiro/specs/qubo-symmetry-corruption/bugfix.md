# Bugfix Requirements Document

## Introduction

The benchmark engine detects a mathematically invalid QUBO matrix during construction:

```
QUBO_SYMMETRY_CORRUPTION: QUBO matrix is not symmetric (max asymmetry=5.589827e+02)
```

A max asymmetry of ~558 is not numerical noise — it is a severe structural defect in quadratic coefficient injection during QUBO matrix construction. A valid QUBO requires `Q = Q^T` because energy evaluation is `E(s) = s^T Q s`. An asymmetric QUBO produces an undefined optimization topology and must be rejected before any solver receives it.

The root cause is in `to_qubo_matrix()` in `qubo-backend/qubo_backend/optimization/qubo_model.py`. The function builds an upper-triangular matrix: for every off-diagonal quadratic term `(left, right)` it writes only to `q[i,j]` when `i <= j` and only to `q[j,i]` when `i > j` — it never mirrors the coefficient to both positions. The result is a matrix where `Q[i,j] != 0` but `Q[j,i] == 0` for all off-diagonal terms, producing asymmetry equal to the full magnitude of every quadratic coefficient.

Additionally, `bqm_builder.py` injects quadratic terms through `PortfolioBQM.add_quadratic()`, which canonicalizes pairs via `_ordered_pair()` and stores each coupling once. When `to_qubo_matrix()` reads these pairs and writes only to the upper or lower triangle, the resulting matrix is structurally half-populated. The fix must ensure every off-diagonal write is mirrored symmetrically, and that a hard symmetry assertion gates all downstream usage.

## Bug Analysis

### Current Behavior (Defect)

1.1 IF `to_qubo_matrix()` processes an off-diagonal quadratic term `(left, right)` with bias `v` and variable indices `i < j` THEN the system writes `q[i,j] += v` but does NOT write `q[j,i] += v`, leaving position `(j,i)` equal to `0.0` for that term

1.2 IF `to_qubo_matrix()` processes an off-diagonal quadratic term `(left, right)` with bias `v` and variable indices `i > j` THEN the system writes `q[j,i] += v` but does NOT write `q[i,j] += v`, leaving position `(i,j)` equal to `0.0` for that term

1.3 WHEN `to_qubo_matrix()` returns the QUBO matrix `Q` THEN the system returns a structurally upper-triangular matrix where `Q[i,j] != Q[j,i]` for every off-diagonal term, producing `max(|Q - Q^T|)` equal to the maximum quadratic coefficient magnitude (observed: `5.589827e+02`)

1.4 IF `decode_and_evaluate()` in `qubo-braket-worker/qaoa_circuit.py` receives the asymmetric QUBO matrix and `np.allclose(Q, Q.T, atol=1e-9)` returns `False` THEN the system raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` with `max_asymmetry=5.589827e+02`, halting execution before any solver receives the invalid matrix

1.5 IF `decode_and_evaluate()` in `qubo-braket-worker/qaoa_circuit.py` receives the asymmetric QUBO matrix and `np.allclose(Q, Q.T, atol=1e-9)` returns `False` THEN the system raises `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` and does not proceed to energy evaluation

1.6 IF the asymmetric QUBO is used in energy evaluation `E(s) = s^T Q s` with a binary vector `s` where `s_i = s_j = 1` at an off-diagonal term with bias `v` THEN the upper-triangular convention produces energy contribution `v * s_i * s_j` while the symmetric convention produces `2 * v * s_i * s_j`, a measurable difference of exactly `2 * v * s_i * s_j` that makes solver comparisons between the two conventions invalid

### Expected Behavior (Correct)

2.1 WHEN `to_qubo_matrix()` processes an off-diagonal quadratic term `(left, right)` with bias `v` and variable indices `i != j` THEN the system SHALL write `q[i,j] += v` AND `q[j,i] += v` so that both symmetric positions carry the full coefficient

2.2 WHEN `to_qubo_matrix()` returns the QUBO matrix `Q` THEN the system SHALL return a fully symmetric matrix satisfying `np.allclose(Q, Q.T, atol=1e-9)` with `max(|Q - Q^T|) < 1e-9`

2.3 WHEN `to_qubo_matrix()` completes construction THEN the system SHALL emit a `[QUBO_SYMMETRY_AUDIT]` log record at INFO level containing `shape=<(n,n)>`, `max_asymmetry=<float>`, `frobenius_asymmetry=<float>`, and `symmetric=<True|False>` before returning

2.4 WHEN the `[QUBO_SYMMETRY_AUDIT]` record reports `max_asymmetry >= 1e-9` THEN the system SHALL raise `RuntimeError("QUBO_SYMMETRY_CORRUPTION: max_asymmetry=<value>")` and SHALL NOT return the matrix to any caller

2.5 WHEN `to_qubo_matrix()` returns a valid symmetric matrix THEN the system SHALL also emit a `[QUBO_EXPORT_AUDIT]` log record containing `binary_variables=<n>`, `qubo_shape=(<n>,<n>)`, and `hilbert_dimension=<2^n>` confirming the matrix is in binary-variable space

2.6 IF any code path attempts a direct asymmetric write `Q[i,j] += value` without a corresponding `Q[j,i] += value` for `i != j` THEN the system SHALL raise `RuntimeError("ASYMMETRIC_WRITE_FORBIDDEN: direct write at ({i},{j}) without mirror")` to enforce that all quadratic writes route through the canonical `add_symmetric_quadratic(Q, i, j, value)` helper

2.7 WHEN `braket_integration.py` invokes `Q.flatten().tolist()` to serialize the QUBO matrix THEN the system SHALL first verify `np.allclose(Q, Q.T, atol=1e-9)` and emit `[QUBO_EXPORT_AUDIT] shape=<> symmetric=<> max_asymmetry=<> flattened_length=<>`; IF `max_asymmetry >= 1e-9` THEN the system SHALL raise `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` and SHALL NOT serialize the matrix

2.8 WHEN `decode_and_evaluate()` in `qubo-braket-worker/qaoa_circuit.py` reconstructs the QUBO matrix from the flat serialized list THEN the system SHALL verify `np.allclose(Q, Q.T, atol=1e-9)` and raise `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` if the check fails

2.9 WHEN the energy consistency audit runs after the fix THEN the system SHALL emit `[ENERGY_CONSISTENCY_AUDIT] samples=<n> max_delta=<float> mean_delta=<float> status=INFORMATIONAL` for at least 100 randomized binary `{0,1}` sample vectors; the status SHALL always be `INFORMATIONAL` because `s^T Q s` evaluates the full penalized BQM energy while `model.evaluate_solution()` evaluates the Markowitz portfolio objective — these are different energy spaces and equality is not expected or asserted

2.10 WHEN the benchmark completes successfully after the fix THEN the system SHALL produce: (a) `[QUBO_SYMMETRY_AUDIT] symmetric=True` with `max_asymmetry` a non-NaN, non-Inf float less than `1e-9` in logs, (b) `[ENERGY_CONSISTENCY_AUDIT] status=VALID` in logs, (c) at least one non-NaN, non-Inf energy value per operational execution mode (AWS_LOCAL, classical, neal, SV1), (d) at least one feasible ratio value in `[0.0, 1.0]`, and (e) at least one normalization graph data point with a non-NaN, non-Inf value

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `to_qubo_matrix()` processes a diagonal term for variable `var` with bias `b` THEN the system SHALL write `q[index[var], index[var]] += b` and the resulting diagonal entry SHALL equal the sum of all linear biases for `var` in `bqm.linear`, verifiable by asserting `q[i,i] == sum(bqm.linear[var] for var with index[var]==i)`

3.2 WHEN `PortfolioBQM.add_quadratic(left, right, bias)` is called THEN the system SHALL store the pair in `bqm.quadratic` under the key returned by `_ordered_pair(left, right)` with the bias argument value without modification, verifiable by asserting `bqm.quadratic[_ordered_pair(left, right)] == bias` immediately after the call

3.3 WHEN `build_portfolio_bqm()` constructs the Markowitz objective, cardinality penalty, linkage penalty, budget penalty, and sector penalty terms THEN the system SHALL produce a `bqm.linear` dict and `bqm.quadratic` dict whose key sets and values are identical to those produced before this fix, verifiable by asserting `set(bqm.linear.keys()) == expected_linear_keys` and `set(bqm.quadratic.keys()) == expected_quadratic_keys` with matching values within `1e-12`

3.4 WHEN `braket_integration.py` serializes the QUBO matrix THEN the system SHALL produce a flat Python list of exactly `n_vars * n_vars` floats, verifiable by asserting `len(flat_list) == n_vars ** 2` and `isinstance(flat_list, list)` and `all(isinstance(x, float) for x in flat_list)`

3.5 WHEN `decode_and_evaluate()` in `qubo-braket-worker/qaoa_circuit.py` receives the flat serialized QUBO and reshapes it to `(n_qubits, n_qubits)` THEN the system SHALL perform the reshape, length validation, and symmetry check; the symmetry check SHALL pass (i.e., `np.allclose(Q, Q.T, atol=1e-9)` returns `True`) because the upstream matrix is correctly symmetric after this fix, verifiable by asserting no `QUBO_SYMMETRY_CORRUPTION` exception is raised

3.6 WHEN `bqm_energy(model.build, int_sample)` and `model.evaluate_solution(sample)` are called in the feasibility filter THEN the system SHALL return energy values that match the values returned before this fix to within `1e-12`, verifiable by asserting `abs(energy_after - energy_before) < 1e-12` for identical inputs

3.7 WHEN the Hadamard fallback path is triggered (no QUBO matrix provided in `req_meta`) THEN the system SHALL return a 2-tuple `(avg_energy, feasible_ratio)` where both values are non-NaN, non-Inf floats and `0.0 <= feasible_ratio <= 1.0`, with no `QUBO_SYMMETRY_CORRUPTION` or dimension-related exception raised

3.8 WHEN `to_qubo_matrix()` returns the fixed symmetric matrix `Q_sym` for a BQM with quadratic terms THEN for any binary vector `s` in `{0,1}^n`, the energy `float(s.T @ Q_sym @ s)` SHALL equal `float(s.T @ Q_upper @ s)` to within `abs(difference) <= 1e-10`, where `Q_upper` is the original upper-triangular matrix, verifiable by asserting this bound holds for all `s` in a test suite of at least 100 random binary vectors
