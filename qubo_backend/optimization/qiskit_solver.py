import time
import logging
from typing import Any

from qubo_backend.config import get_settings
from qubo_backend.optimization.base_solver import BasePortfolioSolver
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution
from qubo_backend.optimization.qubo_model import build_qubo_model, to_qiskit_quadratic_program
from qubo_backend.solvers.quantum_common import safe_error, solution_from_sample

logger = logging.getLogger(__name__)


def qiskit_status(settings=None) -> str:
    """[QISKIT_DEPENDENCY_VALIDATION] Check if Qiskit and required algorithms are available."""
    try:
        # Check core optimization
        from qiskit_optimization.algorithms import MinimumEigenOptimizer # noqa: F401
        
        # Check required algorithms (Issue 6)
        try:
            from qiskit_algorithms.minimum_eigensolvers import QAOA # noqa: F401
            from qiskit_algorithms.optimizers import COBYLA # noqa: F401
        except ImportError as e:
            logger.warning(f"[QISKIT_DEPENDENCY_VALIDATION] qiskit_algorithms missing: {e}")
            return "not_installed"
            
        return "available"
    except ImportError as e:
        logger.warning(f"[QISKIT_DEPENDENCY_VALIDATION] qiskit_optimization missing: {e}")
        return "not_installed"


def solve_qiskit_qaoa(request: SolverRequest, settings=None) -> PortfolioSolution:
    """Compatibility wrapper for benchmark.py."""
    solver = QiskitSolver()
    return solver.solve(request)


class QiskitSolver(BasePortfolioSolver):
    """
    Qiskit QAOA Simulator.
    Local quantum simulation path, highly constrained to small universes due to exponential complexity.
    """
    
    def solve(self, request: SolverRequest, **kwargs: Any) -> PortfolioSolution:
        settings = get_settings()
        
        # 2. Qiskit QAOA Constraints
        # Hardcode a strict ceiling for the Qiskit solver
        max_assets = settings.qiskit_max_assets if hasattr(settings, 'qiskit_max_assets') else 15
        if len(request.mu) > max_assets:
            raise ValueError(f"Qiskit QAOA is capped to {max_assets} assets for local simulation. Requested: {len(request.mu)}.")
            
        max_bits = settings.qiskit_max_binary_bits if hasattr(settings, 'qiskit_max_binary_bits') else 3
        if request.binary_bits > max_bits:
            raise ValueError(f"Qiskit QAOA is capped to {max_bits} binary bits. Requested: {request.binary_bits}.")
            
        try:
            from qiskit_optimization.algorithms import MinimumEigenOptimizer
            from qiskit_optimization.converters import QuadraticProgramToQubo
        except ImportError:
            raise ImportError("qiskit-optimization is not installed.")
            
        started = time.perf_counter()
        model = build_qubo_model(request)
        
        # Store model reference for qubit count access in _make_qaoa_solver
        self._last_model = model
        
        # Calculate expected qubits and add hard protection
        expected_qubits = len(model.variable_order)
        logger.info(f"[QISKIT_EXECUTION_START] Starting Qiskit QAOA with {expected_qubits} qubits")
        if expected_qubits > 24:
            logger.error(f"[QISKIT_EXECUTION_FAILURE] Qiskit QAOA cannot handle {expected_qubits} qubits (would require >1 TiB memory). Maximum allowed: 24 qubits.")
            raise ValueError(f"Qiskit QAOA cannot handle {expected_qubits} qubits (would require >1 TiB memory). Maximum allowed: 24 qubits.")
        
        try:
            qp = to_qiskit_quadratic_program(model)
            converted = QuadraticProgramToQubo().convert(qp)
            minimum_eigensolver = self._make_qaoa_solver()
            optimizer = MinimumEigenOptimizer(minimum_eigensolver)
            result = optimizer.solve(converted)
            
            # Create explicit mapping from variable names to bit values
            # CRITICAL: decode_sample_to_weights expects STRING keys (variable names), not integer indices
            sample = {name: int(round(float(value))) for name, value in zip(model.variable_order, result.x)}
            
            # [QAOA_BITSTRING_FORENSICS] Validate sample before decoding
            total_bits = sum(sample.values())
            nonzero_vars = sum(1 for v in sample.values() if v > 0)
            logger.info(
                f"[QAOA_BITSTRING_FORENSICS] total_bits={total_bits} nonzero_vars={nonzero_vars} "
                f"sample_size={len(sample)} expected_vars={len(model.variable_order)}"
            )
            
            # [QAOA_VARIABLE_MAP_AUDIT] Verify variable name alignment
            expected_var_names = set(model.variable_order)
            sample_var_names = set(sample.keys())
            if expected_var_names != sample_var_names:
                missing = expected_var_names - sample_var_names
                extra = sample_var_names - expected_var_names
                logger.warning(
                    f"[QAOA_VARIABLE_MAP_AUDIT] mismatch: missing={missing} extra={extra}"
                )
            else:
                logger.info(f"[QAOA_VARIABLE_MAP_AUDIT] variable names aligned correctly")
            
            metadata = {
                "solver": "qiskit_qaoa",
                "provider": "ibm-qiskit",
                "quantum_backend": "local_qaoa",
                "backend_name": type(minimum_eigensolver).__name__,
                "is_qpu": False,
                "is_hybrid": True,
                "energy": float(result.fval) if result.fval is not None else None,
                "solve_time_ms": round((time.perf_counter() - started) * 1000, 3),
                "reads": request.trajectories,
                "qiskit_max_assets": max_assets,
                "qiskit_max_binary_bits": max_bits,
            }
            
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            logger.info(f"[QISKIT_EXECUTION_SUCCESS] Qiskit QAOA completed in {elapsed_ms}ms, energy: {result.fval}")
            
            # 3. Unified Output & Repair
            return solution_from_sample(request, model, sample, "qiskit_qaoa", metadata)
            
        except Exception as exc:
            logger.error(f"[QISKIT_EXECUTION_FAILURE] Qiskit QAOA execution failed: {safe_error(exc)}")
            raise RuntimeError(f"Qiskit QAOA execution failed: {safe_error(exc)}")

    def _make_qaoa_solver(self):
        try:
            from qiskit_aer import AerSimulator
            from qiskit.primitives import Sampler
            from qiskit_algorithms.minimum_eigensolvers import QAOA
            from qiskit_algorithms.optimizers import COBYLA
            from qiskit import QuantumCircuit
            import numpy as np
            
            # Use AerSimulator for better memory management
            # Choose method based on qubit count for optimal performance
            expected_qubits = len(self._last_model.variable_order) if hasattr(self, '_last_model') else 20
            
            if expected_qubits > 20:
                # Use MPS method for large qubit counts (exponentially better)
                aer_sim = AerSimulator(method="matrix_product_state")
            else:
                # Use statevector for smaller problems
                aer_sim = AerSimulator(method="statevector")
                
            sampler = Sampler()
            return QAOA(sampler=sampler, optimizer=COBYLA(maxiter=40), reps=1)
        except ImportError:
            from qiskit_algorithms.minimum_eigensolvers import NumPyMinimumEigensolver
            return NumPyMinimumEigensolver()
