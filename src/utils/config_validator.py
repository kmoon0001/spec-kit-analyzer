"""
Configuration validation utilities for the Therapy Compliance Analyzer.

This module provides validation and health checks for the application configuration.
"""

import logging
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Tuple

from src.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate and health-check application configuration."""

    def __init__(self):
        self.validation_errors: List[str] = []
        self.validation_warnings: List[str] = []

    def validate_config_file(
        self, config_path: str = "config.yaml"
    ) -> Tuple[bool, List[str], List[str]]:
        """Validate the configuration file structure and values."""
        self.validation_errors.clear()
        self.validation_warnings.clear()

        # Check if config file exists
        if not os.path.exists(config_path):
            self.validation_errors.append(
                f"Configuration file not found: {config_path}"
            )
            return False, self.validation_errors, self.validation_warnings

        try:
            # Load and parse YAML
            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Validate structure
            self._validate_structure(config_data)

            # Validate paths
            self._validate_paths(config_data.get("paths", {}))

            # Validate database settings
            self._validate_database(config_data.get("database", {}))

            # Validate model settings
            self._validate_models(config_data.get("models", {}))

            # Validate performance settings
            self._validate_performance(config_data.get("performance", {}))

            # Validate security settings
            self._validate_security(config_data.get("security", {}))

            # Try to load with Pydantic for final validation
            try:
                Settings(**config_data)  # Just validate, don't store
                logger.info("Configuration successfully validated with Pydantic models")
            except Exception as e:
                self.validation_errors.append(f"Pydantic validation failed: {str(e)}")

        except yaml.YAMLError as e:
            self.validation_errors.append(f"YAML parsing error: {str(e)}")
        except Exception as e:
            self.validation_errors.append(
                f"Unexpected error during validation: {str(e)}"
            )

        is_valid = len(self.validation_errors) == 0
        return is_valid, self.validation_errors, self.validation_warnings

    def _validate_structure(self, config: Dict[str, Any]) -> None:
        """Validate the basic structure of the configuration."""
        required_sections = [
            "database",
            "auth",
            "maintenance",
            "paths",
            "models",
            "llm",
            "retrieval",
            "analysis",
        ]

        for section in required_sections:
            if section not in config:
                self.validation_errors.append(
                    f"Missing required configuration section: {section}"
                )

    def _validate_paths(self, paths_config: Dict[str, Any]) -> None:
        """Validate path configurations."""
        required_paths = ["temp_upload_dir", "api_url", "rule_dir"]

        for path_key in required_paths:
            if path_key not in paths_config:
                self.validation_errors.append(f"Missing required path: {path_key}")
                continue

            path_value = paths_config[path_key]

            # Skip URL validation
            if path_key == "api_url":
                if not path_value.startswith(("http://", "https://")):
                    self.validation_warnings.append(
                        f"API URL should start with http:// or https://: {path_value}"
                    )
                continue

            # Validate directory paths
            if path_key in ["temp_upload_dir", "rule_dir", "cache_dir", "logs_dir"]:
                # Create directory if it doesn't exist
                try:
                    Path(path_value).mkdir(parents=True, exist_ok=True)
                    logger.info(f"Ensured directory exists: {path_value}")
                except Exception as e:
                    self.validation_errors.append(
                        f"Cannot create directory {path_value}: {str(e)}"
                    )

            # Validate file paths
            elif path_key in ["medical_dictionary"]:
                if not os.path.exists(path_value):
                    self.validation_warnings.append(f"File not found: {path_value}")

    def _validate_database(self, db_config: Dict[str, Any]) -> None:
        """Validate database configuration."""
        if "url" not in db_config:
            self.validation_errors.append("Missing database URL")
            return

        db_url = db_config["url"]

        # Validate SQLite URL format
        if db_url.startswith("sqlite:///"):
            db_path = db_url.replace("sqlite:///", "")
            db_dir = os.path.dirname(db_path)

            if db_dir and not os.path.exists(db_dir):
                try:
                    os.makedirs(db_dir, exist_ok=True)
                    logger.info(f"Created database directory: {db_dir}")
                except Exception as e:
                    self.validation_errors.append(
                        f"Cannot create database directory: {str(e)}"
                    )

        # Validate connection pool settings
        pool_size = db_config.get("pool_size", 5)
        max_overflow = db_config.get("max_overflow", 10)

        if pool_size < 1:
            self.validation_warnings.append("Database pool_size should be at least 1")

        if max_overflow < 0:
            self.validation_warnings.append(
                "Database max_overflow should be non-negative"
            )

    def _validate_models(self, models_config: Dict[str, Any]) -> None:
        """Validate model configuration."""
        required_models = ["retriever", "fact_checker", "ner_ensemble"]

        for model_key in required_models:
            if model_key not in models_config:
                self.validation_errors.append(
                    f"Missing required model configuration: {model_key}"
                )

        # Validate generator profiles
        if "generator_profiles" in models_config:
            profiles = models_config["generator_profiles"]
            if not isinstance(profiles, dict) or len(profiles) == 0:
                self.validation_warnings.append("No generator profiles configured")

            for profile_name, profile_config in profiles.items():
                if "repo" not in profile_config or "filename" not in profile_config:
                    self.validation_errors.append(
                        f"Generator profile {profile_name} missing repo or filename"
                    )

        # Validate prompt file paths
        prompt_files = [
            "doc_classifier_prompt",
            "analysis_prompt_template",
            "nlg_prompt_template",
        ]
        for prompt_file in prompt_files:
            if prompt_file in models_config:
                path = models_config[prompt_file]
                if not os.path.exists(path):
                    self.validation_warnings.append(f"Prompt file not found: {path}")

    def _validate_performance(self, perf_config: Dict[str, Any]) -> None:
        """Validate performance configuration."""
        if not perf_config:
            self.validation_warnings.append(
                "No performance configuration found, using defaults"
            )
            return

        # Validate memory settings
        max_cache_mb = perf_config.get("max_cache_memory_mb", 2048)
        if max_cache_mb < 512:
            self.validation_warnings.append(
                "max_cache_memory_mb is very low, may impact performance"
            )
        elif max_cache_mb > 8192:
            self.validation_warnings.append(
                "max_cache_memory_mb is very high, may cause memory issues"
            )

        # Validate worker settings
        max_workers = perf_config.get("max_workers", 2)
        if max_workers < 1:
            self.validation_errors.append("max_workers must be at least 1")
        elif max_workers > 16:
            self.validation_warnings.append(
                "max_workers is very high, may cause resource contention"
            )

        # Validate timeout settings
        timeouts = [
            "analysis_timeout_minutes",
            "model_load_timeout_minutes",
            "api_request_timeout_seconds",
        ]
        for timeout_key in timeouts:
            if timeout_key in perf_config:
                timeout_value = perf_config[timeout_key]
                if timeout_value <= 0:
                    self.validation_errors.append(f"{timeout_key} must be positive")

    def _validate_security(self, security_config: Dict[str, Any]) -> None:
        """Validate security configuration."""
        if not security_config:
            self.validation_warnings.append(
                "No security configuration found, using defaults"
            )
            return

        # Validate file size limits
        max_file_size = security_config.get("max_file_size_mb", 50)
        if max_file_size < 1:
            self.validation_warnings.append(
                "max_file_size_mb is very low, may reject valid documents"
            )
        elif max_file_size > 500:
            self.validation_warnings.append(
                "max_file_size_mb is very high, may cause performance issues"
            )

        # Validate allowed extensions
        allowed_extensions = security_config.get("allowed_file_extensions", [])
        if not allowed_extensions:
            self.validation_warnings.append("No allowed file extensions configured")
        else:
            for ext in allowed_extensions:
                if not ext.startswith("."):
                    self.validation_warnings.append(
                        f"File extension should start with dot: {ext}"
                    )

        # Validate rate limiting
        if security_config.get("enable_rate_limiting", True):
            max_requests = security_config.get("max_requests_per_minute", 60)
            if max_requests < 10:
                self.validation_warnings.append(
                    "max_requests_per_minute is very low, may impact usability"
                )

    def check_environment_variables(self) -> Tuple[bool, List[str]]:
        """Check for required environment variables."""
        missing_vars = []

        # Check for optional but recommended environment variables
        recommended_vars = ["SECRET_KEY", "DATABASE_URL"]

        for var in recommended_vars:
            if not os.getenv(var):
                missing_vars.append(f"Recommended environment variable not set: {var}")

        return len(missing_vars) == 0, missing_vars

    def validate_file_permissions(self) -> Tuple[bool, List[str]]:
        """Validate file and directory permissions."""
        permission_errors = []

        try:
            settings = get_settings()

            # Check temp directory permissions
            temp_dir = settings.paths.temp_upload_dir
            if not os.access(temp_dir, os.W_OK):
                permission_errors.append(
                    f"No write permission for temp directory: {temp_dir}"
                )

            # Check cache directory permissions
            cache_dir = getattr(settings.paths, "cache_dir", ".cache")
            if not os.access(cache_dir, os.W_OK):
                permission_errors.append(
                    f"No write permission for cache directory: {cache_dir}"
                )

            # Check logs directory permissions
            logs_dir = getattr(settings.paths, "logs_dir", "logs")
            if not os.access(logs_dir, os.W_OK):
                permission_errors.append(
                    f"No write permission for logs directory: {logs_dir}"
                )

        except Exception as e:
            permission_errors.append(f"Error checking permissions: {str(e)}")

        return len(permission_errors) == 0, permission_errors

    def generate_health_report(self) -> Dict[str, Any]:
        """Generate a comprehensive health report for the configuration."""
        report = {
            "timestamp": "2025-10-02",  # Would use datetime in real implementation
            "overall_status": "unknown",
            "config_validation": {},
            "environment_check": {},
            "permissions_check": {},
            "recommendations": [],
        }

        # Validate configuration
        config_valid, config_errors, config_warnings = self.validate_config_file()
        report["config_validation"] = {
            "valid": config_valid,
            "errors": config_errors,
            "warnings": config_warnings,
        }

        # Check environment variables
        env_valid, env_missing = self.check_environment_variables()
        report["environment_check"] = {
            "valid": env_valid,
            "missing_variables": env_missing,
        }

        # Check file permissions
        perm_valid, perm_errors = self.validate_file_permissions()
        report["permissions_check"] = {"valid": perm_valid, "errors": perm_errors}

        # Determine overall status
        if config_valid and env_valid and perm_valid:
            report["overall_status"] = "healthy"
        elif config_valid and perm_valid:
            report["overall_status"] = "warning"
        else:
            report["overall_status"] = "error"

        # Generate recommendations
        if config_warnings:
            report["recommendations"].append(
                "Review configuration warnings and consider adjustments"
            )

        if env_missing:
            report["recommendations"].append(
                "Set recommended environment variables for production use"
            )

        if not config_valid:
            report["recommendations"].append(
                "Fix configuration errors before running the application"
            )

        return report


def validate_configuration() -> bool:
    """Main function to validate the application configuration."""
    validator = ConfigValidator()

    # Generate health report
    health_report = validator.generate_health_report()

    # Log results
    status = health_report["overall_status"]
    logger.info(f"Configuration health check complete. Status: {status}")

    if health_report["config_validation"]["errors"]:
        logger.error("Configuration errors found:")
        for error in health_report["config_validation"]["errors"]:
            logger.error(f"  - {error}")

    if health_report["config_validation"]["warnings"]:
        logger.warning("Configuration warnings:")
        for warning in health_report["config_validation"]["warnings"]:
            logger.warning(f"  - {warning}")

    # Save health report
    try:
        import json

        with open("config_health_report.json", "w") as f:
            json.dump(health_report, f, indent=2)
        logger.info("Health report saved to config_health_report.json")
    except Exception as e:
        logger.warning(f"Failed to save health report: {e}")

    return status in ["healthy", "warning"]


if __name__ == "__main__":
    # Run validation when script is executed directly
    logging.basicConfig(level=logging.INFO)
    is_valid = validate_configuration()
    exit(0 if is_valid else 1)
