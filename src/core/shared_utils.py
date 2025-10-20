"""Shared Utility Modules for Clinical Compliance Analysis.

This module provides common utility functions, patterns, and helpers used
throughout the application using expert practices and design patterns.

Features:
- Common data validation utilities
- File and path utilities
- String and text processing utilities
- Data transformation utilities
- Error handling utilities
- Configuration management utilities
- Retry and resilience utilities
"""

import asyncio
import functools
import hashlib
import json
import os
import re
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, ParamSpec, Tuple
import yaml
from dataclasses import dataclass, field
import aiofiles
import aiohttp
from contextlib import asynccontextmanager
import base64
import mimetypes
from urllib.parse import urlparse, urljoin
import secrets
import string

# Type definitions
T = TypeVar('T')
P = ParamSpec('P')


class ValidationError(Exception):
    """Custom validation error."""
    pass


class RetryError(Exception):
    """Custom retry error."""
    pass


@dataclass
class ValidationResult:
    """Validation result with detailed information."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    data: Optional[Any] = None


class DataValidator:
    """Comprehensive data validation utilities."""

    @staticmethod
    def validate_email(email: str) -> ValidationResult:
        """Validate email address."""
        errors = []

        if not email or not isinstance(email, str):
            errors.append("Email must be a non-empty string")
            return ValidationResult(is_valid=False, errors=errors)

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")

        if len(email) > 254:  # RFC 5321 limit
            errors.append("Email too long")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, data=email)

    @staticmethod
    def validate_phone(phone: str) -> ValidationResult:
        """Validate phone number."""
        errors = []

        if not phone or not isinstance(phone, str):
            errors.append("Phone must be a non-empty string")
            return ValidationResult(is_valid=False, errors=errors)

        # Remove all non-digit characters
        digits_only = re.sub(r'\D', '', phone)

        if len(digits_only) < 10 or len(digits_only) > 15:
            errors.append("Phone number must be 10-15 digits")

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, data=phone)

    @staticmethod
    def validate_json(data: str) -> ValidationResult:
        """Validate JSON string."""
        errors = []

        if not data or not isinstance(data, str):
            errors.append("Data must be a non-empty string")
            return ValidationResult(is_valid=False, errors=errors)

        try:
            parsed_data = json.loads(data)
            return ValidationResult(is_valid=True, data=parsed_data)
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)

    @staticmethod
    def validate_file_path(path: Union[str, Path], must_exist: bool = False) -> ValidationResult:
        """Validate file path."""
        errors = []

        try:
            path_obj = Path(path)

            if not path_obj.is_absolute() and not path_obj.is_relative_to(Path.cwd()):
                errors.append("Path must be relative to current directory or absolute")

            if must_exist and not path_obj.exists():
                errors.append("File does not exist")

            return ValidationResult(is_valid=len(errors) == 0, errors=errors, data=path_obj)

        except Exception as e:
            errors.append(f"Invalid path: {str(e)}")
            return ValidationResult(is_valid=False, errors=errors)


class FileUtils:
    """File and path utilities."""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary."""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """Get safe filename by removing/replacing invalid characters."""
        # Remove or replace invalid characters
        safe_chars = re.sub(r'[<>:"/\\|?*]', '_', filename)

        # Remove leading/trailing spaces and dots
        safe_chars = safe_chars.strip(' .')

        # Ensure filename is not empty
        if not safe_chars:
            safe_chars = f"file_{uuid.uuid4().hex[:8]}"

        # Limit length
        if len(safe_chars) > 255:
            name, ext = os.path.splitext(safe_chars)
            safe_chars = name[:255-len(ext)] + ext

        return safe_chars

    @staticmethod
    def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
        """Get file hash."""
        hash_obj = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    async def get_file_hash_async(file_path: Union[str, Path], algorithm: str = 'sha256') -> str:
        """Get file hash asynchronously."""
        hash_obj = hashlib.new(algorithm)

        async with aiofiles.open(file_path, 'rb') as f:
            while chunk := await f.read(4096):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    @staticmethod
    def get_file_size(file_path: Union[str, Path]) -> int:
        """Get file size in bytes."""
        return Path(file_path).stat().st_size

    @staticmethod
    def get_mime_type(file_path: Union[str, Path]) -> str:
        """Get MIME type of file."""
        mime_type, _ = mimetypes.guess_type(str(file_path))
        return mime_type or 'application/octet-stream'

    @staticmethod
    def is_safe_path(path: Union[str, Path], base_path: Union[str, Path]) -> bool:
        """Check if path is safe (within base path)."""
        try:
            path_obj = Path(path).resolve()
            base_obj = Path(base_path).resolve()
            return path_obj.is_relative_to(base_obj)
        except (ValueError, OSError):
            return False


