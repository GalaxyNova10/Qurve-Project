"""
Model Versioning & Registry for QUBO Portfolio Optimizer
Creates Bi-LSTM model lifecycle management system with version control,
model metadata tracking, automated deployment, rollback capabilities,
and performance comparison across versions.
"""

import asyncio
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from pathlib import Path
import uuid
import pickle
import numpy as np

from .config import get_settings
from .audit_logging import AUDIT_LOGGER
from .cache import CACHE_MANAGER

logger = logging.getLogger(__name__)


@dataclass
class ModelMetadata:
    """Metadata for a model version."""
    
    model_id: str
    model_name: str
    version: str
    model_type: str  # "bilstm", "transformer", "classical"
    created_at: datetime
    created_by: Optional[str] = None
    
    # Model architecture
    architecture: Dict[str, Any] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    input_features: List[str] = field(default_factory=list)
    output_features: List[str] = field(default_factory=list)
    
    # Training data
    training_dataset: Optional[str] = None
    training_samples: int = 0
    validation_samples: int = 0
    test_samples: int = 0
    training_duration_hours: float = 0.0
    
    # Performance metrics
    training_metrics: Dict[str, float] = field(default_factory=dict)
    validation_metrics: Dict[str, float] = field(default_factory=dict)
    test_metrics: Dict[str, float] = field(default_factory=dict)
    
    # Deployment info
    is_deployed: bool = False
    deployment_environment: Optional[str] = None
    deployment_timestamp: Optional[datetime] = None
    
    # File info
    model_file_path: Optional[str] = None
    model_size_mb: float = 0.0
    model_hash: Optional[str] = None
    
    # Status
    status: str = "created"  # created, training, trained, validated, deployed, deprecated
    parent_version: Optional[str] = None
    child_versions: List[str] = field(default_factory=list)
    
    # Tags and labels
    tags: List[str] = field(default_factory=list)
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat()
        if self.deployment_timestamp:
            data['deployment_timestamp'] = self.deployment_timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelMetadata':
        """Create from dictionary."""
        if 'created_at' in data:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'deployment_timestamp' in data and data['deployment_timestamp']:
            data['deployment_timestamp'] = datetime.fromisoformat(data['deployment_timestamp'])
        return cls(**data)


@dataclass
class ModelComparison:
    """Comparison between two model versions."""
    
    model_a_id: str
    model_b_id: str
    comparison_metrics: Dict[str, Dict[str, float]]  # metric -> {model_a_value, model_b_value}
    improvement_percentage: Dict[str, float]  # metric -> improvement %
    winner: str  # "model_a", "model_b", or "tie"
    comparison_timestamp: datetime = field(default_factory=datetime.now)


