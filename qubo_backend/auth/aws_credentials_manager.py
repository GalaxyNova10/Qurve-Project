"""
Qurve AI - AWS Credentials Manager
Production-grade AWS credential handling with complete isolation.

Principles:
✅ ISOLATED: Credential logic never touches execution
✅ SECURE: No secret leakage in logs or APIs
✅ RESILIENT: Graceful degradation on auth failures
✅ ROTATION-READY: Supports credential refresh
✅ ENVIRONMENT-SAFE: Works across deployment environments
"""

import os
import time
import asyncio
import boto3
from botocore.exceptions import ClientError, NoCredentialsError, CredentialRetrievalError
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List
from enum import Enum
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


class CredentialSource(Enum):
    """Credential source enumeration."""
    ENVIRONMENT = "environment"
    AWS_PROFILE = "aws_profile"
    IAM_ROLE = "iam_role"
    UNKNOWN = "unknown"


class CredentialStatus(Enum):
    """Credential status enumeration."""
    VALID = "valid"
    EXPIRING = "expiring"
    EXPIRED = "expired"
    INVALID = "invalid"
    UNAVAILABLE = "unavailable"


@dataclass
class CredentialInfo:
    """Credential information with metadata."""
    source: CredentialSource
    status: CredentialStatus
    region: str
    account_id: Optional[str] = None
    expiration_time: Optional[datetime] = None
    validation_latency_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    last_validation: datetime = field(default_factory=datetime.now)


@dataclass
class AuthTelemetry:
    """Authentication telemetry without secret leakage."""
    credential_source: CredentialSource
    validation_success: bool
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    aws_account_id: Optional[str] = None
    region: str = field(default_factory=lambda: "us-east-1")
    validation_latency_ms: float = field(default_factory=lambda: 0.0)
    timestamp: datetime = field(default_factory=datetime.now)


