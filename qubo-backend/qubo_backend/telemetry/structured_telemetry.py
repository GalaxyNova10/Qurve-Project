"""
Qurve AI - Structured Telemetry System
Production-grade telemetry with correlation IDs and session tracking
"""

import uuid
import time
import logging
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timezone

# Global telemetry state
_telemetry_state = {
    "active_sessions": {},
    "worker_executions": {},
    "correlation_map": {}
}


@dataclass
class TelemetrySession:
    """Telemetry session for benchmark tracking."""
    session_id: str
    correlation_id: str
    start_time: float
    solver: str
    request_data: Dict[str, Any]
    events: List[Dict[str, Any]]
    end_time: Optional[float] = None
    status: str = "active"  # active, completed, failed


@dataclass
class WorkerExecution:
    """Worker execution tracking."""
    execution_id: str
    request_id: str
    worker_request_uuid: str
    correlation_id: str
    start_time: float
    end_time: Optional[float] = None
    status: str = "running"  # running, completed, failed, timeout
    measurements_count: int = 0
    execution_time_ms: Optional[float] = None
    error: Optional[str] = None


@dataclass
class LatencyMetrics:
    """Structured latency tracking."""
    health_check_latency_ms: float = 0.0
    queue_latency_ms: float = 0.0
    http_transport_latency_ms: float = 0.0
    worker_execution_latency_ms: float = 0.0
    post_processing_latency_ms: float = 0.0
    total_solver_latency_ms: float = 0.0


@dataclass
class CloudLatencyMetrics:
    """Cloud-specific latency tracking."""
    cloud_region: str = ""
    device_arn: str = ""
    task_arn: str = ""
    queue_latency_ms: float = 0.0
    cloud_execution_latency_ms: float = 0.0
    total_cloud_latency_ms: float = 0.0
    shot_count: int = 0
    execution_mode: str = "local"


