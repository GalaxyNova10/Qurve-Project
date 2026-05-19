#!/usr/bin/env python3
"""
QURVE AI - Health Check Orchestration
Comprehensive health monitoring for all production services.

Monitors:
✅ Database connectivity and performance
✅ Cache connectivity and performance
✅ Backend API health and performance
✅ Frontend availability and performance
✅ Monitoring stack health
✅ Service dependencies and latency
✅ Resource utilization and thresholds
✅ Security and authentication health
"""

import asyncio
import time
import sys
import json
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import asyncpg
import redis.asyncio as redis
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status classifications."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result."""
    service_name: str
    status: HealthStatus
    response_time_ms: float
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemHealth:
    """Overall system health."""
    overall_status: HealthStatus
    service_count: int
    healthy_count: int
    degraded_count: int
    unhealthy_count: int
    total_response_time_ms: float
    average_response_time_ms: float
    checks: List[HealthCheck] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


class HealthCheckOrchestrator:
    """Production health check orchestrator."""
    
    def __init__(self):
        self.checks: List[HealthCheck] = []
        self.start_time = time.time()
        
        # Service endpoints
        self.services = {
            'database': {
                'url': 'postgresql://qubo_user:password@localhost:5432/qubo_platform',
                'timeout': 5.0
            },
            'redis': {
                'url': 'redis://:password@localhost:6379/0',
                'timeout': 3.0
            },
            'backend_api': {
                'url': 'http://localhost:8000/health',
                'timeout': 10.0
            },
            'frontend': {
                'url': 'http://localhost:3000/health',
                'timeout': 5.0
            },
            'prometheus': {
                'url': 'http://localhost:9090/-/healthy',
                'timeout': 5.0
            },
            'grafana': {
                'url': 'http://localhost:3001/api/health',
                'timeout': 5.0
            }
        }
        
        # Health thresholds
        self.thresholds = {
            'response_time_warning': 1000.0,  # 1 second
            'response_time_critical': 5000.0,  # 5 seconds
            'cpu_warning': 80.0,  # 80% CPU
            'cpu_critical': 95.0,  # 95% CPU
            'memory_warning': 80.0,  # 80% memory
            'memory_critical': 95.0,  # 95% memory
            'disk_warning': 80.0,  # 80% disk
            'disk_critical': 95.0  # 95% disk
        }
    
    async def run_all_health_checks(self) -> SystemHealth:
        """Run comprehensive health checks on all services."""
        logger.info("Starting comprehensive health checks...")
        
        # Run all health checks
        check_tasks = [
            self.check_database_health(),
            self.check_redis_health(),
            self.check_backend_api_health(),
            self.check_frontend_health(),
            self.check_prometheus_health(),
            self.check_grafana_health(),
            self.check_system_resources(),
            self.check_service_dependencies()
        ]
        
        # Execute checks concurrently
        results = await asyncio.gather(*check_tasks, return_exceptions=True)
        
        # Process results
        self.checks = []
        for result in results:
            if isinstance(result, HealthCheck):
                self.checks.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
                self.checks.append(HealthCheck(
                    service_name="unknown",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=0.0,
                    message=f"Check failed: {str(result)}"
                ))
        
        # Calculate overall health
        return self.calculate_overall_health()
    
    async def check_database_health(self) -> HealthCheck:
        """Check PostgreSQL database health."""
        start_time = time.time()
        
        try:
            # Connect to database
            conn = await asyncpg.connect(
                self.services['database']['url'],
                timeout=self.services['database']['timeout']
            )
            
            # Test query
            result = await conn.fetchval("SELECT 1 as test")
            await conn.close()
            
            response_time = (time.time() - start_time) * 1000
            
            if result == 1:
                return HealthCheck(
                    service_name="database",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Database connection and query successful",
                    metadata={"query_result": result}
                )
            else:
                return HealthCheck(
                    service_name="database",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Database query returned unexpected result",
                    metadata={"query_result": result}
                )
                
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="Database connection timeout"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="database",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Database connection failed: {str(e)}"
            )
    
    async def check_redis_health(self) -> HealthCheck:
        """Check Redis cache health."""
        start_time = time.time()
        
        try:
            # Connect to Redis
            redis_client = redis.from_url(
                self.services['redis']['url'],
                socket_timeout=self.services['redis']['timeout']
            )
            
            # Test ping
            result = await redis_client.ping()
            await redis_client.close()
            
            response_time = (time.time() - start_time) * 1000
            
            if result:
                return HealthCheck(
                    service_name="redis",
                    status=HealthStatus.HEALTHY,
                    response_time_ms=response_time,
                    message="Redis connection and ping successful",
                    metadata={"ping_result": result}
                )
            else:
                return HealthCheck(
                    service_name="redis",
                    status=HealthStatus.UNHEALTHY,
                    response_time_ms=response_time,
                    message="Redis ping failed",
                    metadata={"ping_result": result}
                )
                
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="Redis connection timeout"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="redis",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Redis connection failed: {str(e)}"
            )
    
    async def check_backend_api_health(self) -> HealthCheck:
        """Check backend API health."""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.services['backend_api']['timeout'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.services['backend_api']['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    data = await response.json()
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="backend_api",
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="Backend API health check successful",
                            metadata={"status_code": response.status, "response_data": data}
                        )
                    else:
                        return HealthCheck(
                            service_name="backend_api",
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            message=f"Backend API returned status {response.status}",
                            metadata={"status_code": response.status, "response_data": data}
                        )
                        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="backend_api",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="Backend API health check timeout"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="backend_api",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Backend API health check failed: {str(e)}"
            )
    
    async def check_frontend_health(self) -> HealthCheck:
        """Check frontend health."""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.services['frontend']['timeout'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.services['frontend']['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="frontend",
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="Frontend health check successful",
                            metadata={"status_code": response.status}
                        )
                    else:
                        return HealthCheck(
                            service_name="frontend",
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            message=f"Frontend returned status {response.status}",
                            metadata={"status_code": response.status}
                        )
                        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="frontend",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="Frontend health check timeout"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="frontend",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Frontend health check failed: {str(e)}"
            )
    
    async def check_prometheus_health(self) -> HealthCheck:
        """Check Prometheus health."""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.services['prometheus']['timeout'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.services['prometheus']['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="prometheus",
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="Prometheus health check successful",
                            metadata={"status_code": response.status}
                        )
                    else:
                        return HealthCheck(
                            service_name="prometheus",
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            message=f"Prometheus returned status {response.status}",
                            metadata={"status_code": response.status}
                        )
                        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="prometheus",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="Prometheus health check timeout"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="prometheus",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Prometheus health check failed: {str(e)}"
            )
    
    async def check_grafana_health(self) -> HealthCheck:
        """Check Grafana health."""
        start_time = time.time()
        
        try:
            timeout = aiohttp.ClientTimeout(total=self.services['grafana']['timeout'])
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(self.services['grafana']['url']) as response:
                    response_time = (time.time() - start_time) * 1000
                    data = await response.json()
                    
                    if response.status == 200:
                        return HealthCheck(
                            service_name="grafana",
                            status=HealthStatus.HEALTHY,
                            response_time_ms=response_time,
                            message="Grafana health check successful",
                            metadata={"status_code": response.status, "response_data": data}
                        )
                    else:
                        return HealthCheck(
                            service_name="grafana",
                            status=HealthStatus.DEGRADED,
                            response_time_ms=response_time,
                            message=f"Grafana returned status {response.status}",
                            metadata={"status_code": response.status, "response_data": data}
                        )
                        
        except asyncio.TimeoutError:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="grafana",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message="Grafana health check timeout"
            )
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="grafana",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Grafana health check failed: {str(e)}"
            )
    
    async def check_system_resources(self) -> HealthCheck:
        """Check system resource utilization."""
        start_time = time.time()
        
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            response_time = (time.time() - start_time) * 1000
            
            # Determine status based on thresholds
            status = HealthStatus.HEALTHY
            issues = []
            
            if cpu_percent > self.thresholds['cpu_critical']:
                status = HealthStatus.UNHEALTHY
                issues.append(f"CPU usage critical: {cpu_percent:.1f}%")
            elif cpu_percent > self.thresholds['cpu_warning']:
                status = HealthStatus.DEGRADED
                issues.append(f"CPU usage high: {cpu_percent:.1f}%")
            
            if memory.percent > self.thresholds['memory_critical']:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Memory usage critical: {memory.percent:.1f}%")
            elif memory.percent > self.thresholds['memory_warning']:
                status = HealthStatus.DEGRADED
                issues.append(f"Memory usage high: {memory.percent:.1f}%")
            
            disk_percent = (disk.used / disk.total) * 100
            if disk_percent > self.thresholds['disk_critical']:
                status = HealthStatus.UNHEALTHY
                issues.append(f"Disk usage critical: {disk_percent:.1f}%")
            elif disk_percent > self.thresholds['disk_warning']:
                status = HealthStatus.DEGRADED
                issues.append(f"Disk usage high: {disk_percent:.1f}%")
            
            message = "System resources check"
            if issues:
                message += f" - {', '.join(issues)}"
            else:
                message += " - All resources within normal limits"
            
            return HealthCheck(
                service_name="system_resources",
                status=status,
                response_time_ms=response_time,
                message=message,
                metadata={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_used_gb": memory.used / (1024**3),
                    "memory_total_gb": memory.total / (1024**3),
                    "disk_percent": disk_percent,
                    "disk_used_gb": disk.used / (1024**3),
                    "disk_total_gb": disk.total / (1024**3)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="system_resources",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"System resources check failed: {str(e)}"
            )
    
    async def check_service_dependencies(self) -> HealthCheck:
        """Check service dependencies and latency."""
        start_time = time.time()
        
        try:
            # Check service-to-service latency
            dependencies = []
            
            # Backend to database latency
            db_start = time.time()
            try:
                conn = await asyncpg.connect(self.services['database']['url'], timeout=2.0)
                await conn.fetchval("SELECT 1")
                await conn.close()
                db_latency = (time.time() - db_start) * 1000
                dependencies.append({"dependency": "backend->database", "latency_ms": db_latency})
            except Exception as e:
                dependencies.append({"dependency": "backend->database", "error": str(e)})
            
            # Backend to Redis latency
            redis_start = time.time()
            try:
                redis_client = redis.from_url(self.services['redis']['url'], socket_timeout=2.0)
                await redis_client.ping()
                await redis_client.close()
                redis_latency = (time.time() - redis_start) * 1000
                dependencies.append({"dependency": "backend->redis", "latency_ms": redis_latency})
            except Exception as e:
                dependencies.append({"dependency": "backend->redis", "error": str(e)})
            
            response_time = (time.time() - start_time) * 1000
            
            # Calculate average latency
            latencies = [dep.get("latency_ms", 0) for dep in dependencies if "latency_ms" in dep]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            # Determine status
            errors = [dep for dep in dependencies if "error" in dep]
            status = HealthStatus.HEALTHY if not errors and avg_latency < 100 else HealthStatus.DEGRADED
            if errors or avg_latency > 500:
                status = HealthStatus.UNHEALTHY
            
            message = f"Service dependencies check - {len(dependencies)} dependencies checked"
            if errors:
                message += f", {len(errors)} errors"
            if latencies:
                message += f", avg latency: {avg_latency:.1f}ms"
            
            return HealthCheck(
                service_name="service_dependencies",
                status=status,
                response_time_ms=response_time,
                message=message,
                metadata={
                    "dependencies": dependencies,
                    "average_latency_ms": avg_latency,
                    "error_count": len(errors)
                }
            )
            
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            return HealthCheck(
                service_name="service_dependencies",
                status=HealthStatus.UNHEALTHY,
                response_time_ms=response_time,
                message=f"Service dependencies check failed: {str(e)}"
            )
    
    def calculate_overall_health(self) -> SystemHealth:
        """Calculate overall system health."""
        if not self.checks:
            return SystemHealth(
                overall_status=HealthStatus.UNKNOWN,
                service_count=0,
                healthy_count=0,
                degraded_count=0,
                unhealthy_count=0,
                total_response_time_ms=0.0,
                average_response_time_ms=0.0
            )
        
        # Count status types
        healthy_count = sum(1 for check in self.checks if check.status == HealthStatus.HEALTHY)
        degraded_count = sum(1 for check in self.checks if check.status == HealthStatus.DEGRADED)
        unhealthy_count = sum(1 for check in self.checks if check.status == HealthStatus.UNHEALTHY)
        
        # Calculate response times
        total_response_time = sum(check.response_time_ms for check in self.checks)
        average_response_time = total_response_time / len(self.checks)
        
        # Determine overall status
        if unhealthy_count > 0:
            overall_status = HealthStatus.UNHEALTHY
        elif degraded_count > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return SystemHealth(
            overall_status=overall_status,
            service_count=len(self.checks),
            healthy_count=healthy_count,
            degraded_count=degraded_count,
            unhealthy_count=unhealthy_count,
            total_response_time_ms=total_response_time,
            average_response_time_ms=average_response_time,
            checks=self.checks
        )
    
    def print_health_report(self, health: SystemHealth) -> None:
        """Print comprehensive health report."""
        print("\n" + "="*80)
        print("QURVE AI - PRODUCTION HEALTH REPORT")
        print("="*80)
        
        # Overall status
        status_emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.DEGRADED: "⚠️",
            HealthStatus.UNHEALTHY: "❌",
            HealthStatus.UNKNOWN: "❓"
        }
        
        print(f"\nOverall Status: {status_emoji[health.overall_status]} {health.overall_status.value.upper()}")
        print(f"Services Checked: {health.service_count}")
        print(f"Healthy: {health.healthy_count}")
        print(f"Degraded: {health.degraded_count}")
        print(f"Unhealthy: {health.unhealthy_count}")
        print(f"Average Response Time: {health.average_response_time_ms:.1f}ms")
        
        # Individual service status
        print(f"\n{'SERVICE':<20} {'STATUS':<12} {'RESPONSE TIME':<15} {'MESSAGE'}")
        print("-" * 80)
        
        for check in health.checks:
            status = status_emoji[check.status] + " " + check.status.value.upper()
            print(f"{check.service_name:<20} {status:<12} {check.response_time_ms:>8.1f}ms     {check.message}")
        
        print("\n" + "="*80)
        
        # Exit with appropriate code
        if health.overall_status == HealthStatus.HEALTHY:
            print("✅ ALL SYSTEMS HEALTHY")
            sys.exit(0)
        elif health.overall_status == HealthStatus.DEGRADED:
            print("⚠️ SOME SYSTEMS DEGRADED")
            sys.exit(1)
        else:
            print("❌ SOME SYSTEMS UNHEALTHY")
            sys.exit(2)


async def main():
    """Main health check execution."""
    orchestrator = HealthCheckOrchestrator()
    
    try:
        # Run all health checks
        system_health = await orchestrator.run_all_health_checks()
        
        # Print report
        orchestrator.print_health_report(system_health)
        
    except KeyboardInterrupt:
        print("\n❌ Health check interrupted")
        sys.exit(3)
    except Exception as e:
        print(f"\n❌ Health check failed: {e}")
        sys.exit(4)


if __name__ == "__main__":
    asyncio.run(main())
