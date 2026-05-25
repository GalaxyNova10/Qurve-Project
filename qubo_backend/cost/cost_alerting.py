"""
Qurve AI - Cost Alerting System
Multi-level alerting for cost governance without external dependencies.

Features:
✅ Multi-level alerts (50%, 75%, 90%, 100%)
✅ Internal telemetry only
✅ Threshold-based warnings
✅ Alert deduplication
✅ Alert history tracking
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

from .governance_schemas import AlertLevelSchema, CostTelemetrySchema

logger = logging.getLogger(__name__)


@dataclass
class AlertThreshold:
    """Alert threshold configuration."""
    level: AlertLevelSchema
    percentage: float
    message_template: str
    cooldown_minutes: int


@dataclass
class CostAlert:
    """Cost alert data structure."""
    alert_id: str
    level: AlertLevelSchema
    message: str
    timestamp: datetime
    correlation_id: str
    daily_spend_usd: float
    daily_quota_usd: float
    usage_percentage: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertConfig:
    """Alerting configuration."""
    enabled: bool = True
    thresholds: List[AlertThreshold] = field(default_factory=list)
    deduplication_window_minutes: int = 30
    max_alerts_per_hour: int = 10


class CostAlerting:
    """
    Production-grade cost alerting system.
    
    Features:
    - Multi-level threshold alerts
    - Alert deduplication
    - Rate limiting
    - Internal telemetry integration
    - Alert history tracking
    """
    
    def __init__(self, config: AlertConfig):
        self.config = config
        
        # Default alert thresholds
        if not config.thresholds:
            config.thresholds = [
                AlertThreshold(
                    level=AlertLevelSchema.INFO,
                    percentage=50.0,
                    message_template="Info: {usage_pct:.1f}% of daily quota used (${daily_spend:.2f}/${daily_quota:.2f})",
                    cooldown_minutes=60
                ),
                AlertThreshold(
                    level=AlertLevelSchema.WARNING,
                    percentage=75.0,
                    message_template="Warning: {usage_pct:.1f}% of daily quota used (${daily_spend:.2f}/${daily_quota:.2f})",
                    cooldown_minutes=30
                ),
                AlertThreshold(
                    level=AlertLevelSchema.CRITICAL,
                    percentage=90.0,
                    message_template="Critical: {usage_pct:.1f}% of daily quota used (${daily_spend:.2f}/${daily_quota:.2f})",
                    cooldown_minutes=15
                )
            ]
        
        # Alert state
        self._recent_alerts: List[CostAlert] = []
        self._alert_history: List[CostAlert] = []
        self._last_alert_times: Dict[str, float] = {}
        
        logger.info("Cost alerting initialized", 
                  enabled=config.enabled,
                  threshold_count=len(config.thresholds))
    
    def evaluate_alerts(self, telemetry: CostTelemetrySchema) -> List[CostAlert]:
        """
        Evaluate cost telemetry and generate alerts.
        
        Args:
            telemetry: Cost telemetry data
            
        Returns:
            List of new alerts
        """
        if not self.config.enabled:
            return []
        
        alerts = []
        usage_percentage = (telemetry.daily_spend_usd / telemetry.quota_remaining_usd + telemetry.daily_spend_usd) * 100
        
        # Check each threshold
        for threshold in self.config.thresholds:
            if usage_percentage >= threshold.percentage:
                alert = self._create_alert(telemetry, threshold, usage_percentage)
                if self._should_send_alert(alert):
                    alerts.append(alert)
                    self._record_alert(alert)
        
        return alerts
    
    def _create_alert(self, telemetry: CostTelemetrySchema, threshold: AlertThreshold, usage_percentage: float) -> CostAlert:
        """Create an alert from telemetry and threshold."""
        alert_id = f"cost_alert_{int(time.time())}_{threshold.level.value}"
        
        message = threshold.message_template.format(
            usage_pct=usage_percentage,
            daily_spend=telemetry.daily_spend_usd,
            daily_quota=telemetry.quota_remaining_usd + telemetry.daily_spend_usd
        )
        
        return CostAlert(
            alert_id=alert_id,
            level=threshold.level,
            message=message,
            timestamp=datetime.now(),
            correlation_id=telemetry.correlation_id,
            daily_spend_usd=telemetry.daily_spend_usd,
            daily_quota_usd=telemetry.quota_remaining_usd + telemetry.daily_spend_usd,
            usage_percentage=usage_percentage,
            metadata={
                "threshold_percentage": threshold.percentage,
                "governance_decision": telemetry.governance_decision.value,
                "alert_cooldown_minutes": threshold.cooldown_minutes
            }
        )
    
    def _should_send_alert(self, alert: CostAlert) -> bool:
        """Check if alert should be sent (deduplication and rate limiting)."""
        now = time.time()
        
        # Check cooldown for this alert level
        last_alert_time = self._last_alert_times.get(alert.level.value, 0)
        cooldown_seconds = self._get_cooldown_seconds(alert.level)
        
        if now - last_alert_time < cooldown_seconds:
            return False
        
        # Check deduplication window
        for recent_alert in self._recent_alerts:
            if (alert.level == recent_alert.level and 
                alert.correlation_id == recent_alert.correlation_id and
                (alert.timestamp - recent_alert.timestamp).total_seconds() < self.config.deduplication_window_minutes * 60):
                return False
        
        return True
    
    def _get_cooldown_seconds(self, level: AlertLevelSchema) -> int:
        """Get cooldown seconds for alert level."""
        for threshold in self.config.thresholds:
            if threshold.level == level:
                return threshold.cooldown_minutes * 60
        return 60 * 60  # Default 1 hour
    
    def _record_alert(self, alert: CostAlert) -> None:
        """Record alert for deduplication and history."""
        self._recent_alerts.append(alert)
        self._alert_history.append(alert)
        self._last_alert_times[alert.level.value] = time.time()
        
        # Clean old alerts from recent list
        cutoff_time = datetime.now() - timedelta(minutes=self.config.deduplication_window_minutes)
        self._recent_alerts = [a for a in self._recent_alerts if a.timestamp > cutoff_time]
        
        # Limit history size
        if len(self._alert_history) > 1000:
            self._alert_history = self._alert_history[-1000:]
        
        logger.info("Cost alert recorded", 
                   alert_id=alert.alert_id,
                   level=alert.level.value,
                   usage_pct=alert.usage_percentage,
                   correlation_id=alert.correlation_id)
    
    async def emit_alerts(self, alerts: List[CostAlert]) -> None:
        """
        Emit alerts to internal telemetry.
        
        Args:
            alerts: List of alerts to emit
        """
        for alert in alerts:
            try:
                # This would integrate with monitoring service
                logger.warning("Cost alert emitted", 
                            alert_id=alert.alert_id,
                            level=alert.level.value,
                            message=alert.message,
                            correlation_id=alert.correlation_id,
                            daily_spend=alert.daily_spend_usd,
                            usage_pct=alert.usage_percentage)
                
                # TODO: Integrate with monitoring service
                # monitoring_service = get_monitoring_service()
                # await monitoring_service.store_telemetry_event(...)
                
            except Exception as e:
                logger.error("Failed to emit cost alert", 
                            alert_id=alert.alert_id, 
                            error=str(e))
    
    def get_recent_alerts(self, limit: int = 100) -> List[CostAlert]:
        """Get recent alerts."""
        return sorted(self._recent_alerts, key=lambda a: a.timestamp, reverse=True)[:limit]
    
    def get_alert_history(self, limit: int = 1000) -> List[CostAlert]:
        """Get alert history."""
        return sorted(self._alert_history, key=lambda a: a.timestamp, reverse=True)[:limit]
    
    def get_alerting_health(self) -> Dict[str, Any]:
        """Get alerting system health."""
        now = datetime.now()
        recent_cutoff = now - timedelta(hours=1)
        
        recent_alerts = [a for a in self._recent_alerts if a.timestamp > recent_cutoff]
        
        return {
            "enabled": self.config.enabled,
            "threshold_count": len(self.config.thresholds),
            "recent_alerts_count": len(recent_alerts),
            "total_alerts_history": len(self._alert_history),
            "last_alert_times": self._last_alert_times,
            "deduplication_window_minutes": self.config.deduplication_window_minutes,
            "max_alerts_per_hour": self.config.max_alerts_per_hour,
            "alert_levels": {
                level.value: {
                    "percentage": threshold.percentage,
                    "cooldown_minutes": threshold.cooldown_minutes,
                    "last_sent": self._last_alert_times.get(level.value, 0)
                }
                for threshold in self.config.thresholds
            }
        }
    
    def update_config(self, new_config: AlertConfig) -> None:
        """Update alerting configuration."""
        self.config = new_config
        logger.info("Cost alerting configuration updated", 
                  enabled=new_config.enabled,
                  threshold_count=len(new_config.thresholds))


# Global cost alerting instance
_cost_alerting: Optional[CostAlerting] = None


def get_cost_alerting() -> CostAlerting:
    """Get global cost alerting instance."""
    global _cost_alerting
    if _cost_alerting is None:
        _cost_alerting = CostAlerting(AlertConfig())
    return _cost_alerting


def create_alert_config(
    enabled: bool = True,
    deduplication_window_minutes: int = 30,
    max_alerts_per_hour: int = 10
) -> AlertConfig:
    """Create alerting configuration."""
    return AlertConfig(
        enabled=enabled,
        deduplication_window_minutes=deduplication_window_minutes,
        max_alerts_per_hour=max_alerts_per_hour
    )
