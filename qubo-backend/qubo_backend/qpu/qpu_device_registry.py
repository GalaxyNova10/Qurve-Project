"""
Qurve AI - QPU Device Registry
Safe QPU device registry with ARN validation and provider support.

Principles:
✅ ARN validation: Strict AWS resource validation
✅ Provider validation: IonQ, Rigetti, OQC support
✅ Region validation: Geographic availability checks
✅ Device availability: Real-time capability checks
✅ Hardware capability: Device-specific validation
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class QPUProvider(Enum):
    """Supported QPU providers."""
    IONQ = "IonQ"
    RIGETTI = "Rigetti"
    OQC = "OQC"


class QPUDeviceType(Enum):
    """QPU device types."""
    QPU = "QPU"
    SIMULATOR = "SIMULATOR"


@dataclass
class QPUDevice:
    """QPU device definition."""
    device_id: str
    arn: str
    provider: QPUProvider
    device_type: QPUDeviceType
    regions: List[str]
    qubits: int
    connectivity: Optional[str] = None
    gate_fidelity: Optional[float] = None
    readout_fidelity: Optional[float] = None
    t1_time: Optional[float] = None
    t2_time: Optional[float] = None
    available: bool = False
    queue_time_seconds: Optional[int] = None
    cost_per_task: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class QPUDeviceRegistry:
    """
    Production-grade QPU device registry.
    
    Features:
    - ARN validation and parsing
    - Provider validation
    - Region validation
    - Device availability checks
    - Hardware capability validation
    """
    
    def __init__(self):
        self._devices: Dict[str, QPUDevice] = {}
        self._initialize_device_registry()
        
        logger.info("QPU device registry initialized", 
                  total_devices=len(self._devices),
                  providers=[provider.value for provider in QPUProvider])
    
    def _initialize_device_registry(self) -> None:
        """Initialize QPU device registry with supported devices."""
        
        # IonQ Devices
        self._register_device(QPUDevice(
            device_id="ionq_aria",
            arn="arn:aws:braket:::device/qpu/ionq/Aria",
            provider=QPUProvider.IONQ,
            device_type=QPUDeviceType.QPU,
            regions=["us-east-1", "us-west-2"],
            qubits=23,
            connectivity="all-to-all",
            gate_fidelity=0.996,
            readout_fidelity=0.993,
            t1_time=100.0,
            t2_time=200.0,
            available=True,
            queue_time_seconds=300,
            cost_per_task=1.50,
            metadata={
                "technology": "trapped-ion",
                "gate_set": ["rx", "ry", "rz", "cnot", "cz"],
                "benchmark_performance": "high"
            }
        ))
        
        self._register_device(QPUDevice(
            device_id="ionq_harmony",
            arn="arn:aws:braket:::device/qpu/ionq/Harmony",
            provider=QPUProvider.IONQ,
            device_type=QPUDeviceType.QPU,
            regions=["us-east-1"],
            qubits=11,
            connectivity="all-to-all",
            gate_fidelity=0.994,
            readout_fidelity=0.990,
            t1_time=80.0,
            t2_time=150.0,
            available=True,
            queue_time_seconds=180,
            cost_per_task=0.75,
            metadata={
                "technology": "trapped-ion",
                "gate_set": ["rx", "ry", "rz", "cnot", "cz"],
                "benchmark_performance": "medium"
            }
        ))
        
        # Rigetti Devices
        self._register_device(QPUDevice(
            device_id="rigetti_aspen_m2",
            arn="arn:aws:braket:::device/qpu/rigetti/Aspen-M-2",
            provider=QPUProvider.RIGETTI,
            device_type=QPUDeviceType.QPU,
            regions=["us-west-2"],
            qubits=80,
            connectivity="lattice",
            gate_fidelity=0.985,
            readout_fidelity=0.975,
            t1_time=25.0,
            t2_time=20.0,
            available=True,
            queue_time_seconds=600,
            cost_per_task=0.35,
            metadata={
                "technology": "superconducting",
                "gate_set": ["rx", "ry", "rz", "cz", "iswap"],
                "benchmark_performance": "high"
            }
        ))
        
        self._register_device(QPUDevice(
            device_id="rigetti_aspen_m3",
            arn="arn:aws:braket:::device/qpu/rigetti/Aspen-M-3",
            provider=QPUProvider.RIGETTI,
            device_type=QPUDeviceType.QPU,
            regions=["us-west-2"],
            qubits=80,
            connectivity="lattice",
            gate_fidelity=0.987,
            readout_fidelity=0.978,
            t1_time=30.0,
            t2_time=25.0,
            available=False,  # Currently unavailable
            queue_time_seconds=None,
            cost_per_task=0.40,
            metadata={
                "technology": "superconducting",
                "gate_set": ["rx", "ry", "rz", "cz", "iswap"],
                "benchmark_performance": "high"
            }
        ))
        
        # OQC Devices
        self._register_device(QPUDevice(
            device_id="oqc_lucy",
            arn="arn:aws:braket:::device/qpu/oqc/Lucy",
            provider=QPUProvider.OQC,
            device_type=QPUDeviceType.QPU,
            regions=["eu-west-2"],
            qubits=8,
            connectivity="linear",
            gate_fidelity=0.990,
            readout_fidelity=0.980,
            t1_time=40.0,
            t2_time=35.0,
            available=True,
            queue_time_seconds=240,
            cost_per_task=0.25,
            metadata={
                "technology": "photonic",
                "gate_set": ["rx", "ry", "rz", "cz"],
                "benchmark_performance": "medium"
            }
        ))
        
        logger.info("QPU device registry initialized", 
                  ionq_devices=len([d for d in self._devices.values() if d.provider == QPUProvider.IONQ]),
                  rigetti_devices=len([d for d in self._devices.values() if d.provider == QPUProvider.RIGETTI]),
                  oqc_devices=len([d for d in self._devices.values() if d.provider == QPUProvider.OQC]))
    
    def _register_device(self, device: QPUDevice) -> None:
        """Register a QPU device in the registry."""
        try:
            # Validate ARN format
            if not self._validate_arn(device.arn):
                raise ValueError(f"Invalid ARN format: {device.arn}")
            
            # Validate provider
            if device.provider not in QPUProvider:
                raise ValueError(f"Unsupported provider: {device.provider}")
            
            # Validate device type
            if device.device_type not in QPUDeviceType:
                raise ValueError(f"Unsupported device type: {device.device_type}")
            
            # Validate regions
            if not device.regions:
                raise ValueError("At least one region must be specified")
            
            # Register device
            self._devices[device.device_id] = device
            
            logger.debug("QPU device registered", 
                        device_id=device.device_id,
                        provider=device.provider.value,
                        arn=device.arn)
            
        except Exception as e:
            logger.error("Failed to register QPU device", 
                        device_id=device.device_id,
                        error=str(e))
            raise
    
    def _validate_arn(self, arn: str) -> bool:
        """Validate AWS ARN format for Braket devices."""
        # Braket QPU ARN pattern: arn:aws:braket:::device/qpu/{provider}/{device}
        pattern = r'^arn:aws:braket:::device/qpu/([a-zA-Z0-9]+)/([a-zA-Z0-9\-_]+)$'
        return bool(re.match(pattern, arn))
    
    def get_device(self, device_id: str) -> Optional[QPUDevice]:
        """Get QPU device by ID."""
        return self._devices.get(device_id)
    
    def get_devices_by_provider(self, provider: QPUProvider) -> List[QPUDevice]:
        """Get all devices for a specific provider."""
        return [device for device in self._devices.values() if device.provider == provider]
    
    def get_devices_by_region(self, region: str) -> List[QPUDevice]:
        """Get all devices available in a specific region."""
        return [device for device in self._devices.values() if region in device.regions]
    
    def get_available_devices(self) -> List[QPUDevice]:
        """Get all currently available QPU devices."""
        return [device for device in self._devices.values() if device.available]
    
    def validate_device_request(self, 
                            device_id: str,
                            provider: str,
                            region: str) -> Tuple[bool, str, Optional[QPUDevice]]:
        """
        Validate device request against registry.
        
        Args:
            device_id: Requested device ID
            provider: Requested provider
            region: Requested region
            
        Returns:
            Tuple of (valid: bool, reason: str, device: Optional[QPUDevice])
        """
        try:
            # Validate provider
            try:
                qpu_provider = QPUProvider(provider)
            except ValueError:
                return False, f"Unsupported provider: {provider}", None
            
            # Get device
            device = self.get_device(device_id)
            if not device:
                return False, f"Device not found: {device_id}", None
            
            # Validate provider matches
            if device.provider != qpu_provider:
                return False, f"Device {device_id} belongs to provider {device.provider.value}, not {provider}", device
            
            # Validate device type
            if device.device_type != QPUDeviceType.QPU:
                return False, f"Device {device_id} is not a QPU: {device.device_type.value}", device
            
            # Validate region availability
            if region not in device.regions:
                return False, f"Device {device_id} not available in region {region}. Available regions: {device.regions}", device
            
            # Validate device availability
            if not device.available:
                return False, f"Device {device_id} is currently unavailable", device
            
            # Validate hardware capabilities
            if not self._validate_hardware_capabilities(device):
                return False, f"Device {device_id} fails hardware capability validation", device
            
            return True, "Device request validated", device
            
        except Exception as e:
            logger.error("Failed to validate device request", 
                        device_id=device_id,
                        provider=provider,
                        region=region,
                        error=str(e))
            return False, f"Device validation error: {str(e)}", None
    
    def _validate_hardware_capabilities(self, device: QPUDevice) -> bool:
        """Validate hardware capabilities meet minimum requirements."""
        try:
            # Minimum qubit requirement
            if device.qubits < 2:
                return False
            
            # Gate fidelity requirement
            if device.gate_fidelity and device.gate_fidelity < 0.95:
                return False
            
            # Readout fidelity requirement
            if device.readout_fidelity and device.readout_fidelity < 0.90:
                return False
            
            # T1/T2 time requirements
            if device.t1_time and device.t1_time < 10.0:
                return False
            
            if device.t2_time and device.t2_time < 10.0:
                return False
            
            return True
            
        except Exception as e:
            logger.error("Failed to validate hardware capabilities", 
                        device_id=device.device_id,
                        error=str(e))
            return False
    
    def update_device_availability(self, 
                                device_id: str,
                                available: bool,
                                queue_time_seconds: Optional[int] = None) -> bool:
        """Update device availability status."""
        try:
            device = self.get_device(device_id)
            if not device:
                return False
            
            device.available = available
            if queue_time_seconds is not None:
                device.queue_time_seconds = queue_time_seconds
            
            logger.info("Device availability updated", 
                       device_id=device_id,
                       available=available,
                       queue_time_seconds=queue_time_seconds)
            
            return True
            
        except Exception as e:
            logger.error("Failed to update device availability", 
                        device_id=device_id,
                        error=str(e))
            return False
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get registry statistics."""
        devices = list(self._devices.values())
        
        return {
            "total_devices": len(devices),
            "available_devices": len([d for d in devices if d.available]),
            "unavailable_devices": len([d for d in devices if not d.available]),
            "providers": {
                "ionq": len([d for d in devices if d.provider == QPUProvider.IONQ]),
                "rigetti": len([d for d in devices if d.provider == QPUProvider.RIGETTI]),
                "oqc": len([d for d in devices if d.provider == QPUProvider.OQC])
            },
            "regions": {
                "us-east-1": len([d for d in devices if "us-east-1" in d.regions]),
                "us-west-2": len([d for d in devices if "us-west-2" in d.regions]),
                "eu-west-2": len([d for d in devices if "eu-west-2" in d.regions])
            },
            "device_types": {
                "qpu": len([d for d in devices if d.device_type == QPUDeviceType.QPU]),
                "simulator": len([d for d in devices if d.device_type == QPUDeviceType.SIMULATOR])
            },
            "average_qubits": sum(d.qubits for d in devices) / len(devices) if devices else 0,
            "max_qubits": max(d.qubits for d in devices) if devices else 0,
            "average_gate_fidelity": sum(d.gate_fidelity or 0 for d in devices) / len([d for d in devices if d.gate_fidelity]) if devices else 0,
            "average_queue_time": sum(d.queue_time_seconds or 0 for d in devices) / len([d for d in devices if d.queue_time_seconds]) if devices else 0
        }