class TextUtils:
    """Text and string processing utilities."""

    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """Sanitize text by removing/replacing problematic characters."""
        if not text:
            return ""

        # Remove control characters except newlines and tabs
        sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized)

        # Trim whitespace
        sanitized = sanitized.strip()

        # Limit length if specified
        if max_length and len(sanitized) > max_length:
            sanitized = sanitized[:max_length-3] + "..."

        return sanitized

    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract keywords from text."""
        if not text:
            return []

        # Convert to lowercase and split into words
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())

        # Filter by minimum length
        keywords = [word for word in words if len(word) >= min_length]

        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)

        return unique_keywords

    @staticmethod
    def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text to maximum length."""
        if not text or len(text) <= max_length:
            return text

        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        """Normalize whitespace in text."""
        if not text:
            return ""

        # Replace multiple whitespace with single space
        normalized = re.sub(r'\s+', ' ', text)

        # Trim leading/trailing whitespace
        return normalized.strip()

    @staticmethod
    def mask_sensitive_data(text: str, pattern: str, mask_char: str = '*') -> str:
        """Mask sensitive data in text."""
        if not text or not pattern:
            return text

        def mask_match(match):
            matched_text = match.group(0)
            if len(matched_text) <= 2:
                return mask_char * len(matched_text)
            else:
                return matched_text[0] + mask_char * (len(matched_text) - 2) + matched_text[-1]

        return re.sub(pattern, mask_match, text)


class DataTransformer:
    """Data transformation utilities."""

    @staticmethod
    def flatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary."""
        def _flatten(obj, parent_key=''):
            items = []
            if isinstance(obj, dict):
                for k, v in obj.items():
                    new_key = f"{parent_key}{separator}{k}" if parent_key else k
                    items.extend(_flatten(v, new_key).items())
            elif isinstance(obj, list):
                for i, v in enumerate(obj):
                    new_key = f"{parent_key}{separator}{i}" if parent_key else str(i)
                    items.extend(_flatten(v, new_key).items())
            else:
                return {parent_key: obj}
            return dict(items)

        return _flatten(data)

    @staticmethod
    def unflatten_dict(data: Dict[str, Any], separator: str = '.') -> Dict[str, Any]:
        """Unflatten dictionary."""
        result = {}

        for key, value in data.items():
            keys = key.split(separator)
            current = result

            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]

            current[keys[-1]] = value

        return result

    @staticmethod
    def convert_to_snake_case(text: str) -> str:
        """Convert text to snake_case."""
        # Insert underscore before uppercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', text)
        # Insert underscore before uppercase letters that follow lowercase letters
        s2 = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1)
        return s2.lower()

    @staticmethod
    def convert_to_camel_case(text: str) -> str:
        """Convert text to camelCase."""
        components = text.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])


class RetryUtils:
    """Retry and resilience utilities."""

    @staticmethod
    def retry_with_backoff(
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Exception, ...] = (Exception,)
    ):
        """Decorator for retrying functions with exponential backoff."""
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @functools.wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e

                        if attempt == max_attempts - 1:
                            raise RetryError(f"Failed after {max_attempts} attempts") from e

                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)

                        # Add jitter to prevent thundering herd
                        if jitter:
                            delay *= (0.5 + secrets.SystemRandom().random() * 0.5)

                        time.sleep(delay)

                raise RetryError("Retry logic failed") from last_exception

            return wrapper
        return decorator

    @staticmethod
    def async_retry_with_backoff(
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        exceptions: Tuple[Exception, ...] = (Exception,)
    ):
        """Decorator for retrying async functions with exponential backoff."""
        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            @functools.wraps(func)
            async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                last_exception = None

                for attempt in range(max_attempts):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e

                        if attempt == max_attempts - 1:
                            raise RetryError(f"Failed after {max_attempts} attempts") from e

                        # Calculate delay with exponential backoff
                        delay = min(base_delay * (exponential_base ** attempt), max_delay)

                        # Add jitter to prevent thundering herd
                        if jitter:
                            delay *= (0.5 + secrets.SystemRandom().random() * 0.5)

                        await asyncio.sleep(delay)

                raise RetryError("Retry logic failed") from last_exception

            return wrapper
        return decorator


class ConfigUtils:
    """Configuration management utilities."""

    @staticmethod
    def load_yaml_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to load YAML config from {file_path}: {e}")

    @staticmethod
    def save_yaml_config(config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save configuration to YAML file."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise ValueError(f"Failed to save YAML config to {file_path}: {e}")

    @staticmethod
    def load_json_config(file_path: Union[str, Path]) -> Dict[str, Any]:
        """Load JSON configuration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to load JSON config from {file_path}: {e}")

    @staticmethod
    def save_json_config(config: Dict[str, Any], file_path: Union[str, Path]) -> None:
        """Save configuration to JSON file."""
        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise ValueError(f"Failed to save JSON config to {file_path}: {e}")

    @staticmethod
    def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> str:
        """Get environment variable with validation."""
        value = os.getenv(key, default)

        if required and not value:
            raise ValueError(f"Required environment variable {key} is not set")

        return value or ""

    @staticmethod
    def get_env_bool(key: str, default: bool = False) -> bool:
        """Get boolean environment variable."""
        value = os.getenv(key, '').lower()
        return value in ('true', '1', 'yes', 'on')


