"""
Qurve AI - Trace Context Management
Enterprise-grade trace context for request tracking
"""

import threading
from typing import Optional, Dict, Any
from contextlib import contextmanager

from .correlation import get_correlation_manager, get_correlation_id, get_benchmark_session_id


class TraceContext:
    """
    Enterprise-grade trace context for comprehensive request tracking.
    
    Provides:
    - Correlation ID management
    - Benchmark session tracking
    - Thread-safe operations
    - Context propagation
    - Performance timing
    """
    
    def __init__(self):
        self._thread_local = threading.local()
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current trace context with all available information."""
        context = {
            "correlation_id": get_correlation_id(),
            "benchmark_session_id": get_benchmark_session_id(),
            "thread_id": threading.current_thread().ident,
            "thread_name": threading.current_thread().name,
        }
        
        # Add custom context if available
        if hasattr(self._thread_local, 'custom_context'):
            context.update(self._thread_local.custom_context)
        
        return context
    
    def set_custom_context(self, **kwargs):
        """Set custom context for current thread."""
        if not hasattr(self._thread_local, 'custom_context'):
            self._thread_local.custom_context = {}
        
        self._thread_local.custom_context.update(kwargs)
    
    def get_custom_context(self, key: str, default: Any = None) -> Any:
        """Get custom context value."""
        if hasattr(self._thread_local, 'custom_context'):
            return self._thread_local.custom_context.get(key, default)
        return default
    
    def clear_custom_context(self):
        """Clear custom context for current thread."""
        if hasattr(self._thread_local, 'custom_context'):
            delattr(self._thread_local, 'custom_context')
    
    def with_context(self, **context):
        """
        Context manager for temporary context setting.
        
        Usage:
            with trace_context.with_context(solver="neal", provider="dwave"):
                # Operations here will have this context
                pass
        """
        return TraceContextManager(self, context)


class TraceContextManager:
    """Context manager for trace context operations."""
    
    def __init__(self, trace_context: TraceContext, context: Dict[str, Any]):
        self.trace_context = trace_context
        self.context = context
        self.previous_context = None
    
    def __enter__(self):
        # Store previous context
        self.previous_context = {}
        
        # Save current custom context
        if hasattr(self.trace_context._thread_local, 'custom_context'):
            self.previous_context = self.trace_context._thread_local.custom_context.copy()
        
        # Set new context
        self.trace_context.set_custom_context(**self.context)
        return self.trace_context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous context
        if self.previous_context is not None:
            self.trace_context._thread_local.custom_context = self.previous_context
        else:
            self.trace_context.clear_custom_context()


# Global trace context instance
_trace_context = None

def get_trace_context() -> TraceContext:
    """Get global trace context instance."""
    global _trace_context
    if _trace_context is None:
        _trace_context = TraceContext()
    return _trace_context

@contextmanager
def solver_trace_context(solver: str, provider: str = None, backend: str = None, **kwargs):
    """
    Context manager for solver execution tracing.
    
    Automatically sets:
    - Correlation ID
    - Benchmark session ID
    - Solver information
    - Provider/backend details
    """
    correlation_manager = get_correlation_manager()
    trace_context = get_trace_context()
    
    # Generate correlation ID if not set
    if not get_correlation_id():
        correlation_id = correlation_manager.generate_correlation_id()
        correlation_manager.set_correlation_id(correlation_id)
    
    # Generate benchmark session ID if not set
    if not get_benchmark_session_id():
        session_id = correlation_manager.generate_benchmark_session_id()
        correlation_manager.set_benchmark_session_id(session_id)
    
    # Set solver context
    solver_context = {
        "solver": solver,
        "provider": provider,
        "backend": backend,
        **kwargs
    }
    
    with trace_context.with_context(**solver_context):
        yield trace_context.get_current_context()

@contextmanager
def benchmark_trace_context(num_solvers: int = None, problem_size: int = None, **kwargs):
    """
    Context manager for benchmark execution tracing.
    
    Automatically sets:
    - Correlation ID
    - Benchmark session ID
    - Benchmark metadata
    """
    correlation_manager = get_correlation_manager()
    trace_context = get_trace_context()
    
    # Generate correlation ID if not set
    if not get_correlation_id():
        correlation_id = correlation_manager.generate_correlation_id()
        correlation_manager.set_correlation_id(correlation_id)
    
    # Generate benchmark session ID if not set
    if not get_benchmark_session_id():
        session_id = correlation_manager.generate_benchmark_session_id()
        correlation_manager.set_benchmark_session_id(session_id)
    
    # Set benchmark context
    benchmark_context = {
        "num_solvers": num_solvers,
        "problem_size": problem_size,
        **kwargs
    }
    
    with trace_context.with_context(**benchmark_context):
        yield trace_context.get_current_context()
