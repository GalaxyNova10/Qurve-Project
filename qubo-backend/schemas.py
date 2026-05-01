from pydantic import BaseModel
from typing import Any

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
    cardinality: int | None = None
    max_sector_exposure: float | None = None
    risk_tolerance: float | None = None
    binary_bits: int | None = None
    solver_mode: str | None = None
    trajectories: int | None = None
    time_limit_seconds: int | None = None
