"""
Qurve AI - AWS Session Management for Braket Worker
Handles AWS authentication, session management, and device access
"""

import os
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError
except ImportError:
    boto3 = None
    ClientError = Exception
    NoCredentialsError = Exception

logger = logging.getLogger(__name__)

@dataclass
class AwsSession:
    """AWS session management for Braket worker."""
    region_name: str
    device_arn: Optional[str] = None
    session_available: bool = False
    credentials_source: str = "unknown"
    error_message: Optional[str] = None

class BraketAwsSession:
    """
    AWS session manager for Braket cloud execution.
    
    Features:
    - Environment variable support
    - AWS CLI credential loading
    - .aws/config file support
    - Region validation
    - Device ARN validation
    - Safe credential handling
    """
    
    def __init__(self, region_name: str = "us-east-1"):
        self.region_name = region_name
        self.session = None
        self.device_arn = None
        self.logger = logging.getLogger(__name__)
        
        self.logger.info(f"[AWS_SESSION] Initialized for region: {region_name}")
    
    def get_session(self) -> Optional[AwsSession]:
        """Get or create AWS session."""
        if self.session is not None:
            return self._create_session_info()
        
        try:
            # Create boto3 session with automatic credential loading
            session = boto3.Session(
                region_name=self.region_name,
                profile_name=os.getenv('AWS_PROFILE')
            )
            
            # Test credentials
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            self.session = session
            self.logger.info(f"[AWS_SESSION] Session created for account: {identity.get('Account')}")
            
            return self._create_session_info()
            
        except NoCredentialsError as e:
            self.logger.error(f"[AWS_SESSION] No AWS credentials found: {e}")
            return AwsSession(
                region_name=self.region_name,
                session_available=False,
                credentials_source="none",
                error_message=str(e)
            )
        except Exception as e:
            self.logger.error(f"[AWS_SESSION] AWS session creation failed: {e}")
            return AwsSession(
                region_name=self.region_name,
                session_available=False,
                credentials_source="error",
                error_message=str(e)
            )
    
    def _create_session_info(self) -> AwsSession:
        """Create session info object."""
        return AwsSession(
            region_name=self.region_name,
            device_arn=self.device_arn,
            session_available=True,
            credentials_source=self._detect_credentials_source(),
            error_message=None
        )
    
    def _detect_credentials_source(self) -> str:
        """Detect AWS credentials source."""
        sources = []
        
        # Check environment variables
        if os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY'):
            sources.append("environment_variables")
        
        # Check AWS CLI credentials
        if os.path.exists(os.path.expanduser('~/.aws/credentials')):
            sources.append("aws_cli")
        
        # Check AWS profile
        if os.getenv('AWS_PROFILE'):
            sources.append("aws_profile")
        
        if sources:
            return ",".join(sources)
        elif boto3 and hasattr(boto3.Session(), 'get_credentials'):
            return "boto3_chain"
        else:
            return "none"
    
    def set_device_arn(self, device_arn: str) -> bool:
        """Set device ARN for cloud execution."""
        try:
            # Validate device ARN format
            if not device_arn.startswith('arn:aws:braket:'):
                self.logger.error(f"[AWS_SESSION] Invalid device ARN format: {device_arn}")
                return False
            
            # Validate region matches
            arn_parts = device_arn.split(':')
            if len(arn_parts) >= 4 and arn_parts[3] != self.region_name:
                self.logger.error(f"[AWS_SESSION] Device ARN region mismatch: {device_arn} vs {self.region_name}")
                return False
            
            self.device_arn = device_arn
            self.logger.info(f"[AWS_SESSION] Device ARN set: {device_arn}")
            return True
            
        except Exception as e:
            self.logger.error(f"[AWS_SESSION] Error setting device ARN: {e}")
            return False
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get current device information."""
        return {
            "device_arn": self.device_arn,
            "region_name": self.region_name,
            "session_available": self.session is not None,
            "credentials_source": self._detect_credentials_source() if self.session else "none"
        }
    
    def validate_device_access(self, device_arn: str) -> Dict[str, Any]:
        """Validate device access and permissions."""
        if self.session is None:
            return {
                "access_valid": False,
                "error": "No AWS session available"
            }
        
        try:
            # Check if we can access the device
            braket = self.session.client('braket')
            
            # Get device information
            try:
                device_info = braket.get_device(device_arn)
                
                return {
                    "access_valid": True,
                    "device_info": {
                        "device_arn": device_info.device_arn,
                        "device_name": device_info.device_name,
                        "device_type": device_info.device_type,
                        "device_status": device_info.device_status,
                        "provider_name": device_info.provider_name
                    }
                }
                
            except ClientError as e:
                return {
                    "access_valid": False,
                    "error": f"Device access error: {str(e)}"
                }
                
        except Exception as e:
            return {
                "access_valid": False,
                "error": f"Validation error: {str(e)}"
            }


# Global session instance
_braket_session: Optional[BraketAwsSession] = None


def get_braket_session() -> BraketAwsSession:
    """Get the global Braket AWS session instance."""
    global _braket_session
    if _braket_session is None:
        _braket_session = BraketAwsSession()
    return _braket_session


def create_braket_session(region_name: str = "us-east-1") -> BraketAwsSession:
    """Create a new Braket AWS session."""
    return BraketAwsSession(region_name)
