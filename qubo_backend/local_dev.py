"""
Local Development Mode for QUBO Portfolio Optimizer
Enables offline development with automatic local simulator enablement
and mock telemetry mode for development debugging.
"""

import logging
import os
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .config import get_settings
from .solver_registry import SOLVER_REGISTRY, SolverRegistration, SolverCapabilities
from .solver_states import SolverState, SolverInfo, SolverHealthMetrics
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


@dataclass
class LocalDevConfig:
    """Configuration for local development mode."""
    
    enabled: bool = True
    auto_enable_simulators: bool = True
    mock_cloud_services: bool = True
    mock_telemetry: bool = True
    suppress_auth_errors: bool = True
    offline_mode: bool = False


class LocalDevelopmentMode:
    """
    Local development mode with automatic simulator enablement.
    
    Features:
    - Automatic local simulator enablement (Neal, Qiskit Aer, Braket Local)
    - Mock telemetry mode for development debugging
    - Platform stability when tokens/APIs unavailable
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.config = self._load_config()
        self._is_local_dev = self._detect_local_dev()
        
        if self._is_local_dev:
            logger.info("Local development mode detected")
            self._enable_local_dev_features()
    
    def _load_config(self) -> LocalDevConfig:
        """Load local development configuration."""
        return LocalDevConfig(
            enabled=os.getenv("LOCAL_DEV_ENABLED", "true").lower() == "true",
            auto_enable_simulators=os.getenv("AUTO_ENABLE_SIMULATORS", "true").lower() == "true",
            mock_cloud_services=os.getenv("MOCK_CLOUD_SERVICES", "true").lower() == "true",
            mock_telemetry=os.getenv("MOCK_TELEMETRY", "true").lower() == "true",
            suppress_auth_errors=os.getenv("SUPPRESS_AUTH_ERRORS", "true").lower() == "true",
            offline_mode=os.getenv("OFFLINE_MODE", "false").lower() == "true"
        )
    
    def _detect_local_dev(self) -> bool:
        """Detect if running in local development environment."""
        indicators = [
            os.getenv("ENVIRONMENT") == "development",
            os.getenv("DEBUG") == "true",
            not os.getenv("DWAVE_API_TOKEN"),
            not os.getenv("IBM_QUANTUM_TOKEN"),
            "localhost" in os.getenv("DATABASE_URL", ""),
            "sqlite" in os.getenv("DATABASE_URL", "")
        ]
        
        return any(indicators) and self.config.enabled
    
    def _enable_local_dev_features(self) -> None:
        """Enable local development features."""
        if self.config.auto_enable_simulators:
            self._register_local_simulators()
        
        if self.config.mock_cloud_services:
            self._setup_mock_cloud_services()
        
        if self.config.mock_telemetry:
            self._setup_mock_telemetry()
    
    def _register_local_simulators(self) -> None:
        """Register local simulators with solver registry."""
        # D-Wave Neal (Simulated Annealing)
        SOLVER_REGISTRY.register_solver(
            name="dwave_local",
            solver_type="quantum",
            capabilities=SolverCapabilities(
                max_assets=40,
                max_binary_bits=7,
                supports_gpu=False,
                supports_cloud=False,
                supports_local=True,
                requires_auth=False,
                estimated_cost_per_run=0.0,
                average_solve_time_seconds=2.0,
                quality_score=0.75,
                memory_requirement_mb=512
            ),
            registration=SolverRegistration(solver_class=None),  # Will be implemented
            description="D-Wave Neal Simulated Annealing (Local)",
            priority=45
        )
        
        # Qiskit Local (Aer Simulator)
        SOLVER_REGISTRY.register_solver(
            name="qiskit_local",
            solver_type="quantum",
            capabilities=SolverCapabilities(
                max_assets=15,
                max_binary_bits=3,
                supports_gpu=False,
                supports_cloud=False,
                supports_local=True,
                requires_auth=False,
                estimated_cost_per_run=0.0,
                average_solve_time_seconds=5.0,
                quality_score=0.7,
                memory_requirement_mb=1024
            ),
            registration=SolverRegistration(solver_class=None),
            description="Qiskit Aer Simulator (Local)",
            priority=55
        )
        
        # AWS Braket Local Simulator
        SOLVER_REGISTRY.register_solver(
            name="braket_local",
            solver_type="quantum",
            capabilities=SolverCapabilities(
                max_assets=30,
                max_binary_bits=5,
                supports_gpu=False,
                supports_cloud=False,
                supports_local=True,
                requires_auth=False,
                estimated_cost_per_run=0.0,
                average_solve_time_seconds=3.0,
                quality_score=0.7,
                memory_requirement_mb=768
            ),
            registration=SolverRegistration(solver_class=None),
            description="AWS Braket Local Simulator",
            priority=50
        )
        
        logger.info("Local simulators registered successfully")
    
    def _setup_mock_cloud_services(self) -> None:
        """Setup mock cloud services for development."""
        # Mock cloud connectivity checks
        CACHE_MANAGER.set_api_connectivity("dwave", {
            "status": "mock",
            "message": "Mock D-Wave service for local development"
        })
        
        CACHE_MANAGER.set_api_connectivity("ibm_quantum", {
            "status": "mock", 
            "message": "Mock IBM Quantum service for local development"
        })
        
        CACHE_MANAGER.set_api_connectivity("braket", {
            "status": "mock",
            "message": "Mock AWS Braket service for local development"
        })
        
        logger.info("Mock cloud services configured")
    
    def _setup_mock_telemetry(self) -> None:
        """Setup mock telemetry for development."""
        mock_gpu_info = {
            "available": False,
            "message": "Mock GPU telemetry for local development"
        }
        
        CACHE_MANAGER.set_gpu_info(mock_gpu_info)
        logger.info("Mock telemetry configured")
    
    def is_local_dev_mode(self) -> bool:
        """Check if running in local development mode."""
        return self._is_local_dev
    
    def get_local_dev_status(self) -> Dict[str, Any]:
        """Get local development mode status."""
        return {
            "enabled": self._is_local_dev,
            "config": {
                "auto_enable_simulators": self.config.auto_enable_simulators,
                "mock_cloud_services": self.config.mock_cloud_services,
                "mock_telemetry": self.config.mock_telemetry,
                "offline_mode": self.config.offline_mode
            },
            "available_solvers": len(SOLVER_REGISTRY.get_available_solvers()),
            "local_simulators": ["dwave_local", "qiskit_local", "braket_local"]
        }


# Global local development manager
LOCAL_DEV_MANAGER = LocalDevelopmentMode()
