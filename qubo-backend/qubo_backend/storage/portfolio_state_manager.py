import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from qubo_backend.models import Portfolio, Allocation, OptimizationRun

logger = logging.getLogger(__name__)

class PortfolioStateManager:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def persist_optimization_run(self, run_id: str, solver: str, execution_time_ms: float, 
                                       energy: float, strict_ratio: float, feasible_ratio: float,
                                       topology_density: float, scientific_status: str, isolation_status: str) -> OptimizationRun:
        run = OptimizationRun(
            id=run_id,
            solver=solver,
            execution_time_ms=execution_time_ms,
            energy=energy,
            strict_ratio=strict_ratio,
            feasible_ratio=feasible_ratio,
            topology_density=topology_density,
            scientific_status=scientific_status,
            isolation_status=isolation_status
        )
        self.session.add(run)
        await self.session.commit()
        await self.session.refresh(run)
        return run

    async def persist_portfolio(self, portfolio_id: str, optimization_id: str, 
                                total_return: float, volatility: float, sharpe_ratio: float,
                                sortino_ratio: float, max_drawdown: float, alpha: float,
                                scientific_status: str, feasible: bool, allocations: List[Dict[str, Any]]) -> Portfolio:
        portfolio = Portfolio(
            id=portfolio_id,
            optimization_id=optimization_id,
            total_return=total_return,
            volatility=volatility,
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            max_drawdown=max_drawdown,
            alpha=alpha,
            scientific_status=scientific_status,
            feasible=feasible
        )
        self.session.add(portfolio)
        
        for alloc_data in allocations:
            allocation = Allocation(
                portfolio_id=portfolio_id,
                asset=alloc_data["asset"],
                sector=alloc_data.get("sector"),
                weight=alloc_data["weight"],
                expected_return=alloc_data.get("expected_return"),
                risk_contribution=alloc_data.get("risk_contribution")
            )
            self.session.add(allocation)
            
        await self.session.commit()
        await self.session.refresh(portfolio)
        return portfolio

    async def get_latest_portfolio(self) -> Optional[Portfolio]:
        stmt = select(Portfolio).options(selectinload(Portfolio.allocations)).order_by(Portfolio.created_at.desc()).limit(1)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_portfolio_by_id(self, portfolio_id: str) -> Optional[Portfolio]:
        stmt = select(Portfolio).options(selectinload(Portfolio.allocations)).where(Portfolio.id == portfolio_id)
        result = await self.session.execute(stmt)
        return result.scalars().first()