class SecurityUtils:
    """Security utilities."""

    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate secure random token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    @staticmethod
    def generate_api_key(prefix: str = "api") -> str:
        """Generate API key with prefix."""
        token = SecurityUtils.generate_secure_token(32)
        return f"{prefix}_{token}"

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """Hash password with salt."""
        if salt is None:
            salt = SecurityUtils.generate_secure_token(16)

        # Use PBKDF2 for password hashing
        import hashlib
        import base64

        key = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        hashed = base64.b64encode(key).decode()

        return hashed, salt

    @staticmethod
    def verify_password(password: str, hashed: str, salt: str) -> bool:
        """Verify password against hash."""
        computed_hash, _ = SecurityUtils.hash_password(password, salt)
        return computed_hash == hashed

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for security."""
        # Remove path traversal attempts
        filename = filename.replace('..', '').replace('/', '').replace('\\', '')

        # Remove control characters
        filename = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', filename)

        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:255-len(ext)] + ext

        return filename


class NetworkUtils:
    """Network utilities."""

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False

    @staticmethod
    def join_url(base: str, path: str) -> str:
        """Join URL components safely."""
        return urljoin(base.rstrip('/') + '/', path.lstrip('/'))

    @staticmethod
    def get_domain(url: str) -> Optional[str]:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc
        except Exception:
            return None


class AsyncUtils:
    """Async utilities."""

    @staticmethod
    async def gather_with_concurrency_limit(
        tasks: List[Callable],
        limit: int = 10
    ) -> List[Any]:
        """Run async tasks with concurrency limit."""
        semaphore = asyncio.Semaphore(limit)

        async def run_with_semaphore(task):
            async with semaphore:
                if asyncio.iscoroutinefunction(task):
                    return await task()
                else:
                    return task()

        return await asyncio.gather(*[run_with_semaphore(task) for task in tasks])

    @staticmethod
    async def timeout_after(seconds: float):
        """Async timeout context manager."""
        return asyncio.wait_for(asyncio.sleep(seconds), timeout=seconds)


# Global utility instances
data_validator = DataValidator()
file_utils = FileUtils()
text_utils = TextUtils()
data_transformer = DataTransformer()
retry_utils = RetryUtils()
config_utils = ConfigUtils()
security_utils = SecurityUtils()
network_utils = NetworkUtils()
async_utils = AsyncUtils()
