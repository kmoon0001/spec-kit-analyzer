"""Security validation utilities for user input and file handling."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Final

logger = logging.getLogger(__name__)


class SecurityValidator:
    """Centralised security checks shared across the application."""

    # File upload security
    ALLOWED_FILE_EXTENSIONS: Final[set[str]] = {".pdf", ".docx", ".txt", ".doc"}
    MAX_FILE_SIZE_MB: Final[int] = 50
    MAX_FILE_SIZE_BYTES: Final[int] = MAX_FILE_SIZE_MB * 1024 * 1024

    # Discipline validation
    ALLOWED_DISCIPLINES: Final[set[str]] = {"pt", "ot", "slp"}

    # Analysis mode validation
    ALLOWED_ANALYSIS_MODES: Final[set[str]] = {"rubric", "checklist", "hybrid"}

    # Strictness validation
    ALLOWED_STRICTNESS_LEVELS: Final[set[str]] = {"ultra_fast", "balanced", "thorough", "clinical_grade"}

    # String length limits
    MAX_USERNAME_LENGTH: Final[int] = 50
    MAX_PASSWORD_LENGTH: Final[int] = 128
    MAX_FILENAME_LENGTH: Final[int] = 255
    MAX_TEXT_INPUT_LENGTH: Final[int] = 10_000

    # Patterns considered unsafe in free-form text
    DANGEROUS_PATTERNS: Final[tuple[str, ...]] = (
        r"<script",
        r"javascript:",
        r"onerror=",
        r"onload=",
        r"\.\./",  # Path traversal
        r"\.\.\\",  # Path traversal (Windows)
    )

    @staticmethod
    def validate_filename(filename: str) -> tuple[bool, str | None]:
        """Ensure a filename is present, well-formed, and has an allowed extension."""
        if not filename:
            return False, "Filename is required"

        if len(filename) > SecurityValidator.MAX_FILENAME_LENGTH:
            return False, f"Filename exceeds maximum length of {SecurityValidator.MAX_FILENAME_LENGTH}"

        if ".." in filename or "/" in filename or "\\" in filename:
            logger.warning("Path traversal attempt detected in filename: %s", filename)
            return False, "Invalid filename: path traversal detected"

        file_ext = Path(filename).suffix.lower()
        if file_ext not in SecurityValidator.ALLOWED_FILE_EXTENSIONS:
            allowed = ", ".join(sorted(SecurityValidator.ALLOWED_FILE_EXTENSIONS))
            return False, f"File type not allowed. Allowed types: {allowed}"

        return True, None

    @staticmethod
    def validate_and_sanitize_filename(filename: str) -> str:
        """Validate a filename and return a safe representation suitable for storage."""
        is_valid, error = SecurityValidator.validate_filename(filename)
        if not is_valid:
            raise ValueError(error or "Invalid filename")

        safe_name = re.sub(r"[^A-Za-z0-9._-]", "_", Path(filename).name)
        if not safe_name:
            raise ValueError("Filename is invalid after sanitization")
        return safe_name[: SecurityValidator.MAX_FILENAME_LENGTH]

    @staticmethod
    def validate_file_size(file_size: int) -> tuple[bool, str | None]:
        """Confirm that a file size is non-zero and within configured bounds."""
        if file_size > SecurityValidator.MAX_FILE_SIZE_BYTES:
            return False, f"File size exceeds maximum allowed size of {SecurityValidator.MAX_FILE_SIZE_MB}MB"

        if file_size == 0:
            return False, "File is empty"

        return True, None

    @staticmethod
    def validate_discipline(discipline: str) -> tuple[bool, str | None]:
        """Validate a clinical discipline string."""
        if not discipline:
            return False, "Discipline is required"

        if discipline.lower() not in SecurityValidator.ALLOWED_DISCIPLINES:
            allowed = ", ".join(sorted(SecurityValidator.ALLOWED_DISCIPLINES))
            return False, f"Invalid discipline. Allowed values: {allowed}"

        return True, None

    @staticmethod
    def validate_strictness(level: str) -> tuple[bool, str | None]:
        """Check that an analysis strictness level is recognised."""
        if not level:
            return False, "Strictness level is required"

        normalized = level.lower()
        if normalized not in SecurityValidator.ALLOWED_STRICTNESS_LEVELS:
            allowed = ", ".join(sorted(SecurityValidator.ALLOWED_STRICTNESS_LEVELS))
            return False, f"Invalid strictness. Allowed values: {allowed}"

        return True, None

    @staticmethod
    def validate_analysis_mode(mode: str) -> tuple[bool, str | None]:
        """Validate an analysis mode identifier."""
        if not mode:
            return False, "Analysis mode is required"

        if mode.lower() not in SecurityValidator.ALLOWED_ANALYSIS_MODES:
            allowed = ", ".join(sorted(SecurityValidator.ALLOWED_ANALYSIS_MODES))
            return False, f"Invalid analysis mode. Allowed values: {allowed}"

        return True, None

    @staticmethod
    def sanitize_text_input(text: str, max_length: int | None = None) -> str:
        """Strip unsafe patterns and enforce length limits on free-form input."""
        if not text:
            return ""

        if max_length is not None:
            text = text[:max_length]
        elif len(text) > SecurityValidator.MAX_TEXT_INPUT_LENGTH:
            text = text[: SecurityValidator.MAX_TEXT_INPUT_LENGTH]

        for pattern in SecurityValidator.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning("Dangerous pattern detected in input: %s", pattern)
                text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text

    @staticmethod
    def validate_username(username: str) -> tuple[bool, str | None]:
        """Validate username format and length."""
        if not username:
            return False, "Username is required"

        if len(username) > SecurityValidator.MAX_USERNAME_LENGTH:
            return False, f"Username exceeds maximum length of {SecurityValidator.MAX_USERNAME_LENGTH}"

        if not re.match(r"^[a-zA-Z0-9_-]+$", username):
            return False, "Username can only contain letters, numbers, underscores, and hyphens"

        return True, None

    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str | None]:
        """Enforce baseline password complexity requirements."""
        if not password:
            return False, "Password is required"

        if len(password) < 8:
            return False, "Password must be at least 8 characters long"

        if len(password) > SecurityValidator.MAX_PASSWORD_LENGTH:
            return False, f"Password exceeds maximum length of {SecurityValidator.MAX_PASSWORD_LENGTH}"

        if not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        if not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        if not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        return True, None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Generate a filesystem-safe filename without altering the extension dramatically."""
        safe_name = Path(filename).name
        safe_name = re.sub(r"[^\w\s.-]", "", safe_name)
        safe_name = safe_name.replace(" ", "_")

        if len(safe_name) > SecurityValidator.MAX_FILENAME_LENGTH:
            name_part = safe_name[: SecurityValidator.MAX_FILENAME_LENGTH - 10]
            ext_part = Path(safe_name).suffix
            safe_name = name_part + ext_part

        return safe_name
