import logging
import uuid
from typing import Any, Dict
from qubo_backend.events import event_bus
from qubo_backend.storage.db import AsyncSessionLocal
from qubo_backend.storage.portfolio_state_manager import PortfolioStateManager

logger = logging.getLogger(__name__)

async def handle_optimization_completed(data: Dict[str, Any]):
    logger.info(f"Received OptimizationCompleted event for request_id: {data.get('request_id')}")
    
    request_id = data.get("request_id")
    if not request_id:
        request_id = str(uuid.uuid4())

    summary = data.get("summary", {})
    best_solver = summary.get("best_solver", "unknown")
    best_energy = summary.get("best_energy", 0.0)
    total_time = summary.get("total_benchmark_time_ms", 0.0)
    benchmark_status = summary.get("benchmark_status", "UNKNOWN")
    feasible_count = summary.get("feasible_solutions", 0)
    total_solvers = summary.get("total_solvers_attempted", 1)
    
    feasible_ratio = feasible_count / total_solvers if total_solvers > 0 else 0.0
    strict_ratio = feasible_ratio # This can be improved by actually reading strict successes
    
    # Extract the best result
    results = data.get("results", [])
    best_result = None
    if best_solver != "unknown":
        for r in results:
            if r.get("solver") == best_solver:
                best_result = r
                break
    elif results:
        best_result = results[0]
        
    if not best_result:
        logger.warning("No best result found, cannot persist Portfolio allocations")
        return

    metrics = best_result.get("metrics") or {}
    total_return = metrics.get("expected_return", 0.0)
    volatility = metrics.get("volatility", 0.0)
    sharpe = metrics.get("sharpe_ratio", 0.0)
    
    allocations_raw = best_result.get("selected_assets", [])
    allocations = []
    
    # We might need sector or risk contribution, for now we map asset and weight
    for asset_dict in allocations_raw:
        allocations.append({
            "asset": asset_dict.get("asset", "unknown"),
            "weight": asset_dict.get("weight", 0.0),
            "sector": asset_dict.get("sector"),
            "expected_return": asset_dict.get("expected_return"),
            "risk_contribution": asset_dict.get("risk_contribution")
        })

    async with AsyncSessionLocal() as session:
        state_manager = PortfolioStateManager(session)
        
        # 1. Persist OptimizationRun
        run = await state_manager.persist_optimization_run(
            run_id=request_id,
            solver=best_solver,
            execution_time_ms=total_time,
            energy=best_energy,
            strict_ratio=strict_ratio,
            feasible_ratio=feasible_ratio,
            topology_density=summary.get("manifold_health", {}).get("topology_density", 0.0),
            scientific_status=best_result.get("scientific_status", "UNKNOWN"),
            isolation_status=best_result.get("isolation_status", "UNKNOWN")
        )
        
        # 2. Persist Portfolio
        portfolio_id = f"port_{uuid.uuid4().hex[:8]}"
        portfolio = await state_manager.persist_portfolio(
            portfolio_id=portfolio_id,
            optimization_id=run.id,
            total_return=total_return,
            volatility=volatility,
            sharpe_ratio=sharpe,
            sortino_ratio=metrics.get("sortino_ratio", 0.0),
            max_drawdown=metrics.get("max_drawdown", 0.0),
            alpha=metrics.get("alpha", 0.0),
            scientific_status=best_result.get("scientific_status", "UNKNOWN"),
            feasible=best_result.get("feasible", False),
            allocations=allocations
        )
        logger.info(f"Successfully persisted OptimizationRun {run.id} and Portfolio {portfolio.id}")

def register_subscribers():
    event_bus.subscribe("OptimizationCompleted", handle_optimization_completed)
