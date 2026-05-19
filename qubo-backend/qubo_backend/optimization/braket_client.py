"""
Qurve AI - Braket Client Layer
Safe HTTP bridge to isolated Braket worker service
"""

import httpx
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..telemetry import get_structured_logger

logger = get_structured_logger(__name__)

BRAKET_WORKER_URL = "http://127.0.0.1:8011"
BRAKET_WORKER_TIMEOUT = 30  # seconds


@dataclass
class BraketJobResult:
    """Result from Braket worker execution."""
    status: str
    measurements: list
    execution_time_ms: float
    backend: str
    error: Optional[str] = None
    error_type: Optional[str] = None
    execution_mode: Optional[str] = None
    task_arn: Optional[str] = None
    device_arn: Optional[str] = None
    queue_time_ms: Optional[float] = None
    cloud_execution_time_ms: Optional[float] = None


class BraketClientError(Exception):
    """Exception raised when Braket client operations fail."""
    pass


class BraketWorkerUnavailableError(BraketClientError):
    """Exception raised when Braket worker is unavailable."""
    pass


class BraketClient:
    """
    Safe HTTP client for communicating with the isolated Braket worker service.
    
    Provides:
    - HTTP bridge to Braket worker
    - Health validation
    - Error handling and fallback
    - Telemetry integration
    - Timeout protection
    """
    
    def __init__(self, worker_url: str = BRAKET_WORKER_URL, timeout: int = BRAKET_WORKER_TIMEOUT):
        self.worker_url = worker_url.rstrip('/')
        self.timeout = timeout
        self.logger = get_structured_logger(__name__)
        self._available = None  # Cache availability status
    
    async def check_worker_health(self) -> bool:
        """Check if Braket worker is healthy and available."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(f"{self.worker_url}/health")
                
                if response.status_code == 200:
                    health_data = response.json()
                    is_healthy = (
                        health_data.get("status") == "healthy" and
                        health_data.get("service") == "braket-worker"
                    )
                    
                    self._available = is_healthy
                    
                    if is_healthy:
                        self.logger.info(
                            msg="Braket worker health check passed",
                            worker_url=self.worker_url,
                            health_status=health_data.get("status")
                        )
                    else:
                        self.logger.warning(
                            msg="Braket worker health check failed",
                            worker_url=self.worker_url,
                            health_status=health_data.get("status")
                        )
                    
                    return is_healthy
                else:
                    self.logger.warning(
                        msg="Braket worker health check failed with HTTP error",
                        worker_url=self.worker_url,
                        status_code=response.status_code
                    )
                    self._available = False
                    return False
                    
        except httpx.TimeoutException:
            self.logger.error(
                msg="Braket worker health check timed out",
                worker_url=self.worker_url,
                timeout_seconds=5
            )
            self._available = False
            return False
            
        except httpx.ConnectError:
            self.logger.error(
                msg="Braket worker health check failed - connection error",
                worker_url=self.worker_url
            )
            self._available = False
            return False
            
        except Exception as e:
            self.logger.error(
                msg="Braket worker health check failed with unexpected error",
                worker_url=self.worker_url,
                error=str(e),
                error_type=str(type(e))
            )
            self._available = False
            return False
    
    async def is_available(self) -> bool:
        """Check if Braket worker is available (with caching)."""
        if self._available is None:
            return await self.check_worker_health()
        return self._available
    
    async def run_braket_job(self, shots: int = 100, execution_mode: str = "local", 
                          device: str = "local", region: str = "us-east-1", 
                          enable_qpu: bool = False) -> BraketJobResult:
        """
        Run a Braket quantum simulation job through the worker API.
        
        Args:
            shots: Number of measurement shots
            execution_mode: Execution mode (local, cloud_simulator, cloud_qpu)
            device: Target device (local, sv1, tn1, dm1)
            region: AWS region for cloud execution
            enable_qpu: Explicit QPU enable flag
            
        Returns:
            BraketJobResult: Result of the quantum simulation
            
        Raises:
            BraketWorkerUnavailableError: If worker is not available
            BraketClientError: If job execution fails
        """
        # Check worker availability first
        if not await self.is_available():
            raise BraketWorkerUnavailableError(
                f"Braket worker is not available at {self.worker_url}"
            )
        
        try:
            self.logger.info(
                msg="Running Braket job",
                shots=shots,
                execution_mode=execution_mode,
                device=device,
                region=region,
                enable_qpu=enable_qpu,
                worker_url=self.worker_url
            )
            
            # Build request with cloud parameters (backward compatible)
            request_data = {"shots": shots}
            
            # Add cloud parameters only if not default local execution
            if execution_mode != "local":
                request_data.update({
                    "execution_mode": execution_mode,
                    "device": device,
                    "region": region,
                    "enable_qpu": enable_qpu
                })
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.worker_url}/run",
                    json=request_data
                )
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # Validate response structure
                    if result_data.get("status") == "success":
                        result = BraketJobResult(
                            status=result_data.get("status"),
                            measurements=result_data.get("measurements", []),
                            execution_time_ms=result_data.get("execution_time_ms", 0),
                            backend=result_data.get("backend", "unknown"),
                            execution_mode=result_data.get("execution_mode"),
                            task_arn=result_data.get("task_arn"),
                            device_arn=result_data.get("device_arn"),
                            queue_time_ms=result_data.get("queue_time_ms"),
                            cloud_execution_time_ms=result_data.get("cloud_execution_time_ms")
                        )
                        
                        self.logger.info(
                            msg="Braket job completed successfully",
                            shots=shots,
                            execution_time_ms=result.execution_time_ms,
                            backend=result.backend,
                            measurements_count=len(result.measurements)
                        )
                        
                        return result
                    else:
                        # Worker reported an error
                        error_msg = result_data.get("error", "Unknown error")
                        error_type = result_data.get("error_type", "Unknown")
                        
                        self.logger.error(
                            msg="Braket worker reported job execution error",
                            shots=shots,
                            error=error_msg,
                            error_type=error_type
                        )
                        
                        return BraketJobResult(
                            status="error",
                            measurements=[],
                            execution_time_ms=0,
                            backend="amazon_braket_local",
                            error=error_msg,
                            error_type=error_type
                        )
                        
                elif response.status_code == 500:
                    # Internal server error
                    self.logger.error(
                        msg="Braket worker internal server error",
                        shots=shots,
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    
                    raise BraketClientError(
                        f"Braket worker internal server error: {response.text}"
                    )
                    
                else:
                    # Other HTTP errors
                    self.logger.error(
                        msg="Braket worker HTTP error",
                        shots=shots,
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    
                    raise BraketClientError(
                        f"Braket worker HTTP error {response.status_code}: {response.text}"
                    )
                    
        except httpx.TimeoutException:
            self.logger.error(
                msg="Braket job execution timed out",
                shots=shots,
                timeout_seconds=self.timeout
            )
            
            raise BraketClientError(
                f"Braket job execution timed out after {self.timeout} seconds"
            )
            
        except httpx.ConnectError:
            self.logger.error(
                msg="Braket job execution failed - connection error",
                shots=shots,
                worker_url=self.worker_url
            )
            
            # Mark worker as unavailable
            self._available = False
            
            raise BraketWorkerUnavailableError(
                f"Braket worker connection failed at {self.worker_url}"
            )
            
        except BraketClientError:
            # Re-raise our own exceptions
            raise
            
        except Exception as e:
            self.logger.error(
                msg="Braket job execution failed with unexpected error",
                shots=shots,
                worker_url=self.worker_url,
                error=str(e),
                error_type=str(type(e))
            )
            
            raise BraketClientError(f"Unexpected error in Braket job execution: {str(e)}")
    
    async def get_worker_status(self) -> Dict[str, Any]:
        """Get detailed status of the Braket worker."""
        try:
            health_ok = await self.check_worker_health()
            
            return {
                "available": health_ok,
                "worker_url": self.worker_url,
                "timeout_seconds": self.timeout,
                "last_health_check": "now"
            }
            
        except Exception as e:
            return {
                "available": False,
                "worker_url": self.worker_url,
                "timeout_seconds": self.timeout,
                "error": str(e),
                "last_health_check": "now"
            }


# Global client instance
_braket_client: Optional[BraketClient] = None


def get_braket_client() -> BraketClient:
    """Get the global Braket client instance."""
    global _braket_client
    if _braket_client is None:
        _braket_client = BraketClient()
    return _braket_client


async def run_braket_job(shots: int = 100, execution_mode: str = "local", 
                          device: str = "local", region: str = "us-east-1", 
                          enable_qpu: bool = False) -> BraketJobResult:
    """
    Convenience function to run a Braket job.
    
    Args:
        shots: Number of measurement shots
        execution_mode: Execution mode (local, cloud_simulator, cloud_qpu)
        device: Target device (local, sv1, tn1, dm1)
        region: AWS region for cloud execution
        enable_qpu: Explicit QPU enable flag
        
    Returns:
        BraketJobResult: Result of the quantum simulation
    """
    client = get_braket_client()
    return await client.run_braket_job(shots, execution_mode, device, region, enable_qpu)


async def check_braket_worker_health() -> bool:
    """
    Convenience function to check Braket worker health.
    
    Returns:
        bool: True if worker is healthy and available
    """
    client = get_braket_client()
    return await client.check_worker_health()


async def get_braket_worker_status() -> Dict[str, Any]:
    """
    Convenience function to get Braket worker status.
    
    Returns:
        Dict[str, Any]: Worker status information
    """
    client = get_braket_client()
    return await client.get_worker_status()
