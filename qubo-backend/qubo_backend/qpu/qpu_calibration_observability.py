"""
Qurve AI - QPU Calibration Observability
Observational-only calibration metadata for QPU devices.

Principles:
✅ OBSERVATIONAL ONLY: Never use calibration data to mutate outcomes
✅ CALIBRATION METADATA: Device availability and queue tracking
✅ QUEUE DELAY TRACKING: Hardware execution metadata
✅ PROVIDER METADATA: Capture provider-specific data
✅ NO REPLAY MUTATION: Calibration data never affects replay
"""

import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .qpu_device_registry import get_qpu_device_registry, QPUProvider

logger = logging.getLogger(__name__)


class CalibrationStatus(Enum):
    """Calibration status types."""
    CALIBRATED = "calibrated"
    RECALIBRATING = "recalibrating"
    UNCALIBRATED = "uncalibrated"
    CALIBRATION_FAILED = "calibration_failed"
    MAINTENANCE = "maintenance"


@dataclass
class CalibrationSnapshot:
    """Calibration snapshot metadata."""
    snapshot_id: str
    provider: str
    device: str
    timestamp: float
    status: CalibrationStatus
    fidelity_metrics: Dict[str, float] = field(default_factory=dict)
    queue_metrics: Dict[str, Any] = field(default_factory=dict)
    hardware_metrics: Dict[str, Any] = field(default_factory=dict)
    provider_metadata: Dict[str, Any] = field(default_factory=dict)
    observational_only: bool = True


@dataclass
class QPUCalibrationConfig:
    """QPU calibration observability configuration."""
    enable_calibration_tracking: bool = True
    calibration_retention_days: int = 30
    snapshot_interval_seconds: int = 300  # 5 minutes
    queue_delay_threshold_seconds: int = 600  # 10 minutes
    fidelity_threshold: float = 0.95
    observational_only: bool = True


