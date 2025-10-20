"""Advanced Security Enhancement System for Clinical Compliance Analysis.

This module implements comprehensive security improvements including:
- Advanced authentication and authorization
- Data encryption and protection
- Security monitoring and logging
- Threat detection and prevention
- Compliance with healthcare security standards
"""

import asyncio
import hashlib
import logging
import secrets
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import jwt
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

logger = logging.getLogger(__name__)


class SecurityLevel(Enum):
    """Security levels for different operations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ThreatType(Enum):
    """Types of security threats."""
    BRUTE_FORCE = "brute_force"
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    DATA_BREACH = "data_breach"
    UNAUTHORIZED_ACCESS = "unauthorized_access"


class SecurityEvent(BaseModel):
    """Security event record."""
    event_id: str
    event_type: str
    severity: SecurityLevel
    timestamp: datetime
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    description: str
    details: Dict[str, Any] = Field(default_factory=dict)
    resolved: bool = False


class AdvancedSecuritySystem:
    """Advanced security system for clinical compliance analysis."""

    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize the security system."""
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher_suite = Fernet(self.encryption_key)

        # Security monitoring
        self.security_events: List[SecurityEvent] = []
        self.failed_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}

        # Rate limiting
        self.rate_limits: Dict[str, List[datetime]] = {}

        # Security policies
        self.policies = {
            'max_failed_attempts': 5,
            'lockout_duration_minutes': 30,
            'rate_limit_requests_per_minute': 100,
            'session_timeout_minutes': 60,
            'password_min_length': 12,
            'require_mfa': True
        }

        logger.info("Advanced security system initialized")

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error("Failed to encrypt data: %s", e)
            raise

    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error("Failed to decrypt data: %s", e)
            raise

    def generate_secure_token(self, user_id: int, expires_in_hours: int = 24) -> str:
        """Generate secure JWT token."""
        try:
            payload = {
                'user_id': user_id,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(hours=expires_in_hours),
                'jti': secrets.token_urlsafe(32)  # JWT ID for tracking
            }

            token = jwt.encode(payload, self.encryption_key, algorithm='HS256')
            return token

        except Exception as e:
            logger.error("Failed to generate token: %s", e)
            raise

    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Validate JWT token."""
        try:
            payload = jwt.decode(token, self.encryption_key, algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("Token expired")
            return None
        except jwt.InvalidTokenError:
            logger.warning("Invalid token")
            return None

    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = secrets.token_hex(32)

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt.encode(),
            iterations=100000,
        )

        key = base64.b64encode(kdf.derive(password.encode()))
        return key.decode(), salt

    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against hash."""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt.encode(),
                iterations=100000,
            )

            key = base64.b64encode(kdf.derive(password.encode()))
            return key.decode() == hashed_password

        except Exception as e:
            logger.error("Failed to verify password: %s", e)
            return False

    def check_rate_limit(self, identifier: str) -> bool:
        """Check if request is within rate limit."""
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        # Remove old requests
        self.rate_limits[identifier] = [
            req_time for req_time in self.rate_limits[identifier]
            if req_time > minute_ago
        ]

        # Check if within limit
        if len(self.rate_limits[identifier]) >= self.policies['rate_limit_requests_per_minute']:
            return False

        # Add current request
        self.rate_limits[identifier].append(now)
        return True

    def record_failed_attempt(self, identifier: str) -> bool:
        """Record failed authentication attempt."""
        now = datetime.now()

        if identifier not in self.failed_attempts:
            self.failed_attempts[identifier] = []

        self.failed_attempts[identifier].append(now)

        # Check if should be blocked
        recent_attempts = [
            attempt for attempt in self.failed_attempts[identifier]
            if attempt > now - timedelta(minutes=self.policies['lockout_duration_minutes'])
        ]

        if len(recent_attempts) >= self.policies['max_failed_attempts']:
            self.blocked_ips[identifier] = now
            self.log_security_event(
                event_type="account_locked",
                severity=SecurityLevel.HIGH,
                description=f"Account locked due to {len(recent_attempts)} failed attempts",
                details={"identifier": identifier, "attempts": len(recent_attempts)}
            )
            return False

        return True

    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is blocked."""
        if identifier not in self.blocked_ips:
            return False

        block_time = self.blocked_ips[identifier]
        if datetime.now() - block_time > timedelta(minutes=self.policies['lockout_duration_minutes']):
            del self.blocked_ips[identifier]
            return False

        return True

    def log_security_event(
        self,
        event_type: str,
        severity: SecurityLevel,
        description: str,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> str:
        """Log security event."""
        event_id = secrets.token_urlsafe(16)

        event = SecurityEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(),
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            description=description,
            details=details or {}
        )

        self.security_events.append(event)

        # Log to file
        logger.warning(
            "Security event: %s - %s (Severity: %s)",
            event_type, description, severity.value
        )

        return event_id

    def detect_threats(self, request_data: Dict[str, Any]) -> List[ThreatType]:
        """Detect potential security threats."""
        threats = []

        # Check for SQL injection
        if self._detect_sql_injection(request_data):
            threats.append(ThreatType.SQL_INJECTION)

        # Check for XSS
        if self._detect_xss(request_data):
            threats.append(ThreatType.XSS)

        # Check for CSRF
        if self._detect_csrf(request_data):
            threats.append(ThreatType.CSRF)

        return threats

    def _detect_sql_injection(self, data: Dict[str, Any]) -> bool:
        """Detect SQL injection attempts."""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(--|\#|\/\*|\*\/)",
            r"(\b(EXEC|EXECUTE|SP_|XP_)\b)"
        ]

        import re
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in sql_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True

        return False

    def _detect_xss(self, data: Dict[str, Any]) -> bool:
        """Detect XSS attempts."""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>"
        ]

        import re
        for key, value in data.items():
            if isinstance(value, str):
                for pattern in xss_patterns:
                    if re.search(pattern, value, re.IGNORECASE):
                        return True

        return False

    def _detect_csrf(self, data: Dict[str, Any]) -> bool:
        """Detect CSRF attempts."""
        # Check for missing CSRF token in state-changing operations
        if 'csrf_token' not in data and any(key in data for key in ['password', 'email', 'delete']):
            return True

        return False

    def sanitize_input(self, data: Any) -> Any:
        """Sanitize user input."""
        if isinstance(data, str):
            # Remove potentially dangerous characters
            import html
            return html.escape(data.strip())
        elif isinstance(data, dict):
            return {key: self.sanitize_input(value) for key, value in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_input(item) for item in data]
        else:
            return data

    def get_security_report(self) -> Dict[str, Any]:
        """Get comprehensive security report."""
        now = datetime.now()
        last_24h = now - timedelta(hours=24)

        recent_events = [
            event for event in self.security_events
            if event.timestamp > last_24h
        ]

        return {
            "security_summary": {
                "total_events_24h": len(recent_events),
                "high_severity_events": len([e for e in recent_events if e.severity == SecurityLevel.HIGH]),
                "critical_events": len([e for e in recent_events if e.severity == SecurityLevel.CRITICAL]),
                "blocked_ips": len(self.blocked_ips),
                "active_rate_limits": len(self.rate_limits)
            },
            "recent_events": [
                {
                    "event_id": event.event_id,
                    "event_type": event.event_type,
                    "severity": event.severity.value,
                    "timestamp": event.timestamp.isoformat(),
                    "description": event.description
                }
                for event in recent_events[-10:]  # Last 10 events
            ],
            "security_policies": self.policies,
            "generated_at": now.isoformat()
        }


# Global security system instance
security_system = AdvancedSecuritySystem()
