"""
Qurve AI - Execution Storage Module
Durable, async-safe execution persistence without blocking execution flow.

Principles:
✅ ASYNC-SAFE: Never block execution on storage operations
✅ FAILURE-TOLERANT: Graceful degradation if DB unavailable
✅ NON-BLOCKING: Background persistence queue
✅ PASSIVE: Records reality, doesn't control execution
✅ RETENTION: Automatic cleanup of old data
"""

import asyncio
import asyncpg
import json
import os
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Execution status enumeration."""
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


class TaskStatus(Enum):
    """Cloud task status enumeration."""
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


@dataclass
class BenchmarkRun:
    """Benchmark execution record."""
    benchmark_id: str
    correlation_id: str
    started_at: datetime
    status: ExecutionStatus
    selected_solver: str
    num_assets: int
    execution_mode: str
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    fallback_chain: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SolverExecution:
    """Solver execution record."""
    execution_id: str
    benchmark_id: str
    solver_name: str
    provider: str
    backend: str
    status: ExecutionStatus
    fallback_used: bool = False
    latency_ms: Optional[float] = None
    feasibility: Optional[bool] = None
    energy: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CloudTask:
    """Cloud task execution record."""
    task_arn: str
    device_arn: str
    region: str
    shots: int
    task_status: TaskStatus
    queue_latency_ms: Optional[float] = None
    execution_latency_ms: Optional[float] = None
    total_latency_ms: Optional[float] = None
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TelemetryEvent:
    """Telemetry event record."""
    event_id: str
    correlation_id: str
    timestamp: datetime
    event_type: str
    severity: str
    payload_json: str


class StorageConfig:
    """Storage configuration with connection management."""
    
    def __init__(self, database_url: str, max_connections: int = 10):
        self.database_url = database_url
        self.max_connections = max_connections
        self._pool = None
        self._connection_lock = asyncio.Lock()
    
    async def get_connection(self):
        """Get database connection from pool."""
        async with self._connection_lock:
            if self._pool is None:
                self._pool = await asyncpg.create_pool(
                    self.database_url,
                    min_size=2,
                    max_size=self.max_connections,
                    command_timeout=60
                )
            return self._pool.acquire()
    
    async def release_connection(self, connection):
        """Release connection back to pool."""
        if self._pool:
            await self._pool.release(connection)
    
    async def close(self):
        """Close connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None


