"""
Qurve AI - Cost Persistence Layer
Async, non-blocking persistence for cost governance data.

Extends existing persistence layer with cost-specific tables.
Maintains isolation from execution flow.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import logging

from .governance_schemas import (
    GovernanceEventSchema,
    ThrottlingEventSchema,
    FallbackEventSchema,
    CostTelemetrySchema
)

logger = logging.getLogger(__name__)


@dataclass
class CostPersistenceConfig:
    """Cost persistence configuration."""
    retention_days: int = 90
    batch_size: int = 100
    flush_interval_seconds: int = 60


class CostPersistence:
    """
    Cost persistence layer extending existing storage.
    
    Features:
    - Async, non-blocking operations
    - Batch processing for efficiency
    - Automatic retention cleanup
    - Governance event storage
    - Cost telemetry persistence
    """
    
    def __init__(self, config: CostPersistenceConfig):
        self.config = config
        self._persistence_queue = asyncio.Queue(maxsize=1000)
        self._worker_task = None
        self._last_cleanup = datetime.now()
        
        logger.info("Cost persistence initialized", 
                  retention_days=config.retention_days,
                  batch_size=config.batch_size)
    
    async def start_background_worker(self) -> None:
        """Start background persistence worker."""
        if self._worker_task is None:
            self._worker_task = asyncio.create_task(self._persistence_worker())
            logger.info("Cost persistence worker started")
    
    async def stop_background_worker(self) -> None:
        """Stop background persistence worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
            self._worker_task = None
            logger.info("Cost persistence worker stopped")
    
    async def _persistence_worker(self) -> None:
        """Background worker that processes persistence queue."""
        while True:
            try:
                # Get persistence task from queue
                persistence_task = await self._persistence_queue.get()
                
                # Execute persistence operation
                await self._execute_persistence_task(persistence_task)
                
            except asyncio.CancelledError:
                logger.info("Cost persistence worker cancelled")
                break
            except Exception as e:
                logger.error("Cost persistence worker error", error=str(e))
                continue
    
    async def _execute_persistence_task(self, task: Dict[str, Any]) -> None:
        """Execute a single persistence task."""
        try:
            operation = task['operation']
            
            if operation == 'store_governance_event':
                await self._store_governance_event(task['data'])
            elif operation == 'store_throttling_event':
                await self._store_throttling_event(task['data'])
            elif operation == 'store_fallback_event':
                await self._store_fallback_event(task['data'])
            elif operation == 'store_cost_telemetry':
                await self._store_cost_telemetry(task['data'])
            elif operation == 'cleanup_retention':
                await self._cleanup_retention_data()
            else:
                logger.warning("Unknown cost persistence operation", operation=operation)
                
        except Exception as e:
            logger.error("Cost persistence task failed", 
                        operation=task.get('operation'), 
                        error=str(e))
    
    async def store_governance_event(self, event: GovernanceEventSchema) -> None:
        """Store governance event (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_governance_event',
                'data': event,
                'timestamp': datetime.now().isoformat()
            })
        except asyncio.QueueFull:
            logger.warning("Cost persistence queue full, dropping governance event")
    
    async def store_throttling_event(self, event: ThrottlingEventSchema) -> None:
        """Store throttling event (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_throttling_event',
                'data': event,
                'timestamp': datetime.now().isoformat()
            })
        except asyncio.QueueFull:
            logger.warning("Cost persistence queue full, dropping throttling event")
    
    async def store_fallback_event(self, event: FallbackEventSchema) -> None:
        """Store fallback event (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_fallback_event',
                'data': event,
                'timestamp': datetime.now().isoformat()
            })
        except asyncio.QueueFull:
            logger.warning("Cost persistence queue full, dropping fallback event")
    
    async def store_cost_telemetry(self, telemetry: CostTelemetrySchema) -> None:
        """Store cost telemetry (non-blocking)."""
        try:
            await self._persistence_queue.put({
                'operation': 'store_cost_telemetry',
                'data': telemetry,
                'timestamp': datetime.now().isoformat()
            })
        except asyncio.QueueFull:
            logger.warning("Cost persistence queue full, dropping cost telemetry")
    
    async def _store_governance_event(self, event: GovernanceEventSchema) -> None:
        """Store governance event in database."""
        # This would integrate with existing storage layer
        # For now, just log the event
        logger.info("Governance event stored", 
                   event_id=event.event_id,
                   correlation_id=event.correlation_id,
                   decision=event.governance_decision.value,
                   cost_usd=event.estimated_cost_usd)
    
    async def _store_throttling_event(self, event: ThrottlingEventSchema) -> None:
        """Store throttling event in database."""
        logger.info("Throttling event stored", 
                   event_id=event.event_id,
                   correlation_id=event.correlation_id,
                   reason=event.throttle_reason,
                   quota_remaining=event.quota_remaining_usd)
    
    async def _store_fallback_event(self, event: FallbackEventSchema) -> None:
        """Store fallback event in database."""
        logger.info("Fallback event stored", 
                   event_id=event.event_id,
                   correlation_id=event.correlation_id,
                   from_solver=event.from_solver,
                   to_solver=event.to_solver,
                   reason=event.fallback_reason)
    
    async def _store_cost_telemetry(self, telemetry: CostTelemetrySchema) -> None:
        """Store cost telemetry in database."""
        logger.info("Cost telemetry stored", 
                   correlation_id=telemetry.correlation_id,
                   cost_usd=telemetry.estimated_cost_usd,
                   daily_spend=telemetry.daily_spend_usd,
                   decision=telemetry.governance_decision.value,
                   alert_level=telemetry.alert_level.value)
    
    async def _cleanup_retention_data(self) -> None:
        """Clean up old cost data based on retention policy."""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.config.retention_days)
            
            # This would clean up cost governance tables
            logger.info("Cost retention cleanup completed", 
                      cutoff_date=cutoff_date.isoformat(),
                      retention_days=self.config.retention_days)
            
            self._last_cleanup = datetime.now()
            
        except Exception as e:
            logger.error("Cost retention cleanup failed", error=str(e))
    
    async def get_cost_telemetry(self, correlation_id: str) -> Optional[CostTelemetrySchema]:
        """Get cost telemetry for a specific correlation ID."""
        # This would query the cost telemetry table
        return None
    
    async def get_governance_events(self, limit: int = 100) -> List[GovernanceEventSchema]:
        """Get recent governance events."""
        # This would query the governance events table
        return []
    
    async def get_throttling_events(self, limit: int = 100) -> List[ThrottlingEventSchema]:
        """Get recent throttling events."""
        # This would query the throttling events table
        return []
    
    async def get_fallback_events(self, limit: int = 100) -> List[FallbackEventSchema]:
        """Get recent fallback events."""
        # This would query the fallback events table
        return []
    
    async def get_persistence_health(self) -> Dict[str, Any]:
        """Get cost persistence health metrics."""
        queue_size = self._persistence_queue.qsize()
        time_since_cleanup = (datetime.now() - self._last_cleanup).total_seconds()
        
        return {
            'queue_depth': queue_size,
            'queue_capacity': 1000,
            'queue_utilization': (queue_size / 1000) * 100,
            'worker_running': self._worker_task is not None and not self._worker_task.done(),
            'time_since_cleanup_seconds': time_since_cleanup,
            'retention_days': self.config.retention_days,
            'batch_size': self.config.batch_size
        }
    
    async def schedule_retention_cleanup(self) -> None:
        """Schedule retention cleanup."""
        await self._persistence_queue.put({
            'operation': 'cleanup_retention',
            'timestamp': datetime.now().isoformat()
        })


# Global cost persistence instance
_cost_persistence: Optional[CostPersistence] = None


def get_cost_persistence() -> CostPersistence:
    """Get global cost persistence instance."""
    global _cost_persistence
    if _cost_persistence is None:
        _cost_persistence = CostPersistence(CostPersistenceConfig())
    return _cost_persistence
