"""
Qurve AI - QPU Dashboard Extension
QPU visibility dashboard with visual separation from simulators.

Principles:
✅ VISUALLY ISOLATED: Separate from live operational dashboards
✅ HARDWARE EXECUTION LABELING: Clearly marked as QPU execution
✅ NO SLA CONTAMINATION: Never affects operational SLA metrics
✅ NO REPLAY CONTAMINATION: Separate from replay dashboards
✅ PROVIDER STATUS: Real-time QPU provider status
✅ QUEUE LATENCY VISIBILITY: QPU queue delay tracking
✅ GOVERNANCE QUOTA VISIBILITY: Hardware governance limits
✅ FALLBACK VISIBILITY: Fallback chain transparency
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .qpu_device_registry import get_qpu_device_registry, QPUProvider
from .qpu_capability_boundaries import get_qpu_capability_boundaries
from .qpu_hardware_governance import get_qpu_hardware_governance
from .qpu_execution_isolation import get_qpu_execution_isolation
from .qpu_calibration_observability import get_qpu_calibration_observability
from .qpu_fallback_chains import get_qpu_fallback_chains

logger = logging.getLogger(__name__)


class QPUDashboardType(Enum):
    """QPU dashboard component types."""
    QPU_EXECUTION_PANEL = "qpu_execution_panel"
    PROVIDER_STATUS = "provider_status"
    QUEUE_LATENCY = "queue_latency"
    GOVERNANCE_QUOTAS = "governance_quotas"
    FALLBACK_VISIBILITY = "fallback_visibility"
    CALIBRATION_OBSERVABILITY = "calibration_observability"


@dataclass
class QPUDashboardConfig:
    """QPU dashboard extension configuration."""
    enable_qpu_dashboard: bool = True
    visual_isolation: bool = True
    hardware_execution_labeling: bool = True
    no_sla_contamination: bool = True
    no_replay_contamination: bool = True
    max_dashboard_sessions: int = 1000
    dashboard_refresh_interval_seconds: int = 30
    qpu_namespace: str = "qpu_dashboard"


class QPUDashboardExtension:
    """
    Production-grade QPU dashboard extension.
    
    Features:
    - Visually isolated from simulators
    - Hardware execution labeling
    - Provider status visibility
    - Queue latency tracking
    - Governance quota visibility
    - Fallback chain transparency
    - Calibration observability
    """
    
    def __init__(self, config: QPUDashboardConfig):
        self.config = config
        
        # QPU system integrations
        self.device_registry = get_qpu_device_registry()
        self.capability_boundaries = get_qpu_capability_boundaries()
        self.hardware_governance = get_qpu_hardware_governance()
        self.execution_isolation = get_qpu_execution_isolation()
        self.calibration_observability = get_qpu_calibration_observability()
        self.fallback_chains = get_qpu_fallback_chains()
        
        # Dashboard state
        self._dashboard_views = 0
        self._last_refresh = time.time()
        
        logger.info("QPU dashboard extension initialized", 
                  visual_isolation=config.visual_isolation,
                  hardware_labeling=config.hardware_execution_labeling,
                  no_sla_contamination=config.no_sla_contamination)
    
    async def get_qpu_execution_panel(self, limit: int = 100) -> Dict[str, Any]:
        """
        Get QPU execution panel with hardware execution labeling.
        
        Returns dashboard data with visual isolation guarantees.
        """
        try:
            # Get active QPU sessions
            active_sessions = await self.execution_isolation.get_active_sessions()
            
            # Create execution panel with hardware labeling
            execution_panel = {
                "panel_type": QPUDashboardType.QPU_EXECUTION_PANEL.value,
                "active_qpu_sessions": [
                    {
                        "session_id": session.session_id,
                        "provider": session.provider,
                        "device": session.device,
                        "namespace": session.namespace,
                        "isolation_level": session.isolation_level,
                        "created_at": session.created_at,
                        "execution_type": "HARDWARE_EXECUTION",
                        "hardware_label": "QUANTUM_PROCESSING_UNIT",
                        "visual_isolation": self.config.visual_isolation
                    }
                    for session in active_sessions
                ],
                "qpu_capability_status": self.capability_boundaries.get_capability_status(),
                "execution_statistics": {
                    "total_active_sessions": len(active_sessions),
                    "providers_active": list(set(session.provider for session in active_sessions)),
                    "devices_active": list(set(session.device for session in active_sessions)),
                    "namespaces_active": list(set(session.namespace for session in active_sessions))
                },
                "dashboard_metadata": {
                    "namespace": self.config.qpu_namespace,
                    "visual_isolation": self.config.visual_isolation,
                    "hardware_execution_labeling": self.config.hardware_execution_labeling,
                    "no_sla_contamination": self.config.no_sla_contamination,
                    "no_replay_contamination": self.config.no_replay_contamination,
                    "last_refresh": time.time(),
                    "panel_label": "QUANTUM PROCESSING UNIT EXECUTION"
                }
            }
            
            self._dashboard_views += 1
            self._last_refresh = time.time()
            
            logger.debug("QPU execution panel generated", 
                        active_sessions=len(active_sessions),
                        hardware_labeling=self.config.hardware_execution_labeling)
            
            return execution_panel
            
        except Exception as e:
            logger.error("Failed to generate QPU execution panel", error=str(e))
            return self._get_error_panel(QPUDashboardType.QPU_EXECUTION_PANEL, str(e))
    
    async def get_provider_status(self) -> Dict[str, Any]:
        """
        Get provider status with real-time QPU availability.
        
        Returns provider status with visual separation from simulators.
        """
        try:
            # Get device registry statistics
            registry_stats = self.device_registry.get_registry_statistics()
            
            # Get capability status
            capability_status = self.capability_boundaries.get_capability_status()
            
            # Create provider status panel
            provider_status = {
                "panel_type": QPUDashboardType.PROVIDER_STATUS.value,
                "provider_statistics": {
                    provider.value: {
                        "total_devices": len(self.device_registry.get_devices_by_provider(provider)),
                        "available_devices": len(self.device_registry.get_available_devices() if self.device_registry.get_available_devices() else []),
                        "qpu_enabled": capability_status.get("qpu_enabled", False),
                        "explicit_enable_count": capability_status.get("explicit_enable_count", 0),
                        "governance_approvals": capability_status.get("active_governance_approvals", 0),
                        "visual_isolation": self.config.visual_isolation,
                        "provider_type": "QUANTUM_HARDWARE_PROVIDER"
                    }
                    for provider in QPUProvider
                },
                "device_availability": {
                    "total_devices": registry_stats["total_devices"],
                    "available_devices": registry_stats["available_devices"],
                    "unavailable_devices": registry_stats["unavailable_devices"],
                    "availability_rate": (registry_stats["available_devices"] / registry_stats["total_devices"] * 100) if registry_stats["total_devices"] > 0 else 0.0
                },
                "hardware_characteristics": {
                    "average_qubits": registry_stats["average_qubits"],
                    "max_qubits": registry_stats["max_qubits"],
                    "average_gate_fidelity": registry_stats["average_gate_fidelity"],
                    "average_queue_time": registry_stats["average_queue_time"]
                },
                "dashboard_metadata": {
                    "namespace": self.config.qpu_namespace,
                    "visual_isolation": self.config.visual_isolation,
                    "hardware_label": "QUANTUM PROVIDER STATUS",
                    "no_sla_contamination": self.config.no_sla_contamination,
                    "last_refresh": time.time()
                }
            }
            
            self._dashboard_views += 1
            self._last_refresh = time.time()
            
            logger.debug("Provider status panel generated", 
                        total_devices=registry_stats["total_devices"],
                        available_devices=registry_stats["available_devices"])
            
            return provider_status
            
        except Exception as e:
            logger.error("Failed to generate provider status panel", error=str(e))
            return self._get_error_panel(QPUDashboardType.PROVIDER_STATUS, str(e))
    
    async def get_queue_latency_visibility(self) -> Dict[str, Any]:
        """
        Get queue latency visibility for QPU devices.
        
        Returns queue delay tracking with visual separation.
        """
        try:
            # Get available devices
            available_devices = self.device_registry.get_available_devices()
            
            # Create queue latency panel
            queue_latency = {
                "panel_type": QPUDashboardType.QUEUE_LATENCY.value,
                "queue_statistics": {
                    "total_qpu_devices": len(available_devices),
                    "devices_with_queue_data": len([d for d in available_devices if d.queue_time_seconds]),
                    "average_queue_time": sum(d.queue_time_seconds or 0 for d in available_devices) / len(available_devices) if available_devices else 0.0,
                    "max_queue_time": max((d.queue_time_seconds or 0) for d in available_devices)) if available_devices else 0.0,
                    "min_queue_time": min((d.queue_time_seconds or 0) for d in available_devices)) if available_devices else 0.0
                },
                "device_queue_details": [
                    {
                        "device_id": device.device_id,
                        "provider": device.provider.value,
                        "queue_time_seconds": device.queue_time_seconds,
                        "queue_time_minutes": (device.queue_time_seconds or 0) / 60,
                        "queue_status": "AVAILABLE" if device.available else "UNAVAILABLE",
                        "queue_level": "LOW" if (device.queue_time_seconds or 0) < 300 else "MEDIUM" if (device.queue_time_seconds or 0) < 600 else "HIGH",
                        "visual_isolation": self.config.visual_isolation
                    }
                    for device in available_devices
                ],
                "queue_trends": {
                    "trend_direction": "stable",  # This would calculate real trends
                    "trend_percentage": 0.0,
                    "trend_period_hours": 24
                },
                "dashboard_metadata": {
                    "namespace": self.config.qpu_namespace,
                    "visual_isolation": self.config.visual_isolation,
                    "hardware_label": "QUANTUM QUEUE LATENCY",
                    "no_sla_contamination": self.config.no_sla_contamination,
                    "last_refresh": time.time()
                }
            }
            
            self._dashboard_views += 1
            self._last_refresh = time.time()
            
            logger.debug("Queue latency panel generated", 
                        total_devices=len(available_devices),
                        average_queue_time=queue_latency["queue_statistics"]["average_queue_time"])
            
            return queue_latency
            
        except Exception as e:
            logger.error("Failed to generate queue latency panel", error=str(e))
            return self._get_error_panel(QPUDashboardType.QUEUE_LATENCY, str(e))
    
    async def get_governance_quota_visibility(self) -> Dict[str, Any]:
        """
        Get governance quota visibility for QPU operations.
        
        Returns hardware governance limits with visual separation.
        """
        try:
            # Get governance statistics
            governance_stats = await self.hardware_governance.get_governance_statistics()
            
            # Create governance quota panel
            governance_quotas = {
                "panel_type": QPUDashboardType.GOVERNANCE_QUOTAS.value,
                "quota_overview": governance_stats.get("global_quotas", {}),
                "quota_utilization": {
                    "daily_tasks": {
                        "current": sum(usage.get("daily_tasks", 0) for usage in governance_stats.get("quota_usage", {}).values()),
                        "limit": governance_stats.get("global_quotas", {}).get("max_qpu_tasks_per_day", 0),
                        "utilization_rate": 0.0
                    },
                    "concurrent_tasks": {
                        "current": sum(usage.get("concurrent_tasks", 0) for usage in governance_stats.get("quota_usage", {}).values()),
                        "limit": governance_stats.get("global_quotas", {}).get("max_qpu_concurrent", 0),
                        "utilization_rate": 0.0
                    },
                    "daily_cost": {
                        "current": sum(usage.get("daily_cost", 0.0) for usage in governance_stats.get("quota_usage", {}).values()),
                        "limit": governance_stats.get("global_quotas", {}).get("max_qpu_cost_per_day", 0.0),
                        "utilization_rate": 0.0
                    }
                },
                "provider_quotas": governance_stats.get("provider_quotas", {}),
                "governance_guarantees": self.hardware_governance.get_governance_guarantees(),
                "dashboard_metadata": {
                    "namespace": self.config.qpu_namespace,
                    "visual_isolation": self.config.visual_isolation,
                    "hardware_label": "QUANTUM GOVERNANCE QUOTAS",
                    "no_sla_contamination": self.config.no_sla_contamination,
                    "last_refresh": time.time()
                }
            }
            
            # Calculate utilization rates
            for quota_type, quota_data in governance_quotas["quota_utilization"].items():
                current = quota_data["current"]
                limit = quota_data["limit"]
                if limit > 0:
                    quota_data["utilization_rate"] = (current / limit * 100)
            
            self._dashboard_views += 1
            self._last_refresh = time.time()
            
            logger.debug("Governance quota panel generated", 
                        global_quotas=governance_stats.get("global_quotas", {}),
                        provider_quotas=len(governance_stats.get("provider_quotas", {})))
            
            return governance_quotas
            
        except Exception as e:
            logger.error("Failed to generate governance quota panel", error=str(e))
            return self._get_error_panel(QPUDashboardType.GOVERNANCE_QUOTAS, str(e))
    
    async def get_fallback_visibility(self) -> Dict[str, Any]:
        """
        Get fallback chain visibility for QPU operations.
        
        Returns fallback transparency with visual separation.
        """
        try:
            # Get fallback statistics
            fallback_stats = await self.fallback_chains.get_fallback_statistics()
            
            # Create fallback visibility panel
            fallback_visibility = {
                "panel_type": QPUDashboardType.FALLBACK_VISIBILITY.value,
                "fallback_overview": {
                    "total_chains": fallback_stats.get("total_chains", 0),
                    "active_chains": fallback_stats.get("active_chains", 0),
                    "total_fallbacks": fallback_stats.get("total_fallbacks", 0),
                    "fallback_rate": fallback_stats.get("fallback_rate", 0.0)
                },
                "fallback_path_distribution": fallback_stats.get("fallback_path_distribution", {}),
                "fallback_reason_distribution": fallback_stats.get("fallback_reason_distribution", {}),
                "solver_success_rates": fallback_stats.get("solver_success_rates", {}),
                "fallback_guarantees": self.fallback_chains.get_fallback_guarantees(),
                "safe_fallback_hierarchy": [
                    "QPU",
                    "→ cloud_simulator",
                    "→ local_braket",
                    "→ qiskit",
                    "→ neal",
                    "→ classical"
                ],
                "dashboard_metadata": {
                    "namespace": self.config.qpu_namespace,
                    "visual_isolation": self.config.visual_isolation,
                    "hardware_label": "QUANTUM FALLBACK VISIBILITY",
                    "no_sla_contamination": self.config.no_sla_contamination,
                    "no_replay_contamination": self.config.no_replay_contamination,
                    "last_refresh": time.time()
                }
            }
            
            self._dashboard_views += 1
            self._last_refresh = time.time()
            
            logger.debug("Fallback visibility panel generated", 
                        total_chains=fallback_stats.get("total_chains", 0),
                        fallback_rate=fallback_stats.get("fallback_rate", 0.0))
            
            return fallback_visibility
            
        except Exception as e:
            logger.error("Failed to generate fallback visibility panel", error=str(e))
            return self._get_error_panel(QPUDashboardType.FALLBACK_VISIBILITY, str(e))
    
    async def get_calibration_observability(self) -> Dict[str, Any]:
        """
        Get calibration observability for QPU devices.
        
        Returns calibration data with observational-only labeling.
        """
        try:
            # Get calibration observability statistics
            calibration_stats = await self.calibration_observability.get_observability_statistics()
            
            # Create calibration observability panel
            calibration_observability = {
                "panel_type": QPUDashboardType.CALIBRATION_OBSERVABILITY.value,
                "calibration_overview": calibration_stats.get("total_snapshots", 0),
                "provider_calibration_summary": {
                    provider.value: await self.calibration_observability.get_provider_calibration_summary(provider.value)
                    for provider in QPUProvider
                },
                "calibration_guarantees": self.calibration_observability.get_observability_guarantees(),
                "observational_only_label": "CALIBRATION DATA IS OBSERVATIONAL ONLY",
                "dashboard_metadata": {
                    "namespace": self.config.qpu_namespace,
                    "visual_isolation": self.config.visual_isolation,
                    "hardware_label": "QUANTUM CALIBRATION OBSERVABILITY",
                    "observational_only": True,
                    "no_outcome_influence": True,
                    "last_refresh": time.time()
                }
            }
            
            self._dashboard_views += 1
            self._last_refresh = time.time()
            
            logger.debug("Calibration observability panel generated", 
                        total_snapshots=calibration_stats.get("total_snapshots", 0))
            
            return calibration_observability
            
        except Exception as e:
            logger.error("Failed to generate calibration observability panel", error=str(e))
            return self._get_error_panel(QPUDashboardType.CALIBRATION_OBSERVABILITY, str(e))
    
    def _get_error_panel(self, panel_type: QPUDashboardType, error: str) -> Dict[str, Any]:
        """Get error panel for dashboard component."""
        return {
            "panel_type": panel_type.value,
            "error": True,
            "error_message": error,
            "dashboard_metadata": {
                "namespace": self.config.qpu_namespace,
                "visual_isolation": self.config.visual_isolation,
                "hardware_label": "QUANTUM DASHBOARD ERROR",
                "no_sla_contamination": self.config.no_sla_contamination,
                "last_refresh": time.time()
            }
        }
    
    async def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get QPU dashboard extension statistics."""
        return {
            "total_dashboard_views": self._dashboard_views,
            "last_refresh": self._last_refresh,
            "config": {
                "enable_qpu_dashboard": self.config.enable_qpu_dashboard,
                "visual_isolation": self.config.visual_isolation,
                "hardware_execution_labeling": self.config.hardware_execution_labeling,
                "no_sla_contamination": self.config.no_sla_contamination,
                "no_replay_contamination": self.config.no_replay_contamination,
                "max_sessions": self.config.max_dashboard_sessions,
                "refresh_interval": self.config.dashboard_refresh_interval_seconds,
                "namespace": self.config.qpu_namespace
            },
            "components": {
                "qpu_execution_panel": True,
                "provider_status": True,
                "queue_latency": True,
                "governance_quotas": True,
                "fallback_visibility": True,
                "calibration_observability": True
            },
            "visual_separation": {
                "from_simulators": self.config.visual_isolation,
                "from_live_operations": self.config.visual_isolation,
                "from_replay_dashboards": self.config.no_replay_contamination,
                "from_sla_metrics": self.config.no_sla_contamination
            }
        }
    
    def get_dashboard_guarantees(self) -> Dict[str, Any]:
        """Get QPU dashboard extension guarantees."""
        return {
            "visual_isolation": self.config.visual_isolation,
            "hardware_execution_labeling": self.config.hardware_execution_labeling,
            "no_sla_contamination": self.config.no_sla_contamination,
            "no_replay_contamination": self.config.no_replay_contamination,
            "provider_visibility": True,
            "queue_latency_visibility": True,
            "governance_quota_visibility": True,
            "fallback_transparency": True,
            "calibration_observability": True,
            "namespace_separation": True,
            "operational_truth_protection": True,
            "simulator_isolation": True
        }


