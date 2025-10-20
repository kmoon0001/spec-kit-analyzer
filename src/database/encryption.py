"""Database field encryption service.

This module provides encryption/decryption capabilities for sensitive database fields,
ensuring data protection at rest in the database.
"""

import base64
import logging
import os
from typing import Any, Optional, Type, TypeVar

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from sqlalchemy import String, TypeDecorator
from sqlalchemy.types import Text

logger = logging.getLogger(__name__)

T = TypeVar("T")


class DatabaseEncryptionService:
    """Service for encrypting and decrypting database fields."""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the database encryption service.

        Args:
            encryption_key: Base64-encoded encryption key. If None, generates from environment.
        """
        self.encryption_key = self._get_or_generate_key(encryption_key)
        self.cipher = Fernet(self.encryption_key)

    def _get_or_generate_key(self, encryption_key: Optional[str]) -> bytes:
        """Get encryption key from environment or generate a new one."""
        if encryption_key:
            try:
                # The key is already base64 encoded, just encode it to bytes
                return encryption_key.encode()
            except Exception as e:
                logger.error(f"Invalid database encryption key provided: {e}")
                raise ValueError("Invalid database encryption key format")

        # Try to get from environment
        env_key = os.environ.get("DATABASE_ENCRYPTION_KEY")
        if env_key:
            try:
                # The key is already base64 encoded, just encode it to bytes
                return env_key.encode()
            except Exception as e:
                logger.error(f"Invalid DATABASE_ENCRYPTION_KEY in environment: {e}")
                raise ValueError("Invalid DATABASE_ENCRYPTION_KEY format")

        # Generate new key from password
        password = os.environ.get(
            "DATABASE_ENCRYPTION_PASSWORD", "default-db-password-change-in-production"
        )
        salt = os.environ.get(
            "DATABASE_ENCRYPTION_SALT", "default-db-salt-change-in-production"
        ).encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        logger.warning(
            "Generated database encryption key from password. Store DATABASE_ENCRYPTION_KEY in environment for production!"
        )
        return key

    def encrypt_field(self, value: str) -> str:
        """
        Encrypt a database field value.

        Args:
            value: Value to encrypt

        Returns:
            Base64-encoded encrypted value
        """
        if not value:
            return value

        try:
            encrypted_bytes = self.cipher.encrypt(value.encode("utf-8"))
            return base64.urlsafe_b64encode(encrypted_bytes).decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to encrypt database field: {e}")
            raise ValueError(f"Database field encryption failed: {e}")

    def decrypt_field(self, encrypted_value: str) -> str:
        """
        Decrypt a database field value.

        Args:
            encrypted_value: Base64-encoded encrypted value

        Returns:
            Decrypted value
        """
        if not encrypted_value:
            return encrypted_value

        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode("utf-8"))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to decrypt database field: {e}")
            raise ValueError(f"Database field decryption failed: {e}")


class EncryptedString(TypeDecorator):
    """SQLAlchemy type for encrypted string fields."""

    impl = String
    cache_ok = True

    def __init__(self, length: int = 255, **kwargs):
        super().__init__(length=length, **kwargs)
        self._encryption_service = DatabaseEncryptionService()

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value when storing to database."""
        if value is not None:
            return self._encryption_service.encrypt_field(value)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value when loading from database."""
        if value is not None:
            return self._encryption_service.decrypt_field(value)
        return value


class EncryptedText(TypeDecorator):
    """SQLAlchemy type for encrypted text fields."""

    impl = Text
    cache_ok = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._encryption_service = DatabaseEncryptionService()

    def process_bind_param(self, value: Optional[str], dialect) -> Optional[str]:
        """Encrypt value when storing to database."""
        if value is not None:
            return self._encryption_service.encrypt_field(value)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[str]:
        """Decrypt value when loading from database."""
        if value is not None:
            return self._encryption_service.decrypt_field(value)
        return value


class EncryptedJSON(TypeDecorator):
    """SQLAlchemy type for encrypted JSON fields."""

    impl = Text
    cache_ok = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._encryption_service = DatabaseEncryptionService()

    def process_bind_param(self, value: Optional[dict], dialect) -> Optional[str]:
        """Encrypt JSON value when storing to database."""
        if value is not None:
            import json

            json_str = json.dumps(value)
            return self._encryption_service.encrypt_field(json_str)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Optional[dict]:
        """Decrypt JSON value when loading from database."""
        if value is not None:
            import json

            decrypted_str = self._encryption_service.decrypt_field(value)
            return json.loads(decrypted_str)
        return value


# Global encryption service instance
_encryption_service: Optional[DatabaseEncryptionService] = None


def get_database_encryption_service() -> DatabaseEncryptionService:
    """Get global database encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = DatabaseEncryptionService()
    return _encryption_service


def encrypt_sensitive_data(data: str) -> str:
    """Encrypt sensitive data using the global encryption service."""
    service = get_database_encryption_service()
    return service.encrypt_field(data)


def decrypt_sensitive_data(encrypted_data: str) -> str:
    """Decrypt sensitive data using the global encryption service."""
    service = get_database_encryption_service()
    return service.decrypt_field(encrypted_data)
