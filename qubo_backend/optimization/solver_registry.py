"""
Qurve AI - Solver Capability Registry
Centralized solver capability management and availability tracking
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum

from ..telemetry.structured_telemetry import get_solver_telemetry


class SolverType(Enum):
    """Solver type enumeration."""
    CLASSICAL = "classical"
    NEAL = "neal"
    QISKIT = "qiskit"
    QISKIT_LOCAL = "qiskit_local"
    BRAKET_LOCAL = "braket_local"
    AUTO = "auto"


@dataclass
class SolverCapability:
    """Solver capability definition."""
    available: bool
    provider: str
    requires_token: bool
    worker_required: bool = False
    cloud: bool = False
    qpu: bool = False
    local: bool = True
    hybrid: bool = False
    max_assets: Optional[int] = None
    max_binary_bits: Optional[int] = None
    description: str = ""
    dependencies: List[str] = None
    last_check: Optional[float] = None
    error_message: Optional[str] = None


class SolverCapabilityRegistry:
    """
    Centralized solver capability registry.
    
    Provides:
    - Centralized capability checks
    - Centralized status reporting
    - Centralized availability logic
    - Centralized token requirements
    - Centralized cloud/local metadata
    """
    
    def __init__(self):
        self.telemetry = get_solver_telemetry()
        self._capabilities: Dict[SolverType, SolverCapability] = {}
        self._initialize_capabilities()
    
    def _initialize_capabilities(self):
        """Initialize solver capabilities."""
        
        # Classical solver
        self._capabilities[SolverType.CLASSICAL] = SolverCapability(
            available=True,
            provider="local",
            requires_token=False,
            local=True,
            description="Classical optimization solver using scipy",
            dependencies=["scipy", "numpy"]
        )
        
        # Neal solver
        self._capabilities[SolverType.NEAL] = SolverCapability(
            available=True,
            provider="dwave",
            requires_token=False,
            local=True,
            description="D-Wave Neal simulated annealing",
            dependencies=["dwave-neal"]
        )
        
        # Qiskit solver
        self._capabilities[SolverType.QISKIT] = SolverCapability(
            available=True,
            provider="ibm",
            requires_token=True,
            cloud=True,
            qpu=True,
            local=False,
            description="IBM Qiskit quantum solver",
            dependencies=["qiskit"]
        )
        
        # Qiskit local solver
        self._capabilities[SolverType.QISKIT_LOCAL] = SolverCapability(
            available=True,
            provider="ibm",
            requires_token=False,
            local=True,
            description="IBM Qiskit local simulator",
            dependencies=["qiskit"]
        )
        
        # Braket local solver
        self._capabilities[SolverType.BRAKET_LOCAL] = SolverCapability(
            available=True,
            provider="amazon_braket",
            requires_token=False,
            worker_required=True,
            cloud=False,
            local=True,
            hybrid=True,
            max_assets=8,
            max_binary_bits=3,
            description="Amazon Braket local quantum simulator",
            dependencies=["httpx", "qubo-backend.optimization.braket_client_resilient"]
        )
        
        # Auto solver
        self._capabilities[SolverType.AUTO] = SolverCapability(
            available=True,
            provider="auto",
            requires_token=False,
            local=True,
            description="Automatic solver selection based on problem characteristics",
            dependencies=[]
        )
    
    def get_capability(self, solver_type: SolverType) -> SolverCapability:
        """Get capability for specific solver."""
        return self._capabilities.get(solver_type, SolverCapability(
            available=False,
            provider="unknown",
            requires_token=False,
            description="Unknown solver"
        ))
    
    def check_availability(self, solver_type: SolverType) -> bool:
        """Check if solver is available."""
        capability = self.get_capability(solver_type)
        
        # Perform dynamic availability check if needed
        if solver_type == SolverType.BRAKET_LOCAL:
            return self._check_braket_availability()
        
        return capability.available
    
    def _check_braket_availability(self) -> bool:
        """Check Braket worker availability dynamically."""
        try:
            import asyncio
            from .braket_client_resilient import check_braket_worker_health_resilient
            
            # Check availability asynchronously
            try:
                # Try to get current event loop
                loop = asyncio.get_running_loop()
                # If we're in an async context, create task
                task = asyncio.create_task(check_braket_worker_health_resilient())
                return True  # Assume available for now, will be checked properly
            except RuntimeError:
                # No running loop, safe to run
                return asyncio.run(check_braket_worker_health_resilient())
                
        except Exception as e:
            self.telemetry._log_structured(
                event_type="availability_check_failed",
                solver="braket_local",
                error=str(e)
            )
            return False
    
    def update_capability(self, solver_type: SolverType, capability: SolverCapability):
        """Update solver capability."""
        import time
        capability.last_check = time.time()
        self._capabilities[solver_type] = capability
        
        self.telemetry._log_structured(
            event_type="capability_updated",
            solver=solver_type.value,
            available=capability.available,
            provider=capability.provider,
            error_message=capability.error_message
        )
    
    def get_available_solvers(self) -> List[SolverType]:
        """Get list of available solvers."""
        available_solvers = []
        
        for solver_type, capability in self._capabilities.items():
            if self.check_availability(solver_type):
                available_solvers.append(solver_type)
        
        return available_solvers
    
    def get_solver_info(self, solver_type: SolverType) -> Dict[str, Any]:
        """Get comprehensive solver information."""
        capability = self.get_capability(solver_type)
        is_available = self.check_availability(solver_type)
        
        return {
            "solver_type": solver_type.value,
            "available": is_available,
            "provider": capability.provider,
            "requires_token": capability.requires_token,
            "worker_required": capability.worker_required,
            "cloud": capability.cloud,
            "local": capability.local,
            "qpu": capability.qpu,
            "hybrid": capability.hybrid,
            "max_assets": capability.max_assets,
            "max_binary_bits": capability.max_binary_bits,
            "description": capability.description,
            "dependencies": capability.dependencies or [],
            "last_check": capability.last_check,
            "error_message": capability.error_message
        }
    
    def get_all_capabilities(self) -> Dict[str, Any]:
        """Get all solver capabilities."""
        capabilities = {}
        
        for solver_type in SolverType:
            capabilities[solver_type.value] = self.get_solver_info(solver_type)
        
        return {
            "solvers": capabilities,
            "available_count": len(self.get_available_solvers()),
            "total_count": len(SolverType),
            "timestamp": self._get_timestamp()
        }
    
    def validate_solver_request(self, solver_type: SolverType, 
                           request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate solver request against capabilities."""
        capability = self.get_capability(solver_type)
        validation_result = {
            "valid": True,
            "warnings": [],
            "errors": []
        }
        
        # Check availability
        if not self.check_availability(solver_type):
            validation_result["valid"] = False
            validation_result["errors"].append(
                f"Solver {solver_type.value} is not available"
            )
        
        # Check token requirement
        if capability.requires_token:
            if not request_data.get("token"):
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Solver {solver_type.value} requires authentication token"
                )
        
        # Check worker requirement
        if capability.worker_required:
            if not self._check_braket_availability():
                validation_result["valid"] = False
                validation_result["errors"].append(
                    f"Solver {solver_type.value} requires worker service"
                )
        
        # Check asset limits
        if capability.max_assets:
            asset_count = len(request_data.get("mu", []))
            if asset_count > capability.max_assets:
                validation_result["warnings"].append(
                    f"Problem size ({asset_count} assets) exceeds recommended limit "
                    f"({capability.max_assets} assets) for {solver_type.value}"
                )
        
        # Check binary bits limits
        if capability.max_binary_bits:
            binary_bits = request_data.get("binary_bits", 0)
            if binary_bits > capability.max_binary_bits:
                validation_result["warnings"].append(
                    f"Binary bits ({binary_bits}) exceeds recommended limit "
                    f"({capability.max_binary_bits}) for {solver_type.value}"
                )
        
        return validation_result
    
    def get_recommended_solver(self, request_data: Dict[str, Any]) -> SolverType:
        """Get recommended solver based on request characteristics."""
        asset_count = len(request_data.get("mu", []))
        binary_bits = request_data.get("binary_bits", 0)
        
        # Simple recommendation logic
        if asset_count <= 3 and binary_bits <= 2:
            # Small problems: try quantum solvers first
            if self.check_availability(SolverType.BRAKET_LOCAL):
                return SolverType.BRAKET_LOCAL
            elif self.check_availability(SolverType.QISKIT_LOCAL):
                return SolverType.QISKIT_LOCAL
        
        # Medium problems: classical or Neal
        if asset_count <= 10:
            if self.check_availability(SolverType.NEAL):
                return SolverType.NEAL
            elif self.check_availability(SolverType.CLASSICAL):
                return SolverType.CLASSICAL
        
        # Large problems: classical
        return SolverType.CLASSICAL
    
    def _get_timestamp(self) -> float:
        """Get current timestamp."""
        import time
        return time.time()
    
    def refresh_capabilities(self):
        """Refresh all solver capabilities."""
        import time
        
        self.telemetry._log_structured(
            event_type="capabilities_refresh_started"
        )
        
        for solver_type in SolverType:
            capability = self.get_capability(solver_type)
            
            if solver_type == SolverType.BRAKET_LOCAL:
                # Check Braket availability
                is_available = self._check_braket_availability()
                capability.available = is_available
                capability.last_check = time.time()
                if not is_available:
                    capability.error_message = "Braket worker not available"
                else:
                    capability.error_message = None
            
            self.update_capability(solver_type, capability)
        
        self.telemetry._log_structured(
            event_type="capabilities_refresh_completed",
            available_solvers=len(self.get_available_solvers())
        )