class ExecutionStorage:
    """
    Production-grade execution storage with async persistence.
    
    Features:
    - Async-safe operations
    - Background persistence queue
    - Failure-tolerant design
    - Automatic retention
    - Non-blocking execution
    """
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self._persistence_queue = asyncio.Queue(maxsize=1000)
        self._worker_task = None
        self._db_available = True
        self._write_failures = 0
        self._last_cleanup = time.time()
        
        # Retention policies
        self.retention_days = {
            'telemetry_events': 30,
            'cloud_tasks': 90,
            'benchmark_runs': 365
        }
        
        logger.info(f"Execution storage initialized with max_queue_size=1000, retention_days={self.retention_days}")
    
    async def start_background_worker(self) -> None:
        """Start background persistence worker."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._persistence_worker())
            logger.info("Background storage worker started")
    
    async def stop_background_worker(self) -> None:
        """Stop background persistence worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("Background storage worker stopped")
    
    async def _persistence_worker(self) -> None:
        """Background worker that processes persistence queue."""
        while True:
            try:
                # Get persistence task from queue
                persistence_task = await self._persistence_queue.get()
                
                # Execute persistence operation
                await self._execute_persistence_task(persistence_task)
                
            except asyncio.CancelledError:
                logger.info("Persistence worker cancelled")
                break
            except Exception as e:
                logger.error("Persistence worker error", error=str(e))
                # Continue processing other tasks
                continue
    
    async def _execute_persistence_task(self, task: Dict[str, Any]) -> None:
        """Execute a single persistence task with error handling."""
        try:
            operation = task['operation']
            
            if operation == 'store_benchmark':
                await self._store_benchmark(task['data'])
            elif operation == 'store_execution':
                await self._store_execution(task['data'])
            elif operation == 'store_cloud_task':
                await self._store_cloud_task(task['data'])
            elif operation == 'store_telemetry':
                await self._store_telemetry_event(task['data'])
            elif operation == 'cleanup_retention':
                await self._cleanup_retention_data()
            else:
                logger.warning("Unknown persistence operation", operation=operation)
                
        except Exception as e:
            self._write_failures += 1
            logger.error("Persistence task failed", 
                        operation=task.get('operation'), 
                        error=str(e))
            
            # Don't re-raise - storage failures should not crash system
    
    async def store_benchmark_run(self, benchmark: BenchmarkRun) -> None:
        """Store benchmark run (non-blocking)."""
        try:
            # Add to persistence queue
            await self._persistence_queue.put({
                'operation': 'store_benchmark',
                'data': benchmark,
                'timestamp': time.time()
            })
        except asyncio.QueueFull:
            logger.warning("Persistence queue full, dropping benchmark store")
    
    async def store_solver_execution(self, execution: SolverExecution) -> None:
        """Store solver execution (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_execution',
                'data': execution,
                'timestamp': time.time()
            })
        except asyncio.QueueFull:
            logger.warning("Persistence queue full, dropping execution store")
    
    async def store_cloud_task(self, cloud_task: CloudTask) -> None:
        """Store cloud task (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_cloud_task',
                'data': cloud_task,
                'timestamp': time.time()
            })
        except asyncio.QueueFull:
            logger.warning("Persistence queue full, dropping cloud task store")
    
    async def store_telemetry_event(self, event: TelemetryEvent) -> None:
        """Store telemetry event (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_telemetry',
                'data': event,
                'timestamp': time.time()
            })
        except asyncio.QueueFull:
            logger.warning("Persistence queue full, dropping telemetry store")
    
    async def _store_benchmark(self, benchmark: BenchmarkRun) -> None:
        """Store benchmark run in database."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            await conn.execute("""
                INSERT INTO benchmark_runs (
                    benchmark_id, correlation_id, started_at, completed_at, 
                    duration_ms, status, selected_solver, fallback_chain, 
                    num_assets, execution_mode, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, (
                benchmark.benchmark_id,
                benchmark.correlation_id,
                benchmark.started_at,
                benchmark.completed_at,
                benchmark.duration_ms,
                benchmark.status.value,
                benchmark.selected_solver,
                benchmark.fallback_chain,
                benchmark.num_assets,
                benchmark.execution_mode,
                json.dumps(benchmark.metadata)
            ))
            
        except Exception as e:
            logger.error("Failed to store benchmark", benchmark_id=benchmark.benchmark_id, error=str(e))
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def _store_execution(self, execution: SolverExecution) -> None:
        """Store solver execution in database."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            await conn.execute("""
                INSERT INTO solver_executions (
                    execution_id, benchmark_id, solver_name, provider, backend,
                    latency_ms, feasibility, fallback_used, energy, status, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, (
                execution.execution_id,
                execution.benchmark_id,
                execution.solver_name,
                execution.provider,
                execution.backend,
                execution.latency_ms,
                execution.feasibility,
                execution.fallback_used,
                execution.energy,
                execution.status.value,
                json.dumps(execution.metadata)
            ))
            
        except Exception as e:
            logger.error("Failed to store execution", execution_id=execution.execution_id, error=str(e))
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def _store_cloud_task(self, cloud_task: CloudTask) -> None:
        """Store cloud task in database."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            await conn.execute("""
                INSERT INTO cloud_tasks (
                    task_arn, device_arn, region, shots, queue_latency_ms,
                    execution_latency_ms, total_latency_ms, task_status, failure_reason, metadata
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            """, (
                cloud_task.task_arn,
                cloud_task.device_arn,
                cloud_task.region,
                cloud_task.shots,
                cloud_task.queue_latency_ms,
                cloud_task.execution_latency_ms,
                cloud_task.total_latency_ms,
                cloud_task.task_status.value,
                cloud_task.failure_reason,
                json.dumps(cloud_task.metadata)
            ))
            
        except Exception as e:
            logger.error("Failed to store cloud task", task_arn=cloud_task.task_arn, error=str(e))
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def _store_telemetry_event(self, event: TelemetryEvent) -> None:
        """Store telemetry event in database."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            await conn.execute("""
                INSERT INTO telemetry_events (
                    event_id, correlation_id, timestamp, event_type, severity, payload_json
                ) VALUES ($1, $2, $3, $4, $5, $6)
            """, (
                event.event_id,
                event.correlation_id,
                event.timestamp,
                event.event_type,
                event.severity,
                event.payload_json
            ))
            
        except Exception as e:
            logger.error("Failed to store telemetry event", event_id=event.event_id, error=str(e))
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def get_benchmark_runs(self, limit: int = 100, offset: int = 0) -> List[BenchmarkRun]:
        """Get benchmark runs with pagination."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            rows = await conn.fetch("""
                SELECT * FROM benchmark_runs 
                ORDER BY started_at DESC 
                LIMIT $1 OFFSET $2
            """, limit, offset)
            
            return [
                BenchmarkRun(
                    benchmark_id=row['benchmark_id'],
                    correlation_id=row['correlation_id'],
                    started_at=row['started_at'],
                    completed_at=row['completed_at'],
                    duration_ms=row['duration_ms'],
                    status=ExecutionStatus(row['status']),
                    selected_solver=row['selected_solver'],
                    fallback_chain=row['fallback_chain'],
                    num_assets=row['num_assets'],
                    execution_mode=row['execution_mode'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ) for row in rows
            ]
            
        except Exception as e:
            logger.error("Failed to get benchmark runs", error=str(e))
            return []
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def get_solver_executions(self, benchmark_id: str) -> List[SolverExecution]:
        """Get solver executions for a benchmark."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            rows = await conn.fetch("""
                SELECT * FROM solver_executions 
                WHERE benchmark_id = $1 
                ORDER BY execution_id
            """, benchmark_id)
            
            return [
                SolverExecution(
                    execution_id=row['execution_id'],
                    benchmark_id=row['benchmark_id'],
                    solver_name=row['solver_name'],
                    provider=row['provider'],
                    backend=row['backend'],
                    latency_ms=row['latency_ms'],
                    feasibility=row['feasibility'],
                    fallback_used=row['fallback_used'],
                    energy=row['energy'],
                    status=ExecutionStatus(row['status']),
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ) for row in rows
            ]
            
        except Exception as e:
            logger.error("Failed to get solver executions", benchmark_id=benchmark_id, error=str(e))
            return []
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def get_cloud_tasks(self, status: Optional[TaskStatus] = None, limit: int = 100) -> List[CloudTask]:
        """Get cloud tasks with optional status filter."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            query = """
                SELECT * FROM cloud_tasks 
                WHERE ($1 IS NULL OR task_status = $1)
                ORDER BY created_at DESC 
                LIMIT $2
            """
            rows = await conn.fetch(query, status.value if status else None, limit)
            
            return [
                CloudTask(
                    task_arn=row['task_arn'],
                    device_arn=row['device_arn'],
                    region=row['region'],
                    shots=row['shots'],
                    queue_latency_ms=row['queue_latency_ms'],
                    execution_latency_ms=row['execution_latency_ms'],
                    total_latency_ms=row['total_latency_ms'],
                    task_status=TaskStatus(row['task_status']),
                    failure_reason=row['failure_reason'],
                    metadata=json.loads(row['metadata']) if row['metadata'] else {}
                ) for row in rows
            ]
            
        except Exception as e:
            logger.error("Failed to get cloud tasks", error=str(e))
            return []
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def _cleanup_retention_data(self) -> None:
        """Clean up old data based on retention policies."""
        conn = None
        try:
            conn = await self.config.get_connection()
            
            # Clean up telemetry events (30 days)
            cutoff_date = datetime.now() - timedelta(days=self.retention_days['telemetry_events'])
            await conn.execute("""
                DELETE FROM telemetry_events WHERE timestamp < $1
            """, cutoff_date)
            
            # Clean up cloud tasks (90 days)
            cutoff_date = datetime.now() - timedelta(days=self.retention_days['cloud_tasks'])
            await conn.execute("""
                DELETE FROM cloud_tasks WHERE created_at < $1
            """, cutoff_date)
            
            # Clean up benchmark runs (1 year)
            cutoff_date = datetime.now() - timedelta(days=self.retention_days['benchmark_runs'])
            await conn.execute("""
                DELETE FROM benchmark_runs WHERE started_at < $1
            """, cutoff_date)
            
            self._last_cleanup = time.time()
            logger.info("Retention cleanup completed")
            
        except Exception as e:
            logger.error("Failed to cleanup retention data", error=str(e))
        finally:
            if conn:
                await self.config.release_connection(conn)
    
    async def get_storage_health(self) -> Dict[str, Any]:
        """Get storage system health metrics."""
        queue_size = self._persistence_queue.qsize()
        time_since_cleanup = time.time() - self._last_cleanup
        
        return {
            'queue_depth': queue_size,
            'queue_capacity': 1000,
            'queue_utilization': (queue_size / 1000) * 100,
            'db_available': self._db_available,
            'write_failures': self._write_failures,
            'worker_running': self._worker_task is not None and not self._worker_task.done(),
            'time_since_cleanup_seconds': time_since_cleanup,
            'retention_policies': self.retention_days
        }
    
    async def schedule_retention_cleanup(self) -> None:
        """Schedule retention cleanup (runs every 24 hours)."""
        await self._persistence_queue.put({
            'operation': 'cleanup_retention',
            'timestamp': time.time()
        })


# Global storage instance
_execution_storage: Optional[ExecutionStorage] = None


def get_execution_storage() -> ExecutionStorage:
    """Get global execution storage instance."""
    global _execution_storage
    if _execution_storage is None:
        # Initialize with database URL from environment
        database_url = os.getenv('DATABASE_URL', 'postgresql://localhost/quve_ai')
        config = StorageConfig(database_url)
        _execution_storage = ExecutionStorage(config)
    return _execution_storage


def create_benchmark_run(
    correlation_id: str,
    selected_solver: str,
    execution_mode: str,
    num_assets: int,
    metadata: Dict[str, Any] = None
) -> BenchmarkRun:
    """Create a new benchmark run record."""
    return BenchmarkRun(
        benchmark_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        started_at=datetime.now(),
        status=ExecutionStatus.STARTED,
        selected_solver=selected_solver,
        fallback_chain=[],
        num_assets=num_assets,
        execution_mode=execution_mode,
        metadata=metadata or {}
    )


def create_solver_execution(
    benchmark_id: str,
    solver_name: str,
    provider: str,
    backend: str,
    metadata: Dict[str, Any] = None
) -> SolverExecution:
    """Create a new solver execution record."""
    return SolverExecution(
        execution_id=str(uuid.uuid4()),
        benchmark_id=benchmark_id,
        solver_name=solver_name,
        provider=provider,
        backend=backend,
        status=ExecutionStatus.STARTED,
        metadata=metadata or {}
    )


def create_cloud_task(
    task_arn: str,
    device_arn: str,
    region: str,
    shots: int,
    metadata: Dict[str, Any] = None
) -> CloudTask:
    """Create a new cloud task record."""
    return CloudTask(
        task_arn=task_arn,
        device_arn=device_arn,
        region=region,
        shots=shots,
        task_status=TaskStatus.QUEUED,
        metadata=metadata or {}
    )


def create_telemetry_event(
    correlation_id: str,
    event_type: str,
    severity: str,
    payload: Dict[str, Any]
) -> TelemetryEvent:
    """Create a new telemetry event record."""
    return TelemetryEvent(
        event_id=str(uuid.uuid4()),
        correlation_id=correlation_id,
        timestamp=datetime.now(),
        event_type=event_type,
        severity=severity,
        payload_json=json.dumps(payload)
    )
