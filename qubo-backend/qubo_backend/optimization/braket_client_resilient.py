"""
Qurve AI - Resilient Braket Client Layer
Enhanced HTTP bridge with auto-recovery and resiliency
"""

import httpx
import asyncio
import time
from collections import deque
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum

from ..telemetry.structured_telemetry import get_worker_telemetry, get_solver_telemetry, LatencyMetrics
from ..telemetry import get_structured_logger

logger = get_structured_logger(__name__)

BRAKET_WORKER_URL = "http://127.0.0.1:8011"
BRAKET_WORKER_TIMEOUT = 120.0  # seconds


class WorkerState(Enum):
    """Worker state enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"
    RECONNECTING = "reconnecting"


@dataclass
class WorkerConfig:
    """Configuration for resilient worker client."""
    health_check_timeout: float = 5.0
    execution_timeout: float = 120.0
    http_timeout: float = 10.0
    retry_timeout: float = 2.0
    max_retry_count: int = 3
    retry_delay: float = 1.0
    health_check_interval: float = 30.0
    failure_threshold: int = 3  # Failures before marking degraded
    # Predictive routing
    queue_latency_window: int = 20  # Rolling window size for latency tracking
    sv1_congestion_threshold_ms: float = 12000.0  # Median above this → congested
    tn1_congestion_threshold_ms: float = 25000.0  # Median above this → congested


@dataclass
class BraketJobResult:
    """Result from Braket worker execution."""
    status: str
    measurements: list
    execution_time_ms: float
    backend: str
    error: Optional[str] = None
    error_type: Optional[str] = None
    worker_state: Optional[str] = None
    retry_count: int = 0
    task_arn: Optional[str] = None
    device_arn: Optional[str] = None
    execution_mode: Optional[str] = None
    metadata: Optional[Dict] = None


class BraketClientError(Exception):
    """Exception raised when Braket client operations fail."""
    pass


class BraketWorkerUnavailableError(BraketClientError):
    """Exception raised when Braket worker is unavailable."""
    pass


class ResilientBraketClient:
    """
    Resilient HTTP client with auto-recovery and health monitoring.
    
    Features:
    - Automatic worker state tracking
    - Retry logic with exponential backoff
    - Graceful fallback escalation
    - Connection recovery
    - Structured latency tracking
    - Health monitoring
    """
    
    def __init__(self, worker_url: str = BRAKET_WORKER_URL, 
                 config: Optional[WorkerConfig] = None):
        self.worker_url = worker_url.rstrip('/')
        self.config = config or WorkerConfig()
        self.logger = get_structured_logger(__name__)
        self.telemetry = get_worker_telemetry()
        self.solver_telemetry = get_solver_telemetry()
        
        # State tracking
        self._state = WorkerState.UNAVAILABLE
        self._available = None
        self._failure_count = 0
        self._last_health_check = 0.0
        self._last_successful_execution = 0.0
        self._cached_health: Optional[bool] = None
        
        # Health check concurrency guard
        self._health_lock: Optional[asyncio.Lock] = None
        
        # Performance tracking
        self._latency_metrics = LatencyMetrics()
        self._execution_history = []
        
        # Predictive queue routing: rolling latency windows per device
        self._device_latencies: Dict[str, deque] = {
            "sv1": deque(maxlen=self.config.queue_latency_window),
            "tn1": deque(maxlen=self.config.queue_latency_window),
            "dm1": deque(maxlen=self.config.queue_latency_window),
            "local": deque(maxlen=self.config.queue_latency_window),
        }
        
        self.logger.info(f"[BRAKET_CLIENT] Initialized resilient client for {self.worker_url}")
        self.logger.info(f"[BRAKET_CLIENT] Config: {self.config}")
    
    def _get_health_lock(self) -> asyncio.Lock:
        """Lazily create an asyncio.Lock bound to the current event loop."""
        if self._health_lock is None:
            self._health_lock = asyncio.Lock()
        return self._health_lock

    async def check_worker_health(self) -> bool:
        """Check if Braket worker is healthy and available.
        
        Uses a per-request httpx.AsyncClient to avoid cross-event-loop errors.
        Guarded by an asyncio.Lock to prevent concurrent health checks.
        Results are cached for 30s.
        """
        # Fast-path: return cached health within TTL
        now = time.time()
        if self._cached_health is not None and (now - self._last_health_check) < 30.0:
            return self._cached_health
        
        lock = self._get_health_lock()
        if lock.locked():
            # Another check is already running — return last known state
            return self._cached_health if self._cached_health is not None else False
        
        async with lock:
            # Double-check after acquiring lock
            now = time.time()
            if self._cached_health is not None and (now - self._last_health_check) < 30.0:
                return self._cached_health
            
            start_time = time.time()
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.worker_url}/health",
                        timeout=self.config.health_check_timeout,
                    )
                
                health_latency_ms = (time.time() - start_time) * 1000
                self._latency_metrics.health_check_latency_ms = health_latency_ms
                
                if response.status_code == 200:
                    health_data = response.json()
                    is_healthy = (
                        health_data.get("status") == "healthy" and
                        health_data.get("service") == "braket-worker"
                    )
                    
                    if is_healthy:
                        self._update_state(WorkerState.HEALTHY)
                        self._failure_count = 0
                        self._last_health_check = time.time()
                        self._cached_health = True
                        
                        self.logger.info(
                            f"[BRAKET_CLIENT] Health check passed in {health_latency_ms:.2f}ms"
                        )
                        return True
                    else:
                        self._update_state(WorkerState.DEGRADED)
                        self._failure_count += 1
                        self._cached_health = False
                        self._last_health_check = time.time()
                        
                        self.logger.warning(
                            f"[BRAKET_CLIENT] Health check degraded: {health_data}"
                        )
                        return False
                else:
                    self._update_state(WorkerState.UNAVAILABLE)
                    self._failure_count += 1
                    self._cached_health = False
                    self._last_health_check = time.time()
                    
                    self.logger.error(
                        f"[BRAKET_CLIENT] Health check failed: HTTP {response.status_code}"
                    )
                    return False
                    
            except httpx.TimeoutException:
                self._failure_count += 1
                self._cached_health = False
                self._last_health_check = time.time()
                self.logger.error(
                    f"[BRAKET_CLIENT] Health check timed out after {self.config.health_check_timeout}s"
                )
                return False
                
            except httpx.ConnectError:
                self._failure_count += 1
                self._cached_health = False
                self._last_health_check = time.time()
                self.logger.error("[BRAKET_CLIENT] Health check connection failed")
                return False
                
            except Exception as e:
                self._failure_count += 1
                self._cached_health = False
                self._last_health_check = time.time()
                self.logger.error(f"[BRAKET_CLIENT] Health check error: {str(e)}")
                return False
    
    async def is_available(self) -> bool:
        """Check if Braket worker is available with caching."""
        current_time = time.time()
        
        # Check if we need to refresh health status
        if (self._available is None or 
            current_time - self._last_health_check > self.config.health_check_interval):
            
            self._available = await self.check_worker_health()
        else:
            # Check if state has changed
            if self._state == WorkerState.UNAVAILABLE:
                self._available = False
            elif self._state == WorkerState.DEGRADED:
                self._available = False
            else:
                self._available = True
        
        return self._available
    
    async def wait_for_worker_readiness(self, consecutive_checks: int = 3, timeout: float = 15.0) -> bool:
        """[WORKER_READINESS_BARRIER] Wait for N consecutive successful health checks."""
        start_time = time.time()
        successful_checks = 0
        stabilization_attempts = 0
        
        self.logger.info(f"[WORKER_READINESS_BARRIER] Starting stabilization for {consecutive_checks} checks")
        
        while time.time() - start_time < timeout:
            stabilization_attempts += 1
            is_healthy = await self.check_worker_health()
            
            if is_healthy:
                successful_checks += 1
            else:
                successful_checks = 0 # Reset on any failure
            
            if successful_checks >= consecutive_checks:
                duration_ms = (time.time() - start_time) * 1000
                self.logger.info(f"[WORKER_READINESS_BARRIER] Worker stabilized in {duration_ms:.2f}ms after {stabilization_attempts} attempts")
                return True
            
            await asyncio.sleep(0.5) # Short interval for readiness
            
        self.logger.error(f"[WORKER_READINESS_BARRIER] Readiness timeout exceeded after {stabilization_attempts} attempts. Only {successful_checks} consecutive checks succeeded.")
        return False

    async def run_braket_job(self, shots: int = 100, 
                           correlation_id: Optional[str] = None,
                           execution_mode: str = "local",
                           device: str = "local",
                           qubits: int = 2,
                           qubo_matrix: Optional[List] = None,
                           qubo_offset: float = 0.0,
                           qaoa_depth: int = 1,
                           request_meta: Optional[Dict] = None) -> BraketJobResult:
        """
        Run a Braket quantum simulation job with resiliency.
        
        Args:
            shots: Number of measurement shots
            correlation_id: Optional correlation ID for tracking
            execution_mode: local, cloud_simulator, or cloud_qpu
            device: local, sv1, tn1, dm1
            qubits: Number of qubits required
            qubo_matrix: Flattened QUBO matrix for QAOA circuit construction
            qubo_offset: QUBO offset constant
            qaoa_depth: QAOA circuit depth
            request_meta: Full SolverRequest metadata for worker-side decoding
            
        Returns:
            BraketJobResult: Result of the quantum simulation
        """
        # [BENCHMARK_MODE_PROPAGATION]
        qaoa_mode = "QAOA" if qubo_matrix is not None else "HADAMARD"
        self.logger.info(f"[BENCHMARK_MODE_PROPAGATION] run_braket_job shots={shots} mode={execution_mode} device={device} circuit={qaoa_mode}")
        print(f"[BENCHMARK_MODE_PROPAGATION] run_braket_job shots={shots} mode={execution_mode} device={device} circuit={qaoa_mode}")

        start_time = time.time()
        
        # Generate tracking IDs
        if not correlation_id:
            correlation_id = self.telemetry.generate_correlation_id()
        
        worker_request_uuid = self.telemetry.generate_worker_request_uuid()
        execution_id = self.telemetry.track_worker_execution(correlation_id, worker_request_uuid)
        
        try:
            # [BRAKET_LOCAL_ISOLATION] Isolation logic
            is_local = (execution_mode == "local" or device == "local")
            
            if is_local:
                self.logger.info(f"[BRAKET_LOCAL_ISOLATION] Bypassing cloud orchestration for {device}")
                # Local isolation bypasses is_available() check which has caching/state logic
                # We still want a basic health check but no long wait
            else:
                # Check worker availability for cloud jobs
                if not await self.is_available():
                    self.logger.warning(
                        f"[BRAKET_CLIENT] Worker unavailable for job execution"
                    )
                    raise BraketWorkerUnavailableError(
                        f"Braket worker is not available at {self.worker_url}"
                    )
            
            self.telemetry._log_structured(
                event_type="job_execution_started",
                correlation_id=correlation_id,
                execution_id=execution_id,
                worker_request_uuid=worker_request_uuid,
                shots=shots,
                is_local=is_local
            )
            
            # Execute with retry logic (retry logic itself handles isolation internally)
            result = await self._execute_with_retry(
                shots, correlation_id, worker_request_uuid, execution_id,
                execution_mode, device, qubits, is_local=is_local,
                qubo_matrix=qubo_matrix, qubo_offset=qubo_offset,
                qaoa_depth=qaoa_depth, request_meta=request_meta
            )
            
            # Update performance tracking
            total_latency_ms = (time.time() - start_time) * 1000
            self._latency_metrics.total_solver_latency_ms = total_latency_ms
            self._latency_metrics.worker_execution_latency_ms = result.execution_time_ms
            
            self.telemetry.track_latency_metrics(correlation_id, self._latency_metrics)
            self.telemetry.complete_worker_execution(
                execution_id, "completed", len(result.measurements), 
                result.execution_time_ms
            )
            
            # Update success tracking
            self._last_successful_execution = time.time()
            self._execution_history.append({
                "timestamp": time.time(),
                "success": True,
                "execution_time_ms": result.execution_time_ms,
                "measurements_count": len(result.measurements),
                "device": device,
            })
            
            # Record device-specific latency for predictive routing
            device_key = device.lower()
            if device_key in self._device_latencies:
                self._device_latencies[device_key].append(total_latency_ms)
                self.logger.info(
                    f"[CLOUD_QUEUE_PREDICTION] recorded latency for {device_key}: "
                    f"{total_latency_ms:.1f}ms (window={len(self._device_latencies[device_key])})"
                )
            
            # Keep only recent history
            if len(self._execution_history) > 100:
                self._execution_history = self._execution_history[-50:]
            
            self.telemetry._log_structured(
                event_type="job_execution_completed",
                correlation_id=correlation_id,
                execution_id=execution_id,
                status=result.status,
                measurements_count=len(result.measurements),
                execution_time_ms=result.execution_time_ms,
                total_latency_ms=total_latency_ms
            )
            
            self.logger.info(
                f"[BRAKET_CLIENT] Job completed in {result.execution_time_ms:.2f}ms "
                f"({len(result.measurements)} measurements)"
            )
            
            return result
            
        except BraketWorkerUnavailableError:
            # Worker unavailable - escalate to fallback
            self.telemetry.complete_worker_execution(
                execution_id, "failed", 0, None, "Worker unavailable"
            )
            
            self.telemetry._log_structured(
                event_type="job_execution_failed",
                correlation_id=correlation_id,
                execution_id=execution_id,
                error="Worker unavailable",
                escalated_to_fallback=True
            )
            
            raise
            
        except Exception as e:
            # Unexpected error
            self.telemetry.complete_worker_execution(
                execution_id, "failed", 0, None, str(e)
            )
            
            self.telemetry._log_structured(
                event_type="job_execution_error",
                correlation_id=correlation_id,
                execution_id=execution_id,
                error=str(e),
                error_type=str(type(e))
            )
            
            self.logger.error(
                f"[BRAKET_CLIENT] Job execution failed: {str(e)}"
            )
            
            raise BraketClientError(f"Unexpected error in job execution: {str(e)}")
    
    async def _execute_with_retry(self, shots: int, correlation_id: str, 
                              worker_request_uuid: str, execution_id: str, 
                              execution_mode: str = "local", device: str = "local",
                              qubits: int = 2, is_local: bool = False,
                              qubo_matrix: Optional[List] = None,
                              qubo_offset: float = 0.0,
                              qaoa_depth: int = 1,
                              request_meta: Optional[Dict] = None) -> BraketJobResult:
        """Execute job with retry logic."""
        last_error = None
        
        # [BRAKET_LOCAL_ISOLATION] Deterministic local behavior
        max_retries = 0 if is_local else self.config.max_retry_count
        
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    retry_delay = self.config.retry_delay * (2 ** (attempt - 1))  # Exponential backoff
                    self.logger.info(
                        f"[BRAKET_CLIENT] Retry attempt {attempt}/{self.config.max_retry_count} "
                        f"after {retry_delay:.1f}s delay"
                    )
                    await asyncio.sleep(retry_delay)
                
                start_time = time.time()
                
                request_payload = {
                    "shots": shots,
                    "execution_mode": execution_mode,
                    "device": device,
                    "qubits": qubits,
                    "enable_qpu": True if execution_mode == "cloud_qpu" else False,
                }
                # Include QUBO and Metadata for QAOA optimization (Fix 1, 2, 3)
                if qubo_matrix is not None:
                    request_payload["qubo_matrix"] = qubo_matrix
                    request_payload["qubo_offset"] = qubo_offset
                    request_payload["qaoa_depth"] = qaoa_depth
                    if request_meta:
                        request_payload.update(request_meta)
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.worker_url}/run",
                        json=request_payload,
                        headers={
                            "X-Correlation-ID": correlation_id,
                            "X-Worker-Request-UUID": worker_request_uuid,
                            "X-Execution-ID": execution_id
                        },
                        timeout=self.config.execution_timeout
                    )
                
                http_latency_ms = (time.time() - start_time) * 1000
                self._latency_metrics.http_transport_latency_ms = http_latency_ms
                
                if response.status_code == 200:
                    result_data = response.json()
                    
                    # WORKER RESPONSE VALIDATION
                    print(f"[BRAKET_WORKER_RESPONSE] {result_data}")
                    
                    # Validate response structure
                    if result_data.get("status") == "success":
                        result = BraketJobResult(
                            status=result_data.get("status"),
                            measurements=result_data.get("measurements", []),
                            execution_time_ms=result_data.get("execution_time_ms", 0),
                            backend=result_data.get("backend", "unknown"),
                            worker_state=self._state.value,
                            retry_count=attempt,
                            task_arn=result_data.get("task_arn"),
                            device_arn=result_data.get("device_arn"),
                            execution_mode=result_data.get("execution_mode"),
                            metadata=result_data.get("metadata")
                        )
                        
                        self.telemetry._log_structured(
                            event_type="job_execution_success",
                            correlation_id=correlation_id,
                            execution_id=execution_id,
                            attempt=attempt,
                            measurements_count=len(result.measurements),
                            execution_time_ms=result.execution_time_ms
                        )
                        
                        return result
                    else:
                        # Worker reported an error
                        error_msg = result_data.get("error", "Unknown error")
                        error_type = result_data.get("error_type", "Unknown")
                        
                        self.telemetry._log_structured(
                            event_type="job_execution_worker_error",
                            correlation_id=correlation_id,
                            execution_id=execution_id,
                            attempt=attempt,
                            error=error_msg,
                            error_type=error_type
                        )
                        
                        # Phase 3: Retry Classification
                        non_retryable_keywords = [
                            "exceeds maximum", "validation", "unknown device", 
                            "unsupported region", "impossible constraint", "schema mismatch",
                            "requires enable_qpu"
                        ]
                        
                        if any(kw in error_msg.lower() for kw in non_retryable_keywords):
                            self.logger.error(f"[RETRY_CLASSIFICATION] Non-retryable error detected: {error_msg}. Aborting retries.")
                            raise RuntimeError(f"Fatal Braket worker error (Non-retryable): {error_msg}")
                        
                        last_error = BraketClientError(
                            f"Braket worker error: {error_msg}"
                        )
                        
                elif response.status_code == 500:
                    # Internal server error
                    self.telemetry._log_structured(
                        event_type="job_execution_server_error",
                        correlation_id=correlation_id,
                        execution_id=execution_id,
                        attempt=attempt,
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    
                    last_error = BraketClientError(
                        f"Braket worker internal server error: {response.text}"
                    )
                    
                else:
                    # Other HTTP errors
                    self.telemetry._log_structured(
                        event_type="job_execution_http_error",
                        correlation_id=correlation_id,
                        execution_id=execution_id,
                        attempt=attempt,
                        status_code=response.status_code,
                        response_text=response.text
                    )
                    
                    last_error = BraketClientError(
                        f"Braket worker HTTP error {response.status_code}: {response.text}"
                    )
                        
            except httpx.TimeoutException:
                self.telemetry._log_structured(
                    event_type="job_execution_timeout",
                    correlation_id=correlation_id,
                    execution_id=execution_id,
                    attempt=attempt,
                    timeout_seconds=self.config.execution_timeout
                )
                
                last_error = BraketClientError(
                    f"Braket job execution timed out after {self.config.execution_timeout} seconds"
                )
                
            except httpx.ConnectError:
                self._update_state(WorkerState.UNAVAILABLE)
                self.telemetry._log_structured(
                    event_type="job_execution_connection_error",
                    correlation_id=correlation_id,
                    execution_id=execution_id,
                    attempt=attempt
                )
                
                last_error = BraketWorkerUnavailableError(
                    f"Braket worker connection failed at {self.worker_url}"
                )
                
            except Exception as e:
                self.telemetry._log_structured(
                    event_type="job_execution_unexpected_error",
                    correlation_id=correlation_id,
                    execution_id=execution_id,
                    attempt=attempt,
                    error=str(e),
                    error_type=str(type(e))
                )
                
                last_error = BraketClientError(f"Unexpected error: {str(e)}")
        
        # All retries exhausted
        if last_error:
            self._failure_count += 1
            if self._failure_count >= self.config.failure_threshold:
                self._update_state(WorkerState.DEGRADED)
            
            raise last_error
        
        # Should never reach here
        raise BraketClientError("All retry attempts exhausted without result")
    
    def _update_state(self, new_state: WorkerState):
        """Update worker state with logging."""
        if new_state != self._state:
            old_state = self._state
            self._state = new_state
            
            self.telemetry._log_structured(
                event_type="worker_state_changed",
                old_state=old_state.value,
                new_state=new_state.value,
                failure_count=self._failure_count
            )
            
            self.logger.info(
                f"[BRAKET_CLIENT] Worker state changed: {old_state.value} → {new_state.value}"
            )
    
    # ── Predictive Cloud Queue Routing ───────────────────────────────
    
    def get_device_median_latency(self, device: str) -> Optional[float]:
        """Get rolling median latency for a device."""
        device_key = device.lower()
        window = self._device_latencies.get(device_key)
        if not window or len(window) == 0:
            return None
        sorted_vals = sorted(window)
        mid = len(sorted_vals) // 2
        if len(sorted_vals) % 2 == 0:
            return (sorted_vals[mid - 1] + sorted_vals[mid]) / 2.0
        return sorted_vals[mid]
    
    def predict_optimal_device(
        self,
        requested_device: str,
        benchmark_mode: Optional[str] = None,
    ) -> str:
        """Predict the optimal device based on rolling queue latencies.
        
        Rerouting rules:
        - benchmark_fast, benchmark_balanced → rerouting allowed
        - benchmark_accuracy, explicit_tn1, explicit_sv1 → NEVER reroute
        
        Returns the device to actually use (may be the same as requested).
        """
        # Modes that NEVER allow rerouting
        no_reroute_modes = {"benchmark_accuracy", "explicit_tn1", "explicit_sv1"}
        if benchmark_mode in no_reroute_modes:
            self.logger.info(
                f"[CLOUD_QUEUE_PREDICTION] mode={benchmark_mode} → no reroute allowed, "
                f"using requested device={requested_device}"
            )
            return requested_device
        
        # Local devices are never rerouted
        if requested_device.lower() == "local":
            return requested_device
        
        median = self.get_device_median_latency(requested_device)
        if median is None:
            # Not enough data yet
            self.logger.info(
                f"[CLOUD_QUEUE_PREDICTION] no latency data for {requested_device}, "
                f"using as-is"
            )
            return requested_device
        
        # Check congestion thresholds
        threshold = (
            self.config.sv1_congestion_threshold_ms
            if requested_device.lower() == "sv1"
            else self.config.tn1_congestion_threshold_ms
        )
        
        if median > threshold:
            # Try to find a less congested alternative
            alternatives = ["sv1", "tn1"]
            alternatives = [a for a in alternatives if a != requested_device.lower()]
            
            for alt in alternatives:
                alt_median = self.get_device_median_latency(alt)
                alt_threshold = (
                    self.config.sv1_congestion_threshold_ms
                    if alt == "sv1"
                    else self.config.tn1_congestion_threshold_ms
                )
                if alt_median is not None and alt_median < alt_threshold:
                    self.logger.warning(
                        f"[CLOUD_QUEUE_PREDICTION] {requested_device} congested "
                        f"(median={median:.1f}ms > threshold={threshold:.1f}ms). "
                        f"Rerouting to {alt} (median={alt_median:.1f}ms)"
                    )
                    return alt
            
            # All cloud devices congested, fall back to local
            self.logger.warning(
                f"[CLOUD_QUEUE_PREDICTION] All cloud devices congested. "
                f"Falling back to local simulator."
            )
            return "local"
        
        self.logger.info(
            f"[CLOUD_QUEUE_PREDICTION] {requested_device} healthy "
            f"(median={median:.1f}ms < threshold={threshold:.1f}ms)"
        )
        return requested_device
    
    def get_queue_telemetry(self) -> Dict[str, Any]:
        """Get current queue prediction telemetry for all devices."""
        telemetry = {}
        for device, window in self._device_latencies.items():
            median = self.get_device_median_latency(device)
            telemetry[device] = {
                "sample_count": len(window),
                "median_latency_ms": round(median, 2) if median else None,
                "min_latency_ms": round(min(window), 2) if window else None,
                "max_latency_ms": round(max(window), 2) if window else None,
            }
        return telemetry
    
    async def get_worker_status(self) -> Dict[str, Any]:
        """Get detailed status of the Braket worker."""
        try:
            health_ok = await self.check_worker_health()
            
            return {
                "available": health_ok,
                "worker_url": self.worker_url,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "last_health_check": self._last_health_check,
                "last_successful_execution": self._last_successful_execution,
                "config": {
                    "health_check_timeout": self.config.health_check_timeout,
                    "execution_timeout": self.config.execution_timeout,
                    "max_retry_count": self.config.max_retry_count,
                    "retry_delay": self.config.retry_delay
                },
                "performance": {
                    "recent_executions": len(self._execution_history),
                    "average_execution_time": np.mean([e["execution_time_ms"] for e in self._execution_history[-10:]]) if self._execution_history else 0,
                    "success_rate": len([e for e in self._execution_history[-10:] if e["success"]]) / min(len(self._execution_history[-10:]), 1)
                }
            }
            
        except Exception as e:
            return {
                "available": False,
                "worker_url": self.worker_url,
                "state": self._state.value,
                "error": str(e),
                "last_health_check": self._last_health_check
            }
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for monitoring."""
        if not self._execution_history:
            return {
                "total_executions": 0,
                "average_execution_time_ms": 0,
                "success_rate": 0,
                "recent_performance": {}
            }
        
        recent_executions = self._execution_history[-20:]  # Last 20 executions
        successful_executions = [e for e in recent_executions if e["success"]]
        
        return {
            "total_executions": len(self._execution_history),
            "recent_executions": len(recent_executions),
            "successful_executions": len(successful_executions),
            "success_rate": len(successful_executions) / len(recent_executions),
            "average_execution_time_ms": np.mean([e["execution_time_ms"] for e in recent_executions]),
            "min_execution_time_ms": min([e["execution_time_ms"] for e in recent_executions]),
            "max_execution_time_ms": max([e["execution_time_ms"] for e in recent_executions]),
            "latency_metrics": {
                "health_check_latency_ms": self._latency_metrics.health_check_latency_ms,
                "http_transport_latency_ms": self._latency_metrics.http_transport_latency_ms,
                "worker_execution_latency_ms": self._latency_metrics.worker_execution_latency_ms,
                "total_solver_latency_ms": self._latency_metrics.total_solver_latency_ms
            }
        }


