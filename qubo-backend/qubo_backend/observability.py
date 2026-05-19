"""
Observability Stack for QUBO Portfolio Optimizer
Implements enterprise monitoring with distributed tracing and metrics.
Provides real-time alerting, dashboard integration, and system health monitoring.
"""

import asyncio
import logging
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from collections import defaultdict, deque
import threading

from .config import get_settings
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of metrics."""
    
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""
    
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Metric data structure."""
    
    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: Optional[str] = None
    description: str = ""


@dataclass
class Trace:
    """Distributed trace data structure."""
    
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    operation_name: str
    service_name: str
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_ms: Optional[float] = None
    status: str = "ok"  # ok, error, timeout
    tags: Dict[str, str] = field(default_factory=dict)
    logs: List[Dict[str, Any]] = field(default_factory=list)
    
    def finish(self, status: str = "ok") -> None:
        """Finish the trace span."""
        self.end_time = datetime.now()
        self.duration_ms = (self.end_time - self.start_time).total_seconds() * 1000
        self.status = status


@dataclass
class Alert:
    """Alert data structure."""
    
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    service: Optional[str] = None
    metric_name: Optional[str] = None
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    labels: Dict[str, str] = field(default_factory=dict)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MetricsCollector:
    """Collects and manages metrics."""
    
    def __init__(self, max_metrics: int = 10000):
        self.max_metrics = max_metrics
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Dict[str, str] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            
            metric = Metric(
                name=name,
                metric_type=MetricType.COUNTER,
                value=self._counters[key],
                labels=labels or {}
            )
            self._add_metric(key, metric)
    
    def set_gauge(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Set a gauge metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            
            metric = Metric(
                name=name,
                metric_type=MetricType.GAUGE,
                value=value,
                labels=labels or {}
            )
            self._add_metric(key, metric)
    
    def record_histogram(self, name: str, value: float, labels: Dict[str, str] = None) -> None:
        """Record a histogram metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)
            
            # Keep only last 1000 values per histogram
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]
            
            metric = Metric(
                name=name,
                metric_type=MetricType.HISTOGRAM,
                value=value,
                labels=labels or {}
            )
            self._add_metric(key, metric)
    
    def record_timer(self, name: str, duration_ms: float, labels: Dict[str, str] = None) -> None:
        """Record a timer metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(duration_ms)
            
            metric = Metric(
                name=name,
                metric_type=MetricType.TIMER,
                value=duration_ms,
                labels=labels or {},
                unit="ms"
            )
            self._add_metric(key, metric)
    
    def _make_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        
        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}[{label_str}]"
    
    def _add_metric(self, key: str, metric: Metric) -> None:
        """Add metric to storage."""
        self._metrics[key].append(metric)
    
    def get_metrics(self, name: Optional[str] = None, since: Optional[datetime] = None) -> List[Metric]:
        """Get metrics with optional filtering."""
        with self._lock:
            all_metrics = []
            
            for key, metric_deque in self._metrics.items():
                for metric in metric_deque:
                    if name and not metric.name.startswith(name):
                        continue
                    
                    if since and metric.timestamp < since:
                        continue
                    
                    all_metrics.append(metric)
            
            return sorted(all_metrics, key=lambda m: m.timestamp, reverse=True)
    
    def get_metric_summary(self, name: str, since: Optional[datetime] = None) -> Dict[str, Any]:
        """Get summary statistics for a metric."""
        metrics = self.get_metrics(name, since)
        
        if not metrics:
            return {}
        
        values = [m.value for m in metrics]
        
        return {
            "name": name,
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values),
            "latest": metrics[0].value if metrics else None,
            "timestamp_range": {
                "start": min(m.timestamp for m in metrics).isoformat(),
                "end": max(m.timestamp for m in metrics).isoformat()
            }
        }


