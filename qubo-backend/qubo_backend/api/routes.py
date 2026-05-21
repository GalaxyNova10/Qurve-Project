from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from math import cos, sin
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, WebSocket, WebSocketDisconnect

import auth

logger = logging.getLogger(__name__)
from .system import router as system_router
from schemas import (
    ConfigDefaultsResponse,
    GPUMetrics,
    HealthResponse,
    HoldingResponse,
    OptimizationTaskResponse,
    PortfolioHoldingsList,
    PortfolioResponse,
    QuboParams,
    BenchmarkParams,
)
from qubo_backend.config import Settings
from qubo_backend.data.alpha import AlphaData, load_alpha_data
from qubo_backend.jobs.store import JobStore
from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import result_to_portfolio_response
from qubo_backend.solvers.registry import available_solvers, solve
from qubo_backend.solvers.benchmark import run_benchmark
from qubo_backend.storage.artifacts import ArtifactStore


def create_api_router(settings: Settings, artifacts: ArtifactStore, job_store: JobStore) -> APIRouter:
    # Ensure artifacts and job_store are Path objects, not strings
    from pathlib import Path
    if isinstance(artifacts, str):
        artifacts = ArtifactStore(Path(artifacts))
    if isinstance(job_store, str):
        job_store = JobStore(Path(job_store))
        
    router = APIRouter()
    telemetry = TelemetryProvider()
    
    # Include system health endpoints
    router.include_router(system_router, prefix="/system", tags=["system"])

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

    @router.get("/bilstm/predictions/indicators")
    async def bilstm_predictions_with_indicators(ticker: str = "NIFTY 50", days: int = 252):
        candles = deterministic_prediction_series(ticker, days)
        indicators = compute_indicators(candles)
        return {"ticker": ticker, "data": candles, "indicators": indicators}


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

    # ── Braket-specific endpoint ────────────────────────────────────
    @router.post("/optimize/braket", response_model=OptimizationTaskResponse)
    async def create_braket_optimization(
        params: QuboParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        _ = current_user
        return _queue_optimization(settings, artifacts, job_store, params, background_tasks, solver_override="braket")

    # ── Benchmark endpoint ──────────────────────────────────────────
    @router.post("/benchmark")
    @router.post("/benchmarks")
    async def benchmark_solvers(
        params: BenchmarkParams,
        background_tasks: BackgroundTasks,
        current_user: auth.User = Depends(auth.get_current_active_user),
    ):
        """Run the same optimization across selected solvers and return comparison."""
        import traceback
        import uuid
        
        try:
            _ = current_user
            request_id = str(uuid.uuid4())
            
            selected_solvers = params.selected_solvers
            execution_mode = params.execution_mode or "LOCAL_ONLY"
            
            logger.info("[BENCHMARK_REQUEST_PAYLOAD] mode=%s execution_mode=%s selected_solvers=%s assets=%s bits=%s request_id=%s", 
                        params.benchmark_mode, execution_mode, selected_solvers, params.num_assets, params.binary_bits, request_id)
            logger.info("[BENCHMARK_START] Starting benchmark with params: %s", params.model_dump())
            
            if selected_solvers:
                logger.info("[SOLVER_SELECTION_AUDIT] selected_solvers=%s execution_mode=%s request_id=%s",
                            selected_solvers, execution_mode, request_id)
            
            # [BENCHMARK_MODE_PROPAGATION]
            logger.info("[BENCHMARK_MODE_PROPAGATION] api_layer mode=%s", params.benchmark_mode)
            
            # Load alpha data (auto-generates if missing)
            alpha = load_alpha_data(settings.output_dir)
            logger.debug("[BENCHMARK_DEBUG] Alpha data loaded successfully")
            
            request = params_to_solver_request({**params.model_dump(), "solver_mode": "classical"}, alpha)
            logger.debug("[BENCHMARK_DEBUG] Solver request created: %s", request.model_dump())
            
            result = await run_benchmark(
                request,
                settings,
                solvers=selected_solvers,
                execution_mode=execution_mode,
                timeout_ms=30000,
                request_id=request_id,
            )
            logger.info("[BENCHMARK_SUCCESS] Benchmark completed successfully request_id=%s", request_id)
            return result
            
        except FileNotFoundError as e:
            logger.error("[BENCHMARK_ERROR] Alpha data missing: %s", str(e))
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Alpha data not found",
                    "message": str(e),
                    "type": "FileNotFoundError"
                }
            )
        except ValueError as e:
            logger.error("[BENCHMARK_ERROR] Data validation failed: %s", str(e))
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid data format",
                    "message": str(e),
                    "type": "ValueError"
                }
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error("[BENCHMARK_ERROR] Benchmark endpoint failed: %s", str(e))
            logger.error("[BENCHMARK_TRACEBACK] %s", traceback.format_exc())
            
            raise HTTPException(
                status_code=500,
                detail={
                    "error": "Benchmark execution failed",
                    "message": "An internal error occurred during benchmark execution",
                    "type": type(e).__name__,
                }
            )

    return router


