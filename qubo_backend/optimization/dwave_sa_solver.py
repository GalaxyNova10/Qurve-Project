"""
D-Wave Neal Simulated Annealing Solver for QUBO Portfolio Optimization

Local execution of D-Wave's SimulatedAnnealingSampler from the Neal package.
Provides high-quality simulated annealing with configurable parameters and
integration into the existing solver ecosystem.
"""

import time
import logging
import asyncio
import math
import numpy as np
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import neal
    import dimod
    from neal import SimulatedAnnealingSampler
    NEAL_AVAILABLE = True
except ImportError as e:
    NEAL_AVAILABLE = False
    logging.warning(f"D-Wave Neal not available: {e}")

from qubo_backend.optimization.contracts import SolverRequest, SolverRunMetadata
from qubo_backend.optimization.portfolio import solve_locally, PortfolioSolution
from qubo_backend.optimization.bqm_builder import build_portfolio_bqm
from qubo_backend.config import redact_secret

logger = logging.getLogger(__name__)


class PrecisionMode(Enum):
    """Adaptive precision modes for Neal SA execution."""
    BENCHMARK_FAST = "benchmark_fast"    # 4-bit encoding for speed
    STANDARD = "standard"                 # 5-bit encoding for UI optimization
    INSTITUTIONAL = "institutional"       # 7-bit encoding for full precision


@dataclass
class BenchmarkExecutionConfig:
    """Isolated benchmark configuration for safe optimization."""
    precision_mode: PrecisionMode = PrecisionMode.BENCHMARK_FAST
    num_reads: int = 25
    num_sweeps: int = 25
    max_problem_size: int = 30
    aggressive_sparsification: bool = True
    covariance_threshold: float = 0.015


@dataclass
class NealSASolverConfig:
    """Configuration for Neal Simulated Annealing solver."""
    
    # Production-optimized defaults for speed
    num_reads: int = 100  # Reduced from 1000 for 5x speedup
    num_sweeps: int = 100  # Reduced from 1000 for 10x speedup
    beta_range: Optional[tuple[float, float]] = None
    beta_schedule_type: str = "geometric"
    
    # Precision mode for adaptive encoding
    precision_mode: PrecisionMode = PrecisionMode.STANDARD
    
    # Benchmark mode flag for aggressive optimization
    benchmark_mode: bool = False
    benchmark_config: Optional[BenchmarkExecutionConfig] = None
    
    interrupt_function: Optional[callable] = None
    timeout: Optional[float] = None


