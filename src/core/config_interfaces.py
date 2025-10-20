"""Configuration interfaces and implementations.

This module provides configuration interfaces and their implementations
for different components of the application.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

from src.core.interfaces import (
    AIConfigInterface,
    DatabaseConfigInterface,
    SecurityConfigInterface,
)


class Environment(str, Enum):
    """Environment enumeration."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration implementation."""

    url: str
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.url:
            raise ValueError("Database URL is required")
        if self.pool_size <= 0:
            raise ValueError("Pool size must be positive")
        if self.max_overflow < 0:
            raise ValueError("Max overflow cannot be negative")


@dataclass
class SecurityConfig:
    """Security configuration implementation."""

    secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    encryption_key: str = ""
    session_timeout_minutes: int = 30
    max_sessions_per_user: int = 5
    password_min_length: int = 8
    password_require_special: bool = True
    password_require_numbers: bool = True
    password_require_uppercase: bool = True
    rate_limit_requests_per_minute: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.secret_key:
            raise ValueError("Secret key is required")
        if len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        if self.access_token_expire_minutes <= 0:
            raise ValueError("Access token expiration must be positive")
        if self.password_min_length < 6:
            raise ValueError("Password minimum length must be at least 6")


@dataclass
class AIConfig:
    """AI service configuration implementation."""

    model_name: str = "gpt-3.5-turbo"
    max_tokens: int = 4000
    temperature: float = 0.7
    top_p: float = 1.0
    frequency_penalty: float = 0.0
    presence_penalty: float = 0.0
    timeout_seconds: int = 30
    max_retries: int = 3
    api_key: str = ""
    base_url: str = ""
    use_mocks: bool = False

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not self.use_mocks and not self.api_key:
            raise ValueError("API key is required when not using mocks")
        if self.max_tokens <= 0:
            raise ValueError("Max tokens must be positive")
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError("Temperature must be between 0.0 and 2.0")
        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")


@dataclass
class FileStorageConfig:
    """File storage configuration implementation."""

    storage_dir: str = "secure_storage"
    max_file_size_mb: int = 50
    allowed_extensions: list[str] = None
    encryption_enabled: bool = True
    cleanup_interval_hours: int = 24
    max_age_hours: int = 168  # 7 days

    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.max_file_size_mb <= 0:
            raise ValueError("Max file size must be positive")
        if self.allowed_extensions is None:
            self.allowed_extensions = [".pdf", ".docx", ".txt", ".rtf"]
        if self.cleanup_interval_hours <= 0:
            raise ValueError("Cleanup interval must be positive")
        if self.max_age_hours <= 0:
            raise ValueError("Max age must be positive")


@dataclass
class LoggingConfig:
    """Logging configuration implementation."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size_mb: int = 10
    backup_count: int = 5
    enable_console: bool = True
    enable_file: bool = False
    enable_json: bool = False
    correlation_id_header: str = "X-Request-ID"

    def __post_init__(self):
        """Validate configuration after initialization."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.level.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        if self.max_file_size_mb <= 0:
            raise ValueError("Max file size must be positive")
        if self.backup_count < 0:
            raise ValueError("Backup count cannot be negative")


@dataclass
class APIConfig:
    """API configuration implementation."""

    host: str = "127.0.0.1"
    port: int = 8001
    debug: bool = False
    reload: bool = False
    workers: int = 1
    cors_origins: list[str] = None
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = None
    cors_allow_headers: list[str] = None
    enable_docs: bool = True
    enable_redoc: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"

    def __post_init__(self):
        """Validate configuration after initialization."""
        if not 1 <= self.port <= 65535:
            raise ValueError("Port must be between 1 and 65535")
        if self.workers <= 0:
            raise ValueError("Workers must be positive")
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
        if self.cors_allow_methods is None:
            self.cors_allow_methods = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
        if self.cors_allow_headers is None:
            self.cors_allow_headers = ["*"]


@dataclass
class ApplicationConfig:
    """Main application configuration."""

    environment: Environment = Environment.DEVELOPMENT
    app_name: str = "Therapy Compliance Analyzer"
    app_version: str = "1.0.0"
    debug: bool = False
    testing: bool = False

    # Sub-configurations
    database: DatabaseConfig = None
    security: SecurityConfig = None
    ai: AIConfig = None
    file_storage: FileStorageConfig = None
    logging: LoggingConfig = None
    api: APIConfig = None

    def __post_init__(self):
        """Initialize default configurations if not provided."""
        if self.database is None:
            self.database = DatabaseConfig(url="sqlite:///./compliance.db")
        if self.security is None:
            self.security = SecurityConfig(
                secret_key="default-secret-key-change-in-production"
            )
        if self.ai is None:
            self.ai = AIConfig(use_mocks=True)
        if self.file_storage is None:
            self.file_storage = FileStorageConfig()
        if self.logging is None:
            self.logging = LoggingConfig()
        if self.api is None:
            self.api = APIConfig()


class ConfigValidator:
    """Configuration validator."""

    @staticmethod
    def validate_config(config: ApplicationConfig) -> tuple[bool, Optional[str]]:
        """
        Validate application configuration.

        Args:
            config: Application configuration to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Validate database config
            if not config.database.url:
                return False, "Database URL is required"

            # Validate security config
            if not config.security.secret_key:
                return False, "Security secret key is required"

            if len(config.security.secret_key) < 32:
                return False, "Security secret key must be at least 32 characters"

            # Validate AI config
            if not config.ai.use_mocks and not config.ai.api_key:
                return False, "AI API key is required when not using mocks"

            # Validate API config
            if not 1 <= config.api.port <= 65535:
                return False, "API port must be between 1 and 65535"

            return True, None

        except Exception as e:
            return False, f"Configuration validation error: {str(e)}"

    @staticmethod
    def get_production_recommendations(config: ApplicationConfig) -> list[str]:
        """
        Get production configuration recommendations.

        Args:
            config: Application configuration

        Returns:
            List of recommendations
        """
        recommendations = []

        if config.environment == Environment.PRODUCTION:
            if config.security.secret_key == "default-secret-key-change-in-production":
                recommendations.append("Change default security secret key")

            if config.database.url.startswith("sqlite"):
                recommendations.append(
                    "Consider using PostgreSQL or MySQL for production"
                )

            if config.api.debug:
                recommendations.append("Disable debug mode in production")

            if config.api.reload:
                recommendations.append("Disable auto-reload in production")

            if config.logging.level == "DEBUG":
                recommendations.append("Use INFO or WARNING log level in production")

            if not config.security.password_require_special:
                recommendations.append(
                    "Enable special character requirement for passwords"
                )

        return recommendations
