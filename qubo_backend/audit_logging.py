"""
Data Governance & Audit Logging for QUBO Portfolio Optimizer
Implements institutional-grade traceability and structured logging.
Tracks solver decisions, fallback transitions, optimization parameters,
API access history, benchmark modifications, and model versioning.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
import hashlib
import threading

from .config import get_settings
from .security import mask_secrets

logger = logging.getLogger(__name__)


@dataclass
class AuditEvent:
    """Structured audit event for institutional traceability."""
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    event_type: str = ""
    category: str = ""
    severity: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    
    # Event-specific data
    actor: str = ""  # Service, user, system
    action: str = ""
    resource: str = ""  # solver, model, job, API endpoint
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Outcome
    success: bool = True
    error_message: Optional[str] = None
    error_code: Optional[str] = None
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    request_id: Optional[str] = None
    
    # Compliance
    retention_days: int = 365
    compliance_tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data


class AuditLogger:
    """
    Institutional-grade audit logging system.
    
    Features:
    - Structured logging for regulatory compliance
    - Solver decision and fallback transition tracking
    - Optimization parameter and API access logging
    - Benchmark modification and model versioning
    - Secure log storage and rotation
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.audit_dir = self.settings.output_dir / "audit"
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        
        # Log files
        self.current_log_file = self.audit_dir / f"audit_{datetime.now().strftime('%Y%m%d')}.jsonl"
        self.index_file = self.audit_dir / "audit_index.json"
        
        # In-memory buffer for performance
        self._buffer: List[AuditEvent] = []
        self._buffer_size = 100
        self._lock = threading.Lock()
        
        # Load existing index
        self._load_index()
        
        # Setup structured logging
        self._setup_structured_logger()
    
    def _load_index(self) -> None:
        """Load existing audit index."""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r') as f:
                    self._audit_index = json.load(f)
            else:
                self._audit_index = {
                    "created_at": datetime.now().isoformat(),
                    "total_events": 0,
                    "categories": {},
                    "event_types": {}
                }
        except Exception as e:
            logger.error(f"Failed to load audit index: {e}")
            self._audit_index = {
                "created_at": datetime.now().isoformat(),
                "total_events": 0,
                "categories": {},
                "event_types": {}
            }
    
    def _setup_structured_logger(self) -> None:
        """Setup structured audit logger."""
        self.audit_logger = logging.getLogger("qubo_audit")
        self.audit_logger.setLevel(logging.INFO)
        
        # Create handler for audit events
        handler = logging.FileHandler(self.audit_dir / "audit.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)
    
    def log_solver_decision(self, 
                          solver_name: str,
                          problem_params: Dict[str, Any],
                          decision_reason: str,
                          alternatives_considered: List[str],
                          user_id: Optional[str] = None,
                          session_id: Optional[str] = None) -> str:
        """
        Log solver selection decision.
        
        Args:
            solver_name: Selected solver name
            problem_params: Problem parameters
            decision_reason: Reason for selection
            alternatives_considered: Other solvers considered
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type="solver_decision",
            category="solver_management",
            actor="system",
            action="select_solver",
            resource=f"solver:{solver_name}",
            details={
                "selected_solver": solver_name,
                "problem_params": self._sanitize_params(problem_params),
                "decision_reason": decision_reason,
                "alternatives_considered": alternatives_considered,
                "selection_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            session_id=session_id,
            compliance_tags=["solver_selection", "optimization"]
        )
        
        return self._log_event(event)
    
    def log_fallback_transition(self,
                                from_solver: str,
                                to_solver: str,
                                fallback_reason: str,
                                error_context: Optional[Dict[str, Any]] = None,
                                user_id: Optional[str] = None) -> str:
        """
        Log solver fallback transition.
        
        Args:
            from_solver: Original solver that failed
            to_solver: Fallback solver
            fallback_reason: Reason for fallback
            error_context: Error details that triggered fallback
            user_id: User identifier
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type="solver_fallback",
            category="solver_management",
            actor="system",
            action="fallback_transition",
            resource=f"transition:{from_solver}_to_{to_solver}",
            details={
                "from_solver": from_solver,
                "to_solver": to_solver,
                "fallback_reason": fallback_reason,
                "error_context": error_context or {},
                "transition_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            severity="WARNING" if error_context else "INFO",
            compliance_tags=["fallback", "resilience"]
        )
        
        return self._log_event(event)
    
    def log_optimization_parameters(self,
                                  job_id: str,
                                  solver_name: str,
                                  parameters: Dict[str, Any],
                                  user_id: Optional[str] = None,
                                  session_id: Optional[str] = None) -> str:
        """
        Log optimization parameters for audit trail.
        
        Args:
            job_id: Optimization job identifier
            solver_name: Solver used
            parameters: Optimization parameters
            user_id: User identifier
            session_id: Session identifier
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type="optimization_parameters",
            category="optimization",
            actor="user",
            action="configure_optimization",
            resource=f"job:{job_id}",
            details={
                "job_id": job_id,
                "solver_name": solver_name,
                "parameters": self._sanitize_params(parameters),
                "configuration_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            session_id=session_id,
            correlation_id=job_id,
            compliance_tags=["optimization", "parameter_logging"]
        )
        
        return self._log_event(event)
    
    def log_api_access(self,
                      endpoint: str,
                      method: str,
                      user_id: Optional[str] = None,
                      ip_address: Optional[str] = None,
                      user_agent: Optional[str] = None,
                      request_id: Optional[str] = None,
                      response_status: Optional[int] = None,
                      response_time_ms: Optional[float] = None) -> str:
        """
        Log API access for security audit.
        
        Args:
            endpoint: API endpoint accessed
            method: HTTP method
            user_id: User identifier
            ip_address: Client IP address
            user_agent: Client user agent
            request_id: Request identifier
            response_status: HTTP response status
            response_time_ms: Response time in milliseconds
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type="api_access",
            category="security",
            actor="user",
            action=f"{method} {endpoint}",
            resource=f"endpoint:{endpoint}",
            details={
                "endpoint": endpoint,
                "method": method,
                "response_status": response_status,
                "response_time_ms": response_time_ms,
                "access_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            severity="WARNING" if (response_status and response_status >= 400) else "INFO",
            compliance_tags=["api_access", "security"]
        )
        
        return self._log_event(event)
    
    def log_benchmark_modification(self,
                                  benchmark_id: str,
                                  modification_type: str,
                                  old_values: Optional[Dict[str, Any]] = None,
                                  new_values: Optional[Dict[str, Any]] = None,
                                  user_id: Optional[str] = None,
                                  reason: Optional[str] = None) -> str:
        """
        Log benchmark modifications for change tracking.
        
        Args:
            benchmark_id: Benchmark identifier
            modification_type: Type of modification
            old_values: Previous values
            new_values: New values
            user_id: User identifier
            reason: Reason for modification
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type="benchmark_modification",
            category="benchmark_management",
            actor="user",
            action=modification_type,
            resource=f"benchmark:{benchmark_id}",
            details={
                "benchmark_id": benchmark_id,
                "modification_type": modification_type,
                "old_values": old_values,
                "new_values": new_values,
                "reason": reason,
                "modification_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            compliance_tags=["benchmark", "change_tracking"]
        )
        
        return self._log_event(event)
    
    def log_model_versioning(self,
                            model_name: str,
                            version: str,
                            action: str,  # created, updated, deployed, rolled_back
                            previous_version: Optional[str] = None,
                            training_dataset: Optional[str] = None,
                            performance_metrics: Optional[Dict[str, Any]] = None,
                            user_id: Optional[str] = None) -> str:
        """
        Log model versioning for ML lifecycle tracking.
        
        Args:
            model_name: Name of the model
            version: Model version
            action: Versioning action
            previous_version: Previous version
            training_dataset: Training dataset identifier
            performance_metrics: Model performance metrics
            user_id: User identifier
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type="model_versioning",
            category="model_management",
            actor="user",
            action=action,
            resource=f"model:{model_name}",
            details={
                "model_name": model_name,
                "version": version,
                "previous_version": previous_version,
                "training_dataset": training_dataset,
                "performance_metrics": performance_metrics,
                "versioning_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            compliance_tags=["model_versioning", "ml_lifecycle"]
        )
        
        return self._log_event(event)
    
    def log_security_event(self,
                         event_type: str,
                         severity: str,
                         description: str,
                         user_id: Optional[str] = None,
                         ip_address: Optional[str] = None,
                         details: Optional[Dict[str, Any]] = None) -> str:
        """
        Log security-related events.
        
        Args:
            event_type: Type of security event
            severity: Event severity
            description: Event description
            user_id: User identifier
            ip_address: Client IP address
            details: Additional event details
            
        Returns:
            Event ID for reference
        """
        event = AuditEvent(
            event_type=event_type,
            category="security",
            actor="system",
            action=event_type,
            resource="security_system",
            details={
                "description": description,
                "security_details": details or {},
                "security_timestamp": datetime.now().isoformat()
            },
            user_id=user_id,
            ip_address=ip_address,
            severity=severity,
            compliance_tags=["security", "compliance"]
        )
        
        return self._log_event(event)
    
    def _log_event(self, event: AuditEvent) -> str:
        """Log an audit event."""
        with self._lock:
            self._buffer.append(event)
            
            # Flush buffer if needed
            if len(self._buffer) >= self._buffer_size:
                self._flush_buffer()
        
        # Update index
        self._update_index(event)
        
        # Log to structured logger
        log_message = f"{event.event_type}: {event.action} on {event.resource}"
        if event.user_id:
            log_message += f" by user {event.user_id}"
        
        self.audit_logger.log(
            getattr(logging, event.severity),
            log_message,
            extra={"event_id": event.event_id}
        )
        
        return event.event_id
    
    def _flush_buffer(self) -> None:
        """Flush audit buffer to disk."""
        if not self._buffer:
            return
        
        try:
            # Ensure log file exists and is writable
            if not self.current_log_file.exists():
                self.current_log_file.touch()
            
            with open(self.current_log_file, 'a') as f:
                for event in self._buffer:
                    event_data = event.to_dict()
                    # Mask sensitive data
                    event_data = self._mask_sensitive_data(event_data)
                    f.write(json.dumps(event_data) + '\n')
            
            self._buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush audit buffer: {e}")
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Mask sensitive data in audit logs."""
        # Deep copy to avoid modifying original
        masked_data = json.loads(json.dumps(data))
        
        # Mask common sensitive fields
        sensitive_fields = [
            'token', 'password', 'api_key', 'secret', 'credential',
            'authorization', 'auth', 'key'
        ]
        
        def mask_recursive(obj):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if any(sensitive in key.lower() for sensitive in sensitive_fields):
                        obj[key] = '[MASKED]'
                    else:
                        obj[key] = mask_recursive(value)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    obj[i] = mask_recursive(item)
            return obj
        
        return mask_recursive(masked_data)
    
    def _sanitize_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize parameters for audit logging."""
        sanitized = {}
        
        for key, value in params.items():
            # Remove sensitive parameters
            if any(sensitive in key.lower() for sensitive in ['token', 'password', 'secret', 'key']):
                sanitized[key] = '[REDACTED]'
            else:
                # Limit size of large parameters
                if isinstance(value, (list, dict)):
                    if len(str(value)) > 1000:
                        sanitized[key] = f"[TRUNCATED: {type(value).__name__}]"
                    else:
                        sanitized[key] = value
                else:
                    sanitized[key] = value
        
        return sanitized
    
    def _update_index(self, event: AuditEvent) -> None:
        """Update audit index statistics."""
        # Update category counts
        if event.category not in self._audit_index["categories"]:
            self._audit_index["categories"][event.category] = 0
        self._audit_index["categories"][event.category] += 1
        
        # Update event type counts
        if event.event_type not in self._audit_index["event_types"]:
            self._audit_index["event_types"][event.event_type] = 0
        self._audit_index["event_types"][event.event_type] += 1
        
        # Update total events
        self._audit_index["total_events"] += 1
        
        # Save index periodically
        if self._audit_index["total_events"] % 100 == 0:
            self._save_index()
    
    def _save_index(self) -> None:
        """Save audit index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(self._audit_index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save audit index: {e}")
    
    async def query_audit_events(self,
                               event_type: Optional[str] = None,
                               category: Optional[str] = None,
                               user_id: Optional[str] = None,
                               start_time: Optional[datetime] = None,
                               end_time: Optional[datetime] = None,
                               limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Query audit events with filtering.
        
        Args:
            event_type: Filter by event type
            category: Filter by category
            user_id: Filter by user ID
            start_time: Filter events from this time
            end_time: Filter events until this time
            limit: Maximum number of events to return
            
        Returns:
            List of matching audit events
        """
        events = []
        
        # Read from log files (simplified for this example)
        current_date = datetime.now()
        
        # Check last 7 days of log files
        for days_ago in range(7):
            log_date = current_date - timedelta(days=days_ago)
            log_file = self.audit_dir / f"audit_{log_date.strftime('%Y%m%d')}.jsonl"
            
            if not log_file.exists():
                continue
            
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        if not line.strip():
                            continue
                        
                        try:
                            event_data = json.loads(line)
                            
                            # Apply filters
                            if event_type and event_data.get('event_type') != event_type:
                                continue
                            
                            if category and event_data.get('category') != category:
                                continue
                            
                            if user_id and event_data.get('user_id') != user_id:
                                continue
                            
                            event_time = datetime.fromisoformat(event_data['timestamp'])
                            
                            if start_time and event_time < start_time:
                                continue
                            
                            if end_time and event_time > end_time:
                                continue
                            
                            events.append(event_data)
                            
                            if len(events) >= limit:
                                return events
                                
                        except json.JSONDecodeError:
                            continue
                            
            except Exception as e:
                logger.error(f"Error reading audit log {log_file}: {e}")
        
        return events
    
    async def get_audit_statistics(self) -> Dict[str, Any]:
        """Get audit logging statistics."""
        return {
            "index": self._audit_index,
            "current_log_file": str(self.current_log_file),
            "buffer_size": len(self._buffer),
            "audit_directory": str(self.audit_dir),
            "log_retention_days": 365
        }
    
    async def cleanup_old_logs(self, days_to_keep: int = 365) -> int:
        """Clean up old audit logs."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_files = 0
        
        for log_file in self.audit_dir.glob("audit_*.jsonl"):
            try:
                # Extract date from filename
                file_date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(file_date_str, "%Y%m%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    cleaned_files += 1
                    logger.info(f"Cleaned up old audit log: {log_file}")
                    
            except Exception as e:
                logger.error(f"Error cleaning up audit log {log_file}: {e}")
        
        return cleaned_files
    
    def flush(self) -> None:
        """Force flush audit buffer to disk."""
        with self._lock:
            self._flush_buffer()


# Global audit logger instance
AUDIT_LOGGER = AuditLogger()
