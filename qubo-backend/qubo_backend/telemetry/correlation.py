"""
Qurve AI - Correlation Management
Handles correlation IDs and benchmark session tracking
"""

import uuid
import threading
from typing import Optional
from contextlib import contextmanager

# Thread-local storage for correlation context
_thread_local = threading.local()


class CorrelationManager:
    """
    Enterprise-grade correlation ID and session management.
    
    Provides:
    - Unique correlation IDs per request
    - Benchmark session tracking
    - Thread-safe operations
    - Context management
    """
    
    def __init__(self):
        self._active_sessions = {}
        self._lock = threading.Lock()
    
    def generate_correlation_id(self) -> str:
        """Generate unique correlation ID for request tracing."""
        return f"qurve-{uuid.uuid4()}"
    
    def generate_benchmark_session_id(self) -> str:
        """Generate unique benchmark session ID."""
        return f"bench-{uuid.uuid4()}"
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread."""
        _thread_local.correlation_id = correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for current thread."""
        return getattr(_thread_local, 'correlation_id', None)
    
    def set_benchmark_session_id(self, session_id: str):
        """Set benchmark session ID for current thread."""
        _thread_local.benchmark_session_id = session_id
        
        # Track active sessions
        with self._lock:
            self._active_sessions[session_id] = {
                'thread_id': threading.current_thread().ident,
                'start_time': threading.current_thread().native_id,
                'correlation_id': self.get_correlation_id()
            }
    
    def get_benchmark_session_id(self) -> Optional[str]:
        """Get benchmark session ID for current thread."""
        return getattr(_thread_local, 'benchmark_session_id', None)
    
    def clear_session(self, session_id: str):
        """Clear benchmark session from tracking."""
        with self._lock:
            if session_id in self._active_sessions:
                del self._active_sessions[session_id]
    
    def get_active_sessions(self) -> dict:
        """Get all active benchmark sessions."""
        with self._lock:
            return self._active_sessions.copy()
    
    @contextmanager
    def correlation_context(self, correlation_id: str = None):
        """
        Context manager for correlation ID management.
        
        Usage:
            with correlation_manager.correlation_context("qurve-123"):
                # All operations in this context will have correlation ID
                pass
        """
        # Generate correlation ID if not provided
        if correlation_id is None:
            correlation_id = self.generate_correlation_id()
        
        # Store previous correlation ID
        previous_id = self.get_correlation_id()
        
        try:
            # Set new correlation ID
            self.set_correlation_id(correlation_id)
            yield correlation_id
        finally:
            # Restore previous correlation ID
            if previous_id:
                self.set_correlation_id(previous_id)
            else:
                # Clear correlation ID if none was set before
                _thread_local.correlation_id = None
    
    @contextmanager
    def benchmark_session_context(self, session_id: str = None):
        """
        Context manager for benchmark session management.
        
        Usage:
            with correlation_manager.benchmark_session_context():
                # All operations in this context will have session ID
                pass
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = self.generate_benchmark_session_id()
        
        # Store previous session ID
        previous_session_id = self.get_benchmark_session_id()
        
        try:
            # Set new session ID
            self.set_benchmark_session_id(session_id)
            yield session_id
        finally:
            # Clear session
            self.clear_session(session_id)
            # Restore previous session ID if exists
            if previous_session_id:
                self.set_benchmark_session_id(previous_session_id)


# Global correlation manager instance
_correlation_manager = None

def get_correlation_manager() -> CorrelationManager:
    """Get global correlation manager instance."""
    global _correlation_manager
    if _correlation_manager is None:
        _correlation_manager = CorrelationManager()
    return _correlation_manager

def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current thread."""
    return get_correlation_manager().get_correlation_id()

def get_benchmark_session_id() -> Optional[str]:
    """Get benchmark session ID for current thread."""
    return get_correlation_manager().get_benchmark_session_id()

def generate_correlation_id() -> str:
    """Generate new correlation ID."""
    return get_correlation_manager().generate_correlation_id()

def generate_benchmark_session_id() -> str:
    """Generate new benchmark session ID."""
    return get_correlation_manager().generate_benchmark_session_id()
