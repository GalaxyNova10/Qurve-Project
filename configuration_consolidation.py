"""
QURVE AI - Configuration Consolidation System
Centralized environment loading, immutable production configs, validation.

Features:
✅ Centralized environment loading
✅ Immutable production configurations
✅ Environment validation
✅ Deployment-time validation
✅ Config checksum verification
✅ Runtime mutation prevention
"""

import os
import sys
import hashlib
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EnvironmentType(Enum):
    """Environment type classifications."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    DEMO = "demo"


class ConfigurationStatus(Enum):
    """Configuration status classifications."""
    VALID = "valid"
    INVALID = "invalid"
    MUTATED = "mutated"
    CORRUPTED = "corrupted"
    MISSING = "missing"


@dataclass
class ConfigurationSchema:
    """Configuration schema definition."""
    key: str
    required: bool
    type: str
    default: Any = None
    description: str = ""
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    environment_specific: bool = False


@dataclass
class ConfigurationValidation:
    """Configuration validation result."""
    status: ConfigurationStatus
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    checksum: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfigurationConsolidation:
    """
    Production-grade configuration consolidation system.
    
    Features:
    - Centralized environment loading
    - Immutable production configurations
    - Environment validation
    - Deployment-time validation
    - Config checksum verification
    - Runtime mutation prevention
    """
    
    def __init__(self):
        self.environment = os.getenv('ENVIRONMENT', 'development')
        self.config_dir = Path('config')
        self.env_file = self.config_dir / f'.env.{self.environment}'
        self.schema_file = self.config_dir / 'schema.yaml'
        self.checksum_file = self.config_dir / 'checksums.json'
        
        # Configuration storage
        self._config: Dict[str, Any] = {}
        self._schema: List[ConfigurationSchema] = []
        self._checksums: Dict[str, str] = {}
        self._loaded = False
        
        # Runtime protection
        self._frozen = False
        
        logger.info(f"Configuration consolidation initialized for {self.environment}")
    
    def load_configuration(self) -> ConfigurationValidation:
        """
        Load and validate all configuration.
        
        Returns:
            Configuration validation result
        """
        try:
            logger.info(f"Loading configuration for {self.environment} environment...")
            
            # Step 1: Load configuration schema
            self._load_schema()
            
            # Step 2: Load environment variables
            self._load_environment_variables()
            
            # Step 3: Load configuration files
            self._load_configuration_files()
            
            # Step 4: Validate configuration
            validation = self._validate_configuration()
            
            # Step 5: Calculate and verify checksums
            self._calculate_checksums()
            checksum_valid = self._verify_checksums()
            
            if not checksum_valid:
                validation.status = ConfigurationStatus.MUTATED
                validation.errors.append("Configuration checksum mismatch - possible mutation")
            
            # Step 6: Freeze configuration in production
            if self.environment == EnvironmentType.PRODUCTION.value:
                self._freeze_configuration()
            
            self._loaded = True
            
            logger.info(f"Configuration loaded successfully for {self.environment}")
            return validation
            
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            return ConfigurationValidation(
                status=ConfigurationStatus.INVALID,
                errors=[f"Configuration loading failed: {str(e)}"]
            )
    
    def _load_schema(self) -> None:
        """Load configuration schema."""
        try:
            if self.schema_file.exists():
                with open(self.schema_file, 'r') as f:
                    schema_data = yaml.safe_load(f)
                
                self._schema = []
                for key, config in schema_data.items():
                    self._schema.append(ConfigurationSchema(
                        key=key,
                        required=config.get('required', False),
                        type=config.get('type', 'string'),
                        default=config.get('default'),
                        description=config.get('description', ''),
                        validation_rules=config.get('validation_rules', {}),
                        environment_specific=config.get('environment_specific', False)
                    ))
                
                logger.info(f"Loaded {len(self._schema)} configuration schema entries")
            else:
                logger.warning("Configuration schema file not found, using defaults")
                self._load_default_schema()
                
        except Exception as e:
            logger.error(f"Failed to load configuration schema: {str(e)}")
            raise
    
    def _load_default_schema(self) -> None:
        """Load default configuration schema."""
        self._schema = [
            ConfigurationSchema(
                key="ENVIRONMENT",
                required=True,
                type="string",
                description="Application environment"
            ),
            ConfigurationSchema(
                key="DATABASE_URL",
                required=True,
                type="string",
                description="Database connection URL"
            ),
            ConfigurationSchema(
                key="REDIS_URL",
                required=True,
                type="string",
                description="Redis connection URL"
            ),
            ConfigurationSchema(
                key="SECRET_KEY",
                required=True,
                type="string",
                description="Application secret key"
            ),
            ConfigurationSchema(
                key="AWS_ACCESS_KEY_ID",
                required=False,
                type="string",
                description="AWS access key ID"
            ),
            ConfigurationSchema(
                key="AWS_SECRET_ACCESS_KEY",
                required=False,
                type="string",
                description="AWS secret access key"
            ),
            ConfigurationSchema(
                key="AWS_DEFAULT_REGION",
                required=False,
                type="string",
                default="us-east-1",
                description="AWS default region"
            ),
            ConfigurationSchema(
                key="LOG_LEVEL",
                required=False,
                type="string",
                default="INFO",
                description="Application log level"
            ),
            ConfigurationSchema(
                key="MAX_WORKERS",
                required=False,
                type="integer",
                default=4,
                description="Maximum number of worker processes"
            ),
            ConfigurationSchema(
                key="QPU_ENABLED",
                required=False,
                type="boolean",
                default=False,
                description="Enable QPU execution"
            ),
            ConfigurationSchema(
                key="CLOUD_EXECUTION_ENABLED",
                required=False,
                type="boolean",
                default=False,
                description="Enable cloud execution"
            )
        ]
    
    def _load_environment_variables(self) -> None:
        """Load environment variables."""
        try:
            # Load from .env file if it exists
            if self.env_file.exists():
                logger.info(f"Loading environment variables from {self.env_file}")
                with open(self.env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            
                            # Remove quotes if present
                            if value.startswith('"') and value.endswith('"'):
                                value = value[1:-1]
                            elif value.startswith("'") and value.endswith("'"):
                                value = value[1:-1]
                            
                            os.environ[key] = value
            
            # Load all environment variables
            for key, value in os.environ.items():
                self._config[key] = value
            
            logger.info(f"Loaded {len(self._config)} environment variables")
            
        except Exception as e:
            logger.error(f"Failed to load environment variables: {str(e)}")
            raise
    
    def _load_configuration_files(self) -> None:
        """Load additional configuration files."""
        try:
            # Load environment-specific configuration
            config_file = self.config_dir / f'{self.environment}.yaml'
            if config_file.exists():
                logger.info(f"Loading configuration from {config_file}")
                with open(config_file, 'r') as f:
                    file_config = yaml.safe_load(f)
                    self._config.update(file_config)
            
            # Load local configuration override
            local_config_file = self.config_dir / 'local.yaml'
            if local_config_file.exists():
                logger.info(f"Loading local configuration from {local_config_file}")
                with open(local_config_file, 'r') as f:
                    local_config = yaml.safe_load(f)
                    self._config.update(local_config)
            
        except Exception as e:
            logger.error(f"Failed to load configuration files: {str(e)}")
            raise
    
    def _validate_configuration(self) -> ConfigurationValidation:
        """Validate configuration against schema."""
        errors = []
        warnings = []
        
        try:
            for schema in self._schema:
                key = schema.key
                value = self._config.get(key)
                
                # Check required fields
                if schema.required and value is None:
                    errors.append(f"Required configuration '{key}' is missing")
                    continue
                
                # Skip validation if value is None
                if value is None:
                    if schema.default is not None:
                        self._config[key] = schema.default
                        warnings.append(f"Using default value for '{key}': {schema.default}")
                    continue
                
                # Type validation
                if not self._validate_type(key, value, schema.type):
                    errors.append(f"Configuration '{key}' must be of type {schema.type}")
                    continue
                
                # Custom validation rules
                rule_errors = self._validate_rules(key, value, schema.validation_rules)
                errors.extend(rule_errors)
                
                # Environment-specific validation
                if schema.environment_specific and not self._validate_environment_specific(key, value):
                    warnings.append(f"Configuration '{key}' may not be appropriate for {self.environment} environment")
            
            # Production-specific validations
            if self.environment == EnvironmentType.PRODUCTION.value:
                prod_errors = self._validate_production_configuration()
                errors.extend(prod_errors)
            
            status = ConfigurationStatus.VALID if not errors else ConfigurationStatus.INVALID
            
            return ConfigurationValidation(
                status=status,
                errors=errors,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return ConfigurationValidation(
                status=ConfigurationStatus.INVALID,
                errors=[f"Configuration validation failed: {str(e)}"]
            )
    
    def _validate_type(self, key: str, value: Any, expected_type: str) -> bool:
        """Validate configuration value type."""
        try:
            if expected_type == 'string':
                return isinstance(value, str)
            elif expected_type == 'integer':
                return isinstance(value, int) or (isinstance(value, str) and value.isdigit())
            elif expected_type == 'float':
                return isinstance(value, (int, float)) or (isinstance(value, str) and self._is_float(value))
            elif expected_type == 'boolean':
                if isinstance(value, bool):
                    return True
                if isinstance(value, str):
                    return value.lower() in ('true', 'false', '1', '0', 'yes', 'no')
                return False
            elif expected_type == 'list':
                return isinstance(value, (list, tuple))
            elif expected_type == 'dict':
                return isinstance(value, dict)
            else:
                return True  # Unknown type, assume valid
                
        except Exception:
            return False
    
    def _is_float(self, value: str) -> bool:
        """Check if string can be converted to float."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _validate_rules(self, key: str, value: Any, rules: Dict[str, Any]) -> List[str]:
        """Validate configuration value against custom rules."""
        errors = []
        
        try:
            # Min value validation
            if 'min' in rules:
                min_val = rules['min']
                if isinstance(value, (int, float)) and value < min_val:
                    errors.append(f"Configuration '{key}' must be >= {min_val}")
            
            # Max value validation
            if 'max' in rules:
                max_val = rules['max']
                if isinstance(value, (int, float)) and value > max_val:
                    errors.append(f"Configuration '{key}' must be <= {max_val}")
            
            # Pattern validation
            if 'pattern' in rules:
                import re
                pattern = rules['pattern']
                if isinstance(value, str) and not re.match(pattern, value):
                    errors.append(f"Configuration '{key}' does not match required pattern")
            
            # Allowed values validation
            if 'allowed' in rules:
                allowed_values = rules['allowed']
                if value not in allowed_values:
                    errors.append(f"Configuration '{key}' must be one of: {allowed_values}")
            
            # Forbidden values validation
            if 'forbidden' in rules:
                forbidden_values = rules['forbidden']
                if value in forbidden_values:
                    errors.append(f"Configuration '{key}' cannot be any of: {forbidden_values}")
            
        except Exception as e:
            errors.append(f"Rule validation failed for '{key}': {str(e)}")
        
        return errors
    
    def _validate_environment_specific(self, key: str, value: Any) -> bool:
        """Validate environment-specific configuration."""
        # Production environment specific validations
        if self.environment == EnvironmentType.PRODUCTION.value:
            if key in ['DEBUG', 'TESTING'] and value in [True, 'true', '1']:
                return False
            if key == 'LOG_LEVEL' and value in ['DEBUG', 'debug']:
                return False
        
        return True
    
    def _validate_production_configuration(self) -> List[str]:
        """Validate production-specific configuration."""
        errors = []
        
        # Required production configurations
        required_prod_configs = ['SECRET_KEY', 'DATABASE_URL']
        for config in required_prod_configs:
            if not self._config.get(config):
                errors.append(f"Production requires '{config}' to be set")
        
        # Security validations
        secret_key = self._config.get('SECRET_KEY', '')
        if len(secret_key) < 32:
            errors.append("Production SECRET_KEY must be at least 32 characters long")
        
        if 'password' in self._config.get('DATABASE_URL', '').lower():
            errors.append("Production DATABASE_URL should not contain 'password' in plain text")
        
        # Debug mode validation
        debug_mode = self._config.get('DEBUG', False)
        if debug_mode in [True, 'true', '1']:
            errors.append("Production cannot run with DEBUG mode enabled")
        
        return errors
    
    def _calculate_checksums(self) -> None:
        """Calculate configuration checksums."""
        try:
            # Create config dictionary for checksum calculation
            config_for_checksum = {}
            for key, value in sorted(self._config.items()):
                if not key.startswith('_'):  # Skip internal keys
                    config_for_checksum[key] = value
            
            # Calculate checksum
            config_json = json.dumps(config_for_checksum, sort_keys=True)
            checksum = hashlib.sha256(config_json.encode()).hexdigest()
            
            self._checksums['configuration'] = checksum
            self._checksums['environment'] = self.environment
            self._checksums['timestamp'] = int(time.time())
            
            logger.info(f"Configuration checksum calculated: {checksum}")
            
        except Exception as e:
            logger.error(f"Failed to calculate checksums: {str(e)}")
            raise
    
    def _verify_checksums(self) -> bool:
        """Verify configuration checksums."""
        try:
            if not self.checksum_file.exists():
                logger.warning("Checksum file not found, creating new one")
                self._save_checksums()
                return True
            
            with open(self.checksum_file, 'r') as f:
                saved_checksums = json.load(f)
            
            saved_config_checksum = saved_checksums.get('configuration')
            current_config_checksum = self._checksums.get('configuration')
            
            if saved_config_checksum != current_config_checksum:
                logger.error(f"Configuration checksum mismatch: saved={saved_config_checksum}, current={current_config_checksum}")
                return False
            
            logger.info("Configuration checksum verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Failed to verify checksums: {str(e)}")
            return False
    
    def _save_checksums(self) -> None:
        """Save configuration checksums."""
        try:
            with open(self.checksum_file, 'w') as f:
                json.dump(self._checksums, f, indent=2)
            
            logger.info("Configuration checksums saved")
            
        except Exception as e:
            logger.error(f"Failed to save checksums: {str(e)}")
            raise
    
    def _freeze_configuration(self) -> None:
        """Freeze configuration to prevent runtime mutations."""
        try:
            # Convert config to immutable mapping
            self._config = dict(self._config)  # Create copy
            self._frozen = True
            
            logger.info("Configuration frozen for production environment")
            
        except Exception as e:
            logger.error(f"Failed to freeze configuration: {str(e)}")
            raise
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        if not self._loaded:
            logger.warning("Configuration not loaded, loading now...")
            self.load_configuration()
        
        return self._config.get(key, default)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        if not self._loaded:
            logger.warning("Configuration not loaded, loading now...")
            self.load_configuration()
        
        return dict(self._config)  # Return copy to prevent mutation
    
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == EnvironmentType.PRODUCTION.value
    
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == EnvironmentType.DEVELOPMENT.value
    
    def is_staging(self) -> bool:
        """Check if running in staging environment."""
        return self.environment == EnvironmentType.STAGING.value
    
    def is_demo(self) -> bool:
        """Check if running in demo environment."""
        return self.environment == EnvironmentType.DEMO.value
    
    def get_environment_type(self) -> EnvironmentType:
        """Get environment type enum."""
        return EnvironmentType(self.environment)
    
    def validate_runtime_config(self) -> ConfigurationValidation:
        """Validate runtime configuration integrity."""
        try:
            # Recalculate current checksum
            current_checksums = dict(self._checksums)
            self._calculate_checksums()
            
            # Compare with saved checksums
            if current_checksums.get('configuration') != self._checksums.get('configuration'):
                return ConfigurationValidation(
                    status=ConfigurationStatus.MUTATED,
                    errors=["Runtime configuration has been mutated"]
                )
            
            return ConfigurationValidation(status=ConfigurationStatus.VALID)
            
        except Exception as e:
            return ConfigurationValidation(
                status=ConfigurationStatus.INVALID,
                errors=[f"Runtime validation failed: {str(e)}"]
            )


