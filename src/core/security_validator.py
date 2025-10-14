"""Security validation utilities for input sanitization and validation.
import numpy as np

This module provides comprehensive security validation for user inputs,
file uploads, and API parameters to prevent common security vulnerabilities.
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Centralized security validation for all user inputs."""

    # File upload security
    ALLOWED_FILE_EXTENSIONS: set[str] = {".pdf", ".docx", ".txt", ".doc"}
    MAX_FILE_SIZE_MB: int = 50
    MAX_FILE_SIZE_BYTES: int = MAX_FILE_SIZE_MB * 1024 * 1024

    # Discipline validation
    ALLOWED_DISCIPLINES: set[str] = {"pt", "ot", "slp"}

    # Analysis mode validation
    ALLOWED_ANALYSIS_MODES: set[str] = {"rubric", "checklist", "hybrid"}

    # Strictness validation
    ALLOWED_STRICTNESS_LEVELS: set[str] = {"lenient", "standard", "strict"}

    # String length limits
    MAX_USERNAME_LENGTH: int = 50
    MAX_PASSWORD_LENGTH: int = 128
    MAX_FILENAME_LENGTH: int = 255
    MAX_TEXT_INPUT_LENGTH: int = 10000

    # Dangerous patterns to block
    DANGEROUS_PATTERNS: list[str] = [
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"\.\./",  # Path traversal
        r"\.\.\\",  # Path traversal (Windows)
    ]

    @staticmethod
    def validate_filename(filename: str) -> tuple[bool, str | None]:
        """Validate uploaded filename for security.

        Args:
            filename: The filename to validate

        Returns:
            Tuple of (is_valid, error_message)

        """
        if not filename:
            return False, "Filename is required"

        if len(filename) > SecurityValidator.MAX_FILENAME_LENGTH:
            return (False, f"Filename exceeds maximum length of {SecurityValidator.MAX_FILENAME_LENGTH}")

        # Check for path traversal attempts
        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning("Path traversal attempt detected in filename: %s", filename)
            return False, "Invalid filename: path traversal detected"

        # Validate file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in SecurityValidator.ALLOWED_FILE_EXTENSIONS:
            return (
                False,
                f"File type not allowed. Allowed types: {', '.join(SecurityValidator.ALLOWED_FILE_EXTENSIONS)}",
            )

        return True, None

    @staticmethod
    def validate_and_sanitize_filename(filename: str) -> str:
        """Validate a filename and return a sanitized version safe for storage."""
        is_valid, error = SecurityValidator.validate_filename(filename)
        if not is_valid:
            raise ValueError(error or "Invalid filename")

        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
        if not safe_name:
            raise ValueError("Filename is invalid after sanitization")
        return safe_name[: SecurityValidator.MAX_FILENAME_LENGTH]

    @staticmethod
    def validate_file_size(file_size: int) -> tuple[bool, str | None]:
        """Validate file size.

        Args:
            file_size: Size of file in bytes

        Returns:
            Tuple of (is_valid, error_message)

        """
        if file_size > SecurityValidator.MAX_FILE_SIZE_BYTES:
            return (False, f"File size exceeds maximum allowed size of {SecurityValidator.MAX_FILE_SIZE_MB}MB")

        if file_size == 0:
            return False, "File is empty"

        return True, None

    @staticmethod
    def validate_discipline(discipline: str) -> tuple[bool, str | None]:
        """Validate discipline parameter.

        Args:
            discipline: The discipline to validate

        Returns:
            Tuple of (is_valid, error_message)

        """
        if not discipline:
            return False, "Discipline is required"

        if discipline.lower() not in SecurityValidator.ALLOWED_DISCIPLINES:
            return (False, f"Invalid discipline. Allowed values: {', '.join(SecurityValidator.ALLOWED_DISCIPLINES)}")

        return True, None

    
    @staticmethod
    def validate_strictness(level: str) -> tuple[bool, str | None]:
        """Validate analysis strictness level."""

        if not level:
            return False, "Strictness level is required"

        normalized = level.lower()
        if normalized not in SecurityValidator.ALLOWED_STRICTNESS_LEVELS:
            allowed = ', '.join(sorted(SecurityValidator.ALLOWED_STRICTNESS_LEVELS))
            return False, f"Invalid strictness. Allowed values: {allowed}"

        return True, None


@staticmethod
    def validate_analysis_mode(mode: str) -> tuple[bool, str | None]:
        """Validate analysis mode parameter.

        Args:
            mode: The analysis mode to validate

        Returns:
            Tuple of (is_valid, error_message)

        """
        if not mode:
            return False, "Analysis mode is required"

        if mode.lower() not in SecurityValidator.ALLOWED_ANALYSIS_MODES:
            return (
                False,
                f"Invalid analysis mode. Allowed values: {', '.join(SecurityValidator.ALLOWED_ANALYSIS_MODES)}",
            )

        return True, None

    @staticmethod
    def sanitize_text_input(text: str, max_length: int | None = None) -> str:
        """Sanitize text input to prevent XSS and injection attacks.

        Args:
            text: The text to sanitize
            max_length: Optional maximum length to enforce

        Returns:
            Sanitized text

        """
        if not text:
            return ""

        # Enforce length limit
        if max_length:
            text = text[:max_length]
        elif len(text) > SecurityValidator.MAX_TEXT_INPUT_LENGTH:
            text = text[: SecurityValidator.MAX_TEXT_INPUT_LENGTH]

        # Check for dangerous patterns
        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("Dangerous pattern detected in input: %s", pattern)
                # Remove the dangerous pattern
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str | None]:
        """Validate username for security and format.

        Args:
            username: The username to validate

        Returns:
            Tuple of (is_valid, error_message)

        """
        if not username:
            return False, "Username is required"

        if len(username) > SecurityValidator.MAX_USERNAME_LENGTH:
            return (False, f"Username exceeds maximum length of {SecurityValidator.MAX_USERNAME_LENGTH}")

        # Username should only contain alphanumeric characters, underscores, and hyphens
        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return (False, "Username can only contain letters, numbers, underscores, and hyphens")

        return True, None

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str | None]:
        """Validate password strength.

        Args:
            password: The password to validate

        Returns:
            Tuple of (is_valid, error_message)

        """
        if not password:
            return False, "Password is required"

        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if len(password) > SecurityValidator.MAX_PASSWORD_LENGTH:
            return (False, f"Password exceeds maximum length of {SecurityValidator.MAX_PASSWORD_LENGTH}")

        # Check for at least one uppercase, one lowercase, and one digit
        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        return True, None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent security issues.

        Args:
            filename: The filename to sanitize

        Returns:
            Sanitized filename

        """
        # Get just the filename without path
        safe_name = Path(filename).name

        # Remove any non-alphanumeric characters except dots, underscores, and hyphens
        safe_name = re.sub(r"[^\w\s.-]", "", safe_name)

        # Replace spaces with underscores
        safe_name = safe_name.replace(" ", "_")

        # Limit length
        if len(safe_name) > SecurityValidator.MAX_FILENAME_LENGTH:
            # Preserve extension
            name_part = safe_name[: SecurityValidator.MAX_FILENAME_LENGTH - 10]
            ext_part = Path(safe_name).suffix
            safe_name = name_part + ext_part

        return safe_name
