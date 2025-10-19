"""Enhanced configuration management with validation and caching.

This module provides improved configuration management including:
- Configuration validation
- Environment-specific settings
- Configuration caching
- Runtime configuration updates
"""

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class DatabaseConfig(BaseModel):
    """Database configuration with validation."""
    url: str = Field(..., description="Database connection URL")
    echo: bool = Field(default=False, description="Enable SQL query logging")
    pool_size: int = Field(default=10, ge=1, le=100, description="Connection pool size")
    max_overflow: int = Field(default=20, ge=0, le=200, description="Maximum overflow connections")
    pool_timeout: int = Field(default=30, ge=1, le=300, description="Pool timeout in seconds")
    pool_recycle: int = Field(default=3600, ge=300, le=7200, description="Connection recycle time")
    sqlite_optimizations: bool = Field(default=True, description="Enable SQLite optimizations")
    connection_timeout: int = Field(default=20, ge=1, le=120, description="Connection timeout")

    @validator('pool_size')
    def validate_pool_size(cls, v, values):
        """Validate pool size is reasonable."""
        if v < 1 or v > 100:
            raise ValueError("Pool size must be between 1 and 100")
        return v

    @validator('max_overflow')
    def validate_max_overflow(cls, v, values):
        """Validate max overflow is reasonable."""
        if v < 0 or v > 200:
            raise ValueError("Max overflow must be between 0 and 200")
        return v


class AuthConfig(BaseModel):
    """Authentication configuration with validation."""
    secret_key: str = Field(..., min_length=32, description="JWT secret key")
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(default=30, ge=5, le=1440, description="Token expiration in minutes")

    @validator('secret_key')
    def validate_secret_key(cls, v):
        """Validate secret key strength."""
        if len(v) < 32:
            raise ValueError("Secret key must be at least 32 characters long")
        return v

    @validator('access_token_expire_minutes')
    def validate_token_expiry(cls, v):
        """Validate token expiry is reasonable."""
        if v < 5 or v > 1440:  # 5 minutes to 24 hours
            raise ValueError("Token expiry must be between 5 minutes and 24 hours")
        return v


class PerformanceConfig(BaseModel):
    """Performance configuration with validation."""
    max_workers: int = Field(default=4, ge=1, le=16, description="Maximum worker threads")
    batch_size: int = Field(default=4, ge=1, le=32, description="Batch processing size")
    max_chunk_size: int = Field(default=2000, ge=500, le=10000, description="Maximum chunk size")
    overlap_size: int = Field(default=200, ge=50, le=1000, description="Chunk overlap size")
    enable_caching: bool = Field(default=True, description="Enable caching")
    cache_ttl_hours: int = Field(default=24, ge=1, le=168, description="Cache TTL in hours")

    @validator('max_workers')
    def validate_max_workers(cls, v):
        """Validate max workers is reasonable."""
        if v < 1 or v > 16:
            raise ValueError("Max workers must be between 1 and 16")
        return v


class LoggingConfig(BaseModel):
    """Logging configuration with validation."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file_enabled: bool = Field(default=True, description="Enable file logging")
    console_enabled: bool = Field(default=True, description="Enable console logging")
    max_file_size_mb: int = Field(default=10, ge=1, le=100, description="Maximum log file size")
    backup_count: int = Field(default=5, ge=1, le=20, description="Number of backup files")

    @validator('level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()


class EnhancedSettings(BaseSettings):
    """Enhanced application settings with comprehensive validation."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
        case_sensitive=False
    )

    # Core settings
    app_name: str = Field(default="ElectroAnalyzer", description="Application name")
    version: str = Field(default="1.0.0", description="Application version")
    environment: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    auth: AuthConfig = Field(default_factory=AuthConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)

    # API settings
    host: str = Field(default="127.0.0.1", description="API host")
    port: int = Field(default=8001, ge=1024, le=65535, description="API port")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"], description="CORS origins")

    # Feature flags
    use_ai_mocks: bool = Field(default=False, description="Use AI mocks")
    enable_director_dashboard: bool = Field(default=True, description="Enable director dashboard")
    enable_advanced_analytics: bool = Field(default=True, description="Enable advanced analytics")

    @validator('environment')
    def validate_environment(cls, v):
        """Validate environment setting."""
        valid_envs = ['development', 'testing', 'staging', 'production']
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of: {valid_envs}")
        return v.lower()

    @validator('port')
    def validate_port(cls, v):
        """Validate port number."""
        if v < 1024 or v > 65535:
            raise ValueError("Port must be between 1024 and 65535")
        return v

    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    def get_database_url(self) -> str:
        """Get database URL with environment-specific modifications."""
        if self.is_production():
            # In production, ensure secure connection
            if not self.database.url.startswith(('postgresql://', 'mysql://')):
                logger.warning("Production should use PostgreSQL or MySQL, not SQLite")
        return self.database.url


