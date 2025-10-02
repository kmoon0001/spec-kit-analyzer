# Security Validation Guidelines

## Quick Reference for Developers

When working with user inputs in the Therapy Compliance Analyzer, always use the centralized `SecurityValidator` class for validation and sanitization.

## Import

```python
from src.core.security_validator import SecurityValidator
```

## Common Validation Patterns

### File Upload Endpoints

```python
from fastapi import UploadFile, HTTPException

# Validate filename
is_valid, error_msg = SecurityValidator.validate_filename(file.filename)
if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)

# Read and validate file size
content = await file.read()
is_valid, error_msg = SecurityValidator.validate_file_size(len(content))
if not is_valid:
    raise HTTPException(status_code=413, detail=error_msg)

# Sanitize filename before saving
safe_filename = SecurityValidator.sanitize_filename(file.filename)
```

### Form Parameters

```python
# Validate discipline parameter
is_valid, error_msg = SecurityValidator.validate_discipline(discipline)
if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)

# Validate analysis mode
is_valid, error_msg = SecurityValidator.validate_analysis_mode(mode)
if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)
```

### Text Inputs

```python
# Sanitize user text input
clean_text = SecurityValidator.sanitize_text_input(user_input)

# With custom length limit
clean_text = SecurityValidator.sanitize_text_input(user_input, max_length=500)
```

### Authentication

```python
# Validate username format
is_valid, error_msg = SecurityValidator.validate_username(username)
if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)

# Validate password strength
is_valid, error_msg = SecurityValidator.validate_password_strength(password)
if not is_valid:
    raise HTTPException(status_code=400, detail=error_msg)
```

## Validation Rules

### File Uploads
- **Allowed extensions**: `.pdf`, `.docx`, `.txt`, `.doc`
- **Max file size**: 50MB
- **Filename length**: Max 255 characters
- **Blocks**: Path traversal, dangerous characters

### Disciplines
- **Allowed values**: `pt`, `ot`, `slp` (case-insensitive)

### Analysis Modes
- **Allowed values**: `rubric`, `checklist`, `hybrid` (case-insensitive)

### Usernames
- **Format**: Alphanumeric, underscores, hyphens only
- **Max length**: 50 characters
- **No spaces or special characters**

### Passwords
- **Min length**: 8 characters
- **Max length**: 128 characters
- **Requirements**: 
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one digit

### Text Inputs
- **Max length**: 10,000 characters (default)
- **Sanitizes**: XSS patterns, path traversal, injection attempts

## Error Handling Pattern

Always use the tuple return pattern for validation:

```python
is_valid, error_msg = SecurityValidator.validate_something(value)
if not is_valid:
    # Handle error - error_msg contains user-friendly message
    raise HTTPException(status_code=400, detail=error_msg)
```

## Security Logging

Log validation failures for security monitoring:

```python
import logging

logger = logging.getLogger(__name__)

is_valid, error_msg = SecurityValidator.validate_filename(filename)
if not is_valid:
    logger.warning(f"Validation failed: {error_msg}", extra={"filename": filename})
    raise HTTPException(status_code=400, detail=error_msg)
```

## Testing

When writing tests, use the SecurityValidator for consistent validation:

```python
def test_my_endpoint(client):
    # Test with invalid input
    response = client.post("/upload", files={"file": ("../etc/passwd", b"content")})
    assert response.status_code == 400
    assert "path traversal" in response.json()["detail"].lower()
```

## DO NOT

❌ **Don't** implement custom validation logic for security-critical inputs
❌ **Don't** skip validation for "trusted" inputs
❌ **Don't** use generic error messages that don't help users
❌ **Don't** validate after processing - validate at the boundary

## DO

✅ **Do** use SecurityValidator for all user inputs
✅ **Do** validate at API boundaries before processing
✅ **Do** sanitize text inputs before storage
✅ **Do** provide clear, actionable error messages
✅ **Do** log security validation failures

## Questions?

See `SECURITY_VALIDATOR_IMPLEMENTATION.md` for detailed documentation and examples.