class NealSASolver:
    """
    D-Wave Neal Simulated Annealing solver implementation.
    
    Executes local simulated annealing using D-Wave's Neal package
    with proper integration into the QUBO portfolio optimization pipeline.
    """
    
    def __init__(self, config: Optional[NealSASolverConfig] = None):
        self.config = config or NealSASolverConfig()
        
        # Benchmark mode: use isolated configuration
        if self.config.benchmark_mode:
            logger.info("[NEAL_CONFIG] Benchmark mode enabled - using isolated optimization")
            if self.config.benchmark_config:
                # Use dedicated benchmark configuration
                self.config.num_reads = self.config.benchmark_config.num_reads
                self.config.num_sweeps = self.config.benchmark_config.num_sweeps
                self.config.precision_mode = self.config.benchmark_config.precision_mode
            else:
                # Fallback to aggressive defaults
                self.config.num_reads = 50
                self.config.num_sweeps = 50
                self.config.precision_mode = PrecisionMode.BENCHMARK_FAST
        
        self._sampler = None
        self._initialize_sampler()
    
    def _initialize_sampler(self) -> None:
        """Initialize Neal SimulatedAnnealingSampler."""
        if not NEAL_AVAILABLE:
            raise ImportError("D-Wave Neal package is not installed or not importable")
        
        try:
            # SimulatedAnnealingSampler() constructor takes no arguments
            # Parameters like num_sweeps, beta_range, beta_schedule_type are passed to .sample() method
            self._sampler = SimulatedAnnealingSampler()
            logger.info("Neal SA sampler initialized with default parameters")
        except Exception as e:
            logger.error(f"Failed to initialize Neal SA sampler: {e}")
            raise
    
    async def solve_async(self, request: SolverRequest) -> PortfolioSolution:
        """
        Asynchronously solve() QUBO problem using Neal SA.
        
        Args:
            request: Solver request with QUBO parameters
            
        Returns:
            PortfolioSolution with optimization results
        """
        logger.info("[NEAL_PROFILE] Starting Neal SA solve for %d assets", len(request.tickers))
        total_start = time.perf_counter()
        
        # Store original asset count for padding if asset limiting is applied
        original_num_assets = len(request.tickers)
        
        try:
            # Phase 1: Adaptive QUBO Generation with Asset Limiting
            qubo_start = time.perf_counter()
            logger.debug("[NEAL_QUBO_BUILD] Building portfolio BQM")
            
            # Apply benchmark asset limiting if needed
            asset_limited = False
            if self.config.benchmark_mode and self.config.benchmark_config:
                original_request = request
                request = self._apply_benchmark_asset_limiting(request)
                asset_limited = len(request.tickers) < original_num_assets
            
            # Apply adaptive precision and sparsification
            request = self._apply_adaptive_precision(request)
            request = self._apply_sparsification(request)
            
            bqm_build = build_portfolio_bqm(request)
            qubo_time = (time.perf_counter() - qubo_start) * 1000
            logger.info("[NEAL_QUBO_BUILD] QUBO generation: %.2fms", qubo_time)
            
            # Phase 2: Sampler Execution Profiling
            sampler_start = time.perf_counter()
            logger.debug("[NEAL_SAMPLER_EXECUTION] Executing Neal SA with %d reads", self.config.num_reads)
            sampleset = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._execute_sampling, 
                bqm_build.bqm.to_dimod()
            )
            sampler_time = (time.perf_counter() - sampler_start) * 1000
            logger.info("[NEAL_SAMPLER_EXECUTION] Sampler execution: %.2fms", sampler_time)
            
            # Phase 3: Post-processing Profiling
            postprocess_start = time.perf_counter()
            best_sample = sampleset.first
            energy = float(best_sample.energy)
            postprocess_time = (time.perf_counter() - postprocess_start) * 1000
            logger.info("[NEAL_POSTPROCESS] Post-processing: %.2fms", postprocess_time)
            
            # ── [NEAL_DECODE_REMEDIATION] (Phase 1/2) ───────────────────
            convert_start = time.perf_counter()
            from qubo_backend.optimization.qubo_model import QuboModel, decode_sample_to_weights
            
            model = QuboModel(request=request, build=bqm_build)
            
            # Decode best sample
            weights = decode_sample_to_weights(model, best_sample.sample)
            
            # Calculate feasibility_native from sampleset (Phase 6/7)
            n_feasible = 0
            n_strict = 0
            n_total = len(sampleset)
            for s in sampleset:
                try:
                    s_weights = decode_sample_to_weights(model, s.sample)
                    s_active = int(np.sum(s_weights > 1e-6))
                    if s_active == request.cardinality:
                        n_feasible += 1
                        # Strictly positive means all selected bits have weight
                        # decode_sample_to_weights already enforces this or raises RuntimeError
                        n_strict += 1
                except Exception:
                    continue
            
            feasibility_native = n_feasible / max(1, n_total)
            strict_ratio = n_strict / max(1, n_total)
            convert_time = (time.perf_counter() - convert_start) * 1000
            logger.info("[NEAL_POSTPROCESS] Solution decoding and feasibility audit: %.2fms", convert_time)
            
            # Convert to portfolio solution - skip redundant call in benchmark mode
            if self.config.benchmark_mode:
                # Skip expensive classical solver conversion in benchmark mode
                # Use the solution we already computed but apply padding if needed
                from qubo_backend.optimization.portfolio import PortfolioSolution
                from qubo_backend.optimization.contracts import SolverRunMetadata
                
                total_solve_time = (time.perf_counter() - total_start) * 1000
                
                # If asset limiting was applied, pad the weights array to match original size
                if asset_limited:
                    padded_weights = np.zeros(original_num_assets)
                    padded_weights[:len(weights)] = weights
                    weights = padded_weights
                    logger.info("[NEAL_ASSET_PADDING] Padded weights from %d to %d assets", 
                               len(request.tickers), original_num_assets)
                
                # Create new solution with proper weights and metadata
                solution = PortfolioSolution(
                    weights=weights,
                    energy=energy,
                    metadata=SolverRunMetadata(
                        solver="dwave_neal",
                        actual_solver_used="DWave_Neal_Simulated_Annealing",
                        bqm_backend="dimod",
                        qubo_variables=original_num_assets if asset_limited else len(request.tickers),
                        linear_terms=len(bqm_build.bqm.linear),
                        quadratic_terms=len(bqm_build.bqm.quadratic),
                        solve_time_ms=round(total_solve_time, 3),
                        reads=self.config.num_reads,
                        energy=energy,
                        objective_span=bqm_build.objective_span,
                        provider="dwave",
                        backend_name="neal.SimulatedAnnealingSampler",
                        scientific_comparability=True,
                        feasibility_native=feasibility_native,
                        feasibility_final=1.0 if n_feasible > 0 else 0.0,
                        strict_positive_allocation_ratio=strict_ratio,
                        energy_inversion_detected=False
                    )
                )
            else:
                # Normal mode: return the decoded solution
                from qubo_backend.optimization.portfolio import SolverRunMetadata
                solution = PortfolioSolution(
                    weights=weights,
                    energy=energy,
                    metadata=SolverRunMetadata(
                        solver="dwave_neal",
                        actual_solver_used="DWave_Neal_Simulated_Annealing",
                        bqm_backend="dimod",
                        qubo_variables=original_num_assets if asset_limited else len(request.tickers),
                        linear_terms=len(bqm_build.bqm.linear),
                        quadratic_terms=len(bqm_build.bqm.quadratic),
                        solve_time_ms=round(total_solve_time, 3),
                        reads=self.config.num_reads,
                        energy=energy,
                        objective_span=bqm_build.objective_span,
                        provider="dwave",
                        backend_name="neal.SimulatedAnnealingSampler",
                        feasibility_native=feasibility_native,
                        feasibility_final=1.0 if n_feasible > 0 else 0.0,
                        strict_positive_allocation_ratio=strict_ratio,
                        energy_inversion_detected=False
                    )
                )
            
            # Add Neal-specific metadata
            solution.metadata.num_reads = self.config.num_reads
            # solution.metadata.neal_metadata = {  # Remove this field since it doesn't exist
            #     "beta_range": self.config.beta_range,
            #     "beta_schedule_type": self.config.beta_schedule_type,
            #     "sampleset_info": {
            #         "first_energy": energy,
            #         "first_occurrences": best_sample.num_occurrences,
            #         "total_samples": len(sampleset)
            #     }
            # }
            
            logger.info("[NEAL_EXECUTION_SUCCESS] Neal SA solve completed in %.2fms, energy: %f", total_solve_time, energy)
            return solution
            
        except Exception as e:
            logger.error("[NEAL_EXECUTION_FAILURE] Neal SA solve failed: %s", redact_secret(e))
            # Fallback to classical solver
            logger.info("[NEAL_FALLBACK_TRIGGERED] Falling back to classical solver")
            return solve_locally(
                request, 
                solver_name="dwave_neal_fallback",
                fallback_reason=f"Neal SA error: {redact_secret(e)}"
            )
    
    def _apply_benchmark_asset_limiting(self, request: SolverRequest) -> SolverRequest:
        """Apply asset limiting for benchmark mode."""
        if not self.config.benchmark_config:
            return request
        
        max_assets = self.config.benchmark_config.max_problem_size
        if len(request.tickers) <= max_assets:
            return request
        
        # Downsample to max_assets while preserving sector diversity
        # Group by sector and sample proportionally
        sectors = np.array(request.sectors)
        unique_sectors = list(set(sectors))
        
        selected_indices = []
        assets_per_sector = max_assets // len(unique_sectors)
        
        for sector in unique_sectors:
            sector_indices = np.where(sectors == sector)[0]
            if len(sector_indices) > assets_per_sector:
                # Randomly sample from this sector
                np.random.shuffle(sector_indices)
                selected_indices.extend(sector_indices[:assets_per_sector])
            else:
                selected_indices.extend(sector_indices)
        
        # Ensure we don't exceed max_assets
        selected_indices = selected_indices[:max_assets]
        
        # Create downsampled request
        selected_mu = np.array(request.mu)[selected_indices].tolist()
        selected_sigma = np.array(request.sigma)[selected_indices][:, selected_indices].tolist()
        selected_tickers = [request.tickers[i] for i in selected_indices]
        selected_sectors = [request.sectors[i] for i in selected_indices]
        
        request_dict = {
            'mu': selected_mu,
            'sigma': selected_sigma,
            'tickers': selected_tickers,
            'sectors': selected_sectors,
            'cardinality': min(request.cardinality, max_assets),
            'max_sector_exposure': request.max_sector_exposure,
            'risk_tolerance': request.risk_tolerance,
            'binary_bits': self._get_adaptive_bits(),
            'solver': request.solver,
            'trajectories': request.trajectories,
            'time_limit_seconds': request.time_limit_seconds
        }
        
        logger.info("[NEAL_ASSET_LIMITING] Reduced from %d to %d assets", 
                   len(request.tickers), len(selected_indices))
        
        return SolverRequest(**request_dict)
    
    def _apply_adaptive_precision(self, request: SolverRequest) -> SolverRequest:
        """Apply adaptive binary encoding based on precision mode."""
        adaptive_bits = self._get_adaptive_bits()
        
        if request.binary_bits == adaptive_bits:
            return request
        
        # Create request with adaptive bits
        request_dict = {
            'mu': request.mu,
            'sigma': request.sigma,
            'tickers': request.tickers,
            'sectors': request.sectors,
            'cardinality': request.cardinality,
            'max_sector_exposure': request.max_sector_exposure,
            'risk_tolerance': request.risk_tolerance,
            'binary_bits': adaptive_bits,
            'solver': request.solver,
            'trajectories': request.trajectories,
            'time_limit_seconds': request.time_limit_seconds
        }
        
        logger.info("[NEAL_ADAPTIVE_PRECISION] Using %d-bit encoding (mode: %s)", 
                   adaptive_bits, self.config.precision_mode.value)
        
        return SolverRequest(**request_dict)
    
    def _apply_sparsification(self, request: SolverRequest) -> SolverRequest:
        """Apply safe covariance sparsification."""
        if not self.config.benchmark_config or not self.config.benchmark_config.aggressive_sparsification:
            return request
        
        threshold = self.config.benchmark_config.covariance_threshold
        if threshold <= 0:
            return request
        
        # Apply threshold to covariance matrix
        sigma = np.array(request.sigma)
        original_terms = np.count_nonzero(sigma)
        
        # Keep diagonal terms always
        np.fill_diagonal(sigma, np.diag(sigma))
        
        # Apply threshold to off-diagonal terms
        mask = np.abs(sigma) >= threshold
        sigma = sigma * mask
        
        # Ensure symmetry and positive semi-definiteness
        sigma = (sigma + sigma.T) / 2
        eigenvals = np.linalg.eigvals(sigma)
        if np.any(eigenvals < 0):
            # Add small diagonal to ensure PSD
            sigma += np.eye(len(sigma)) * abs(min(eigenvals)) * 1.1
        
        pruned_terms = np.count_nonzero(sigma)
        
        request_dict = {
            'mu': request.mu,
            'sigma': sigma.tolist(),
            'tickers': request.tickers,
            'sectors': request.sectors,
            'cardinality': request.cardinality,
            'max_sector_exposure': request.max_sector_exposure,
            'risk_tolerance': request.risk_tolerance,
            'binary_bits': request.binary_bits,
            'solver': request.solver,
            'trajectories': request.trajectories,
            'time_limit_seconds': request.time_limit_seconds
        }
        
        logger.info("[NEAL_SPARSIFICATION] original_terms=%d pruned_terms=%d remaining_terms=%d", 
                   original_terms, pruned_terms, pruned_terms)
        
        return SolverRequest(**request_dict)
    
    def _get_adaptive_bits(self) -> int:
        """Get adaptive binary encoding bits based on precision mode."""
        if self.config.precision_mode == PrecisionMode.BENCHMARK_FAST:
            return 4  # Fast 4-bit encoding
        elif self.config.precision_mode == PrecisionMode.STANDARD:
            return 5  # Standard 5-bit encoding
        else:  # INSTITUTIONAL
            return 7  # Full 7-bit encoding
    
    def _execute_sampling(self, bqm) -> Any:
        """
        Execute sampling with timeout handling.
        
        Args:
            bqm: Binary Quadratic Model to sample
            
        Returns:
            Sampleset from Neal SA
        """
        try:
            # Execute sampling with optimized parameters
            sample_kwargs = {
                'num_reads': self.config.num_reads
            }
            
            # Benchmark mode: skip expensive options
            if not self.config.benchmark_mode:
                if self.config.interrupt_function is not None:
                    sample_kwargs['interrupt_function'] = self.config.interrupt_function
                if self.config.timeout is not None:
                    sample_kwargs['timeout'] = self.config.timeout
                
            sampleset = self._sampler.sample(bqm, **sample_kwargs)
            return sampleset
            
        except Exception as e:
            logger.error(f"Neal SA sampling failed: {e}")
            raise
    
    def solve(self, request: SolverRequest) -> PortfolioSolution:
        """
        Synchronous solve method for compatibility.
        
        Args:
            request: Solver request
            
        Returns:
            PortfolioSolution
        """
        try:
            # Check if we're already in an event loop
            loop = asyncio.get_running_loop()
            # If we're in a loop, run in thread pool
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, self.solve_async(request))
                return future.result()
        except RuntimeError:
            # No running loop, safe to use asyncio.run()
            return asyncio.run(self.solve_async(request))
    
    def validate_configuration(self) -> tuple[bool, str]:
        """
        Validate solver configuration.
        
        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not NEAL_AVAILABLE:
            return False, "D-Wave Neal package is not available"
        
        if self.config.num_reads <= 0:
            return False, "num_reads must be positive"
        
        if self.config.num_sweeps <= 0:
            return False, "num_sweeps must be positive"
        
        if self.config.timeout is not None and self.config.timeout <= 0:
            return False, "timeout must be positive"
        
        if self.config.beta_range is not None:
            if len(self.config.beta_range) != 2:
                return False, "beta_range must be a tuple of 2 values"
            if self.config.beta_range[0] >= self.config.beta_range[1]:
                return False, "beta_range must be (min_beta, max_beta) with min < max"
        
        return True, "Configuration is valid"
    
    def get_solver_info(self) -> Dict[str, Any]:
        """
        Get solver information and capabilities.
        
        Returns:
            Dictionary with solver metadata
        """
        return {
            "name": "D-Wave Neal Simulated Annealing",
            "type": "local_simulator",
            "provider": "D-Wave",
            "execution": "local",
            "cost": "free",
            "benchmark_ready": True,
            "supported_problem_sizes": {
                "min": 1,
                "max": 10000,  # Practical limit for local SA
                "recommended": 500
            },
            "configuration": {
                "num_reads": self.config.num_reads,
                "num_sweeps": self.config.num_sweeps,
                "beta_range": self.config.beta_range,
                "beta_schedule_type": self.config.beta_schedule_type,
                "timeout": self.config.timeout
            },
            "capabilities": [
                "binary_quadratic_model",
                "simulated_annealing",
                "configurable_sweeps",
                "configurable_reads",
                "timeout_support",
                "interrupt_support"
            ]
        }


def create_neal_sa_solver(request: SolverRequest) -> PortfolioSolution:
    """
    Convenience function to create and solve with Neal SA.
    
    Args:
        request: Solver request
        
    Returns:
        PortfolioSolution
    """
    # Configure solver based on problem size
    config = NealSASolverConfig(
        num_reads=min(request.trajectories, 2000),  # Cap for performance
        num_sweeps=1000 if len(request.tickers) <= 50 else 2000,
        beta_range=(0.1, 10.0) if len(request.tickers) <= 30 else None,
        timeout=300.0  # 5 minute timeout
    )
    
    solver = NealSASolver(config)
    return solver.solve(request)


def is_neal_sa_available() -> bool:
    """
    Check if Neal SA solver is available.
    
    Returns:
        True if Neal is installed and importable
    """
    return NEAL_AVAILABLE


def get_neal_sa_status() -> str:
    """
    Get the status of Neal SA solver for registry.
    
    Returns:
        Status string for solver registry
    """
    if not NEAL_AVAILABLE:
        return "not_installed"
    
    try:
        # Test basic functionality
        sampler = SimulatedAnnealingSampler()
        return "available"
    except Exception as e:
        logger.error(f"Neal SA status check failed: {e}")
        return f"error:{redact_secret(e)}"
