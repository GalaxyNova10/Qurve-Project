"""
Qurve AI - Structured Logger
Enterprise-grade structured JSON logging with correlation tracking
"""

import logging
import json
from typing import Dict, Any, Optional
import threading
from datetime import datetime, timezone
import uuid

# Thread-local storage for correlation context
_thread_local = threading.local()

def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current thread."""
    return getattr(_thread_local, 'correlation_id', None)

def get_benchmark_session_id() -> Optional[str]:
    """Get benchmark session ID for current thread."""
    return getattr(_thread_local, 'benchmark_session_id', None)

def generate_correlation_id() -> str:
    """Generate new correlation ID."""
    correlation_id = f"qurve-{uuid.uuid4()}"
    _thread_local.correlation_id = correlation_id
    return correlation_id

def generate_benchmark_session_id() -> str:
    """Generate new benchmark session ID."""
    session_id = f"bench-{uuid.uuid4()}"
    _thread_local.benchmark_session_id = session_id
    return session_id

class StructuredLogger:
    """
    Enterprise-grade structured logger with correlation tracking.
    
    Provides consistent JSON-formatted logs with:
    - Correlation IDs for request tracing
    - Benchmark session IDs
    - Structured event metadata
    - Performance timing
    - Thread-safe operation
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._thread_local = threading.local()
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base logging context with correlation and timing."""
        correlation_id = get_correlation_id()
        
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "thread": threading.current_thread().name,
            "logger": self.logger.name
        }
        
        # Add benchmark session ID if available
        if hasattr(self._thread_local, 'benchmark_session_id'):
            context["benchmark_session_id"] = self._thread_local.benchmark_session_id
        
        return context
    
    def _create_log_entry(self, level: str, event: str, **kwargs) -> Dict[str, Any]:
        """Create structured log entry with all required fields."""
        context = self._get_base_context()
        
        # Core log fields
        entry = {
            **context,
            "level": level,
            "event": event,
            "message": kwargs.get("message", ""),
        }
        
        # Add solver information if provided
        if "solver" in kwargs:
            entry["solver"] = kwargs["solver"]
        
        # Add provider/backend if provided
        if "provider" in kwargs:
            entry["provider"] = kwargs["provider"]
        if "backend" in kwargs:
            entry["backend"] = kwargs["backend"]
        
        # Add performance metrics if provided
        if "duration_ms" in kwargs:
            entry["duration_ms"] = kwargs["duration_ms"]
        if "energy" in kwargs:
            entry["energy"] = kwargs["energy"]
        
        # Add fallback information if provided
        if "fallback_reason" in kwargs:
            entry["fallback_reason"] = kwargs["fallback_reason"]
        
        # Add status if provided
        if "status" in kwargs:
            entry["status"] = kwargs["status"]
        
        # Add any additional fields
        for key, value in kwargs.items():
            if key not in ["message", "solver", "provider", "backend", "duration_ms", "energy", "fallback_reason", "status"]:
                entry[key] = value
        
        return entry
    
    def _log_structured(self, level: str, event: str, **kwargs):
        """Log structured entry at specified level."""
        entry = self._create_log_entry(level, event, **kwargs)
        
        # Convert to JSON for structured logging
        log_message = json.dumps(entry, default=str, separators=(',', ':'))
        
        # Log at appropriate level
        if level == "DEBUG":
            self.logger.debug(log_message)
        elif level == "INFO":
            self.logger.info(log_message)
        elif level == "WARNING":
            self.logger.warning(log_message)
        elif level == "ERROR":
            self.logger.error(log_message)
        elif level == "CRITICAL":
            self.logger.critical(log_message)
    
    def debug(self, event: str, **kwargs):
        """Log debug event."""
        self._log_structured("DEBUG", event, **kwargs)
    
    def info(self, event: str, **kwargs):
        """Log info event."""
        self._log_structured("INFO", event, **kwargs)
    
    def warning(self, event: str, **kwargs):
        """Log warning event."""
        self._log_structured("WARNING", event, **kwargs)
    
    def error(self, event: str, **kwargs):
        """Log error event."""
        self._log_structured("ERROR", event, **kwargs)
    
    def critical(self, event: str, **kwargs):
        """Log critical event."""
        self._log_structured("CRITICAL", event, **kwargs)
    
    def solver_start(self, solver: str, provider: str = None, backend: str = None, **kwargs):
        """Log solver execution start."""
        self.info(
            event="SOLVER_EXECUTION_START",
            solver=solver,
            provider=provider,
            backend=backend,
            **kwargs
        )
    
    def solver_success(self, solver: str, duration_ms: float, energy: float = None, **kwargs):
        """Log solver execution success."""
        self.info(
            event="SOLVER_EXECUTION_SUCCESS",
            solver=solver,
            duration_ms=duration_ms,
            energy=energy,
            **kwargs
        )
    
    def solver_failure(self, solver: str, error: str, **kwargs):
        """Log solver execution failure."""
        self.error(
            event="SOLVER_EXECUTION_FAILURE",
            solver=solver,
            message=error,
            **kwargs
        )
    
    def solver_fallback(self, from_solver: str, to_solver: str, reason: str, **kwargs):
        """Log solver fallback."""
        self.warning(
            event="SOLVER_EXECUTION_FALLBACK",
            solver=from_solver,
            fallback_reason=reason,
            status=f"fallback_to_{to_solver}",
            **kwargs
        )
    
    def benchmark_start(self, num_solvers: int, problem_size: int, **kwargs):
        """Log benchmark execution start."""
        self.info(
            event="BENCHMARK_EXECUTION_START",
            num_solvers=num_solvers,
            problem_size=problem_size,
            **kwargs
        )
    
    def benchmark_complete(self, duration_ms: float, successful_solvers: int, **kwargs):
        """Log benchmark execution completion."""
        self.info(
            event="BENCHMARK_EXECUTION_COMPLETE",
            duration_ms=duration_ms,
            successful_solvers=successful_solvers,
            **kwargs
        )
    
    def set_benchmark_session(self, session_id: str):
        """Set benchmark session ID for current thread."""
        self._thread_local.benchmark_session_id = session_id
    
    def clear_benchmark_session(self):
        """Clear benchmark session ID for current thread."""
        if hasattr(self._thread_local, 'benchmark_session_id'):
            delattr(self._thread_local, 'benchmark_session_id')


# Global structured logger instances
_structured_loggers = {}

def get_structured_logger(name: str) -> StructuredLogger:
    """Get or create structured logger instance."""
    if name not in _structured_loggers:
        _structured_loggers[name] = StructuredLogger(name)
    return _structured_loggers[name]
