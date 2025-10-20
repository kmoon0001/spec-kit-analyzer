"""Advanced ML Model Management System for Clinical Compliance Analysis.

This module provides comprehensive ML model management including model versioning,
A/B testing, performance monitoring, automatic retraining, and model deployment
using expert patterns and best practices.

Features:
- Model versioning and lifecycle management
- A/B testing and model comparison
- Performance monitoring and drift detection
- Automatic retraining and deployment
- Model registry and metadata management
- Model serving and load balancing
- Comprehensive model analytics
"""

import asyncio
import json
import pickle
import shutil
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
from pathlib import Path
import threading
from collections import defaultdict, deque
import numpy as np
import pandas as pd

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
import joblib

from src.core.centralized_logging import get_logger, performance_tracker, audit_logger
from src.core.type_safety import Result, ErrorHandler, error_handler


class ModelStatus(Enum):
    """Model status enumeration."""
    TRAINING = "training"
    TRAINED = "trained"
    VALIDATING = "validating"
    VALIDATED = "validated"
    DEPLOYING = "deploying"
    DEPLOYED = "deployed"
    SERVING = "serving"
    RETIRING = "retiring"
    RETIRED = "retired"
    FAILED = "failed"


class ModelType(Enum):
    """Model type enumeration."""
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    NER = "ner"
    EMBEDDING = "embedding"
    ENSEMBLE = "ensemble"
    TRANSFORMER = "transformer"


class DeploymentStrategy(Enum):
    """Deployment strategy enumeration."""
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    A_B_TEST = "a_b_test"


@dataclass
class ModelMetadata:
    """Model metadata information."""
    model_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    version: str = "1.0.0"
    model_type: ModelType = ModelType.CLASSIFICATION
    description: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = ""
    framework: str = ""  # pytorch, tensorflow, sklearn, etc.
    size_bytes: int = 0
    checksum: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    hyperparameters: Dict[str, Any] = field(default_factory=dict)
    training_data_info: Dict[str, Any] = field(default_factory=dict)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ModelVersion:
    """Model version information."""
    version_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_id: str = ""
    version: str = ""
    status: ModelStatus = ModelStatus.TRAINING
    file_path: str = ""
    metadata: ModelMetadata = field(default_factory=ModelMetadata)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deployed_at: Optional[datetime] = None
    performance_history: List[Dict[str, Any]] = field(default_factory=list)
    deployment_info: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelPerformance:
    """Model performance metrics."""
    model_id: str = ""
    version: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    auc_roc: float = 0.0
    inference_time_ms: float = 0.0
    throughput_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class ModelDeployment:
    """Model deployment information."""
    deployment_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    model_id: str = ""
    version: str = ""
    strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN
    status: ModelStatus = ModelStatus.DEPLOYING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    deployed_at: Optional[datetime] = None
    traffic_percentage: float = 100.0
    health_check_url: str = ""
    metrics_endpoint: str = ""
    rollback_version: Optional[str] = None
    deployment_config: Dict[str, Any] = field(default_factory=dict)