def create_websocket_router(settings: Settings) -> APIRouter:
    """Separate router for WebSocket endpoints (no /api/v1 prefix)."""
    router = APIRouter()
    telemetry = TelemetryProvider()

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
        payload["requested_solver"] = solver_override
    job = job_store.create(payload)
    background_tasks.add_task(run_optimization_job, settings, artifacts, job_store, job["task_id"])
    return optimization_response(job)


def params_to_solver_request(params: dict[str, Any], alpha: AlphaData) -> SolverRequest:
    requested_solver = str(params.get("requested_solver") or "auto")
    solver_aliases = {
        "ballistic": "sb",
        "adiabatic": "sb",
        "qiskit": "qiskit_qaoa",
        "gpu": "sb",
        "dwave": "dwave_hybrid",
        "auto": "auto",
        "classical": "classical",
        "hybrid": "hybrid",
        "braket": "braket",
        "braket_local": "braket_local",
        "dwave_local": "dwave_local",
        "qiskit_local": "qiskit_local",
    }
    requested_solver = solver_aliases.get(requested_solver, requested_solver)
    allowed = {
        "auto", "gpu", "classical", "sb", "neal",
        "dwave", "dwave_hybrid", "dwave_qpu", "dwave_local",
        "qiskit", "qiskit_qaoa", "qiskit_local",
        "braket", "braket_local",
        "hybrid",
    }
    solver = requested_solver if requested_solver in allowed else "auto"
    
    # Handle asset limiting if num_assets is specified
    num_assets = params.get("num_assets")
    if num_assets is not None and num_assets < len(alpha.tickers):
        import numpy as np
        
        # Take first num_assets assets (simple approach)
        limited_indices = list(range(min(num_assets, len(alpha.tickers))))
        
        mu_limited = np.array(alpha.mu)[limited_indices].tolist()
        sigma_limited = np.array(alpha.sigma)[limited_indices][:, limited_indices].tolist()
        tickers_limited = [alpha.tickers[i] for i in limited_indices]
        sectors_limited = [alpha.sectors[i] for i in limited_indices]
        
        logger.info("[ASSET_LIMITING] Limited dataset from %d to %d assets", 
                   len(alpha.tickers), len(tickers_limited))
        
        return SolverRequest(
            mu=mu_limited,
            sigma=sigma_limited,
            tickers=tickers_limited,
            sectors=sectors_limited,
            cardinality=min(int(params.get("cardinality", 15)), len(tickers_limited)),
            max_sector_exposure=float(params.get("max_sector_exposure", 0.25)),
            risk_tolerance=float(params.get("risk_tolerance", 0.5)),
            binary_bits=int(params.get("binary_bits", 7)),
            solver=solver,  # type: ignore[arg-type]
            trajectories=int(params.get("trajectories", 256) or 256),
            time_limit_seconds=params.get("time_limit_seconds"),
            benchmark_mode=params.get("benchmark_mode"),  # type: ignore[arg-type]
        )
    else:
        # Use full dataset
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
            benchmark_mode=params.get("benchmark_mode"),  # type: ignore[arg-type]
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
    except FileNotFoundError as e:
        job_store.update(task_id, status="failed", progress=100.0, step="Failed", error=f"Alpha data missing: {e}")
    except Exception as exc:
        job_store.update(task_id, status="failed", progress=100.0, step="Failed", error=str(exc))


