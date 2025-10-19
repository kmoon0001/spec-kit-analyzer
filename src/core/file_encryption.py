"""Secure file encryption service for document storage.

This module provides encryption/decryption capabilities for sensitive files
stored in the application, ensuring data protection at rest.
"""

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class FileEncryptionService:
    """Service for encrypting and decrypting files at rest."""

    def __init__(self, encryption_key: Optional[str] = None):
        """
        Initialize the encryption service.

        Args:
            encryption_key: Base64-encoded encryption key. If None, generates from environment.
        """
        self.encryption_key = self._get_or_generate_key(encryption_key)
        self.cipher = Fernet(self.encryption_key)

    def _get_or_generate_key(self, encryption_key: Optional[str]) -> bytes:
        """Get encryption key from environment or generate a new one."""
        if encryption_key:
            try:
                return base64.urlsafe_b64decode(encryption_key.encode())
            except Exception as e:
                logger.error(f"Invalid encryption key provided: {e}")
                raise ValueError("Invalid encryption key format")

        # Try to get from environment
        env_key = os.environ.get("FILE_ENCRYPTION_KEY")
        if env_key:
            try:
                return base64.urlsafe_b64decode(env_key.encode())
            except Exception as e:
                logger.error(f"Invalid FILE_ENCRYPTION_KEY in environment: {e}")
                raise ValueError("Invalid FILE_ENCRYPTION_KEY format")

        # Generate new key from password
        password = os.environ.get("FILE_ENCRYPTION_PASSWORD", "default-password-change-in-production")
        salt = os.environ.get("FILE_ENCRYPTION_SALT", "default-salt-change-in-production").encode()

        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))

        logger.warning("Generated encryption key from password. Store FILE_ENCRYPTION_KEY in environment for production!")
        return key

    def encrypt_file_content(self, content: bytes) -> bytes:
        """
        Encrypt file content.

        Args:
            content: Raw file content to encrypt

        Returns:
            Encrypted content
        """
        try:
            return self.cipher.encrypt(content)
        except Exception as e:
            logger.error(f"Failed to encrypt file content: {e}")
            raise ValueError(f"Encryption failed: {e}")

    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """
        Decrypt file content.

        Args:
            encrypted_content: Encrypted content to decrypt

        Returns:
            Decrypted content
        """
        try:
            return self.cipher.decrypt(encrypted_content)
        except Exception as e:
            logger.error(f"Failed to decrypt file content: {e}")
            raise ValueError(f"Decryption failed: {e}")

    def encrypt_text(self, text: str) -> str:
        """
        Encrypt text content.

        Args:
            text: Text to encrypt

        Returns:
            Base64-encoded encrypted text
        """
        try:
            encrypted_bytes = self.cipher.encrypt(text.encode('utf-8'))
            return base64.urlsafe_b64encode(encrypted_bytes).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to encrypt text: {e}")
            raise ValueError(f"Text encryption failed: {e}")

    def decrypt_text(self, encrypted_text: str) -> str:
        """
        Decrypt text content.

        Args:
            encrypted_text: Base64-encoded encrypted text

        Returns:
            Decrypted text
        """
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_text.encode('utf-8'))
            decrypted_bytes = self.cipher.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to decrypt text: {e}")
            raise ValueError(f"Text decryption failed: {e}")