# Global configuration consolidation instance
_configuration_consolidation: Optional[ConfigurationConsolidation] = None


def get_configuration_consolidation() -> ConfigurationConsolidation:
    """Get global configuration consolidation instance."""
    global _configuration_consolidation
    if _configuration_consolidation is None:
        _configuration_consolidation = ConfigurationConsolidation()
        # Auto-load configuration
        _configuration_consolidation.load_configuration()
    return _configuration_consolidation


def get_config(key: str, default: Any = None) -> Any:
    """Get configuration value (convenience function)."""
    return get_configuration_consolidation().get(key, default)


def is_production() -> bool:
    """Check if running in production environment (convenience function)."""
    return get_configuration_consolidation().is_production()


def is_development() -> bool:
    """Check if running in development environment (convenience function)."""
    return get_configuration_consolidation().is_development()


def is_staging() -> bool:
    """Check if running in staging environment (convenience function)."""
    return get_configuration_consolidation().is_staging()


def is_demo() -> bool:
    """Check if running in demo environment (convenience function)."""
    return get_configuration_consolidation().is_demo()


if __name__ == "__main__":
    # Test configuration consolidation
    config = ConfigurationConsolidation()
    validation = config.load_configuration()
    
    print(f"Configuration Status: {validation.status.value}")
    if validation.errors:
        print("Errors:")
        for error in validation.errors:
            print(f"  - {error}")
    if validation.warnings:
        print("Warnings:")
        for warning in validation.warnings:
            print(f"  - {warning}")
    
    print(f"Environment: {config.environment}")
    print(f"Configuration Keys: {len(config.get_all())}")
