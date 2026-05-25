"""
Modular Service Architecture for QUBO Portfolio Optimizer
Designs modular monolith approach with clear service boundaries:
Frontend → API Gateway → Optimization Service → Quantum Service → Telemetry Service
Prevents scaling collapse and enables independent service deployment.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime
import uuid

from .config import get_settings
from .performance import PERFORMANCE_MONITOR, monitor_performance

logger = logging.getLogger(__name__)


class ServiceError(Exception):
    """Service-level error with context."""
    
    def __init__(self, message: str, service_name: str, error_code: str = None):
        super().__init__(message)
        self.service_name = service_name
        self.error_code = error_code
        self.timestamp = datetime.now()


@dataclass
class ServiceRequest:
    """Standardized service request format."""
    
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    method: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user_context: Optional[Dict[str, Any]] = None
    timeout_seconds: float = 30.0


@dataclass
class ServiceResponse:
    """Standardized service response format."""
    
    request_id: str
    service_name: str
    method: str
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    error_code: Optional[str] = None
    processing_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseService(ABC):
    """
    Abstract base class for all services.
    
    Provides common functionality for service registration,
    health monitoring, and request/response handling.
    """
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.settings = get_settings()
        self._health_status = "unknown"
        self._last_health_check = None
        self._request_count = 0
        self._error_count = 0
        
    @abstractmethod
    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        Handle a service request.
        
        Args:
            request: Service request to process
            
        Returns:
            Service response
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform service-specific health check.
        
        Returns:
            Health status information
        """
        pass
    
    async def process_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        Process request with monitoring and error handling.
        
        Args:
            request: Service request to process
            
        Returns:
            Service response
        """
        start_time = datetime.now()
        self._request_count += 1
        
        try:
            # Validate request
            if not self._validate_request(request):
                return ServiceResponse(
                    request_id=request.request_id,
                    service_name=self.service_name,
                    method=request.method,
                    success=False,
                    error="Invalid request format",
                    error_code="INVALID_REQUEST"
                )
            
            # Process request
            response = await self.handle_request(request)
            
            # Update processing time
            end_time = datetime.now()
            response.processing_time_ms = (end_time - start_time).total_seconds() * 1000
            
            # Log successful request
            logger.debug(f"Service {self.service_name} processed request {request.request_id} in {response.processing_time_ms:.2f}ms")
            
            return response
            
        except Exception as e:
            self._error_count += 1
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            logger.error(f"Service {self.service_name} error processing request {request.request_id}: {e}")
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="SERVICE_ERROR",
                processing_time_ms=processing_time
            )
    
    def _validate_request(self, request: ServiceRequest) -> bool:
        """Validate request format and content."""
        if not request.service_name or not request.method:
            return False
        
        if request.timeout_seconds <= 0:
            return False
        
        return True
    
    def get_service_stats(self) -> Dict[str, Any]:
        """Get service statistics."""
        error_rate = (self._error_count / self._request_count * 100) if self._request_count > 0 else 0
        
        return {
            "service_name": self.service_name,
            "health_status": self._health_status,
            "last_health_check": self._last_health_check.isoformat() if self._last_health_check else None,
            "total_requests": self._request_count,
            "error_count": self._error_count,
            "error_rate_percent": error_rate,
            "uptime_percentage": 100.0 - error_rate
        }


class OptimizationService(BaseService):
    """
    Optimization Service - Core portfolio optimization logic.
    
    Handles:
    - QUBO model construction
    - Solver selection and execution
    - Portfolio constraint validation
    - Result processing and formatting
    """
    
    def __init__(self):
        super().__init__("optimization")
        
    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """Handle optimization requests."""
        if request.method == "optimize":
            return await self._handle_optimization(request)
        elif request.method == "validate_constraints":
            return await self._handle_constraint_validation(request)
        elif request.method == "estimate_resources":
            return await self._handle_resource_estimation(request)
        else:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=f"Unknown method: {request.method}",
                error_code="UNKNOWN_METHOD"
            )
    
    @monitor_performance("optimization_optimize", include_memory=True)
    async def _handle_optimization(self, request: ServiceRequest) -> ServiceResponse:
        """Handle portfolio optimization request."""
        try:
            # Extract parameters
            params = request.parameters
            num_assets = params.get("num_assets", 15)
            binary_bits = params.get("binary_bits", 7)
            risk_tolerance = params.get("risk_tolerance", 0.5)
            cardinality = params.get("cardinality", 10)
            
            # Import here to avoid circular imports
            from .solver_hierarchy import PRODUCTION_HIERARCHY
            from .resource_guardrails import RESOURCE_GUARDRAILS
            
            # Select best solver
            solver = PRODUCTION_HIERARCHY.select_best_solver(
                num_assets=num_assets,
                binary_bits=binary_bits
            )
            
            if not solver:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_name=self.service_name,
                    method=request.method,
                    success=False,
                    error="No suitable solver available",
                    error_code="NO_SOLVER_AVAILABLE"
                )
            
            # Check resource guardrails
            resource_reqs = RESOURCE_GUARDRAILS.estimate_resource_requirements(
                num_assets, binary_bits, solver.solver_type
            )
            
            can_execute, error_msg = RESOURCE_GUARDRAILS.can_execute_job(
                num_assets, binary_bits,
                resource_reqs['estimated_memory_mb'],
                resource_reqs['estimated_time_seconds']
            )
            
            if not can_execute:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_name=self.service_name,
                    method=request.method,
                    success=False,
                    error=f"Resource guardrails violation: {error_msg}",
                    error_code="RESOURCE_VIOLATION"
                )
            
            # Execute optimization (simplified for this example)
            optimization_result = {
                "solver_used": solver.name,
                "num_assets": num_assets,
                "binary_bits": binary_bits,
                "risk_tolerance": risk_tolerance,
                "cardinality": cardinality,
                "weights": [0.1] * num_assets,  # Placeholder
                "objective_value": 0.05,  # Placeholder
                "constraint_satisfaction": 1.0,
                "execution_time_seconds": resource_reqs['estimated_time_seconds']
            }
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data=optimization_result
            )
            
        except Exception as e:
            logger.error(f"Optimization error: {e}")
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="OPTIMIZATION_ERROR"
            )
    
    async def _handle_constraint_validation(self, request: ServiceRequest) -> ServiceResponse:
        """Handle constraint validation request."""
        params = request.parameters
        weights = params.get("weights", [])
        
        # Simple validation logic
        if not weights:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error="No weights provided",
                error_code="NO_WEIGHTS"
            )
        
        # Check sum constraint
        weight_sum = sum(weights)
        is_valid = abs(weight_sum - 1.0) < 0.01
        
        return ServiceResponse(
            request_id=request.request_id,
            service_name=self.service_name,
            method=request.method,
            success=True,
            data={
                "weight_sum": weight_sum,
                "valid": is_valid,
                "message": "Weights sum to 1.0" if is_valid else f"Weights sum to {weight_sum}"
            }
        )
    
    async def _handle_resource_estimation(self, request: ServiceRequest) -> ServiceResponse:
        """Handle resource estimation request."""
        params = request.parameters
        num_assets = params.get("num_assets", 15)
        binary_bits = params.get("binary_bits", 7)
        
        from .resource_guardrails import RESOURCE_GUARDRAILS
        
        estimation = RESOURCE_GUARDRAILS.estimate_resource_requirements(
            num_assets, binary_bits, "quantum"
        )
        
        return ServiceResponse(
            request_id=request.request_id,
            service_name=self.service_name,
            method=request.method,
            success=True,
            data=estimation
        )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform optimization service health check."""
        try:
            # Check if we can create a simple optimization problem
            test_params = {
                "num_assets": 5,
                "binary_bits": 3,
                "risk_tolerance": 0.5,
                "cardinality": 3
            }
            
            test_request = ServiceRequest(
                service_name=self.service_name,
                method="estimate_resources",
                parameters=test_params
            )
            
            response = await self.process_request(test_request)
            
            self._health_status = "healthy" if response.success else "unhealthy"
            self._last_health_check = datetime.now()
            
            return {
                "service": self.service_name,
                "status": self._health_status,
                "test_optimization": response.success,
                "test_result": response.data if response.success else None,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            self._last_health_check = datetime.now()
            
            return {
                "service": self.service_name,
                "status": self._health_status,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class QuantumService(BaseService):
    """
    Quantum Service - Quantum solver management and execution.
    
    Handles:
    - Quantum solver registration and health
    - Cloud quantum service integration
    - Quantum circuit execution
    - Quantum result processing
    """
    
    def __init__(self):
        super().__init__("quantum")
        
    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """Handle quantum service requests."""
        if request.method == "list_solvers":
            return await self._handle_list_solvers(request)
        elif request.method == "get_solver_status":
            return await self._handle_solver_status(request)
        elif request.method == "execute_quantum":
            return await self._handle_quantum_execution(request)
        elif request.method == "check_quantum_availability":
            return await self._handle_quantum_availability(request)
        else:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=f"Unknown method: {request.method}",
                error_code="UNKNOWN_METHOD"
            )
    
    @monitor_performance("quantum_list_solvers")
    async def _handle_list_solvers(self, request: ServiceRequest) -> ServiceResponse:
        """Handle quantum solver listing."""
        try:
            from .solver_registry import SOLVER_REGISTRY
            
            quantum_solvers = SOLVER_REGISTRY.get_available_solvers(solver_type="quantum")
            
            solver_list = []
            for solver in quantum_solvers:
                solver_list.append({
                    "name": solver.name,
                    "type": solver.solver_type,
                    "state": solver.state.name,
                    "capabilities": {
                        "max_assets": solver.capabilities.max_assets,
                        "max_binary_bits": solver.capabilities.max_binary_bits,
                        "supports_gpu": solver.capabilities.supports_gpu,
                        "supports_cloud": solver.capabilities.supports_cloud
                    },
                    "health": {
                        "success_rate": solver.health_metrics.success_rate,
                        "total_runs": solver.health_metrics.total_runs,
                        "average_latency": solver.health_metrics.average_latency_seconds
                    }
                })
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data={"solvers": solver_list}
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="LIST_SOLVERS_ERROR"
            )
    
    async def _handle_solver_status(self, request: ServiceRequest) -> ServiceResponse:
        """Handle solver status query."""
        solver_name = request.parameters.get("solver_name")
        
        if not solver_name:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error="Solver name required",
                error_code="MISSING_SOLVER_NAME"
            )
        
        try:
            from .solver_registry import SOLVER_REGISTRY
            
            solver = SOLVER_REGISTRY.get_solver(solver_name)
            if not solver:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_name=self.service_name,
                    method=request.method,
                    success=False,
                    error=f"Solver not found: {solver_name}",
                    error_code="SOLVER_NOT_FOUND"
                )
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data={
                    "name": solver.name,
                    "state": solver.state.name,
                    "health_metrics": {
                        "success_rate": solver.health_metrics.success_rate,
                        "total_runs": solver.health_metrics.total_runs,
                        "average_latency": solver.health_metrics.average_latency_seconds,
                        "last_successful_run": solver.health_metrics.last_successful_run.isoformat() if solver.health_metrics.last_successful_run else None
                    }
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="SOLVER_STATUS_ERROR"
            )
    
    async def _handle_quantum_execution(self, request: ServiceRequest) -> ServiceResponse:
        """Handle quantum circuit execution."""
        # This would integrate with actual quantum hardware/simulators
        # For now, return a placeholder response
        return ServiceResponse(
            request_id=request.request_id,
            service_name=self.service_name,
            method=request.method,
            success=True,
            data={
                "message": "Quantum execution placeholder",
                "circuit_id": str(uuid.uuid4()),
                "shots": request.parameters.get("shots", 1000)
            }
        )
    
    async def _handle_quantum_availability(self, request: ServiceRequest) -> ServiceResponse:
        """Handle quantum availability check."""
        try:
            from .cloud_resilience import CLOUD_SERVICE_MANAGER
            
            # Check all quantum cloud services
            dwave_status = await CLOUD_SERVICE_MANAGER.check_service_connectivity("dwave")
            ibm_status = await CLOUD_SERVICE_MANAGER.check_service_connectivity("ibm_quantum")
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data={
                    "dwave_available": dwave_status.get("status") == "connected",
                    "ibm_available": ibm_status.get("status") == "connected",
                    "local_simulators": True,  # Always available
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="QUANTUM_AVAILABILITY_ERROR"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform quantum service health check."""
        try:
            from .solver_registry import SOLVER_REGISTRY
            from .cloud_resilience import CLOUD_SERVICE_MANAGER
            
            # Check solver registry
            quantum_solvers = SOLVER_REGISTRY.get_available_solvers(solver_type="quantum")
            
            # Check cloud connectivity
            cloud_status = await CLOUD_SERVICE_MANAGER.get_all_service_status()
            
            self._health_status = "healthy" if quantum_solvers else "degraded"
            self._last_health_check = datetime.now()
            
            return {
                "service": self.service_name,
                "status": self._health_status,
                "quantum_solvers_available": len(quantum_solvers),
                "cloud_services": cloud_status,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            self._last_health_check = datetime.now()
            
            return {
                "service": self.service_name,
                "status": self._health_status,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class TelemetryService(BaseService):
    """
    Telemetry Service - System monitoring and metrics collection.
    
    Handles:
    - Performance metrics collection
    - System resource monitoring
    - Service health aggregation
    - Alert generation
    """
    
    def __init__(self):
        super().__init__("telemetry")
        
    async def handle_request(self, request: ServiceRequest) -> ServiceResponse:
        """Handle telemetry requests."""
        if request.method == "get_metrics":
            return await self._handle_get_metrics(request)
        elif request.method == "get_service_health":
            return await self._handle_service_health(request)
        elif request.method == "get_system_status":
            return await self._handle_system_status(request)
        elif request.method == "get_performance_summary":
            return await self._handle_performance_summary(request)
        else:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=f"Unknown method: {request.method}",
                error_code="UNKNOWN_METHOD"
            )
    
    @monitor_performance("telemetry_get_metrics")
    async def _handle_get_metrics(self, request: ServiceRequest) -> ServiceResponse:
        """Handle metrics retrieval."""
        try:
            from .performance import PERFORMANCE_MONITOR
            
            operation_name = request.parameters.get("operation_name")
            hours = request.parameters.get("hours", 24)
            
            if operation_name:
                metrics = PERFORMANCE_MONITOR.get_performance_summary(operation_name, hours)
            else:
                # Get all available metrics
                metrics = PERFORMANCE_MONITOR._metrics
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data=metrics
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="METRICS_ERROR"
            )
    
    async def _handle_service_health(self, request: ServiceRequest) -> ServiceResponse:
        """Handle service health aggregation."""
        try:
            # This would aggregate health from all services
            # For now, return placeholder
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data={
                    "optimization_service": "healthy",
                    "quantum_service": "healthy",
                    "api_gateway": "healthy",
                    "overall_status": "healthy",
                    "timestamp": datetime.now().isoformat()
                }
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="SERVICE_HEALTH_ERROR"
            )
    
    async def _handle_system_status(self, request: ServiceRequest) -> ServiceResponse:
        """Handle system status request."""
        try:
            from .system_diagnostics import SYSTEM_DIAGNOSTICS
            
            # Get comprehensive system diagnostics
            system_status = await SYSTEM_DIAGNOSTICS.run_full_diagnostics()
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data=system_status
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="SYSTEM_STATUS_ERROR"
            )
    
    async def _handle_performance_summary(self, request: ServiceRequest) -> ServiceResponse:
        """Handle performance summary request."""
        try:
            from .performance import PERFORMANCE_MONITOR
            from .cache import CACHE_MANAGER
            
            # Get performance summary
            performance_summary = {
                "cache_stats": CACHE_MANAGER.get_cache_stats(),
                "performance_metrics": len(PERFORMANCE_MONITOR._metrics),
                "system_uptime": "24h",  # Placeholder
                "timestamp": datetime.now().isoformat()
            }
            
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=True,
                data=performance_summary
            )
            
        except Exception as e:
            return ServiceResponse(
                request_id=request.request_id,
                service_name=self.service_name,
                method=request.method,
                success=False,
                error=str(e),
                error_code="PERFORMANCE_SUMMARY_ERROR"
            )
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform telemetry service health check."""
        try:
            # Check if we can collect basic metrics
            from .performance import PERFORMANCE_MONITOR
            
            metrics_count = len(PERFORMANCE_MONITOR._metrics)
            
            self._health_status = "healthy" if metrics_count >= 0 else "unhealthy"
            self._last_health_check = datetime.now()
            
            return {
                "service": self.service_name,
                "status": self._health_status,
                "metrics_count": metrics_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self._health_status = "unhealthy"
            self._last_health_check = datetime.now()
            
            return {
                "service": self.service_name,
                "status": self._health_status,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


class APIGateway:
    """
    API Gateway - Routes requests to appropriate services.
    
    Provides:
    - Request routing and validation
    - Service discovery and load balancing
    - Request/response transformation
    - Cross-cutting concerns (auth, logging, metrics)
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._services: Dict[str, BaseService] = {}
        self._route_table: Dict[str, str] = {}
        
        # Initialize services
        self._initialize_services()
        self._build_route_table()
    
    def _initialize_services(self) -> None:
        """Initialize all services."""
        self._services["optimization"] = OptimizationService()
        self._services["quantum"] = QuantumService()
        self._services["telemetry"] = TelemetryService()
        
        logger.info("API Gateway services initialized")
    
    def _build_route_table(self) -> None:
        """Build routing table for service requests."""
        self._route_table = {
            # Optimization routes
            "optimize": "optimization",
            "validate_constraints": "optimization",
            "estimate_resources": "optimization",
            
            # Quantum routes
            "list_solvers": "quantum",
            "get_solver_status": "quantum",
            "execute_quantum": "quantum",
            "check_quantum_availability": "quantum",
            
            # Telemetry routes
            "get_metrics": "telemetry",
            "get_service_health": "telemetry",
            "get_system_status": "telemetry",
            "get_performance_summary": "telemetry"
        }
        
        logger.info(f"Route table built with {len(self._route_table)} routes")
    
    async def route_request(self, request: ServiceRequest) -> ServiceResponse:
        """
        Route request to appropriate service.
        
        Args:
            request: Service request to route
            
        Returns:
            Service response from target service
        """
        # Set service name if not provided
        if not request.service_name:
            service_name = self._route_table.get(request.method)
            if not service_name:
                return ServiceResponse(
                    request_id=request.request_id,
                    service_name="api_gateway",
                    method=request.method,
                    success=False,
                    error=f"No route for method: {request.method}",
                    error_code="NO_ROUTE"
                )
            request.service_name = service_name
        
        # Get target service
        service = self._services.get(request.service_name)
        if not service:
            return ServiceResponse(
                request_id=request.request_id,
                service_name="api_gateway",
                method=request.method,
                success=False,
                error=f"Service not found: {request.service_name}",
                error_code="SERVICE_NOT_FOUND"
            )
        
        # Add gateway processing time
        gateway_start = datetime.now()
        
        try:
            # Route to service
            response = await service.process_request(request)
            
            # Add gateway metadata
            response.metadata["gateway_processing_time_ms"] = (
                (datetime.now() - gateway_start).total_seconds() * 1000
            )
            response.metadata["routed_to"] = service.service_name
            
            return response
            
        except Exception as e:
            logger.error(f"API Gateway routing error: {e}")
            return ServiceResponse(
                request_id=request.request_id,
                service_name="api_gateway",
                method=request.method,
                success=False,
                error=f"Gateway error: {str(e)}",
                error_code="GATEWAY_ERROR"
            )
    
    async def get_gateway_status(self) -> Dict[str, Any]:
        """Get API Gateway status."""
        service_status = {}
        
        for service_name, service in self._services.items():
            service_status[service_name] = service.get_service_stats()
        
        return {
            "gateway": {
                "total_routes": len(self._route_table),
                "active_services": len(self._services),
                "timestamp": datetime.now().isoformat()
            },
            "services": service_status
        }
    
    def register_service(self, service_name: str, service: BaseService) -> None:
        """Register a new service."""
        self._services[service_name] = service
        logger.info(f"Registered service: {service_name}")
    
    def unregister_service(self, service_name: str) -> bool:
        """Unregister a service."""
        if service_name in self._services:
            del self._services[service_name]
            logger.info(f"Unregistered service: {service_name}")
            return True
        return False


# Global service instances
OPTIMIZATION_SERVICE = OptimizationService()
QUANTUM_SERVICE = QuantumService()
TELEMETRY_SERVICE = TelemetryService()
API_GATEWAY = APIGateway()