# Global registry instance
_solver_registry: Optional[SolverCapabilityRegistry] = None


def get_solver_registry() -> SolverCapabilityRegistry:
    """Get the global solver registry instance."""
    global _solver_registry
    if _solver_registry is None:
        _solver_registry = SolverCapabilityRegistry()
    return _solver_registry


def get_solver_capabilities() -> Dict[str, Any]:
    """Get all solver capabilities."""
    registry = get_solver_registry()
    return registry.get_all_capabilities()


def check_solver_availability(solver_type: str) -> bool:
    """Check if solver is available by name."""
    try:
        solver_enum = SolverType(solver_type)
        registry = get_solver_registry()
        return registry.check_availability(solver_enum)
    except ValueError:
        return False


def get_available_solvers() -> List[str]:
    """Get list of available solver names."""
    registry = get_solver_registry()
    available_solvers = registry.get_available_solvers()
    return [solver.value for solver in available_solvers]


def validate_solver_request(solver_type: str, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate solver request by name."""
    try:
        solver_enum = SolverType(solver_type)
        registry = get_solver_registry()
        return registry.validate_solver_request(solver_enum, request_data)
    except ValueError:
        return {
            "valid": False,
            "warnings": [],
            "errors": [f"Unknown solver type: {solver_type}"]
        }


def get_recommended_solver(request_data: Dict[str, Any]) -> str:
    """Get recommended solver name."""
    registry = get_solver_registry()
    solver_type = registry.get_recommended_solver(request_data)
    return solver_type.value