def deterministic_prediction_series(ticker: str, days: int) -> list[dict[str, Any]]:
    """Generate realistic NIFTY 50-style OHLCV data with multi-harmonic price movement."""
    base = 24500.0 if ticker.upper() == "NIFTY 50" else 2456.8
    seed = sum(ord(char) for char in ticker)
    now = datetime.now()
    rows: list[dict[str, Any]] = []
    price = base
    total_days = max(10, min(days, 1260))

    # Pre-compute a long-term trend direction
    trend = 0.0003  # slight bullish bias (~7.5% annual)

    for offset in range(total_days, 0, -1):
        phase = (seed + offset) / 9.0
        # Multi-harmonic: trend + short cycle + medium cycle + long cycle + noise
        cycle_short = sin(phase * 1.1) * 0.005
        cycle_med = sin(phase * 0.35) * 0.008
        cycle_long = cos(phase * 0.07) * 0.012
        noise = sin(phase * 7.3) * 0.002 + cos(phase * 13.1) * 0.001
        mean_rev = -0.01 * ((price - base) / base)  # mean-reversion pull
        change = trend + cycle_short + cycle_med + cycle_long + noise + mean_rev

        # Gap open simulation (occasional 0.3-0.8% gaps)
        gap = 0.0
        if abs(sin(phase * 3.7)) > 0.92:
            gap = sin(phase * 5.1) * 0.006
        open_price = price * (1 + gap)

        close_price = max(base * 0.6, open_price * (1 + change))

        # Realistic wicks: upper wick + lower wick
        body = abs(close_price - open_price)
        upper_wick = body * (0.3 + abs(sin(phase * 2.3)) * 0.8)
        lower_wick = body * (0.3 + abs(cos(phase * 1.7)) * 0.8)
        high_price = max(open_price, close_price) + upper_wick
        low_price = min(open_price, close_price) - lower_wick

        # Volume: higher on trend days, lower on doji days
        body_pct = abs(change) * 100
        vol_base = 8_000_000 + int(abs(sin(phase * 0.5)) * 12_000_000)
        vol_trend_mult = 1.0 + min(body_pct, 2.0) * 0.5
        volume = int(vol_base * vol_trend_mult)

        rows.append(
            {
                "time": (now - timedelta(days=offset)).strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(high_price, 2),
                "low": round(low_price, 2),
                "close": round(close_price, 2),
                "volume": volume,
                "predicted": False,
            }
        )
        price = close_price

    # Future predicted candles (10 days)
    for offset in range(1, 11):
        phase = (seed + total_days + offset) / 11.0
        change = 0.0004 + sin(phase) * 0.004 + cos(phase * 0.3) * 0.002
        open_price = price
        close_price = max(base * 0.6, price * (1 + change))
        body = abs(close_price - open_price)
        rows.append(
            {
                "time": (now + timedelta(days=offset)).strftime("%Y-%m-%d"),
                "open": round(open_price, 2),
                "high": round(max(open_price, close_price) + body * 0.3, 2),
                "low": round(min(open_price, close_price) - body * 0.3, 2),
                "close": round(close_price, 2),
                "volume": 0,
                "predicted": True,
            }
        )
        price = close_price
    return rows


