from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


SolverName = Literal[
    "auto", "gpu", "classical", "sb", "neal",
    "dwave", "dwave_hybrid", "dwave_qpu", "dwave_local",
    "qiskit", "qiskit_qaoa", "qiskit_local",
    "braket", "braket_local",
    "hybrid",
    "AWS_BRAKET_TN1", "AWS_BRAKET_SV1", "AWS_BRAKET_LOCAL", "AWS_BRAKET_CLOUD", "AWS_BRAKET_DM1"
]

BenchmarkMode = Literal[
    "FAST", "BALANCED", "RESEARCH", "STRESS", "CLOUD_ONLY", "DETERMINISTIC",
    "benchmark_fast", "benchmark_balanced", "benchmark_accuracy"
]

class ExecutionProvenance(BaseModel):
    requested_solver: str
    actual_solver: str
    execution_origin: str
    repair_used: bool = False
    fallback_triggered: bool = False
    benchmark_mode: str | None = None

class BenchmarkFingerprint(BaseModel):
    semantic_version: str = "v1.0"
    portfolio_hash: str
    covariance_hash: str
    constraint_hash: str
    solver_config_hash: str
    normalization_version: str = "v1.0"

class OperationalCertification(BaseModel):
    status: Literal["CERTIFIED", "DEGRADED", "FAILED"]
    latency_ok: bool
    reliability_ok: bool
    stability_ok: bool
    reason: str | None = None

class ScientificCertification(BaseModel):
    status: Literal["CERTIFIED", "RESEARCH_GRADE", "UX_GRADE", "NON_COMPARABLE", "STRONG_CONVERGENCE"]
    feasibility_ok: bool
    approximation_ok: bool
    decode_integrity_ok: bool
    comparability_ok: bool
    reason: str | None = None

class SolverRequest(BaseModel):
    mu: list[float]
    sigma: list[list[float]]
    tickers: list[str]
    sectors: list[str]
    cardinality: int = Field(default=15, ge=1, le=50)
    max_sector_exposure: float = Field(default=0.25, ge=0.05, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=10.0)
    binary_bits: int = Field(default=7, ge=2, le=10)
    solver: SolverName = "auto"
    trajectories: int = Field(default=256, ge=1, le=4096)
    time_limit_seconds: int | None = Field(default=None, ge=1, le=3600)
    warm_start_params: list[float] | None = None
    warm_start_weights: list[float] | None = None
    warm_start_energy: float | None = None

class QuantumExecutionProfile(BaseModel):
    shots: int
    depth: int
    mixer_type: str
    density: float
    entanglement_width: float
    projected_cost: float
    projected_memory: str
    scientific_mode: str
    benchmark_mode: BenchmarkMode | None = None

class BenchmarkRequest(SolverRequest):
    benchmark_mode: BenchmarkMode = Field(..., description="Benchmark mode is mandatory for scientific integrity")

    @field_validator("sigma")
    @classmethod
    def validate_sigma(cls, value: list[list[float]]) -> list[list[float]]:
        if not value:
            raise ValueError("sigma must not be empty")
        width = len(value[0])
        if any(len(row) != width for row in value):
            raise ValueError("sigma must be rectangular")
        return value

    @field_validator("tickers", "sectors")
    @classmethod
    def validate_non_empty(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("list must not be empty")
        return value


class SolverRunMetadata(BaseModel):
    solver: str
    actual_solver_used: str | None = None
    bqm_backend: str | None = None
    qubo_variables: int | None = None
    linear_terms: int | None = None
    quadratic_terms: int | None = None
    solve_time_ms: float | None = None
    reads: int | None = None
    num_reads: int | None = None
    time_limit_seconds: int | None = None
    energy: float | None = None
    objective_span: float | None = None
    chain_break_fraction: float | None = None
    fallback_reason: str | None = None
    quantum_backend: str | None = None
    provider: str | None = None
    backend_name: str | None = None
    is_qpu: bool | None = None
    is_hybrid: bool | None = None
    qiskit_max_assets: int | None = None
    qiskit_max_binary_bits: int | None = None
    braket_max_assets: int | None = None
    braket_max_binary_bits: int | None = None
    strategy: str | None = None
    eligibility_reason: str | None = None
    
    # Execution Status
    execution_status: str = "success"
    optimization_status: str = "success"
    scientific_comparability: bool = True
    degraded_scientific_mode: bool = False
    error: str | None = None
    
    # Cloud Convergence Metadata
    execution_origin: str | None = None
    fallback_triggered: bool = False
    task_arn: str | None = None
    device_arn: str | None = None
    execution_mode: str | None = None
    
    worker_state: str | None = None
    
    # Feasibility diagnostics
    feasibility_native: float | None = None
    feasibility_final: float | None = None
    strict_positive_allocation_ratio: float | None = None
    selection_entropy: float | None = None
    energy_gap_ratio: float | None = None
    approximation_ratio: float | None = None
    manifold_stability_score: float | None = None
    decode_rejection_rate: float | None = None
    constraint_violation_norm: float | None = None
    energy_variance: float | None = None
    convergence_slope: float | None = None
    effective_coupling_degree: float | None = None
    graph_treewidth_estimate: float | None = None
    tensor_contraction_complexity: float | None = None
    projected_cost_usd: float | None = None
    energy_inversion_detected: bool | None = None
    qaoa_depth: int | None = None
    adaptive_shots: int | None = None
    penalty_scale: float | None = None
    best_energy: float | None = None
    avg_energy: float | None = None
    energy_std: float | None = None
    
    # Phase 5: Decoder Trace
    repair_trace: list[str] = Field(default_factory=list)
    
    # Phase 12: Quantum Runtime Realism
    energy_landscape_entropy: float | None = None
    barren_plateau_risk: float | None = None
    parameter_concentration: float | None = None
    sample_diversity: float | None = None
    effective_hilbert_exploration: float | None = None
    bitstring_entropy: float | None = None
    
    fallback_chain: list[str] = Field(default_factory=list)

class AllocationValidationResult(BaseModel):
    feasible: bool
    leakage_detected: bool
    normalization_valid: bool
    budget_valid: bool
    sector_valid: bool
    selected_count: int
    allocation_sum: float
    violations: list[str] = Field(default_factory=list)

