"""
Qurve AI - Structured Logger (Clean Version)
Enterprise-grade structured JSON logging with zero circular dependencies
"""

import logging
import json
import time
import threading
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import from shared models to break circular dependencies
from .shared.event_models import BaseEvent, EventType, ComponentType, StatusType
from .shared.context_models import TelemetryContext
from .shared.correlation_models import CorrelationId, BenchmarkSessionId, create_correlation_id, create_benchmark_session_id


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
        self.name = name
    
    def _get_base_context(self) -> Dict[str, Any]:
        """Get base logging context with correlation and timing."""
        correlation_id = self._get_correlation_id()
        benchmark_session_id = self._get_benchmark_session_id()
        
        context = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "correlation_id": correlation_id,
            "thread": threading.current_thread().name,
            "logger": self.name
        }
        
        # Add benchmark session ID if available
        if benchmark_session_id:
            context["benchmark_session_id"] = benchmark_session_id
        
        return context
    
    def _get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for current thread."""
        try:
            # Try to get from thread-local storage
            if hasattr(threading.current_thread(), '_correlation_id'):
                return threading.current_thread()._correlation_id
        except Exception:
            pass
        return None
    
    def _get_benchmark_session_id(self) -> Optional[str]:
        """Get benchmark session ID for current thread."""
        try:
            # Try to get from thread-local storage
            if hasattr(threading.current_thread(), '_benchmark_session_id'):
                return threading.current_thread()._benchmark_session_id
        except Exception:
            pass
        return None
    
    def info(self, msg: str, **kwargs):
        """Log info message with structured context."""
        context = self._get_base_context()
        context.update(kwargs)
        context["level"] = "INFO"
        context["message"] = msg
        
        self.logger.info(json.dumps(context, default=str))
    
    def warning(self, msg: str, **kwargs):
        """Log warning message with structured context."""
        context = self._get_base_context()
        context.update(kwargs)
        context["level"] = "WARNING"
        context["message"] = msg
        
        self.logger.warning(json.dumps(context, default=str))
    
    def error(self, msg: str, **kwargs):
        """Log error message with structured context."""
        context = self._get_base_context()
        context.update(kwargs)
        context["level"] = "ERROR"
        context["message"] = msg
        
        self.logger.error(json.dumps(context, default=str))
    
    def debug(self, msg: str, **kwargs):
        """Log debug message with structured context."""
        context = self._get_base_context()
        context.update(kwargs)
        context["level"] = "DEBUG"
        context["message"] = msg
        
        self.logger.debug(json.dumps(context, default=str))
    
    def event(self, event: BaseEvent):
        """Log structured event."""
        event_dict = event.to_dict()
        event_dict["logger"] = self.name
        
        self.logger.info(json.dumps(event_dict, default=str))
    
    def metric(self, name: str, value: float, **kwargs):
        """Log metric."""
        context = self._get_base_context()
        context.update(kwargs)
        context["metric_name"] = name
        context["metric_value"] = value
        context["type"] = "metric"
        
        self.logger.info(json.dumps(context, default=str))


class CorrelationManager:
    """Thread-safe correlation ID and benchmark session ID manager."""
    
    def __init__(self):
        self._lock = threading.Lock()
    
    def generate_correlation_id(self) -> str:
        """Generate new correlation ID."""
        correlation_id = create_correlation_id()
        self._set_correlation_id(str(correlation_id))
        return str(correlation_id)
    
    def generate_benchmark_session_id(self) -> str:
        """Generate new benchmark session ID."""
        session_id = create_benchmark_session_id()
        self._set_benchmark_session_id(str(session_id))
        return str(session_id)
    
    def get_correlation_id(self) -> Optional[str]:
        """Get current correlation ID."""
        return self._get_correlation_id()
    
    def get_benchmark_session_id(self) -> Optional[str]:
        """Get current benchmark session ID."""
        return self._get_benchmark_session_id()
    
    def _get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from thread-local storage."""
        try:
            return getattr(threading.current_thread(), '_correlation_id', None)
        except Exception:
            return None
    
    def _get_benchmark_session_id(self) -> Optional[str]:
        """Get benchmark session ID from thread-local storage."""
        try:
            return getattr(threading.current_thread(), '_benchmark_session_id', None)
        except Exception:
            return None
    
    def _set_correlation_id(self, correlation_id: str):
        """Set correlation ID in thread-local storage."""
        try:
            threading.current_thread()._correlation_id = correlation_id
        except Exception:
            pass
    
    def _set_benchmark_session_id(self, session_id: str):
        """Set benchmark session ID in thread-local storage."""
        try:
            threading.current_thread()._benchmark_session_id = session_id
        except Exception:
            pass


# Global instances
_logger_registry = {}
_correlation_manager = CorrelationManager()


def get_structured_logger(name: str) -> StructuredLogger:
    """Get structured logger instance."""
    if name not in _logger_registry:
        _logger_registry[name] = StructuredLogger(name)
    return _logger_registry[name]


def get_correlation_manager() -> CorrelationManager:
    """Get correlation manager instance."""
    return _correlation_manager


def generate_correlation_id() -> str:
    """Generate new correlation ID."""
    return _correlation_manager.generate_correlation_id()


def generate_benchmark_session_id() -> str:
    """Generate new benchmark session ID."""
    return _correlation_manager.generate_benchmark_session_id()


def get_correlation_id() -> Optional[str]:
    """Get current correlation ID."""
    return _correlation_manager.get_correlation_id()


def get_benchmark_session_id() -> Optional[str]:
    """Get current benchmark session ID."""
    return _correlation_manager.get_benchmark_session_id()


class CorrelationContext:
    """Context manager for correlation IDs."""
    
    def __init__(self, correlation_id: Optional[str] = None, benchmark_session_id: Optional[str] = None):
        self.correlation_id = correlation_id or generate_correlation_id()
        self.benchmark_session_id = benchmark_session_id or generate_benchmark_session_id()
        self._old_correlation_id = None
        self._old_session_id = None
    
    def __enter__(self):
        self._old_correlation_id = get_correlation_id()
        self._old_session_id = get_benchmark_session_id()
        
        _correlation_manager._set_correlation_id(self.correlation_id)
        _correlation_manager._set_benchmark_session_id(self.benchmark_session_id)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._old_correlation_id:
            _correlation_manager._set_correlation_id(self._old_correlation_id)
        if self._old_session_id:
            _correlation_manager._set_benchmark_session_id(self._old_session_id)


def solver_trace_context(solver: str, provider: str = None, backend: str = None):
    """Create solver-specific trace context."""
    correlation_id = generate_correlation_id()
    benchmark_session_id = generate_benchmark_session_id()
    
    return CorrelationContext(
        correlation_id=correlation_id,
        benchmark_session_id=benchmark_session_id
    )