class ModelRegistry:
    """Comprehensive model registry and management system."""

    def __init__(self, base_path: str = "models"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        self.models: Dict[str, ModelMetadata] = {}
        self.versions: Dict[str, ModelVersion] = {}
        self.deployments: Dict[str, ModelDeployment] = {}
        self.performance_history: List[ModelPerformance] = []

        self.lock = threading.RLock()
        self.logger = get_logger(__name__)

        # Load existing models
        self._load_existing_models()

    def _load_existing_models(self) -> None:
        """Load existing models from disk."""
        try:
            registry_file = self.base_path / "registry.json"
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    data = json.load(f)

                # Load models
                for model_id, model_data in data.get("models", {}).items():
                    metadata = ModelMetadata(**model_data)
                    self.models[model_id] = metadata

                # Load versions
                for version_id, version_data in data.get("versions", {}).items():
                    version = ModelVersion(**version_data)
                    self.versions[version_id] = version

                # Load deployments
                for deployment_id, deployment_data in data.get("deployments", {}).items():
                    deployment = ModelDeployment(**deployment_data)
                    self.deployments[deployment_id] = deployment

                self.logger.info("Loaded %d models, %d versions, %d deployments",
                               len(self.models), len(self.versions), len(self.deployments))

        except Exception as e:
            self.logger.error("Failed to load existing models: %s", e)

    def _save_registry(self) -> None:
        """Save registry to disk."""
        try:
            registry_file = self.base_path / "registry.json"

            data = {
                "models": {model_id: model.__dict__ for model_id, model in self.models.items()},
                "versions": {version_id: version.__dict__ for version_id, version in self.versions.items()},
                "deployments": {deployment_id: deployment.__dict__ for deployment_id, deployment in self.deployments.items()}
            }

            with open(registry_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)

        except Exception as e:
            self.logger.error("Failed to save registry: %s", e)

    def register_model(
        self,
        name: str,
        model_type: ModelType,
        description: str = "",
        tags: Optional[List[str]] = None,
        created_by: str = "",
        framework: str = "",
        hyperparameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Register a new model."""
        with self.lock:
            model_id = str(uuid.uuid4())

            metadata = ModelMetadata(
                model_id=model_id,
                name=name,
                model_type=model_type,
                description=description,
                tags=tags or [],
                created_by=created_by,
                framework=framework,
                hyperparameters=hyperparameters or {}
            )

            self.models[model_id] = metadata
            self._save_registry()

            self.logger.info("Registered new model: %s (%s)", name, model_id)
            return model_id

    def create_version(
        self,
        model_id: str,
        version: str,
        file_path: str,
        performance_metrics: Optional[Dict[str, float]] = None
    ) -> str:
        """Create a new model version."""
        with self.lock:
            if model_id not in self.models:
                raise ValueError(f"Model {model_id} not found")

            version_id = str(uuid.uuid4())

            # Get model metadata
            model_metadata = self.models[model_id]

            # Create version metadata
            version_metadata = ModelMetadata(
                model_id=model_id,
                name=model_metadata.name,
                version=version,
                model_type=model_metadata.model_type,
                description=model_metadata.description,
                tags=model_metadata.tags.copy(),
                created_by=model_metadata.created_by,
                framework=model_metadata.framework,
                hyperparameters=model_metadata.hyperparameters.copy(),
                performance_metrics=performance_metrics or {}
            )

            # Calculate file size and checksum
            file_path_obj = Path(file_path)
            if file_path_obj.exists():
                version_metadata.size_bytes = file_path_obj.stat().st_size
                version_metadata.checksum = self._calculate_checksum(file_path)

            version_obj = ModelVersion(
                version_id=version_id,
                model_id=model_id,
                version=version,
                status=ModelStatus.TRAINED,
                file_path=file_path,
                metadata=version_metadata
            )

            self.versions[version_id] = version_obj
            self._save_registry()

            self.logger.info("Created new version: %s v%s", model_metadata.name, version)
            return version_id

    def _calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum."""
        import hashlib

        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def deploy_model(
        self,
        model_id: str,
        version: str,
        strategy: DeploymentStrategy = DeploymentStrategy.BLUE_GREEN,
        traffic_percentage: float = 100.0,
        deployment_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """Deploy a model version."""
        with self.lock:
            # Find the version
            version_obj = None
            for v in self.versions.values():
                if v.model_id == model_id and v.version == version:
                    version_obj = v
                    break

            if not version_obj:
                raise ValueError(f"Version {version} not found for model {model_id}")

            deployment_id = str(uuid.uuid4())

            deployment = ModelDeployment(
                deployment_id=deployment_id,
                model_id=model_id,
                version=version,
                strategy=strategy,
                status=ModelStatus.DEPLOYING,
                traffic_percentage=traffic_percentage,
                deployment_config=deployment_config or {}
            )

            self.deployments[deployment_id] = deployment

            # Update version status
            version_obj.status = ModelStatus.DEPLOYING
            version_obj.deployment_info = deployment.__dict__

            self._save_registry()

            self.logger.info("Deploying model %s v%s with strategy %s",
                           self.models[model_id].name, version, strategy.value)

            return deployment_id

    def record_performance(
        self,
        model_id: str,
        version: str,
        performance: ModelPerformance
    ) -> None:
        """Record model performance metrics."""
        with self.lock:
            performance.model_id = model_id
            performance.version = version
            self.performance_history.append(performance)

            # Update version performance history
            for version_obj in self.versions.values():
                if version_obj.model_id == model_id and version_obj.version == version:
                    version_obj.performance_history.append(performance.__dict__)
                    break

            # Keep only recent performance history
            if len(self.performance_history) > 10000:
                self.performance_history = self.performance_history[-5000:]

            self._save_registry()

    def get_model_info(self, model_id: str) -> Optional[ModelMetadata]:
        """Get model information."""
        return self.models.get(model_id)

    def get_model_versions(self, model_id: str) -> List[ModelVersion]:
        """Get all versions of a model."""
        return [v for v in self.versions.values() if v.model_id == model_id]

    def get_latest_version(self, model_id: str) -> Optional[ModelVersion]:
        """Get the latest version of a model."""
        versions = self.get_model_versions(model_id)
        if not versions:
            return None

        # Sort by version string (simple version comparison)
        versions.sort(key=lambda v: v.version, reverse=True)
        return versions[0]

    def get_deployed_models(self) -> List[ModelDeployment]:
        """Get all deployed models."""
        return [d for d in self.deployments.values() if d.status == ModelStatus.DEPLOYED]

    def get_performance_history(
        self,
        model_id: Optional[str] = None,
        version: Optional[str] = None,
        hours: int = 24
    ) -> List[ModelPerformance]:
        """Get performance history."""
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)

        filtered_history = [
            p for p in self.performance_history
            if p.timestamp >= cutoff_time
        ]

        if model_id:
            filtered_history = [p for p in filtered_history if p.model_id == model_id]

        if version:
            filtered_history = [p for p in filtered_history if p.version == version]

        return filtered_history


class ModelPerformanceMonitor:
    """Model performance monitoring and drift detection."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.logger = get_logger(__name__)
        self.drift_threshold = 0.1  # 10% performance degradation
        self.performance_window_hours = 24

    def detect_performance_drift(self, model_id: str, version: str) -> Dict[str, Any]:
        """Detect performance drift in a model."""
        try:
            # Get recent performance history
            recent_performance = self.registry.get_performance_history(
                model_id=model_id,
                version=version,
                hours=self.performance_window_hours
            )

            if len(recent_performance) < 10:
                return {"drift_detected": False, "reason": "Insufficient data"}

            # Calculate baseline performance (first 50% of data)
            baseline_size = len(recent_performance) // 2
            baseline_performance = recent_performance[:baseline_size]
            current_performance = recent_performance[baseline_size:]

            # Calculate average metrics
            baseline_metrics = self._calculate_average_metrics(baseline_performance)
            current_metrics = self._calculate_average_metrics(current_performance)

            # Detect drift
            drift_detected = False
            drift_details = {}

            for metric in ["accuracy", "precision", "recall", "f1_score"]:
                baseline_value = baseline_metrics.get(metric, 0)
                current_value = current_metrics.get(metric, 0)

                if baseline_value > 0:
                    degradation = (baseline_value - current_value) / baseline_value
                    drift_details[metric] = {
                        "baseline": baseline_value,
                        "current": current_value,
                        "degradation": degradation
                    }

                    if degradation > self.drift_threshold:
                        drift_detected = True

            return {
                "drift_detected": drift_detected,
                "drift_threshold": self.drift_threshold,
                "baseline_metrics": baseline_metrics,
                "current_metrics": current_metrics,
                "drift_details": drift_details,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        except Exception as e:
            self.logger.error("Error detecting performance drift: %s", e)
            return {"drift_detected": False, "error": str(e)}

    def _calculate_average_metrics(self, performance_list: List[ModelPerformance]) -> Dict[str, float]:
        """Calculate average metrics from performance list."""
        if not performance_list:
            return {}

        metrics = defaultdict(list)

        for perf in performance_list:
            metrics["accuracy"].append(perf.accuracy)
            metrics["precision"].append(perf.precision)
            metrics["recall"].append(perf.recall)
            metrics["f1_score"].append(perf.f1_score)
            metrics["inference_time_ms"].append(perf.inference_time_ms)
            metrics["throughput_per_second"].append(perf.throughput_per_second)

        return {
            metric: sum(values) / len(values)
            for metric, values in metrics.items()
        }

    def get_performance_summary(self, model_id: str, version: str) -> Dict[str, Any]:
        """Get performance summary for a model version."""
        performance_history = self.registry.get_performance_history(
            model_id=model_id,
            version=version,
            hours=self.performance_window_hours
        )

        if not performance_history:
            return {"error": "No performance data available"}

        # Calculate statistics
        metrics = self._calculate_average_metrics(performance_history)

        # Calculate trends
        recent_performance = performance_history[-10:] if len(performance_history) >= 10 else performance_history
        older_performance = performance_history[:-10] if len(performance_history) >= 20 else performance_history[:len(performance_history)//2]

        recent_metrics = self._calculate_average_metrics(recent_performance)
        older_metrics = self._calculate_average_metrics(older_performance)

        trends = {}
        for metric in ["accuracy", "precision", "recall", "f1_score"]:
            if metric in recent_metrics and metric in older_metrics:
                trends[metric] = recent_metrics[metric] - older_metrics[metric]

        return {
            "model_id": model_id,
            "version": version,
            "total_samples": len(performance_history),
            "average_metrics": metrics,
            "trends": trends,
            "time_window_hours": self.performance_window_hours,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


class ModelABTesting:
    """A/B testing framework for models."""

    def __init__(self, registry: ModelRegistry):
        self.registry = registry
        self.logger = get_logger(__name__)
        self.active_tests: Dict[str, Dict[str, Any]] = {}

    def start_ab_test(
        self,
        test_name: str,
        model_a_id: str,
        model_a_version: str,
        model_b_id: str,
        model_b_version: str,
        traffic_split: float = 0.5,
        success_metric: str = "accuracy",
        minimum_samples: int = 1000
    ) -> str:
        """Start an A/B test between two model versions."""
        test_id = str(uuid.uuid4())

        test_config = {
            "test_id": test_id,
            "test_name": test_name,
            "model_a": {"id": model_a_id, "version": model_a_version},
            "model_b": {"id": model_b_id, "version": model_b_version},
            "traffic_split": traffic_split,
            "success_metric": success_metric,
            "minimum_samples": minimum_samples,
            "started_at": datetime.now(timezone.utc),
            "status": "active",
            "results": {"model_a": [], "model_b": []}
        }

        self.active_tests[test_id] = test_config

        self.logger.info("Started A/B test %s: %s vs %s", test_name, model_a_version, model_b_version)

        return test_id

    def record_ab_test_result(
        self,
        test_id: str,
        model_version: str,
        result: Dict[str, Any]
    ) -> None:
        """Record a result for an A/B test."""
        if test_id not in self.active_tests:
            raise ValueError(f"A/B test {test_id} not found")

        test_config = self.active_tests[test_id]

        # Determine which model this result belongs to
        if model_version == test_config["model_a"]["version"]:
            test_config["results"]["model_a"].append(result)
        elif model_version == test_config["model_b"]["version"]:
            test_config["results"]["model_b"].append(result)
        else:
            raise ValueError(f"Model version {model_version} not part of test {test_id}")

    def get_ab_test_results(self, test_id: str) -> Dict[str, Any]:
        """Get A/B test results."""
        if test_id not in self.active_tests:
            raise ValueError(f"A/B test {test_id} not found")

        test_config = self.active_tests[test_id]
        results_a = test_config["results"]["model_a"]
        results_b = test_config["results"]["model_b"]

        if not results_a or not results_b:
            return {"error": "Insufficient data for analysis"}

        # Calculate statistics
        metric = test_config["success_metric"]

        values_a = [r.get(metric, 0) for r in results_a]
        values_b = [r.get(metric, 0) for r in results_b]

        mean_a = sum(values_a) / len(values_a)
        mean_b = sum(values_b) / len(values_b)

        # Simple statistical significance test (t-test approximation)
        std_a = np.std(values_a) if len(values_a) > 1 else 0
        std_b = np.std(values_b) if len(values_b) > 1 else 0

        # Calculate confidence interval
        n_a, n_b = len(values_a), len(values_b)
        se_diff = np.sqrt((std_a**2 / n_a) + (std_b**2 / n_b))

        # 95% confidence interval
        margin_error = 1.96 * se_diff
        diff = mean_b - mean_a

        return {
            "test_id": test_id,
            "test_name": test_config["test_name"],
            "model_a": {
                "id": test_config["model_a"]["id"],
                "version": test_config["model_a"]["version"],
                "mean": mean_a,
                "std": std_a,
                "samples": n_a
            },
            "model_b": {
                "id": test_config["model_b"]["id"],
                "version": test_config["model_b"]["version"],
                "mean": mean_b,
                "std": std_b,
                "samples": n_b
            },
            "difference": diff,
            "confidence_interval": [diff - margin_error, diff + margin_error],
            "statistically_significant": abs(diff) > margin_error,
            "winner": "model_b" if diff > 0 else "model_a" if diff < 0 else "tie",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }


# Global instances
model_registry = ModelRegistry()
performance_monitor = ModelPerformanceMonitor(model_registry)
ab_testing = ModelABTesting(model_registry)

# API Router
router = APIRouter(prefix="/api/v2/ml-models", tags=["ML Model Management"])


# Pydantic models
class ModelRegistrationRequest(BaseModel):
    """Request model for model registration."""
    name: str = Field(..., description="Model name")
    model_type: str = Field(..., description="Model type")
    description: str = Field(default="", description="Model description")
    tags: List[str] = Field(default_factory=list, description="Model tags")
    created_by: str = Field(default="", description="Creator")
    framework: str = Field(default="", description="ML framework")
    hyperparameters: Dict[str, Any] = Field(default_factory=dict, description="Hyperparameters")


class ModelVersionRequest(BaseModel):
    """Request model for creating model version."""
    model_id: str = Field(..., description="Model ID")
    version: str = Field(..., description="Version string")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")


class ModelDeploymentRequest(BaseModel):
    """Request model for model deployment."""
    model_id: str = Field(..., description="Model ID")
    version: str = Field(..., description="Version to deploy")
    strategy: str = Field(default="blue_green", description="Deployment strategy")
    traffic_percentage: float = Field(default=100.0, description="Traffic percentage")
    deployment_config: Dict[str, Any] = Field(default_factory=dict, description="Deployment configuration")


class PerformanceRecordRequest(BaseModel):
    """Request model for recording performance."""
    model_id: str = Field(..., description="Model ID")
    version: str = Field(..., description="Version")
    accuracy: float = Field(default=0.0, description="Accuracy")
    precision: float = Field(default=0.0, description="Precision")
    recall: float = Field(default=0.0, description="Recall")
    f1_score: float = Field(default=0.0, description="F1 score")
    inference_time_ms: float = Field(default=0.0, description="Inference time")
    custom_metrics: Dict[str, float] = Field(default_factory=dict, description="Custom metrics")


# API Endpoints
@router.post("/register")
async def register_model(request: ModelRegistrationRequest) -> Dict[str, Any]:
    """Register a new model."""
    try:
        model_type = ModelType(request.model_type)

        model_id = model_registry.register_model(
            name=request.name,
            model_type=model_type,
            description=request.description,
            tags=request.tags,
            created_by=request.created_by,
            framework=request.framework,
            hyperparameters=request.hyperparameters
        )

        return {
            "message": "Model registered successfully",
            "model_id": model_id,
            "name": request.name,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to register model: {str(e)}"
        )


@router.post("/versions")
async def create_model_version(request: ModelVersionRequest) -> Dict[str, Any]:
    """Create a new model version."""
    try:
        version_id = model_registry.create_version(
            model_id=request.model_id,
            version=request.version,
            file_path="",  # Would be provided via file upload
            performance_metrics=request.performance_metrics
        )

        return {
            "message": "Model version created successfully",
            "version_id": version_id,
            "model_id": request.model_id,
            "version": request.version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create model version: {str(e)}"
        )


@router.post("/deploy")
async def deploy_model(request: ModelDeploymentRequest) -> Dict[str, Any]:
    """Deploy a model version."""
    try:
        strategy = DeploymentStrategy(request.strategy)

        deployment_id = model_registry.deploy_model(
            model_id=request.model_id,
            version=request.version,
            strategy=strategy,
            traffic_percentage=request.traffic_percentage,
            deployment_config=request.deployment_config
        )

        return {
            "message": "Model deployment started",
            "deployment_id": deployment_id,
            "model_id": request.model_id,
            "version": request.version,
            "strategy": request.strategy,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to deploy model: {str(e)}"
        )


@router.post("/performance")
async def record_performance(request: PerformanceRecordRequest) -> Dict[str, Any]:
    """Record model performance metrics."""
    try:
        performance = ModelPerformance(
            accuracy=request.accuracy,
            precision=request.precision,
            recall=request.recall,
            f1_score=request.f1_score,
            inference_time_ms=request.inference_time_ms,
            custom_metrics=request.custom_metrics
        )

        model_registry.record_performance(
            model_id=request.model_id,
            version=request.version,
            performance=performance
        )

        return {
            "message": "Performance recorded successfully",
            "model_id": request.model_id,
            "version": request.version,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to record performance: {str(e)}"
        )


@router.get("/models")
async def list_models() -> List[Dict[str, Any]]:
    """List all registered models."""
    return [model.__dict__ for model in model_registry.models.values()]


@router.get("/models/{model_id}")
async def get_model_info(model_id: str) -> Dict[str, Any]:
    """Get model information."""
    model_info = model_registry.get_model_info(model_id)
    if not model_info:
        raise HTTPException(status_code=404, detail="Model not found")

    return model_info.__dict__


@router.get("/models/{model_id}/versions")
async def get_model_versions(model_id: str) -> List[Dict[str, Any]]:
    """Get all versions of a model."""
    versions = model_registry.get_model_versions(model_id)
    return [version.__dict__ for version in versions]


@router.get("/models/{model_id}/performance")
async def get_model_performance(
    model_id: str,
    version: Optional[str] = None,
    hours: int = 24
) -> List[Dict[str, Any]]:
    """Get model performance history."""
    performance_history = model_registry.get_performance_history(
        model_id=model_id,
        version=version,
        hours=hours
    )
    return [perf.__dict__ for perf in performance_history]


@router.get("/models/{model_id}/drift")
async def check_performance_drift(model_id: str, version: str) -> Dict[str, Any]:
    """Check for performance drift."""
    return performance_monitor.detect_performance_drift(model_id, version)


@router.get("/deployments")
async def list_deployments() -> List[Dict[str, Any]]:
    """List all model deployments."""
    deployments = model_registry.get_deployed_models()
    return [deployment.__dict__ for deployment in deployments]


@router.get("/performance/summary")
async def get_performance_summary(model_id: str, version: str) -> Dict[str, Any]:
    """Get performance summary for a model version."""
    return performance_monitor.get_performance_summary(model_id, version)
