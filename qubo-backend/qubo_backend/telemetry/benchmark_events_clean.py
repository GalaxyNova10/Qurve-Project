"""
Qurve AI - Benchmark Events (Clean Version)
Enterprise-grade benchmark event tracking with zero circular dependencies
"""

import time
import threading
from typing import Dict, Any, List, Optional

# Import from shared models to break circular dependencies
from .shared.event_models import (
    BaseEvent, BenchmarkEvent, TaskEvent, WorkerEvent, 
    EventType, ComponentType, StatusType
)
from .shared.context_models import TelemetryContext, BenchmarkContext, ExecutionContext
from .shared.correlation_models import CorrelationId, BenchmarkSessionId, create_correlation_id, create_benchmark_session_id


class BenchmarkEventTracker:
    """
    Enterprise-grade benchmark event tracking and analysis.
    
    Provides:
    - Complete execution chain tracking
    - Performance analytics
    - Fallback analysis
    - Error correlation
    - Thread-safe operations
    """
    
    def __init__(self):
        self._events: List[BaseEvent] = []
        self._lock = threading.Lock()
        self._start_times: Dict[str, float] = {}
        self._solver_chains: Dict[str, List[str]] = {}
    
    def add_event(self, event: BaseEvent):
        """Add benchmark event to tracking."""
        with self._lock:
            self._events.append(event)
    
    def solver_start(self, solver: str, provider: str = None, backend: str = None, **metadata):
        """Track solver execution start."""
        event = TaskEvent(
            event_type=EventType.SOLVER_START,
            solver=solver,
            provider=provider,
            backend=backend,
            metadata=metadata
        )
        
        self.add_event(event)
        self._start_times[solver] = time.perf_counter()
    
    def solver_success(self, solver: str, energy: float = None, provider: str = None, backend: str = None, **metadata):
        """Track solver execution success."""
        start_time = self._start_times.get(solver)
        duration_ms = None
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000
            del self._start_times[solver]
        
        event = TaskEvent(
            event_type=EventType.SOLVER_SUCCESS,
            solver=solver,
            provider=provider,
            backend=backend,
            status=StatusType.SUCCESS,
            duration_ms=duration_ms,
            metadata=metadata
        )
        
        if energy is not None:
            event.metadata["energy"] = energy
        
        self.add_event(event)
    
    def solver_failure(self, solver: str, error: str, provider: str = None, backend: str = None, **metadata):
        """Track solver execution failure."""
        start_time = self._start_times.get(solver)
        duration_ms = None
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000
            del self._start_times[solver]
        
        event = TaskEvent(
            event_type=EventType.SOLVER_FAILURE,
            solver=solver,
            provider=provider,
            backend=backend,
            status=StatusType.FAILURE,
            duration_ms=duration_ms,
            error=error,
            metadata=metadata
        )
        
        self.add_event(event)
    
    def solver_fallback(self, from_solver: str, to_solver: str, reason: str, **metadata):
        """Track solver fallback event."""
        event = TaskEvent(
            event_type=EventType.FALLBACK_TRIGGERED,
            solver=from_solver,
            status=StatusType.CANCELLED,
            fallback_reason=reason,
            metadata={
                "fallback_to": to_solver,
                **metadata
            }
        )
        
        self.add_event(event)
        
        # Track fallback chain
        if from_solver not in self._solver_chains:
            self._solver_chains[from_solver] = []
        self._solver_chains[from_solver].append(to_solver)
    
    def benchmark_start(self, num_solvers: int, problem_size: int, **metadata):
        """Track benchmark execution start."""
        event = BenchmarkEvent(
            event_type=EventType.BENCHMARK_START,
            num_solvers=num_solvers,
            problem_size=problem_size,
            metadata=metadata
        )
        
        self.add_event(event)
    
    def benchmark_complete(self, successful_solvers: int, total_solvers: int, **metadata):
        """Track benchmark execution completion."""
        event = BenchmarkEvent(
            event_type=EventType.BENCHMARK_COMPLETE,
            successful_solvers=successful_solvers,
            total_solvers=total_solvers,
            status=StatusType.COMPLETED,
            metadata={
                "success_rate": successful_solvers / total_solvers if total_solvers > 0 else 0,
                **metadata
            }
        )
        
        self.add_event(event)
    
    def task_start(self, task_id: str, task_type: str, **metadata):
        """Track task start."""
        event = TaskEvent(
            event_type=EventType.TASK_START,
            task_id=task_id,
            task_type=task_type,
            status=StatusType.RUNNING,
            metadata=metadata
        )
        
        self.add_event(event)
        self._start_times[task_id] = time.perf_counter()
    
    def task_complete(self, task_id: str, result: Any = None, **metadata):
        """Track task completion."""
        start_time = self._start_times.get(task_id)
        duration_ms = None
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000
            del self._start_times[task_id]
        
        event = TaskEvent(
            event_type=EventType.TASK_SUCCESS,
            task_id=task_id,
            status=StatusType.COMPLETED,
            duration_ms=duration_ms,
            result=result,
            metadata=metadata
        )
        
        self.add_event(event)
    
    def task_failure(self, task_id: str, error: str, **metadata):
        """Track task failure."""
        start_time = self._start_times.get(task_id)
        duration_ms = None
        if start_time:
            duration_ms = (time.perf_counter() - start_time) * 1000
            del self._start_times[task_id]
        
        event = TaskEvent(
            event_type=EventType.TASK_FAILURE,
            task_id=task_id,
            status=StatusType.FAILURE,
            duration_ms=duration_ms,
            error=error,
            metadata=metadata
        )
        
        self.add_event(event)
    
    def queue_event(self, event_type: EventType, queue_depth: int, **metadata):
        """Track queue events."""
        from .shared.event_models import QueueEvent
        
        event = QueueEvent(
            event_type=event_type,
            queue_depth=queue_depth,
            metadata=metadata
        )
        
        self.add_event(event)
    
    def worker_event(self, event_type: EventType, worker_pool_size: int, active_workers: int, **metadata):
        """Track worker events."""
        from .shared.event_models import WorkerEvent
        
        event = WorkerEvent(
            event_type=event_type,
            worker_pool_size=worker_pool_size,
            active_workers=active_workers,
            metadata=metadata
        )
        
        self.add_event(event)
    
    def get_events(self, event_type: str = None, solver: str = None) -> List[BaseEvent]:
        """Get filtered events."""
        with self._lock:
            events = self._events.copy()
        
        filtered_events = []
        for event in events:
            # Filter by event type
            if event_type and event.event_type != event_type:
                continue
            
            # Filter by solver
            if solver and event.solver != solver:
                continue
            
            filtered_events.append(event)
        
        return filtered_events
    
    def get_solver_chain(self, initial_solver: str) -> List[str]:
        """Get complete fallback chain for a solver."""
        chain = [initial_solver]
        current = initial_solver
        
        # Trace fallback chain
        while current in self._solver_chains:
            next_solver = self._solver_chains[current][-1]  # Get last fallback
            if next_solver in chain:  # Prevent infinite loops
                break
            chain.append(next_solver)
            current = next_solver
        
        return chain
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary from tracked events."""
        with self._lock:
            events = self._events.copy()
        
        # Calculate performance metrics
        solver_performance = {}
        successful_events = [e for e in events if e.event_type == EventType.SOLVER_SUCCESS]
        failure_events = [e for e in events if e.event_type == EventType.SOLVER_FAILURE]
        
        for event in successful_events:
            if event.solver:
                if event.solver not in solver_performance:
                    solver_performance[event.solver] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'total_duration_ms': 0,
                        'energies': [],
                        'provider': event.provider,
                        'backend': event.backend
                    }
                
                solver_performance[event.solver]['success_count'] += 1
                if event.duration_ms:
                    solver_performance[event.solver]['total_duration_ms'] += event.duration_ms
                if event.metadata.get('energy'):
                    solver_performance[event.solver]['energies'].append(event.metadata['energy'])
        
        for event in failure_events:
            if event.solver:
                if event.solver not in solver_performance:
                    solver_performance[event.solver] = {
                        'success_count': 0,
                        'failure_count': 0,
                        'total_duration_ms': 0,
                        'energies': [],
                        'provider': event.provider,
                        'backend': event.backend
                    }
                
                solver_performance[event.solver]['failure_count'] += 1
                if event.duration_ms:
                    solver_performance[event.solver]['total_duration_ms'] += event.duration_ms
        
        # Calculate averages and statistics
        for solver, perf in solver_performance.items():
            total_runs = perf['success_count'] + perf['failure_count']
            if total_runs > 0:
                perf['success_rate'] = perf['success_count'] / total_runs
                perf['avg_duration_ms'] = perf['total_duration_ms'] / total_runs
            else:
                perf['success_rate'] = 0
                perf['avg_duration_ms'] = 0
            
            if perf['energies']:
                perf['avg_energy'] = sum(perf['energies']) / len(perf['energies'])
                perf['min_energy'] = min(perf['energies'])
                perf['max_energy'] = max(perf['energies'])
            else:
                perf['avg_energy'] = None
                perf['min_energy'] = None
                perf['max_energy'] = None
        
        return solver_performance
    
    def get_fallback_analysis(self) -> Dict[str, Any]:
        """Get fallback chain analysis."""
        with self._lock:
            events = self._events.copy()
        
        fallback_events = [e for e in events if e.event_type == EventType.FALLBACK_TRIGGERED]
        
        # Analyze fallback patterns
        fallback_analysis = {
            'total_fallbacks': len(fallback_events),
            'solvers_with_fallbacks': set(),
            'fallback_reasons': {},
            'fallback_chains': {}
        }
        
        for event in fallback_events:
            if event.solver:
                fallback_analysis['solvers_with_fallbacks'].add(event.solver)
            
            if event.fallback_reason:
                reason = event.fallback_reason
                fallback_analysis['fallback_reasons'][reason] = fallback_analysis['fallback_reasons'].get(reason, 0) + 1
            
            if event.solver and event.metadata.get('fallback_to'):
                chain = self.get_solver_chain(event.solver)
                fallback_analysis['fallback_chains'][event.solver] = chain
        
        return fallback_analysis
    
    def clear_events(self):
        """Clear all tracked events."""
        with self._lock:
            self._events.clear()
            self._start_times.clear()
            self._solver_chains.clear()


# Global event tracker instance
_event_tracker = None

def get_benchmark_event_tracker() -> BenchmarkEventTracker:
    """Get global benchmark event tracker instance."""
    global _event_tracker
    if _event_tracker is None:
        _event_tracker = BenchmarkEventTracker()
    return _event_tracker