class SecureDocumentStorage:
    """Secure storage for documents with encryption and access control."""

    def __init__(self, storage_dir: str = "secure_storage", encryption_service: Optional[FileEncryptionService] = None):
        """
        Initialize secure document storage.

        Args:
            storage_dir: Directory to store encrypted files
            encryption_service: Encryption service instance
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.encryption_service = encryption_service or FileEncryptionService()
        self.metadata_file = self.storage_dir / "metadata.json"
        self._metadata = self._load_metadata()

    def _load_metadata(self) -> Dict[str, Any]:
        """Load storage metadata."""
        if self.metadata_file.exists():
            try:
                import json
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load metadata: {e}")
        return {}

    def _save_metadata(self):
        """Save storage metadata."""
        try:
            import json
            with open(self.metadata_file, 'w') as f:
                json.dump(self._metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    def store_document(self, content: bytes, filename: str, user_id: int, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store encrypted document.

        Args:
            content: Document content
            filename: Original filename
            user_id: User who owns the document
            metadata: Additional metadata

        Returns:
            Document ID for retrieval
        """
        import uuid
        import datetime

        doc_id = str(uuid.uuid4())
        encrypted_content = self.encryption_service.encrypt_file_content(content)

        # Store encrypted file
        file_path = self.storage_dir / f"{doc_id}.enc"
        with open(file_path, 'wb') as f:
            f.write(encrypted_content)

        # Store metadata
        self._metadata[doc_id] = {
            "filename": filename,
            "user_id": user_id,
            "stored_at": datetime.datetime.utcnow().isoformat(),
            "file_size": len(content),
            "encrypted_size": len(encrypted_content),
            "metadata": metadata or {}
        }
        self._save_metadata()

        logger.info(f"Stored encrypted document {doc_id} for user {user_id}")
        return doc_id

    def retrieve_document(self, doc_id: str, user_id: int) -> Optional[bytes]:
        """
        Retrieve and decrypt document.

        Args:
            doc_id: Document ID
            user_id: User requesting the document

        Returns:
            Decrypted document content or None if not found/unauthorized
        """
        if doc_id not in self._metadata:
            logger.warning(f"Document {doc_id} not found")
            return None

        doc_metadata = self._metadata[doc_id]
        if doc_metadata["user_id"] != user_id:
            logger.warning(f"User {user_id} not authorized to access document {doc_id}")
            return None

        file_path = self.storage_dir / f"{doc_id}.enc"
        if not file_path.exists():
            logger.error(f"Encrypted file not found for document {doc_id}")
            return None

        try:
            with open(file_path, 'rb') as f:
                encrypted_content = f.read()

            decrypted_content = self.encryption_service.decrypt_file_content(encrypted_content)
            logger.info(f"Retrieved document {doc_id} for user {user_id}")
            return decrypted_content
        except Exception as e:
            logger.error(f"Failed to decrypt document {doc_id}: {e}")
            return None

    def delete_document(self, doc_id: str, user_id: int) -> bool:
        """
        Delete document.

        Args:
            doc_id: Document ID
            user_id: User requesting deletion

        Returns:
            True if deleted successfully
        """
        if doc_id not in self._metadata:
            return False

        doc_metadata = self._metadata[doc_id]
        if doc_metadata["user_id"] != user_id:
            logger.warning(f"User {user_id} not authorized to delete document {doc_id}")
            return False

        # Delete encrypted file
        file_path = self.storage_dir / f"{doc_id}.enc"
        if file_path.exists():
            file_path.unlink()

        # Remove metadata
        del self._metadata[doc_id]
        self._save_metadata()

        logger.info(f"Deleted document {doc_id} for user {user_id}")
        return True

    def list_user_documents(self, user_id: int) -> list[Dict[str, Any]]:
        """
        List documents for a user.

        Args:
            user_id: User ID

        Returns:
            List of document metadata
        """
        user_docs = []
        for doc_id, metadata in self._metadata.items():
            if metadata["user_id"] == user_id:
                user_docs.append({
                    "doc_id": doc_id,
                    "filename": metadata["filename"],
                    "stored_at": metadata["stored_at"],
                    "file_size": metadata["file_size"],
                    "metadata": metadata["metadata"]
                })

        return user_docs

    def cleanup_expired_documents(self, max_age_hours: int = 24):
        """
        Clean up documents older than specified age.

        Args:
            max_age_hours: Maximum age in hours
        """
        import datetime

        cutoff_time = datetime.datetime.utcnow() - datetime.timedelta(hours=max_age_hours)
        expired_docs = []

        for doc_id, metadata in self._metadata.items():
            stored_at = datetime.datetime.fromisoformat(metadata["stored_at"])
            if stored_at < cutoff_time:
                expired_docs.append(doc_id)

        for doc_id in expired_docs:
            file_path = self.storage_dir / f"{doc_id}.enc"
            if file_path.exists():
                file_path.unlink()
            del self._metadata[doc_id]

        if expired_docs:
            self._save_metadata()
            logger.info(f"Cleaned up {len(expired_docs)} expired documents")


# Global instances
_encryption_service: Optional[FileEncryptionService] = None
_secure_storage: Optional[SecureDocumentStorage] = None


def get_encryption_service() -> FileEncryptionService:
    """Get global encryption service instance."""
    global _encryption_service
    if _encryption_service is None:
        _encryption_service = FileEncryptionService()
    return _encryption_service


def get_secure_storage() -> SecureDocumentStorage:
    """Get global secure storage instance."""
    global _secure_storage
    if _secure_storage is None:
        _secure_storage = SecureDocumentStorage()
    return _secure_storage
