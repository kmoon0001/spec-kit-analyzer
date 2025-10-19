"""Enhanced file upload validation with magic number detection.

This module provides comprehensive file validation including:
- Magic number (file signature) validation
- Content scanning for malicious patterns
- File size and type restrictions
- Virus scanning integration points
"""

import logging
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class FileMagicValidator:
    """Validates files using magic numbers (file signatures)."""

    # File signatures (magic numbers) for allowed file types
    MAGIC_SIGNATURES: Dict[str, List[bytes]] = {
        'pdf': [
            b'%PDF-',  # PDF files
        ],
        'docx': [
            b'PK\x03\x04',  # ZIP-based format (DOCX, XLSX, PPTX)
        ],
        'doc': [
            b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1',  # Microsoft Office legacy format
        ],
        'txt': [
            b'',  # Text files have no signature, validate by content
        ],
    }

    # Maximum file sizes by type (in bytes)
    MAX_FILE_SIZES: Dict[str, int] = {
        'pdf': 50 * 1024 * 1024,  # 50MB
        'docx': 25 * 1024 * 1024,  # 25MB
        'doc': 25 * 1024 * 1024,   # 25MB
        'txt': 10 * 1024 * 1024,   # 10MB
    }

    # Dangerous patterns in file content
    DANGEROUS_PATTERNS: List[bytes] = [
        b'<script',  # JavaScript
        b'javascript:',  # JavaScript protocol
        b'vbscript:',  # VBScript
        b'<iframe',  # Iframe injection
        b'<object',  # Object injection
        b'<embed',  # Embed injection
        b'<link',  # Link injection
        b'<meta',  # Meta injection
        b'<style',  # Style injection
        b'expression(',  # CSS expression
        b'@import',  # CSS import
        b'data:text/html',  # Data URI HTML
        b'data:application/javascript',  # Data URI JS
        b'blob:',  # Blob URL
        b'file:',  # File protocol
        b'ftp:',  # FTP protocol
        b'gopher:',  # Gopher protocol
        b'jar:',  # JAR protocol
        b'ldap:',  # LDAP protocol
        b'mailto:',  # Mailto protocol
        b'tel:',  # Tel protocol
        b'telnet:',  # Telnet protocol
        b'ws:',  # WebSocket protocol
        b'wss:',  # Secure WebSocket protocol
    ]

    @classmethod
    def validate_file(cls, file_content: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[bool, str]:
        """
        Comprehensive file validation.

        Args:
            file_content: Raw file content
            filename: Original filename
            content_type: MIME type from upload

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # 1. Basic file size check
            if len(file_content) == 0:
                return False, "File is empty"

            if len(file_content) > max(cls.MAX_FILE_SIZES.values()):
                return False, f"File size exceeds maximum allowed size"

            # 2. Determine file type from extension
            file_ext = Path(filename).suffix.lower().lstrip('.')
            if file_ext not in cls.MAGIC_SIGNATURES:
                return False, f"File type '{file_ext}' is not allowed"

            # 3. Check file size for specific type
            if len(file_content) > cls.MAX_FILE_SIZES.get(file_ext, 0):
                max_size_mb = cls.MAX_FILE_SIZES[file_ext] // (1024 * 1024)
                return False, f"File size exceeds maximum allowed size for {file_ext} files ({max_size_mb}MB)"

            # 4. Validate magic number
            if not cls._validate_magic_number(file_content, file_ext):
                return False, f"File content does not match expected format for {file_ext} files"

            # 5. Content scanning for malicious patterns
            if not cls._scan_content(file_content):
                return False, "File contains potentially malicious content"

            # 6. Additional validation based on file type
            if file_ext == 'txt':
                if not cls._validate_text_content(file_content):
                    return False, "Text file contains invalid characters or encoding"

            return True, "File validation passed"

        except Exception as e:
            logger.error(f"File validation error: {e}")
            return False, "File validation failed due to internal error"

    @classmethod
    def _validate_magic_number(cls, content: bytes, file_type: str) -> bool:
        """Validate file magic number."""
        if file_type not in cls.MAGIC_SIGNATURES:
            return False

        signatures = cls.MAGIC_SIGNATURES[file_type]

        # For text files, we don't check magic number
        if file_type == 'txt':
            return True

        # Check if content starts with any of the expected signatures
        for signature in signatures:
            if content.startswith(signature):
                return True

        return False

    @classmethod
    def _scan_content(cls, content: bytes) -> bool:
        """Scan file content for dangerous patterns."""
        try:
            # Convert to lowercase for case-insensitive matching
            content_lower = content.lower()

            # Check for dangerous patterns
            for pattern in cls.DANGEROUS_PATTERNS:
                if pattern.lower() in content_lower:
                    logger.warning(f"Dangerous pattern detected in file: {pattern}")
                    return False

            # Additional checks for specific file types
            if content.startswith(b'%PDF-'):
                # PDF-specific checks
                if b'/JavaScript' in content_lower or b'/JS' in content_lower:
                    logger.warning("PDF contains JavaScript")
                    return False

            elif content.startswith(b'PK\x03\x04'):
                # ZIP-based format checks (DOCX, XLSX, etc.)
                if b'vba' in content_lower or b'macro' in content_lower:
                    logger.warning("Office document contains macros")
                    return False

            return True

        except Exception as e:
            logger.error(f"Content scanning error: {e}")
            return False

    @classmethod
    def _validate_text_content(cls, content: bytes) -> bool:
        """Validate text file content."""
        try:
            # Try to decode as UTF-8
            try:
                text_content = content.decode('utf-8')
            except UnicodeDecodeError:
                # Try other common encodings
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        text_content = content.decode(encoding)
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    return False

            # Check for reasonable text content
            if len(text_content.strip()) == 0:
                return False

            # Check for excessive binary content
            binary_chars = sum(1 for c in text_content if ord(c) < 32 and c not in '\t\n\r')
            if binary_chars > len(text_content) * 0.1:  # More than 10% binary chars
                return False

            return True

        except Exception as e:
            logger.error(f"Text content validation error: {e}")
            return False

    @classmethod
    def get_file_type_from_content(cls, content: bytes) -> Optional[str]:
        """Determine file type from content magic number."""
        for file_type, signatures in cls.MAGIC_SIGNATURES.items():
            for signature in signatures:
                if content.startswith(signature):
                    return file_type
        return None

    @classmethod
    def sanitize_filename(cls, filename: str) -> str:
        """Sanitize filename for safe storage."""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')

        # Remove or replace dangerous characters
        dangerous_chars = '<>:"|?*'
        for char in dangerous_chars:
            filename = filename.replace(char, '_')

        # Limit length
        if len(filename) > 255:
            name, ext = Path(filename).stem, Path(filename).suffix
            filename = name[:255-len(ext)] + ext

        return filename


def validate_uploaded_file(file_content: bytes, filename: str, content_type: Optional[str] = None) -> Tuple[bool, str]:
    """
    Main function to validate uploaded files.

    Args:
        file_content: Raw file content
        filename: Original filename
        content_type: MIME type from upload

    Returns:
        Tuple of (is_valid, error_message)
    """
    return FileMagicValidator.validate_file(file_content, filename, content_type)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage."""
    return FileMagicValidator.sanitize_filename(filename)
