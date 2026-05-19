from abc import ABC, abstractmethod
from typing import Any

from qubo_backend.optimization.contracts import SolverRequest
from qubo_backend.optimization.portfolio import PortfolioSolution

class BasePortfolioSolver(ABC):
    """
    Abstract Base Class for all QUBO Portfolio Solvers.
    Enforces a strict interface contract across Classical, GPU, and Quantum engines.
    """
    
    @abstractmethod
    def solve(self, request: SolverRequest, **kwargs: Any) -> PortfolioSolution:
        """
        Standardized solve method.
        
        Args:
            request: The standard SolverRequest containing mu, sigma, constraints, etc.
            **kwargs: Additional parameters specific to the solver engine.
            
        Returns:
            PortfolioSolution containing the optimal weights, energy, and metadata.
        """
        pass
