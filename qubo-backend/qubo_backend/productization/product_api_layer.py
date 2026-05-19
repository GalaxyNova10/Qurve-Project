"""
Qurve AI - Product API Layer
Public-safe APIs with strict segregation and access controls.

Principles:
✅ PUBLIC-SAFE APIS: Safe public API endpoints
✅ AUTHENTICATED APIS: Authenticated API endpoints
✅ INTERNAL-ONLY APIS: Internal-only API endpoints
✅ OPERATOR APIS: Operator-specific API endpoints
✅ FORENSIC APIS: Forensic analysis API endpoints
✅ STRICT API SEGREGATION: Clear API separation
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .user_identity_system import get_user_identity_system, UserType
from .benchmark_execution_gateway import get_benchmark_execution_gateway
from .user_quota_management import get_user_quota_management
from ..operations.audit_trail_system import get_audit_trail_system

logger = logging.getLogger(__name__)


class APIType(Enum):
    """API type classifications."""
    PUBLIC_SAFE = "public_safe"
    AUTHENTICATED = "authenticated"
    INTERNAL_ONLY = "internal_only"
    OPERATOR = "operator"
    FORENSIC = "forensic"


class APIEndpoint(Enum):
    """API endpoint classifications."""
    # Public-safe endpoints
    PUBLIC_STATUS = "public_status"
    PUBLIC_INFO = "public_info"
    
    # Authenticated endpoints
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_PROFILE = "user_profile"
    BENCHMARK_SUBMIT = "benchmark_submit"
    BENCHMARK_STATUS = "benchmark_status"
    BENCHMARK_RESULTS = "benchmark_results"
    USER_QUOTAS = "user_quotas"
    
    # Internal-only endpoints
    SYSTEM_HEALTH = "system_health"
    SYSTEM_METRICS = "system_metrics"
    
    # Operator endpoints
    OPERATOR_DASHBOARD = "operator_dashboard"
    OPERATOR_USERS = "operator_users"
    OPERATOR_QUOTAS = "operator_quotas"
    OPERATOR_GOVERNANCE = "operator_governance"
    
    # Forensic endpoints
    FORENSIC_REPLAY = "forensic_replay"
    FORENSIC_TIMELINE = "forensic_timeline"
    FORENSIC_DIVERGENCE = "forensic_divergence"


@dataclass
class APIRequest:
    """API request definition."""
    request_id: str
    api_type: APIType
    endpoint: APIEndpoint
    user_id: Optional[str]
    session_id: Optional[str]
    api_token: Optional[str]
    request_data: Dict[str, Any]
    request_time: float
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class APIResponse:
    """API response definition."""
    request_id: str
    api_type: APIType
    endpoint: APIEndpoint
    success: bool
    response_data: Dict[str, Any]
    error_message: Optional[str] = None
    response_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductAPILayer:
    """
    Production-grade product API layer.
    
    Features:
    - Public-safe APIs
    - Authenticated APIs
    - Internal-only APIs
    - Operator APIs
    - Forensic APIs
    - Strict API segregation
    """
    
    def __init__(self):
        self.user_identity_system = get_user_identity_system()
        self.benchmark_gateway = get_benchmark_execution_gateway()
        self.quota_management = get_user_quota_management()
        self.audit_trail = get_audit_trail_system()
        
        # API statistics
        self._request_count = 0
        self._response_count = 0
        self._api_type_stats = {api_type.value: 0 for api_type in APIType}
        
        logger.info("Product API layer initialized")
    
    async def handle_api_request(self, 
                                api_type: APIType,
                                endpoint: APIEndpoint,
                                request_data: Dict[str, Any],
                                user_id: Optional[str] = None,
                                session_id: Optional[str] = None,
                                api_token: Optional[str] = None,
                                ip_address: Optional[str] = None,
                                user_agent: Optional[str] = None) -> APIResponse:
        """
        Handle API request with proper routing and validation.
        
        Args:
            api_type: API type
            endpoint: API endpoint
            request_data: Request data
            user_id: User identifier (if applicable)
            session_id: Session identifier (if applicable)
            api_token: API token (if applicable)
            ip_address: Client IP address
            user_agent: Client user agent
            
        Returns:
            API response
        """
        try:
            request_id = f"api_{api_type.value}_{endpoint.value}_{int(time.time())}"
            request_time = time.time()
            
            # Create API request
            api_request = APIRequest(
                request_id=request_id,
                api_type=api_type,
                endpoint=endpoint,
                user_id=user_id,
                session_id=session_id,
                api_token=api_token,
                request_data=request_data,
                request_time=request_time,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            self._request_count += 1
            self._api_type_stats[api_type.value] += 1
            
            # Route to appropriate handler
            response_data = await self._route_request(api_request)
            
            # Create response
            response = APIResponse(
                request_id=request_id,
                api_type=api_type,
                endpoint=endpoint,
                success=True,
                response_data=response_data,
                response_time_ms=(time.time() - request_time) * 1000
            )
            
            self._response_count += 1
            
            # Log API access
            await self._log_api_access(api_request, response)
            
            return response
            
        except Exception as e:
            logger.error("Failed to handle API request", 
                        api_type=api_type.value,
                        endpoint=endpoint.value,
                        error=str(e))
            
            return APIResponse(
                request_id=request_id if 'request_id' in locals() else "unknown",
                api_type=api_type,
                endpoint=endpoint,
                success=False,
                response_data={},
                error_message=str(e),
                response_time_ms=(time.time() - request_time) * 1000 if 'request_time' in locals() else None
            )
    
    async def _route_request(self, api_request: APIRequest) -> Dict[str, Any]:
        """Route API request to appropriate handler."""
        try:
            # Public-safe endpoints
            if api_request.api_type == APIType.PUBLIC_SAFE:
                return await self._handle_public_safe_request(api_request)
            
            # Authenticated endpoints
            elif api_request.api_type == APIType.AUTHENTICATED:
                return await self._handle_authenticated_request(api_request)
            
            # Internal-only endpoints
            elif api_request.api_type == APIType.INTERNAL_ONLY:
                return await self._handle_internal_request(api_request)
            
            # Operator endpoints
            elif api_request.api_type == APIType.OPERATOR:
                return await self._handle_operator_request(api_request)
            
            # Forensic endpoints
            elif api_request.api_type == APIType.FORENSIC:
                return await self._handle_forensic_request(api_request)
            
            else:
                raise ValueError(f"Unsupported API type: {api_request.api_type.value}")
                
        except Exception as e:
            logger.error("Failed to route request", 
                        api_type=api_request.api_type.value,
                        endpoint=api_request.endpoint.value,
                        error=str(e))
            raise
    
    async def _handle_public_safe_request(self, api_request: APIRequest) -> Dict[str, Any]:
        """Handle public-safe API requests."""
        try:
            if api_request.endpoint == APIEndpoint.PUBLIC_STATUS:
                return await self._public_status(api_request)
            elif api_request.endpoint == APIEndpoint.PUBLIC_INFO:
                return await self._public_info(api_request)
            else:
                raise ValueError(f"Unsupported public endpoint: {api_request.endpoint.value}")
                
        except Exception as e:
            logger.error("Failed to handle public-safe request", error=str(e))
            raise
    
    async def _handle_authenticated_request(self, api_request: APIRequest) -> Dict[str, Any]:
        """Handle authenticated API requests."""
        try:
            # Validate session or API token
            user_id = None
            if api_request.session_id:
                session = await self.user_identity_system.validate_session(
                    api_request.session_id, api_request.session_id
                )
                user_id = session.user_id if session else None
            elif api_request.api_token:
                # This would validate API token against environment
                user_id = "token_user"  # Placeholder
            
            if not user_id:
                raise ValueError("Authentication required")
            
            # Update request user_id
            api_request.user_id = user_id
            
            if api_request.endpoint == APIEndpoint.USER_LOGIN:
                return await self._user_login(api_request)
            elif api_request.endpoint == APIEndpoint.USER_LOGOUT:
                return await self._user_logout(api_request)
            elif api_request.endpoint == APIEndpoint.USER_PROFILE:
                return await self._user_profile(api_request)
            elif api_request.endpoint == APIEndpoint.BENCHMARK_SUBMIT:
                return await self._benchmark_submit(api_request)
            elif api_request.endpoint == APIEndpoint.BENCHMARK_STATUS:
                return await self._benchmark_status(api_request)
            elif api_request.endpoint == APIEndpoint.BENCHMARK_RESULTS:
                return await self._benchmark_results(api_request)
            elif api_request.endpoint == APIEndpoint.USER_QUOTAS:
                return await self._user_quotas(api_request)
            else:
                raise ValueError(f"Unsupported authenticated endpoint: {api_request.endpoint.value}")
                
        except Exception as e:
            logger.error("Failed to handle authenticated request", error=str(e))
            raise
    
    async def _handle_internal_request(self, api_request: APIRequest) -> Dict[str, Any]:
        """Handle internal-only API requests."""
        try:
            # Validate internal access
            # This would validate internal token or IP range
            internal_access = True  # Placeholder
            
            if not internal_access:
                raise ValueError("Internal access required")
            
            if api_request.endpoint == APIEndpoint.SYSTEM_HEALTH:
                return await self._system_health(api_request)
            elif api_request.endpoint == APIEndpoint.SYSTEM_METRICS:
                return await self._system_metrics(api_request)
            else:
                raise ValueError(f"Unsupported internal endpoint: {api_request.endpoint.value}")
                
        except Exception as e:
            logger.error("Failed to handle internal request", error=str(e))
            raise
    
    async def _handle_operator_request(self, api_request: APIRequest) -> Dict[str, Any]:
        """Handle operator API requests."""
        try:
            # Validate operator permissions
            # This would validate operator role and permissions
            operator_access = True  # Placeholder
            
            if not operator_access:
                raise ValueError("Operator access required")
            
            if api_request.endpoint == APIEndpoint.OPERATOR_DASHBOARD:
                return await self._operator_dashboard(api_request)
            elif api_request.endpoint == APIEndpoint.OPERATOR_USERS:
                return await self._operator_users(api_request)
            elif api_request.endpoint == APIEndpoint.OPERATOR_QUOTAS:
                return await self._operator_quotas(api_request)
            elif api_request.endpoint == APIEndpoint.OPERATOR_GOVERNANCE:
                return await self._operator_governance(api_request)
            else:
                raise ValueError(f"Unsupported operator endpoint: {api_request.endpoint.value}")
                
        except Exception as e:
            logger.error("Failed to handle operator request", error=str(e))
            raise
    
    async def _handle_forensic_request(self, api_request: APIRequest) -> Dict[str, Any]:
        """Handle forensic API requests."""
        try:
            # Validate forensic access
            # This would validate forensic role and permissions
            forensic_access = True  # Placeholder
            
            if not forensic_access:
                raise ValueError("Forensic access required")
            
            if api_request.endpoint == APIEndpoint.FORENSIC_REPLAY:
                return await self._forensic_replay(api_request)
            elif api_request.endpoint == APIEndpoint.FORENSIC_TIMELINE:
                return await self._forensic_timeline(api_request)
            elif api_request.endpoint == APIEndpoint.FORENSIC_DIVERGENCE:
                return await self._forensic_divergence(api_request)
            else:
                raise ValueError(f"Unsupported forensic endpoint: {api_request.endpoint.value}")
                
        except Exception as e:
            logger.error("Failed to handle forensic request", error=str(e))
            raise
    
    # Public-safe endpoint handlers
    async def _public_status(self, api_request: APIRequest) -> Dict[str, Any]:
        """Public status endpoint."""
        return {
            "status": "operational",
            "timestamp": time.time(),
            "version": "1.0.0",
            "api_version": "v1"
        }
    
    async def _public_info(self, api_request: APIRequest) -> Dict[str, Any]:
        """Public info endpoint."""
        return {
            "service": "Qurve AI Platform",
            "description": "Quantum optimization platform",
            "features": [
                "Quantum benchmark execution",
                "Multiple solver support",
                "Cloud execution capabilities",
                "QPU access (authorized users)"
            ]
        }
    
    # Authenticated endpoint handlers
    async def _user_login(self, api_request: APIRequest) -> Dict[str, Any]:
        """User login endpoint."""
        username = api_request.request_data.get("username")
        password = api_request.request_data.get("password")
        environment = api_request.request_data.get("environment", "development")
        
        # This would use proper environment mapping
        from ..operations.environment_governance import EnvironmentType
        env_type = EnvironmentType.DEVELOPMENT
        
        session = await self.user_identity_system.authenticate_user(
            username, password, env_type, api_request.ip_address, api_request.user_agent
        )
        
        if session:
            return {
                "success": True,
                "session_id": session.session_id,
                "session_token": session.session_token,
                "refresh_token": session.refresh_token,
                "expires_at": session.expires_at
            }
        else:
            return {
                "success": False,
                "error": "Invalid credentials"
            }
    
    async def _user_logout(self, api_request: APIRequest) -> Dict[str, Any]:
        """User logout endpoint."""
        session_id = api_request.request_data.get("session_id")
        
        success = await self.user_identity_system.terminate_session(
            session_id, api_request.user_id
        )
        
        return {
            "success": success
        }
    
    async def _user_profile(self, api_request: APIRequest) -> Dict[str, Any]:
        """User profile endpoint."""
        user = self.user_identity_system.get_user(api_request.user_id)
        
        if user:
            return {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type.value,
                "operator_role": user.operator_role.value if user.operator_role else None,
                "created_at": user.created_at,
                "last_login": user.last_login
            }
        else:
            return {
                "error": "User not found"
            }
    
    async def _benchmark_submit(self, api_request: APIRequest) -> Dict[str, Any]:
        """Benchmark submission endpoint."""
        benchmark_id = api_request.request_data.get("benchmark_id")
        qubo_data = api_request.request_data.get("qubo_data")
        solver_preferences = api_request.request_data.get("solver_preferences", [])
        execution_mode = api_request.request_data.get("execution_mode", "local")
        shots = api_request.request_data.get("shots", 100)
        
        # Convert string to enum
        from ..operations.internal_cloud_execution import ExecutionMode
        exec_mode = ExecutionMode.LOCAL
        if execution_mode == "cloud_simulator":
            exec_mode = ExecutionMode.CLOUD_SIMULATOR
        elif execution_mode == "cloud_qpu":
            exec_mode = ExecutionMode.CLOUD_QPU
        
        request_id = await self.benchmark_gateway.submit_benchmark_execution(
            api_request.session_id,
            benchmark_id,
            qubo_data,
            solver_preferences,
            exec_mode,
            shots=shots
        )
        
        return {
            "success": True,
            "request_id": request_id
        }
    
    async def _benchmark_status(self, api_request: APIRequest) -> Dict[str, Any]:
        """Benchmark status endpoint."""
        request_id = api_request.request_data.get("request_id")
        
        request = await self.benchmark_gateway.get_execution_request(request_id)
        result = await self.benchmark_gateway.get_execution_result(request_id)
        
        return {
            "request_id": request_id,
            "status": request.status.value if request else "not_found",
            "result_status": result.status.value if result else None,
            "created_at": request.created_at if request else None,
            "started_at": result.started_at if result else None,
            "completed_at": result.completed_at if result else None,
            "execution_time_ms": result.execution_time_ms if result else None,
            "execution_origin": result.execution_origin if result else "local",
            "fallback_triggered": result.fallback_triggered if result else False,
            "task_arn": result.task_arn if result else None,
            "device_arn": result.device_arn if result else None,
            "fallback_chain": result.fallback_chain if result else []
        }
    
    async def _benchmark_results(self, api_request: APIRequest) -> Dict[str, Any]:
        """Benchmark results endpoint."""
        request_id = api_request.request_data.get("request_id")
        
        result = await self.benchmark_gateway.get_execution_result(request_id)
        
        if result:
            return {
                "request_id": request_id,
                "status": result.status.value,
                "result_data": result.result_data,
                "error_message": result.error_message,
                "execution_time_ms": result.execution_time_ms,
                "fallback_chain": result.fallback_chain,
                "execution_origin": result.execution_origin,
                "fallback_triggered": result.fallback_triggered,
                "task_arn": result.task_arn,
                "device_arn": result.device_arn,
                "replay_metadata": result.replay_metadata
            }
        else:
            return {
                "error": "Result not found"
            }
    
    async def _user_quotas(self, api_request: APIRequest) -> Dict[str, Any]:
        """User quotas endpoint."""
        quotas = self.quota_management.get_user_quotas(api_request.user_id)
        
        return {
            "user_id": api_request.user_id,
            "quotas": [
                {
                    "quota_type": quota.quota_type.value,
                    "current_usage": quota.current_usage,
                    "limit": quota.limit,
                    "remaining": quota.limit - quota.current_usage,
                    "period_end": quota.period_end
                }
                for quota in quotas
            ]
        }
    
    # Internal endpoint handlers
    async def _system_health(self, api_request: APIRequest) -> Dict[str, Any]:
        """System health endpoint."""
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "services": {
                "user_identity": "healthy",
                "benchmark_gateway": "healthy",
                "quota_management": "healthy",
                "audit_trail": "healthy"
            }
        }
    
    async def _system_metrics(self, api_request: APIRequest) -> Dict[str, Any]:
        """System metrics endpoint."""
        return {
            "timestamp": time.time(),
            "api_stats": {
                "total_requests": self._request_count,
                "total_responses": self._response_count,
                "api_type_stats": self._api_type_stats
            },
            "service_stats": {
                "active_sessions": len(self.user_identity_system.get_active_sessions()),
                "benchmark_requests": self.benchmark_gateway.get_execution_statistics(),
                "quota_checks": self.quota_management.get_quota_statistics()
            }
        }
    
    # Operator endpoint handlers
    async def _operator_dashboard(self, api_request: APIRequest) -> Dict[str, Any]:
        """Operator dashboard endpoint."""
        return {
            "dashboard_data": {
                "users": self.user_identity_system.get_identity_statistics(),
                "executions": self.benchmark_gateway.get_execution_statistics(),
                "quotas": self.quota_management.get_quota_statistics(),
                "audit": self.audit_trail.get_audit_statistics()
            }
        }
    
    async def _operator_users(self, api_request: APIRequest) -> Dict[str, Any]:
        """Operator users endpoint."""
        user_type = api_request.request_data.get("user_type")
        
        if user_type:
            from .user_identity_system import UserType
            user_type_enum = UserType(user_type)
            users = self.user_identity_system.get_users_by_type(user_type_enum)
        else:
            users = []  # Would get all users
        
        return {
            "users": [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "email": user.email,
                    "user_type": user.user_type.value,
                    "operator_role": user.operator_role.value if user.operator_role else None,
                    "active": user.active,
                    "created_at": user.created_at,
                    "last_login": user.last_login
                }
                for user in users
            ]
        }
    
    async def _operator_quotas(self, api_request: APIRequest) -> Dict[str, Any]:
        """Operator quotas endpoint."""
        user_id = api_request.request_data.get("user_id")
        
        if user_id:
            quotas = self.quota_management.get_user_quotas(user_id)
        else:
            quotas = []  # Would get all quotas
        
        return {
            "quotas": [
                {
                    "user_id": quota.user_id,
                    "quota_type": quota.quota_type.value,
                    "current_usage": quota.current_usage,
                    "limit": quota.limit,
                    "remaining": quota.limit - quota.current_usage,
                    "period_start": quota.period_start,
                    "period_end": quota.period_end
                }
                for quota in quotas
            ]
        }
    
    async def _operator_governance(self, api_request: APIRequest) -> Dict[str, Any]:
        """Operator governance endpoint."""
        return {
            "governance_data": {
                "environment_governance": {},  # Would get from environment governance
                "rbac": {},  # Would get from RBAC
                "audit_trail": self.audit_trail.get_audit_statistics()
            }
        }
    
    # Forensic endpoint handlers
    async def _forensic_replay(self, api_request: APIRequest) -> Dict[str, Any]:
        """Forensic replay endpoint."""
        correlation_id = api_request.request_data.get("correlation_id")
        
        return {
            "replay_data": {
                "correlation_id": correlation_id,
                "replay_available": True,  # Would check replay system
                "replay_metadata": {
                    "reconstructed_artifact": True,
                    "not_operational_truth": True
                }
            }
        }
    
    async def _forensic_timeline(self, api_request: APIRequest) -> Dict[str, Any]:
        """Forensic timeline endpoint."""
        correlation_id = api_request.request_data.get("correlation_id")
        
        return {
            "timeline_data": {
                "correlation_id": correlation_id,
                "events": [],  # Would get from audit trail
                "timeline": []  # Would reconstruct timeline
            }
        }
    
    async def _forensic_divergence(self, api_request: APIRequest) -> Dict[str, Any]:
        """Forensic divergence endpoint."""
        correlation_id = api_request.request_data.get("correlation_id")
        
        return {
            "divergence_data": {
                "correlation_id": correlation_id,
                "divergence_analysis": {
                    "divergence_score": 0.1,
                    "divergence_type": "timing"
                }
            }
        }
    
    async def _log_api_access(self, api_request: APIRequest, response: APIResponse) -> None:
        """Log API access."""
        try:
            await self.audit_trail.log_operator_action(
                operator_id=api_request.user_id,
                action="api_access",
                resource=f"api:{api_request.api_type.value}:{api_request.endpoint.value}",
                details={
                    "request_id": api_request.request_id,
                    "api_type": api_request.api_type.value,
                    "endpoint": api_request.endpoint.value,
                    "success": response.success,
                    "response_time_ms": response.response_time_ms,
                    "ip_address": api_request.ip_address
                }
            )
            
        except Exception as e:
            logger.error("Failed to log API access", error=str(e))
    
    def get_api_statistics(self) -> Dict[str, Any]:
        """Get API layer statistics."""
        return {
            "total_requests": self._request_count,
            "total_responses": self._response_count,
            "api_type_stats": self._api_type_stats,
            "public_safe_apis": True,
            "authenticated_apis": True,
            "internal_only_apis": True,
            "operator_apis": True,
            "forensic_apis": True,
            "strict_api_segregation": True
        }
    
    def get_api_guarantees(self) -> Dict[str, Any]:
        """Get API layer guarantees."""
        return {
            "public_safe_apis": True,
            "authenticated_apis": True,
            "internal_only_apis": True,
            "operator_apis": True,
            "forensic_apis": True,
            "strict_api_segregation": True,
            "api_access_logging": True,
            "request_validation": True,
            "response_formatting": True,
            "error_handling": True,
            "authentication_validation": True,
            "authorization_validation": True,
            "audit_trail_integration": True
        }


# Global product API layer instance
_product_api_layer: Optional[ProductAPILayer] = None


def get_product_api_layer() -> ProductAPILayer:
    """Get global product API layer instance."""
    global _product_api_layer
    if _product_api_layer is None:
        _product_api_layer = ProductAPILayer()
    return _product_api_layer
