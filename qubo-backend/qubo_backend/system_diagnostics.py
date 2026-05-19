"""
Startup Self-Diagnostics for QUBO Portfolio Optimizer
Provides comprehensive system health endpoint and validation checks.
"""

import asyncio
import logging
import platform
import sys
import psutil
import torch
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

from .config import get_settings
from .solver_registry import SOLVER_REGISTRY
from .resource_guardrails import RESOURCE_GUARDRAILS
from .security import CREDENTIAL_MANAGER

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Result of a health check."""
    
    component: str
    status: str  # 'healthy', 'warning', 'error', 'disabled'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    duration_ms: float = 0.0


class SystemDiagnostics:
    """
    Comprehensive system health monitoring and diagnostics.
    
    Validates CUDA availability, GPU VRAM, quantum package imports,
    API connectivity, solver readiness, and websocket health.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.startup_time = datetime.now()
        
    async def run_full_diagnostics(self) -> Dict[str, Any]:
        """
        Run comprehensive system diagnostics.
        
        Returns:
            Complete health report for enterprise monitoring
        """
        start_time = datetime.now()
        health_results = []
        
        # Core system checks
        health_results.append(await self._check_python_environment())
        health_results.append(await self._check_system_resources())
        health_results.append(await self._check_cuda_availability())
        health_results.append(await self._check_quantum_packages())
        
        # Application-specific checks
        health_results.append(await self._check_solver_registry())
        health_results.append(await self._check_api_connectivity())
        health_results.append(await self._check_database_connectivity())
        health_results.append(await self._check_redis_connectivity())
        health_results.append(await self._check_credential_security())
        
        # Performance and resource checks
        health_results.append(await self._check_resource_guardrails())
        health_results.append(await self._check_disk_space())
        
        # Calculate overall status
        overall_status = self._calculate_overall_status(health_results)
        
        total_duration = (datetime.now() - start_time).total_seconds() * 1000
        
        return {
            "status": overall_status,
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - self.startup_time).total_seconds(),
            "duration_ms": total_duration,
            "version": "1.2.0",
            "environment": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "architecture": platform.architecture(),
                "processor": platform.processor(),
                "hostname": platform.node()
            },
            "health_checks": [
                {
                    "component": result.component,
                    "status": result.status,
                    "message": result.message,
                    "details": result.details,
                    "timestamp": result.timestamp.isoformat(),
                    "duration_ms": result.duration_ms
                }
                for result in health_results
            ],
            "summary": {
                "total_checks": len(health_results),
                "healthy": len([r for r in health_results if r.status == "healthy"]),
                "warnings": len([r for r in health_results if r.status == "warning"]),
                "errors": len([r for r in health_results if r.status == "error"]),
                "disabled": len([r for r in health_results if r.status == "disabled"])
            }
        }
    
    async def _check_python_environment(self) -> HealthCheckResult:
        """Check Python environment and dependencies."""
        start_time = datetime.now()
        
        try:
            # Check Python version
            python_version = sys.version_info
            if python_version.major == 3 and python_version.minor == 11:
                python_status = "healthy"
                python_msg = f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Correct version"
            else:
                python_status = "warning"
                python_msg = f"Python {python_version.major}.{python_version.minor}.{python_version.micro} - Recommended: 3.11.x"
            
            # Check critical packages
            critical_packages = ["fastapi", "torch", "numpy", "pandas", "dimod"]
            missing_packages = []
            
            for package in critical_packages:
                try:
                    __import__(package)
                except ImportError:
                    missing_packages.append(package)
            
            if missing_packages:
                status = "error"
                message = f"Missing critical packages: {', '.join(missing_packages)}"
            else:
                status = python_status if python_status == "error" else "healthy"
                message = python_msg if not missing_packages else f"{python_msg}, All critical packages available"
            
            return HealthCheckResult(
                component="python_environment",
                status=status,
                message=message,
                details={
                    "python_version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
                    "critical_packages": critical_packages,
                    "missing_packages": missing_packages
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="python_environment",
                status="error",
                message=f"Python environment check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resources (CPU, memory, disk)."""
        start_time = datetime.now()
        
        try:
            # CPU info
            cpu_count = psutil.cpu_count()
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Memory info
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            memory_available_gb = memory.available / (1024**3)
            
            # Determine status
            if memory.percent > 90:
                status = "error"
                message = f"High memory usage: {memory.percent:.1f}%"
            elif memory.percent > 80:
                status = "warning"
                message = f"Elevated memory usage: {memory.percent:.1f}%"
            else:
                status = "healthy"
                message = f"System resources normal: CPU {cpu_percent:.1f}%, Memory {memory.percent:.1f}%"
            
            return HealthCheckResult(
                component="system_resources",
                status=status,
                message=message,
                details={
                    "cpu_count": cpu_count,
                    "cpu_percent": cpu_percent,
                    "memory_total_gb": round(memory_gb, 2),
                    "memory_available_gb": round(memory_available_gb, 2),
                    "memory_percent": memory.percent,
                    "load_average": list(psutil.getloadavg()) if hasattr(psutil, 'getloadavg') else None
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="system_resources",
                status="error",
                message=f"System resource check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_cuda_availability(self) -> HealthCheckResult:
        """Check CUDA and GPU availability."""
        start_time = datetime.now()
        
        try:
            if not torch.cuda.is_available():
                return HealthCheckResult(
                    component="cuda_availability",
                    status="disabled",
                    message="CUDA not available - CPU-only mode",
                    details={
                        "cuda_available": False,
                        "gpu_count": 0
                    },
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000
                )
            
            # GPU information
            gpu_count = torch.cuda.device_count()
            gpu_info = []
            
            for i in range(gpu_count):
                props = torch.cuda.get_device_properties(i)
                gpu_info.append({
                    "device_id": i,
                    "name": props.name,
                    "total_memory_gb": props.total_memory / (1024**3),
                    "compute_capability": f"{props.major}.{props.minor}",
                    "multiprocessor_count": props.multi_processor_count
                })
            
            # Check GPU memory
            if gpu_count > 0:
                memory_allocated = torch.cuda.memory_allocated(0) / (1024**3)
                memory_reserved = torch.cuda.memory_reserved(0) / (1024**3)
                total_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
                memory_percent = (memory_allocated / total_memory) * 100
                
                if memory_percent > 90:
                    status = "error"
                    message = f"GPU memory critically high: {memory_percent:.1f}%"
                elif memory_percent > 80:
                    status = "warning"
                    message = f"GPU memory elevated: {memory_percent:.1f}%"
                else:
                    status = "healthy"
                    message = f"GPU available: {gpu_count} devices, memory usage {memory_percent:.1f}%"
            else:
                status = "healthy"
                message = "CUDA available but no GPU devices detected"
            
            return HealthCheckResult(
                component="cuda_availability",
                status=status,
                message=message,
                details={
                    "cuda_available": True,
                    "gpu_count": gpu_count,
                    "gpu_info": gpu_info,
                    "memory_allocated_gb": round(memory_allocated, 2) if gpu_count > 0 else 0,
                    "memory_reserved_gb": round(memory_reserved, 2) if gpu_count > 0 else 0,
                    "memory_percent": round(memory_percent, 1) if gpu_count > 0 else 0
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="cuda_availability",
                status="error",
                message=f"CUDA check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_quantum_packages(self) -> HealthCheckResult:
        """Check quantum computing package availability."""
        start_time = datetime.now()
        
        try:
            quantum_packages = {
                "dimod": "D-Wave Ocean SDK",
                "dwave_neal": "D-Wave Neal",
                "qiskit": "Qiskit",
                "qiskit_algorithms": "Qiskit Algorithms",
                "qiskit_optimization": "Qiskit Optimization"
            }
            
            package_status = {}
            missing_packages = []
            
            for package, description in quantum_packages.items():
                try:
                    __import__(package)
                    package_status[package] = {"status": "available", "description": description}
                except ImportError:
                    package_status[package] = {"status": "missing", "description": description}
                    missing_packages.append(package)
            
            if missing_packages:
                status = "warning"
                message = f"Missing quantum packages: {', '.join(missing_packages)}"
            else:
                status = "healthy"
                message = "All quantum packages available"
            
            return HealthCheckResult(
                component="quantum_packages",
                status=status,
                message=message,
                details={
                    "packages": package_status,
                    "missing_packages": missing_packages,
                    "quantum_enabled": self.settings.quantum_enabled
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="quantum_packages",
                status="error",
                message=f"Quantum package check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_solver_registry(self) -> HealthCheckResult:
        """Check solver registry status."""
        start_time = datetime.now()
        
        try:
            # Initialize solver health if not already done
            await SOLVER_REGISTRY.initialize_solver_health()
            
            stats = SOLVER_REGISTRY.get_solver_stats()
            available_solvers = SOLVER_REGISTRY.get_available_solvers()
            
            if stats['available_solvers'] == 0:
                status = "error"
                message = "No solvers available"
            elif stats['available_solvers'] < 2:
                status = "warning"
                message = f"Limited solver availability: {stats['available_solvers']} solvers"
            else:
                status = "healthy"
                message = f"Solver registry healthy: {stats['available_solvers']} solvers available"
            
            return HealthCheckResult(
                component="solver_registry",
                status=status,
                message=message,
                details={
                    "registry_stats": stats,
                    "available_solvers": [s.name for s in available_solvers],
                    "solver_types": list(set(s.solver_type for s in available_solvers))
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="solver_registry",
                status="error",
                message=f"Solver registry check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_api_connectivity(self) -> HealthCheckResult:
        """Check external API connectivity."""
        start_time = datetime.now()
        
        try:
            import httpx
            
            # Check basic internet connectivity
            connectivity_results = {}
            
            # Test D-Wave API if token is available
            if self.settings.dwave_api_token:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get("https://cloud.dwavesys.com/sapi/")
                        connectivity_results["dwave"] = {
                            "status": "connected" if response.status_code == 200 else "error",
                            "status_code": response.status_code
                        }
                except Exception as e:
                    connectivity_results["dwave"] = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                connectivity_results["dwave"] = {
                    "status": "no_token"
                }
            
            # Test IBM Quantum if token is available
            if self.settings.ibm_quantum_token:
                try:
                    async with httpx.AsyncClient(timeout=10) as client:
                        response = await client.get("https://quantum-computing.ibm.com/")
                        connectivity_results["ibm_quantum"] = {
                            "status": "connected" if response.status_code == 200 else "error",
                            "status_code": response.status_code
                        }
                except Exception as e:
                    connectivity_results["ibm_quantum"] = {
                        "status": "error",
                        "error": str(e)
                    }
            else:
                connectivity_results["ibm_quantum"] = {
                    "status": "no_token"
                }
            
            # Determine overall status
            connected_services = [k for k, v in connectivity_results.items() if v.get("status") == "connected"]
            error_services = [k for k, v in connectivity_results.items() if v.get("status") == "error"]
            
            if error_services:
                status = "warning"
                message = f"API connectivity issues: {', '.join(error_services)}"
            elif connected_services:
                status = "healthy"
                message = f"API connectivity OK: {', '.join(connected_services)}"
            else:
                status = "disabled"
                message = "No cloud services configured"
            
            return HealthCheckResult(
                component="api_connectivity",
                status=status,
                message=message,
                details=connectivity_results,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="api_connectivity",
                status="error",
                message=f"API connectivity check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_database_connectivity(self) -> HealthCheckResult:
        """Check database connectivity."""
        start_time = datetime.now()
        
        try:
            from sqlalchemy import text
            from sqlalchemy.ext.asyncio import create_async_engine
            
            engine = create_async_engine(self.settings.database_url)
            
            async with engine.begin() as conn:
                result = await conn.execute(text("SELECT 1"))
                await engine.dispose()
            
            return HealthCheckResult(
                component="database_connectivity",
                status="healthy",
                message="Database connection successful",
                details={
                    "database_url": self.settings.database_url.split("@")[-1] if "@" in self.settings.database_url else "local"
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="database_connectivity",
                status="error",
                message=f"Database connection failed: {str(e)}",
                details={
                    "database_url": self.settings.database_url.split("@")[-1] if "@" in self.settings.database_url else "local"
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_redis_connectivity(self) -> HealthCheckResult:
        """Check Redis connectivity."""
        start_time = datetime.now()
        
        try:
            import redis.asyncio as redis
            
            # Extract Redis connection info from database URL or use default
            redis_client = redis.from_url("redis://localhost:6379")
            
            # Test connection
            await redis_client.ping()
            await redis_client.close()
            
            return HealthCheckResult(
                component="redis_connectivity",
                status="healthy",
                message="Redis connection successful",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="redis_connectivity",
                status="warning",
                message=f"Redis connection failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_credential_security(self) -> HealthCheckResult:
        """Check credential security and storage."""
        start_time = datetime.now()
        
        try:
            # Check if credential manager is working
            services = CREDENTIAL_MANAGER.list_services()
            
            # Check for plaintext tokens in environment
            env_tokens = {
                "dwave_token_set": bool(self.settings.dwave_api_token),
                "ibm_token_set": bool(self.settings.ibm_quantum_token)
            }
            
            # Determine status
            if services:
                status = "healthy"
                message = f"Credential manager active with {len(services)} services"
            elif any(env_tokens.values()):
                status = "warning"
                message = "Tokens found in environment variables (consider using credential manager)"
            else:
                status = "disabled"
                message = "No credentials configured"
            
            return HealthCheckResult(
                component="credential_security",
                status=status,
                message=message,
                details={
                    "stored_services": services,
                    "environment_tokens": env_tokens,
                    "credential_manager_active": bool(services)
                },
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="credential_security",
                status="error",
                message=f"Credential security check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_resource_guardrails(self) -> HealthCheckResult:
        """Check resource guardrails configuration."""
        start_time = datetime.now()
        
        try:
            system_status = RESOURCE_GUARDRAILS.get_system_status()
            
            # Check for any pressure conditions
            pressure_conditions = [
                k for k, v in system_status["system_health"].items() if v
            ]
            
            if pressure_conditions:
                status = "warning"
                message = f"Resource pressure detected: {', '.join(pressure_conditions)}"
            else:
                status = "healthy"
                message = "Resource guardrails operating normally"
            
            return HealthCheckResult(
                component="resource_guardrails",
                status=status,
                message=message,
                details=system_status,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="resource_guardrails",
                status="error",
                message=f"Resource guardrails check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    async def _check_disk_space(self) -> HealthCheckResult:
        """Check disk space availability."""
        start_time = datetime.now()
        
        try:
            # Check disk space for key directories
            disk_usage = {}
            
            for path in [self.settings.output_dir, self.settings.checkpoint_dir]:
                if path.exists():
                    usage = psutil.disk_usage(str(path))
                    free_percent = (usage.free / usage.total) * 100
                    
                    disk_usage[str(path)] = {
                        "total_gb": round(usage.total / (1024**3), 2),
                        "free_gb": round(usage.free / (1024**3), 2),
                        "used_percent": round((usage.used / usage.total) * 100, 1),
                        "free_percent": round(free_percent, 1)
                    }
            
            # Determine status based on lowest free space
            if disk_usage:
                min_free_percent = min(d["free_percent"] for d in disk_usage.values())
                
                if min_free_percent < 5:
                    status = "error"
                    message = f"Critical disk space: {min_free_percent:.1f}% free"
                elif min_free_percent < 10:
                    status = "warning"
                    message = f"Low disk space: {min_free_percent:.1f}% free"
                else:
                    status = "healthy"
                    message = f"Disk space adequate: {min_free_percent:.1f}% free"
            else:
                status = "warning"
                message = "Could not check disk space for key directories"
                disk_usage = {}
            
            return HealthCheckResult(
                component="disk_space",
                status=status,
                message=message,
                details=disk_usage,
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
        except Exception as e:
            return HealthCheckResult(
                component="disk_space",
                status="error",
                message=f"Disk space check failed: {str(e)}",
                duration_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
    
    def _calculate_overall_status(self, health_results: List[HealthCheckResult]) -> str:
        """Calculate overall system status from individual health checks."""
        if not health_results:
            return "error"
        
        statuses = [result.status for result in health_results]
        
        if "error" in statuses:
            return "error"
        elif "warning" in statuses:
            return "warning"
        elif statuses.count("disabled") == len(statuses):
            return "disabled"
        else:
            return "healthy"


# Global diagnostics instance
SYSTEM_DIAGNOSTICS = SystemDiagnostics()
