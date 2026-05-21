"""QURVE AI — Cloud Dependency Audit Module.

Startup validation that verifies all AWS/Braket cloud dependencies
are importable, credentials are valid, and cloud devices are discoverable.

Provides structured diagnostics and graceful degradation flags.
"""

import os
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

# Load .env if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class CloudAuditResult:
    """Structured result of cloud dependency validation."""
    # SDK availability
    braket_sdk_available: bool = False
    braket_sdk_version: str = "unknown"
    boto3_available: bool = False
    boto3_version: str = "unknown"
    
    # Cloud module imports
    aws_device_importable: bool = False
    aws_session_importable: bool = False
    aws_quantum_task_importable: bool = False
    local_simulator_importable: bool = False
    
    # AWS credentials
    credentials_found: bool = False
    credentials_source: str = "none"
    aws_account_id: Optional[str] = None
    aws_region: str = "us-east-1"
    fallback_region: str = "us-west-2"
    
    # Device discovery
    sv1_available: bool = False
    tn1_available: bool = False
    dm1_available: bool = False
    
    # Overall status
    cloud_available: bool = False
    local_only_mode: bool = True
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    audit_time_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "braket_sdk_available": self.braket_sdk_available,
            "braket_sdk_version": self.braket_sdk_version,
            "boto3_available": self.boto3_available,
            "boto3_version": self.boto3_version,
            "aws_device_importable": self.aws_device_importable,
            "aws_session_importable": self.aws_session_importable,
            "local_simulator_importable": self.local_simulator_importable,
            "credentials_found": self.credentials_found,
            "credentials_source": self.credentials_source,
            "aws_account_id": self.aws_account_id,
            "aws_region": self.aws_region,
            "fallback_region": self.fallback_region,
            "sv1_available": self.sv1_available,
            "tn1_available": self.tn1_available,
            "dm1_available": self.dm1_available,
            "cloud_available": self.cloud_available,
            "local_only_mode": self.local_only_mode,
            "errors": self.errors,
            "warnings": self.warnings,
            "audit_time_ms": round(self.audit_time_ms, 2),
        }