class AWSCredentialsManager:
    """
    Production-grade AWS credentials manager.
    
    Features:
    - Multiple credential sources with priority order
    - Automatic credential validation and refresh
    - Region policy enforcement
    - Safe failure handling with telemetry
    - Rate limiting and caching
    - No secret leakage in logs
    """
    
    def __init__(self):
        self.allowed_regions = {"us-east-1", "us-west-2"}
        self._credential_cache: Optional[CredentialInfo] = None
        self._cache_timestamp: Optional[float] = None
        self._cache_ttl = 300.0  # 5 minutes
        self._validation_cooldown = 30.0  # 30 seconds between validations
        self._last_validation: Optional[float] = None
        
        logger.info("AWS credentials manager initialized", 
                  allowed_regions=list(self.allowed_regions))
    
    async def get_credentials(self, region: str = "us-east-1") -> Tuple[bool, CredentialInfo]:
        """
        Get AWS credentials with validation.
        
        Priority order: environment → profile → IAM role
        
        Returns:
            (success: bool, credential_info: CredentialInfo)
        """
        try:
            # Validate region first
            if region not in self.allowed_regions:
                return False, CredentialInfo(
                    source=CredentialSource.UNKNOWN,
                    status=CredentialStatus.INVALID,
                    region=region,
                    last_validation=datetime.now(),
                    metadata={"error": "Unsupported region"}
                )
            
            # Check cache first
            if self._is_cache_valid():
                logger.debug("Using cached credentials", region=region)
                return True, self._credential_cache
            
            # Rate limiting
            if self._is_validation_cooldown():
                return False, CredentialInfo(
                    source=CredentialSource.UNKNOWN,
                    status=CredentialStatus.UNAVAILABLE,
                    region=region,
                    last_validation=datetime.now(),
                    metadata={"error": "Validation cooldown active"}
                )
            
            # Try credential sources in priority order
            success, credential_info = await self._try_environment_credentials(region)
            if not success:
                success, credential_info = await self._try_profile_credentials(region)
            if not success:
                success, credential_info = await self._try_iam_role_credentials(region)
            
            # Cache successful result
            if success:
                self._credential_cache = credential_info
                self._cache_timestamp = time.time()
                self._last_validation = time.time()
            
            return success, credential_info
            
        except Exception as e:
            logger.error("Unexpected error getting credentials", 
                        region=region, error=str(e))
            return False, CredentialInfo(
                source=CredentialSource.UNKNOWN,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                metadata={"error": f"Unexpected error: {str(e)}"}
            )
    
    async def _try_environment_credentials(self, region: str) -> Tuple[bool, CredentialInfo]:
        """Try environment variable credentials."""
        start_time = time.time()
        
        try:
            # Check for required environment variables
            access_key = os.getenv('AWS_ACCESS_KEY_ID')
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
            session_token = os.getenv('AWS_SESSION_TOKEN')
            
            if not access_key or not secret_key:
                return False, CredentialInfo(
                    source=CredentialSource.ENVIRONMENT,
                    status=CredentialStatus.UNAVAILABLE,
                    region=region,
                    last_validation=datetime.now(),
                    metadata={"error": "Missing environment variables"}
                )
            
            # Create session with environment credentials
            session = boto3.Session(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                aws_session_token=session_token,
                region_name=region
            )
            
            # Validate credentials
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            # Get account ID
            account_id = identity.get('Account', '')
            
            # Check expiration (if session token present)
            expiration_time = None
            if session_token:
                expiration_time = identity.get('Expiration')
            
            validation_latency = (time.time() - start_time) * 1000
            
            # Determine status
            status = CredentialStatus.VALID
            if expiration_time:
                time_until_expiry = expiration_time - datetime.now()
                if time_until_expiry.total_seconds() < 3600:  # Less than 1 hour
                    status = CredentialStatus.EXPIRING
            
            credential_info = CredentialInfo(
                source=CredentialSource.ENVIRONMENT,
                status=status,
                region=region,
                account_id=account_id,
                expiration_time=expiration_time,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"validation_method": "sts_get_caller_identity"}
            )
            
            # Emit telemetry
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.ENVIRONMENT,
                validation_success=True,
                validation_latency_ms=validation_latency,
                region=region,
                aws_account_id=account_id
            ))
            
            logger.info("Environment credentials validated", 
                       region=region, 
                       account_id=account_id,
                       status=status.value)
            
            return True, credential_info
            
        except (NoCredentialsError, CredentialRetrievalError) as e:
            validation_latency = (time.time() - start_time) * 1000
            
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.ENVIRONMENT,
                validation_success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                validation_latency_ms=validation_latency,
                region=region
            ))
            
            logger.warning("Environment credentials failed", 
                         region=region, 
                         error=str(e))
            
            return False, CredentialInfo(
                source=CredentialSource.ENVIRONMENT,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"error": str(e)}
            )
        
        except Exception as e:
            validation_latency = (time.time() - start_time) * 1000
            
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.ENVIRONMENT,
                validation_success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                validation_latency_ms=validation_latency,
                region=region
            ))
            
            logger.error("Unexpected error with environment credentials", 
                        region=region, error=str(e))
            
            return False, CredentialInfo(
                source=CredentialSource.ENVIRONMENT,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"error": f"Unexpected error: {str(e)}"}
            )
    
    async def _try_profile_credentials(self, region: str) -> Tuple[bool, CredentialInfo]:
        """Try AWS profile credentials."""
        start_time = time.time()
        
        try:
            # Check if profile is specified
            profile_name = os.getenv('AWS_PROFILE')
            if not profile_name:
                return False, CredentialInfo(
                    source=CredentialSource.AWS_PROFILE,
                    status=CredentialStatus.UNAVAILABLE,
                    region=region,
                    last_validation=datetime.now(),
                    metadata={"error": "No AWS profile specified"}
                )
            
            # Create session with profile
            session = boto3.Session(profile_name=profile_name, region_name=region)
            
            # Validate credentials
            sts = session.client('sts')
            identity = sts.get_caller_identity()
            
            account_id = identity.get('Account', '')
            
            validation_latency = (time.time() - start_time) * 1000
            
            credential_info = CredentialInfo(
                source=CredentialSource.AWS_PROFILE,
                status=CredentialStatus.VALID,
                region=region,
                account_id=account_id,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"profile_name": profile_name, "validation_method": "sts_get_caller_identity"}
            )
            
            # Emit telemetry
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.AWS_PROFILE,
                validation_success=True,
                validation_latency_ms=validation_latency,
                region=region,
                aws_account_id=account_id
            ))
            
            logger.info("AWS profile credentials validated", 
                       profile=profile_name,
                       region=region,
                       account_id=account_id)
            
            return True, credential_info
            
        except (NoCredentialsError, CredentialRetrievalError) as e:
            validation_latency = (time.time() - start_time) * 1000
            
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.AWS_PROFILE,
                validation_success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                validation_latency_ms=validation_latency,
                region=region
            ))
            
            logger.warning("AWS profile credentials failed", 
                         profile=profile_name,
                         region=region, 
                         error=str(e))
            
            return False, CredentialInfo(
                source=CredentialSource.AWS_PROFILE,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"profile_name": os.getenv('AWS_PROFILE', 'default'), "error": str(e)}
            )
        
        except Exception as e:
            validation_latency = (time.time() - start_time) * 1000
            
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.AWS_PROFILE,
                validation_success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                validation_latency_ms=validation_latency,
                region=region
            ))
            
            logger.error("Unexpected error with AWS profile credentials", 
                        profile=os.getenv('AWS_PROFILE', 'default'),
                        region=region, 
                        error=str(e))
            
            return False, CredentialInfo(
                source=CredentialSource.AWS_PROFILE,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"profile_name": os.getenv('AWS_PROFILE', 'default'), "error": f"Unexpected error: {str(e)}"}
            )
    
    async def _try_iam_role_credentials(self, region: str) -> Tuple[bool, CredentialInfo]:
        """Try IAM role credentials."""
        start_time = time.time()
        
        try:
            # Check if IAM role is configured
            role_arn = os.getenv('AWS_ROLE_ARN')
            if not role_arn:
                return False, CredentialInfo(
                    source=CredentialSource.IAM_ROLE,
                    status=CredentialStatus.UNAVAILABLE,
                    region=region,
                    last_validation=datetime.now(),
                    metadata={"error": "No IAM role ARN specified"}
                )
            
            # Create session with IAM role
            session = boto3.Session(region_name=region)
            
            # Validate IAM role
            sts = session.client('sts')
            identity = sts.assume_role(RoleArn=role_arn, RoleSessionName='quve-ai')
            
            account_id = identity.get('AssumedRoleUser', {}).get('Arn', '').split(':')[4]
            
            validation_latency = (time.time() - start_time) * 1000
            
            credential_info = CredentialInfo(
                source=CredentialSource.IAM_ROLE,
                status=CredentialStatus.VALID,
                region=region,
                account_id=account_id,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"role_arn": role_arn, "validation_method": "sts_assume_role"}
            )
            
            # Emit telemetry
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.IAM_ROLE,
                validation_success=True,
                validation_latency_ms=validation_latency,
                region=region,
                aws_account_id=account_id
            ))
            
            logger.info("IAM role credentials validated", 
                       role_arn=role_arn,
                       region=region,
                       account_id=account_id)
            
            return True, credential_info
            
        except (NoCredentialsError, CredentialRetrievalError, ClientError) as e:
            validation_latency = (time.time() - start_time) * 1000
            
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.IAM_ROLE,
                validation_success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                validation_latency_ms=validation_latency,
                region=region
            ))
            
            logger.warning("IAM role credentials failed", 
                         role_arn=os.getenv('AWS_ROLE_ARN', 'unknown'),
                         region=region, 
                         error=str(e))
            
            return False, CredentialInfo(
                source=CredentialSource.IAM_ROLE,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"role_arn": os.getenv('AWS_ROLE_ARN', 'unknown'), "error": str(e)}
            )
        
        except Exception as e:
            validation_latency = (time.time() - start_time) * 1000
            
            await self._emit_auth_telemetry(AuthTelemetry(
                credential_source=CredentialSource.IAM_ROLE,
                validation_success=False,
                error_type=type(e).__name__,
                error_message=str(e),
                validation_latency_ms=validation_latency,
                region=region
            ))
            
            logger.error("Unexpected error with IAM role credentials", 
                        role_arn=os.getenv('AWS_ROLE_ARN', 'unknown'),
                        region=region, 
                        error=str(e))
            
            return False, CredentialInfo(
                source=CredentialSource.IAM_ROLE,
                status=CredentialStatus.INVALID,
                region=region,
                last_validation=datetime.now(),
                validation_latency_ms=validation_latency,
                metadata={"role_arn": os.getenv('AWS_ROLE_ARN', 'unknown'), "error": f"Unexpected error: {str(e)}"}
            )
    
    def _is_cache_valid(self) -> bool:
        """Check if cached credentials are still valid."""
        if not self._credential_cache or not self._cache_timestamp:
            return False
        
        # Check if cache is expired
        if time.time() - self._cache_timestamp > self._cache_ttl:
            return False
        
        # Check if credentials are expired or invalid
        if self._credential_cache.status in [CredentialStatus.EXPIRED, CredentialStatus.INVALID]:
            return False
        
        return True
    
    def _is_validation_cooldown(self) -> bool:
        """Check if validation is in cooldown period."""
        if not self._last_validation:
            return False
        
        return time.time() - self._last_validation < self._validation_cooldown
    
    async def _emit_auth_telemetry(self, telemetry: AuthTelemetry) -> None:
        """Emit authentication telemetry without secret leakage."""
        try:
            # This would integrate with the monitoring system
            # For now, just log without secrets
            logger.info("Auth telemetry emitted", 
                       credential_source=telemetry.credential_source.value,
                       validation_success=telemetry.validation_success,
                       validation_latency_ms=telemetry.validation_latency_ms,
                       region=telemetry.region,
                       error_type=telemetry.error_type)
            
            # TODO: Integrate with monitoring service when available
            # monitoring_service = get_monitoring_service()
            # await monitoring_service.store_telemetry_event(...)
            
        except Exception as e:
            logger.error("Failed to emit auth telemetry", error=str(e))
    
    def get_session(self, region: str = "us-east-1") -> Optional[boto3.Session]:
        """
        Get boto3 session with credentials.
        
        Returns None if credentials are not available.
        """
        try:
            # This would use the cached credential info
            success, credential_info = asyncio.run(self.get_credentials(region))
            
            if not success:
                return None
            
            # Create session based on credential source
            if credential_info.source == CredentialSource.ENVIRONMENT:
                return boto3.Session(
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    aws_session_token=os.getenv('AWS_SESSION_TOKEN'),
                    region_name=region
                )
            elif credential_info.source == CredentialSource.AWS_PROFILE:
                return boto3.Session(
                    profile_name=os.getenv('AWS_PROFILE'),
                    region_name=region
                )
            elif credential_info.source == CredentialSource.IAM_ROLE:
                # For IAM role, we'd need to implement credential provider
                # This is complex and should be implemented carefully
                logger.warning("IAM role session creation not fully implemented")
                return None
            
            return None
            
        except Exception as e:
            logger.error("Failed to create session", region=region, error=str(e))
            return None
    
    async def validate_credentials(self, region: str = "us-east-1") -> CredentialInfo:
        """
        Validate credentials and return credential info.
        """
        success, credential_info = await self.get_credentials(region)
        return credential_info
    
    def get_allowed_regions(self) -> List[str]:
        """Get list of allowed AWS regions."""
        return list(self.allowed_regions)
    
    async def get_auth_health(self) -> Dict[str, Any]:
        """
        Get authentication system health status.
        """
        try:
            # Test each credential source
            env_valid, env_info = await self._try_environment_credentials("us-east-1")
            profile_valid, profile_info = await self._try_profile_credentials("us-east-1")
            iam_valid, iam_info = await self._try_iam_role_credentials("us-east-1")
            
            # Determine overall health
            any_valid = env_valid or profile_valid or iam_valid
            primary_source = None
            if env_valid:
                primary_source = CredentialSource.ENVIRONMENT
            elif profile_valid:
                primary_source = CredentialSource.AWS_PROFILE
            elif iam_valid:
                primary_source = CredentialSource.IAM_ROLE
            
            return {
                "status": "healthy" if any_valid else "unhealthy",
                "primary_source": primary_source.value if primary_source else "none",
                "credential_sources": {
                    "environment": {
                        "available": env_valid,
                        "status": env_info.status.value if env_valid else "unavailable",
                        "account_id": env_info.account_id if env_valid else None
                    },
                    "aws_profile": {
                        "available": profile_valid,
                        "status": profile_info.status.value if profile_valid else "unavailable",
                        "account_id": profile_info.account_id if profile_valid else None
                    },
                    "iam_role": {
                        "available": iam_valid,
                        "status": iam_info.status.value if iam_valid else "unavailable",
                        "account_id": iam_info.account_id if iam_valid else None
                    }
                },
                "allowed_regions": self.get_allowed_regions(),
                "cache_status": {
                    "cached": self._credential_cache is not None,
                    "valid": self._is_cache_valid(),
                    "timestamp": self._cache_timestamp
                }
            }
            
        except Exception as e:
            logger.error("Failed to get auth health", error=str(e))
            return {
                "status": "error",
                "error": str(e)
            }


# Global credential manager instance
_aws_credentials_manager: Optional[AWSCredentialsManager] = None


def get_aws_credentials_manager() -> AWSCredentialsManager:
    """Get global AWS credentials manager instance."""
    global _aws_credentials_manager
    if _aws_credentials_manager is None:
        _aws_credentials_manager = AWSCredentialsManager()
    return _aws_credentials_manager
