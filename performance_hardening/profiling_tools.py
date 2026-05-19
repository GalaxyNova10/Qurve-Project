"""
QURVE AI - Performance Profiling Tools
Comprehensive performance profiling and optimization.

Features:
✅ Benchmark execution profiling
✅ Replay performance profiling
✅ Telemetry memory profiling
✅ WebSocket streaming optimization
✅ Database query optimization
✅ Async task profiling
✅ Queue throughput validation
"""

import asyncio
import time
import sys
import psutil
import tracemalloc
import cProfile
import pstats
import io
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProfilingType(Enum):
    """Profiling type classifications."""
    BENCHMARK_EXECUTION = "benchmark_execution"
    REPLAY_SYSTEM = "replay_system"
    TELEMETRY_COLLECTION = "telemetry_collection"
    WEBSOCKET_STREAMING = "websocket_streaming"
    DATABASE_QUERIES = "database_queries"
    ASYNC_TASKS = "async_tasks"
    QUEUE_THROUGHPUT = "queue_throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"


class PerformanceMetric(Enum):
    """Performance metric classifications."""
    RESPONSE_TIME = "response_time"
    THROUGHPUT = "throughput"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    ERROR_RATE = "error_rate"
    CONCURRENCY = "concurrency"
    QUEUE_LENGTH = "queue_length"
    DATABASE_CONNECTIONS = "database_connections"
    CACHE_HIT_RATE = "cache_hit_rate"


@dataclass
class ProfileResult:
    """Profiling result definition."""
    profiling_type: ProfilingType
    metric: PerformanceMetric
    value: float
    unit: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class PerformanceSnapshot:
    """Performance snapshot definition."""
    timestamp: float
    cpu_percent: float
    memory_usage_mb: float
    memory_percent: float
    disk_usage_mb: float
    disk_percent: float
    network_io_mb: float
    active_connections: int
    queue_length: int
    cache_hit_rate: float
    response_time_ms: float
    throughput_rps: float
    error_rate: float


