"""
Enterprise-grade Security and Token Encryption for QUBO Portfolio Optimizer
Provides encrypted token storage, secure credential handling, and secret masking.
"""

import os
import json
import base64
import logging
import hashlib
from typing import Dict, Optional, Any, Tuple
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from dataclasses import dataclass, field
from pathlib import Path
import secrets

logger = logging.getLogger(__name__)


@dataclass
class CredentialInfo:
    """Information about stored credentials."""
    
    service: str
    encrypted_token: str
    created_at: str
    last_accessed: str
    access_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SecureCredentialManager:
    """
    Enterprise-grade credential management with encryption.
    
    Provides encrypted token storage, environment variable isolation,
    secret masking in logs, and secure credential rotation.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        self.storage_dir = storage_dir or Path.home() / ".qubo" / "credentials"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._credentials_file = self.storage_dir / "encrypted_credentials.json"
        self._key_file = self.storage_dir / "encryption.key"
        self._fernet: Optional[Fernet] = None
        self._credentials: Dict[str, CredentialInfo] = {}
        self._known_secrets: set = set()
        
        # Initialize encryption
        self._initialize_encryption()
        self._load_credentials()
    
    def _initialize_encryption(self) -> None:
        """Initialize or load encryption key."""
        try:
            if self._key_file.exists():
                # Load existing key
                with open(self._key_file, 'rb') as f:
                    key_data = f.read()
                    # Ensure key is properly base64 encoded
                    if isinstance(key_data, str):
                        key = key_data.encode()
                    else:
                        key = key_data
            else:
                # Generate new key
                key = Fernet.generate_key()
                with open(self._key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions
                os.chmod(self._key_file, 0o600)
            
            # Ensure key is valid Fernet key (32-byte base64url-safe encoded)
            if not isinstance(key, bytes):
                key = str(key).encode()
            
            # If key doesn't look like a proper Fernet key, derive one from it
            try:
                # Test if it's a valid Fernet key
                Fernet(key)
            except (ValueError, TypeError):
                # Derive a valid Fernet key from whatever we have
                key = base64.urlsafe_b64encode(hashlib.sha256(key).digest())
            
            self._fernet = Fernet(key)
            logger.info("Encryption initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            raise
    
    def _load_credentials(self) -> None:
        """Load encrypted credentials from storage."""
        if not self._credentials_file.exists():
            return
        
        try:
            with open(self._credentials_file, 'r') as f:
                encrypted_data = f.read()
            
            if not encrypted_data:
                return
            
            # Decrypt the data
            decrypted_data = self._fernet.decrypt(encrypted_data.encode()).decode()
            credentials_data = json.loads(decrypted_data)
            
            # Reconstruct CredentialInfo objects
            for service, cred_data in credentials_data.items():
                self._credentials[service] = CredentialInfo(**cred_data)
                self._known_secrets.add(cred_data['encrypted_token'])
            
            logger.info(f"Loaded {len(self._credentials)} encrypted credentials")
            
        except Exception as e:
            logger.error(f"Failed to load credentials: {e}")
            # Don't raise - continue with empty credentials
    
    def _save_credentials(self) -> None:
        """Save encrypted credentials to storage."""
        try:
            # Convert to serializable format
            credentials_data = {}
            for service, cred_info in self._credentials.items():
                credentials_data[service] = {
                    'service': cred_info.service,
                    'encrypted_token': cred_info.encrypted_token,
                    'created_at': cred_info.created_at,
                    'last_accessed': cred_info.last_accessed,
                    'access_count': cred_info.access_count,
                    'metadata': cred_info.metadata
                }
            
            # Encrypt and save
            json_data = json.dumps(credentials_data, indent=2)
            encrypted_data = self._fernet.encrypt(json_data.encode())
            
            with open(self._credentials_file, 'wb') as f:
                f.write(encrypted_data)
            
            # Set restrictive permissions
            os.chmod(self._credentials_file, 0o600)
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            raise
    
    def store_credential(self, 
                        service: str, 
                        token: str, 
                        metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Securely store a credential token.
        
        Args:
            service: Service name (e.g., 'dwave', 'ibm_quantum')
            token: Plain text token to encrypt and store
            metadata: Additional metadata about the credential
            
        Returns:
            True if stored successfully
        """
        try:
            if not self._fernet:
                logger.error("Encryption not initialized")
                return False
            
            # Encrypt the token
            encrypted_token = self._fernet.encrypt(token.encode()).decode()
            
            # Create credential info
            now = secrets.token_hex(8)  # Simple timestamp replacement
            cred_info = CredentialInfo(
                service=service,
                encrypted_token=encrypted_token,
                created_at=now,
                last_accessed=now,
                metadata=metadata or {}
            )
            
            # Store in memory and save
            self._credentials[service] = cred_info
            self._known_secrets.add(encrypted_token)
            self._save_credentials()
            
            logger.info(f"Stored encrypted credential for service: {service}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store credential for {service}: {e}")
            return False
    
    def retrieve_credential(self, service: str) -> Optional[str]:
        """
        Retrieve and decrypt a credential token.
        
        Args:
            service: Service name
            
        Returns:
            Decrypted token or None if not found
        """
        try:
            if not self._fernet:
                logger.error("Encryption not initialized")
                return None
            
            if service not in self._credentials:
                logger.warning(f"No credential found for service: {service}")
                return None
            
            cred_info = self._credentials[service]
            
            # Decrypt the token
            decrypted_token = self._fernet.decrypt(cred_info.encrypted_token.encode()).decode()
            
            # Update access metadata
            cred_info.last_accessed = secrets.token_hex(8)
            cred_info.access_count += 1
            self._save_credentials()
            
            logger.debug(f"Retrieved credential for service: {service}")
            return decrypted_token
            
        except Exception as e:
            logger.error(f"Failed to retrieve credential for {service}: {e}")
            return None
    
    def delete_credential(self, service: str) -> bool:
        """
        Delete a stored credential.
        
        Args:
            service: Service name
            
        Returns:
            True if deleted successfully
        """
        try:
            if service in self._credentials:
                del self._credentials[service]
                self._save_credentials()
                logger.info(f"Deleted credential for service: {service}")
                return True
            else:
                logger.warning(f"No credential found to delete for service: {service}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete credential for {service}: {e}")
            return False
    
    def list_services(self) -> list[str]:
        """List all services with stored credentials."""
        return list(self._credentials.keys())
    
    def rotate_credential(self, service: str, new_token: str) -> bool:
        """
        Rotate an existing credential with a new token.
        
        Args:
            service: Service name
            new_token: New token to replace the old one
            
        Returns:
            True if rotated successfully
        """
        try:
            if service in self._credentials:
                # Preserve metadata
                old_metadata = self._credentials[service].metadata
                return self.store_credential(service, new_token, old_metadata)
            else:
                logger.warning(f"Cannot rotate non-existent credential for service: {service}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to rotate credential for {service}: {e}")
            return False
    
    def mask_secrets_in_text(self, text: str) -> str:
        """
        Mask known secrets in log text.
        
        Args:
            text: Text that may contain secrets
            
        Returns:
            Text with secrets masked
        """
        masked_text = text
        
        # Mask encrypted tokens
        for secret in self._known_secrets:
            if secret in masked_text:
                masked_text = masked_text.replace(secret, "[REDACTED_TOKEN]")
        
        # Mask environment variables
        env_secrets = [
            os.getenv("DWAVE_API_TOKEN", ""),
            os.getenv("IBM_QUANTUM_TOKEN", ""),
            os.getenv("AWS_ACCESS_KEY_ID", ""),
            os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        ]
        
        for secret in env_secrets:
            if secret and secret in masked_text:
                masked_text = masked_text.replace(secret, "[REDACTED_ENV]")
        
        return masked_text
    
    def validate_credential_strength(self, token: str) -> Tuple[bool, str]:
        """
        Validate the strength of a credential token.
        
        Args:
            token: Token to validate
            
        Returns:
            Tuple of (is_valid, validation_message)
        """
        if not token:
            return False, "Token cannot be empty"
        
        if len(token) < 16:
            return False, "Token too short (minimum 16 characters)"
        
        if token in ["password", "123456", "admin", "token"]:
            return False, "Token is too common/insecure"
        
        # Check for basic entropy (simplified)
        unique_chars = len(set(token))
        if unique_chars < len(token) * 0.3:
            return False, "Token has insufficient entropy"
        
        return True, "Token appears to have sufficient strength"
    
    def get_credential_info(self, service: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about a stored credential without exposing the token.
        
        Args:
            service: Service name
            
        Returns:
            Credential metadata or None if not found
        """
        if service not in self._credentials:
            return None
        
        cred_info = self._credentials[service]
        return {
            'service': cred_info.service,
            'created_at': cred_info.created_at,
            'last_accessed': cred_info.last_accessed,
            'access_count': cred_info.access_count,
            'metadata': cred_info.metadata,
            'has_token': True  # Existence check without exposing token
        }
    
    def export_credentials_backup(self, backup_path: Path) -> bool:
        """
        Export encrypted credentials backup.
        
        Args:
            backup_path: Path to save backup file
            
        Returns:
            True if backup created successfully
        """
        try:
            if self._credentials_file.exists():
                import shutil
                shutil.copy2(self._credentials_file, backup_path)
                os.chmod(backup_path, 0o600)
                logger.info(f"Credentials backup exported to: {backup_path}")
                return True
            else:
                logger.warning("No credentials file to backup")
                return False
                
        except Exception as e:
            logger.error(f"Failed to export credentials backup: {e}")
            return False


# Global credential manager instance
CREDENTIAL_MANAGER = SecureCredentialManager()


def get_secure_token(service: str) -> Optional[str]:
    """
    Convenience function to get a secure token for a service.
    
    Args:
        service: Service name
        
    Returns:
        Decrypted token or None if not found
    """
    return CREDENTIAL_MANAGER.retrieve_credential(service)


def store_secure_token(service: str, token: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Convenience function to store a secure token for a service.
    
    Args:
        service: Service name
        token: Token to encrypt and store
        metadata: Additional metadata
        
    Returns:
        True if stored successfully
    """
    return CREDENTIAL_MANAGER.store_credential(service, token, metadata)


def mask_secrets(text: str) -> str:
    """
    Convenience function to mask secrets in text.
    
    Args:
        text: Text that may contain secrets
        
    Returns:
        Text with secrets masked
    """
    return CREDENTIAL_MANAGER.mask_secrets_in_text(text)