# Global client instance
_resilient_braket_client: Optional[ResilientBraketClient] = None


def get_resilient_braket_client() -> ResilientBraketClient:
    """Get the global resilient Braket client instance."""
    global _resilient_braket_client
    if _resilient_braket_client is None:
        _resilient_braket_client = ResilientBraketClient()
    return _resilient_braket_client


async def run_braket_job_resilient(shots: int = 100, 
                                  correlation_id: Optional[str] = None,
                                  execution_mode: str = "local",
                                  device: str = "local",
                                  qubits: int = 2) -> BraketJobResult:
        """
        Convenience function to run a Braket job with resiliency.
        
        Args:
            shots: Number of measurement shots
            correlation_id: Optional correlation ID for tracking
            execution_mode: local, cloud_simulator, or cloud_qpu
            device: local, sv1, tn1, dm1
            qubits: Number of qubits required
        """
        client = get_resilient_braket_client()
        return await client.run_braket_job(shots, correlation_id, execution_mode, device, qubits)


async def check_braket_worker_health_resilient() -> bool:
    """
    Convenience function to check Braket worker health with resiliency.
    
    Returns:
        bool: True if worker is healthy and available
    """
    client = get_resilient_braket_client()
    return await client.check_worker_health()


async def get_braket_worker_status_resilient() -> Dict[str, Any]:
    """
    Convenience function to get Braket worker status with resiliency.
    
    Returns:
        Dict[str, Any]: Worker status information
    """
    client = get_resilient_braket_client()
    return await client.get_worker_status()
