# Bugfix Requirements Document

## Introduction

The benchmark engine crashes during post-processing energy evaluation with a `ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 (size 256 is different from 16)`. This occurs in `decode_and_evaluate()` inside `qubo-braket-worker/qaoa_circuit.py` when the function attempts to compute `s @ Q @ s` to evaluate the QUBO energy of a measurement bitstring.

The root cause is a dimension mismatch between the sample vector `s` (shape `(n,)` where `n = n_qubits`) and the QUBO matrix `Q` retrieved from `req_meta["qubo_matrix"]`. The QUBO matrix is stored in `req_meta` as a flat Python list of length `n_qubits²` (e.g., 256 elements for 16 qubits). When `np.array(req_meta.get("qubo_matrix"))` is called without reshaping, NumPy produces a 1-D array of shape `(n_qubits²,)` rather than the required `(n_qubits, n_qubits)` matrix. The subsequent `s @ Q @ s` operation then fails because the inner dimensions do not align.

This is a classical post-processing defect — the quantum execution itself completes successfully. The fix must restore correct `(n, n)` QUBO matrix shape in the decode layer without altering any quantum operator, Hamiltonian, or statevector representation.

## Bug Analysis

### Current Behavior (Defect)

1.1 WHEN `decode_and_evaluate()` retrieves `Q = req_meta.get("qubo_matrix")` and converts it with `np.array(Q)` THEN the system produces a 1-D array of shape `(n_qubits²,)` — where `n_qubits` is the integer square root of `len(Q)` — instead of a 2-D matrix of shape `(n_qubits, n_qubits)`; this is verifiable by asserting `np.array(Q).ndim == 1` and `len(np.array(Q)) == n_qubits ** 2` before any reshape

1.2 WHEN the energy computation `float(s @ Q @ s)` is executed with `s.shape == (n,)` and `Q.shape == (n²,)` (e.g., `n=16`, `n²=256`) THEN the system raises `ValueError` with a message indicating a core-dimension mismatch between the two operands; the exception is raised by NumPy's matmul and is not caught within `decode_and_evaluate()`

1.3 WHEN the `ValueError` is raised inside `decode_and_evaluate()` THEN the function does not return a tuple; the exception propagates to the caller (`run_qaoa_optimized()`) and the benchmark run terminates without producing any energy value, feasible-ratio value, or normalization output for that execution

1.4 WHEN `req_meta["qubo_matrix"]` is populated in `braket_integration.py` THEN the stored value is a flat Python list of `n_qubits²` floats that carries no shape metadata (no `.shape` attribute, no `(rows, cols)` tuple); the decode layer receives only the flat list and is solely responsible for reconstruction, which it currently does not perform

1.5 WHEN the dimension mismatch occurs THEN no log record containing both the sample dimension and the Q dimension is emitted before the crash; specifically, no log line with fields `sample_dim`, `qubo_dim`, and `status` is written to the logger at any level prior to the exception

### Expected Behavior (Correct)

2.1 WHEN `decode_and_evaluate()` retrieves `Q = req_meta.get("qubo_matrix")` THEN the system SHALL produce a 2-D NumPy array of shape `(n_qubits, n_qubits)` with `dtype=float64` before any matrix operation; the resulting array SHALL satisfy `Q_2d.ndim == 2`, `Q_2d.shape[0] == Q_2d.shape[1]`, and `Q_2d.shape[0] == n_qubits`

2.2 WHEN the energy computation `float(s @ Q @ s)` is executed with `s.shape == (n_qubits,)` and `Q.shape == (n_qubits, n_qubits)` THEN the system SHALL complete without raising any exception and SHALL return a finite scalar float (i.e., `math.isfinite(energy) == True`)

2.3 WHEN `decode_and_evaluate()` is about to perform the matmul THEN the system SHALL verify that `s` is 1-D, that `Q` is square, and that `Q.shape[0] == len(s)`; if any of these conditions is false, the system SHALL raise an error with a message containing the string `"QUBO_DIMENSION_CORRUPTION"` and SHALL NOT proceed to the matmul

2.4 WHEN the dimension checks in 2.3 all pass THEN the system SHALL emit a log record at INFO level containing the fields `sample_dim=<n>`, `qubo_dim=<n>`, `hilbert_dim=<2^n>`, and `status=VALID` before computing the energy; this record SHALL be emitted on every call to `decode_and_evaluate()` that reaches the matmul

2.5 WHEN `build_portfolio_bqm()` exports the QUBO matrix THEN the system SHALL emit a log record at INFO level containing the fields `binary_variables=<n>`, `qubo_shape=(<n>, <n>)`, and `hilbert_dimension=<2^n>`; the logged `qubo_shape` SHALL equal `(n_binary_variables, n_binary_variables)` — not `(2^n, 2^n)` — confirming the matrix is in binary-variable space

2.6 WHEN the benchmark completes successfully THEN the system SHALL produce: (a) at least one finite energy value per execution mode (LOCAL, neal, AWS_LOCAL), (b) a feasible ratio strictly greater than 0.0 for at least one execution mode, (c) normalization graph data containing at least one data point, and (d) zero matmul-related exceptions in the run log

