import logging

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution
from qubo_backend.optimization.classical_solver import ClassicalSolver
from qubo_backend.optimization.gpu_solver import GPUSolver
from qubo_backend.optimization.dwave_solver import DWaveSolver
from qubo_backend.optimization.qiskit_solver import QiskitSolver
from qubo_backend.optimization.dwave_sa_solver import NealSASolver, is_neal_sa_available

logger = logging.getLogger(__name__)

# Lazy import for Braket (optional dependency)
_braket_solver = None

def _get_braket_solver():
    global _braket_solver
    if _braket_solver is None:
        try:
            from qubo_backend.optimization.braket_integration import IntegratedBraketSolver
            _braket_solver = IntegratedBraketSolver()
        except ImportError:
            _braket_solver = False  # sentinel: SDK or integration not available
    return _braket_solver if _braket_solver is not False else None


class SolverRouter:
    """
    Smart Solver Router with OOM protection and tiered cascading fallbacks.
    Routes QUBO problems to the most appropriate engine:
      Quantum (D-Wave/Qiskit/Braket) → GPU (Simulated Bifurcation) → Classical (Multi-Strategy)
    """

    def __init__(self):
        self.classical_solver = ClassicalSolver()
        self.gpu_solver = GPUSolver()
        self.dwave_solver = DWaveSolver()
        self.qiskit_solver = QiskitSolver()
        self.neal_sa_solver = NealSASolver() if is_neal_sa_available() else None

    def route(self, request: SolverRequest) -> PortfolioSolution:
        """
        Routes the request through the solver hierarchy with graceful cascading.
        """
        N = len(request.mu)
        
        # [BENCHMARK_MODE_PROPAGATION]
        benchmark_mode = getattr(request, "benchmark_mode", None)
        if benchmark_mode:
            logger.info(f"[BENCHMARK_MODE_PROPAGATION] solver_router mode={benchmark_mode}")
            print(f"[BENCHMARK_MODE_PROPAGATION] solver_router mode={benchmark_mode}")

        try:
            # ── Explicit Quantum Requests ────────────────────────────
            if request.solver in ("qiskit_qaoa", "qiskit", "qiskit_local"):
                sol = self.qiskit_solver.solve(request)
                sol.metadata.actual_solver_used = "Qiskit_QAOA"
                return sol

            if request.solver in ("dwave", "dwave_hybrid", "dwave_qpu", "dwave_local", "hybrid"):
                return self._solve_hybrid_cascade(request, N)

            if request.solver in ("braket", "braket_local", "AWS_BRAKET_TN1", "AWS_BRAKET_SV1", "AWS_BRAKET_DM1", "AWS_BRAKET_LOCAL", "AWS_BRAKET_CLOUD"):
                mode = "cloud_simulator" if request.solver in ("AWS_BRAKET_TN1", "AWS_BRAKET_SV1", "AWS_BRAKET_DM1", "AWS_BRAKET_CLOUD") else "local"
                logger.info(f"[BRAKET_ROUTING_CONVERGENCE] solver={request.solver} execution_mode={mode}")
                print(f"[BRAKET_ROUTING_CONVERGENCE] solver={request.solver} execution_mode={mode}")
                return self._solve_braket(request)

            # ── Neal SA Requests ──────────────────────────────────────
            if request.solver == "neal":
                if self.neal_sa_solver is not None:
                    logger.info("[NEAL_PRIMARY_EXECUTION] Executing Neal SA as primary solver")
                    sol = self.neal_sa_solver.solve(request)
                    sol.metadata.actual_solver_used = "DWave_Neal_Simulated_Annealing"
                    logger.info("[NEAL_PRIMARY_EXECUTION] Neal SA execution completed successfully")
                    return sol
                else:
                    logger.warning("[NEAL_PRIMARY_EXECUTION] Neal SA requested but not available. Falling back to classical.")
                    sol = self.classical_solver.solve(request, solver_name="neal_fallback", fallback_reason="Neal SA not available")
                    sol.metadata.actual_solver_used = "Classical_Multi_Strategy"
                    return sol

            # ── Scale-up / GPU Requests ──────────────────────────────
            if request.solver in ("sb", "gpu") or (request.solver == "auto" and N > 50):
                sol = self.gpu_solver.solve(request)
                sol.metadata.actual_solver_used = "GPU_Simulated_Bifurcation"
                return sol

            # ── Default Classical ────────────────────────────────────
            sol = self.classical_solver.solve(request)
            sol.metadata.actual_solver_used = "Classical_Multi_Strategy"
            return sol

        except Exception as e:
            # [BENCHMARK_TRUTHFULNESS_LOCK]
            # In benchmark mode, silent fallback is a scientific violation.
            # We must fail hard so the benchmarking engine can record the actual failure.
            if getattr(request, "benchmark_mode", None):
                logger.error(f"[SCIENTIFIC_VIOLATION] Solver '{request.solver}' failed in benchmark mode: {e}. Recording failure.")
                from qubo_backend.optimization.portfolio import PortfolioSolution, SolverRunMetadata
                import numpy as np
                n_assets = len(request.mu)
                return PortfolioSolution(
                    weights=np.zeros(n_assets, dtype=float),
                    energy=None,
                    metadata=SolverRunMetadata(
                        solver=request.solver,
                        actual_solver_used=request.solver,
                        bqm_backend="error",
                        qubo_variables=0,
                        linear_terms=0,
                        quadratic_terms=0,
                        solve_time_ms=0.0,
                        execution_status="error",
                        optimization_status="error",
                        error=str(e),
                        scientific_comparability=False
                    )
                )
                
            logger.error(f"Primary solver '{request.solver}' failed: {e}. Cascading...")
            return self._cascade_fallback(request, N, str(e))

    # ── Hybrid Cascade: DWave → Braket → Qiskit → GPU → Classical ──
    def _solve_hybrid_cascade(self, request: SolverRequest, N: int) -> PortfolioSolution:
        errors: list[str] = []

        # 1. Try D-Wave
        try:
            direct_qpu = (request.solver == "dwave_qpu")
            sol = self.dwave_solver.solve(request, direct_qpu=direct_qpu)
            sol.metadata.actual_solver_used = "DWave_Hybrid_Quantum"
            return sol
        except Exception as e:
            errors.append(f"DWave: {e}")
            logger.warning(f"D-Wave failed in hybrid cascade: {e}")

        # 2. Try Braket LocalSimulator
        braket = _get_braket_solver()
        if braket is not None:
            try:
                sol = braket.solve(request)
                sol.metadata.actual_solver_used = "Braket_LocalSimulator_QAOA"
                sol.metadata.fallback_reason = f"D-Wave unavailable. {errors[0] if errors else ''}"
                return sol
            except Exception as e:
                errors.append(f"Braket: {e}")
                logger.warning(f"Braket failed in hybrid cascade: {e}")

        # 3. Try Qiskit
        try:
            sol = self.qiskit_solver.solve(request)
            sol.metadata.actual_solver_used = "Qiskit_QAOA"
            sol.metadata.fallback_reason = f"Upstream solvers unavailable: {'; '.join(errors)}"
            return sol
        except Exception as e:
            errors.append(f"Qiskit: {e}")
            logger.warning(f"Qiskit failed in hybrid cascade: {e}")

        # 4. Try Neal SA (local simulator)
        if self.neal_sa_solver is not None:
            try:
                sol = self.neal_sa_solver.solve(request)
                sol.metadata.actual_solver_used = "DWave_Neal_Simulated_Annealing"
                sol.metadata.fallback_reason = f"Upstream solvers failed: {'; '.join(errors)}"
                return sol
            except Exception as e:
                errors.append(f"Neal SA: {e}")
                logger.warning(f"Neal SA failed in hybrid cascade: {e}")

        # 5. Try GPU (if N > 50)
        if N > 50:
            try:
                sol = self.gpu_solver.solve(
                    request,
                    fallback_reason=f"All quantum solvers failed: {'; '.join(errors)}"
                )
                sol.metadata.actual_solver_used = "GPU_Simulated_Bifurcation"
                return sol
            except Exception as e:
                errors.append(f"GPU: {e}")
                logger.warning(f"GPU failed in hybrid cascade: {e}")

        # 6. Classical safety net
        sol = self.classical_solver.solve(
            request,
            solver_name="classical_fallback",
            fallback_reason=f"All solvers failed: {'; '.join(errors)}"
        )
        sol.metadata.actual_solver_used = "Classical_Multi_Strategy"
        return sol

    def _solve_braket(self, request: SolverRequest) -> PortfolioSolution:
        braket = _get_braket_solver()
        if braket is None:
            logger.warning("Braket solver not available. Falling back to classical.")
            sol = self.classical_solver.solve(
                request,
                fallback_reason="Braket integration is not available"
            )
            sol.metadata.actual_solver_used = "Classical_Multi_Strategy"
            return sol
        
        # The IntegratedBraketSolver handles its own mapping and metadata
        sol = braket.solve(request)
        return sol

    # ── General fallback cascade ────────────────────────────────────
    def _cascade_fallback(self, request: SolverRequest, N: int, error_msg: str) -> PortfolioSolution:
        # Try GPU if large problem
        if N > 50 and request.solver not in ("sb", "gpu"):
            try:
                sol = self.gpu_solver.solve(
                    request,
                    fallback_reason=f"Cascaded to GPU from {request.solver}: {error_msg}"
                )
                sol.metadata.actual_solver_used = "GPU_Simulated_Bifurcation"
                return sol
            except Exception as gpu_e:
                logger.error(f"Secondary GPU solver also failed: {gpu_e}")
                error_msg = f"{error_msg} | GPU fallback: {gpu_e}"

        # Ultimate safety net
        sol = self.classical_solver.solve(
            request,
            solver_name="classical_fallback",
            fallback_reason=f"Cascaded to classical: {error_msg}"
        )
        sol.metadata.actual_solver_used = "Classical_Multi_Strategy"
        return sol


# Singleton instance for API registry integration
smart_router = SolverRouter()


# Compatibility wrapper for benchmark.py (matches source backend API)
def route_and_solve(request: SolverRequest, settings=None) -> PortfolioSolution:
    """Route and solve using the smart router singleton."""
    return smart_router.route(request)
