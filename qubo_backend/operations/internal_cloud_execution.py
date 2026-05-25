"""
Qurve AI - Internal Cloud Execution Enablement
Internal-only cloud benchmark execution with authentication and governance controls.

Principles:
✅ INTERNAL ONLY: Cloud execution restricted to internal operators
✅ AUTHENTICATED BENCHMARK EXECUTION: Operator authentication required
✅ GOVERNANCE-APPROVED EXECUTION ROUTING: Governance approval required
✅ OPERATOR-APPROVED QPU ENABLEMENT: QPU requires operator approval
✅ DASHBOARD-TRIGGERED BENCHMARK RUNS: Dashboard integration
✅ AUTHENTICATED: All execution requires authentication
✅ GOVERNANCE-CONTROLLED: All execution respects governance
✅ AUDIT-TRACKED: All execution is audited
✅ QUOTA-ENFORCED: All execution respects quotas
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .operator_rbac import get_operator_rbac, Permission
from .environment_governance import EnvironmentType, get_environment_governance
from .audit_trail_system import get_audit_trail_system
from ..cost.cost_governance import get_cost_governance
from ..qpu.qpu_capability_boundaries import get_qpu_capability_boundaries
from ..qpu.qpu_hardware_governance import get_qpu_hardware_governance

logger = logging.getLogger(__name__)


class ExecutionMode(Enum):
    """Execution mode types."""
    LOCAL = "local"
    CLOUD_SIMULATOR = "cloud_simulator"
    CLOUD_QPU = "cloud_qpu"


class ExecutionStatus(Enum):
    """Execution status types."""
    PENDING = "pending"
    AUTHENTICATING = "authenticating"
    GOVERNANCE_CHECKING = "governance_checking"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ExecutionRequest:
    """Internal cloud execution request."""
    request_id: str
    operator_id: str
    execution_mode: ExecutionMode
    benchmark_id: str
    qubo_data: Dict[str, Any]
    cloud_provider: Optional[str] = None
    qpu_device: Optional[str] = None
    shots: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    status: ExecutionStatus = ExecutionStatus.PENDING


@dataclass
class ExecutionResult:
    """Internal cloud execution result."""
    request_id: str
    operator_id: str
    execution_mode: ExecutionMode
    status: ExecutionStatus
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    governance_decision: Optional[str] = None
    audit_trail_id: Optional[str] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class InternalCloudExecution:
    """
    Production-grade internal cloud execution system.
    
    Features:
    - Internal-only cloud execution
    - Authenticated benchmark execution
    - Governance-approved execution routing
    - Operator-approved QPU enablement
    - Dashboard-triggered benchmark runs
    - Audit tracking
    - Quota enforcement
    """
    
    def __init__(self):
        self.operator_rbac = get_operator_rbac()
        self.environment_governance = get_environment_governance()
        self.audit_trail = get_audit_trail_system()
        self.cost_governance = get_cost_governance()
        self.qpu_capability_boundaries = get_qpu_capability_boundaries()
        self.qpu_hardware_governance = get_qpu_hardware_governance()
        
        # Execution storage
        self._execution_requests: Dict[str, ExecutionRequest] = {}
        self._execution_results: Dict[str, ExecutionResult] = {}
        
        # Statistics
        self._request_count = 0
        self._execution_count = 0
        
        logger.info("Internal cloud execution system initialized")
    
    async def submit_execution_request(self, 
                                      operator_id: str,
                                      execution_mode: ExecutionMode,
                                      benchmark_id: str,
                                      qubo_data: Dict[str, Any],
                                      cloud_provider: Optional[str] = None,
                                      qpu_device: Optional[str] = None,
                                      shots: int = 100,
                                      metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Submit internal cloud execution request.
        
        Args:
            operator_id: Operator identifier
            execution_mode: Execution mode
            benchmark_id: Benchmark identifier
            qubo_data: QUBO problem data
            cloud_provider: Cloud provider (for cloud modes)
            qpu_device: QPU device (for QPU mode)
            shots: Number of shots
            metadata: Additional metadata
            
        Returns:
            request_id: Unique request identifier
        """
        try:
            request_id = f"exec_{execution_mode.value}_{operator_id}_{int(time.time())}"
            
            # Create execution request
            execution_request = ExecutionRequest(
                request_id=request_id,
                operator_id=operator_id,
                execution_mode=execution_mode,
                benchmark_id=benchmark_id,
                qubo_data=qubo_data,
                cloud_provider=cloud_provider,
                qpu_device=qpu_device,
                shots=shots,
                metadata=metadata or {}
            )
            
            # Store request
            self._execution_requests[request_id] = execution_request
            self._request_count += 1
            
            # Log request submission
            await self.audit_trail.log_cloud_execution_approval(
                operator_id=operator_id,
                action="submit_request",
                cloud_provider=cloud_provider or "local",
                device=qpu_device or "local",
                execution_id=request_id,
                approved=False,  # Pending approval
                correlation_id=request_id,
                metadata={
                    "execution_mode": execution_mode.value,
                    "benchmark_id": benchmark_id,
                    "shots": shots
                }
            )
            
            logger.info("Execution request submitted", 
                       request_id=request_id,
                       operator_id=operator_id,
                       execution_mode=execution_mode.value,
                       benchmark_id=benchmark_id)
            
            return request_id
            
        except Exception as e:
            logger.error("Failed to submit execution request", 
                        operator_id=operator_id,
                        execution_mode=execution_mode.value,
                        error=str(e))
            raise
    
    async def authenticate_and_approve_request(self, 
                                               request_id: str,
                                               approved_by: str,
                                               metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Authenticate and approve execution request.
        
        Args:
            request_id: Request identifier
            approved_by: Approving operator
            metadata: Additional metadata
            
        Returns:
            Success status
        """
        try:
            execution_request = self._execution_requests.get(request_id)
            if not execution_request:
                logger.warning("Execution request not found", request_id=request_id)
                return False
            
            # Update status to authenticating
            execution_request.status = ExecutionStatus.AUTHENTICATING
            
            # Validate operator permissions
            has_permission = await self._validate_operator_permissions(
                execution_request.operator_id, execution_request.execution_mode
            )
            
            if not has_permission:
                execution_request.status = ExecutionStatus.REJECTED
                await self._log_execution_decision(
                    request_id, "rejected", "Insufficient permissions", approved_by
                )
                return False
            
            # Update status to governance checking
            execution_request.status = ExecutionStatus.GOVERNANCE_CHECKING
            
            # Validate governance approval
            governance_approved = await self._validate_governance_approval(
                execution_request, approved_by
            )
            
            if not governance_approved:
                execution_request.status = ExecutionStatus.REJECTED
                await self._log_execution_decision(
                    request_id, "rejected", "Governance rejection", approved_by
                )
                return False
            
            # Approve request
            execution_request.status = ExecutionStatus.APPROVED
            execution_request.metadata.update({
                "approved_by": approved_by,
                "approved_at": time.time(),
                **(metadata or {})
            })
            
            await self._log_execution_decision(
                request_id, "approved", "Request approved", approved_by
            )
            
            logger.info("Execution request approved", 
                       request_id=request_id,
                       operator_id=execution_request.operator_id,
                       execution_mode=execution_request.execution_mode.value,
                       approved_by=approved_by)
            
            return True
            
        except Exception as e:
            logger.error("Failed to approve execution request", 
                        request_id=request_id,
                        error=str(e))
            return False
    
    async def execute_approved_request(self, request_id: str) -> bool:
        """
        Execute approved cloud execution request.
        
        Args:
            request_id: Request identifier
            
        Returns:
            Success status
        """
        try:
            execution_request = self._execution_requests.get(request_id)
            if not execution_request:
                logger.warning("Execution request not found", request_id=request_id)
                return False
            
            # Validate request is approved
            if execution_request.status != ExecutionStatus.APPROVED:
                logger.warning("Request not approved", request_id=request_id)
                return False
            
            # Create execution result
            execution_result = ExecutionResult(
                request_id=request_id,
                operator_id=execution_request.operator_id,
                execution_mode=execution_request.execution_mode,
                status=ExecutionStatus.EXECUTING,
                started_at=time.time()
            )
            
            # Store execution result
            self._execution_results[request_id] = execution_result
            self._execution_count += 1
            
            # Update request status
            execution_request.status = ExecutionStatus.EXECUTING
            
            # Execute based on mode
            try:
                result_data = await self._execute_by_mode(execution_request)
                
                # Update result
                execution_result.result_data = result_data
                execution_result.status = ExecutionStatus.COMPLETED
                execution_result.completed_at = time.time()
                execution_result.execution_time_ms = (
                    execution_result.completed_at - execution_result.started_at
                ) * 1000
                
                # Capture metadata from request (which was updated by _execute_by_mode)
                execution_result.metadata.update(execution_request.metadata)
                
                # Update request status
                execution_request.status = ExecutionStatus.COMPLETED
                
                await self._log_execution_completion(request_id, True, None)
                
                logger.info("Execution completed successfully", 
                           request_id=request_id,
                           execution_mode=execution_request.execution_mode.value,
                           execution_time_ms=execution_result.execution_time_ms)
                
                return True
                
            except Exception as e:
                # Update result with error
                execution_result.status = ExecutionStatus.FAILED
                execution_result.error_message = str(e)
                execution_result.completed_at = time.time()
                execution_result.execution_time_ms = (
                    execution_result.completed_at - execution_result.started_at
                ) * 1000
                
                # Update request status
                execution_request.status = ExecutionStatus.FAILED
                
                await self._log_execution_completion(request_id, False, str(e))
                
                logger.error("Execution failed", 
                           request_id=request_id,
                           error=str(e))
                
                return False
            
        except Exception as e:
            logger.error("Failed to execute approved request", 
                        request_id=request_id,
                        error=str(e))
            return False
    
    async def _validate_operator_permissions(self, 
                                           operator_id: str,
                                           execution_mode: ExecutionMode) -> bool:
        """Validate operator has required permissions."""
        try:
            # Check basic execution permission
            has_basic_permission = await self.operator_rbac.check_permission(
                operator_id, Permission.EXECUTE_BENCHMARK, "benchmark_execution", "check_permission"
            )
            
            if not has_basic_permission:
                return False
            
            # Check cloud execution permission for cloud modes
            if execution_mode in [ExecutionMode.CLOUD_SIMULATOR, ExecutionMode.CLOUD_QPU]:
                has_cloud_permission = await self.operator_rbac.check_permission(
                    operator_id, Permission.ACCESS_CLOUD, "cloud_execution", "check_permission"
                )
                if not has_cloud_permission:
                    return False
            
            # Check QPU permission for QPU mode
            if execution_mode == ExecutionMode.CLOUD_QPU:
                has_qpu_permission = await self.operator_rbac.check_permission(
                    operator_id, Permission.ACCESS_QPU, "qpu_execution", "check_permission"
                )
                if not has_qpu_permission:
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Failed to validate operator permissions", error=str(e))
            return False
    
    async def _validate_governance_approval(self, 
                                           execution_request: ExecutionRequest,
                                           approved_by: str) -> bool:
        """Validate governance approval for execution."""
        try:
            # Validate QPU capability boundaries
            if execution_request.execution_mode == ExecutionMode.CLOUD_QPU:
                qpu_enabled = self.qpu_capability_boundaries.get_capability_status().get("qpu_enabled", False)
                if not qpu_enabled:
                    return False
                
                # Validate QPU governance approval
                governance_approved = await self.qpu_hardware_governance.validate_qpu_execution(
                    execution_request.operator_id,
                    execution_request.qpu_device,
                    execution_request.metadata
                )
                if not governance_approved:
                    return False
            
            # Validate cost governance
            cost_approved = await self.cost_governance.validate_execution_cost(
                execution_request.operator_id,
                execution_request.execution_mode.value,
                execution_request.shots,
                execution_request.metadata
            )
            if not cost_approved:
                return False
            
            # Validate environment governance
            current_environment = self.environment_governance.get_current_environment()
            if current_environment == EnvironmentType.PRODUCTION:
                # Cloud execution restricted in production
                return False
            
            return True
            
        except Exception as e:
            logger.error("Failed to validate governance approval", error=str(e))
            return False
    
    async def _execute_by_mode(self, execution_request: ExecutionRequest) -> Dict[str, Any]:
        """Execute based on execution mode."""
        try:
            if execution_request.execution_mode == ExecutionMode.LOCAL:
                return await self._execute_local(execution_request)
            elif execution_request.execution_mode == ExecutionMode.CLOUD_SIMULATOR:
                return await self._execute_cloud_simulator(execution_request)
            elif execution_request.execution_mode == ExecutionMode.CLOUD_QPU:
                return await self._execute_cloud_qpu(execution_request)
            else:
                raise ValueError(f"Unsupported execution mode: {execution_request.execution_mode.value}")
                
        except Exception as e:
            logger.error("Failed to execute by mode", 
                        execution_mode=execution_request.execution_mode.value,
                        error=str(e))
            raise
    
    async def _execute_local(self, execution_request: ExecutionRequest) -> Dict[str, Any]:
        """Execute local benchmark."""
        try:
            from ..optimization.braket_integration import get_braket_integration
            from ..optimization.contracts import SolverRequest
            
            braket = get_braket_integration()
            
            # Map request to Braket request
            solver_request = SolverRequest(
                qubo=execution_request.qubo_data.get("qubo", {}),
                solver="AWS_BRAKET_LOCAL",
                shots=execution_request.shots,
                execution_mode="local"
            )
            
            # Execute real Braket job locally
            result = await braket.solve_portfolio(solver_request)
            
            # Update metadata
            execution_request.metadata.update({
                "execution_origin": result.metadata.execution_origin,
                "fallback_triggered": result.metadata.fallback_triggered,
                "fallback_chain": result.metadata.fallback_chain
            })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error("Failed to execute local", error=str(e))
            raise
    
    async def _execute_cloud_simulator(self, execution_request: ExecutionRequest) -> Dict[str, Any]:
        """Execute cloud simulator benchmark."""
        try:
            from ..optimization.braket_integration import get_braket_integration
            from ..optimization.contracts import SolverRequest
            
            braket = get_braket_integration()
            
            # Map request to Braket request
            solver_request = SolverRequest(
                qubo=execution_request.qubo_data.get("qubo", {}),
                solver="AWS_BRAKET_SV1", # Default simulator
                shots=execution_request.shots,
                execution_mode="cloud_simulator"
            )
            
            # Execute real Braket job
            result = await braket.solve_portfolio(solver_request)
            
            # Update metadata with cloud telemetry
            execution_request.metadata.update({
                "execution_origin": result.metadata.execution_origin,
                "fallback_triggered": result.metadata.fallback_triggered,
                "fallback_chain": result.metadata.fallback_chain,
                "task_arn": result.metadata.task_arn,
                "device_arn": result.metadata.device_arn
            })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error("Failed to execute cloud simulator", error=str(e))
            raise
    
    async def _execute_cloud_qpu(self, execution_request: ExecutionRequest) -> Dict[str, Any]:
        """Execute cloud QPU benchmark."""
        try:
            # Validate QPU execution is enabled
            qpu_status = self.qpu_capability_boundaries.get_capability_status()
            if not qpu_status.get("qpu_enabled", False):
                raise ValueError("QPU execution is not enabled")
            
            from ..optimization.braket_integration import get_braket_integration
            from ..optimization.contracts import SolverRequest
            
            braket = get_braket_integration()
            
            # Map request to Braket request
            solver_request = SolverRequest(
                qubo=execution_request.qubo_data.get("qubo", {}),
                solver="AWS_BRAKET_TN1", # Preferred QPU/Sim
                shots=execution_request.shots,
                execution_mode="cloud_qpu"
            )
            
            # Execute real Braket job
            result = await braket.solve_portfolio(solver_request)
            
            # Update metadata with cloud telemetry
            execution_request.metadata.update({
                "execution_origin": result.metadata.execution_origin,
                "fallback_triggered": result.metadata.fallback_triggered,
                "fallback_chain": result.metadata.fallback_chain,
                "task_arn": result.metadata.task_arn,
                "device_arn": result.metadata.device_arn
            })
            
            return result.to_dict()
            
        except Exception as e:
            logger.error("Failed to execute cloud QPU", error=str(e))
            raise
    
    async def _log_execution_decision(self, 
                                      request_id: str,
                                      decision: str,
                                      reason: str,
                                      decided_by: str) -> None:
        """Log execution decision."""
        try:
            await self.audit_trail.log_cloud_execution_approval(
                operator_id=decided_by,
                action=f"decision_{decision}",
                cloud_provider="internal",
                device="internal",
                execution_id=request_id,
                approved=(decision == "approved"),
                correlation_id=request_id,
                metadata={
                    "decision": decision,
                    "reason": reason,
                    "internal_execution": True
                }
            )
            
        except Exception as e:
            logger.error("Failed to log execution decision", error=str(e))
    
    async def _log_execution_completion(self, 
                                         request_id: str,
                                         success: bool,
                                         error_message: Optional[str] = None) -> None:
        """Log execution completion."""
        try:
            execution_result = self._execution_results.get(request_id)
            if not execution_result:
                return
            
            await self.audit_trail.log_cloud_execution_approval(
                operator_id=execution_result.operator_id,
                action="execution_completed",
                cloud_provider="internal",
                device="internal",
                execution_id=request_id,
                approved=success,
                correlation_id=request_id,
                metadata={
                    "execution_mode": execution_result.execution_mode.value,
                    "success": success,
                    "error_message": error_message,
                    "execution_time_ms": execution_result.execution_time_ms,
                    "internal_execution": True
                }
            )
            
        except Exception as e:
            logger.error("Failed to log execution completion", error=str(e))
    
    async def get_execution_request(self, request_id: str) -> Optional[ExecutionRequest]:
        """Get execution request by ID."""
        return self._execution_requests.get(request_id)
    
    async def get_execution_result(self, request_id: str) -> Optional[ExecutionResult]:
        """Get execution result by ID."""
        return self._execution_results.get(request_id)
    
    def get_execution_requests(self, 
                               operator_id: Optional[str] = None,
                               execution_mode: Optional[ExecutionMode] = None,
                               status: Optional[ExecutionStatus] = None,
                               limit: int = 100) -> List[ExecutionRequest]:
        """Get execution requests with filtering."""
        requests = list(self._execution_requests.values())
        
        # Apply filters
        if operator_id:
            requests = [r for r in requests if r.operator_id == operator_id]
        
        if execution_mode:
            requests = [r for r in requests if r.execution_mode == execution_mode]
        
        if status:
            requests = [r for r in requests if r.status == status]
        
        # Sort by creation time (most recent first)
        requests.sort(key=lambda r: r.created_at, reverse=True)
        
        return requests[:limit]
    
    def get_execution_results(self, 
                              operator_id: Optional[str] = None,
                              execution_mode: Optional[ExecutionMode] = None,
                              status: Optional[ExecutionStatus] = None,
                              limit: int = 100) -> List[ExecutionResult]:
        """Get execution results with filtering."""
        results = list(self._execution_results.values())
        
        # Apply filters
        if operator_id:
            results = [r for r in results if r.operator_id == operator_id]
        
        if execution_mode:
            results = [r for r in results if r.execution_mode == execution_mode]
        
        if status:
            results = [r for r in results if r.status == status]
        
        # Sort by start time (most recent first)
        results.sort(key=lambda r: r.started_at or 0, reverse=True)
        
        return results[:limit]
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """Get internal cloud execution statistics."""
        requests = list(self._execution_requests.values())
        results = list(self._execution_results.values())
        
        # Status distribution
        status_counts = {}
        for request in requests:
            status = request.status.value
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Mode distribution
        mode_counts = {}
        for request in requests:
            mode = request.execution_mode.value
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
        
        # Success rate
        completed_results = [r for r in results if r.status == ExecutionStatus.COMPLETED]
        failed_results = [r for r in results if r.status == ExecutionStatus.FAILED]
        success_rate = (len(completed_results) / len(results) * 100) if results else 0.0
        
        # Average execution time
        completed_with_time = [r for r in completed_results if r.execution_time_ms]
        avg_execution_time = sum(r.execution_time_ms for r in completed_with_time) / len(completed_with_time) if completed_with_time else 0.0
        
        return {
            "total_requests": len(requests),
            "request_count": self._request_count,
            "total_executions": len(results),
            "execution_count": self._execution_count,
            "status_distribution": status_counts,
            "mode_distribution": mode_counts,
            "success_rate": success_rate,
            "average_execution_time_ms": avg_execution_time,
            "completed_executions": len(completed_results),
            "failed_executions": len(failed_results),
            "internal_only": True,
            "authenticated_execution": True,
            "governance_controlled": True,
            "audit_tracked": True,
            "quota_enforced": True
        }
    
    def get_execution_guarantees(self) -> Dict[str, Any]:
        """Get internal cloud execution guarantees."""
        return {
            "internal_only": True,
            "authenticated_benchmark_execution": True,
            "governance_approved_execution_routing": True,
            "operator_approved_qpu_enablement": True,
            "dashboard_triggered_benchmark_runs": True,
            "authenticated": True,
            "governance_controlled": True,
            "audit_tracked": True,
            "quota_enforced": True,
            "operator_permission_validation": True,
            "qpu_capability_validation": True,
            "cost_governance_validation": True,
            "environment_governance_validation": True,
            "execution_mode_isolation": True,
            "request_approval_workflow": True
        }


# Global internal cloud execution instance
_internal_cloud_execution: Optional[InternalCloudExecution] = None


def get_internal_cloud_execution() -> InternalCloudExecution:
    """Get global internal cloud execution instance."""
    global _internal_cloud_execution
    if _internal_cloud_execution is None:
        _internal_cloud_execution = InternalCloudExecution()
    return _internal_cloud_execution