2.7 WHEN `decode_and_evaluate()` receives a `qubo_matrix` value that cannot be reshaped into a square `(n_qubits, n_qubits)` array (e.g., length is not `n_qubits²`, or the value is `None` after the Q-is-not-None guard) THEN the system SHALL raise an error with a message containing `"QUBO_DIMENSION_CORRUPTION"` and SHALL NOT silently skip energy evaluation or substitute a default energy value

2.8 WHEN `decode_and_evaluate()` reconstructs the QUBO matrix from the flat serialized list THEN the system SHALL verify `len(flat_qubo) == n_qubits * n_qubits` BEFORE executing the reshape; IF `len(flat_qubo) != n_qubits * n_qubits` THEN the system SHALL raise `RuntimeError("QUBO_SERIALIZATION_CORRUPTION")` and SHALL NOT truncate, pad, infer dimensions, or auto-correct the malformed matrix in any way

2.9 WHEN the QUBO matrix is reconstructed inside `decode_and_evaluate()` THEN the system SHALL verify `np.allclose(Q, Q.T, atol=1e-9)`; IF symmetry validation fails THEN the system SHALL raise `RuntimeError("QUBO_SYMMETRY_CORRUPTION")` and SHALL NOT proceed to energy evaluation; this check SHALL run after reshape and before the dimension assertions in 2.3

2.10 WHEN the flat serialized QUBO list is reshaped into matrix form THEN the system SHALL emit a log record at INFO level with the fields `flat_length=<n²>`, `reconstructed_shape=(<n>,<n>)`, `expected_shape=(<n>,<n>)`, `symmetric=<True|False>`, `dtype=<dtype>`, and `status=<VALID|CORRUPT>`; for a valid 16-qubit case the record SHALL read `[QUBO_RECONSTRUCTION_AUDIT] flat_length=256 reconstructed_shape=(16,16) expected_shape=(16,16) symmetric=True dtype=float64 status=VALID`

2.11 WHEN `decode_and_evaluate()` retrieves `offset = req_meta.get("qubo_offset", 0.0)` THEN the system SHALL verify `isinstance(offset, (int, float, np.floating))`; IF the type check fails THEN the system SHALL raise `RuntimeError("QUBO_OFFSET_CORRUPTION: offset is not a numeric type")` and SHALL NOT proceed to energy evaluation; additionally, the system SHALL verify `math.isfinite(offset)`; IF `math.isfinite(offset)` is False THEN the system SHALL raise `RuntimeError("QUBO_OFFSET_CORRUPTION: offset is not finite")` and SHALL NOT proceed to energy evaluation; these checks prevent NaN propagation, string serialization bugs, malformed JSON payloads, and silent infinite energies

### Unchanged Behavior (Regression Prevention)

3.1 WHEN `decode_and_evaluate()` receives a `qubo_matrix` that is already a correctly shaped `(n_qubits, n_qubits)` 2-D array THEN the system SHALL compute `float(s @ Q @ s) + offset` and return that scalar as the energy component of its return tuple, with no other transformation applied

3.2 WHEN the quantum circuit execution (QAOA, Hadamard, or cloud) runs THEN the system SHALL produce measurement counts and statevector outputs that are bit-for-bit identical to those produced before this fix; the fix SHALL NOT alter any `Circuit`, quantum operator, or statevector object

3.3 WHEN `to_qubo_matrix()` in `qubo_model.py` constructs the binary-variable QUBO matrix THEN the system SHALL return a 2-D array whose first dimension equals the number of BQM variables `n` (not `2^n`); this is verifiable by asserting `Q.shape == (n_vars, n_vars)` on the return value

3.4 WHEN `braket_integration.py` serializes the QUBO matrix for the worker HTTP request THEN the system SHALL send a flat list of `n_qubits × n_qubits` floats (i.e., `len(flat_list) == n_qubits ** 2`); the serialization format SHALL NOT change as a result of this fix

3.5 WHEN `bqm_energy()` and `model.evaluate_solution()` are called in the feasibility filter THEN the system SHALL return energy values that match the reference BQM variable-space computation to within floating-point tolerance (`abs(result - reference) < 1e-9`)

3.6 WHEN the Hadamard fallback path is triggered (no QUBO matrix provided in `req_meta`) THEN the system SHALL return a non-empty list of bitstring measurement results and SHALL NOT raise any dimension-related exception

3.7 WHEN `run_qaoa_optimized()` calls `decode_and_evaluate()` iteratively during COBYLA optimization THEN every call SHALL return a 2-tuple `(avg_energy, feasible_ratio)` where both elements are finite floats (`math.isfinite(avg_energy) == True` and `math.isfinite(feasible_ratio) == True`), enabling the optimizer to continue without interruption

3.8 WHEN `decode_and_evaluate()` computes `energy = float(s.T @ Q @ s) + offset` for any sample THEN the result SHALL match the reference BQM evaluation `model.evaluate_solution(sample)` to within `abs(energy_decode - energy_reference) < 1e-9` for all regression test cases; this guarantees the reconstructed matrix is numerically correct, not merely dimensionally correct