class StructuredTelemetry:
    """Production-grade structured telemetry system."""
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logging.getLogger(f"qubo_backend.telemetry.{component_name}")
    
    def generate_correlation_id(self) -> str:
        """Generate unique correlation ID."""
        return str(uuid.uuid4())
    
    def generate_session_id(self) -> str:
        """Generate unique session ID."""
        return str(uuid.uuid4())
    
    def generate_execution_id(self) -> str:
        """Generate unique execution ID."""
        return str(uuid.uuid4())
    
    def generate_worker_request_uuid(self) -> str:
        """Generate unique worker request UUID."""
        return str(uuid.uuid4())
    
    def start_benchmark_session(self, solver: str, request_data: Dict[str, Any]) -> str:
        """Start a new benchmark session."""
        session_id = self.generate_session_id()
        correlation_id = self.generate_correlation_id()
        
        session = TelemetrySession(
            session_id=session_id,
            correlation_id=correlation_id,
            start_time=time.time(),
            solver=solver,
            request_data=request_data,
            events=[]
        )
        
        _telemetry_state["active_sessions"][session_id] = session
        _telemetry_state["correlation_map"][correlation_id] = session_id
        
        self._log_structured(
            event_type="benchmark_session_started",
            correlation_id=correlation_id,
            session_id=session_id,
            solver=solver,
            request_summary={
                "assets": len(request_data.get("mu", [])),
                "cardinality": request_data.get("cardinality", 0),
                "risk_tolerance": request_data.get("risk_tolerance", 0.0),
                "binary_bits": request_data.get("binary_bits", 0)
            }
        )
        
        return session_id
    
    def end_benchmark_session(self, session_id: str, status: str, 
                           final_result: Optional[Dict[str, Any]] = None):
        """End a benchmark session."""
        if session_id not in _telemetry_state["active_sessions"]:
            self.logger.warning(f"Session {session_id} not found in active sessions")
            return
        
        session = _telemetry_state["active_sessions"][session_id]
        session.end_time = time.time()
        session.status = status
        
        duration_ms = (session.end_time - session.start_time) * 1000
        
        self._log_structured(
            event_type="benchmark_session_ended",
            correlation_id=session.correlation_id,
            session_id=session_id,
            solver=session.solver,
            status=status,
            duration_ms=duration_ms,
            events_count=len(session.events),
            final_result=final_result
        )
        
        # Move to completed sessions (could be archived)
        del _telemetry_state["active_sessions"][session_id]
        if session.correlation_id in _telemetry_state["correlation_map"]:
            del _telemetry_state["correlation_map"][session.correlation_id]
    
    def track_worker_execution(self, correlation_id: str, worker_request_uuid: str) -> str:
        """Track worker execution start."""
        execution_id = self.generate_execution_id()
        request_id = f"req_{int(time.time() * 1000)}"
        
        execution = WorkerExecution(
            execution_id=execution_id,
            request_id=request_id,
            worker_request_uuid=worker_request_uuid,
            correlation_id=correlation_id,
            start_time=time.time()
        )
        
        _telemetry_state["worker_executions"][execution_id] = execution
        
        self._log_structured(
            event_type="worker_execution_started",
            correlation_id=correlation_id,
            execution_id=execution_id,
            request_id=request_id,
            worker_request_uuid=worker_request_uuid
        )
        
        return execution_id
    
    def complete_worker_execution(self, execution_id: str, status: str, 
                              measurements_count: int = 0, execution_time_ms: Optional[float] = None,
                              error: Optional[str] = None):
        """Complete worker execution tracking."""
        if execution_id not in _telemetry_state["worker_executions"]:
            self.logger.warning(f"Execution {execution_id} not found in active executions")
            return
        
        execution = _telemetry_state["worker_executions"][execution_id]
        execution.end_time = time.time()
        execution.status = status
        execution.measurements_count = measurements_count
        execution.execution_time_ms = execution_time_ms
        execution.error = error
        
        duration_ms = (execution.end_time - execution.start_time) * 1000
        
        self._log_structured(
            event_type="worker_execution_completed",
            correlation_id=execution.correlation_id,
            execution_id=execution_id,
            request_id=execution.request_id,
            worker_request_uuid=execution.worker_request_uuid,
            status=status,
            duration_ms=duration_ms,
            measurements_count=measurements_count,
            execution_time_ms=execution_time_ms,
            error=error
        )
        
        # Move to completed executions (could be archived)
        del _telemetry_state["worker_executions"][execution_id]
    
    def track_latency_metrics(self, correlation_id: str, metrics: LatencyMetrics):
        """Track structured latency metrics."""
        self._log_structured(
            event_type="latency_metrics",
            correlation_id=correlation_id,
            health_check_latency_ms=metrics.health_check_latency_ms,
            queue_latency_ms=metrics.queue_latency_ms,
            http_transport_latency_ms=metrics.http_transport_latency_ms,
            worker_execution_latency_ms=metrics.worker_execution_latency_ms,
            post_processing_latency_ms=metrics.post_processing_latency_ms,
            total_solver_latency_ms=metrics.total_solver_latency_ms
        )
    
    def track_cloud_execution(self, correlation_id: str, cloud_metrics: CloudLatencyMetrics):
        """Track cloud execution metrics."""
        self._log_structured(
            event_type="cloud_execution_metrics",
            correlation_id=correlation_id,
            cloud_region=cloud_metrics.cloud_region,
            device_arn=cloud_metrics.device_arn,
            task_arn=cloud_metrics.task_arn,
            queue_latency_ms=cloud_metrics.queue_latency_ms,
            cloud_execution_latency_ms=cloud_metrics.cloud_execution_latency_ms,
            total_cloud_latency_ms=cloud_metrics.total_cloud_latency_ms,
            shot_count=cloud_metrics.shot_count,
            execution_mode=cloud_metrics.execution_mode
        )
    
    def add_cloud_session_event(self, session_id: str, event_type: str, 
                              cloud_data: Optional[Dict[str, Any]] = None):
        """Add cloud-specific event to benchmark session."""
        if session_id not in _telemetry_state["active_sessions"]:
            self.logger.warning(f"Session {session_id} not found in active sessions")
            return
        
        session = _telemetry_state["active_sessions"][session_id]
        
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": cloud_data or {},
            "cloud_execution": True
        }
        
        session.events.append(event)
        
        self._log_structured(
            event_type=event_type,
            correlation_id=session.correlation_id,
            session_id=session_id,
            **(cloud_data or {})
        )
    
    def add_session_event(self, session_id: str, event_type: str, 
                        event_data: Optional[Dict[str, Any]] = None):
        """Add event to benchmark session."""
        if session_id not in _telemetry_state["active_sessions"]:
            self.logger.warning(f"Session {session_id} not found in active sessions")
            return
        
        session = _telemetry_state["active_sessions"][session_id]
        
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "data": event_data or {}
        }
        
        session.events.append(event)
        
        self._log_structured(
            event_type=event_type,
            correlation_id=session.correlation_id,
            session_id=session_id,
            **(event_data or {})
        )
    
    def get_active_sessions(self) -> Dict[str, TelemetrySession]:
        """Get all active benchmark sessions."""
        return _telemetry_state["active_sessions"].copy()
    
    def get_active_executions(self) -> Dict[str, WorkerExecution]:
        """Get all active worker executions."""
        return _telemetry_state["worker_executions"].copy()
    
    def get_session_by_correlation_id(self, correlation_id: str) -> Optional[TelemetrySession]:
        """Get session by correlation ID."""
        session_id = _telemetry_state["correlation_map"].get(correlation_id)
        if session_id:
            return _telemetry_state["active_sessions"].get(session_id)
        return None
    
    def _log_structured(self, event_type: str, **kwargs):
        """Log structured telemetry event."""
        structured_event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "component": self.component_name,
            "event_type": event_type,
            **kwargs
        }
        
        # Log as JSON for structured parsing
        self.logger.info(json.dumps(structured_event, default=str))


# Global telemetry instances
_benchmark_telemetry = StructuredTelemetry("benchmark")
_worker_telemetry = StructuredTelemetry("worker")
_solver_telemetry = StructuredTelemetry("solver")


def get_benchmark_telemetry() -> StructuredTelemetry:
    """Get benchmark telemetry instance."""
    return _benchmark_telemetry


def get_worker_telemetry() -> StructuredTelemetry:
    """Get worker telemetry instance."""
    return _worker_telemetry


def get_solver_telemetry() -> StructuredTelemetry:
    """Get solver telemetry instance."""
    return _solver_telemetry


def get_telemetry_state() -> Dict[str, Any]:
    """Get current telemetry state for monitoring."""
    return {
        "active_sessions_count": len(_telemetry_state["active_sessions"]),
        "active_executions_count": len(_telemetry_state["worker_executions"]),
        "correlation_mappings": len(_telemetry_state["correlation_map"]),
        "active_sessions": {k: asdict(v) for k, v in _telemetry_state["active_sessions"].items()},
        "active_executions": {k: asdict(v) for k, v in _telemetry_state["worker_executions"].items()}
    }


def clear_telemetry_state():
    """Clear telemetry state (for testing)."""
    _telemetry_state["active_sessions"].clear()
    _telemetry_state["worker_executions"].clear()
    _telemetry_state["correlation_map"].clear()