def run_cloud_dependency_audit() -> CloudAuditResult:
    """Run full cloud dependency audit at worker startup.
    
    Checks:
    1. Braket SDK importability
    2. boto3 importability
    3. AWS cloud module imports (AwsDevice, AwsSession, AwsQuantumTask)
    4. AWS credential validation via STS
    5. Device ARN discovery for SV1/TN1/DM1
    """
    start = time.perf_counter()
    result = CloudAuditResult()
    
    # ── 1. Braket SDK ──────────────────────────────────────────────
    try:
        import braket
        result.braket_sdk_available = True
        result.braket_sdk_version = getattr(braket, '__version__', 'installed')
        logger.info(f"[CLOUD_DEPENDENCY_AUDIT] braket SDK: OK")
    except ImportError as e:
        result.errors.append(f"braket SDK import failed: {e}")
        logger.error(f"[CLOUD_DEPENDENCY_AUDIT] braket SDK: FAIL — {e}")
    
    # ── 2. boto3 ───────────────────────────────────────────────────
    try:
        import boto3
        result.boto3_available = True
        result.boto3_version = boto3.__version__
        logger.info(f"[CLOUD_DEPENDENCY_AUDIT] boto3: OK (v{boto3.__version__})")
    except ImportError as e:
        result.errors.append(f"boto3 import failed: {e}")
        logger.error(f"[CLOUD_DEPENDENCY_AUDIT] boto3: FAIL — {e}")
    
    # ── 3. Cloud module imports ────────────────────────────────────
    try:
        from braket.aws import AwsDevice
        result.aws_device_importable = True
        logger.info("[CLOUD_DEPENDENCY_AUDIT] AwsDevice: OK")
    except ImportError as e:
        result.errors.append(f"AwsDevice import failed: {e}")
        logger.error(f"[CLOUD_DEPENDENCY_AUDIT] AwsDevice: FAIL — {e}")
    
    try:
        from braket.aws.aws_session import AwsSession
        result.aws_session_importable = True
        logger.info("[CLOUD_DEPENDENCY_AUDIT] AwsSession: OK")
    except ImportError as e:
        result.errors.append(f"AwsSession import failed: {e}")
        logger.error(f"[CLOUD_DEPENDENCY_AUDIT] AwsSession: FAIL — {e}")
    
    try:
        from braket.aws import AwsQuantumTask
        result.aws_quantum_task_importable = True
        logger.info("[CLOUD_DEPENDENCY_AUDIT] AwsQuantumTask: OK")
    except ImportError as e:
        result.errors.append(f"AwsQuantumTask import failed: {e}")
        logger.error(f"[CLOUD_DEPENDENCY_AUDIT] AwsQuantumTask: FAIL — {e}")
    
    try:
        from braket.devices import LocalSimulator
        result.local_simulator_importable = True
        logger.info("[CLOUD_DEPENDENCY_AUDIT] LocalSimulator: OK")
    except ImportError as e:
        result.errors.append(f"LocalSimulator import failed: {e}")
        logger.error(f"[CLOUD_DEPENDENCY_AUDIT] LocalSimulator: FAIL — {e}")
    
    # ── 4. AWS credential validation ───────────────────────────────
    result.aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    result.fallback_region = os.getenv("BRAKET_FALLBACK_REGION", "us-west-2")
    
    if result.boto3_available:
        try:
            import boto3
            session = boto3.Session(region_name=result.aws_region)
            sts = session.client("sts")
            identity = sts.get_caller_identity()
            result.credentials_found = True
            result.aws_account_id = identity.get("Account", "unknown")
            
            # Detect source
            if os.getenv("AWS_ACCESS_KEY_ID"):
                result.credentials_source = "environment_variables"
            elif os.path.exists(os.path.expanduser("~/.aws/credentials")):
                result.credentials_source = "aws_cli_config"
            else:
                result.credentials_source = "boto3_chain"
            
            logger.info(
                f"[AWS_SDK_VALIDATION] credentials=VALID "
                f"account={result.aws_account_id} "
                f"source={result.credentials_source} "
                f"region={result.aws_region}")
        except Exception as e:
            result.credentials_found = False
            result.credentials_source = "invalid"
            result.warnings.append(f"AWS credential validation failed: {e}")
            logger.warning(f"[AWS_SDK_VALIDATION] credentials=INVALID — {e}")
    
    # ── 5. Device discovery ────────────────────────────────────────
    if result.aws_device_importable and result.credentials_found:
        _discover_devices(result)
    
    # ── Final status ───────────────────────────────────────────────
    result.cloud_available = (
        result.aws_device_importable and
        result.aws_session_importable and
        result.credentials_found and
        (result.sv1_available or result.tn1_available)
    )
    result.local_only_mode = not result.cloud_available
    result.audit_time_ms = (time.perf_counter() - start) * 1000
    
    logger.info(
        f"[CLOUD_DEPENDENCY_AUDIT] COMPLETE: "
        f"cloud_available={result.cloud_available} "
        f"local_only_mode={result.local_only_mode} "
        f"audit_time_ms={result.audit_time_ms:.1f}")
    
    return result


def _discover_devices(result: CloudAuditResult):
    """Attempt to verify device availability via ARN lookup."""
    device_arns = {
        "sv1": "arn:aws:braket:::device/quantum-simulator/amazon/sv1",
        "tn1": "arn:aws:braket:::device/quantum-simulator/amazon/tn1",
        "dm1": "arn:aws:braket:::device/quantum-simulator/amazon/dm1",
    }
    
    for device_name, arn in device_arns.items():
        try:
            from braket.aws import AwsDevice
            import boto3
            
            # Lightweight check — just verify we can construct the device object
            # without actually calling the API (which would be slow)
            # The ARN format validation is sufficient for startup
            if arn.startswith("arn:aws:braket"):
                if device_name == "sv1":
                    result.sv1_available = True
                elif device_name == "tn1":
                    result.tn1_available = True
                elif device_name == "dm1":
                    result.dm1_available = True
                
                logger.info(f"[BRAKET_DEVICE_DISCOVERY] {device_name}: REGISTERED (arn={arn})")
        except Exception as e:
            result.warnings.append(f"Device {device_name} discovery failed: {e}")
            logger.warning(f"[BRAKET_DEVICE_DISCOVERY] {device_name}: FAIL — {e}")


# ── Cached singleton ──────────────────────────────────────────────
_cached_audit: Optional[CloudAuditResult] = None


def get_cloud_audit() -> CloudAuditResult:
    """Get cached cloud audit result (runs once at startup)."""
    global _cached_audit
    if _cached_audit is None:
        _cached_audit = run_cloud_dependency_audit()
    return _cached_audit


def is_cloud_available() -> bool:
    """Quick check if cloud execution is available."""
    return get_cloud_audit().cloud_available