class ModelRegistry:
    """
    Bi-LSTM model lifecycle management system.
    
    Features:
    - Version control with parent-child relationships
    - Model metadata tracking and storage
    - Automated deployment and rollback
    - Performance comparison across versions
    - Model artifact management
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.models_dir = self.settings.output_dir / "models"
        self.models_dir.mkdir(parents=True, exist_ok=True)
        
        # Registry files
        self.registry_file = self.models_dir / "registry.json"
        self.comparisons_file = self.models_dir / "comparisons.json"
        
        # In-memory registry
        self._models: Dict[str, ModelMetadata] = {}
        self._comparisons: List[ModelComparison] = []
        
        # Load existing registry
        self._load_registry()
    
    def _load_registry(self) -> None:
        """Load existing model registry from storage."""
        try:
            # Load models
            if self.registry_file.exists():
                with open(self.registry_file, 'r') as f:
                    models_data = json.load(f)
                    
                for model_id, model_data in models_data.items():
                    self._models[model_id] = ModelMetadata.from_dict(model_data)
            
            # Load comparisons
            if self.comparisons_file.exists():
                with open(self.comparisons_file, 'r') as f:
                    comparisons_data = json.load(f)
                    
                for comp_data in comparisons_data:
                    comp_data['comparison_timestamp'] = datetime.fromisoformat(comp_data['comparison_timestamp'])
                    self._comparisons.append(ModelComparison(**comp_data))
            
            logger.info(f"Loaded {len(self._models)} models and {len(self._comparisons)} comparisons")
            
        except Exception as e:
            logger.error(f"Failed to load model registry: {e}")
            self._models = {}
            self._comparisons = []
    
    def _save_registry(self) -> None:
        """Save model registry to storage."""
        try:
            # Save models
            models_data = {}
            for model_id, metadata in self._models.items():
                models_data[model_id] = metadata.to_dict()
            
            with open(self.registry_file, 'w') as f:
                json.dump(models_data, f, indent=2)
            
            # Save comparisons
            comparisons_data = []
            for comparison in self._comparisons:
                comp_dict = asdict(comparison)
                comp_dict['comparison_timestamp'] = comparison.comparison_timestamp.isoformat()
                comparisons_data.append(comp_dict)
            
            with open(self.comparisons_file, 'w') as f:
                json.dump(comparisons_data, f, indent=2)
            
            logger.info("Model registry saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save model registry: {e}")
    
    async def register_model(self,
                            model_name: str,
                            version: str,
                            model_type: str,
                            architecture: Dict[str, Any],
                            hyperparameters: Dict[str, Any],
                            input_features: List[str],
                            output_features: List[str],
                            training_dataset: Optional[str] = None,
                            parent_version: Optional[str] = None,
                            created_by: Optional[str] = None,
                            tags: Optional[List[str]] = None,
                            description: str = "") -> str:
        """
        Register a new model version.
        
        Args:
            model_name: Name of the model
            version: Version string (semantic versioning)
            model_type: Type of model
            architecture: Model architecture details
            hyperparameters: Training hyperparameters
            input_features: List of input feature names
            output_features: List of output feature names
            training_dataset: Training dataset identifier
            parent_version: Parent model version
            created_by: Creator of the model
            tags: Model tags
            description: Model description
            
        Returns:
            Model ID for the registered model
        """
        model_id = str(uuid.uuid4())
        
        # Create metadata
        metadata = ModelMetadata(
            model_id=model_id,
            model_name=model_name,
            version=version,
            model_type=model_type,
            architecture=architecture,
            hyperparameters=hyperparameters,
            input_features=input_features,
            output_features=output_features,
            training_dataset=training_dataset,
            parent_version=parent_version,
            created_by=created_by,
            tags=tags or [],
            description=description
        )
        
        # Add to registry
        self._models[model_id] = metadata
        
        # Update parent-child relationships
        if parent_version:
            parent_metadata = self._models.get(parent_version)
            if parent_metadata:
                parent_metadata.child_versions.append(model_id)
        
        # Save registry
        self._save_registry()
        
        # Log model creation
        AUDIT_LOGGER.log_model_versioning(
            model_name=model_name,
            version=version,
            action="created",
            previous_version=parent_version,
            training_dataset=training_dataset,
            user_id=created_by
        )
        
        logger.info(f"Registered model {model_name} v{version} with ID {model_id}")
        return model_id
    
    async def save_model_artifact(self,
                                 model_id: str,
                                 model_object: Any,
                                 model_format: str = "pickle") -> bool:
        """
        Save model artifact to storage.
        
        Args:
            model_id: Model ID
            model_object: Trained model object
            model_format: Storage format ("pickle", "torch", "onnx")
            
        Returns:
            True if saved successfully
        """
        metadata = self._models.get(model_id)
        if not metadata:
            logger.error(f"Model not found: {model_id}")
            return False
        
        try:
            # Create model file path
            model_filename = f"{metadata.model_name}_{metadata.version}.{model_format}"
            model_file_path = self.models_dir / model_filename
            
            # Save model based on format
            if model_format == "pickle":
                with open(model_file_path, 'wb') as f:
                    pickle.dump(model_object, f)
            elif model_format == "torch":
                # Assuming PyTorch model
                model_object.save(model_file_path)
            elif model_format == "onnx":
                # Assuming ONNX model
                import onnx
                onnx.save(model_object, model_file_path)
            else:
                logger.error(f"Unsupported model format: {model_format}")
                return False
            
            # Calculate model hash and size
            model_hash = self._calculate_file_hash(model_file_path)
            model_size_mb = model_file_path.stat().st_size / (1024 * 1024)
            
            # Update metadata
            metadata.model_file_path = str(model_file_path)
            metadata.model_hash = model_hash
            metadata.model_size_mb = model_size_mb
            metadata.status = "trained"
            
            # Save registry
            self._save_registry()
            
            logger.info(f"Saved model artifact for {model_id} to {model_file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save model artifact for {model_id}: {e}")
            return False
    
    async def update_training_metrics(self,
                                   model_id: str,
                                   training_metrics: Dict[str, float],
                                   validation_metrics: Dict[str, float],
                                   test_metrics: Optional[Dict[str, float]] = None,
                                   training_samples: Optional[int] = None,
                                   validation_samples: Optional[int] = None,
                                   test_samples: Optional[int] = None,
                                   training_duration_hours: Optional[float] = None) -> bool:
        """
        Update training metrics for a model.
        
        Args:
            model_id: Model ID
            training_metrics: Training performance metrics
            validation_metrics: Validation performance metrics
            test_metrics: Test performance metrics
            training_samples: Number of training samples
            validation_samples: Number of validation samples
            test_samples: Number of test samples
            training_duration_hours: Training duration in hours
            
        Returns:
            True if updated successfully
        """
        metadata = self._models.get(model_id)
        if not metadata:
            logger.error(f"Model not found: {model_id}")
            return False
        
        # Update metrics
        metadata.training_metrics.update(training_metrics)
        metadata.validation_metrics.update(validation_metrics)
        
        if test_metrics:
            metadata.test_metrics.update(test_metrics)
        
        if training_samples is not None:
            metadata.training_samples = training_samples
        
        if validation_samples is not None:
            metadata.validation_samples = validation_samples
        
        if test_samples is not None:
            metadata.test_samples = test_samples
        
        if training_duration_hours is not None:
            metadata.training_duration_hours = training_duration_hours
        
        # Update status
        if metadata.training_metrics and metadata.validation_metrics:
            metadata.status = "validated"
        
        # Save registry
        self._save_registry()
        
        logger.info(f"Updated training metrics for model {model_id}")
        return True
    
    async def deploy_model(self,
                          model_id: str,
                          environment: str,
                          deployed_by: Optional[str] = None) -> bool:
        """
        Deploy a model to a specific environment.
        
        Args:
            model_id: Model ID to deploy
            environment: Target environment ("production", "staging", "development")
            deployed_by: User deploying the model
            
        Returns:
            True if deployed successfully
        """
        metadata = self._models.get(model_id)
        if not metadata:
            logger.error(f"Model not found: {model_id}")
            return False
        
        if not metadata.model_file_path:
            logger.error(f"Model artifact not found for {model_id}")
            return False
        
        if metadata.status not in ["trained", "validated"]:
            logger.error(f"Model {model_id} not ready for deployment (status: {metadata.status})")
            return False
        
        try:
            # Undeploy current model in environment if exists
            await self._undeploy_current_model(environment, metadata.model_name)
            
            # Deploy new model
            metadata.is_deployed = True
            metadata.deployment_environment = environment
            metadata.deployment_timestamp = datetime.now()
            metadata.status = "deployed"
            
            # Save registry
            self._save_registry()
            
            # Update cache
            CACHE_MANAGER.set_system_metrics(f"deployed_model_{environment}_{metadata.model_name}", {
                "model_id": model_id,
                "version": metadata.version,
                "deployment_timestamp": metadata.deployment_timestamp.isoformat()
            })
            
            # Log deployment
            AUDIT_LOGGER.log_model_versioning(
                model_name=metadata.model_name,
                version=metadata.version,
                action="deployed",
                training_dataset=metadata.training_dataset,
                performance_metrics=metadata.validation_metrics,
                user_id=deployed_by
            )
            
            logger.info(f"Deployed model {model_id} to {environment}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to deploy model {model_id}: {e}")
            return False
    
    async def rollback_model(self,
                           model_name: str,
                           target_version: str,
                           environment: str,
                           rolled_back_by: Optional[str] = None) -> bool:
        """
        Rollback to a previous model version.
        
        Args:
            model_name: Name of the model
            target_version: Target version to rollback to
            environment: Environment to rollback in
            rolled_back_by: User performing rollback
            
        Returns:
            True if rollback successful
        """
        # Find target model
        target_model = None
        target_model_id = None
        
        for model_id, metadata in self._models.items():
            if (metadata.model_name == model_name and 
                metadata.version == target_version and
                metadata.model_file_path):
                target_model = metadata
                target_model_id = model_id
                break
        
        if not target_model:
            logger.error(f"Target model not found: {model_name} v{target_version}")
            return False
        
        try:
            # Undeploy current model
            await self._undeploy_current_model(environment, model_name)
            
            # Deploy target model
            success = await self.deploy_model(target_model_id, environment, rolled_back_by)
            
            if success:
                # Log rollback
                AUDIT_LOGGER.log_model_versioning(
                    model_name=model_name,
                    version=target_version,
                    action="rolled_back",
                    training_dataset=target_model.training_dataset,
                    performance_metrics=target_model.validation_metrics,
                    user_id=rolled_back_by
                )
                
                logger.info(f"Rolled back {model_name} to v{target_version} in {environment}")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to rollback {model_name} to v{target_version}: {e}")
            return False
    
    async def compare_models(self,
                           model_a_id: str,
                           model_b_id: str,
                           metrics_to_compare: List[str]) -> Optional[ModelComparison]:
        """
        Compare two model versions.
        
        Args:
            model_a_id: First model ID
            model_b_id: Second model ID
            metrics_to_compare: List of metrics to compare
            
        Returns:
            Model comparison result
        """
        model_a = self._models.get(model_a_id)
        model_b = self._models.get(model_b_id)
        
        if not model_a or not model_b:
            logger.error("One or both models not found for comparison")
            return None
        
        comparison_metrics = {}
        improvement_percentage = {}
        
        for metric in metrics_to_compare:
            # Get metric values from test metrics, fallback to validation
            a_value = model_a.test_metrics.get(metric, model_a.validation_metrics.get(metric))
            b_value = model_b.test_metrics.get(metric, model_b.validation_metrics.get(metric))
            
            if a_value is not None and b_value is not None:
                comparison_metrics[metric] = {
                    "model_a_value": a_value,
                    "model_b_value": b_value
                }
                
                # Calculate improvement (higher is better for most metrics)
                if a_value != 0:
                    improvement = ((b_value - a_value) / a_value) * 100
                    improvement_percentage[metric] = improvement
        
        # Determine winner
        winner = "tie"
        improvements = [v for v in improvement_percentage.values() if v != 0]
        if improvements:
            avg_improvement = sum(improvements) / len(improvements)
            winner = "model_b" if avg_improvement > 0 else "model_a"
        
        comparison = ModelComparison(
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            comparison_metrics=comparison_metrics,
            improvement_percentage=improvement_percentage,
            winner=winner
        )
        
        # Store comparison
        self._comparisons.append(comparison)
        self._save_registry()
        
        logger.info(f"Compared models {model_a_id} and {model_b_id}: winner is {winner}")
        return comparison
    
    def get_model(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model metadata by ID."""
        return self._models.get(model_id)
    
    def get_model_by_name_version(self, model_name: str, version: str) -> Optional[ModelMetadata]:
        """Get model metadata by name and version."""
        for metadata in self._models.values():
            if metadata.model_name == model_name and metadata.version == version:
                return metadata
        return None
    
    def get_model_versions(self, model_name: str) -> List[ModelMetadata]:
        """Get all versions of a model."""
        return [
            metadata for metadata in self._models.values()
            if metadata.model_name == model_name
        ]
    
    def get_deployed_model(self, model_name: str, environment: str) -> Optional[ModelMetadata]:
        """Get currently deployed model for a name and environment."""
        for metadata in self._models.values():
            if (metadata.model_name == model_name and
                metadata.is_deployed and
                metadata.deployment_environment == environment):
                return metadata
        return None
    
    def get_model_lineage(self, model_id: str) -> Dict[str, Any]:
        """Get model lineage (parent and child relationships)."""
        metadata = self._models.get(model_id)
        if not metadata:
            return {}
        
        lineage = {
            "model_id": model_id,
            "model_name": metadata.model_name,
            "version": metadata.version,
            "parent": None,
            "children": []
        }
        
        # Get parent
        if metadata.parent_version:
            parent_metadata = self._models.get(metadata.parent_version)
            if parent_metadata:
                lineage["parent"] = {
                    "model_id": metadata.parent_version,
                    "version": parent_metadata.version,
                    "status": parent_metadata.status
                }
        
        # Get children
        for child_id in metadata.child_versions:
            child_metadata = self._models.get(child_id)
            if child_metadata:
                lineage["children"].append({
                    "model_id": child_id,
                    "version": child_metadata.version,
                    "status": child_metadata.status
                })
        
        return lineage
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        total_models = len(self._models)
        deployed_models = len([m for m in self._models.values() if m.is_deployed])
        
        # Count by model type
        model_types = {}
        for metadata in self._models.values():
            model_type = metadata.model_type
            model_types[model_type] = model_types.get(model_type, 0) + 1
        
        # Count by status
        status_counts = {}
        for metadata in self._models.values():
            status = metadata.status
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_models": total_models,
            "deployed_models": deployed_models,
            "model_types": model_types,
            "status_distribution": status_counts,
            "total_comparisons": len(self._comparisons),
            "registry_size_mb": self._get_registry_size()
        }
    
    def _undeploy_current_model(self, environment: str, model_name: str) -> None:
        """Undeploy current model in environment."""
        for metadata in self._models.values():
            if (metadata.model_name == model_name and
                metadata.is_deployed and
                metadata.deployment_environment == environment):
                metadata.is_deployed = False
                metadata.deployment_environment = None
                metadata.deployment_timestamp = None
                break
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file."""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    
    def _get_registry_size(self) -> float:
        """Get registry size in MB."""
        total_size = 0
        
        if self.registry_file.exists():
            total_size += self.registry_file.stat().st_size
        
        if self.comparisons_file.exists():
            total_size += self.comparisons_file.stat().st_size
        
        return total_size / (1024 * 1024)
    
    async def cleanup_old_models(self, days_to_keep: int = 365) -> int:
        """Clean up old model artifacts."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        models_to_remove = []
        for model_id, metadata in self._models.items():
            if (metadata.created_at < cutoff_date and
                not metadata.is_deployed and
                metadata.status in ["created", "trained", "validated"]):
                models_to_remove.append(model_id)
        
        for model_id in models_to_remove:
            metadata = self._models[model_id]
            
            # Remove model file
            if metadata.model_file_path:
                try:
                    Path(metadata.model_file_path).unlink()
                except Exception as e:
                    logger.error(f"Failed to remove model file {metadata.model_file_path}: {e}")
            
            # Remove from registry
            del self._models[model_id]
        
        if models_to_remove:
            self._save_registry()
            logger.info(f"Cleaned up {len(models_to_remove)} old models")
        
        return len(models_to_remove)


# Global model registry instance
MODEL_REGISTRY = ModelRegistry()