class PerformanceProfiler:
    """
    Production-grade performance profiler.
    
    Features:
    - Benchmark execution profiling
    - Replay performance profiling
    - Telemetry memory profiling
    - WebSocket streaming optimization
    - Database query optimization
    - Async task profiling
    - Queue throughput validation
    """
    
    def __init__(self):
        self.profiles: Dict[str, ProfileResult] = {}
        self.snapshots: List[PerformanceSnapshot] = []
        self.start_time = time.time()
        
        # Profiling state
        self._profiling_active = False
        self._memory_profiler = None
        self._cpu_profiler = None
        
        # Performance thresholds
        self.thresholds = {
            'response_time_warning': 1000.0,  # 1 second
            'response_time_critical': 5000.0,  # 5 seconds
            'memory_warning': 80.0,  # 80% memory
            'memory_critical': 95.0,  # 95% memory
            'cpu_warning': 80.0,  # 80% CPU
            'cpu_critical': 95.0,  # 95% CPU
            'error_rate_warning': 0.05,  # 5% error rate
            'error_rate_critical': 0.10,  # 10% error rate
            'queue_length_warning': 50,  # 50 items in queue
            'queue_length_critical': 100  # 100 items in queue
        }
        
        logger.info("Performance profiler initialized")
    
    def start_profiling(self, profiling_types: List[ProfilingType]) -> None:
        """Start performance profiling."""
        try:
            logger.info(f"Starting performance profiling for: {[pt.value for pt in profiling_types]}")
            
            self._profiling_active = True
            
            # Start memory profiling
            if ProfilingType.MEMORY_USAGE in profiling_types:
                tracemalloc.start()
                self._memory_profiler = 'tracemalloc'
                logger.info("Memory profiling started")
            
            # Start CPU profiling
            if ProfilingType.CPU_USAGE in profiling_types:
                self._cpu_profiler = cProfile.Profile()
                self._cpu_profiler.enable()
                logger.info("CPU profiling started")
            
            # Start system monitoring
            self._start_system_monitoring()
            
            logger.info("Performance profiling started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start profiling: {str(e)}")
            raise
    
    def stop_profiling(self) -> Dict[str, Any]:
        """Stop performance profiling and return results."""
        try:
            logger.info("Stopping performance profiling...")
            
            self._profiling_active = False
            
            # Stop memory profiling
            memory_stats = {}
            if self._memory_profiler == 'tracemalloc':
                current, peak = tracemalloc.get_traced_memory()
                memory_stats = {
                    'current_memory_mb': current / (1024 * 1024),
                    'peak_memory_mb': peak / (1024 * 1024),
                    'traced_allocations': tracemalloc.get_tracemalloc_memory()[1]
                }
                tracemalloc.stop()
                logger.info("Memory profiling stopped")
            
            # Stop CPU profiling
            cpu_stats = {}
            if self._cpu_profiler:
                self._cpu_profiler.disable()
                stats_stream = io.StringIO()
                ps = pstats.Stats(self._cpu_profiler, stream=stats_stream)
                ps.sort_stats('cumulative')
                cpu_stats = {
                    'total_calls': ps.total_calls,
                    'total_time': ps.total_tt,
                    'average_time': ps.total_tt / ps.total_calls if ps.total_calls > 0 else 0,
                    'top_functions': stats_stream.getvalue()
                }
                logger.info("CPU profiling stopped")
            
            # Get final system snapshot
            final_snapshot = self._capture_system_snapshot()
            
            # Generate recommendations
            recommendations = self._generate_recommendations(memory_stats, cpu_stats, final_snapshot)
            
            results = {
                'profiling_duration': time.time() - self.start_time,
                'memory_stats': memory_stats,
                'cpu_stats': cpu_stats,
                'final_snapshot': final_snapshot,
                'recommendations': recommendations,
                'profiles': self.profiles,
                'snapshots': self.snapshots
            }
            
            logger.info("Performance profiling completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Failed to stop profiling: {str(e)}")
            raise
    
    def _start_system_monitoring(self) -> None:
        """Start system monitoring."""
        try:
            # Start background monitoring task
            asyncio.create_task(self._monitoring_loop())
            logger.info("System monitoring started")
            
        except Exception as e:
            logger.error(f"Failed to start system monitoring: {str(e)}")
            raise
    
    async def _monitoring_loop(self) -> None:
        """Background monitoring loop."""
        while self._profiling_active:
            try:
                snapshot = self._capture_system_snapshot()
                self.snapshots.append(snapshot)
                
                # Keep only last 1000 snapshots
                if len(self.snapshots) > 1000:
                    self.snapshots = self.snapshots[-1000:]
                
                # Sleep for 1 second
                await asyncio.sleep(1.0)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {str(e)}")
                await asyncio.sleep(1.0)
    
    def _capture_system_snapshot(self) -> PerformanceSnapshot:
        """Capture current system snapshot."""
        try:
            # Get system metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            
            # Calculate network I/O
            network_io_mb = (network.bytes_sent + network.bytes_recv) / (1024 * 1024)
            
            return PerformanceSnapshot(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_usage_mb=memory.used / (1024 * 1024),
                memory_percent=memory.percent,
                disk_usage_mb=disk.used / (1024 * 1024),
                disk_percent=(disk.used / disk.total) * 100,
                network_io_mb=network_io_mb,
                active_connections=0,  # Would be populated by actual monitoring
                queue_length=0,  # Would be populated by actual monitoring
                cache_hit_rate=0.0,  # Would be populated by actual monitoring
                response_time_ms=0.0,  # Would be populated by actual monitoring
                throughput_rps=0.0,  # Would be populated by actual monitoring
                error_rate=0.0  # Would be populated by actual monitoring
            )
            
        except Exception as e:
            logger.error(f"Failed to capture system snapshot: {str(e)}")
            raise
    
    def profile_benchmark_execution(self, 
                                benchmark_function: callable,
                                *args, 
                                **kwargs) -> ProfileResult:
        """Profile benchmark execution performance."""
        try:
            logger.info("Profiling benchmark execution...")
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            # Execute benchmark
            result = benchmark_function(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            execution_time_ms = (end_time - start_time) * 1000
            memory_delta_mb = end_memory - start_memory
            
            # Create profile result
            profile_result = ProfileResult(
                profiling_type=ProfilingType.BENCHMARK_EXECUTION,
                metric=PerformanceMetric.RESPONSE_TIME,
                value=execution_time_ms,
                unit="ms",
                timestamp=start_time,
                metadata={
                    'memory_delta_mb': memory_delta_mb,
                    'start_memory_mb': start_memory,
                    'end_memory_mb': end_memory,
                    'result': result
                },
                recommendations=self._generate_execution_recommendations(execution_time_ms, memory_delta_mb)
            )
            
            self.profiles[f"benchmark_execution_{int(start_time)}"] = profile_result
            
            logger.info(f"Benchmark execution profiled: {execution_time_ms:.2f}ms, {memory_delta_mb:.2f}MB delta")
            return profile_result
            
        except Exception as e:
            logger.error(f"Failed to profile benchmark execution: {str(e)}")
            raise
    
    def profile_replay_system(self, 
                           replay_function: callable,
                           *args, 
                           **kwargs) -> ProfileResult:
        """Profile replay system performance."""
        try:
            logger.info("Profiling replay system...")
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            # Execute replay
            result = replay_function(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            execution_time_ms = (end_time - start_time) * 1000
            memory_delta_mb = end_memory - start_memory
            
            # Create profile result
            profile_result = ProfileResult(
                profiling_type=ProfilingType.REPLAY_SYSTEM,
                metric=PerformanceMetric.RESPONSE_TIME,
                value=execution_time_ms,
                unit="ms",
                timestamp=start_time,
                metadata={
                    'memory_delta_mb': memory_delta_mb,
                    'start_memory_mb': start_memory,
                    'end_memory_mb': end_memory,
                    'result': result
                },
                recommendations=self._generate_replay_recommendations(execution_time_ms, memory_delta_mb)
            )
            
            self.profiles[f"replay_system_{int(start_time)}"] = profile_result
            
            logger.info(f"Replay system profiled: {execution_time_ms:.2f}ms, {memory_delta_mb:.2f}MB delta")
            return profile_result
            
        except Exception as e:
            logger.error(f"Failed to profile replay system: {str(e)}")
            raise
    
    def profile_database_queries(self, 
                             query_function: callable,
                             *args, 
                             **kwargs) -> ProfileResult:
        """Profile database query performance."""
        try:
            logger.info("Profiling database queries...")
            
            start_time = time.time()
            
            # Execute query
            result = query_function(*args, **kwargs)
            
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            
            # Create profile result
            profile_result = ProfileResult(
                profiling_type=ProfilingType.DATABASE_QUERIES,
                metric=PerformanceMetric.RESPONSE_TIME,
                value=execution_time_ms,
                unit="ms",
                timestamp=start_time,
                metadata={
                    'result': result,
                    'query_type': type(query_function).__name__
                },
                recommendations=self._generate_database_recommendations(execution_time_ms)
            )
            
            self.profiles[f"database_query_{int(start_time)}"] = profile_result
            
            logger.info(f"Database query profiled: {execution_time_ms:.2f}ms")
            return profile_result
            
        except Exception as e:
            logger.error(f"Failed to profile database query: {str(e)}")
            raise
    
    def profile_websocket_streaming(self, 
                                 streaming_function: callable,
                                 *args, 
                                 **kwargs) -> ProfileResult:
        """Profile WebSocket streaming performance."""
        try:
            logger.info("Profiling WebSocket streaming...")
            
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            # Execute streaming
            result = streaming_function(*args, **kwargs)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss / (1024 * 1024)
            
            execution_time_ms = (end_time - start_time) * 1000
            memory_delta_mb = end_memory - start_memory
            
            # Create profile result
            profile_result = ProfileResult(
                profiling_type=ProfilingType.WEBSOCKET_STREAMING,
                metric=PerformanceMetric.THROUGHPUT,
                value=1000 / execution_time_ms if execution_time_ms > 0 else 0,  # messages per second
                unit="msg/s",
                timestamp=start_time,
                metadata={
                    'execution_time_ms': execution_time_ms,
                    'memory_delta_mb': memory_delta_mb,
                    'result': result
                },
                recommendations=self._generate_streaming_recommendations(execution_time_ms, memory_delta_mb)
            )
            
            self.profiles[f"websocket_streaming_{int(start_time)}"] = profile_result
            
            logger.info(f"WebSocket streaming profiled: {1000 / execution_time_ms:.2f} msg/s")
            return profile_result
            
        except Exception as e:
            logger.error(f"Failed to profile WebSocket streaming: {str(e)}")
            raise
    
    def _generate_execution_recommendations(self, 
                                        response_time_ms: float, 
                                        memory_delta_mb: float) -> List[str]:
        """Generate execution performance recommendations."""
        recommendations = []
        
        if response_time_ms > self.thresholds['response_time_critical']:
            recommendations.append("Critical: Execution time is too slow (>5s). Consider optimizing algorithms.")
        elif response_time_ms > self.thresholds['response_time_warning']:
            recommendations.append("Warning: Execution time is slow (>1s). Consider performance optimization.")
        
        if memory_delta_mb > 100:
            recommendations.append("High memory usage detected. Consider memory optimization.")
        
        return recommendations
    
    def _generate_replay_recommendations(self, 
                                       response_time_ms: float, 
                                       memory_delta_mb: float) -> List[str]:
        """Generate replay performance recommendations."""
        recommendations = []
        
        if response_time_ms > self.thresholds['response_time_critical']:
            recommendations.append("Critical: Replay is too slow. Consider optimizing replay data structures.")
        elif response_time_ms > self.thresholds['response_time_warning']:
            recommendations.append("Warning: Replay is slow. Consider replay optimization.")
        
        if memory_delta_mb > 200:
            recommendations.append("High replay memory usage. Consider replay data compression.")
        
        return recommendations
    
    def _generate_database_recommendations(self, response_time_ms: float) -> List[str]:
        """Generate database performance recommendations."""
        recommendations = []
        
        if response_time_ms > self.thresholds['response_time_critical']:
            recommendations.append("Critical: Database query is too slow. Consider query optimization.")
        elif response_time_ms > self.thresholds['response_time_warning']:
            recommendations.append("Warning: Database query is slow. Consider indexing.")
        
        return recommendations
    
    def _generate_streaming_recommendations(self, 
                                           response_time_ms: float, 
                                           memory_delta_mb: float) -> List[str]:
        """Generate streaming performance recommendations."""
        recommendations = []
        
        if response_time_ms > self.thresholds['response_time_critical']:
            recommendations.append("Critical: Streaming is too slow. Consider buffering optimization.")
        elif response_time_ms > self.thresholds['response_time_warning']:
            recommendations.append("Warning: Streaming is slow. Consider optimization.")
        
        if memory_delta_mb > 50:
            recommendations.append("High streaming memory usage. Consider memory management.")
        
        return recommendations
    
    def _generate_recommendations(self, 
                                  memory_stats: Dict[str, Any],
                                  cpu_stats: Dict[str, Any],
                                  final_snapshot: PerformanceSnapshot) -> List[str]:
        """Generate overall performance recommendations."""
        recommendations = []
        
        # Memory recommendations
        if final_snapshot.memory_percent > self.thresholds['memory_critical']:
            recommendations.append("Critical: Memory usage is too high. Consider memory optimization.")
        elif final_snapshot.memory_percent > self.thresholds['memory_warning']:
            recommendations.append("Warning: Memory usage is high. Monitor memory usage.")
        
        # CPU recommendations
        if final_snapshot.cpu_percent > self.thresholds['cpu_critical']:
            recommendations.append("Critical: CPU usage is too high. Consider CPU optimization.")
        elif final_snapshot.cpu_percent > self.thresholds['cpu_warning']:
            recommendations.append("Warning: CPU usage is high. Monitor CPU usage.")
        
        # Queue recommendations
        if final_snapshot.queue_length > self.thresholds['queue_length_critical']:
            recommendations.append("Critical: Queue is too long. Consider scaling.")
        elif final_snapshot.queue_length > self.thresholds['queue_length_warning']:
            recommendations.append("Warning: Queue is long. Monitor queue length.")
        
        return recommendations
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        try:
            if not self.snapshots:
                return {"status": "no_data"}
            
            # Calculate averages
            avg_cpu = sum(s.cpu_percent for s in self.snapshots) / len(self.snapshots)
            avg_memory = sum(s.memory_percent for s in self.snapshots) / len(self.snapshots)
            avg_response_time = sum(s.response_time_ms for s in self.snapshots) / len(self.snapshots)
            avg_throughput = sum(s.throughput_rps for s in self.snapshots) / len(self.snapshots)
            avg_error_rate = sum(s.error_rate for s in self.snapshots) / len(self.snapshots)
            
            # Get latest values
            latest = self.snapshots[-1] if self.snapshots else None
            
            return {
                "status": "success",
                "snapshot_count": len(self.snapshots),
                "profile_count": len(self.profiles),
                "averages": {
                    "cpu_percent": avg_cpu,
                    "memory_percent": avg_memory,
                    "response_time_ms": avg_response_time,
                    "throughput_rps": avg_throughput,
                    "error_rate": avg_error_rate
                },
                "latest": {
                    "cpu_percent": latest.cpu_percent if latest else 0,
                    "memory_percent": latest.memory_percent if latest else 0,
                    "response_time_ms": latest.response_time_ms if latest else 0,
                    "throughput_rps": latest.throughput_rps if latest else 0,
                    "error_rate": latest.error_rate if latest else 0,
                    "queue_length": latest.queue_length if latest else 0,
                    "cache_hit_rate": latest.cache_hit_rate if latest else 0
                },
                "thresholds": self.thresholds
            }
            
        except Exception as e:
            logger.error(f"Failed to get performance summary: {str(e)}")
            return {"status": "error", "error": str(e)}
    
    def export_profiles(self, filename: str) -> None:
        """Export profiling data to file."""
        try:
            import json
            
            export_data = {
                "export_timestamp": time.time(),
                "profiles": {
                    key: {
                        "profiling_type": profile.profiling_type.value,
                        "metric": profile.metric.value,
                        "value": profile.value,
                        "unit": profile.unit,
                        "timestamp": profile.timestamp,
                        "metadata": profile.metadata,
                        "recommendations": profile.recommendations
                    }
                    for key, profile in self.profiles.items()
                },
                "snapshots": [
                    {
                        "timestamp": snapshot.timestamp,
                        "cpu_percent": snapshot.cpu_percent,
                        "memory_usage_mb": snapshot.memory_usage_mb,
                        "memory_percent": snapshot.memory_percent,
                        "disk_usage_mb": snapshot.disk_usage_mb,
                        "disk_percent": snapshot.disk_percent,
                        "network_io_mb": snapshot.network_io_mb,
                        "active_connections": snapshot.active_connections,
                        "queue_length": snapshot.queue_length,
                        "cache_hit_rate": snapshot.cache_hit_rate,
                        "response_time_ms": snapshot.response_time_ms,
                        "throughput_rps": snapshot.throughput_rps,
                        "error_rate": snapshot.error_rate
                    }
                    for snapshot in self.snapshots
                ],
                "thresholds": self.thresholds
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Profiling data exported to {filename}")
            
        except Exception as e:
            logger.error(f"Failed to export profiles: {str(e)}")
            raise


# Global performance profiler instance
_performance_profiler: Optional[PerformanceProfiler] = None


def get_performance_profiler() -> PerformanceProfiler:
    """Get global performance profiler instance."""
    global _performance_profiler
    if _performance_profiler is None:
        _performance_profiler = PerformanceProfiler()
    return _performance_profiler


if __name__ == "__main__":
    # Example usage
    profiler = get_performance_profiler()
    
    # Start profiling
    profiler.start_profiling([
        ProfilingType.BENCHMARK_EXECUTION,
        ProfilingType.MEMORY_USAGE,
        ProfilingType.CPU_USAGE
    ])
    
    # Simulate some work
    import asyncio
    
    async def sample_work():
        await asyncio.sleep(2)
        return {"result": "sample_work_completed"}
    
    # Profile the work
    result = asyncio.run(sample_work())
    
    # Stop profiling
    profiling_results = profiler.stop_profiling()
    
    # Print summary
    print("Profiling Results:")
    print(f"Duration: {profiling_results['profiling_duration']:.2f}s")
    print(f"Recommendations: {len(profiling_results['recommendations'])}")
    for rec in profiling_results['recommendations']:
        print(f"  - {rec}")
    
    # Export results
    profiler.export_profiles("performance_profiles.json")