class ConfigurationManager:
    """Configuration manager with caching and validation."""

    def __init__(self):
        self._settings: Optional[EnhancedSettings] = None
        self._config_cache: Dict[str, Any] = {}
        self._last_loaded: Optional[float] = None

    def load_settings(self, force_reload: bool = False) -> EnhancedSettings:
        """Load settings with caching."""
        import time

        if self._settings is None or force_reload:
            try:
                # Load environment variables
                load_dotenv()

                # Load config file
                config_path = Path(__file__).parent.parent / "config.yaml"
                config_data = {}
                if config_path.exists():
                    with open(config_path, encoding="utf-8") as f:
                        config_data = yaml.safe_load(f) or {}

                # Create settings with validation
                self._settings = EnhancedSettings(**config_data)
                self._last_loaded = time.time()

                logger.info(f"Configuration loaded successfully for environment: {self._settings.environment}")

            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")
                raise

        return self._settings

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting value."""
        if self._settings is None:
            self.load_settings()

        # Support dot notation for nested settings
        keys = key.split('.')
        value = self._settings
        for k in keys:
            if hasattr(value, k):
                value = getattr(value, k)
            else:
                return default

        return value

    def update_setting(self, key: str, value: Any) -> bool:
        """Update a setting value at runtime."""
        try:
            if self._settings is None:
                self.load_settings()

            # Support dot notation for nested settings
            keys = key.split('.')
            obj = self._settings
            for k in keys[:-1]:
                if hasattr(obj, k):
                    obj = getattr(obj, k)
                else:
                    return False

            setattr(obj, keys[-1], value)
            logger.info(f"Setting updated: {key} = {value}")
            return True

        except Exception as e:
            logger.error(f"Failed to update setting {key}: {e}")
            return False

    def validate_configuration(self) -> Dict[str, Any]:
        """Validate current configuration."""
        if self._settings is None:
            self.load_settings()

        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "environment": self._settings.environment
        }

        try:
            # Validate database configuration
            if self._settings.database.url.startswith('sqlite://') and self._settings.is_production():
                validation_results["warnings"].append("SQLite not recommended for production")

            # Validate authentication
            if len(self._settings.auth.secret_key) < 32:
                validation_results["errors"].append("Secret key too short")
                validation_results["valid"] = False

            # Validate performance settings
            if self._settings.performance.max_workers > 8 and not self._settings.is_production():
                validation_results["warnings"].append("High worker count may impact development performance")

        except Exception as e:
            validation_results["errors"].append(f"Validation error: {e}")
            validation_results["valid"] = False

        return validation_results

    def get_environment_summary(self) -> Dict[str, Any]:
        """Get environment configuration summary."""
        if self._settings is None:
            self.load_settings()

        return {
            "environment": self._settings.environment,
            "debug": self._settings.debug,
            "database_type": self._settings.database.url.split('://')[0],
            "api_host": self._settings.host,
            "api_port": self._settings.port,
            "features": {
                "ai_mocks": self._settings.use_ai_mocks,
                "director_dashboard": self._settings.enable_director_dashboard,
                "advanced_analytics": self._settings.enable_advanced_analytics,
            },
            "performance": {
                "max_workers": self._settings.performance.max_workers,
                "batch_size": self._settings.performance.batch_size,
                "caching_enabled": self._settings.performance.enable_caching,
            }
        }


# Global configuration manager
_config_manager = ConfigurationManager()


@lru_cache(maxsize=1)
def get_enhanced_settings() -> EnhancedSettings:
    """Get enhanced settings with caching."""
    return _config_manager.load_settings()


def get_config_manager() -> ConfigurationManager:
    """Get configuration manager instance."""
    return _config_manager


def reload_configuration() -> EnhancedSettings:
    """Reload configuration from files."""
    return _config_manager.load_settings(force_reload=True)
