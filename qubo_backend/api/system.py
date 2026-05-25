"""
System Health API endpoints for QUBO Portfolio Optimizer
Provides enterprise monitoring and diagnostics endpoints.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional

from ..system_diagnostics import SYSTEM_DIAGNOSTICS
from ..solver_registry import SOLVER_REGISTRY
from ..resource_guardrails import RESOURCE_GUARDRAILS
from ..optimization.braket_adapter import get_braket_adapter

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health():
    """
    Comprehensive system health endpoint for enterprise monitoring.
    
    Returns detailed health status of all system components including:
    - Python environment and dependencies
    - System resources (CPU, memory, disk)
    - CUDA and GPU availability
    - Quantum package imports
    - Solver registry status
    - API connectivity
    - Database and Redis connectivity
    - Credential security
    - Resource guardrails
    """
    try:
        health_report = await SYSTEM_DIAGNOSTICS.run_full_diagnostics()
        
        # Return appropriate HTTP status based on overall health
        status_code = 200
        if health_report["status"] == "error":
            status_code = 503  # Service Unavailable
        elif health_report["status"] == "warning":
            status_code = 206  # Partial Content
        
        return JSONResponse(
            status_code=status_code,
            content=health_report
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/health/summary", response_model=Dict[str, Any])
async def get_health_summary():
    """
    Simplified health summary for quick monitoring.
    
    Returns condensed health information suitable for dashboards
    and quick health checks.
    """
    try:
        full_report = await SYSTEM_DIAGNOSTICS.run_full_diagnostics()
        
        # Extract key information for summary
        summary = {
            "status": full_report["status"],
            "timestamp": full_report["timestamp"],
            "uptime_seconds": full_report["uptime_seconds"],
            "version": full_report["version"],
            "summary": full_report["summary"],
            "critical_components": {
                "solvers_available": full_report["summary"]["healthy"] > 0,
                "database_connected": any(
                    check["component"] == "database_connectivity" and check["status"] == "healthy"
                    for check in full_report["health_checks"]
                ),
                "memory_ok": not any(
                    check["component"] == "system_resources" and check["status"] in ["error", "warning"]
                    for check in full_report["health_checks"]
                ),
                "disk_ok": not any(
                    check["component"] == "disk_space" and check["status"] in ["error", "warning"]
                    for check in full_report["health_checks"]
                )
            }
        }
        
        return summary
        
    except Exception as e:
        logger.error(f"Health summary failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health summary failed: {str(e)}"
        )


@router.get("/health/solvers", response_model=Dict[str, Any])
async def get_solver_health():
    """
    Detailed solver health information.
    
    Returns comprehensive solver registry status and individual
    solver health metrics.
    """
    try:
        # Get solver registry stats
        registry_stats = SOLVER_REGISTRY.get_solver_stats()
        
        # Get available solvers with detailed info
        available_solvers = SOLVER_REGISTRY.get_available_solvers()
        
        solver_details = []
        for solver in available_solvers:
            solver_details.append({
                "name": solver.name,
                "type": solver.solver_type,
                "state": solver.state.name,
                "priority": solver.priority,
                "experimental": solver.experimental,
                "deprecated": solver.deprecated,
                "capabilities": {
                    "max_assets": solver.capabilities.max_assets,
                    "max_binary_bits": solver.capabilities.max_binary_bits,
                    "supports_gpu": solver.capabilities.supports_gpu,
                    "supports_cloud": solver.capabilities.supports_cloud,
                    "quality_score": solver.capabilities.quality_score
                },
                "health_metrics": {
                    "is_healthy": solver.health_metrics.is_healthy,
                    "success_rate": solver.health_metrics.success_rate,
                    "total_runs": solver.health_metrics.total_runs,
                    "average_latency_seconds": solver.health_metrics.average_latency_seconds,
                    "last_successful_run": solver.health_metrics.last_successful_run.isoformat() if solver.health_metrics.last_successful_run else None,
                    "last_error_message": solver.health_metrics.last_error_message
                }
            })
        
        return {
            "registry_stats": registry_stats,
            "available_solvers": solver_details,
            "timestamp": SYSTEM_DIAGNOSTICS.startup_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Solver health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Solver health check failed: {str(e)}"
        )


@router.get("/health/resources", response_model=Dict[str, Any])
async def get_resource_health():
    """
    Resource usage and guardrails information.
    
    Returns current resource usage, limits, and system
    resource health status.
    """
    try:
        system_status = RESOURCE_GUARDRAILS.get_system_status()
        
        return system_status
        
    except Exception as e:
        logger.error(f"Resource health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Resource health check failed: {str(e)}"
        )


@router.get("/metrics", response_model=Dict[str, Any])
async def get_system_metrics():
    """
    System metrics for monitoring and alerting.
    
    Returns performance metrics suitable for monitoring systems
    like Prometheus, Grafana, etc.
    """
    try:
        # Get comprehensive diagnostics
        health_report = await SYSTEM_DIAGNOSTICS.run_full_diagnostics()
        
        # Extract metrics in monitoring-friendly format
        metrics = {
            "system": {
                "uptime_seconds": health_report["uptime_seconds"],
                "python_version": health_report["environment"]["python_version"],
                "platform": health_report["environment"]["platform"]
            },
            "performance": {
                "health_check_duration_ms": health_report["duration_ms"],
                "total_health_checks": health_report["summary"]["total_checks"],
                "healthy_checks": health_report["summary"]["healthy"],
                "warning_checks": health_report["summary"]["warnings"],
                "error_checks": health_report["summary"]["errors"]
            },
            "resources": {},
            "solvers": {},
            "services": {}
        }
        
        # Extract resource metrics
        for check in health_report["health_checks"]:
            if check["component"] == "system_resources":
                metrics["resources"] = {
                    "cpu_percent": check["details"]["cpu_percent"],
                    "memory_percent": check["details"]["memory_percent"],
                    "memory_total_gb": check["details"]["memory_total_gb"],
                    "memory_available_gb": check["details"]["memory_available_gb"]
                }
            elif check["component"] == "cuda_availability":
                metrics["resources"]["gpu"] = {
                    "available": check["details"]["cuda_available"],
                    "gpu_count": check["details"]["gpu_count"],
                    "memory_percent": check["details"]["memory_percent"]
                }
            elif check["component"] == "solver_registry":
                metrics["solvers"] = {
                    "total_solvers": check["details"]["registry_stats"]["total_solvers"],
                    "available_solvers": check["details"]["registry_stats"]["available_solvers"],
                    "healthy_solvers": check["details"]["registry_stats"]["healthy_solvers"]
                }
            elif check["component"] == "api_connectivity":
                metrics["services"] = check["details"]
        
        return metrics
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Metrics collection failed: {str(e)}"
        )


@router.get("/quantum-health", response_model=Dict[str, Any])
async def get_quantum_health():
    """
    Quantum computing health and availability status.
    
    Returns detailed status of quantum computing packages and solvers:
    - D-Wave Ocean SDK availability
    - Neal Simulated Annealing status
    - Qiskit ecosystem status
    - AWS Braket availability
    - Local simulator readiness
    - Cloud service connectivity
    """
    try:
        quantum_health = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "packages": {},
            "solvers": {},
            "connectivity": {}
        }
        
        # Check D-Wave Ocean SDK
        try:
            import neal
            import dimod
            from neal import SimulatedAnnealingSampler
            
            # Test basic functionality
            sampler = SimulatedAnnealingSampler()
            
            quantum_health["packages"]["dwave_ocean_sdk"] = {
                "status": "available",
                "version": getattr(neal, '__version__', 'unknown'),
                "components": {
                    "neal": "available",
                    "dimod": "available",
                    "simulated_annealing_sampler": "available"
                },
                "installation_path": neal.__file__ if hasattr(neal, '__file__') else None
            }
            
        except ImportError as e:
            quantum_health["packages"]["dwave_ocean_sdk"] = {
                "status": "not_installed",
                "error": str(e)
            }
            quantum_health["overall_status"] = "degraded"
        except Exception as e:
            quantum_health["packages"]["dwave_ocean_sdk"] = {
                "status": "error",
                "error": str(e)
            }
            quantum_health["overall_status"] = "degraded"
        
        # Check Neal SA specifically
        try:
            from ..optimization.dwave_sa_solver import get_neal_sa_status, is_neal_sa_available
            
            neal_status = get_neal_sa_status()
            neal_available = is_neal_sa_available()
            
            quantum_health["solvers"]["dwave_neal_sa"] = {
                "status": neal_status,
                "available": neal_available,
                "type": "local_simulator",
                "provider": "D-Wave",
                "execution": "local",
                "cost": "free",
                "benchmark_ready": True
            }
            
            if neal_status != "available":
                quantum_health["overall_status"] = "degraded"
                
        except Exception as e:
            quantum_health["solvers"]["dwave_neal_sa"] = {
                "status": "error",
                "error": str(e)
            }
            quantum_health["overall_status"] = "degraded"
        
        # Check Qiskit
        try:
            import qiskit
            from qiskit_algorithms import QAOA
            from qiskit_optimization import QuadraticProgram
            
            quantum_health["packages"]["qiskit"] = {
                "status": "available",
                "version": getattr(qiskit, '__version__', 'unknown'),
                "components": {
                    "qaoa": "available",
                    "quadratic_program": "available"
                }
            }
            
        except ImportError as e:
            quantum_health["packages"]["qiskit"] = {
                "status": "not_installed",
                "error": str(e)
            }
        except Exception as e:
            quantum_health["packages"]["qiskit"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Check AWS Braket
        try:
            import braket
            quantum_health["packages"]["aws_braket"] = {
                "status": "available",
                "version": getattr(braket, '__version__', 'unknown')
            }
        except ImportError as e:
            quantum_health["packages"]["aws_braket"] = {
                "status": "not_installed",
                "error": str(e)
            }
        except Exception as e:
            quantum_health["packages"]["aws_braket"] = {
                "status": "error",
                "error": str(e)
            }
        
        # Summary
        quantum_health["summary"] = {
            "total_packages": len(quantum_health["packages"]),
            "available_packages": len([p for p in quantum_health["packages"].values() if p["status"] == "available"]),
            "total_solvers": len(quantum_health["solvers"]),
            "available_solvers": len([s for s in quantum_health["solvers"].values() if s.get("available", False)])
        }
        
        return quantum_health
        
    except Exception as e:
        logger.error(f"Quantum health check failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Quantum health check failed: {str(e)}"
        )


@router.get("/braket-health", response_model=Dict[str, Any])
async def get_braket_health():
    """
    Braket environment validation endpoint.
    
    Returns detailed Braket SDK status including:
    - SDK availability and version
    - LocalSimulator availability
    - Pydantic compatibility status
    - Circuit creation and execution tests
    - Import error details
    """
    try:
        adapter = get_braket_adapter()
        braket_status = adapter.validate_environment()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "braket_status": braket_status,
            "status": "healthy" if braket_status.get("braket_available") and braket_status.get("pydantic_compatible") else "unhealthy",
            "message": "Braket environment validation completed"
        }
        
    except Exception as e:
        logger.error(f"Braket health check failed: {e}")
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "braket_status": {
                "braket_available": False,
                "error": f"Health check failed: {str(e)}"
            },
            "status": "error",
            "message": "Braket environment validation failed"
        }


@router.post("/health/refresh", response_model=Dict[str, Any])
async def refresh_system_health():
    """
    Force refresh of all health checks.
    
    Triggers immediate re-evaluation of all system components
    and returns updated health status.
    """
    try:
        # Re-initialize solver health
        await SOLVER_REGISTRY.initialize_solver_health()
        
        # Run fresh diagnostics
        health_report = await SYSTEM_DIAGNOSTICS.run_full_diagnostics()
        
        return {
            "message": "Health checks refreshed successfully",
            "health_report": health_report
        }
        
    except Exception as e:
        logger.error(f"Health refresh failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Health refresh failed: {str(e)}"
        )
