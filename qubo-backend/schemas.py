from pydantic import BaseModel, field_validator
from typing import Any

VALID_SOLVERS = {
    "classical",
    "neal",
    "AWS_BRAKET_LOCAL",
    "qiskit_qaoa",
    "AWS_BRAKET_SV1",
    "AWS_BRAKET_TN1",
    "AWS_BRAKET_DM1",
}

VALID_EXECUTION_MODES = {
    "LOCAL_ONLY",
    "CLOUD_ONLY",
    "QUANTUM_ONLY",
    "CLASSICAL_ONLY",
    "FULL_STACK",
}

class ConfigDefaultsResponse(BaseModel):
    cardinality: int
    binary_bits: int
    max_sector_exposure: float
    risk_tolerance: float
    solver_mode: str
    trajectories: int

class GPUMetrics(BaseModel):
    utilization: int
    vram_used_mb: int
    vram_total_mb: int
    temperature_c: int
    power_draw_w: float
    cuda_alloc_mb: int
    gpu_name: str
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    gpu_available: bool
    gpu_name: str
    cuda_version: str
    output_dir_exists: bool
    alpha_data_exists: bool
    optimal_weights_exists: bool
    timestamp: str

class HoldingResponse(BaseModel):
    ticker: str
    weight: float
    sector: str

class OptimizationTaskResponse(BaseModel):
    task_id: str
    status: str
    progress: float
    step: str
    result: Any | None = None
    error: str | None = None

class PortfolioHoldingsList(BaseModel):
    holdings: list[HoldingResponse]
    total_assets: int

class PortfolioResponse(BaseModel):
    portfolio: dict[str, Any]
    constraint_verification: dict[str, Any]
    metrics: dict[str, Any] | None = None

class QuboParams(BaseModel):
    num_assets: int | None = None
    cardinality: int | None = None
    max_sector_exposure: float | None = None
    risk_tolerance: float | None = None
    binary_bits: int | None = None
    requested_solver: str | None = None
    trajectories: int | None = None
    time_limit_seconds: int | None = None
    benchmark_mode: str | None = None

class BenchmarkParams(QuboParams):
    benchmark_mode: str
    selected_solvers: list[str] | None = None
    execution_mode: str | None = None

    @field_validator("selected_solvers", mode="before")
    @classmethod
    def validate_solvers(cls, v: list[str] | None) -> list[str] | None:
        if v is None:
            return None
        if len(v) == 0:
            raise ValueError("selected_solvers must not be empty")
        deduped = list(dict.fromkeys(v))
        unknown = [s for s in deduped if s not in VALID_SOLVERS]
        if unknown:
            raise ValueError(f"Unknown solvers: {unknown}. Valid: {sorted(VALID_SOLVERS)}")
        return deduped

    @field_validator("execution_mode", mode="before")
    @classmethod
    def validate_execution_mode(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if v not in VALID_EXECUTION_MODES:
            raise ValueError(f"Unknown execution_mode: {v}. Valid: {sorted(VALID_EXECUTION_MODES)}")
        return v
