from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from math import cos, sin
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect

import auth
from schemas import (
    ConfigDefaultsResponse,
    GPUMetrics,
    HealthResponse,
    HoldingResponse,
    OptimizationTaskResponse,
    PortfolioHoldingsList,
    PortfolioResponse,
    QuboParams,
)
from qubo_backend.config import Settings
from qubo_backend.data.alpha import AlphaData, load_alpha_data
from qubo_backend.jobs.store import JobStore
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import result_to_portfolio_response
from qubo_backend.solvers.registry import available_solvers, solve
from qubo_backend.storage.artifacts import ArtifactStore


def create_api_router(settings: Settings, artifacts: ArtifactStore, job_store: JobStore) -> APIRouter:
    router = APIRouter()
    telemetry = TelemetryProvider()

    @router.get("/health", response_model=HealthResponse)
    async def health_check():
        metrics = telemetry.get_gpu_metrics()
        return HealthResponse(
            status="ok",
            gpu_available=metrics.gpu_name not in {"No GPU / NVML unavailable", "Unknown"},
            gpu_name=metrics.gpu_name,
            cuda_version=telemetry.cuda_version,
            output_dir_exists=settings.output_dir.exists(),
            alpha_data_exists=artifacts.exists("alpha_data.npz"),
            optimal_weights_exists=artifacts.exists("optimal_weights.json"),
            timestamp=datetime.now().isoformat(),
        )

    @router.get("/config/defaults", response_model=ConfigDefaultsResponse)
    async def config_defaults():
        return ConfigDefaultsResponse(
            cardinality=settings.default_cardinality,
            binary_bits=settings.default_bits,
            max_sector_exposure=settings.default_max_sector,
            risk_tolerance=settings.default_risk_tolerance,
            solver_mode=settings.default_solver,
            trajectories=settings.default_trajectories,
        )

    @router.get("/portfolio/current", response_model=PortfolioResponse)
    async def current_portfolio():
        data = artifacts.read_json("optimal_weights.json")
        if data is None:
            raise HTTPException(status_code=404, detail="No portfolio result found. Run an optimization first.")
        return PortfolioResponse(**data)

    @router.get("/portfolio/holdings", response_model=PortfolioHoldingsList)
    async def portfolio_holdings():
        data = artifacts.read_json("optimal_weights.json")
        if data is None:
            raise HTTPException(status_code=404, detail="No portfolio result found.")
        holdings = [
            HoldingResponse(ticker=ticker, weight=payload["weight"], sector=payload["sector"])
            for ticker, payload in data["portfolio"].items()
        ]
        holdings.sort(key=lambda item: item.weight, reverse=True)
        return PortfolioHoldingsList(holdings=holdings, total_assets=len(holdings))

    @router.get("/gpu/current", response_model=GPUMetrics)
    async def gpu_current():
        return telemetry.get_gpu_metrics()

    @router.get("/bilstm/predictions")
    async def bilstm_predictions(ticker: str = "NIFTY 50", days: int = 60):
        return {"ticker": ticker, "data": deterministic_prediction_series(ticker, days)}

    @router.get("/solvers")
    async def solvers():
        return {"solvers": available_solvers(settings), "default_solver": settings.default_solver}

    @router.get("/datasets")
    async def datasets():
        alpha_exists = artifacts.exists("alpha_data.npz")
        return {
            "datasets": [
                {
                    "id": "nifty50-alpha",
                    "label": "NIFTY 50 alpha/covariance artifact",
                    "available": alpha_exists,
                    "path": str(artifacts.path("alpha_data.npz")),
                    "universe": "NIFTY 50",
                }
            ]
        }

    @router.get("/models")
    async def models():
        checkpoints = sorted(settings.checkpoint_dir.glob("*.pt")) if settings.checkpoint_dir.exists() else []
        return {
            "models": [
                {
                    "id": path.stem,
                    "filename": path.name,
                    "size_mb": round(path.stat().st_size / (1024 * 1024), 3),
                    "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
                }
                for path in checkpoints
            ],
            "checkpoint_dir": str(settings.checkpoint_dir),
        }

    @router.get("/benchmarks")
    async def benchmarks():
        result = artifacts.read_json("optimal_weights.json")
        return {
            "benchmarks": [
                {"id": "equal_weight", "label": "Equal Weight", "available": True},
                {"id": "classical_markowitz", "label": "Classical Markowitz Baseline", "available": False},
                {"id": "latest_qubo", "label": "Latest QUBO Run", "available": result is not None},
            ]
        }

    @router.post("/optimizations", response_model=OptimizationTaskResponse)
    async def create_optimization(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        _ = current_user
        return _queue_optimization(settings, artifacts, job_store, params, background_tasks)

    @router.post("/optimize/classical", response_model=OptimizationTaskResponse)
    async def optimize_classical(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        _ = current_user
        return _queue_optimization(settings, artifacts, job_store, params, background_tasks, solver_override="classical")

    @router.post("/optimize/dwave", response_model=OptimizationTaskResponse)
    async def optimize_dwave(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        _ = current_user
        return _queue_optimization(settings, artifacts, job_store, params, background_tasks, solver_override="dwave_hybrid")

    @router.post("/optimize/qiskit", response_model=OptimizationTaskResponse)
    async def optimize_qiskit(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        _ = current_user
        return _queue_optimization(settings, artifacts, job_store, params, background_tasks, solver_override="qiskit_qaoa")

    @router.post("/optimize/hybrid", response_model=OptimizationTaskResponse)
    async def optimize_hybrid(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        _ = current_user
        return _queue_optimization(settings, artifacts, job_store, params, background_tasks, solver_override="hybrid")

    @router.get("/optimizations/{task_id}", response_model=OptimizationTaskResponse)
    async def optimization_status(task_id: str):
        job = job_store.get(task_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Optimization job not found")
        return optimization_response(job)

    @router.get("/optimizations/{task_id}/result", response_model=PortfolioResponse)
    async def optimization_result(task_id: str):
        job = job_store.get(task_id)
        if job is None:
            raise HTTPException(status_code=404, detail="Optimization job not found")
        if job["status"] != "complete" or not job.get("result"):
            raise HTTPException(status_code=409, detail=f"Optimization is {job['status']}")
        return PortfolioResponse(**job["result"])

    # Backward-compatible endpoints consumed by the current frontend.
    @router.post("/optimize", response_model=OptimizationTaskResponse)
    async def legacy_create_optimization(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        return await create_optimization(params, background_tasks, current_user)

    @router.get("/optimize/{task_id}", response_model=OptimizationTaskResponse)
    async def legacy_optimization_status(task_id: str):
        return await optimization_status(task_id)

    @router.websocket("/ws/gpu-telemetry")
    async def gpu_telemetry_ws(ws: WebSocket):
        await ws.accept()
        try:
            while True:
                await ws.send_json(telemetry.get_gpu_metrics().model_dump())
                await asyncio.sleep(1)
        except WebSocketDisconnect:
            return

    return router


def optimization_response(job: dict[str, Any]) -> OptimizationTaskResponse:
    result = PortfolioResponse(**job["result"]) if job.get("result") else None
    return OptimizationTaskResponse(
        task_id=job["task_id"],
        status=job["status"],
        progress=job.get("progress", 0.0),
        step=job.get("step", ""),
        result=result,
        error=job.get("error"),
    )


def _queue_optimization(
    settings: Settings,
    artifacts: ArtifactStore,
    job_store: JobStore,
    params: QuboParams,
    background_tasks: BackgroundTasks,
    solver_override: str | None = None,
) -> OptimizationTaskResponse:
    payload = params.model_dump()
    if solver_override is not None:
        payload["solver_mode"] = solver_override
    job = job_store.create(payload)
    background_tasks.add_task(run_optimization_job, settings, artifacts, job_store, job["task_id"])
    return optimization_response(job)


def params_to_solver_request(params: dict[str, Any], alpha: AlphaData) -> SolverRequest:
    solver_mode = str(params.get("solver_mode") or "sb")
    solver_aliases = {
        "ballistic": "sb",
        "adiabatic": "sb",
        "qiskit": "qiskit_qaoa",
    }
    solver_mode = solver_aliases.get(solver_mode, solver_mode)
    allowed = {"classical", "sb", "neal", "dwave_hybrid", "dwave_qpu", "qiskit_qaoa", "hybrid"}
    solver = solver_mode if solver_mode in allowed else "sb"
    return SolverRequest(
        mu=alpha.mu.tolist(),
        sigma=alpha.sigma.tolist(),
        tickers=alpha.tickers,
        sectors=alpha.sectors,
        cardinality=int(params.get("cardinality", 15)),
        max_sector_exposure=float(params.get("max_sector_exposure", 0.25)),
        risk_tolerance=float(params.get("risk_tolerance", 0.5)),
        binary_bits=int(params.get("binary_bits", 7)),
        solver=solver,  # type: ignore[arg-type]
        trajectories=int(params.get("trajectories", 256) or 256),
        time_limit_seconds=params.get("time_limit_seconds"),
    )


def run_optimization_job(settings: Settings, artifacts: ArtifactStore, job_store: JobStore, task_id: str) -> None:
    try:
        job_store.update(task_id, status="running", progress=10.0, step="Loading alpha artifact")
        alpha = load_alpha_data(settings.output_dir)

        job_store.update(task_id, progress=35.0, step="Building QUBO/BQM model")
        job = job_store.get(task_id)
        if job is None:
            raise RuntimeError("Job disappeared before execution")
        request = params_to_solver_request(job["params"], alpha)

        job_store.update(task_id, progress=60.0, step=f"Solving with {request.solver}")
        solution = solve(request, settings)
        result = result_to_portfolio_response(request, solution)

        if not result["constraint_verification"]["all_satisfied"]:
            raise RuntimeError(f"Infeasible result rejected: {result['constraint_verification']}")

        job_store.update(task_id, progress=90.0, step="Persisting result")
        # Save task-specific result
        artifacts.write_json(f"result_{task_id}.json", result)
        # Update global latest safely
        artifacts.write_json("optimal_weights.json", result, safe=True)
        job_store.update(task_id, status="complete", progress=100.0, step="Done", result=result, error=None)
    except Exception as exc:
        job_store.update(task_id, status="failed", progress=100.0, step="Failed", error=str(exc))


def deterministic_prediction_series(ticker: str, days: int) -> list[dict[str, Any]]:
    base = 22500.0 if ticker.upper() == "NIFTY 50" else 2456.8
    seed = sum(ord(char) for char in ticker)
    now = datetime.now()
    rows: list[dict[str, Any]] = []
    price = base
    total_days = max(10, min(days, 365))
    for offset in range(total_days, 0, -1):
        phase = (seed + offset) / 9.0
        change = 0.0002 + sin(phase) * 0.006 + cos(phase / 2.5) * 0.003
        open_price = price
        close_price = max(1.0, price * (1 + change))
        spread = abs(sin(phase)) * 0.008
        rows.append(
            {
                "time": (now - timedelta(days=offset)).strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(max(open_price, close_price) * (1 + spread), 2),
                "low": round(min(open_price, close_price) * (1 - spread), 2),
                "close": round(close_price, 2),
                "volume": int(1_000_000 + (abs(sin(phase)) * 4_000_000)),
                "predicted": False,
            }
        )
        price = close_price
    for offset in range(1, 11):
        phase = (seed + total_days + offset) / 11.0
        change = 0.0004 + sin(phase) * 0.003
        open_price = price
        close_price = max(1.0, price * (1 + change))
        rows.append(
            {
                "time": (now + timedelta(days=offset)).strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(max(open_price, close_price) * 1.004, 2),
                "low": round(min(open_price, close_price) * 0.996, 2),
                "close": round(close_price, 2),
                "volume": 0,
                "predicted": True,
            }
        )
        price = close_price
    return rows


class TelemetryProvider:
    def __init__(self) -> None:
        self.cuda_version = ""
        self._torch = None
        self._pynvml = None
        self._gpu_handle = None
        self._gpu_name = "No GPU / NVML unavailable"
        try:
            import torch

            self._torch = torch
            if torch.cuda.is_available():
                self.cuda_version = torch.version.cuda or ""
        except (ImportError, OSError):
            self._torch = None
        try:
            import pynvml

            self._pynvml = pynvml
            pynvml.nvmlInit()
            self._gpu_handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            name = pynvml.nvmlDeviceGetName(self._gpu_handle)
            self._gpu_name = name.decode("utf-8") if isinstance(name, bytes) else str(name)
        except Exception:
            self._pynvml = None
            self._gpu_handle = None

    def get_gpu_metrics(self) -> GPUMetrics:
        timestamp = datetime.now().isoformat()
        if self._pynvml is None or self._gpu_handle is None:
            return GPUMetrics(
                utilization=0,
                vram_used_mb=0,
                vram_total_mb=0,
                temperature_c=0,
                power_draw_w=0.0,
                cuda_alloc_mb=0,
                gpu_name=self._gpu_name,
                timestamp=timestamp,
            )
        try:
            util = self._pynvml.nvmlDeviceGetUtilizationRates(self._gpu_handle)
            mem = self._pynvml.nvmlDeviceGetMemoryInfo(self._gpu_handle)
            temp = self._pynvml.nvmlDeviceGetTemperature(self._gpu_handle, self._pynvml.NVML_TEMPERATURE_GPU)
            power = self._pynvml.nvmlDeviceGetPowerUsage(self._gpu_handle) / 1000
            cuda_alloc = 0
            if self._torch is not None and self._torch.cuda.is_available():
                cuda_alloc = int(self._torch.cuda.memory_allocated() // (1024**2))
            return GPUMetrics(
                utilization=int(util.gpu),
                vram_used_mb=int(mem.used // (1024**2)),
                vram_total_mb=int(mem.total // (1024**2)),
                temperature_c=int(temp),
                power_draw_w=round(float(power), 1),
                cuda_alloc_mb=cuda_alloc,
                gpu_name=self._gpu_name,
                timestamp=timestamp,
            )
        except Exception as exc:
            return GPUMetrics(
                utilization=0,
                vram_used_mb=0,
                vram_total_mb=0,
                temperature_c=0,
                power_draw_w=0.0,
                cuda_alloc_mb=0,
                gpu_name=f"Telemetry error: {exc}",
                timestamp=timestamp,
            )
