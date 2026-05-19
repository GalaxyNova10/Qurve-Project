"""
AWS Braket Cloud Execution Module

ALL AWS-specific logic belongs ONLY here.
Responsibilities:
- AWS session creation
- Region validation  
- Credential validation
- Device lookup
- ARN management
- Task submission
- Polling
- Result extraction
- Cloud telemetry
- Safety limits
- Cloud timeout handling

NO business logic inside this module.
"""

import asyncio
import time
import logging
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError

# Safety limits - HARD PROTECTIONS
MAX_CLOUD_SHOTS = 256
MAX_CLOUD_QUBITS = 24
MAX_CONCURRENT_CLOUD_TASKS = 2
MAX_CLOUD_TIMEOUT_SECONDS = 120

# Supported regions
SUPPORTED_REGIONS = ["us-east-1", "us-west-2"]

# Device registry with ARNs and capabilities
BRAKET_CLOUD_DEVICES = {
    "sv1": {
        "arn": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "type": "SIMULATOR",
        "max_shots": 1024,
        "max_qubits": 34,
        "regions": ["us-east-1", "us-west-2"]
    },
    "tn1": {
        "arn": "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
        "type": "SIMULATOR", 
        "max_shots": 1024,
        "max_qubits": 20,
        "regions": ["us-east-1", "us-west-2"]
    },
    "dm1": {
        "arn": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
        "type": "SIMULATOR",
        "max_shots": 1024,
        "max_qubits": 20,
        "regions": ["us-east-1", "us-west-2"]
    }
}

class ExecutionMode(Enum):
    """Execution modes for Braket tasks"""
    LOCAL = "local"
    CLOUD_SIMULATOR = "cloud_simulator"
    CLOUD_QPU = "cloud_qpu"

class TaskStatus(Enum):
    """Cloud task statuses"""
    CREATED = "CREATED"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

@dataclass
class CloudTaskResult:
    """Result from cloud task execution"""
    success: bool
    task_arn: Optional[str] = None
    device_arn: Optional[str] = None
    result_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    queue_time_ms: Optional[int] = None
    execution_time_ms: Optional[int] = None
    total_time_ms: Optional[int] = None

@dataclass
class CloudTelemetry:
    """Telemetry data for cloud execution"""
    cloud_region: str
    device_arn: str
    task_arn: str
    queue_latency_ms: int
    cloud_execution_latency_ms: int
    total_cloud_latency_ms: int
    shot_count: int
    execution_mode: str

class BraketCloudManager:
    """
    Isolated AWS session and device management.
    All AWS-specific operations go through this class.
    """
    
    def __init__(self, region: str = "us-east-1"):
        self.region = region
        self.session: Optional[boto3.Session] = None
        self.braket_client: Optional[Any] = None
        self.logger = logging.getLogger(__name__)
        
    def validate_region(self) -> bool:
        """Validate that the region is supported"""
        return self.region in SUPPORTED_REGIONS
    
    def initialize_session(self) -> Tuple[bool, str]:
        """
        Initialize AWS session and Braket client.
        Returns (success, error_message)
        """
        if not self.validate_region():
            return False, f"Unsupported region: {self.region}"
        
        try:
            # Create explicit boto3 session
            self.session = boto3.Session()
            
            # Test credentials
            sts_client = self.session.client('sts')
            sts_client.get_caller_identity()
            
            # Create Braket client
            self.braket_client = self.session.client('braket', region_name=self.region)
            
            self.logger.info(f"AWS session initialized for region {self.region}")
            return True, ""
            
        except (NoCredentialsError, PartialCredentialsError):
            return False, "AWS credentials not found or incomplete"
        except ClientError as e:
            return False, f"AWS client error: {str(e)}"
        except Exception as e:
            return False, f"Session initialization error: {str(e)}"
    
    def validate_device(self, device_name: str) -> Tuple[bool, str]:
        """
        Validate device availability and compatibility.
        Returns (is_valid, error_message)
        """
        if device_name not in BRAKET_CLOUD_DEVICES:
            return False, f"Unknown device: {device_name}"
        
        device_info = BRAKET_CLOUD_DEVICES[device_name]
        
        if self.region not in device_info["regions"]:
            return False, f"Device {device_name} not available in region {self.region}"
        
        # In a real implementation, we would check device status here
        # For now, assume all listed devices are available
        
        return True, ""
    
    def get_device_arn(self, device_name: str) -> Optional[str]:
        """Get device ARN from registry"""
        if device_name in BRAKET_CLOUD_DEVICES:
            return BRAKET_CLOUD_DEVICES[device_name]["arn"]
        return None
    
    def check_credentials_available(self) -> bool:
        """Check if AWS credentials are available without creating session"""
        try:
            session = boto3.Session()
            sts_client = session.client('sts')
            sts_client.get_caller_identity()
            return True
        except:
            return False