class TraceManager:
    """Manages distributed tracing."""
    
    def __init__(self, max_traces: int = 5000):
        self.max_traces = max_traces
        self._active_traces: Dict[str, Trace] = {}
        self._completed_traces: deque = deque(maxlen=max_traces)
        self._lock = threading.Lock()
    
    def start_trace(self, 
                   operation_name: str,
                   service_name: str,
                   parent_span_id: Optional[str] = None,
                   tags: Dict[str, str] = None) -> Trace:
        """Start a new trace span."""
        trace = Trace(
            trace_id=str(uuid.uuid4()),
            span_id=str(uuid.uuid4()),
            parent_span_id=parent_span_id,
            operation_name=operation_name,
            service_name=service_name,
            tags=tags or {}
        )
        
        with self._lock:
            self._active_traces[trace.span_id] = trace
        
        return trace
    
    def finish_trace(self, span_id: str, status: str = "ok") -> Optional[Trace]:
        """Finish a trace span."""
        with self._lock:
            trace = self._active_traces.pop(span_id, None)
            if trace:
                trace.finish(status)
                self._completed_traces.append(trace)
        
        return trace
    
    def add_log(self, span_id: str, log_data: Dict[str, Any]) -> None:
        """Add log entry to active trace."""
        with self._lock:
            trace = self._active_traces.get(span_id)
            if trace:
                trace.logs.append(log_data)
    
    def get_traces(self, 
                   service_name: Optional[str] = None,
                   operation_name: Optional[str] = None,
                   since: Optional[datetime] = None,
                   limit: int = 100) -> List[Trace]:
        """Get completed traces with filtering."""
        with self._lock:
            traces = list(self._completed_traces)
        
        # Apply filters
        if service_name:
            traces = [t for t in traces if t.service_name == service_name]
        
        if operation_name:
            traces = [t for t in traces if t.operation_name == operation_name]
        
        if since:
            traces = [t for t in traces if t.start_time >= since]
        
        # Sort by start time and limit
        traces.sort(key=lambda t: t.start_time, reverse=True)
        return traces[:limit]
    
    def get_trace_by_id(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID."""
        with self._lock:
            # Check active traces first
            for trace in self._active_traces.values():
                if trace.trace_id == trace_id:
                    return trace
            
            # Check completed traces
            for trace in self._completed_traces:
                if trace.trace_id == trace_id:
                    return trace
        
        return None


class AlertManager:
    """Manages alerts and alerting rules."""
    
    def __init__(self):
        self._alerts: Dict[str, Alert] = {}
        self._alert_rules: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
        # Setup default alert rules
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default alerting rules."""
        self._alert_rules = [
            {
                "name": "high_error_rate",
                "condition": "error_rate > 5.0",
                "severity": "warning",
                "description": "Error rate exceeds 5%"
            },
            {
                "name": "critical_error_rate",
                "condition": "error_rate > 10.0",
                "severity": "critical",
                "description": "Error rate exceeds 10%"
            },
            {
                "name": "high_response_time",
                "condition": "response_time_p95 > 5000",
                "severity": "warning",
                "description": "95th percentile response time exceeds 5 seconds"
            },
            {
                "name": "critical_response_time",
                "condition": "response_time_p95 > 10000",
                "severity": "critical",
                "description": "95th percentile response time exceeds 10 seconds"
            },
            {
                "name": "memory_usage_high",
                "condition": "memory_usage_percent > 90",
                "severity": "warning",
                "description": "Memory usage exceeds 90%"
            },
            {
                "name": "memory_usage_critical",
                "condition": "memory_usage_percent > 95",
                "severity": "critical",
                "description": "Memory usage exceeds 95%"
            }
        ]
    
    def create_alert(self,
                     name: str,
                     severity: AlertSeverity,
                     message: str,
                     service: Optional[str] = None,
                     metric_name: Optional[str] = None,
                     threshold_value: Optional[float] = None,
                     current_value: Optional[float] = None,
                     labels: Dict[str, str] = None) -> str:
        """Create a new alert."""
        alert = Alert(
            name=name,
            severity=severity,
            message=message,
            service=service,
            metric_name=metric_name,
            threshold_value=threshold_value,
            current_value=current_value,
            labels=labels or {}
        )
        
        with self._lock:
            self._alerts[alert.alert_id] = alert
        
        logger.warning(f"Alert created: {name} - {message}")
        return alert.alert_id
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert."""
        with self._lock:
            alert = self._alerts.get(alert_id)
            if alert and not alert.resolved:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                logger.info(f"Alert resolved: {alert.name}")
                return True
        
        return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """Get active alerts."""
        with self._lock:
            alerts = [a for a in self._alerts.values() if not a.resolved]
            
            if severity:
                alerts = [a for a in alerts if a.severity == severity]
            
            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_all_alerts(self, hours: int = 24) -> List[Alert]:
        """Get all alerts from last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            alerts = [
                a for a in self._alerts.values()
                if a.timestamp >= cutoff_time
            ]
        
        return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def evaluate_rules(self, metrics_summary: Dict[str, Any]) -> List[Alert]:
        """Evaluate alerting rules against metrics."""
        new_alerts = []
        
        for rule in self._alert_rules:
            try:
                if self._evaluate_condition(rule["condition"], metrics_summary):
                    # Check if alert already exists
                    existing_alert = None
                    for alert in self.get_active_alerts():
                        if alert.name == rule["name"]:
                            existing_alert = alert
                            break
                    
                    if not existing_alert:
                        alert_id = self.create_alert(
                            name=rule["name"],
                            severity=AlertSeverity(rule["severity"]),
                            message=rule["description"],
                            labels={"rule": rule["name"]}
                        )
                        new_alerts.append(alert_id)
                        
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {e}")
        
        return new_alerts
    
    def _evaluate_condition(self, condition: str, metrics: Dict[str, Any]) -> bool:
        """Evaluate a simple condition string."""
        # Simple condition evaluation (in production, use a proper expression parser)
        try:
            # Replace common metric names
            condition = condition.replace("error_rate", str(metrics.get("error_rate", 0)))
            condition = condition.replace("response_time_p95", str(metrics.get("response_time_p95", 0)))
            condition = condition.replace("memory_usage_percent", str(metrics.get("memory_usage_percent", 0)))
            
            # Evaluate the condition
            return eval(condition)
        except:
            return False


class ObservabilityStack:
    """
    Enterprise observability stack.
    
    Features:
    - Real-time metrics collection and aggregation
    - Distributed tracing with span management
    - Alert management with rule evaluation
    - Dashboard integration support
    - System health monitoring
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.metrics_collector = MetricsCollector()
        self.trace_manager = TraceManager()
        self.alert_manager = AlertManager()
        
        # Start background tasks
        self._running = False
        self._alert_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Start monitoring
        self.start()
    
    def start(self) -> None:
        """Start observability stack."""
        if self._running:
            return
        
        self._running = True
        
        # Start background tasks
        loop = asyncio.get_event_loop()
        self._alert_task = loop.create_task(self._alert_evaluation_loop())
        self._cleanup_task = loop.create_task(self._cleanup_loop())
        
        logger.info("Observability stack started")
    
    def stop(self) -> None:
        """Stop observability stack."""
        self._running = False
        
        if self._alert_task:
            self._alert_task.cancel()
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
        
        logger.info("Observability stack stopped")
    
    async def _alert_evaluation_loop(self) -> None:
        """Background task for alert evaluation."""
        while self._running:
            try:
                # Get metrics summary
                metrics_summary = self._get_metrics_summary()
                
                # Evaluate alert rules
                self.alert_manager.evaluate_rules(metrics_summary)
                
                await asyncio.sleep(60)  # Evaluate every minute
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(60)
    
    async def _cleanup_loop(self) -> None:
        """Background task for data cleanup."""
        while self._running:
            try:
                # Clean up old data
                cutoff_time = datetime.now() - timedelta(hours=24)
                
                # Clean old metrics (handled by deque maxlen)
                # Clean old traces (handled by deque maxlen)
                # Clean old alerts
                old_alerts = [
                    alert_id for alert_id, alert in self.alert_manager._alerts.items()
                    if alert.timestamp < cutoff_time and alert.resolved
                ]
                
                for alert_id in old_alerts:
                    del self.alert_manager._alerts[alert_id]
                
                if old_alerts:
                    logger.info(f"Cleaned up {len(old_alerts)} old alerts")
                
                await asyncio.sleep(3600)  # Clean every hour
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
                await asyncio.sleep(3600)
    
    def _get_metrics_summary(self) -> Dict[str, Any]:
        """Get current metrics summary for alert evaluation."""
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_metrics(since=datetime.now() - timedelta(minutes=5))
        
        summary = {}
        
        # Calculate error rate
        total_requests = len([m for m in recent_metrics if m.name == "http_requests_total"])
        error_requests = len([m for m in recent_metrics if m.name == "http_errors_total"])
        
        if total_requests > 0:
            summary["error_rate"] = (error_requests / total_requests) * 100
        
        # Calculate response time percentiles
        response_times = [m.value for m in recent_metrics if m.name == "http_request_duration_ms"]
        if response_times:
            response_times.sort()
            p95_index = int(len(response_times) * 0.95)
            summary["response_time_p95"] = response_times[min(p95_index, len(response_times) - 1)]
        
        # Get memory usage
        memory_metrics = [m for m in recent_metrics if m.name == "memory_usage_bytes"]
        if memory_metrics:
            latest_memory = memory_metrics[0].value  # Most recent
            # Assume 8GB total memory (would be dynamic in production)
            total_memory = 8 * 1024 * 1024 * 1024
            summary["memory_usage_percent"] = (latest_memory / total_memory) * 100
        
        return summary
    
    def record_metric(self, 
                     name: str,
                     value: float,
                     metric_type: MetricType = MetricType.GAUGE,
                     labels: Dict[str, str] = None) -> None:
        """Record a metric."""
        if metric_type == MetricType.COUNTER:
            self.metrics_collector.increment_counter(name, value, labels)
        elif metric_type == MetricType.GAUGE:
            self.metrics_collector.set_gauge(name, value, labels)
        elif metric_type == MetricType.HISTOGRAM:
            self.metrics_collector.record_histogram(name, value, labels)
        elif metric_type == MetricType.TIMER:
            self.metrics_collector.record_timer(name, value, labels)
    
    def trace_function(self, 
                      operation_name: str,
                      service_name: str = "qubo_backend"):
        """Decorator to trace function execution."""
        def decorator(func: Callable) -> Callable:
            async def async_wrapper(*args, **kwargs):
                trace = self.trace_manager.start_trace(operation_name, service_name)
                try:
                    result = await func(*args, **kwargs)
                    self.trace_manager.finish_trace(trace.span_id, "ok")
                    return result
                except Exception as e:
                    self.trace_manager.add_log(trace.span_id, {"error": str(e)})
                    self.trace_manager.finish_trace(trace.span_id, "error")
                    raise
            
            def sync_wrapper(*args, **kwargs):
                trace = self.trace_manager.start_trace(operation_name, service_name)
                try:
                    result = func(*args, **kwargs)
                    self.trace_manager.finish_trace(trace.span_id, "ok")
                    return result
                except Exception as e:
                    self.trace_manager.add_log(trace.span_id, {"error": str(e)})
                    self.trace_manager.finish_trace(trace.span_id, "error")
                    raise
            
            import asyncio
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            else:
                return sync_wrapper
        
        return decorator
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard visualization."""
        # Get recent metrics
        recent_metrics = self.metrics_collector.get_metrics(since=datetime.now() - timedelta(hours=1))
        
        # Get active alerts
        active_alerts = self.alert_manager.get_active_alerts()
        
        # Get recent traces
        recent_traces = self.trace_manager.get_traces(limit=50)
        
        return {
            "metrics": {
                "total_metrics": len(recent_metrics),
                "error_rate": self._calculate_error_rate(recent_metrics),
                "avg_response_time": self._calculate_avg_response_time(recent_metrics),
                "memory_usage": self._get_memory_usage(recent_metrics)
            },
            "alerts": {
                "active_count": len(active_alerts),
                "critical_count": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
                "warning_count": len([a for a in active_alerts if a.severity == AlertSeverity.WARNING]),
                "recent_alerts": [
                    {
                        "name": alert.name,
                        "severity": alert.severity.value,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in active_alerts[:10]
                ]
            },
            "traces": {
                "total_traces": len(recent_traces),
                "error_rate": len([t for t in recent_traces if t.status == "error"]) / len(recent_traces) * 100 if recent_traces else 0,
                "avg_duration": sum(t.duration_ms or 0 for t in recent_traces) / len(recent_traces) if recent_traces else 0,
                "recent_traces": [
                    {
                        "operation": t.operation_name,
                        "service": t.service_name,
                        "duration_ms": t.duration_ms,
                        "status": t.status,
                        "timestamp": t.start_time.isoformat()
                    }
                    for t in recent_traces[:20]
                ]
            },
            "system_health": {
                "status": "healthy" if len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]) == 0 else "degraded",
                "timestamp": datetime.now().isoformat()
            }
        }
    
    def _calculate_error_rate(self, metrics: List[Metric]) -> float:
        """Calculate error rate from metrics."""
        requests = [m for m in metrics if m.name == "http_requests_total"]
        errors = [m for m in metrics if m.name == "http_errors_total"]
        
        if not requests:
            return 0.0
        
        total_requests = sum(m.value for m in requests)
        total_errors = sum(m.value for m in errors)
        
        return (total_errors / total_requests) * 100 if total_requests > 0 else 0.0
    
    def _calculate_avg_response_time(self, metrics: List[Metric]) -> float:
        """Calculate average response time from metrics."""
        response_times = [m.value for m in metrics if m.name == "http_request_duration_ms"]
        
        return sum(response_times) / len(response_times) if response_times else 0.0
    
    def _get_memory_usage(self, metrics: List[Metric]) -> float:
        """Get memory usage from metrics."""
        memory_metrics = [m for m in metrics if m.name == "memory_usage_bytes"]
        
        if not memory_metrics:
            return 0.0
        
        # Return most recent memory usage in MB
        return memory_metrics[0].value / (1024 * 1024)
    
    def get_observability_status(self) -> Dict[str, Any]:
        """Get observability stack status."""
        return {
            "running": self._running,
            "metrics_count": len(self.metrics_collector._metrics),
            "active_traces": len(self.trace_manager._active_traces),
            "completed_traces": len(self.trace_manager._completed_traces),
            "active_alerts": len(self.alert_manager.get_active_alerts()),
            "alert_rules": len(self.alert_manager._alert_rules),
            "timestamp": datetime.now().isoformat()
        }


# Global observability stack instance
OBSERVABILITY_STACK = ObservabilityStack()