def compute_indicators(candles: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute technical indicators from OHLCV candle data."""
    closes = [c["close"] for c in candles]
    highs = [c["high"] for c in candles]
    lows = [c["low"] for c in candles]
    volumes = [c["volume"] for c in candles]
    n = len(closes)

    def _sma(data: list[float], period: int) -> list[float | None]:
        result: list[float | None] = [None] * n
        for i in range(period - 1, n):
            result[i] = sum(data[i - period + 1: i + 1]) / period
        return result

    def _ema(data: list[float], period: int) -> list[float | None]:
        result: list[float | None] = [None] * n
        if n < period:
            return result
        k = 2 / (period + 1)
        result[period - 1] = sum(data[:period]) / period
        for i in range(period, n):
            result[i] = data[i] * k + (result[i - 1] or 0) * (1 - k)
        return result

    sma20 = _sma(closes, 20)
    sma50 = _sma(closes, 50)
    ema9 = _ema(closes, 9)
    ema21 = _ema(closes, 21)

    # RSI(14)
    rsi: list[float | None] = [None] * n
    period_rsi = 14
    if n > period_rsi:
        gains = [0.0] * n
        losses = [0.0] * n
        for i in range(1, n):
            diff = closes[i] - closes[i - 1]
            gains[i] = max(diff, 0)
            losses[i] = max(-diff, 0)
        avg_gain = sum(gains[1:period_rsi + 1]) / period_rsi
        avg_loss = sum(losses[1:period_rsi + 1]) / period_rsi
        if avg_loss > 0:
            rsi[period_rsi] = 100 - (100 / (1 + avg_gain / avg_loss))
        else:
            rsi[period_rsi] = 100.0
        for i in range(period_rsi + 1, n):
            avg_gain = (avg_gain * (period_rsi - 1) + gains[i]) / period_rsi
            avg_loss = (avg_loss * (period_rsi - 1) + losses[i]) / period_rsi
            if avg_loss > 0:
                rsi[i] = 100 - (100 / (1 + avg_gain / avg_loss))
            else:
                rsi[i] = 100.0

    # MACD(12,26,9)
    ema12 = _ema(closes, 12)
    ema26 = _ema(closes, 26)
    macd_line: list[float | None] = [None] * n
    for i in range(n):
        if ema12[i] is not None and ema26[i] is not None:
            macd_line[i] = ema12[i] - ema26[i]
    macd_vals = [v if v is not None else 0.0 for v in macd_line]
    signal_line = _ema(macd_vals, 9)
    macd_histogram: list[float | None] = [None] * n
    for i in range(n):
        if macd_line[i] is not None and signal_line[i] is not None:
            macd_histogram[i] = macd_line[i] - signal_line[i]

    # Bollinger Bands(20,2)
    bb_upper: list[float | None] = [None] * n
    bb_lower: list[float | None] = [None] * n
    bb_mid = sma20
    for i in range(19, n):
        window = closes[i - 19: i + 1]
        mean = sum(window) / 20
        std = (sum((x - mean) ** 2 for x in window) / 20) ** 0.5
        bb_upper[i] = mean + 2 * std
        bb_lower[i] = mean - 2 * std

    # VWAP (cumulative)
    vwap: list[float | None] = [None] * n
    cum_tp_vol = 0.0
    cum_vol = 0.0
    for i in range(n):
        tp = (highs[i] + lows[i] + closes[i]) / 3
        cum_tp_vol += tp * volumes[i]
        cum_vol += volumes[i]
        if cum_vol > 0:
            vwap[i] = cum_tp_vol / cum_vol

    # Supertrend(10,3)
    supertrend: list[float | None] = [None] * n
    supertrend_dir: list[int] = [1] * n  # 1=bullish, -1=bearish
    atr_period = 10
    mult = 3.0
    if n > atr_period:
        tr_list = [0.0] * n
        for i in range(1, n):
            tr_list[i] = max(highs[i] - lows[i], abs(highs[i] - closes[i - 1]), abs(lows[i] - closes[i - 1]))
        atr = [0.0] * n
        atr[atr_period] = sum(tr_list[1:atr_period + 1]) / atr_period
        for i in range(atr_period + 1, n):
            atr[i] = (atr[i - 1] * (atr_period - 1) + tr_list[i]) / atr_period

        upper_band = [0.0] * n
        lower_band = [0.0] * n
        for i in range(atr_period, n):
            hl2 = (highs[i] + lows[i]) / 2
            upper_band[i] = hl2 + mult * atr[i]
            lower_band[i] = hl2 - mult * atr[i]

            if i > atr_period:
                if lower_band[i] < lower_band[i - 1] and closes[i - 1] > lower_band[i - 1]:
                    pass
                elif closes[i - 1] > lower_band[i - 1]:
                    lower_band[i] = max(lower_band[i], lower_band[i - 1])

                if upper_band[i] > upper_band[i - 1] and closes[i - 1] < upper_band[i - 1]:
                    pass
                elif closes[i - 1] < upper_band[i - 1]:
                    upper_band[i] = min(upper_band[i], upper_band[i - 1])

            if i == atr_period:
                supertrend_dir[i] = 1 if closes[i] > upper_band[i] else -1
            else:
                prev_dir = supertrend_dir[i - 1]
                if prev_dir == 1 and closes[i] < lower_band[i]:
                    supertrend_dir[i] = -1
                elif prev_dir == -1 and closes[i] > upper_band[i]:
                    supertrend_dir[i] = 1
                else:
                    supertrend_dir[i] = prev_dir

            supertrend[i] = lower_band[i] if supertrend_dir[i] == 1 else upper_band[i]

    def _round_list(lst: list) -> list:
        return [round(v, 2) if v is not None else None for v in lst]

    return {
        "sma20": _round_list(sma20),
        "sma50": _round_list(sma50),
        "ema9": _round_list(ema9),
        "ema21": _round_list(ema21),
        "rsi": _round_list(rsi),
        "macd_line": _round_list(macd_line),
        "macd_signal": _round_list(signal_line),
        "macd_histogram": _round_list(macd_histogram),
        "bb_upper": _round_list(bb_upper),
        "bb_mid": _round_list(bb_mid),
        "bb_lower": _round_list(bb_lower),
        "vwap": _round_list(vwap),
        "supertrend": _round_list(supertrend),
        "supertrend_direction": supertrend_dir,
    }


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