class QPUCalibrationObservability:
    """
    Production-grade QPU calibration observability.
    
    Features:
    - Observational-only calibration tracking
    - Device availability snapshots
    - Queue delay tracking
    - Hardware execution metadata
    - Provider metadata capture
    """
    
    def __init__(self, config: QPUCalibrationConfig):
        self.config = config
        self.device_registry = get_qpu_device_registry()
        
        # Calibration state
        self._calibration_snapshots: Dict[str, List[CalibrationSnapshot]] = {}
        self._device_availability: Dict[str, bool] = {}
        self._queue_delays: Dict[str, List[float]] = {}
        
        # Observability statistics
        self._snapshot_count = 0
        self._last_snapshot_time = 0.0
        
        logger.info("QPU calibration observability initialized", 
                  observational_only=config.observational_only,
                  snapshot_interval=config.snapshot_interval_seconds,
                  retention_days=config.calibration_retention_days)
    
    async def capture_calibration_snapshot(self, 
                                       provider: str,
                                       device: str,
                                       force_capture: bool = False) -> Optional[CalibrationSnapshot]:
        """
        Capture calibration snapshot for QPU device.
        
        Args:
            provider: QPU provider
            device: QPU device
            force_capture: Force capture regardless of interval
            
        Returns:
            Calibration snapshot if captured successfully
        """
        try:
            current_time = time.time()
            
            # Check if enough time has passed since last snapshot
            if not force_capture:
                time_since_last = current_time - self._last_snapshot_time
                if time_since_last < self.config.snapshot_interval_seconds:
                    return None
            
            # Get device from registry
            device_obj = self.device_registry.get_device(device)
            if not device_obj:
                logger.warning("Device not found for calibration snapshot", device=device)
                return None
            
            # Create calibration snapshot
            snapshot_id = f"calibration_{provider}_{device}_{int(current_time)}"
            snapshot = CalibrationSnapshot(
                snapshot_id=snapshot_id,
                provider=provider,
                device=device,
                timestamp=current_time,
                status=await self._determine_calibration_status(device_obj),
                fidelity_metrics=await self._capture_fidelity_metrics(device_obj),
                queue_metrics=await self._capture_queue_metrics(device_obj),
                hardware_metrics=await self._capture_hardware_metrics(device_obj),
                provider_metadata=await self._capture_provider_metadata(provider, device_obj),
                observational_only=self.config.observational_only
            )
            
            # Store snapshot
            if provider not in self._calibration_snapshots:
                self._calibration_snapshots[provider] = []
            
            self._calibration_snapshots[provider].append(snapshot)
            self._snapshot_count += 1
            self._last_snapshot_time = current_time
            
            # Clean up old snapshots
            await self._cleanup_old_snapshots()
            
            logger.info("Calibration snapshot captured", 
                       snapshot_id=snapshot_id,
                       provider=provider,
                       device=device,
                       status=snapshot.status.value,
                       observational_only=snapshot.observational_only)
            
            return snapshot
            
        except Exception as e:
            logger.error("Failed to capture calibration snapshot", 
                        provider=provider,
                        device=device,
                        error=str(e))
            return None
    
    async def _determine_calibration_status(self, device_obj) -> CalibrationStatus:
        """Determine calibration status for device."""
        try:
            # Check device availability
            if not device_obj.available:
                return CalibrationStatus.MAINTENANCE
            
            # Check queue delay
            queue_time = device_obj.queue_time_seconds
            if queue_time and queue_time > self.config.queue_delay_threshold_seconds:
                return CalibrationStatus.RECALIBRATING
            
            # Check fidelity metrics
            if (device_obj.gate_fidelity and device_obj.gate_fidelity < self.config.fidelity_threshold):
                return CalibrationStatus.CALIBRATION_FAILED
            
            # Default to calibrated
            return CalibrationStatus.CALIBRATED
            
        except Exception as e:
            logger.error("Failed to determine calibration status", error=str(e))
            return CalibrationStatus.UNCALIBRATED
    
    async def _capture_fidelity_metrics(self, device_obj) -> Dict[str, float]:
        """Capture fidelity metrics for device."""
        try:
            metrics = {}
            
            if device_obj.gate_fidelity:
                metrics["gate_fidelity"] = device_obj.gate_fidelity
            
            if device_obj.readout_fidelity:
                metrics["readout_fidelity"] = device_obj.readout_fidelity
            
            # Calculate composite fidelity
            if metrics:
                metrics["composite_fidelity"] = sum(metrics.values()) / len(metrics)
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to capture fidelity metrics", error=str(e))
            return {}
    
    async def _capture_queue_metrics(self, device_obj) -> Dict[str, Any]:
        """Capture queue metrics for device."""
        try:
            metrics = {}
            
            if device_obj.queue_time_seconds:
                metrics["queue_time_seconds"] = device_obj.queue_time_seconds
                metrics["queue_delay_exceeded"] = device_obj.queue_time_seconds > self.config.queue_delay_threshold_seconds
            
            # Track queue delay history
            device_key = f"{device_obj.provider.value}_{device_obj.device_id}"
            if device_obj.queue_time_seconds:
                if device_key not in self._queue_delays:
                    self._queue_delays[device_key] = []
                self._queue_delays[device_key].append(device_obj.queue_time_seconds)
                
                # Keep only recent delays
                if len(self._queue_delays[device_key]) > 100:
                    self._queue_delays[device_key] = self._queue_delays[device_key][-100:]
                
                metrics["average_queue_delay"] = sum(self._queue_delays[device_key]) / len(self._queue_delays[device_key])
                metrics["max_queue_delay"] = max(self._queue_delays[device_key])
                metrics["min_queue_delay"] = min(self._queue_delays[device_key])
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to capture queue metrics", error=str(e))
            return {}
    
    async def _capture_hardware_metrics(self, device_obj) -> Dict[str, Any]:
        """Capture hardware metrics for device."""
        try:
            metrics = {}
            
            if device_obj.qubits:
                metrics["qubits"] = device_obj.qubits
            
            if device_obj.connectivity:
                metrics["connectivity"] = device_obj.connectivity
            
            if device_obj.t1_time:
                metrics["t1_time"] = device_obj.t1_time
            
            if device_obj.t2_time:
                metrics["t2_time"] = device_obj.t2_time
            
            # Calculate quality score
            quality_factors = []
            if device_obj.gate_fidelity:
                quality_factors.append(device_obj.gate_fidelity)
            if device_obj.readout_fidelity:
                quality_factors.append(device_obj.readout_fidelity)
            if device_obj.t1_time and device_obj.t1_time > 0:
                quality_factors.append(min(1.0, device_obj.t1_time / 100.0))  # Normalize T1 time
            if device_obj.t2_time and device_obj.t2_time > 0:
                quality_factors.append(min(1.0, device_obj.t2_time / 100.0))  # Normalize T2 time
            
            if quality_factors:
                metrics["hardware_quality_score"] = sum(quality_factors) / len(quality_factors)
            
            return metrics
            
        except Exception as e:
            logger.error("Failed to capture hardware metrics", error=str(e))
            return {}
    
    async def _capture_provider_metadata(self, provider: str, device_obj) -> Dict[str, Any]:
        """Capture provider-specific metadata."""
        try:
            metadata = {}
            
            # Provider-specific metadata
            if provider == QPUProvider.IONQ.value:
                metadata.update({
                    "technology": "trapped-ion",
                    "gate_set": ["rx", "ry", "rz", "cnot", "cz"],
                    "native_gates": device_obj.metadata.get("gate_set", []),
                    "ion_trap_type": "linear_chain",
                    "laser_wavelength": device_obj.metadata.get("laser_wavelength", "355nm")
                })
            
            elif provider == QPUProvider.RIGETTI.value:
                metadata.update({
                    "technology": "superconducting",
                    "gate_set": ["rx", "ry", "rz", "cz", "iswap"],
                    "native_gates": device_obj.metadata.get("gate_set", []),
                    "chip_architecture": "lattice",
                    "qubit_topology": device_obj.connectivity,
                    "operating_temperature": device_obj.metadata.get("operating_temperature", "15mK")
                })
            
            elif provider == QPUProvider.OQC.value:
                metadata.update({
                    "technology": "photonic",
                    "gate_set": ["rx", "ry", "rz", "cz"],
                    "native_gates": device_obj.metadata.get("gate_set", []),
                    "photon_source": "spontaneous_parametric_down_conversion",
                    "wavelength": device_obj.metadata.get("wavelength", "1550nm"),
                    "interferometer_type": device_obj.metadata.get("interferometer_type", "time-bin")
                })
            
            # Add device metadata
            metadata.update(device_obj.metadata)
            
            return metadata
            
        except Exception as e:
            logger.error("Failed to capture provider metadata", error=str(e))
            return {}
    
    async def _cleanup_old_snapshots(self) -> None:
        """Clean up old calibration snapshots."""
        try:
            cutoff_time = time.time() - (self.config.calibration_retention_days * 24 * 60 * 60)
            
            for provider, snapshots in self._calibration_snapshots.items():
                original_count = len(snapshots)
                # Keep only recent snapshots
                self._calibration_snapshots[provider] = [
                    snapshot for snapshot in snapshots
                    if snapshot.timestamp > cutoff_time
                ]
                cleaned_count = original_count - len(self._calibration_snapshots[provider])
                
                if cleaned_count > 0:
                    logger.debug("Cleaned up old calibration snapshots", 
                                provider=provider,
                                cleaned_count=cleaned_count)
            
        except Exception as e:
            logger.error("Failed to cleanup old snapshots", error=str(e))
    
    async def get_device_calibration_history(self, 
                                           provider: str,
                                           device: str,
                                           limit: int = 100) -> List[CalibrationSnapshot]:
        """Get calibration history for specific device."""
        try:
            if provider not in self._calibration_snapshots:
                return []
            
            device_snapshots = [
                snapshot for snapshot in self._calibration_snapshots[provider]
                if snapshot.device == device
            ]
            
            # Sort by timestamp (most recent first)
            device_snapshots.sort(key=lambda s: s.timestamp, reverse=True)
            
            return device_snapshots[:limit]
            
        except Exception as e:
            logger.error("Failed to get device calibration history", error=str(e))
            return []
    
    async def get_provider_calibration_summary(self, provider: str) -> Dict[str, Any]:
        """Get calibration summary for provider."""
        try:
            if provider not in self._calibration_snapshots:
                return {"error": "No calibration data for provider"}
            
            snapshots = self._calibration_snapshots[provider]
            
            if not snapshots:
                return {"error": "No calibration snapshots available"}
            
            # Calculate summary statistics
            recent_snapshots = snapshots[-10:]  # Last 10 snapshots
            status_counts = {}
            fidelity_averages = {}
            queue_averages = {}
            
            for snapshot in recent_snapshots:
                # Count statuses
                status = snapshot.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Average fidelity metrics
                for metric, value in snapshot.fidelity_metrics.items():
                    if metric not in fidelity_averages:
                        fidelity_averages[metric] = []
                    fidelity_averages[metric].append(value)
                
                # Average queue metrics
                for metric, value in snapshot.queue_metrics.items():
                    if isinstance(value, (int, float)):
                        if metric not in queue_averages:
                            queue_averages[metric] = []
                        queue_averages[metric].append(value)
            
            # Calculate averages
            for metric in fidelity_averages:
                fidelity_averages[metric] = sum(fidelity_averages[metric]) / len(fidelity_averages[metric])
            
            for metric in queue_averages:
                queue_averages[metric] = sum(queue_averages[metric]) / len(queue_averages[metric])
            
            return {
                "provider": provider,
                "total_snapshots": len(snapshots),
                "recent_snapshots": len(recent_snapshots),
                "status_distribution": status_counts,
                "average_fidelity_metrics": fidelity_averages,
                "average_queue_metrics": queue_averages,
                "latest_snapshot": snapshots[-1] if snapshots else None,
                "observational_only": self.config.observational_only
            }
            
        except Exception as e:
            logger.error("Failed to get provider calibration summary", error=str(e))
            return {"error": str(e)}
    
    async def get_observability_statistics(self) -> Dict[str, Any]:
        """Get calibration observability statistics."""
        try:
            total_snapshots = sum(len(snapshots) for snapshots in self._calibration_snapshots.values())
            
            # Calculate provider statistics
            provider_stats = {}
            for provider, snapshots in self._calibration_snapshots.items():
                if snapshots:
                    latest_snapshot = snapshots[-1]
                    provider_stats[provider] = {
                        "snapshot_count": len(snapshots),
                        "latest_status": latest_snapshot.status.value,
                        "latest_timestamp": latest_snapshot.timestamp,
                        "average_fidelity": sum(s.fidelity_metrics.get("composite_fidelity", 0) for s in snapshots) / len(snapshots) if snapshots else 0
                    }
            
            return {
                "total_snapshots": total_snapshots,
                "providers_tracked": len(self._calibration_snapshots),
                "snapshot_count": self._snapshot_count,
                "last_snapshot_time": self._last_snapshot_time,
                "provider_statistics": provider_stats,
                "config": {
                    "observational_only": self.config.observational_only,
                    "snapshot_interval": self.config.snapshot_interval_seconds,
                    "retention_days": self.config.calibration_retention_days,
                    "fidelity_threshold": self.config.fidelity_threshold,
                    "queue_delay_threshold": self.config.queue_delay_threshold_seconds
                },
                "queue_delay_tracking": {
                    "devices_tracked": len(self._queue_delays),
                    "total_delay_measurements": sum(len(delays) for delays in self._queue_delays.values())
                }
            }
            
        except Exception as e:
            logger.error("Failed to get observability statistics", error=str(e))
            return {"error": str(e)}
    
    def get_observability_guarantees(self) -> Dict[str, Any]:
        """Get calibration observability guarantees."""
        return {
            "observational_only": self.config.observational_only,
            "no_replay_mutation": True,
            "no_outcome_influence": True,
            "calibration_metadata_only": True,
            "device_availability_tracking": True,
            "queue_delay_tracking": True,
            "hardware_execution_metadata": True,
            "provider_metadata_capture": True,
            "isolated_from_operational_truth": True,
            "never_affects_replay_determinism": True,
            "never_affects_governance_decisions": True
        }


# Global QPU calibration observability instance
_qpu_calibration_observability: Optional[QPUCalibrationObservability] = None


def get_qpu_calibration_observability() -> QPUCalibrationObservability:
    """Get global QPU calibration observability instance."""
    global _qpu_calibration_observability
    if _qpu_calibration_observability is None:
        _qpu_calibration_observability = QPUCalibrationObservability(QPUCalibrationConfig())
    return _qpu_calibration_observability


def create_qpu_calibration_config(
    enable_calibration_tracking: bool = True,
    calibration_retention_days: int = 30,
    snapshot_interval_seconds: int = 300,
    queue_delay_threshold_seconds: int = 600,
    fidelity_threshold: float = 0.95,
    observational_only: bool = True
) -> QPUCalibrationConfig:
    """Create QPU calibration observability configuration."""
    return QPUCalibrationConfig(
        enable_calibration_tracking=enable_calibration_tracking,
        calibration_retention_days=calibration_retention_days,
        snapshot_interval_seconds=snapshot_interval_seconds,
        queue_delay_threshold_seconds=queue_delay_threshold_seconds,
        fidelity_threshold=fidelity_threshold,
        observational_only=observational_only
    )
