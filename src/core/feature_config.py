"""
Feature Configuration Service - Manages optional features and their settings.
Allows safe enabling/disabling of enhanced features without affecting core functionality.
"""

import logging
from typing import Dict, Any
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class FeatureConfig:
    """
    Manages configuration for optional features in the application.
    Provides safe defaults and graceful fallbacks.
    """

    def __init__(self, config_file: str = "features.json"):
        self.config_file = config_file
        self.features = self._load_default_config()
        self._load_user_config()

    def _load_default_config(self) -> Dict[str, Any]:
        """Load default feature configuration."""
        return {
            # Documentation Features
            "api_documentation": {
                "enabled": True,
                "include_examples": True,
                "swagger_ui": True,
                "redoc": True,
            },
            # Export Features
            "pdf_export": {
                "enabled": True,
                "include_branding": True,
                "max_file_size_mb": 50,
            },
            "data_export": {
                "enabled": True,
                "excel_support": True,
                "csv_support": True,
                "json_support": True,
                "max_file_size_mb": 100,
            },
            # Analytics Features
            "advanced_analytics": {
                "enabled": True,
                "trend_analysis": True,
                "predictive_insights": True,
                "performance_metrics": True,
            },
            # UI Enhancements
            "help_system": {
                "enabled": True,
                "tooltips": True,
                "help_bubbles": True,
                "compliance_guide": True,
            },
            "interactive_tutorials": {
                "enabled": False,  # Disabled by default (would need intro.js)
                "auto_start": False,
                "show_on_first_run": False,
            },
            # Performance Features
            "performance_optimization": {
                "enabled": True,
                "gpu_acceleration": True,
                "model_quantization": True,
                "adaptive_caching": True,
            },
            # Advanced Report Features
            "enhanced_reports": {
                "enabled": True,
                "interactive_elements": True,
                "custom_branding": False,
                "advanced_formatting": True,
            },
        }

    def _load_user_config(self):
        """Load user-specific configuration if available."""
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                with open(config_path, "r") as f:
                    user_config = json.load(f)

                # Merge user config with defaults
                self._merge_config(self.features, user_config)
                logger.info(
                    f"Loaded user feature configuration from {self.config_file}"
                )
            else:
                logger.info("No user feature configuration found, using defaults")

        except Exception as e:
            logger.warning(f"Could not load user config: {e}, using defaults")

    def _merge_config(self, default: Dict[str, Any], user: Dict[str, Any]):
        """Recursively merge user configuration with defaults."""
        for key, value in user.items():
            if key in default:
                if isinstance(value, dict) and isinstance(default[key], dict):
                    self._merge_config(default[key], value)
                else:
                    default[key] = value

    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, "w") as f:
                json.dump(self.features, f, indent=2)
            logger.info(f"Feature configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Could not save feature configuration: {e}")

    def is_feature_enabled(self, feature_path: str) -> bool:
        """
        Check if a feature is enabled using dot notation.

        Args:
            feature_path: Feature path like 'pdf_export.enabled' or 'help_system.tooltips'

        Returns:
            True if feature is enabled, False otherwise
        """
        try:
            parts = feature_path.split(".")
            current = self.features

            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    logger.warning(f"Feature path not found: {feature_path}")
                    return False

            return bool(current)

        except Exception as e:
            logger.error(f"Error checking feature {feature_path}: {e}")
            return False

    def get_feature_config(self, feature_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific feature.

        Args:
            feature_name: Name of the feature (e.g., 'pdf_export')

        Returns:
            Feature configuration dictionary
        """
        return self.features.get(feature_name, {})

    def set_feature_enabled(self, feature_path: str, enabled: bool):
        """
        Enable or disable a feature.

        Args:
            feature_path: Feature path like 'pdf_export.enabled'
            enabled: Whether to enable the feature
        """
        try:
            parts = feature_path.split(".")
            current = self.features

            # Navigate to parent
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]

            # Set the value
            current[parts[-1]] = enabled
            logger.info(f"Feature {feature_path} set to {enabled}")

        except Exception as e:
            logger.error(f"Error setting feature {feature_path}: {e}")

    def get_enabled_features(self) -> list[str]:
        """Get list of all enabled features."""
        enabled = []

        def check_features(config: Dict[str, Any], prefix: str = ""):
            for key, value in config.items():
                current_path = f"{prefix}.{key}" if prefix else key

                if isinstance(value, dict):
                    if value.get("enabled", False):
                        enabled.append(current_path)
                    check_features(value, current_path)
                elif key == "enabled" and value:
                    enabled.append(prefix)

        check_features(self.features)
        return enabled

    def validate_dependencies(self) -> Dict[str, str]:
        """
        Validate that required dependencies are available for enabled features.

        Returns:
            Dictionary of feature -> error message for missing dependencies
        """
        issues = {}

        # Check PDF export dependencies
        if self.is_feature_enabled("pdf_export.enabled"):
            try:
                import importlib.util

                if importlib.util.find_spec("reportlab") is None:
                    raise ImportError("ReportLab not found")
            except ImportError:
                issues["pdf_export"] = "ReportLab library not installed"

        # Check Excel export dependencies
        if self.is_feature_enabled("data_export.excel_support"):
            try:
                import importlib.util

                if (
                    importlib.util.find_spec("pandas") is None
                    or importlib.util.find_spec("openpyxl") is None
                ):
                    raise ImportError("Required libraries not found")
            except ImportError:
                issues["excel_export"] = "Pandas or OpenPyXL library not installed"

        # Check GPU acceleration dependencies
        if self.is_feature_enabled("performance_optimization.gpu_acceleration"):
            try:
                import torch

                if not torch.cuda.is_available():
                    issues["gpu_acceleration"] = "CUDA not available"
            except ImportError:
                issues["gpu_acceleration"] = "PyTorch not installed"

        return issues

    def get_feature_summary(self) -> Dict[str, Any]:
        """Get summary of feature status and configuration."""
        enabled_features = self.get_enabled_features()
        dependency_issues = self.validate_dependencies()

        return {
            "total_features": len(enabled_features),
            "enabled_features": enabled_features,
            "dependency_issues": dependency_issues,
            "config_file": self.config_file,
            "all_features_working": len(dependency_issues) == 0,
        }


# Global feature configuration instance
feature_config = FeatureConfig()


def is_feature_enabled(feature_path: str) -> bool:
    """Global function to check if a feature is enabled."""
    return feature_config.is_feature_enabled(feature_path)


def get_feature_config(feature_name: str) -> Dict[str, Any]:
    """Global function to get feature configuration."""
    return feature_config.get_feature_config(feature_name)


# Convenience functions for common feature checks
def is_pdf_export_enabled() -> bool:
    """Check if PDF export is enabled and available."""
    return is_feature_enabled("pdf_export.enabled")


def is_help_system_enabled() -> bool:
    """Check if help system is enabled."""
    return is_feature_enabled("help_system.enabled")


def is_advanced_analytics_enabled() -> bool:
    """Check if advanced analytics are enabled."""
    return is_feature_enabled("advanced_analytics.enabled")


def is_data_export_enabled() -> bool:
    """Check if data export is enabled."""
    return is_feature_enabled("data_export.enabled")