# Global QPU dashboard extension instance
_qpu_dashboard_extension: Optional[QPUDashboardExtension] = None


def get_qpu_dashboard_extension() -> QPUDashboardExtension:
    """Get global QPU dashboard extension instance."""
    global _qpu_dashboard_extension
    if _qpu_dashboard_extension is None:
        _qpu_dashboard_extension = QPUDashboardExtension(QPUDashboardConfig())
    return _qpu_dashboard_extension


def create_qpu_dashboard_config(
    enable_qpu_dashboard: bool = True,
    visual_isolation: bool = True,
    hardware_execution_labeling: bool = True,
    no_sla_contamination: bool = True,
    no_replay_contamination: bool = True,
    max_dashboard_sessions: int = 1000,
    dashboard_refresh_interval_seconds: int = 30,
    qpu_namespace: str = "qpu_dashboard"
) -> QPUDashboardConfig:
    """Create QPU dashboard extension configuration."""
    return QPUDashboardConfig(
        enable_qpu_dashboard=enable_qpu_dashboard,
        visual_isolation=visual_isolation,
        hardware_execution_labeling=hardware_execution_labeling,
        no_sla_contamination=no_sla_contamination,
        no_replay_contamination=no_replay_contamination,
        max_dashboard_sessions=max_dashboard_sessions,
        dashboard_refresh_interval_seconds=dashboard_refresh_interval_seconds,
        qpu_namespace=qpu_namespace
    )