async def submit_cloud_task(
    manager: BraketCloudManager,
    device_name: str,
    task_spec: Any,
    shots: int,
    timeout_seconds: int = 300
) -> CloudTaskResult:
    """
    Submit task to AWS Braket cloud with polling and timeout handling.
    
    Args:
        manager: Initialized BraketCloudManager
        device_name: Target device name
        task_spec: Task specification (e.g. Braket Circuit)
        shots: Number of shots
        timeout_seconds: Maximum execution time
        
    Returns:
        CloudTaskResult with execution details
    """
    start_time = time.time()
    
    # Validate safety limits
    if shots > 1024:
        return CloudTaskResult(
            success=False,
            error_message=f"Shots {shots} exceeds maximum limit"
        )
    
    # Validate device
    is_valid, error_msg = manager.validate_device(device_name)
    if not is_valid:
        return CloudTaskResult(
            success=False,
            error_message=f"Device validation failed: {error_msg}"
        )
    
    device_arn = manager.get_device_arn(device_name)
    if not device_arn:
        return CloudTaskResult(
            success=False,
            error_message=f"Could not get ARN for device {device_name}"
        )
    
    try:
        # Import here to avoid import issues when Braket not available
        from braket.aws import AwsDevice, AwsSession
        
        # Create AWS session for Braket
        aws_session = AwsSession(boto_session=manager.session)
        
        # Create device
        device = AwsDevice(arn=device_arn, aws_session=aws_session)
        
        # Submit task
        task_start = time.time()
        task = device.run(task_spec, shots=shots)
        queue_time_ms = int((time.time() - task_start) * 1000)
        
        # Poll for completion with timeout
        poll_start = time.time()
        while True:
            if time.time() - poll_start > timeout_seconds:
                # Cancel task if timeout
                try:
                    task.cancel()
                except:
                    pass
                return CloudTaskResult(
                    success=False,
                    error_message=f"Task timeout after {timeout_seconds} seconds",
                    task_arn=task.id,
                    device_arn=device_arn,
                    queue_time_ms=queue_time_ms
                )
            
            # Check task state
            state = task.state()
            
            if state == "COMPLETED":
                execution_time_ms = int((time.time() - poll_start) * 1000)
                total_time_ms = int((time.time() - start_time) * 1000)
                
                # Extract results safely
                task_res = task.result()
                if hasattr(task_res, 'measurements'):
                    samples = task_res.measurements
                elif hasattr(task_res, 'get_samples'):
                    samples = task_res.get_samples()
                else:
                    samples = []
                
                result_data = {
                    "samples": samples,
                    "energies": [],  # Energies not typically available for pure circuits unless evaluated
                    "num_shots": shots,
                    "device_name": device_name
                }
                
                return CloudTaskResult(
                    success=True,
                    task_arn=task.id,
                    device_arn=device_arn,
                    result_data=result_data,
                    queue_time_ms=queue_time_ms,
                    execution_time_ms=execution_time_ms,
                    total_time_ms=total_time_ms
                )
            
            elif state in ["FAILED", "CANCELLED"]:
                execution_time_ms = int((time.time() - poll_start) * 1000)
                return CloudTaskResult(
                    success=False,
                    error_message=f"Task {state.lower()}",
                    task_arn=task.id,
                    device_arn=device_arn,
                    queue_time_ms=queue_time_ms,
                    execution_time_ms=execution_time_ms
                )
            
            # Still running/queued, wait a bit
            await asyncio.sleep(1.0)
            
    except ImportError:
        return CloudTaskResult(
            success=False,
            error_message="AWS Braket SDK not available"
        )
    except Exception as e:
        total_time_ms = int((time.time() - start_time) * 1000)
        return CloudTaskResult(
            success=False,
            error_message=f"Cloud execution error: {str(e)}",
            total_time_ms=total_time_ms
        )

def create_cloud_telemetry(
    result: CloudTaskResult,
    execution_mode: str,
    shot_count: int
) -> CloudTelemetry:
    """Create telemetry data from cloud execution result"""
    return CloudTelemetry(
        cloud_region="us-east-1",  # TODO: Get from manager
        device_arn=result.device_arn or "",
        task_arn=result.task_arn or "",
        queue_latency_ms=result.queue_time_ms or 0,
        cloud_execution_latency_ms=result.execution_time_ms or 0,
        total_cloud_latency_ms=result.total_time_ms or 0,
        shot_count=shot_count,
        execution_mode=execution_mode
    )

def validate_cloud_request(
    execution_mode: str,
    device: str,
    shots: int,
    region: str
) -> Tuple[bool, str]:
    """
    Validate cloud execution request against safety limits.
    Returns (is_valid, error_message)
    """
    if execution_mode not in ["cloud_simulator", "cloud_qpu"]:
        return False, f"Invalid execution mode: {execution_mode}"
    
    if execution_mode == "cloud_qpu":
        # QPU mode requires explicit enable flag (not implemented yet)
        return False, "QPU execution not enabled"
    
    if device not in BRAKET_CLOUD_DEVICES:
        return False, f"Unknown device: {device}"
    
    if shots > MAX_CLOUD_SHOTS:
        return False, f"Shots {shots} exceeds maximum {MAX_CLOUD_SHOTS}"
    
    if region not in SUPPORTED_REGIONS:
        return False, f"Unsupported region: {region}"
    
    return True, ""

def check_cloud_availability() -> Dict[str, bool]:
    """Check availability of cloud execution components"""
    return {
        "aws_credentials": BraketCloudManager().check_credentials_available(),
        "braket_sdk": _check_braket_sdk(),
        "supported_regions": len(SUPPORTED_REGIONS) > 0,
        "device_registry": len(BRAKET_CLOUD_DEVICES) > 0
    }

def _check_braket_sdk() -> bool:
    """Check if Braket SDK is available"""
    try:
        import braket
        return True
    except ImportError:
        return False
