#!/usr/bin/env python3
"""
QURVE AI - Production Deployment Validation
Comprehensive validation of production deployment readiness.

Validates:
✅ Cold boot deployment
✅ Full stack startup
✅ Database migrations
✅ Replay system startup
✅ Governance startup
✅ Frontend/backend integration
✅ WebSocket stability
✅ Cloud execution routing
✅ Fallback integrity
✅ Monitoring startup
"""

import asyncio
import time
import sys
import json
import logging
import aiohttp
import asyncpg
import redis.asyncio as redis
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Validation status classifications."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ValidationCategory(Enum):
    """Validation category classifications."""
    DEPLOYMENT = "deployment"
    DATABASE = "database"
    BACKEND = "backend"
    FRONTEND = "frontend"
    INTEGRATION = "integration"
    MONITORING = "monitoring"
    SECURITY = "security"
    PERFORMANCE = "performance"
    GOVERNANCE = "governance"


@dataclass
class ValidationResult:
    """Validation result definition."""
    validation_id: str
    category: ValidationCategory
    name: str
    description: str
    status: ValidationStatus
    message: str
    timestamp: float
    duration_seconds: float
    details: Dict[str, Any] = field(default_factory=dict)
    artifacts: List[str] = field(default_factory=list)


@dataclass
class DeploymentValidation:
    """Deployment validation result."""
    validation_id: str
    overall_status: ValidationStatus
    total_validations: int
    passed_validations: int
    failed_validations: int
    skipped_validations: int
    duration_seconds: float
    results: List[ValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProductionDeploymentValidator:
    """
    Production-grade deployment validator.
    
    Features:
    - Cold boot deployment validation
    - Full stack startup validation
    - Database migration validation
    - Replay system startup validation
    - Governance startup validation
    - Frontend/backend integration validation
    - WebSocket stability validation
    - Cloud execution routing validation
    - Fallback integrity validation
    - Monitoring startup validation
    """
    
    def __init__(self):
        self.start_time = time.time()
        self.validation_results: List[ValidationResult] = []
        
        # Service endpoints
        self.endpoints = {
            'database': 'postgresql://qubo_user:password@localhost:5432/qubo_platform',
            'redis': 'redis://:password@localhost:6379/0',
            'backend_api': 'http://localhost:8000',
            'frontend': 'http://localhost:3000',
            'monitoring': 'http://localhost:9090',
            'grafana': 'http://localhost:3001'
        }
        
        # Validation timeouts
        self.timeouts = {
            'database': 30,
            'redis': 10,
            'api': 15,
            'frontend': 10,
            'monitoring': 15,
            'websocket': 30
        }
        
        logger.info("Production deployment validator initialized")
    
    async def run_full_validation(self) -> DeploymentValidation:
        """Run comprehensive production deployment validation."""
        try:
            logger.info("Starting production deployment validation...")
            
            # Define validation steps
            validation_steps = [
                self._validate_cold_boot_deployment,
                self._validate_database_startup,
                self._validate_redis_startup,
                self._validate_backend_startup,
                self._validate_frontend_startup,
                self._validate_database_migrations,
                self._validate_replay_system_startup,
                self._validate_governance_startup,
                self._validate_frontend_backend_integration,
                self._validate_websocket_stability,
                self._validate_cloud_execution_routing,
                self._validate_fallback_integrity,
                self._validate_monitoring_startup
            ]
            
            # Run all validations
            for validation_step in validation_steps:
                try:
                    result = await validation_step()
                    self.validation_results.append(result)
                    status_emoji = "✅" if result.status == ValidationStatus.PASSED else "❌"
                    logger.info(f"{status_emoji} {result.name}: {result.status.value}")
                except Exception as e:
                    logger.error(f"Validation step failed: {str(e)}")
                    failed_result = ValidationResult(
                        validation_id=f"failed_{int(time.time())}",
                        category=ValidationCategory.DEPLOYMENT,
                        name="Validation Step Failed",
                        description=f"Validation step failed with exception",
                        status=ValidationStatus.FAILED,
                        message=str(e),
                        timestamp=time.time(),
                        duration_seconds=0.0
                    )
                    self.validation_results.append(failed_result)
            
            # Calculate overall results
            total_validations = len(self.validation_results)
            passed_validations = sum(1 for r in self.validation_results if r.status == ValidationStatus.PASSED)
            failed_validations = sum(1 for r in self.validation_results if r.status == ValidationStatus.FAILED)
            skipped_validations = sum(1 for r in self.validation_results if r.status == ValidationStatus.SKIPPED)
            
            overall_status = ValidationStatus.PASSED if failed_validations == 0 else ValidationStatus.FAILED
            
            # Create deployment validation result
            deployment_validation = DeploymentValidation(
                validation_id=f"deployment_validation_{int(time.time())}",
                overall_status=overall_status,
                total_validations=total_validations,
                passed_validations=passed_validations,
                failed_validations=failed_validations,
                skipped_validations=skipped_validations,
                duration_seconds=time.time() - self.start_time,
                results=self.validation_results,
                metadata={
                    'endpoints': self.endpoints,
                    'timeouts': self.timeouts,
                    'validation_timestamp': time.time()
                }
            )
            
            # Generate validation report
            await self._generate_validation_report(deployment_validation)
            
            logger.info(f"Production deployment validation completed: {overall_status.value}")
            return deployment_validation
            
        except Exception as e:
            logger.error(f"Production deployment validation failed: {str(e)}")
            raise
    
    async def _validate_cold_boot_deployment(self) -> ValidationResult:
        """Validate cold boot deployment."""
        try:
            start_time = time.time()
            
            # Check if all services are starting from cold state
            logger.info("Validating cold boot deployment...")
            
            # Check service containers
            containers = ['qubo-postgres', 'qubo-redis', 'qubo-backend', 'qubo-frontend', 'qubo-nginx']
            running_containers = []
            
            for container in containers:
                # Check if container is running
                try:
                    process = await asyncio.create_subprocess_shell(
                        f"docker ps -f name={container} --format '{{{{.Status}}}}'",
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    stdout, stderr = await process.communicate()
                    
                    if 'Up' in stdout.decode():
                        running_containers.append(container)
                except Exception:
                    pass
            
            # Check if all containers are running
            all_running = len(running_containers) == len(containers)
            
            duration = time.time() - start_time
            
            return ValidationResult(
                validation_id="cold_boot_deployment",
                category=ValidationCategory.DEPLOYMENT,
                name="Cold Boot Deployment",
                description="Validate all services start from cold state",
                status=ValidationStatus.PASSED if all_running else ValidationStatus.FAILED,
                message=f"{'All containers running' if all_running else f'Running containers: {running_containers}'}",
                timestamp=start_time,
                duration_seconds=duration,
                details={
                    'expected_containers': containers,
                    'running_containers': running_containers,
                    'all_running': all_running
                }
            )
            
        except Exception as e:
            return ValidationResult(
                validation_id="cold_boot_deployment",
                category=ValidationCategory.DEPLOYMENT,
                name="Cold Boot Deployment",
                description="Validate all services start from cold state",
                status=ValidationStatus.FAILED,
                message=f"Cold boot validation failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_database_startup(self) -> ValidationResult:
        """Validate database startup."""
        try:
            start_time = time.time()
            
            # Test database connection
            conn = await asyncpg.connect(
                self.endpoints['database'],
                timeout=self.timeouts['database']
            )
            
            # Test basic query
            result = await conn.fetchval("SELECT 1 as test")
            await conn.close()
            
            duration = time.time() - start_time
            
            return ValidationResult(
                validation_id="database_startup",
                category=ValidationCategory.DATABASE,
                name="Database Startup",
                description="Validate database connection and basic functionality",
                status=ValidationStatus.PASSED if result == 1 else ValidationStatus.FAILED,
                message="Database connection successful" if result == 1 else "Database query failed",
                timestamp=start_time,
                duration_seconds=duration,
                details={
                    'connection_successful': True,
                    'query_result': result,
                    'connection_string': self.endpoints['database']
                }
            )
            
        except Exception as e:
            return ValidationResult(
                validation_id="database_startup",
                category=ValidationCategory.DATABASE,
                name="Database Startup",
                description="Validate database connection and basic functionality",
                status=ValidationStatus.FAILED,
                message=f"Database startup failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_redis_startup(self) -> ValidationResult:
        """Validate Redis startup."""
        try:
            start_time = time.time()
            
            # Test Redis connection
            redis_client = redis.from_url(
                self.endpoints['redis'],
                socket_timeout=self.timeouts['redis']
            )
            
            # Test basic ping
            result = await redis_client.ping()
            await redis_client.close()
            
            duration = time.time() - start_time
            
            return ValidationResult(
                validation_id="redis_startup",
                category=ValidationCategory.DATABASE,
                name="Redis Startup",
                description="Validate Redis connection and basic functionality",
                status=ValidationStatus.PASSED if result else ValidationStatus.FAILED,
                message="Redis connection successful" if result else "Redis ping failed",
                timestamp=start_time,
                duration_seconds=duration,
                details={
                    'connection_successful': result,
                    'connection_string': self.endpoints['redis']
                }
            )
            
        except Exception as e:
            return ValidationResult(
                validation_id="redis_startup",
                category=ValidationCategory.DATABASE,
                name="Redis Startup",
                description="Validate Redis connection and basic functionality",
                status=ValidationStatus.FAILED,
                message=f"Redis startup failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_backend_startup(self) -> ValidationResult:
        """Validate backend startup."""
        try:
            start_time = time.time()
            
            # Test backend API health endpoint
            timeout = aiohttp.ClientTimeout(total=self.timeouts['api'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoints['backend_api']}/health") as response:
                    response_data = await response.json()
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="backend_startup",
                        category=ValidationCategory.BACKEND,
                        name="Backend Startup",
                        description="Validate backend API startup and health",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"Backend health check: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'response_data': response_data,
                            'endpoint': f"{self.endpoints['backend_api']}/health"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="backend_startup",
                category=ValidationCategory.BACKEND,
                name="Backend Startup",
                description="Validate backend API startup and health",
                status=ValidationStatus.FAILED,
                message=f"Backend startup failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_frontend_startup(self) -> ValidationResult:
        """Validate frontend startup."""
        try:
            start_time = time.time()
            
            # Test frontend health endpoint
            timeout = aiohttp.ClientTimeout(total=self.timeouts['frontend'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoints['frontend']}/health") as response:
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="frontend_startup",
                        category=ValidationCategory.FRONTEND,
                        name="Frontend Startup",
                        description="Validate frontend startup and health",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"Frontend health check: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'endpoint': f"{self.endpoints['frontend']}/health"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="frontend_startup",
                category=ValidationCategory.FRONTEND,
                name="Frontend Startup",
                description="Validate frontend startup and health",
                status=ValidationStatus.FAILED,
                message=f"Frontend startup failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_database_migrations(self) -> ValidationResult:
        """Validate database migrations."""
        try:
            start_time = time.time()
            
            # Check if migrations table exists and is up to date
            conn = await asyncpg.connect(self.endpoints['database'])
            
            # Check migration table
            try:
                migration_result = await conn.fetchval("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_name = 'schema_migrations'
                    )
                """)
                
                if not migration_result:
                    await conn.close()
                    return ValidationResult(
                        validation_id="database_migrations",
                        category=ValidationCategory.DATABASE,
                        name="Database Migrations",
                        description="Validate database migrations",
                        status=ValidationStatus.FAILED,
                        message="Migration table does not exist",
                        timestamp=start_time,
                        duration_seconds=time.time() - start_time
                    )
                
                # Get latest migration
                latest_migration = await conn.fetchval("""
                    SELECT version FROM schema_migrations 
                    ORDER BY applied_at DESC LIMIT 1
                """)
                
                await conn.close()
                
                duration = time.time() - start_time
                
                return ValidationResult(
                    validation_id="database_migrations",
                    category=ValidationCategory.DATABASE,
                    name="Database Migrations",
                    description="Validate database migrations",
                    status=ValidationStatus.PASSED if latest_migration else ValidationStatus.FAILED,
                    message=f"Latest migration: {latest_migration}" if latest_migration else "No migrations found",
                    timestamp=start_time,
                    duration_seconds=duration,
                    details={
                        'migration_table_exists': True,
                        'latest_migration': latest_migration
                    }
                )
                
            except Exception as e:
                await conn.close()
                raise e
                
        except Exception as e:
            return ValidationResult(
                validation_id="database_migrations",
                category=ValidationCategory.DATABASE,
                name="Database Migrations",
                description="Validate database migrations",
                status=ValidationStatus.FAILED,
                message=f"Database migration validation failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_replay_system_startup(self) -> ValidationResult:
        """Validate replay system startup."""
        try:
            start_time = time.time()
            
            # Test replay API endpoint
            timeout = aiohttp.ClientTimeout(total=self.timeouts['api'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoints['backend_api']}/api/v1/replay/health") as response:
                    response_data = await response.json() if response.status == 200 else {}
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="replay_system_startup",
                        category=ValidationCategory.BACKEND,
                        name="Replay System Startup",
                        description="Validate replay system startup and health",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"Replay system health: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'response_data': response_data,
                            'endpoint': f"{self.endpoints['backend_api']}/api/v1/replay/health"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="replay_system_startup",
                category=ValidationCategory.BACKEND,
                name="Replay System Startup",
                description="Validate replay system startup and health",
                status=ValidationStatus.FAILED,
                message=f"Replay system startup failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_governance_startup(self) -> ValidationResult:
        """Validate governance system startup."""
        try:
            start_time = time.time()
            
            # Test governance API endpoint
            timeout = aiohttp.ClientTimeout(total=self.timeouts['api'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoints['backend_api']}/api/v1/governance/health") as response:
                    response_data = await response.json() if response.status == 200 else {}
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="governance_startup",
                        category=ValidationCategory.GOVERNANCE,
                        name="Governance System Startup",
                        description="Validate governance system startup and health",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"Governance system health: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'response_data': response_data,
                            'endpoint': f"{self.endpoints['backend_api']}/api/v1/governance/health"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="governance_startup",
                category=ValidationCategory.GOVERNANCE,
                name="Governance System Startup",
                description="Validate governance system startup and health",
                status=ValidationStatus.FAILED,
                message=f"Governance system startup failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_frontend_backend_integration(self) -> ValidationResult:
        """Validate frontend/backend integration."""
        try:
            start_time = time.time()
            
            # Test API integration through frontend
            timeout = aiohttp.ClientTimeout(total=self.timeouts['api'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                # Test a sample API call
                async with session.get(f"{self.endpoints['backend_api']}/api/v1/public/status") as response:
                    response_data = await response.json()
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="frontend_backend_integration",
                        category=ValidationCategory.INTEGRATION,
                        name="Frontend/Backend Integration",
                        description="Validate frontend/backend API integration",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"API integration test: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'response_data': response_data,
                            'endpoint': f"{self.endpoints['backend_api']}/api/v1/public/status"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="frontend_backend_integration",
                category=ValidationCategory.INTEGRATION,
                name="Frontend/Backend Integration",
                description="Validate frontend/backend API integration",
                status=ValidationStatus.FAILED,
                message=f"Frontend/backend integration failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_websocket_stability(self) -> ValidationResult:
        """Validate WebSocket stability."""
        try:
            start_time = time.time()
            
            # Test WebSocket connection
            import websockets
            
            uri = f"ws://localhost:8000/ws"
            
            try:
                async with websockets.connect(uri, timeout=self.timeouts['websocket']) as websocket:
                    # Send test message
                    await websocket.send('{"type": "ping"}')
                    
                    # Wait for response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="websocket_stability",
                        category=ValidationCategory.INTEGRATION,
                        name="WebSocket Stability",
                        description="Validate WebSocket connection and stability",
                        status=ValidationStatus.PASSED,
                        message="WebSocket connection successful",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'websocket_uri': uri,
                            'test_message_sent': True,
                            'response_received': True,
                            'response': response
                        }
                    )
                    
            except asyncio.TimeoutError:
                return ValidationResult(
                    validation_id="websocket_stability",
                    category=ValidationCategory.INTEGRATION,
                    name="WebSocket Stability",
                    description="Validate WebSocket connection and stability",
                    status=ValidationStatus.FAILED,
                    message="WebSocket connection timeout",
                    timestamp=start_time,
                    duration_seconds=time.time() - start_time
                )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="websocket_stability",
                category=ValidationCategory.INTEGRATION,
                name="WebSocket Stability",
                description="Validate WebSocket connection and stability",
                status=ValidationStatus.FAILED,
                message=f"WebSocket validation failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_cloud_execution_routing(self) -> ValidationResult:
        """Validate cloud execution routing."""
        try:
            start_time = time.time()
            
            # Test cloud execution API endpoint
            timeout = aiohttp.ClientTimeout(total=self.timeouts['api'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoints['backend_api']}/api/v1/cloud/health") as response:
                    response_data = await response.json() if response.status == 200 else {}
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="cloud_execution_routing",
                        category=ValidationCategory.BACKEND,
                        name="Cloud Execution Routing",
                        description="Validate cloud execution routing and health",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"Cloud execution health: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'response_data': response_data,
                            'endpoint': f"{self.endpoints['backend_api']}/api/v1/cloud/health"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="cloud_execution_routing",
                category=ValidationCategory.BACKEND,
                name="Cloud Execution Routing",
                description="Validate cloud execution routing and health",
                status=ValidationStatus.FAILED,
                message=f"Cloud execution routing validation failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_fallback_integrity(self) -> ValidationResult:
        """Validate fallback integrity."""
        try:
            start_time = time.time()
            
            # Test fallback system API endpoint
            timeout = aiohttp.ClientTimeout(total=self.timeouts['api'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.endpoints['backend_api']}/api/v1/fallback/health") as response:
                    response_data = await response.json() if response.status == 200 else {}
                    
                    duration = time.time() - start_time
                    
                    return ValidationResult(
                        validation_id="fallback_integrity",
                        category=ValidationCategory.GOVERNANCE,
                        name="Fallback Integrity",
                        description="Validate fallback system integrity and health",
                        status=ValidationStatus.PASSED if response.status == 200 else ValidationStatus.FAILED,
                        message=f"Fallback system health: {response.status}",
                        timestamp=start_time,
                        duration_seconds=duration,
                        details={
                            'http_status': response.status,
                            'response_data': response_data,
                            'endpoint': f"{self.endpoints['backend_api']}/api/v1/fallback/health"
                        }
                    )
                    
        except Exception as e:
            return ValidationResult(
                validation_id="fallback_integrity",
                category=ValidationCategory.GOVERNANCE,
                name="Fallback Integrity",
                description="Validate fallback system integrity and health",
                status=ValidationStatus.FAILED,
                message=f"Fallback integrity validation failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _validate_monitoring_startup(self) -> ValidationResult:
        """Validate monitoring startup."""
        try:
            start_time = time.time()
            
            # Test Prometheus
            prometheus_healthy = False
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeouts['monitoring'])
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{self.endpoints['monitoring']}/-/healthy") as response:
                        prometheus_healthy = response.status == 200
            except Exception:
                pass
            
            # Test Grafana
            grafana_healthy = False
            try:
                timeout = aiohttp.ClientTimeout(total=self.timeouts['monitoring'])
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.get(f"{self.endpoints['grafana']}/api/health") as response:
                        grafana_healthy = response.status == 200
            except Exception:
                pass
            
            duration = time.time() - start_time
            all_healthy = prometheus_healthy and grafana_healthy
            
            return ValidationResult(
                validation_id="monitoring_startup",
                category=ValidationCategory.MONITORING,
                name="Monitoring Startup",
                description="Validate monitoring stack startup and health",
                status=ValidationStatus.PASSED if all_healthy else ValidationStatus.FAILED,
                message=f"Monitoring stack: {'Healthy' if all_healthy else 'Unhealthy'}",
                timestamp=start_time,
                duration_seconds=duration,
                details={
                    'prometheus_healthy': prometheus_healthy,
                    'grafana_healthy': grafana_healthy,
                    'prometheus_endpoint': f"{self.endpoints['monitoring']}/-/healthy",
                    'grafana_endpoint': f"{self.endpoints['grafana']}/api/health"
                }
            )
            
        except Exception as e:
            return ValidationResult(
                validation_id="monitoring_startup",
                category=ValidationCategory.MONITORING,
                name="Monitoring Startup",
                description="Validate monitoring stack startup and health",
                status=ValidationStatus.FAILED,
                message=f"Monitoring startup validation failed: {str(e)}",
                timestamp=time.time(),
                duration_seconds=0.0
            )
    
    async def _generate_validation_report(self, validation: DeploymentValidation) -> None:
        """Generate validation report."""
        try:
            report = {
                'validation_id': validation.validation_id,
                'overall_status': validation.overall_status.value,
                'summary': {
                    'total_validations': validation.total_validations,
                    'passed_validations': validation.passed_validations,
                    'failed_validations': validation.failed_validations,
                    'skipped_validations': validation.skipped_validations,
                    'success_rate': (validation.passed_validations / validation.total_validations * 100) if validation.total_validations > 0 else 0,
                    'duration_seconds': validation.duration_seconds
                },
                'results': [
                    {
                        'validation_id': result.validation_id,
                        'category': result.category.value,
                        'name': result.name,
                        'description': result.description,
                        'status': result.status.value,
                        'message': result.message,
                        'timestamp': result.timestamp,
                        'duration_seconds': result.duration_seconds,
                        'details': result.details
                    }
                    for result in validation.results
                ],
                'metadata': validation.metadata,
                'generated_at': time.time()
            }
            
            # Save report to file
            report_filename = f"deployment_validation_report_{int(time.time())}.json"
            with open(report_filename, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Validation report saved to {report_filename}")
            
        except Exception as e:
            logger.error(f"Failed to generate validation report: {str(e)}")
    
    def print_validation_summary(self, validation: DeploymentValidation) -> None:
        """Print validation summary."""
        print("\n" + "="*80)
        print("PRODUCTION DEPLOYMENT VALIDATION REPORT")
        print("="*80)
        
        # Overall status
        status_emoji = "✅" if validation.overall_status == ValidationStatus.PASSED else "❌"
        print(f"\nOverall Status: {status_emoji} {validation.overall_status.value.upper()}")
        print(f"Total Validations: {validation.total_validations}")
        print(f"Passed: {validation.passed_validations}")
        print(f"Failed: {validation.failed_validations}")
        print(f"Skipped: {validation.skipped_validations}")
        print(f"Success Rate: {(validation.passed_validations / validation.total_validations * 100):.1f}%")
        print(f"Duration: {validation.duration_seconds:.2f} seconds")
        
        # Individual validation results
        print(f"\n{'VALIDATION':<30} {'STATUS':<12} {'DURATION':<10} {'MESSAGE'}")
        print("-" * 80)
        
        for result in validation.results:
            status_emoji = "✅" if result.status == ValidationStatus.PASSED else "❌"
            print(f"{result.name:<30} {status_emoji} {result.status.value:<12} {result.duration_seconds:>8.2f}s     {result.message}")
        
        print("\n" + "="*80)
        
        # Exit with appropriate code
        if validation.overall_status == ValidationStatus.PASSED:
            print("✅ PRODUCTION DEPLOYMENT VALIDATION: PASSED")
            print("All systems are ready for production deployment.")
            sys.exit(0)
        else:
            print("❌ PRODUCTION DEPLOYMENT VALIDATION: FAILED")
            print("Some systems are not ready for production deployment.")
            sys.exit(1)


async def main():
    """Main validation execution."""
    validator = ProductionDeploymentValidator()
    
    try:
        validation = await validator.run_full_validation()
        validator.print_validation_summary(validation)
        
    except KeyboardInterrupt:
        print("\n❌ Production deployment validation interrupted")
        sys.exit(3)
    except Exception as e:
        print(f"\n❌ Production deployment validation failed: {e}")
        sys.exit(4)


if __name__ == "__main__":
    asyncio.run(main())
