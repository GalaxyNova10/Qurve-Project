from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator


SolverName = Literal["classical", "sb", "neal", "dwave_hybrid", "dwave_qpu", "qiskit", "qiskit_qaoa", "hybrid"]


class SolverRequest(BaseModel):
    mu: list[float]
    sigma: list[list[float]]
    tickers: list[str]
    sectors: list[str]
    cardinality: int = Field(default=15, ge=1, le=50)
    max_sector_exposure: float = Field(default=0.25, ge=0.05, le=1.0)
    risk_tolerance: float = Field(default=0.5, ge=0.0, le=10.0)
    binary_bits: int = Field(default=7, ge=2, le=10)
    solver: SolverName = "sb"
    trajectories: int = Field(default=256, ge=1, le=4096)
    time_limit_seconds: int | None = Field(default=None, ge=1, le=3600)

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
    bqm_backend: str
    qubo_variables: int
    linear_terms: int
    quadratic_terms: int
    solve_time_ms: float
    reads: int | None = None
    time_limit_seconds: int | None = None
    energy: float | None = None
    chain_break_fraction: float | None = None
    fallback_reason: str | None = None
    quantum_backend: str | None = None
    provider: str | None = None
    backend_name: str | None = None
    is_qpu: bool | None = None
    is_hybrid: bool | None = None
    qiskit_max_assets: int | None = None
    qiskit_max_binary_bits: int | None = None
    eligibility_reason: str | None = None
