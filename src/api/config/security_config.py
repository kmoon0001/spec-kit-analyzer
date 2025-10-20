"""Security Configuration for Clinical Compliance Analysis API.

This module provides security configuration and utilities.
"""

import os
from typing import Optional
from pydantic import BaseSettings, Field


class SecurityConfig(BaseSettings):
    """Security configuration settings."""

    # JWT Configuration
    jwt_secret_key: str = Field(..., description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_access_token_expire_minutes: int = Field(default=30, description="Access token expiration")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh token expiration")

    # Password Security
    password_min_length: int = Field(default=12, description="Minimum password length")
    password_require_uppercase: bool = Field(default=True, description="Require uppercase letters")
    password_require_lowercase: bool = Field(default=True, description="Require lowercase letters")
    password_require_numbers: bool = Field(default=True, description="Require numbers")
    password_require_special: bool = Field(default=True, description="Require special characters")
    password_max_age_days: int = Field(default=90, description="Maximum password age")

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, description="Requests per minute limit")
    rate_limit_burst_size: int = Field(default=10, description="Burst size for rate limiting")
    rate_limit_window_minutes: int = Field(default=1, description="Rate limit window")

    # Session Security
    session_timeout_minutes: int = Field(default=30, description="Session timeout")
    session_max_concurrent: int = Field(default=3, description="Max concurrent sessions per user")
    session_require_https: bool = Field(default=True, description="Require HTTPS for sessions")

    # File Upload Security
    max_file_size_mb: int = Field(default=50, description="Maximum file size in MB")
    allowed_file_types: list[str] = Field(default=[".pdf", ".doc", ".docx", ".txt"], description="Allowed file types")
    scan_uploaded_files: bool = Field(default=True, description="Scan uploaded files for threats")

    # API Security
    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: list[str] = Field(default=["http://localhost:3000"], description="Allowed CORS origins")
    enable_csrf_protection: bool = Field(default=True, description="Enable CSRF protection")
    csrf_token_expire_minutes: int = Field(default=30, description="CSRF token expiration")

    # Logging and Monitoring
    log_security_events: bool = Field(default=True, description="Log security events")
    log_failed_attempts: bool = Field(default=True, description="Log failed authentication attempts")
    log_suspicious_activity: bool = Field(default=True, description="Log suspicious activity")
    security_log_retention_days: int = Field(default=90, description="Security log retention period")

    # Threat Detection
    enable_threat_detection: bool = Field(default=True, description="Enable threat detection")
    threat_detection_sensitivity: str = Field(default="medium", description="Threat detection sensitivity")
    auto_block_suspicious_ips: bool = Field(default=True, description="Auto-block suspicious IPs")
    block_duration_hours: int = Field(default=24, description="IP block duration")

    # Data Protection
    enable_data_encryption: bool = Field(default=True, description="Enable data encryption")
    encryption_key: Optional[str] = Field(default=None, description="Data encryption key")
    enable_phi_detection: bool = Field(default=True, description="Enable PHI detection")
    phi_redaction_enabled: bool = Field(default=True, description="Enable PHI redaction")

    # Compliance
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    audit_log_retention_days: int = Field(default=2555, description="Audit log retention (7 years)")
    enable_compliance_monitoring: bool = Field(default=True, description="Enable compliance monitoring")

    class Config:
        env_prefix = "SECURITY_"
        case_sensitive = False


# Global security configuration
security_config = SecurityConfig()


def get_security_config() -> SecurityConfig:
    """Get security configuration."""
    return security_config


def validate_security_config() -> bool:
    """Validate security configuration."""
    try:
        config = get_security_config()

        # Validate JWT secret
        if not config.jwt_secret_key or len(config.jwt_secret_key) < 32:
            raise ValueError("JWT secret key must be at least 32 characters")

        # Validate password requirements
        if config.password_min_length < 8:
            raise ValueError("Password minimum length must be at least 8")

        # Validate rate limiting
        if config.rate_limit_requests_per_minute < 1:
            raise ValueError("Rate limit must be at least 1 request per minute")

        # Validate file upload limits
        if config.max_file_size_mb < 1:
            raise ValueError("Maximum file size must be at least 1 MB")

        return True

    except Exception as e:
        print(f"Security configuration validation failed: {e}")
        return False


# Validate configuration on import
if not validate_security_config():
    raise RuntimeError("Invalid security configuration")