# Global QPU device registry instance
_qpu_device_registry: Optional[QPUDeviceRegistry] = None


def get_qpu_device_registry() -> QPUDeviceRegistry:
    """Get global QPU device registry instance."""
    global _qpu_device_registry
    if _qpu_device_registry is None:
        _qpu_device_registry = QPUDeviceRegistry()
    return _qpu_device_registry


# Export device registry for external use
BRAKET_QPU_DEVICES = {
    "ionq_aria": {
        "arn": "arn:aws:braket:::device/qpu/ionq/Aria",
        "provider": "IonQ",
        "type": "QPU",
        "regions": ["us-east-1", "us-west-2"]
    },
    "ionq_harmony": {
        "arn": "arn:aws:braket:::device/qpu/ionq/Harmony",
        "provider": "IonQ",
        "type": "QPU",
        "regions": ["us-east-1"]
    },
    "rigetti_aspen_m2": {
        "arn": "arn:aws:braket:::device/qpu/rigetti/Aspen-M-2",
        "provider": "Rigetti",
        "type": "QPU",
        "regions": ["us-west-2"]
    },
    "rigetti_aspen_m3": {
        "arn": "arn:aws:braket:::device/qpu/rigetti/Aspen-M-3",
        "provider": "Rigetti",
        "type": "QPU",
        "regions": ["us-west-2"]
    },
    "oqc_lucy": {
        "arn": "arn:aws:braket:::device/qpu/oqc/Lucy",
        "provider": "OQC",
        "type": "QPU",
        "regions": ["eu-west-2"]
    }
}
